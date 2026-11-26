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
import sys
from homily_clone import homily_circle, ema
from homily_data import fetch_daily, weekly_closes, weekly_ohlcv
from homily_strategy_backtest import UNIV_A, UNIV_B
from homily_vol import find_hole, MAX_GAP, VOL_WIN

WARMUP_W = 40          # weeks before the 30w SMA/regime engine is credible

# Committed output of the 2026-07-11 run (see BACKTEST_RESULTS §7):
# median completed weekly-RED spell, both universes combined. daily_run
# reads this for the info-only base-rate suffix on RED rows.
RED_MEDIAN_RUN_W = 8


# ---------------------------------------------------------------------------
# #143 · the descending-blue-ribbon primitive + the conjunction study
# (PRD §5o/§8.3 #143, DESIGNS D-143). Lives here, not in a new module:
# the census is at its cap (#116) and this is #82's harness, the ribbon's
# existing home. `homily_clone` stays FROZEN — this only reads its `ema`.
#
# RULE — FROZEN BEFORE THE FIRST RUN (do not renegotiate after numbers):
#
#   Ribbon (Danny's colours; red ribbon = mid-term uptrend, blue =
#   protracted downtrend): on weekly closes, blue ⇔ EMA10 < EMA30;
#   descending ⇔ EMA30 below its prior-week value; slope = EMA30 w/w
#   change. The same definition §5o measured (blue 48.6%, blue+descending
#   45.0% of 13,028 weekly observations); the run re-publishes both.
#   Bars: COMPLETED weekly OHLCV (`homily_data.weekly_ohlcv`) from 10y
#   daily; decision at week t's close, forward return from that close.
#   VH APPEARS at week t ⇔ live `find_hole` on the weekly prefix
#   (ref_win 60, max_age 52 — #77's weekly settings) returns a hole whose
#   cluster ends AT t (age 0) and no hole cluster ended in the prior
#   MAX_GAP weeks (a growing cluster is one event, not several). This is
#   Danny's stage-1 "a volatility hole appears", not its later resolution.
#   Arms, per week t: CONJ = VH appears + blue + descending · VH-ONLY =
#   VH appears, not (blue+descending) · RIB-ONLY = blue + descending, no
#   VH appearing · NEITHER · BASE = every week (unconditional).
#   Horizons: 6 / 13 / 26 weeks (Danny's "6 weeks to 6 months").
#   Universes: A (current) and B (hype-2021 control) per
#   homily_strategy_backtest, overlap names counted in both; ALL = union.
#
#   VERDICT (pre-registered): PASS iff
#     (i)  n(CONJ events with a 26w forward) ≥ 30 on ALL, and
#     (ii) on BOTH universe A and universe B, at BOTH 6w and 26w, mean
#          fwd(CONJ) > mean fwd of each of VH-ONLY, RIB-ONLY and BASE.
#   The PRD row says "on the honest universe"; requiring both universes is
#   the STRICTER reading, chosen here before the run (a gate may tighten
#   before a read, never loosen after). Anything else = NULL: the ribbon
#   stays a score component and #165/#167 use the primitive only as a
#   definition, never as evidence that it times bottoms. No digest
#   surface ships from the study session (Part III rule 5).
# ---------------------------------------------------------------------------
RIB_FAST, RIB_SLOW = 10, 30
VH_REF_W, VH_AGE_W = 60, 52
CONJ_FWD_W = (6, 13, 26)


def ribbon_state(weekly_closes):
    """-> (blue, descending, slope) at the LAST weekly close, or None when
    there is too little history. Read-only; `homily_clone.ema` unchanged."""
    if len(weekly_closes) < RIB_SLOW + 2:
        return None
    fast, slow = ema(weekly_closes, RIB_FAST), ema(weekly_closes, RIB_SLOW)
    slope = slow[-1] / slow[-2] - 1
    return fast[-1] < slow[-1], slow[-1] < slow[-2], slope


def vh_appears(wk_bars):
    """Week indices where a NEW weekly hole cluster first prints (frozen
    rule above). Point-in-time: prefix calls only."""
    out, last_end = [], None
    for i in range(VH_REF_W + VOL_WIN + 5, len(wk_bars)):
        h = find_hole(wk_bars[:i + 1], ref_win=VH_REF_W, max_age=VH_AGE_W)
        if h is None:
            continue
        end = i - h.age
        if h.age == 0 and (last_end is None or end - last_end > MAX_GAP):
            out.append(i)
        last_end = end
    return out


def conjunction_rows(wk_bars):
    """[(arm, {h: fwd})] for every week with a defined ribbon."""
    cl = [b[4] for b in wk_bars]
    app = set(vh_appears(wk_bars))
    rows = []
    for i in range(VH_REF_W + VOL_WIN + 5, len(cl)):
        st = ribbon_state(cl[:i + 1])
        if st is None:
            continue
        blue, desc, _ = st
        rib, vh = blue and desc, i in app
        arm = ("CONJ" if vh and rib else "VH-ONLY" if vh else
               "RIB-ONLY" if rib else "NEITHER")
        fw = {h: cl[i + h] / cl[i] - 1 for h in CONJ_FWD_W if i + h < len(cl)}
        rows.append((arm, blue, fw))
    return rows


def conjunction_study():
    univ_all = UNIV_A + [n for n in UNIV_B if n not in UNIV_A]
    per, dead = {}, []
    for sym in univ_all:
        try:
            per[sym] = conjunction_rows(weekly_ohlcv(fetch_daily(sym, rng="10y")))
        except Exception:
            dead.append(sym)
    groups = {"A current": [s for s in UNIV_A if s in per],
              "B hype-2021": [s for s in UNIV_B if s in per],
              "ALL": [s for s in univ_all if s in per]}
    avg = lambda xs: sum(xs) / len(xs) if xs else float("nan")
    win = lambda xs: 100 * sum(x > 0 for x in xs) / len(xs) if xs else float("nan")
    allrows = [r for s in groups["ALL"] for r in per[s]]
    nb = sum(1 for _, b, _ in allrows if b)
    nbd = sum(1 for a, _, _ in allrows if a in ("CONJ", "RIB-ONLY"))
    print(f"#143 descending-blue-ribbon conjunction — {len(groups['ALL'])} "
          f"names, 10y weekly (completed bars)"
          + (f"; unfetchable: {', '.join(dead)}" if dead else ""))
    print(f"base rates over {len(allrows):,} weekly obs: blue "
          f"{100 * nb / len(allrows):.1f}% · blue+descending "
          f"{100 * nbd / len(allrows):.1f}%  (§5o measured 48.6% / 45.0%)")
    means = {}
    for g, syms in groups.items():
        rows = [r for s in syms for r in per[s]]
        print(f"\n{g}")
        print(f"  {'arm':<9}" + "".join(f"{'n':>7}{str(h) + 'w':>8}{'win':>6}"
                                        for h in CONJ_FWD_W))
        for arm in ("CONJ", "VH-ONLY", "RIB-ONLY", "NEITHER", "BASE"):
            sel = [fw for a, _, fw in rows if arm == "BASE" or a == arm]
            line = f"  {arm:<9}"
            for h in CONJ_FWD_W:
                xs = [fw[h] for fw in sel if h in fw]
                means[(g, arm, h)] = (avg(xs), len(xs))
                line += f"{len(xs):>7}{avg(xs) * 100:>7.1f}%{win(xs):>5.0f}%"
            print(line)
    n_conj = means[("ALL", "CONJ", 26)][1]
    beats = {(g, h): all(means[(g, "CONJ", h)][0] > means[(g, o, h)][0]
                         for o in ("VH-ONLY", "RIB-ONLY", "BASE"))
             for g in ("A current", "B hype-2021") for h in (6, 26)}
    ok = n_conj >= 30 and all(beats.values())
    print(f"\nVerdict (pre-registered): n(CONJ, 26w) on ALL = {n_conj} "
          f"({'≥' if n_conj >= 30 else '<'} 30); CONJ beats VH-ONLY, "
          "RIB-ONLY and BASE —")
    for (g, h), b in beats.items():
        print(f"  {g:<12} {h:>2}w  {'yes' if b else 'NO'}")
    print(f"-> {'PASS' if ok else 'NULL'}")
    return ok


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


if __name__ == "__main__" and "--conjunction" in sys.argv:
    conjunction_study()
elif __name__ == "__main__":
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
