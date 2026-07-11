#!/usr/bin/env python3
"""
Right-stock discipline gate (#66, design D-66) — can Q separate the wrecks
from the recovered greats, using only what was filed at the time?
==========================================================================

Test 1 — wreck separation (MUST pass first; pre-committed rule below).
As-of 2021-11-01 (the top): Q for every US name in both universes from
filings FILED on/before that date plus 3y RS to that date. Outcome =
forward 24m return from the 2021-11-01 close. PASS iff
    mean fwd24m(Q1) − mean fwd24m(Q3) ≥ 20 pts
    AND ≥ 60% of the canonical wreck list scores ≤ Q2
    AND ≥ 75% of the canonical recovered-great list scores Q1.
(A second as-of, 2022-07-01, is printed to show how fast Q catches on —
information, not the gate.) If test 1 fails: the Q label may still print
(labels are free) but 💎 and the veto STAY DEAD — close honestly.

Test 3 regression (the over-blocking guard): PLTR as-of 2026-06-01 must
score ≥ Q2 — Danny's June add was RIGHT and a veto that would have blocked
it fails the standard regardless of anything else.

Test 2 (💎 event study) and the full veto count run with `--replay`: dip
days (state ⚪, point-in-time) split by Q-tier-at-the-time; fwd 252d vs
unfiltered ⚪ dips and the all-days baseline. 💎 becomes buyable ONLY if
it beats both — and any ship is a future session either way (rule 5).
"""
import datetime

from homily_data import fetch_daily
from homily_quality import fetch_facts, q_points, tier_of, rs3y_of
from homily_strategy_backtest import UNIV_A, UNIV_B

ASOF = datetime.date(2021, 11, 1)
ASOF2 = datetime.date(2022, 7, 1)
FWD_M = 24
WRECKS = ["PTON", "ZM", "DOCU", "ROKU", "TDOC", "LCID", "AFRM", "UPST",
          "BYND", "W"]
GREATS = ["NVDA", "META", "AMD", "NFLX", "CRWD", "SHOP", "UBER"]


def close_at(bars, d):
    px = None
    for b in bars:
        if b[0] <= d:
            px = b[4]
        else:
            break
    return px


def fwd_24m(bars, d):
    p0 = close_at(bars, d)
    p1 = close_at(bars, d.replace(year=d.year + 2))
    return p1 / p0 - 1 if p0 and p1 else None


if __name__ == "__main__":
    import sys
    spy = fetch_daily("SPY", rng="max")
    spy_cl = [b[4] for b in spy]
    univ = sorted(set(UNIV_A) | set(UNIV_B))

    rows = []
    for tk in univ:
        try:
            bars = fetch_daily(tk, rng="max")
        except Exception:
            continue
        facts = fetch_facts(tk)
        if facts is None:
            continue
        out = {"tk": tk, "fwd": fwd_24m(bars, ASOF)}
        for label, asof in (("q21", ASOF), ("q22", ASOF2)):
            pit = [b[4] for b in bars if b[0] <= asof]
            spy_pit = [b[4] for b, c in zip(spy, spy_cl) if b[0] <= asof]
            rs = rs3y_of(pit, spy_pit)
            qp = q_points(facts, asof, rs)
            out[label] = tier_of(qp[0]) if qp else None
            out[label + "_pts"] = qp[0] if qp else None
        if out["q21"]:
            rows.append(out)
        print(f"  {tk:<6} Q@2021-11 {out.get('q21') or '—'} "
              f"({out.get('q21_pts')})  Q@2022-07 {out.get('q22') or '—'}"
              f"  fwd24m {out['fwd'] * 100:+.0f}%" if out.get("fwd") is not None
              else f"  {tk:<6} Q@2021-11 {out.get('q21') or '—'} (no fwd)",
              flush=True)

    print(f"\n#66 Test 1 — wreck separation, as-of {ASOF} "
          f"(filings filed ≤ as-of; {len(rows)} scoreable names)")
    print(f"{'tier':<6}{'n':>4}{'mean fwd24m':>13}{'median':>9}")
    means = {}
    for tier in ("Q1", "Q2", "Q3"):
        xs = sorted(r["fwd"] for r in rows
                    if r["q21"] == tier and r["fwd"] is not None)
        if xs:
            means[tier] = sum(xs) / len(xs)
            print(f"{tier:<6}{len(xs):>4}{means[tier] * 100:>+12.1f}%"
                  f"{xs[len(xs) // 2] * 100:>+8.1f}%")
        else:
            print(f"{tier:<6}{0:>4}{'—':>13}{'—':>9}")

    by_tk = {r["tk"]: r for r in rows}
    wr_ok = [tk for tk in WRECKS
             if by_tk.get(tk, {}).get("q21") in ("Q2", "Q3")]
    gr_ok = [tk for tk in GREATS if by_tk.get(tk, {}).get("q21") == "Q1"]
    wr_have = [tk for tk in WRECKS if tk in by_tk]
    gr_have = [tk for tk in GREATS if tk in by_tk]
    print(f"\nwrecks ≤Q2: {len(wr_ok)}/{len(wr_have)} "
          f"({', '.join(f"{tk}:{by_tk[tk]['q21']}" for tk in wr_have)})")
    print(f"greats =Q1: {len(gr_ok)}/{len(gr_have)} "
          f"({', '.join(f'{tk}:{by_tk[tk]['q21']}' for tk in gr_have)})")
    sep = (means.get("Q1") is not None and means.get("Q3") is not None
           and means["Q1"] - means["Q3"] >= 0.20)
    p1 = sep and len(wr_ok) >= 0.6 * len(wr_have) \
        and len(gr_ok) >= 0.75 * len(gr_have)
    print(f"\nPRE-COMMITTED RULE: Q1−Q3 mean gap ≥20pts "
          f"({(means.get('Q1', float('nan')) - means.get('Q3', float('nan'))) * 100:+.1f}) "
          f"AND wrecks≤Q2 ≥60% AND greats=Q1 ≥75%")
    print(f"TEST 1 VERDICT: {'PASS — 💎/veto studies may proceed (their own gates)' if p1 else 'FAIL — label prints, everything downstream stays dead'}")

    # Test 3 regression: the veto must NOT have blocked Danny's June PLTR add
    pltr_bars = fetch_daily("PLTR", rng="max")
    asof3 = datetime.date(2026, 6, 1)
    pit = [b[4] for b in pltr_bars if b[0] <= asof3]
    spy_pit = [b[4] for b in spy if b[0] <= asof3]
    qp = q_points(fetch_facts("PLTR"), asof3, rs3y_of(pit, spy_pit))
    t = tier_of(qp[0]) if qp else "—"
    print(f"\nTest 3 regression — PLTR as-of {asof3}: {t} ({qp[0] if qp else '—'} pts) "
          f"→ {'veto would NOT have blocked (correct)' if t in ('Q1', 'Q2') else 'veto WOULD have blocked — over-blocking, veto fails regardless'}")
