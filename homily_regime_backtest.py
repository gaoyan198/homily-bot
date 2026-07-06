#!/usr/bin/env python3
"""
Regime timing vs buy-and-hold — SPY (1993→) and QQQ (1999→).
============================================================

Strategy: at each month end, hold the index if its close > 10-month SMA,
else hold cash (0% yield — conservative; T-bills would flatter the timing
side). 5bps cost per switch. No look-ahead: month t's position is decided
at the close of month t-1... i.e. returns of month t accrue to the position
chosen from data through month t-1.

Also reports each major bear episode so the "sell signal" value is visible
where it matters, and the bull-market lag cost where it hurts.
"""
from homily_regime import fetch_monthly

COST = 0.0005
EPISODES = [
    ("dot-com   2000-09→2002-09", 2000, 9, 2002, 9),
    ("GFC       2007-10→2009-02", 2007, 10, 2009, 2),
    ("COVID     2020-01→2020-03", 2020, 1, 2020, 3),
    ("infl bear 2022-01→2022-09", 2022, 1, 2022, 9),
    ("bull run  2023-01→2025-12", 2023, 1, 2025, 12),
]


def run(sym):
    m = fetch_monthly(sym)[:-1]              # completed months only
    dates = [d for d, _ in m]
    px = [c for _, c in m]
    n = len(px)
    eq_bh, eq_st = [1.0], [1.0]
    pos, switches, cash_months = 1, 0, 0
    pos_hist = []
    for i in range(10, n - 1):
        want = 1 if px[i] > sum(px[i - 9:i + 1]) / 10 else 0
        if want != pos:
            eq_st[-1] *= (1 - COST); switches += 1; pos = want
        r = px[i + 1] / px[i]
        eq_bh.append(eq_bh[-1] * r)
        eq_st.append(eq_st[-1] * (r if pos else 1.0))
        cash_months += (pos == 0)
        pos_hist.append((dates[i + 1], pos))
    yrs = (n - 11) / 12
    stats = lambda eq: (
        (eq[-1]) ** (1 / yrs) - 1,
        min(eq[j] / max(eq[:j + 1]) - 1 for j in range(1, len(eq))))
    return dates[10:], px[10:], eq_bh, eq_st, stats(eq_bh), stats(eq_st), \
        switches, cash_months, yrs, pos_hist


def episode(dates, eq, y1, mo1, y2, mo2):
    idx = [i for i, d in enumerate(dates)
           if (d.year, d.month) >= (y1, mo1) and (d.year, d.month) <= (y2, mo2)]
    if not idx or idx[0] == 0:
        return None
    return eq[idx[-1]] / eq[idx[0] - 1] - 1


if __name__ == "__main__":
    for sym in ("SPY", "QQQ"):
        dates, px, eq_bh, eq_st, (bh_c, bh_dd), (st_c, st_dd), sw, cm, yrs, ph = run(sym)
        print(f"\n{sym} — {yrs:.0f}y monthly, 10m-SMA timing vs buy&hold "
              f"({sw} switches, {100*cm/len(ph):.0f}% months in cash)")
        print(f"  {'':14}{'CAGR':>8}{'MaxDD':>8}{'$1 -> ':>10}")
        print(f"  {'buy & hold':<14}{bh_c*100:>7.1f}%{bh_dd*100:>7.0f}%"
              f"{eq_bh[-1]:>9.1f}")
        print(f"  {'10m-SMA timed':<14}{st_c*100:>7.1f}%{st_dd*100:>7.0f}%"
              f"{eq_st[-1]:>9.1f}")
        print("  episodes (strategy vs B&H total return):")
        for name, y1, mo1, y2, mo2 in EPISODES:
            b = episode(dates, eq_bh, y1, mo1, y2, mo2)
            s = episode(dates, eq_st, y1, mo1, y2, mo2)
            if b is None:
                continue
            print(f"    {name:<28} timed {s*100:>7.1f}%   B&H {b*100:>7.1f}%")
