#!/usr/bin/env python3
"""
Danny-style concentration: ~90% of the book in a top-4 core.
============================================================

User constraint: full-time job, can't execute a many-name dip screen.
Danny's structure: 85% in top 3 / 90% in top 4, rest satellites. This
backtests the CORE-4 discipline: $1/month, split equally across the four
core names at each month's first close (10bps). Executable in five minutes
a month.

Three cores, July 2021 → now:
  D4   Danny's literal four — NVDA PLTR AMD HOOD. PURE HINDSIGHT: we know
       in 2026 these won; in July 2021 HOOD was a fresh meme-IPO. Upper
       bound, not a strategy.
  E4f  Engine-picked four, chosen ONCE at the start using only data
       available then (conviction score over the loser-salted 2021 control
       universe), held fixed. Tests: could the score have picked winners
       before knowing them?
  E4r  Same, but re-picked every July (sell dropped names, proceeds into
       the new ones). The realistic, executable version — one decision a
       year.

Benchmarks: same $1/month DCA'd into SPY / QQQ. NAV unit accounting for
time-weighted CAGR and real MaxDD. No regime overlay (see §5 of the docs:
full liquidation halved returns in this window).
"""
from homily_data import fetch_daily
from homily_danny import danny_signal
from homily_conviction import conviction
from homily_strategy_backtest import month_first_idx, close_on, run_dca, UNIV_B

COST = 0.001
DANNY4 = ["NVDA", "PLTR", "AMD", "HOOD"]
POOL = sorted(set(UNIV_B + ["NVDA", "AMD", "HOOD", "TSLA", "TSM", "AVGO"]))


def pick4(names, data, spy_bars, d):
    """Top 4 by conviction score, point-in-time at date d (gates as filter
    first, score-ranked; fill from non-gated by score if fewer than 4)."""
    spy = [b[4] for b in spy_bars if b[0] <= d]
    scored = []
    for n in names:
        bars = [b for b in data[n] if b[0] <= d]
        if len(bars) < 200:
            continue
        try:
            c = conviction(danny_signal(n, bars), bars, spy)
        except Exception:
            continue
        scored.append((c.gates_ok, c.score, n))
    scored.sort(key=lambda x: (-x[0], -x[1]))
    return [n for _, _, n in scored[:4]]


def run_core(core_fn, data, spy, label_dates):
    months = [spy[i][0] for i in month_first_idx(spy)][1:]
    core = core_fn(months[0])
    picks_log = [(months[0], list(core))]
    hold, cash, units, unit_val = {}, 0.0, 0.0, 1.0
    nav = []
    for d in months:
        if d in label_dates and d != months[0]:          # annual re-pick
            new = core_fn(d)
            if set(new) != set(core):
                freed = 0.0
                for n in [x for x in core if x not in new]:
                    px = close_on(data[n], d)
                    if px and n in hold:
                        freed += hold.pop(n) * px * (1 - COST)
                added = [x for x in new if x not in core]
                for n in added:
                    px = close_on(data[n], d)
                    if px:
                        hold[n] = hold.get(n, 0) + freed / len(added) / px
                picks_log.append((d, list(new)))
            core = new
        val = cash + sum(sh * (close_on(data[n], d) or 0)
                         for n, sh in hold.items())
        if units > 0:
            unit_val = val / units
        nav.append(unit_val)
        cash += 1.0
        units += 1.0 / unit_val
        live = [n for n in core if close_on(data[n], d)]
        if live:
            per = cash * (1 - COST) / len(live)
            for n in live:
                hold[n] = hold.get(n, 0) + per / close_on(data[n], d)
            cash = 0.0
    d_end = spy[-1][0]
    final = cash + sum(sh * (close_on(data[n], d_end) or 0)
                       for n, sh in hold.items())
    nav.append(final / units)
    yrs = len(months) / 12
    cagr = (nav[-1] / nav[0]) ** (1 / yrs) - 1
    mdd = min(nav[j] / max(nav[:j + 1]) - 1 for j in range(1, len(nav)))
    return final / len(months), cagr, mdd, picks_log


if __name__ == "__main__":
    spy = fetch_daily("SPY", rng="10y")
    spy5 = [b for b in spy if b[0] >= fetch_daily("SPY", rng="5y")[0][0]]
    qqq = fetch_daily("QQQ", rng="5y")
    data = {}
    for n in set(POOL + DANNY4):
        try:
            data[n] = fetch_daily(n, rng="10y")
        except Exception:
            pass
    julys = {spy5[i][0] for i in month_first_idx(spy5)
             if spy5[i][0].month == 7}

    print(f"window: {spy5[0][0]} -> {spy5[-1][0]}  ($1/month core-4, 10bps)")
    print(f"\n{'':38}{'MOIC':>6}{'TWR CAGR':>10}{'MaxDD':>8}")
    for label, ix in (("DCA SPY (benchmark)", spy5), ("DCA QQQ (benchmark)", qqq)):
        m, c, dd = run_dca(ix, spy5)
        print(f"{label:<38}{m:>6.2f}{c*100:>9.1f}%{dd*100:>7.0f}%")

    m, c, dd, _ = run_core(lambda d: DANNY4, data, spy5, set())
    print(f"{'D4  Danny4 fixed (PURE HINDSIGHT)':<38}{m:>6.2f}{c*100:>9.1f}%{dd*100:>7.0f}%")

    pool = [n for n in POOL if n in data]
    m, c, dd, log = run_core(
        lambda d, _f=[None]: _f[0] or _f.__setitem__(0, pick4(pool, data, spy, d)) or _f[0],
        data, spy5, set())
    print(f"{'E4f engine-picked once, 2021, fixed':<38}{m:>6.2f}{c*100:>9.1f}%{dd*100:>7.0f}%")
    print(f"     picked in 2021: {', '.join(log[0][1])}")

    m, c, dd, log = run_core(lambda d: pick4(pool, data, spy, d),
                             data, spy5, julys)
    print(f"{'E4r engine-picked, re-pick each July':<38}{m:>6.2f}{c*100:>9.1f}%{dd*100:>7.0f}%")
    for d, picks in log:
        print(f"     {d}: {', '.join(picks)}")
