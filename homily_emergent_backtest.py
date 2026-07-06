#!/usr/bin/env python3
"""
Emergent concentration — Danny's actual mechanic, tested.
=========================================================

User's (correct) observation: Danny never *picked* a top-4 core. He buys
dips only on names whose trend is intact, never sells in a bull market, and
the compounders naturally GROW into 85–90% of the book. Concentration is an
output, not an input.

This replays exactly that on the loser-salted 2021 control universe
(July 2021 → now, $1/month, 10bps, point-in-time, never sell):

  EQ  equal-weight adds     — monthly cash split equally across the names
                              currently ⭐ ACCUMULATE (fallback 🔵).
  CW  conviction-weight adds — same candidates, but cash weighted by their
                              point-in-time conviction score (Danny sizes
                              with conviction; losers-in-trend get less).

Reported: MOIC / TWR / MaxDD vs SPY & QQQ DCA, plus the emergent
concentration — final and peak top-3 / top-4 share of the book — to see if
the 85/90% structure appears by itself.
"""
from homily_data import fetch_daily
from homily_danny import danny_signal
from homily_conviction import conviction
from homily_strategy_backtest import (month_first_idx, close_on, run_dca,
                                      UNIV_B, COST)


def run_emergent(names, data, spy, weighted, min_bars=260):
    months = [spy[i][0] for i in month_first_idx(spy)][1:]
    spy_px = [b[4] for b in spy]
    hold, cash = {}, 0.0
    nav, units, unit_val = [], 0.0, 1.0
    top4_peak = 0.0
    for d in months:
        val = cash + sum(sh * (close_on(data[n], d) or 0)
                         for n, sh in hold.items())
        if units > 0:
            unit_val = val / units
        nav.append(unit_val)
        cash += 1.0
        units += 1.0 / unit_val

        cands, backs = [], []
        for n in names:
            bars = [b for b in data[n] if b[0] <= d]
            if len(bars) < min_bars:
                continue
            try:
                sig = danny_signal(n, bars)
            except Exception:
                continue
            if sig.state == "ACCUMULATE":
                cands.append((n, sig, bars))
            elif sig.state == "BOTTOMING":
                backs.append((n, sig, bars))
        picks = cands or backs
        if picks and cash > 0:
            if weighted:
                spy_pt = [p for b, p in zip(spy, spy_px) if b[0] <= d]
                w = {n: max(1, conviction(sig, bars, spy_pt).score)
                     for n, sig, bars in picks}
            else:
                w = {n: 1.0 for n, _, _ in picks}
            tot = sum(w.values())
            for n, _, _ in picks:
                px = close_on(data[n], d)
                if px:
                    hold[n] = hold.get(n, 0) + cash * (1 - COST) * w[n] / tot / px
            cash = 0.0
        # emergent concentration this month
        vals = sorted((sh * (close_on(data[n], d) or 0)
                       for n, sh in hold.items()), reverse=True)
        tot_v = sum(vals) + cash
        if tot_v > 12 and vals:                     # once the book is real
            top4_peak = max(top4_peak, sum(vals[:4]) / tot_v)

    d_end = spy[-1][0]
    final_by = {n: sh * (close_on(data[n], d_end) or 0)
                for n, sh in hold.items()}
    final = cash + sum(final_by.values())
    nav.append(final / units)
    yrs = len(months) / 12
    cagr = (nav[-1] / nav[0]) ** (1 / yrs) - 1
    mdd = min(nav[j] / max(nav[:j + 1]) - 1 for j in range(1, len(nav)))
    ranked = sorted(final_by.items(), key=lambda kv: -kv[1])
    top3 = sum(v for _, v in ranked[:3]) / final
    top4 = sum(v for _, v in ranked[:4]) / final
    return (final / len(months), cagr, mdd, top3, top4, top4_peak,
            ranked[:6], len(final_by))


if __name__ == "__main__":
    spy = fetch_daily("SPY", rng="5y")
    qqq = fetch_daily("QQQ", rng="5y")
    data = {}
    for n in UNIV_B:
        try:
            data[n] = fetch_daily(n, rng="5y")
        except Exception:
            pass
    live = [n for n in UNIV_B if n in data]

    print(f"window: {spy[0][0]} -> {spy[-1][0]}  ($1/month, never sell)")
    print(f"\n{'':30}{'MOIC':>6}{'TWR':>7}{'MaxDD':>7}{'top3':>6}{'top4':>6}{'pk4':>5}{'names':>6}")
    for label, ix in (("DCA SPY", spy), ("DCA QQQ", qqq)):
        m, c, dd = run_dca(ix, spy)
        print(f"{label:<30}{m:>6.2f}{c*100:>6.1f}%{dd*100:>6.0f}%{'—':>6}{'—':>6}{'—':>5}{'—':>6}")
    for label, wt in (("EQ equal-weight dips", False),
                      ("CW conviction-weighted dips", True)):
        m, c, dd, t3, t4, pk, top, nn = run_emergent(live, data, spy, wt)
        print(f"{label:<30}{m:>6.2f}{c*100:>6.1f}%{dd*100:>6.0f}%"
              f"{t3*100:>5.0f}%{t4*100:>5.0f}%{pk*100:>4.0f}%{nn:>6}")
        top_s = ", ".join(f"{n} {v:.1f}" for n, v in top)
        print(f"    final book ($ per name): {top_s}")
