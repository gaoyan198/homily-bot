#!/usr/bin/env python3
"""
GAMBIT G-S4 — strategy arms S1-pure / S1-stopped / S2 / S3 on the G-S3
engine, with the D-G3 exit stack and honest fill model. Runs the full
Part-II protocol and writes BACKTEST_RESULTS.md with a mechanical verdict.

PRE-REGISTERED IMPLEMENTATION CHOICES (docstring-registered BEFORE the
first protocol run, homily §2.2 rule; ambiguities in PRD §4 / DESIGNS D-G3
resolved here and frozen — changes are logged amendments):

* Cadence: decisions on each window Friday (last session of its ISO week),
  fills at the next session's open. S1 re-ranks every 4th Friday. Setup
  arms (S2/S3) scan every Friday, max 2 new entries per scan (PRD §5.1),
  max 6 concurrent positions. S1 holds the top N=5 (PRD's "top 3–5" pinned
  to 5 — matches the RANDOM-5 luck band and D-G3's ~6-position sizing).
* RS blend: mean of 63/126/252-session returns on adjusted closes, each
  skipping the most recent 10 sessions (the 2-week reversal guard).
  Rankable = point-in-time D-G2-eligible + ≥262 bars. "Top decile" =
  first ceil(n/10) of the ranked list.
* Exit stack (D-G3, verbatim): initial stop = fill − 2×ATR(14) (ATR from
  decision day; 1R = that distance); TP at +2R closes HALF (remainder
  runs); trail = max(initial stop, 20-day low of lows), ratchets up only,
  active from entry; time stop = exit at next open once 56 calendar days
  in position have passed (fill model forbids exit-at-close fictions);
  regime flip closes everything at next open.
* Fill model (D-G3, verbatim): stop gap-through fills at open, touch fills
  at stop; TP mirror-image; stop checked before TP on the same bar
  (conservative). Costs 0.125%/side, stress 0.175%/side.
* Sizing: S1-pure equal-weight equity/5 at entry, no interim rebalance.
  Stopped arms risk-parity: qty = 0.75% of equity / 1R, capped at 40% of
  equity notional and by cash (cash ≥ 0 always).
* Regime (D-63): QQQ weekly close < 40-week SMA two consecutive weeks →
  BEAR from the next session (liquidate at that open, no entries while
  bear). First weekly close ≥ MA flips back; re-entry ramp caps invested
  notional at 1/3, 2/3, 3/3 of equity over the next three weeks; rotation
  arms may re-enter on each ramp Friday, not just 4-week boundaries.
* S2 trigger (Friday close): RS top decile · close > SMA100 and SMA100
  rising (> its value 20 sessions back — the "rising 20-week trend" on
  daily bars) · close 3–8% below its 20-day closing high · within ±3% of
  SMA20 · reclaim bar (close > previous session's high).
* S3 trigger (Friday close, Amendment A1): RS top decile · vol-hole zone
  in force (gambit_vol port) · Friday close above the zone's upper bound ·
  the first close above the upper bound happened within the last 5
  sessions on volume > 1.5× its 20-day median · one entry per zone, ever
  (parsimony). Close below the lower bound = journal-only VOLHOLE_BREAK
  DOWN count, never an action (homily §5b).
* Amendment A3 (logged with reason, per the freeze rule): the G5
  2-positions-per-cluster cap is NOT mechanically enforceable in P1 — no
  key-free sector source exists. The backtest substitutes the concurrency
  caps above; the paper phase enforces cluster caps at digest review.
"""
import bisect
import datetime
import statistics
from dataclasses import dataclass

import gambit_backtest as bt
import gambit_vol

RISK_FRAC = 0.0075          # 0.75% of equity risked per trade
MAX_NOTIONAL_FRAC = 0.40
TIME_STOP_DAYS = 56         # 8 weeks
S1_N = 5
SETUP_MAX_POS = 6
SETUP_MAX_ENTRIES = 2
RS_SKIP = 10
RS_LOOKBACKS = (63, 126, 252)
MIN_RS_BARS = 262
PULLBACK = (0.03, 0.08)
NEAR_MEAN = 0.03
VOL_EXPANSION = 1.5
BREAKOUT_RECENCY = 5


# ------------------------------------------------------------- indicators --

class Ind:
    """Per-symbol precomputed indicator arrays over the FULL adjusted series
    (every value at index i uses bars[:i+1] only — walk-forward safe)."""

    def __init__(self, ser):
        self.ser = ser
        b = ser.bars
        n = len(b)
        closes = [x[4] for x in b]
        self.closes = closes
        tr = [max(b[i][2], b[i - 1][4] if i else b[i][4])
              - min(b[i][3], b[i - 1][4] if i else b[i][4])
              for i in range(n)]
        self.atr14 = _rollmean(tr, 14)
        self.sma20 = _rollmean(closes, 20)
        self.sma100 = _rollmean(closes, 100)
        self.low20 = _rollmin([x[3] for x in b], 20)
        self.high20c = _rollmax(closes, 20)
        self.medvol20 = _rollmedian([x[5] for x in b], 20)
        self.holes = gambit_vol.hole_days(b)

    def rs(self, i):
        if i < MIN_RS_BARS:
            return None
        j = i - RS_SKIP
        vals = []
        for k in RS_LOOKBACKS:
            if j - k < 0 or self.closes[j - k] <= 0:
                return None
            vals.append(self.closes[j] / self.closes[j - k] - 1)
        return sum(vals) / len(vals)


def _rollmean(xs, w):
    out, s = [], 0.0
    for i, x in enumerate(xs):
        s += x
        if i >= w:
            s -= xs[i - w]
        out.append(s / min(i + 1, w))
    return out


def _rollmin(xs, w):
    return [min(xs[max(0, i - w + 1):i + 1]) for i in range(len(xs))]


def _rollmax(xs, w):
    return [max(xs[max(0, i - w + 1):i + 1]) for i in range(len(xs))]


def _rollmedian(xs, w):
    return [statistics.median(xs[max(0, i - w + 1):i + 1])
            for i in range(len(xs))]


# ----------------------------------------------------------------- regime --

class Regime:
    """D-63 kill-switch from QQQ weekly closes vs the 40-week SMA. State for
    a session is decided from weeks fully COMPLETED before it."""

    def __init__(self, qqq_series):
        weeks = []                                  # (week_end_date, close)
        cur, last = None, None
        for d, o, h, l, c, v in qqq_series.bars:
            k = d.isocalendar()[:2]
            if k != cur and cur is not None:
                weeks.append(last)
            cur, last = k, (d, c)
        if last:
            weeks.append(last)
        self.effective = []          # (from_date, state, ramp_week_index)
        consec_below, bear = 0, False
        ramp = 99                                    # weeks since flip-back
        for i, (wend, close) in enumerate(weeks):
            if i < 40:
                continue
            ma = sum(c for _, c in weeks[i - 39:i + 1]) / 40
            if close < ma:
                consec_below += 1
                if consec_below >= 2 and not bear:
                    bear, ramp = True, 99
            else:
                if bear:
                    bear, ramp = False, 0            # flip-back this week
                elif ramp < 99:
                    ramp += 1
                consec_below = 0
            eff = wend + datetime.timedelta(days=1)
            self.effective.append((eff, bear, ramp))
        self._dates = [e[0] for e in self.effective]

    def at(self, d):
        """-> (bear, invested_cap_fraction) for session d."""
        i = bisect.bisect_right(self._dates, d) - 1
        if i < 0:
            return False, 1.0
        _, bear, ramp = self.effective[i]
        if bear:
            return True, 0.0
        cap = {0: 1 / 3, 1: 2 / 3, 2: 1.0}.get(ramp, 1.0)
        return False, cap


# ----------------------------------------------------------------- engine --

@dataclass
class Pos:
    sym: str
    qty: float
    entry: float
    r: float                # 1R in price units (0 for unstopped arms)
    stop: float
    tp: float
    half_done: bool
    entry_date: datetime.date


def fridays(cal):
    return [a for a, b in zip(cal, cal[1:] + [None])
            if b is None or a.isocalendar()[:2] != b.isocalendar()[:2]]


def run_arm(series, inds, cal, regime, *, mode, cost_side=bt.COST_SIDE,
            capital=bt.CAPITAL, signal=None):
    """mode: 's1_pure' | 's1_stop' | 'setup' (S2/S3 differ only in `signal`).
    -> (curve, trades, events) — trades rows carry R multiples; events
    counts journal-only occurrences (e.g. VOLHOLE_BREAKDOWN)."""
    stops = mode != "s1_pure"
    rotation = mode.startswith("s1")
    frs = fridays(cal)
    rot_fridays = set(frs[::4])
    cash = capital
    book = {}                                  # sym -> Pos
    pending_entry, pending_exit = [], []       # queued at close, fill next open
    trades, events = [], {"VOLHOLE_BREAKDOWN": 0}
    consumed = set()                           # (sym, zone_id) for S3
    was_bear = False
    curve = []
    prev_d = cal[0] - datetime.timedelta(days=1)

    def px_at(sym, d):
        return series[sym].close_at(d)

    def equity(d):
        return cash + sum(p.qty * (px_at(p.sym, d) or p.entry)
                          for p in book.values())

    def close_out(p, price, frac, reason, d):
        nonlocal cash
        qty = p.qty * frac
        cash += qty * price * (1 - cost_side)
        r_mult = (price - p.entry) / p.r if p.r else 0.0
        trades.append({"sym": p.sym, "entry_date": p.entry_date,
                       "exit_date": d, "entry": p.entry, "exit": price,
                       "frac": frac, "reason": reason, "R": r_mult})
        p.qty -= qty
        if p.qty * price < 1.0:
            book.pop(p.sym, None)

    def bar_today(sym, d):
        ser = series[sym]
        i = ser.idx_at(d)
        return (i, ser.bars[i]) if i is not None and ser.dates[i] == d \
            else (None, None)

    def ranked(d):
        rows = []
        for sym, ser in series.items():
            if not ser.eligible_at(d):
                continue
            i = ser.idx_at(d)
            r = inds[sym].rs(i) if i is not None else None
            if r is not None:
                rows.append((sym, r))
        rows.sort(key=lambda x: (-x[1], x[0]))
        return rows

    for d in cal:
        bear, cap = regime.at(d)
        # 1. regime flip -> liquidate everything at this open
        if bear and not was_bear:
            for p in list(book.values()):
                i, bar = bar_today(p.sym, d)
                close_out(p, bar[1] if bar else px_at(p.sym, d) or p.entry,
                          1.0, "REGIME", d)
            pending_entry, pending_exit = [], []
        was_bear = bear

        # 2. queued exits at the open
        for sym, reason in pending_exit:
            if sym in book:
                i, bar = bar_today(sym, d)
                price = bar[1] if bar else px_at(sym, d)
                if price:
                    close_out(book[sym], price, 1.0, reason, d)
        pending_exit = []

        # 3. queued entries at the open — sizing marks the existing book at
        # the PREVIOUS session's close (today's close is still unknown at
        # the open; prime directive 4)
        if not bear:
            eq = equity(prev_d)
            invested = eq - cash
            limit = cap * eq
            for sym, r_dollars, reason in pending_entry:
                if sym in book:
                    continue
                max_pos = S1_N if rotation else SETUP_MAX_POS
                if len(book) >= max_pos:
                    continue
                i, bar = bar_today(sym, d)
                if not bar:
                    continue
                fill = bar[1]
                if mode == "s1_pure":
                    dollars = eq / S1_N
                else:
                    qty_r = RISK_FRAC * eq / r_dollars if r_dollars else 0
                    dollars = min(qty_r * fill, MAX_NOTIONAL_FRAC * eq)
                dollars = min(dollars, cash, max(0.0, limit - invested))
                if dollars <= 1.0:
                    continue
                qty = dollars * (1 - cost_side) / fill
                cash -= dollars
                invested += dollars
                r = r_dollars if stops else 0.0
                book[sym] = Pos(sym, qty, fill, r,
                                fill - r if r else 0.0,
                                fill + 2 * r if r else float("inf"),
                                False, d)
        pending_entry = []

        # 4. intraday exit stack
        if stops:
            for p in list(book.values()):
                i, bar = bar_today(p.sym, d)
                if not bar or p.sym not in book:
                    continue
                _, o, h, l, c, v = bar
                if p.r:
                    if o <= p.stop:                    # gap through the stop
                        close_out(p, o, 1.0, "STOP", d)
                        continue
                    if l <= p.stop:
                        close_out(p, p.stop, 1.0, "STOP", d)
                        continue
                    if not p.half_done:
                        if o >= p.tp:
                            close_out(p, o, 0.5, "TP", d)
                            p.half_done = True
                        elif h >= p.tp:
                            close_out(p, p.tp, 0.5, "TP", d)
                            p.half_done = True
            # EOD: trail ratchet + time stop
            for p in list(book.values()):
                i, bar = bar_today(p.sym, d)
                if bar and p.r:
                    p.stop = max(p.stop, inds[p.sym].low20[i])
                if (d - p.entry_date).days >= TIME_STOP_DAYS:
                    pending_exit.append((p.sym, "TIME"))

        # 5. Friday decisions
        if d in frs:
            if rotation:
                ramp_reentry = (not bear and cap < 1.0
                                and len(book) < S1_N)
                if d in rot_fridays or ramp_reentry:
                    rows = ranked(d)
                    decile = {s for s, _ in rows[:max(1, -(-len(rows) // 10))]}
                    top = [s for s, _ in rows[:S1_N]]
                    for p in list(book.values()):
                        if p.sym not in decile:
                            pending_exit.append((p.sym, "ROTATE"))
                    exiting = {s for s, _ in pending_exit}
                    slots = S1_N - (len(book) - len(exiting))
                    for sym in top:
                        if slots <= 0:
                            break
                        if sym in book and sym not in exiting:
                            continue
                        i = series[sym].idx_at(d)
                        r = 2 * inds[sym].atr14[i] if stops else 0.0
                        pending_entry.append((sym, r, "ROTATE"))
                        slots -= 1
            elif not bear:
                rows = ranked(d)
                decile = rows[:max(1, -(-len(rows) // 10))]
                cands = signal(d, decile, inds, series, consumed, events)
                taken = 0
                for sym, r_dollars in cands:
                    if taken >= SETUP_MAX_ENTRIES or sym in book:
                        continue
                    pending_entry.append((sym, r_dollars, "SETUP"))
                    taken += 1

        curve.append((d, equity(d)))
        prev_d = d
    return curve, trades, events


# ---------------------------------------------------------------- signals --

def s2_signal(d, decile, inds, series, consumed, events):
    out = []
    for sym, rs in decile:
        ind = inds[sym]
        ser = series[sym]
        i = ser.idx_at(d)
        if i is None or ser.dates[i] != d or i < 120:
            continue
        c = ind.closes[i]
        if not (c > ind.sma100[i] > 0 and ind.sma100[i] > ind.sma100[i - 20]):
            continue
        depth = 1 - c / ind.high20c[i]
        if not (PULLBACK[0] <= depth <= PULLBACK[1]):
            continue
        if abs(c / ind.sma20[i] - 1) > NEAR_MEAN:
            continue
        if c <= ser.bars[i - 1][2]:                    # reclaim bar
            continue
        out.append((sym, 2 * ind.atr14[i]))
    return out


def s3_signal(d, decile, inds, series, consumed, events):
    out = []
    for sym, rs in decile:
        ind = inds[sym]
        ser = series[sym]
        i = ser.idx_at(d)
        if i is None or ser.dates[i] != d:
            continue
        hole = gambit_vol.find_hole_at(ser.bars, i, ind.holes)
        if hole is None:
            continue
        if hole.status == "BREAKDOWN":
            events["VOLHOLE_BREAKDOWN"] += 1          # journal-only, no action
            continue
        if hole.status != "BREAKOUT":
            continue
        zone = (sym, hole.cluster_start)
        if zone in consumed:
            continue
        # first close above the upper bound since the cluster ended
        b = None
        for j in range(hole.cluster_end + 1, i + 1):
            if ind.closes[j] > hole.upper:
                b = j
                break
        if b is None or i - b > BREAKOUT_RECENCY - 1:
            continue
        if ser.bars[b][5] <= VOL_EXPANSION * ind.medvol20[b]:
            continue
        consumed.add(zone)
        out.append((sym, 2 * ind.atr14[i]))
    return out


ARMS = (("S1-pure", "s1_pure", None),
        ("S1-stopped", "s1_stop", None),
        ("S2 pullback", "setup", s2_signal),
        ("S3 vol-hole", "setup", s3_signal))
