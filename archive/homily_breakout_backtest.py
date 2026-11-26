#!/usr/bin/env python3
"""
Breakout-add anatomy (#105, PRD §5l) — Danny's OTHER entry class, tested.
=========================================================================

His NVDA buy-signal post (Jun 7 2025): a close above the longest
momentum bars is a momentum buy, valid only with an updated
whale-accumulation read. Our engine owns exactly one entry class — the
dip at chip support (⭐ / WHALE-DIP). This tests the opposite motion on
our own furniture:

    EVENT (all point-in-time, live functions only):
      close[i] > R0(bars[:i])         first close above the nearest major
      close[i-1] <= R0(bars[:i-1])    overhead shelf, where R0 = prior-day
                                      profile's resistance[0] — the shelf a
                                      live rule could actually have watched
                                      (the same-day profile would already
                                      have reclassified a broken shelf as
                                      support), from the top-8 strongest
                                      de-duplicated peaks
      + 🐳 within 10 sessions         whale_read on the prefix, same-day
                                      convention the live engine uses,
                                      probed i, i-1, … i-9, first hit wins

    COMPARATORS: (a) DCA baseline — unconditional forward return of every
    eligible day, same names; (b) ⭐-dip adds — the first cut-day of each
    ACCUMULATE spell on the weekly grid (live danny_signal, D-20/#107
    convention), the "add moment" of our existing entry class.

    RISK: per-event worst forward drawdown from entry within 120d
    (events with <60 fwd days excluded from DD stats), median and p10 —
    the 2021 control's DD row is where breakout-chasing should die if
    it is hype-chasing.

Pre-committed pass bar (PRD row #104-adjacent, #105 — verbatim): PASS =
beats the DCA baseline on fwd-60d in BOTH universes AND the universe-B
median worst-forward-DD of breakout events is <= that of the ⭐-dip
entries. On PASS the ship is an info-only `⤴` row tag proposal (≤2%
WHALE-DIP framing, own session, own gate; budget/copilot untouched
without an R10 slot). On FAIL either leg → NULL, closed, recorded.
"""
from homily_chips import build_profile
from homily_danny import danny_signal
from homily_data import fetch_daily
from homily_strategy_backtest import UNIV_A, UNIV_B
from homily_whale import whale_read

FWD = (20, 60, 120)
WARMUP = 300
GRID = 5
WARMUP_W = 60
WHALE_LOOK = 10
DD_WIN, DD_MIN = 120, 60


def r0(bars_prefix):
    p = build_profile(bars_prefix)
    return p.resistance[0][0] if p.resistance else None


def whale_near(bars, i, look=WHALE_LOOK):
    for j in range(i, max(i - look, 0) - 1, -1):
        pre = bars[:j + 1]
        p = build_profile(pre)
        sh = p.support[0][0] if p.support else None
        if whale_read(pre, sh).whale:
            return True
    return False


def breakout_events(bars):
    closes = [b[4] for b in bars]
    out, prev_above = [], None
    for i in range(WARMUP, len(bars)):
        ref = r0(bars[:i])
        above = ref is not None and closes[i] > ref
        if above and prev_above is False and whale_near(bars, i):
            out.append(i)
        prev_above = above if ref is not None else None
    return out


def star_entries(sym, bars):
    """First cut-day of each ⭐ spell on the weekly grid (live engine)."""
    out, prev = [], False
    for i in range(WARMUP_W * GRID, len(bars), GRID):
        st = danny_signal(sym, bars[:i + 1]).state == "ACCUMULATE"
        if st and not prev:
            out.append(i)
        prev = st
    return out


def fwd_ret(closes, i, n):
    if i + n >= len(closes):
        return None
    return closes[i + n] / closes[i] - 1


def worst_dd(closes, i):
    end = min(i + DD_WIN, len(closes) - 1)
    if end - i < DD_MIN:
        return None
    return min(closes[j] / closes[i] - 1 for j in range(i + 1, end + 1))


def scan(names, label):
    ev = {n: [] for n in FWD}
    star = {n: [] for n in FWD}
    base = {n: [] for n in FWD}
    ev_dd, star_dd, dead, n_ev, n_st = [], [], [], 0, 0
    for sym in names:
        try:
            bars = fetch_daily(sym, rng="5y")
        except Exception:
            dead.append(sym)
            continue
        closes = [b[4] for b in bars]
        if len(closes) < WARMUP + 80:
            dead.append(sym)
            continue
        for i in range(WARMUP, len(closes)):
            for n in FWD:
                r = fwd_ret(closes, i, n)
                if r is not None:
                    base[n].append(r)
        bo = breakout_events(bars)
        se = star_entries(sym, bars)
        n_ev += len(bo)
        n_st += len(se)
        for src, rets, dds in ((bo, ev, ev_dd), (se, star, star_dd)):
            for i in src:
                for n in FWD:
                    r = fwd_ret(closes, i, n)
                    if r is not None:
                        rets[n].append(r)
                d = worst_dd(closes, i)
                if d is not None:
                    dds.append(d)
        print(f"  {sym:<6} breakouts {len(bo):>3}  ⭐entries {len(se):>3}",
              flush=True)
    return dict(label=label, ev=ev, star=star, base=base, ev_dd=ev_dd,
                star_dd=star_dd, dead=dead, n_ev=n_ev, n_st=n_st)


AVG = lambda xs: sum(xs) / len(xs) if xs else float("nan")
WIN = lambda xs: 100 * sum(x > 0 for x in xs) / len(xs) if xs else float("nan")


def q(xs, p):
    if not xs:
        return float("nan")
    s = sorted(xs)
    return s[min(len(s) - 1, int(p * (len(s) - 1) + 0.5))]


def report(r):
    print(f"\n{r['label']}  ({r['n_ev']} breakout events / {r['n_st']} ⭐ "
          f"entries" + (f"; unfetchable/short: {', '.join(r['dead'])}"
                        if r["dead"] else "") + ")")
    print(f"{'arm':<14}{'fwd':>5}{'avg ret':>9}{'win%':>7}{'n':>6}")
    for arm, rets in (("BREAKOUT+🐳", r["ev"]), ("⭐-dip entry", r["star"]),
                      ("DCA baseline", r["base"])):
        for n in FWD:
            xs = rets[n]
            print(f"{arm:<14}{n:>4}d{AVG(xs)*100:>8.1f}%{WIN(xs):>6.0f}%"
                  f"{len(xs):>6}")
    print(f"worst fwd-DD (120d):  breakout median {AVG([q(r['ev_dd'],0.5)])*100:.1f}% "
          f"p10 {q(r['ev_dd'],0.1)*100:.1f}%   ⭐ median {q(r['star_dd'],0.5)*100:.1f}% "
          f"p10 {q(r['star_dd'],0.1)*100:.1f}%")


if __name__ == "__main__":
    ra = scan(UNIV_A, "A current univ (HINDSIGHT BIAS)")
    rb = scan([s for s in UNIV_B if s not in UNIV_A], "B hype-2021 control")
    for r in (ra, rb):
        report(r)
    beat_a = AVG(ra["ev"][60]) > AVG(ra["base"][60])
    beat_b = AVG(rb["ev"][60]) > AVG(rb["base"][60])
    dd_ok = q(rb["ev_dd"], 0.5) >= q(rb["star_dd"], 0.5)
    print(f"\nPre-committed pass bar:")
    print(f"  beats DCA fwd-60d, universe A: {'YES' if beat_a else 'NO'} "
          f"({AVG(ra['ev'][60])*100:.1f}% vs {AVG(ra['base'][60])*100:.1f}%)")
    print(f"  beats DCA fwd-60d, universe B: {'YES' if beat_b else 'NO'} "
          f"({AVG(rb['ev'][60])*100:.1f}% vs {AVG(rb['base'][60])*100:.1f}%)")
    print(f"  control median DD breakout <= ⭐: {'YES' if dd_ok else 'NO'} "
          f"({q(rb['ev_dd'],0.5)*100:.1f}% vs {q(rb['star_dd'],0.5)*100:.1f}%)")
    ok = beat_a and beat_b and dd_ok
    print(f"VERDICT: {'PASS — ⤴ tag proposal earns its own gated session' if ok else 'NULL — closed, nothing ships'}")
