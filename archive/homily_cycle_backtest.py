#!/usr/bin/env python3
"""
#178 · A cycle exit for commodity-cycle names (memory · storage · semicap)
=========================================================================

PRD §5r follow-up (Danny's memory post: "charting … until we see a clear
trend reversal"). Never-sell was measured on a growth book. Memory is a
commodity cycle whose P/E is LOWEST at peak earnings, so §5.2's
fundamental gate cannot fire at the top, and DRAM/SNDK/MU were 64% of the
account's October–November 2026 loss. Question: does exiting a cyclical
when the FROZEN monthly trend turns not-up (and re-entering when it turns
up) beat holding through the cycle?

PRE-REGISTERED 2026-11-09, written before the first run (Part III r6):

  names   MU · AMAT · LRCX · KLAC · WDC · STX (Yahoo adjclose; a name
          enters a window only if it has ≥12 monthly closes before the
          window opens — STX misses C1, recorded, not patched)
  signal  `monthly_up` exactly as homily_danny computes it — last monthly
          close > EMA10 of monthly closes AND EMA10 rising — read on
          COMPLETED month-ends only (homily_clone.ema, the frozen engine)
  arms    HOLD: equal dollars per name at the window open, never sold.
          EXIT: same dollars; at each month-end close a name with
          monthly_up False is sold to cash (0%), a name back to True is
          re-bought; 10 bps per trade.
  windows four memory busts, fixed by calendar before the run:
            C1 2000-01 → 2003-12   C2 2007-01 → 2010-12
            C3 2018-01 → 2021-12   C4 2022-01 → latest close
          plus rolling 5y windows opening each January 2000–2021,
          REPORTED for robustness, never the verdict
  gate    a cycle PASSES iff EXIT MOIC ≥ HOLD MOIC AND EXIT MaxDD ≥ HOLD
          MaxDD + 0.10 (MaxDD are negative fractions). #178 PASSES iff
          ≥3 of the 4 cycles pass. Anything else → NULL.

Caveats that travel: survivorship (Qimonda, Elpida, Spansion are not on
Yahoo, which FLATTERS HOLD); n≈4 cycles, so even a PASS is a direction,
not a rate; the windows are hindsight-chosen busts by construction, which
is why the rolling 5y set is printed beside them.

Reproduce: python homily_cycle_backtest.py
"""
import datetime

from homily_data import fetch_series
from homily_clone import ema

NAMES = ("MU", "AMAT", "LRCX", "KLAC", "WDC", "STX")
COST = 0.001
CYCLES = (("C1", datetime.date(2000, 1, 1), datetime.date(2003, 12, 31)),
          ("C2", datetime.date(2007, 1, 1), datetime.date(2010, 12, 31)),
          ("C3", datetime.date(2018, 1, 1), datetime.date(2021, 12, 31)),
          ("C4", datetime.date(2022, 1, 1), datetime.date(2099, 1, 1)))


def month_ends(bars, adj):
    """[(date of last session, adj close)] per calendar month."""
    out = {}
    for b, a in zip(bars, adj):
        out[(b[0].year, b[0].month)] = (b[0], a)
    return [out[k] for k in sorted(out)]


def monthly_up(closes):
    """homily_danny's rule on a list of completed monthly closes."""
    if len(closes) < 12:
        return False
    e = ema(closes, 10)
    return closes[-1] > e[-1] and e[-1] > e[-2]


def run_window(series, w0, w1):
    """series: {name: [(date, close)] month-ends}. -> (hold, exit) dicts
    with moic/maxdd, or None if no name qualifies."""
    names = [n for n, s in series.items()
             if sum(1 for d, _ in s if d < w0) >= 12
             and any(w0 <= d <= w1 for d, _ in s)]
    if not names:
        return None
    months = sorted({d for n in names for d, _ in series[n] if w0 <= d <= w1})
    px = {n: dict(series[n]) for n in names}
    hist = {n: [c for d, c in series[n] if d < w0] for n in names}
    hold = {n: 1.0 / len(names) / hist[n][-1] for n in names}
    ex_sh = {}
    ex_cash = 0.0
    for n in names:
        if monthly_up(hist[n]):
            ex_sh[n] = (1.0 / len(names)) * (1 - COST) / hist[n][-1]
        else:
            ex_cash += 1.0 / len(names)
    last = {n: hist[n][-1] for n in names}
    path_h, path_e = [1.0], [1.0]
    for d in months:
        for n in names:
            if d in px[n]:
                last[n] = px[n][d]
                hist[n].append(px[n][d])
        vh = sum(hold[n] * last[n] for n in names)
        ve = ex_cash + sum(sh * last[n] for n, sh in ex_sh.items())
        path_h.append(vh)
        path_e.append(ve)
        for n in names:                       # decide at this month-end
            if d not in px[n]:
                continue
            up = monthly_up(hist[n])
            if n in ex_sh and not up:
                ex_cash += ex_sh.pop(n) * last[n] * (1 - COST)
            elif n not in ex_sh and up and ex_cash > 0:
                stake = min(ex_cash, ve / len(names))
                ex_sh[n] = stake * (1 - COST) / last[n]
                ex_cash -= stake

    def dd(p):
        peak, worst = p[0], 0.0
        for v in p:
            peak = max(peak, v)
            worst = min(worst, v / peak - 1)
        return worst
    return ({"moic": path_h[-1], "maxdd": dd(path_h), "n": len(names)},
            {"moic": path_e[-1], "maxdd": dd(path_e), "n": len(names)})


def main():
    series = {}
    for n in NAMES:
        bars, adj = fetch_series(n, rng="max")
        series[n] = month_ends(bars, adj)
    print("#178 cycle exit — EXIT on frozen monthly_up vs HOLD, equal $ "
          "per name, 10 bps")
    passed = 0
    for tag, w0, w1 in CYCLES:
        r = run_window(series, w0, w1)
        if r is None:
            print(f"  {tag}: no qualifying names")
            continue
        h, e = r
        ok = e["moic"] >= h["moic"] and e["maxdd"] >= h["maxdd"] + 0.10
        passed += ok
        print(f"  {tag} {w0}→{min(w1, datetime.date.today())} (n={h['n']}):"
              f" HOLD {h['moic']:.2f} dd{h['maxdd']*100:.0f}% · EXIT"
              f" {e['moic']:.2f} dd{e['maxdd']*100:.0f}% → "
              + ("pass" if ok else "fail"))
    print("\n  rolling 5y (robustness, not the verdict):")
    wins = 0
    tot = 0
    for y in range(2000, 2022):
        r = run_window(series, datetime.date(y, 1, 1),
                       datetime.date(y + 4, 12, 31))
        if r is None:
            continue
        h, e = r
        tot += 1
        wins += e["moic"] >= h["moic"]
        print(f"    {y}–{y+4}: HOLD {h['moic']:5.2f} dd{h['maxdd']*100:4.0f}%"
              f" · EXIT {e['moic']:5.2f} dd{e['maxdd']*100:4.0f}%")
    print(f"    EXIT ≥ HOLD on MOIC in {wins}/{tot} rolling windows")
    print(f"\n== #178 PRE-REGISTERED VERDICT: {passed}/4 cycles pass → "
          + ("PASS (info-only tag first; promotion R10)" if passed >= 3
             else "NULL") + " ==")


if __name__ == "__main__":
    main()
