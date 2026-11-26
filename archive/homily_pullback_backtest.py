#!/usr/bin/env python3
"""
Pullback clock (#78, PRD §5k — Danny's KOSPI Jun 26 2026 claim).
================================================================

Claim under test: within an intact red ribbon a pullback "usually takes 3
to 7 trading days before the next strong bullish candle". Our reading: a
PULLBACK = a maximal run of consecutive non-RED *daily* candles while the
*weekly* circle stays RED. It ends one of three ways:

  resolved   a RED daily candle prints with the weekly circle still RED —
             the dip duration Danny is counting;
  failed     the weekly circle leaves RED mid-run — not a pullback but a
             trend failure (this is the class a data-driven early warning
             would flag: a "dip" outlasting ~p90 is odds-on a failure);
  censored   the series ends mid-run — excluded from the distribution.

Point-in-time throughout (R6): the weekly circle at day i is the LIVE
`homily_circle` over weekly closes *including the running week* (exactly
the circle the digest would print that day), and the daily candle is the
LIVE `daily_candle` on the close prefix. 5y daily bars, both universes.

Pre-committed ship rule (before the run): the digest "dip day n (typ.
x–y)" line ships ONLY if the resolved-duration band is stable — medians
within ±1 day and p90 within ±2 days across universe A, universe B, and
the first/second OOS half of the window. Otherwise: study recorded,
nothing ships (the honest null).
"""
from homily_clone import homily_circle
from homily_danny import daily_candle
from homily_strategy_backtest import UNIV_A, UNIV_B
from homily_data import fetch_daily

WARMUP = 260          # daily bars before either engine is credible

# Committed output of the 2026-07-11 run (BACKTEST_RESULTS §8), STABLE per
# the pre-committed rule above: medians 4–6d, p90 21–23d across A/B × H1/H2.
# daily_run prints these next to a live dip's age. NOT shipped: the "dip
# past p90 = trend-failure warning" idea — the run showed failures resolve
# FASTER (median 3d), so age does not raise failure odds; saying otherwise
# would be a lie the data already refused.
DIP_MEDIAN_D = 4
DIP_P90_D = 22
DIP_SCAN = 40         # live dip_age() lookback cap (p99 territory)


def dip_age(closes):
    """Trailing consecutive days whose LIVE daily candle is non-RED — the
    'dip day n' counter for digest rows whose weekly circle is RED. 0 means
    today's candle is RED (no dip in progress)."""
    age = 0
    for i in range(len(closes) - 1, max(WARMUP - 1, len(closes) - 1 - DIP_SCAN),
                   -1):
        if daily_candle(closes[:i + 1]) == "RED":
            break
        age += 1
    return age


def day_states(tk, bars):
    """-> (weekly_red[], candle_red[]) per day, live engines on prefixes."""
    closes = [b[4] for b in bars]
    wred, cred = [], []
    wk, cur_key = [], None
    for i, b in enumerate(bars):
        key = b[0].isocalendar()[:2]
        if key != cur_key:
            wk.append(b[4])
            cur_key = key
        else:
            wk[-1] = b[4]
        if i < WARMUP:
            wred.append(None)
            cred.append(None)
            continue
        wred.append(homily_circle(tk, wk).circle == "RED")
        cred.append(daily_candle(closes[:i + 1]) == "RED")
    return wred, cred


def pullbacks(wred, cred):
    """-> (resolved [(start, length)], failed [(start, length)])."""
    resolved, failed = [], []
    run_start = None
    for i in range(WARMUP, len(wred)):
        in_red, candle_red = wred[i], cred[i]
        if run_start is None:
            if in_red and not candle_red:
                run_start = i
        else:
            if not in_red:
                failed.append((run_start, i - run_start))
                run_start = None
            elif candle_red:
                resolved.append((run_start, i - run_start))
                run_start = None
    return resolved, failed          # an open run at series end is censored


def dist(lengths):
    if not lengths:
        return None
    xs = sorted(lengths)
    q = lambda p: xs[min(len(xs) - 1, int(p * (len(xs) - 1) + 0.5))]
    return {"n": len(xs), "median": q(0.5), "p25": q(0.25), "p75": q(0.75),
            "p90": q(0.9)}


def fmt(d):
    return (f"n={d['n']:>5}  median {d['median']:>2}d  p25 {d['p25']:>2}d  "
            f"p75 {d['p75']:>2}d  p90 {d['p90']:>2}d") if d else "n=0"


if __name__ == "__main__":
    univ_all = UNIV_A + [n for n in UNIV_B if n not in UNIV_A]
    res = {}   # (universe, half) -> [lengths]; fail counts pooled
    n_fail, fail_lens, dead = 0, [], []
    for sym in univ_all:
        try:
            bars = fetch_daily(sym, rng="5y")
        except Exception:
            dead.append(sym)
            continue
        if len(bars) < WARMUP + 120:
            dead.append(sym)
            continue
        wred, cred = day_states(sym, bars)
        resolved, failed = pullbacks(wred, cred)
        n_fail += len(failed)
        fail_lens += [l for _, l in failed]
        mid = len(bars) // 2
        for start, l in resolved:
            half = "H1" if start < mid else "H2"
            for g in (("A", sym in UNIV_A), ("B", sym in UNIV_B)):
                if g[1]:
                    res.setdefault((g[0], half), []).append(l)
                    res.setdefault((g[0], "all"), []).append(l)
        print(f"  {sym:<6} resolved {len(resolved):>4}  failed {len(failed):>3}",
              flush=True)

    print(f"\nPullback clock (#78) — dips inside intact weekly-RED spells, "
          f"5y daily, live engines"
          + (f" (skipped: {', '.join(dead)})" if dead else ""))
    cells = []
    for u in ("A", "B"):
        for h in ("all", "H1", "H2"):
            d = dist(res.get((u, h), []))
            print(f"  univ {u} {h:<4} {fmt(d)}")
            if h != "all" or True:
                cells.append(d)
    comb = dist(res.get(("A", "all"), []) + res.get(("B", "all"), []))
    print(f"  COMBINED     {fmt(comb)}")
    fd = dist(fail_lens)
    print(f"  failures     {fmt(fd)}   (weekly RED broke mid-dip; "
          f"{n_fail} runs)")

    checks = [d for d in cells if d]
    stable = (len(checks) == 6
              and max(d["median"] for d in checks)
              - min(d["median"] for d in checks) <= 2      # ±1d of each other
              and max(d["p90"] for d in checks)
              - min(d["p90"] for d in checks) <= 4)        # ±2d of each other
    print(f"\nPre-committed ship rule: medians within ±1d AND p90 within ±2d "
          f"across A/B × H1/H2 -> "
          f"{'STABLE — digest line may ship' if stable else 'NOT stable — nothing ships'}.")
    if comb:
        print(f"Danny's claim: 3–7 trading days. Our band: p25–p75 = "
              f"{comb['p25']}–{comb['p75']}d, median {comb['median']}d, "
              f"p90 {comb['p90']}d.")
