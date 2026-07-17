#!/usr/bin/env python3
"""
#51 — ⚪ time-stop calibration (PLAYBOOK §5.2's 12-week constant).
==================================================================

§5.2 ("⚪ CAUTION 12+ weeks + F:0–1 → sell half") is the ONE per-name exit
with a measured, attributable edge (~3 pts/yr on the wreck-salted control,
BACKTEST_RESULTS D-63 mode (f)). Its 12-week constant was DECLARED, never
calibrated (#67's provenance registry) — this study prices it.

Machinery: D-63's `run_mode(..., "perstock", caution_months=w)` verbatim —
point-in-time signals on bar prefixes, $1/month, 10 bps, fund-unit NAV.
Same caveat as the committed mode-(f) tables: the F:0–1 fundamental gate is
NOT modelled (fundamentals aren't point-in-time), so every cell is the
AGGRESSIVE bound on the exit; the comparison across w is like-for-like.

DECISION RULE (frozen here, before any run):

    Grid: w ∈ {1, 2, 3, 4, 6} completed months in ⚪ before selling half
    (3 ≈ the incumbent 12 weeks; the 0.5 sell fraction is §5.2's own
    constant and is NOT under study). Windows: 5y and 10y, universes A
    (hindsight, reported not trusted) and B (honest control).

    A challenger w is ADOPTABLE only if, versus the incumbent w=3:
      (a) it wins MOIC on BOTH universe-B windows (the honest control),
      (b) it is not worse on both universe-A windows simultaneously, and
      (c) MaxDD stays within +5 pts everywhere.
    If several pass, the one CLOSEST to the incumbent wins (minimal
    change; distance ties go to the smaller w). Anything less = NULL: the
    12w constant stays, the grid table is recorded in BACKTEST_RESULTS,
    and the item closes. PLAYBOOK §5.2 is edited ONLY by a later gated
    promotion session (R10) — never by this study.

Gate: the rule above; a null closed honestly is a successful run.
"""
from homily_data import fetch_daily
from homily_bear_backtest import run_mode, _fetch
from homily_strategy_backtest import UNIV_A, UNIV_B, run_dca

GRID_W = (1, 2, 3, 4, 6)          # completed ⚪ months; 3 = incumbent
INCUMBENT = 3


def grid_table(names, data, spy, qqq, tag):
    print(f"\n{tag}")
    print(f"{'time-stop':<14}{'MOIC':>6}{'CAGR':>9}{'MaxDD':>8}{'trades':>8}")
    for label, ix in (("DCA SPY", spy), ("DCA QQQ", qqq)):
        m, c, dd = run_dca(ix, spy)
        print(f"{'  ' + label:<14}{m:>6.2f}{c*100:>8.1f}%{dd*100:>7.0f}%{'—':>8}")
    out = {}
    for w in GRID_W:
        m, c, dd, _, tr = run_mode(names, data, spy, qqq, "perstock",
                                   index_bars=spy, caution_months=w)
        mark = "  <- incumbent (12w)" if w == INCUMBENT else ""
        print(f"  w={w} (~{w*4}wk){'':<3}{m:>6.2f}{c*100:>8.1f}%"
              f"{dd*100:>7.0f}%{tr:>8}{mark}", flush=True)
        out[w] = (m, c, dd)
    return out


def main():
    results = {}
    for rng in ("5y", "10y"):
        spy = fetch_daily("SPY", rng=rng)
        qqq = fetch_daily("QQQ", rng=rng)
        for univ, names in (("B", UNIV_B), ("A", UNIV_A)):
            data, dead = _fetch(names, rng)
            live = [n for n in names if n in data]
            tag = (f"[{univ} · {rng}] {spy[0][0]} → {spy[-1][0]}"
                   + (f"  (dead: {', '.join(dead)})" if dead else ""))
            results[(univ, rng)] = grid_table(live, data, spy, qqq, tag)

    # decision rule, mechanically applied
    inc = {k: v[INCUMBENT] for k, v in results.items()}
    passing = []
    for w in GRID_W:
        if w == INCUMBENT:
            continue
        beats_b = all(results[("B", r)][w][0] > inc[("B", r)][0]
                      for r in ("5y", "10y"))
        worse_a_both = all(results[("A", r)][w][0] < inc[("A", r)][0]
                           for r in ("5y", "10y"))
        dd_ok = all(results[(u, r)][w][2] >= inc[(u, r)][2] - 0.05
                    for u in ("A", "B") for r in ("5y", "10y"))
        if beats_b and not worse_a_both and dd_ok:
            passing.append(w)
    if passing:
        best = min(passing, key=lambda w: (abs(w - INCUMBENT), w))
        print(f"\nRULE: PASS — w={best} (~{best*4} weeks) is the minimal-change"
              f" winner (passing: {passing}). Adoption is a LATER gated"
              " promotion session (R10); §5.2 unchanged today.")
    else:
        print("\nRULE: NULL — no challenger cleared all three clauses; the"
              " declared 12-week constant stays. Recorded, item closes.")


if __name__ == "__main__":
    main()
