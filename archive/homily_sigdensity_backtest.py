#!/usr/bin/env python3
"""
#132 · Buy-signal density as a selection challenger (PRD §5n, HOOD).
====================================================================

Danny's conviction expresses as REPEATED prints on one name over months
(HOOD Jul 16 2026: ">10 bullish signals in my daily MUST-READ posts",
6+ posted buy orders). We rank candidates by rs12 (the incumbent, #24)
and have raced whale_rank and conviction score against it — but never a
trailing signal COUNT. This study races it, in the #24/#120 bake-off
harness, unchanged.

RULE — FROZEN BEFORE THE FIRST RUN (do not renegotiate after numbers):

  Density (point-in-time, live `danny_signal` on truncated bars — R6):
    * for each name, walk its OWN daily bars; on the first trading day of
      each ISO week (once ≥ 260 bars exist) compute
      danny_signal(name, bars[:i+1]).state;
    * a week is a BUY-CLASS print iff state ∈ {ACCUMULATE, BOTTOMING} —
      the ⭐/🔵 backbone. 🐳/⤴ are conditioned decorations of the same
      days and are OUT of scope for tractability (a null here nulls the
      backbone claim; a pass does NOT vouch for the decorations);
    * density at decision date d = count of buy-class prints over the 13
      most recent weekly observations ≤ d (13 weeks ≈ one quarter — the
      "campaign" window; frozen, not tuned).
  Arms: density-top3 (rank by density desc, tie-break rs12 desc) vs the
  incumbent rs12-top3, plus equal-all and DCA SPY/QQQ context. All
  accounting, screening, windows, and the equal-all regression check are
  homily_selection_backtest's, reused verbatim (cache rows carry density
  in the conviction slot; pickers are the only new code).
  Windows/reads: universe B read windows = 2020→2025, 2021→2026,
  2016→2026 (B_READ); universe A printed as hindsight upper bound only.

  VERDICT (pre-registered, from the PRD §8.3 row): density-top3 is
  adoption-worthy ONLY if its MOIC ≥ rs12-top3 MOIC − 0.01 on ALL THREE
  universe-B read windows. Else the null is the result and the item
  closes. Even on a PASS nothing ships from this session (Part III rule
  5); a promotion would pay the normal R10 selection price (next free
  slot 2027-Q3).
"""
import datetime

from homily_data import fetch_daily
from homily_danny import danny_signal
from homily_strategy_backtest import UNIV_A, UNIV_B, month_first_idx, run_dca
from homily_bear_backtest import run_mode
from homily_selection_backtest import (WINDOWS, B_READ, build_month_cache,
                                       run_selected, pick_all, pick_rs)

DENS_WEEKS = 13
MIN_BARS = 260
BUY_STATES = {"ACCUMULATE", "BOTTOMING"}


def weekly_buy_flags(name, bars):
    """[(date, is_buy_class)] on the first trading day of each ISO week,
    point-in-time, live engine (R6)."""
    out, cur = [], None
    for i, b in enumerate(bars):
        wk = b[0].isocalendar()[:2]
        if wk == cur:
            continue
        cur = wk
        if i + 1 < MIN_BARS:
            continue
        try:
            st = danny_signal(name, bars[:i + 1]).state
        except Exception:
            continue
        out.append((b[0], st in BUY_STATES))
    return out


def density_at(flags, d):
    recent = [f for dt, f in flags if dt <= d][-DENS_WEEKS:]
    return sum(recent)


def pick_density(k):
    # rows = [(name, rs12, density)] — density in the conviction slot
    return lambda rows: [n for n, _, _ in
                         sorted(rows, key=lambda r: (-r[2], -r[1]))[:k]]


ARMS = (("equal-all", pick_all), ("rs12-top3", pick_rs(3)),
        ("dens-top3", pick_density(3)))


def main():
    spy = fetch_daily("SPY", rng="max")
    qqq = fetch_daily("QQQ", rng="max")
    all_months = [spy[i][0] for i in month_first_idx(spy)][1:]
    span = [m for m in all_months if WINDOWS[0][0] <= m <= WINDOWS[-1][1]]

    verdict_rows = []
    for tag, names in (("B hype-2021 control", UNIV_B),
                       ("A current univ (HINDSIGHT)", UNIV_A)):
        data = {}
        for n in names:
            try:
                data[n] = fetch_daily(n, rng="max")
            except Exception:
                pass
        live = sorted(data)
        print(f"\n{'#' * 74}\n# {tag} — {len(live)} names\n{'#' * 74}",
              flush=True)
        cache = build_month_cache(live, data, spy, span)
        flags = {}
        for n in live:
            flags[n] = weekly_buy_flags(n, data[n])
            print(f"  weekly states {n}: {len(flags[n])} obs, "
                  f"{sum(f for _, f in flags[n])} buy-class", flush=True)
        # density replaces the conviction slot; rs12 kept for tie-break
        cache2 = {d: [(n, rs, density_at(flags[n], d)) for n, rs, _ in rows]
                  for d, rows in cache.items()}

        for w0, w1, wl in WINDOWS:
            win = (w0, w1)
            ref = run_mode(live, data, spy, qqq, "hold", index_bars=spy,
                           win=win)
            got = run_selected(cache2, data, spy, win, spy, pick_all)
            drift = max(abs(a - b) for a, b in zip(ref[:3], got))
            flag = "OK" if drift < 1e-9 else "DRIFT-VOID"
            dm, _, _ = run_dca(spy, spy, win=win)
            qm, _, _ = run_dca(qqq, spy, win=win)
            read = ("READ" if win in B_READ else "context") \
                if tag.startswith("B") else "upper-bound"
            print(f"\n── {w0} → {w1} ({wl}) · {read} · regression {flag}"
                  f" · DCA SPY {dm:.2f} / QQQ {qm:.2f} MOIC ──")
            print(f"  {'arm':<12}{'MOIC':>6}{'CAGR':>8}{'MaxDD':>7}{'>QQQ':>6}")
            arm_moic = {}
            for arm, picker in ARMS:
                m, c, dd = run_selected(cache2, data, spy, win, spy, picker)
                arm_moic[arm] = m
                print(f"  {arm:<12}{m:>6.2f}{c * 100:>7.1f}%"
                      f"{dd * 100:>6.0f}%{'✓' if m > qm else '✗':>6}",
                      flush=True)
            if tag.startswith("B") and win in B_READ and flag == "OK":
                verdict_rows.append((f"{w0}→{w1}", arm_moic["dens-top3"],
                                     arm_moic["rs12-top3"]))

    print(f"\nPRE-REGISTERED VERDICT (universe B read windows, "
          f"dens-top3 MOIC ≥ rs12-top3 − 0.01 on ALL three):")
    ok = len(verdict_rows) == 3
    for label, dm_, rm_ in verdict_rows:
        cell = dm_ >= rm_ - 0.01
        ok = ok and cell
        print(f"  {label}: dens {dm_:.2f} vs rs12 {rm_:.2f}  "
              f"{'PASS' if cell else 'FAIL'}")
    verdict = (("PASS — a promotion still needs its own session + R10 "
                "selection slot (next free 2027-Q3)") if ok
               else "NULL — rs12-top3 stands, item closes honestly")
    print(f"  => {verdict}")


if __name__ == "__main__":
    print(__doc__.strip().splitlines()[1].strip("= "))
    main()
