#!/usr/bin/env python3
"""
#138 · Leverage drift on the CORE BOOK — the asset the ladder never tested.
==========================================================================

Owner's question, 2026-08-13: *"how do we fix the issue of leverage growing
when stocks are suffering drawdowns? If we say 30% leverage is safe, then
when drawdown comes our leverage becomes 40% right even without borrowing
more."*

The arithmetic half is not in dispute: debt is fixed in dollars, equity
absorbs the whole loss, so a constant-debt 1.30× book reads 1.41× after
−20% and 1.86× after −50%. But the drifted ratio is a SYMPTOM — the call
point was fixed at entry (uniform d*(1.30) = −69.2%), so the reading moving
does not move the risk. The question worth measuring is the one behind it:
**§15 certified 1.30× on QQQ under a policy that rebalances monthly in both
directions — i.e. one that SELLS and pays debt down in a decline. The live
account never performs that sale, and it is not holding QQQ.**

`homily_leverage_backtest.policy_axis` settles the policy half on QQQ.
This file settles the ASSET half: it runs the same three policies against
the strategy book's own equity curve, taken from the committed harness via
the `nav_out` sink added to `run_mode` (kwarg-inert, #135's pattern).

  arms:      rebal (§15's policy) · ratchet (LEVERAGE.md as written) ·
             fixed (borrow once, never act on the 🐻 signal)
  L:         1.15 · 1.30 · 1.50
  book:      mode "hold"     — never-sell core, no §4 protocol (the −59…−76%
                               paths LEVERAGE.md §2 quotes when it BANS core
                               margin)
             mode "faithful" — the core book as the PLAYBOOK actually runs
                               it, §4 bear protocol included
  universes: B honest control (5y/10y) · GRIND survivors (33y, SURVIVOR
             BIAS — context only, never a verdict)
  financing: 5.8% base / 7.8% stress, accrued at the series' own step

PRE-REGISTERED (PRD #138, frozen before this file ran):
  (a) SURVIVAL, primary — breach ⇔ equity/position < 0.25 on any
      observation; a cell PASSES iff zero breaches in every window. Both
      sides positive, lower is worse: no sign trap (0.24 < 0.25 → BREACH).
  (b) DRIFT, descriptive — max L reached; the owner's "1.30 became X".
  (c) COST OF DELEVERING, sign-safe against the #126 trap — MaxDD are
      NEGATIVE fractions, so the test is `maxdd_ratchet >= maxdd_rebal −
      0.05` (worked: rebal −0.29, ratchet −0.37 → −0.37 >= −0.34 is FALSE
      → ratchet worse by more than tolerance).

DECLARED LIMITATION, and it flatters every cell below: the NAV path is
MONTHLY, so intramonth lows are invisible and a book that margin-called on
2008-10-10 and recovered by month-end is recorded as surviving. Reported,
not corrected — same direction as §15's "intra-day gaps not modeled" and
its concentrated-maintenance caveat. A core cell that breaches on MONTHLY
data has therefore breached decisively.

Reproduce: python homily_levdrift_backtest.py   (fetches both universes)
Results → BACKTEST_RESULTS.md §39 (#138).
"""
import datetime

from homily_data import fetch_daily, fetch_series
from homily_strategy_backtest import UNIV_B
from homily_bear_backtest import GRIND_UNIV, _fetch, run_mode
from homily_leverage_backtest import (FIN_BASE, FIN_STRESS, LADDER_LS,
                                      M_MAINT, POLICIES, d_star,
                                      regime_by_month, run_arm)

WINDOWS_B = [(datetime.date(2021, 7, 22), datetime.date(2026, 7, 21), "5y"),
             (datetime.date(2016, 7, 22), datetime.date(2026, 7, 21), "10y")]
WINDOW_G = [(datetime.date(1993, 1, 1), datetime.date(2026, 7, 21), "33y")]


def core_nav(live, data, spy, qqq, mode, win):
    """The book's own equity curve under `mode`. -> (dates, values, scalars)"""
    sink = []
    scalars = run_mode(live, data, spy, qqq, mode, index_bars=spy, win=win,
                       nav_out=sink)
    dates = [d for d, _ in sink]
    vals = [v for _, v in sink]
    return dates, vals, scalars


def main():
    # regime labels come from ADJUSTED closes, exactly as §15 builds them
    spy_bars, spy_adj = fetch_series("SPY", rng="max")
    qqq_bars, qqq_adj = fetch_series("QQQ", rng="max")
    labels = regime_by_month([b[0] for b in spy_bars], spy_adj,
                             [b[0] for b in qqq_bars], qqq_adj)
    # run_mode keeps the committed harness's own fetcher, untouched
    spy = fetch_daily("SPY", rng="max")
    qqq = fetch_daily("QQQ", rng="max")

    print("#138 · leverage drift on the CORE BOOK")
    print(f"maintenance {M_MAINT} · financing {FIN_BASE:.1%} base /"
          f" {FIN_STRESS:.1%} stress · MONTHLY NAV (flatters survival)")
    print(f"call boundary: d*(1.15) = −{d_star(1.15)*100:.1f}% ·"
          f" d*(1.30) = −{d_star(1.30)*100:.1f}% ·"
          f" d*(1.50) = −{d_star(1.50)*100:.1f}%")

    verdict = []
    for tag, univ, wins, is_verdict in (
            ("B honest control", UNIV_B, WINDOWS_B, True),
            ("GRIND survivors (SURVIVOR BIAS — context, never a verdict)",
             GRIND_UNIV, WINDOW_G, False)):
        data, dead = _fetch(univ, "max")
        live = [n for n in univ if n in data]
        print(f"\n{'='*74}\n### {tag} — {len(live)} names"
              f"{' (dead: ' + ', '.join(dead) + ')' if dead else ''} ###"
              f"\n{'='*74}", flush=True)

        if is_verdict:
            # `nav_out` must be a pure sink: run_mode's scalars — and so
            # every committed table that reads them — cannot move because a
            # list was passed. Proven, not asserted in prose (#135 pattern).
            w = (WINDOWS_B[0][0], WINDOWS_B[0][1])
            without = run_mode(live, data, spy, qqq, "faithful",
                               index_bars=spy, win=w)
            sink = []
            with_ = run_mode(live, data, spy, qqq, "faithful",
                             index_bars=spy, win=w, nav_out=sink)
            drift = max(abs(a - b) for a, b in zip(without[:3], with_[:3]))
            print(f"  nav_out kwarg-inert drift: {drift:.2e}"
                  f" · sink received {len(sink)} months"
                  + ("" if drift == 0.0 else "  ⚠ NOT INERT — RUN VOID"))

        for w0, w1, wl in wins:
            for mode in ("hold", "faithful"):
                dts, vals, sc = core_nav(live, data, spy, qqq, mode, (w0, w1))
                if len(dts) < 24:
                    print(f"  {wl} {mode}: too few months, skipped")
                    continue
                # The levered arms compound this NAV path from eq=1.0, so
                # their "moic" is a TIME-weighted multiple. run_mode's own
                # MOIC is MONEY-weighted (final/paid on a $1/month DCA) and
                # is NOT the baseline for them — printing it as one would
                # read as though 1.30× turned 2.51 into 21.99. The unlevered
                # arm on the SAME path is the honest baseline.
                base = run_arm(dts, vals, labels, 1.0, 0.0,
                               periods_per_year=12)
                print(f"\n  --- {wl} ({w0} → {w1}) · book mode '{mode}' ·"
                      f" {len(dts)} months ---")
                print(f"  unlevered on this path: {base['moic']:.2f}×"
                      f" (time-weighted, the baseline below) · MaxDD"
                      f" {base['maxdd']*100:.0f}% · run_mode's own"
                      f" money-weighted MOIC {sc[0]:.2f} / CAGR"
                      f" {sc[1]*100:.1f}% (different measure, not a"
                      f" baseline)")
                print(f"  {'policy':<9}" + "".join(f"{f'L{L}':>24}"
                                                   for L in LADDER_LS))
                print(f"  {'':<9}" + "".join(f"{'moic  minR  maxL':>24}"
                                             for _ in LADDER_LS))
                cells = {}
                for pol in POLICIES:
                    line = f"  {pol:<9}"
                    for L in LADDER_LS:
                        r = run_arm(dts, vals, labels, L, FIN_BASE,
                                    policy=pol, periods_per_year=12)
                        cells[(pol, L)] = r
                        br = " ⚠CALL" if r["breach"] else ""
                        line += (f"{r['moic']:>9.2f}{r['min_ratio']:>7.2f}"
                                 f"{r['max_lev']:>6.2f}{br:<2}")
                    print(line)
                # stress financing, ladder cells only
                st = []
                for pol in POLICIES:
                    for L in LADDER_LS:
                        r = run_arm(dts, vals, labels, L, FIN_STRESS,
                                    policy=pol, periods_per_year=12)
                        if r["breach"]:
                            st.append(f"{pol} L{L} {r['breach']}")
                print(f"  stress {FIN_STRESS:.1%}: "
                      + ("no additional breaches" if not st
                         else "⚠CALL " + " · ".join(st)))
                if is_verdict:
                    verdict.append((wl, mode, cells))

    print(f"\n{'='*74}\n== #138 · READOUT (a) SURVIVAL — core book, honest"
          f" universe only ==\n{'='*74}")
    print(f"breach ⇔ equity/position < {M_MAINT}; a cell PASSES iff zero"
          " breaches in every window")
    for pol in POLICIES:
        for L in LADDER_LS:
            bad = [f"{wl}/{mode} {c[(pol, L)]['breach']}"
                   for wl, mode, c in verdict if c[(pol, L)]["breach"]]
            worst = min(c[(pol, L)]["min_ratio"] for _, _, c in verdict)
            print(f"  {pol:<8} L={L:<5} worst equity/position {worst:.2f}"
                  + ("  → PASS (zero breaches)" if not bad
                     else "  → BREACH " + ", ".join(bad)))

    print("\n== #138 · READOUT (b) DRIFT — descriptive, no pass/fail ==")
    for L in LADDER_LS:
        for pol in POLICIES:
            peak = max(c[(pol, L)]["max_lev"] for _, _, c in verdict)
            print(f"  {pol:<8} started {L:.2f}× → peaked {peak:.2f}×")

    print("  NOTE on 'fixed': it borrows once at t0 and never adjusts, so"
          " over a long\n  window its leverage DECAYS toward 1.00× as equity"
          " compounds — its mild peak\n  and low return in the 33y rows are"
          " that decay, not safety. It is a faithful\n  model of ONE thing:"
          " levered up, then never acted on the 🐻 signal.")

    print("\n== #138 · READOUT (c) COST OF DELEVERING (sign-safe) ==")
    print("  MaxDD are NEGATIVE fractions; test is"
          " maxdd_ratchet >= maxdd_rebal − 0.05")
    for wl, mode, c in verdict:
        a, b = c[("rebal", 1.30)], c[("ratchet", 1.30)]
        ok = b["maxdd"] >= a["maxdd"] - 0.05
        print(f"  {wl}/{mode:<9} rebal {a['maxdd']*100:>5.0f}%  ratchet"
              f" {b['maxdd']*100:>5.0f}%  moic {a['moic']:.2f} vs"
              f" {b['moic']:.2f}  → "
              + ("within tolerance" if ok else "ratchet WORSE by >5pt"))


if __name__ == "__main__":
    main()
