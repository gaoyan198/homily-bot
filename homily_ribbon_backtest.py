#!/usr/bin/env python3
"""
Ribbon run-length study (#82, PRD §5k) — how long does a weekly-RED run last?
=============================================================================

Danny's "ribbon" is a regime run: "big red candles open bullish runs
lasting weeks to months". That is a run-length claim, and the digest
already prints "weekly RED 8w" with no base rate — the owner can't tell
how much accumulate-window typically remains. This measures the historical
distribution of weekly-RED spell lengths, per universe, by calling the
LIVE `homily_circle` on weekly-close prefixes (R6 — prefix EMA/MACD equal
the full-series values, so this is exactly what the digest would have
printed each week).

Two questions, decision rules pre-committed here before the run:

  1. Base rate: median / p25 / p75 / p90 completed-spell length. The digest
     line ships the COMBINED median ("RED 8w · median run Nw"), info-only.
  2. Entry-candle conditioning ("big red candles open runs..."): spells
     split by entry-week return above/below the pooled median. Conditioning
     is adopted ONLY if the big-entry median exceeds the small-entry median
     by >= 3 weeks IN THE SAME DIRECTION on both universes — otherwise the
     unconditional base rate ships alone (PRD #82's own rule).

Open (right-censored) spells are excluded from the distribution and
counted separately — including them would bias run lengths short.
"""
from homily_clone import homily_circle
from homily_data import fetch_daily, weekly_closes
from homily_strategy_backtest import UNIV_A, UNIV_B

WARMUP_W = 40          # weeks before the 30w SMA/regime engine is credible

# Committed output of the 2026-07-11 run (see BACKTEST_RESULTS §7):
# median completed weekly-RED spell, both universes combined. daily_run
# reads this for the info-only base-rate suffix on RED rows.
RED_MEDIAN_RUN_W = 8


def circles(tk, wk):
    """Weekly circle colour per week, live engine on prefixes (R6)."""
    return [homily_circle(tk, wk[:i + 1]).circle
            for i in range(WARMUP_W, len(wk))]


def spells(tk, wk):
    """-> (completed [(length, entry_return)], open_length or None)."""
    cs = circles(tk, wk)
    out, run, entry = [], 0, None
    for j, c in enumerate(cs):
        if c == "RED":
            if run == 0:
                i = WARMUP_W + j     # absolute week index of the entry week
                entry = wk[i] / wk[i - 1] - 1 if i > 0 else 0.0
            run += 1
        elif run:
            out.append((run, entry))
            run = 0
    return out, (run if run else None)


def dist(lengths):
    if not lengths:
        return None
    xs = sorted(lengths)
    q = lambda p: xs[min(len(xs) - 1, int(p * (len(xs) - 1) + 0.5))]
    return {"n": len(xs), "median": q(0.5), "p25": q(0.25), "p75": q(0.75),
            "p90": q(0.9), "mean": sum(xs) / len(xs)}


def fmt(d):
    return (f"n={d['n']:>4}  median {d['median']:>3}w  "
            f"p25 {d['p25']:>3}w  p75 {d['p75']:>3}w  p90 {d['p90']:>3}w  "
            f"mean {d['mean']:.1f}w") if d else "n=0"


if __name__ == "__main__":
    univ_all = UNIV_A + [n for n in UNIV_B if n not in UNIV_A]
    per_univ = {"A current": [], "B hype-2021": []}
    open_runs, dead = 0, []
    for sym in univ_all:
        try:
            wk = weekly_closes(fetch_daily(sym, rng="max"))
        except Exception:
            dead.append(sym)
            continue
        if len(wk) < WARMUP_W + 30:
            dead.append(sym)
            continue
        comp, open_len = spells(sym, wk)
        open_runs += open_len is not None
        if sym in UNIV_A:
            per_univ["A current"].extend(comp)
        if sym in UNIV_B:
            per_univ["B hype-2021"].extend(comp)
        print(f"  {sym:<6} {len(wk):>5}w history  {len(comp):>3} completed "
              f"spells" + (f"  (open: {open_len}w)" if open_len else ""),
              flush=True)

    print(f"\nRibbon run-length study (#82) — weekly-RED spells, max history,"
          f" live circle engine" + (f" (unfetchable/short: {', '.join(dead)})"
                                    if dead else ""))
    combined = per_univ["A current"] + per_univ["B hype-2021"]
    med_split = sorted(e for _, e in combined)[len(combined) // 2]
    for g, sp in (*per_univ.items(), ("COMBINED", combined)):
        lens = [l for l, _ in sp]
        print(f"\n{g} ({'pooled' if g == 'COMBINED' else 'universe'})")
        print(f"  all entries      {fmt(dist(lens))}")
        big = [l for l, e in sp if e > med_split]
        small = [l for l, e in sp if e <= med_split]
        print(f"  big-entry  (>{med_split * 100:+.1f}%)  {fmt(dist(big))}")
        print(f"  small-entry      {fmt(dist(small))}")

    da = dist([l for l, _ in per_univ["A current"]])
    db = dist([l for l, _ in per_univ["B hype-2021"]])
    ba = dist([l for l, e in per_univ["A current"] if e > med_split])
    sa = dist([l for l, e in per_univ["A current"] if e <= med_split])
    bb = dist([l for l, e in per_univ["B hype-2021"] if e > med_split])
    sb = dist([l for l, e in per_univ["B hype-2021"] if e <= med_split])
    adopt = (ba and sa and bb and sb
             and ba["median"] - sa["median"] >= 3
             and bb["median"] - sb["median"] >= 3)
    dc = dist([l for l, _ in combined])
    print(f"\n{open_runs} spells still open (right-censored, excluded).")
    print(f"Pre-committed rule: entry-size conditioning ships only if the "
          f"big-entry median beats the small-entry median by >=3w on BOTH "
          f"universes -> {'ADOPT split' if adopt else 'UNCONDITIONAL only'}.")
    print(f"Digest base rate (combined median): {dc['median']}w — commit as "
          f"RED_MEDIAN_RUN_W (currently {RED_MEDIAN_RUN_W}).")
