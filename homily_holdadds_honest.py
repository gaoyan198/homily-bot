#!/usr/bin/env python3
"""
#125 HONEST-WINDOW re-test — the buy-day routine alone, no survivorship.
=======================================================================

Why this exists (owner, 2026-07-26): *"the 2.69x study is already old,
that's just buying stars during buy day"* — correct on both counts. §16b's
10y bar tested the OLD ⭐-only selection, and #125's own gate
(`homily_holdadds_backtest.py`) replayed the 2026-07-11 universe BACKWARDS,
so every name in it survived to be picked. Neither answers *"what do I get
if I follow the new buy day for ten years?"*

This does, on the repo's own honest control.

WHAT IS MEASURED — the buy-day routine and nothing else
  Monthly $1,000, 100% to stocks (the owner's SRS_COVERS_INDEX=true
  setting), split equally across the top-3 by RS12 among that arm's
  eligible set, **never sold**. No §5.2 exit, no §4 bear protocol, no
  time-stop. That is deliberately NOT §16b's strategy — §16b measured the
  full engine including the exits that are its best-measured arm. Read the
  two together, never interchangeably: this is the floor the picks alone
  deliver, before any selling discipline is applied.

ARMS
  OLD   state == ACCUMULATE (any tier)          — pre-#125
  NEW   tier == CONVICTION and state ACC|HOLD   — the live rule
  a month with no eligible name buys SPY (PLAYBOOK §3.5)

UNIVERSES (the whole point)
  B  hype-2021 control — THE HONEST ONE. What a growth investor plausibly
     held in mid-2021: winners AND still-listed wrecks (PTON, ZM, DOCU,
     ROKU, LCID, TDOC...). The list was NOT drawn from 2026 knowledge.
     Residual bias stated by homily_strategy_backtest and inherited here:
     fully delisted names cannot be fetched key-free, so the very worst
     outcomes are missing from B too.
  A  current bot universe — hindsight-picked 2026 winners. Reported for
     contrast only; any A number is upward-biased by construction.

WINDOWS  §16b's, so the rows sit next to each other:
  5y   2021-07-22 -> 2026-07-21      10y  2016-07-22 -> 2026-07-21
A name is only buyable on a date it has ≥260 bars of history by — no
buying a company before it listed.

REPORTED  MOIC (final value / dollars contributed), monthly-mark MaxDD,
and the same-months DCA SPY / DCA QQQ bars. Raw closes, dividends ignored,
consistently across every arm and benchmark.

This is a measurement, not a gate: #125 already shipped on its own
pre-registered gate. Nothing here can promote or demote anything — a
FAIL-shaped result is a finding to publish (and, if it contradicts §29,
an argument for the registry's demotion checker, which runs monthly on
live ledger rows and is the only thing allowed to reverse #125).

Reproduce:  python homily_holdadds_honest.py   (~5 min, ~65 fetches)
"""
import bisect
import datetime
import collections

from homily_data import fetch_series
from homily_danny import danny_signal
from homily_conviction import conviction
from homily_strategy_backtest import COST, UNIV_A, UNIV_B, month_first_idx

MONTHLY = 1000.0
MAX_PICKS = 3
MIN_BARS = 260
FIVE_Y = datetime.timedelta(days=365 * 5 + 1)
WINDOWS = [(datetime.date(2021, 7, 22), datetime.date(2026, 7, 21), "5y"),
           (datetime.date(2016, 7, 22), datetime.date(2026, 7, 21), "10y")]

RULES = {
    "OLD  (pre-#125, star-only)": lambda st, ti: st == "ACCUMULATE",
    "NEW  (#125 CONVICTION)": lambda st, ti: (ti == "CONVICTION"
                                              and st in ("ACCUMULATE",
                                                         "HOLD")),
}


def _win(bars, adj, i):
    lo = bisect.bisect_left([b[0] for b in bars], bars[i][0] - FIVE_Y)
    return bars[lo:i + 1], adj[lo:i + 1]


def signal_table(cache, buy_dates):
    """(date, ticker) -> (state, tier, rs12, close), point-in-time.
    Computed once and shared by every arm and window."""
    spy_bars, spy_adj = cache["SPY"]
    spy_dates = [b[0] for b in spy_bars]
    out = {}
    for t, (bars, adj) in sorted(cache.items()):
        if t in ("SPY", "QQQ"):
            continue
        dates = [b[0] for b in bars]
        for d in buy_dates:
            i = bisect.bisect_right(dates, d) - 1
            if i < MIN_BARS:
                continue                     # not listed / too little history
            if (d - dates[i]).days > 7:
                continue                     # stale: delisted or halted
            j = bisect.bisect_right(spy_dates, d) - 1
            b, a = _win(bars, adj, i)
            sb, sa = _win(spy_bars, spy_adj, j)
            try:
                s = danny_signal(t, b)
                c = conviction(s, b, [x[4] for x in sb], adj=a, spy_adj=sa)
            except Exception:                              # noqa: BLE001
                continue
            out[(d, t)] = (s.state, c.tier, c.rs12, b[-1][4])
    return out


def price_fn(cache):
    px = {t: ([b[0] for b in bars], [b[4] for b in bars])
          for t, (bars, _a) in cache.items()}

    def price(t, d):
        ds, cs = px[t]
        i = bisect.bisect_right(ds, d) - 1
        return cs[i] if i >= 0 else None
    return price


def run_arm(rule, names, sig, buy_dates, price, w0, w1, mark_dates):
    book = collections.defaultdict(float)
    contributed = 0.0
    peak = mdd = 0.0
    marks = {d: None for d in mark_dates}
    dates = sorted(set(buy_dates) | set(mark_dates))
    for d in dates:
        if d in set(buy_dates):
            cand = []
            for t in names:
                v = sig.get((d, t))
                if v and rule(v[0], v[1]):
                    cand.append((v[2], t, v[3]))
            cand.sort(key=lambda x: (-x[0], x[1]))
            picks = cand[:MAX_PICKS]
            contributed += MONTHLY
            if not picks:                                  # §3.5
                p = price("SPY", d)
                book["SPY"] += MONTHLY / (p * (1 + COST))
            else:
                for _rs, t, px0 in picks:
                    book[t] += (MONTHLY / len(picks)) / (px0 * (1 + COST))
        if d in marks and contributed:
            val = sum(sh * (price(t, d) or 0) for t, sh in book.items())
            r = val / contributed
            peak = max(peak, r)
            if peak:
                mdd = min(mdd, (r - peak) / peak * 100)
    val = sum(sh * (price(t, w1) or 0) for t, sh in book.items())
    return val / contributed, mdd, len(book)


def dca(ix, buy_dates, w1, price):
    sh = dep = 0.0
    for d in buy_dates:
        p = price(ix, d)
        if p:
            sh += MONTHLY / (p * (1 + COST))
            dep += MONTHLY
    return sh * price(ix, w1) / dep if dep else None


def main():
    names = sorted(set(UNIV_A) | set(UNIV_B))
    print(f"fetching {len(names) + 2} symbols …")
    cache = {}
    for t in names + ["SPY", "QQQ"]:
        try:
            cache[t] = fetch_series(t, rng="max")
        except Exception as e:                             # noqa: BLE001
            print(f"  skip {t}: {e!r:.50}")
    spy_bars = cache["SPY"][0]
    all_first = [spy_bars[i][0] for i in month_first_idx(spy_bars)]
    lo = min(w[0] for w in WINDOWS)
    buy_all = [d for d in all_first if lo <= d <= WINDOWS[0][1]]
    marks = buy_all
    print(f"computing point-in-time signals on {len(buy_all)} month-starts …")
    sig = signal_table(cache, buy_all)
    price = price_fn(cache)
    print(f"  {len(sig):,} name-days scored\n")

    for ulabel, univ in (("B hype-2021 control  << THE HONEST ONE", UNIV_B),
                         ("A current universe (hindsight-picked)", UNIV_A)):
        live = [n for n in univ if n in cache]
        print(f"=== UNIVERSE {ulabel}  ({len(live)} fetched) ===")
        print(f"{'window':<7}{'arm':<28}{'MOIC':>7}{'MaxDD':>8}"
              f"{'names':>7}{'  vs QQQ':>9}")
        for w0, w1, wl in WINDOWS:
            bd = [d for d in buy_all if w0 <= d <= w1]
            md = [d for d in marks if w0 <= d <= w1]
            q = dca("QQQ", bd, w1, price)
            s = dca("SPY", bd, w1, price)
            for alabel, rule in RULES.items():
                m, dd, n = run_arm(rule, live, sig, bd, price, w0, w1, md)
                print(f"{wl:<7}{alabel:<28}{m:>7.2f}{dd:>7.1f}%{n:>7}"
                      f"{'  BEATS' if m > q else '  loses':>9}")
            print(f"{wl:<7}{'DCA SPY':<28}{s:>7.2f}")
            print(f"{wl:<7}{'DCA QQQ  << the bar':<28}{q:>7.2f}")
            print()


if __name__ == "__main__":
    main()
