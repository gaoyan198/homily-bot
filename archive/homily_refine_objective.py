#!/usr/bin/env python3
"""
Refine-loop re-point (#21, design D-21) — the objective the circle is FOR.
==========================================================================

`homily_refine.py` tunes circle params for hold-🔴/cut-⚪ Calmar — a
strategy §1 retired. The circle's live job is gating composite states, so
the objective it is tuned on should score exactly that:

    J(p) = mean over basket[ mean fwd-60d excess of ⭐(p) days ]
           − λ · FB(p)

⭐(p) day = monthly trend UP · weekly circle(p) RED · price at/near the
top chip-support shelf (the composite's ACCUMULATE condition; the 🔵 VH
upgrade is p-independent and deliberately outside the objective). The
excess is vs the SAME NAME's unconditional fwd-60d drift over the segment
(isolates timing skill from name selection). FB(p) = fraction of ⚪(p)
days (monthly down OR circle(p) WHITE) followed by ≥+15% in 60d — the
false-block penalty, i.e. the PLTR-June failure class as a first-class
term. λ = 0.5, NEVER tuned on outcome; the diagnostic prints the param
RANKING at λ ∈ {0.25, 0.5, 1.0} and the objective is trusted only while
the ranking is stable across all three.

D-21 order of operations, honoured here:
  1. `--diagnostic` — pooled ⭐-day counts per walk-forward fold. If a
     fold pools <100 obs the ⭐ objective is unstable → J falls back to
     scoring RED-regime days (more obs, same spirit). The diagnostic run
     IS its own deliverable; the fallback decision is committed to the log
     header, not improvised later.
  2. 30-day parallel run — `log_parallel()` (called by daily_refine with
     the bars the digest already fetched) appends J(champion) and
     J(challenger) to `homily_refine_j.csv`, a SIBLING append-only file:
     the Calmar log keeps its history byte-identical (R2 — new fields
     live in a new file rather than widening old rows). Champion
     selection stays Calmar until the parallel read (≥2026-08-22, 30
     rows) shows no adoption-flapping; the switch is its own session.
"""
import os
import datetime

from homily_clone import ema, sma, macd
from homily_chips import build_profile
from homily_data import weekly_closes
from homily_danny import NEAR_SUPPORT_PCT

HERE = os.path.dirname(os.path.abspath(__file__))
J_LOG = os.path.join(HERE, "homily_refine_j.csv")
J_HEADER = ("date,params,j_lam050,star_days,fb_rate,fallback_red\n")

LAM = 0.5
FB_GAIN = 0.15          # a ⚪ day followed by ≥+15% in 60d = false block
FWD = 60
TEST_SPLIT = 0.6        # J is judged on the last 40%, like the Calmar loop
MIN_FOLD_OBS = 100      # D-21: below this per fold -> RED-day fallback
BASKET_J = ("NVDA", "TSLA", "PLTR", "META", "AMD", "SHOP", "NET", "CRWD")

# Set by the 2026-07-11 --diagnostic run (BACKTEST_RESULTS §13): folds
# pooled 479/1012/736 ⭐-days — all ≥ MIN_FOLD_OBS, so the ⭐ objective
# stands and no RED-day fallback is needed. Same run's λ read: rankings
# IDENTICAL at λ=0.25/0.5, reshuffled at λ=1.0 — λ stays 0.5 (fixed a
# priori, never tuned) and the future switch session must weigh that the
# ranking is FB-sensitive at high λ before trusting any J-selected champion.
FALLBACK_RED = False


def circle_series_p(closes, p):
    """Weekly circle colour per week under params p — the same arithmetic
    homily_refine.circle_series_p pins, kept in lock-step by validate."""
    e_f, e_s, s_s = ema(closes, p["ef"]), ema(closes, p["es"]), \
        sma(closes, p["es"])
    line, _, hist = macd(closes)
    out = []
    for i in range(len(closes)):
        sc = ((closes[i] > e_s[i]) + (e_f[i] > e_s[i])
              + (hist[i] > 0 and line[i] > 0)
              + (s_s[i] is not None and i >= 4 and s_s[i - 4] is not None
                 and s_s[i] > s_s[i - 4]))
        out.append("RED" if sc >= 3 else ("WHITE" if sc <= 1 else "AMBER"))
    return out


PROFILE_STRIDE = 5      # chip profile recomputed every N days; the shelf is
                        # cached between. Against a 60-day-half-life
                        # histogram a ≤4-day-stale shelf is noise, and the
                        # 5× saving is what lets the parallel log ride the
                        # daily CI run instead of doubling it. An
                        # OBJECTIVE-side approximation only — the live
                        # signal path is untouched.


def day_context(bars):
    """The p-INDEPENDENT per-day series, computed once and reused by every
    param set: (monthly_up[i], near_support[i], week_index[i]). This is
    the expensive pass (a chip profile per PROFILE_STRIDE days)."""
    m_up, near, wk_ix = [], [], []
    wk_keys, cur = [], None
    mo, mo_key = [], None
    shelf = None
    for i in range(len(bars)):
        d = bars[i][0]
        k = d.isocalendar()[:2]
        if k != cur:
            wk_keys.append(k)
            cur = k
        wk_ix.append(len(wk_keys) - 1)
        mk = (d.year, d.month)
        if mk != mo_key:
            mo.append(bars[i][4])
            mo_key = mk
        else:
            mo[-1] = bars[i][4]
        e10m = ema(mo, 10)
        m_up.append(len(mo) >= 12 and mo[-1] > e10m[-1]
                    and e10m[-1] > e10m[-2])
        if i % PROFILE_STRIDE == 0:
            prof = build_profile(bars[:i + 1])
            shelf = prof.support[0][0] if prof.support else None
        near.append(shelf is not None
                    and bars[i][4] <= shelf * (1 + NEAR_SUPPORT_PCT / 100))
    return m_up, near, wk_ix


def j_of(bars, ctx, p, lam=LAM, span=None, fallback_red=None):
    """J terms for ONE name over day range `span` (default: the test
    segment). -> (mean_star_excess or None, n_star, fb_rate, n_block)."""
    if fallback_red is None:
        fallback_red = FALLBACK_RED
    closes = [b[4] for b in bars]
    m_up, near, wk_ix = ctx
    wcirc = circle_series_p(weekly_closes(bars), p)
    n = len(bars)
    lo, hi = span if span else (int(n * TEST_SPLIT), n - FWD)
    hi = min(hi, n - FWD)
    fwd = [closes[i + FWD] / closes[i] - 1 if i + FWD < n else None
           for i in range(n)]
    seg = [r for r in (fwd[i] for i in range(lo, hi)) if r is not None]
    drift = sum(seg) / len(seg) if seg else 0.0
    stars, blocks, fb = [], 0, 0
    for i in range(lo, hi):
        c = wcirc[wk_ix[i]]
        star = (m_up[i] and c == "RED"
                and (True if fallback_red else near[i]))
        if star and fwd[i] is not None:
            stars.append(fwd[i] - drift)
        if (not m_up[i]) or c == "WHITE":
            if fwd[i] is not None:
                blocks += 1
                fb += fwd[i] >= FB_GAIN
    mean_star = sum(stars) / len(stars) if stars else None
    return mean_star, len(stars), (fb / blocks if blocks else 0.0), blocks


def j_basket(bars_map, p, lam=LAM, ctx_cache=None, fallback_red=None):
    """J(p) over the basket names available in bars_map. -> (J, star_days,
    fb_rate, names_used). ctx_cache maps name -> day_context output."""
    ex, ns, fbs, used = [], 0, [], 0
    for tk in BASKET_J:
        bars = bars_map.get(tk)
        if not bars or len(bars) < 500:
            continue
        ctx = ctx_cache.setdefault(tk, day_context(bars)) \
            if ctx_cache is not None else day_context(bars)
        m, n, fb, _ = j_of(bars, ctx, p, lam, fallback_red=fallback_red)
        if m is not None:
            ex.append(m)
            ns += n
            fbs.append(fb)
            used += 1
    if not ex:
        return None, 0, 0.0, 0
    return (sum(ex) / len(ex) - lam * (sum(fbs) / len(fbs)),
            ns, sum(fbs) / len(fbs), used)


def log_parallel(bars_map, champ_p, chal_p, day=None, path=J_LOG):
    """The 30-day parallel run's daily row(s): J for champion and
    challenger, appended to the sibling log. Idempotent per (date,
    params): a same-day re-run replaces nothing and appends nothing."""
    day = day or datetime.date.today()
    if not os.path.exists(path):
        with open(path, "w") as f:
            f.write(J_HEADER)
    with open(path) as f:
        seen = {tuple(ln.split(",")[:2]) for ln in f.read().splitlines()[1:]}
    ctx_cache = {}
    rows = []
    for p in (champ_p, chal_p):
        key = (day.isoformat(), str(p).replace(",", ";"))
        if key in seen:
            continue
        j, ns, fb, used = j_basket(bars_map, p, ctx_cache=ctx_cache)
        if j is None:
            continue
        rows.append(f"{key[0]},{key[1]},{j:.5f},{ns},{fb:.4f},"
                    f"{int(FALLBACK_RED)}\n")
        seen.add(key)
    if rows:
        with open(path, "a") as f:
            f.writelines(rows)
    return len(rows)


if __name__ == "__main__":
    import sys
    from homily_data import fetch_daily
    from homily_refine import GRID, DEFAULT, load_champion

    bars_map = {}
    for tk in BASKET_J:
        try:
            bars_map[tk] = fetch_daily(tk, rng="5y")
        except Exception:
            pass
    print(f"basket: {sorted(bars_map)} ({len(bars_map)}/{len(BASKET_J)})")

    if "--diagnostic" in sys.argv:
        # D-21 step 1 — do NOT skip to the objective.
        ctx_cache = {}
        print("\n1 · pooled ⭐-day counts per walk-forward fold "
              f"(DEFAULT params, need ≥{MIN_FOLD_OBS}/fold):")
        for f0, f1, lbl in ((0.2, 0.47, "fold1"), (0.47, 0.73, "fold2"),
                            (0.73, 1.0, "fold3")):
            pooled = 0
            for tk, bars in bars_map.items():
                ctx = ctx_cache.setdefault(tk, day_context(bars))
                n = len(bars)
                _, ns, _, _ = j_of(bars, ctx, DEFAULT,
                                   span=(int(n * f0), int(n * f1)),
                                   fallback_red=False)
                pooled += ns
            print(f"  {lbl}: {pooled} ⭐-days pooled "
                  f"{'OK' if pooled >= MIN_FOLD_OBS else '< MIN — RED fallback'}")

        print("\n2 · λ ranking stability on the test segment "
              "(top-5 params by J at each λ):")
        for lam in (0.25, 0.5, 1.0):
            scored = []
            for p in GRID:
                j, ns, fb, used = j_basket(bars_map, p, lam,
                                           ctx_cache=ctx_cache,
                                           fallback_red=False)
                if j is not None:
                    scored.append((j, str(p)))
            scored.sort(reverse=True)
            print(f"  λ={lam}: " + " · ".join(s for _, s in scored[:5]))

        champ = load_champion()
        for label, p in (("champion", champ["params"]), ("DEFAULT", DEFAULT)):
            j, ns, fb, used = j_basket(bars_map, p, ctx_cache=ctx_cache,
                                       fallback_red=False)
            print(f"\n  J({label} {p}) = {j:+.4f}  "
                  f"(⭐-days {ns}, FB {fb * 100:.1f}%, {used} names)")
    else:
        from homily_refine import search
        champ = load_champion()
        chal, _, _ = search()
        n = log_parallel(bars_map, champ["params"], chal)
        print(f"logged {n} parallel J row(s) to {os.path.basename(J_LOG)}")
