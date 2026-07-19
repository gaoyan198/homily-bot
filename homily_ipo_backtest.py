#!/usr/bin/env python3
"""
Below-IPO quality tag study (#111, PRD §5m) — Danny's valuation sourcing axis.
==============================================================================

His Apr-2025 Threads thread screened quality growers trading below their
IPO reference (ALAB, SNOW, OSCR, COIN) — and OSCR from that list became
his big 2026 winner. Our discovery screen is tape-first; no valuation
axis exists. This tests the sourcing claim on its own: is "trading below
the price the company first sold stock at" forward-informative for the
kind of names we screen, or is it just a value trap collector (PTON
below $29 forever)?

Data: `ipo_ref.json` — offer price (IPOs) / reference price (direct
listings) / $10 NAV (SPACs), hand-collected 2026-07-19, split-adjusted
to match Yahoo's adjusted closes (SHOP, ANET). Aggregate-study grade;
the file's own note says verify entries before trusting any single one.
Danny's thread also filtered on fundamentals (EV/S, growth); we have no
point-in-time fundamentals, so this tests the price condition ALONE —
recorded limitation, and any shipped tag would pair with the LIVE
`F:n/3` at display time.

Design: max-history daily bars, monthly grid (21 bars), first 250
post-listing bars skipped (price discovery/lockup year). Obs = below
(close < ref) vs the all-days baseline of the same names; fwd 6m/12m
(126/252 bars), dividends not counted on either side (R1 series).

Pre-committed verdict: the `IPO↓` discovery tag earns its own gated
session ONLY if below-IPO obs beat the all-days baseline at BOTH
horizons on the combined pool AND on the universe-B side alone (the
control side, where survivorship can't rescue it). Null → closed, the
data file stays for future studies.
"""
import json
import os
from homily_data import fetch_daily
from homily_strategy_backtest import UNIV_A, UNIV_B

FWD = {"6m": 126, "12m": 252}
GRID = 21
WARMUP = 250

REFS = {k: v for k, v in json.load(
    open(os.path.join(os.path.dirname(__file__), "ipo_ref.json"))).items()
    if not k.startswith("_")}


def fwd_ret(closes, i, n):
    if i + n >= len(closes):
        return None
    return closes[i + n] / closes[i] - 1


def scan():
    below = {u: {h: [] for h in FWD} for u in ("A", "B")}
    base = {u: {h: [] for h in FWD} for u in ("A", "B")}
    n_below = {u: 0 for u in ("A", "B")}
    dead = []
    for sym, meta in sorted(REFS.items()):
        try:
            bars = fetch_daily(sym, rng="max")
        except Exception:
            dead.append(sym)
            continue
        if len(bars) < WARMUP + 200:
            dead.append(sym)
            continue
        closes = [b[4] for b in bars]
        univs = [u for u, univ in (("A", UNIV_A), ("B", UNIV_B))
                 if sym in univ]
        if not univs:
            univs = ["A"]        # ipo_ref names outside both lists: A-side
        nb = 0
        for i in range(WARMUP, len(closes), GRID):
            rets = {h: fwd_ret(closes, i, n) for h, n in FWD.items()}
            if rets["6m"] is None:
                continue
            is_below = closes[i] < meta["ref"]
            nb += is_below
            for u in univs:
                for h in FWD:
                    if rets[h] is not None:
                        base[u][h].append(rets[h])
                        if is_below:
                            below[u][h].append(rets[h])
                if is_below:
                    n_below[u] += 1
        print(f"  {sym:<5} ref {meta['ref']:>7.2f}  below-obs {nb:>4}",
              flush=True)
    return below, base, n_below, dead


AVG = lambda xs: sum(xs) / len(xs) if xs else float("nan")
WIN = lambda xs: 100 * sum(x > 0 for x in xs) / len(xs) if xs else float("nan")


if __name__ == "__main__":
    below, base, n_below, dead = scan()
    comb_b = {h: below["A"][h] + below["B"][h] for h in FWD}
    comb_a = {h: base["A"][h] + base["B"][h] for h in FWD}
    print(f"\nBelow-IPO study — monthly grid, max history, {len(REFS)} refs"
          + (f" (unfetchable/short: {', '.join(dead)})" if dead else ""))
    print(f"{'pool':<26}{'fwd':>5}{'below':>9}{'win%':>7}{'baseline':>10}{'n below':>9}")
    for label, b_, a_ in (("A-side names", below["A"], base["A"]),
                          ("B-side names (control)", below["B"], base["B"]),
                          ("COMBINED", comb_b, comb_a)):
        for h in FWD:
            print(f"{label:<26}{h:>5}{AVG(b_[h])*100:>8.1f}%{WIN(b_[h]):>6.0f}%"
                  f"{AVG(a_[h])*100:>9.1f}%{len(b_[h]):>9}")
    ok = (all(AVG(comb_b[h]) > AVG(comb_a[h]) for h in FWD)
          and all(AVG(below["B"][h]) > AVG(base["B"][h]) for h in FWD))
    print("\nCaveats: price condition alone (no point-in-time fundamentals);"
          " dividends uncounted both sides; refs hand-collected.")
    print(f"Pre-committed verdict: IPO↓ tag earns a session only if below "
          f"beats baseline at both horizons combined AND on the B side -> "
          f"{'PASS' if ok else 'NULL — closed, nothing ships'}")
