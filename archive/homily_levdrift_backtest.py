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
                                      month_end_closes, month_key,
                                      regime_by_month, run_arm, target)

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


# =============================================================================
# §5r ARMS — #174 counter-cyclical · #175 house-money · #170 intramonth brake
# =============================================================================
# PRE-REGISTERED 2026-11-09, written into this file BEFORE `--5r` first ran.
# Rules and gates copied from PRD #170/#174/#175 (2026-11-08/09); nothing
# below may be edited after the run to change a verdict (Part III rule 6).
#
# Incumbent: the SIGNED ladder as LEVERAGE.md runs it = `ratchet` at 1.30
# (lever up on 🐂, MIXED drifts with no new margin, 🐻 debt → 0, never
# sell). `run_policy("ratchet")` must reproduce run_arm(policy="ratchet",
# L=1.30) to 1e-12 on every path or the whole --5r run is VOID.
#
#   counter (#174)  1.00× by default; lever to ≤1.30× only in the 12 months
#                   after a 🐻 spell ends (first non-🐻 month = re-entry,
#                   §38 EITHER-above) AND while QQQ (adj) is ≥15% below its
#                   prior all-time high at the month start; when either
#                   lapses, delever to 1.00× (sell + repay). 🐻 row intact.
#   house   (#175)  the ladder, but new borrowing on a 🐂 month only up to
#                   the house money H = max(0, equity − capital) (capital =
#                   1.0, the lump sum); MIXED no new margin; 🐻 debt → 0;
#                   no forced sale when H shrinks (no contributions exist in
#                   a lump-sum path, so the loan drifts — as the spec says).
#   brake   (#170)  the ladder, PLUS on any QQQ day whose close is below the
#                   ROLLED 10m SMA ((9 completed month-ends + today)/10),
#                   delever to 1.00× at that close; re-lever only at a month
#                   start whose label is 🐂. On the MONTHLY core-book path the
#                   intramonth fire is invisible: a fire in month k−1 delevers
#                   at the start of month k only if k's label is not 🐂 —
#                   this UNDERSTATES the brake on the core book (recorded).
#
# GATES (financing 5.8% base; §15 read windows on the daily QQQ path;
# core book = universe B, 5y + 10y, modes hold + faithful, monthly NAV):
#   #174 PASS ⇔ MOIC ≥ ratchet on ≥2 of 3 read windows AND worst
#        equity/position (QQQ max path + every core cell) ≥ ratchet's.
#   #175 PASS ⇔ worst equity/position on the core book ≥ ratchet's + 0.05
#        AND MOIC ≥ 0.97 × ratchet on all 3 read windows.
#   #170 PASS ⇔ worst equity/position on the core book ≥ ratchet's + 0.05
#        AND MOIC ≥ 0.97 × ratchet on all 3 read windows AND brake fires
#        ≤ 4 per year on average over the QQQ max path.
#   Any FAIL → NULL, published with its numbers.

def _rolled_below(dates, adj):
    """{date: True} for QQQ days closing below the rolled 10m SMA."""
    me = month_end_closes(dates, adj)
    done = {}
    hist = []
    for k, c in me:
        done[k] = list(hist)
        hist.append(c)
    out = {}
    for d, c in zip(dates, adj):
        h = done.get(month_key(d), [])
        if len(h) >= 9:
            out[d] = c < (sum(h[-9:]) + c) / 10.0
    return out


def _dd_by_month(dates, adj):
    """month_key -> QQQ drawdown from its all-time high at the PRIOR close."""
    out, ath, last, cur = {}, None, None, None
    for d, c in zip(dates, adj):
        k = month_key(d)
        if k != cur:
            cur = k
            if last is not None:
                out[k] = last / ath - 1.0
        ath = c if ath is None else max(ath, c)
        last = c
    return out


def run_policy(dates, adj, labels, policy, fin, *, L=1.30, ppy=252,
               dd_by_month=None, below=None, below_months=None):
    """One NAV path under a §5r policy. -> run_arm's dict + "fires"."""
    from homily_leverage_backtest import M_MAINT as _M
    eq, pos, debt = 1.0, 0.0, 0.0
    peak, maxdd = 1.0, 0.0
    breach, min_ratio, max_lev = None, 1.0, 0.0
    cur_m, entered, braked, fires = None, False, False, 0
    last_bear, prev_k = None, None
    daily_fin = fin / float(ppy)
    for i, d in enumerate(dates):
        k = month_key(d)
        if k != cur_m:
            cur_m = k
            lbl = labels.get(k, "BULL")
            if lbl == "BEAR":
                last_bear = k
            tgt = target(L, lbl)
            if breach is not None:
                tgt = min(tgt, 1.0)
            if policy == "counter":
                since = (None if last_bear is None else
                         (k[0] - last_bear[0]) * 12 + k[1] - last_bear[1])
                deep = (dd_by_month or {}).get(k, 0.0) <= -0.15
                ok = (lbl != "BEAR" and since is not None
                      and 1 <= since <= 12 and deep and breach is None)
                t2 = L if ok else 1.0
                pos, debt = t2 * eq, max(0.0, t2 - 1.0) * eq
            elif not entered:
                pos, debt = tgt * eq, max(0.0, tgt - 1.0) * eq
                if policy == "house":
                    pos, debt = eq, 0.0           # no gains yet: H = 0
            else:
                if policy == "brake" and braked:
                    if lbl == "BULL":
                        braked = False
                    else:
                        pos, debt = eq, 0.0
                if policy == "brake" and below_months is not None and \
                        prev_k in below_months and lbl != "BULL" and debt:
                    pos, debt = eq, 0.0
                    fires += 1
                if breach is not None or lbl == "BEAR":
                    pos, debt = tgt * eq, max(0.0, tgt - 1.0) * eq
                elif lbl == "BULL" and pos < tgt * eq and not braked:
                    want = max(0.0, tgt - 1.0) * eq
                    if policy == "house":
                        want = min(want, max(debt, max(0.0, eq - 1.0)))
                    if want > debt:
                        pos, debt = eq + want, want
            entered = True
            prev_k = k
        if i:
            pos *= adj[i] / adj[i - 1]
            debt *= 1.0 + daily_fin
            eq = pos - debt if pos else eq
        if policy == "brake" and below is not None and debt > 0 and \
                below.get(d):
            pos, debt, braked = eq, 0.0, True
            fires += 1
        if pos:
            ratio = eq / pos
            min_ratio = min(min_ratio, ratio)
            if eq > 0:
                max_lev = max(max_lev, pos / eq)
            if ratio < _M and breach is None:
                breach = d.isoformat()
                pos, debt = eq, 0.0
        peak = max(peak, eq)
        maxdd = min(maxdd, eq / peak - 1.0)
    yrs = (dates[-1] - dates[0]).days / 365.25
    return {"moic": eq, "cagr": eq ** (1 / yrs) - 1 if yrs > 0 else 0.0,
            "maxdd": maxdd, "breach": breach, "min_ratio": min_ratio,
            "max_lev": max_lev, "fires": fires}


ARMS_5R = ("ratchet", "counter", "house", "brake")


def main_5r():
    from homily_leverage_backtest import READ_WINDOWS, window_slice
    qb, qa = fetch_series("QQQ", rng="max")
    sb, sa = fetch_series("SPY", rng="max")
    qd = [b[0] for b in qb]
    labels = regime_by_month([b[0] for b in sb], sa, qd, qa)
    below = _rolled_below(qd, qa)
    below_m = {month_key(d) for d, v in below.items() if v}
    ddm = _dd_by_month(qd, qa)
    kw = {"dd_by_month": ddm}
    print("§5r leverage arms — #174 counter · #175 house · #170 brake vs the"
          " signed ladder (ratchet 1.30), base financing 5.8%")

    # regression: run_policy("ratchet") == run_arm(policy="ratchet")
    ref = run_arm(qd, qa, labels, 1.30, FIN_BASE, policy="ratchet")
    mine = run_policy(qd, qa, labels, "ratchet", FIN_BASE, **kw)
    drift = abs(ref["moic"] - mine["moic"]) + abs(ref["min_ratio"]
                                                  - mine["min_ratio"])
    print(f"  ratchet reimplementation drift vs run_arm: {drift:.2e}"
          + ("" if drift < 1e-12 else "  ⚠ VOID"))
    if drift >= 1e-12:
        return

    qqq = {}
    rows = [(f"{s}+{m}m", window_slice(qd, s, m)) for s, m in READ_WINDOWS]
    rows.append(("MAX", (0, len(qd))))
    print(f"\n  QQQ daily path      " + "".join(f"{a:>22}" for a in ARMS_5R))
    for name, sl in rows:
        lo, hi = sl
        line = f"  {name:<18}"
        for arm in ARMS_5R:
            r = run_policy(qd[lo:hi], qa[lo:hi], labels, arm, FIN_BASE,
                           below=below if arm == "brake" else None, **kw)
            qqq[(name, arm)] = r
            line += (f"{r['moic']:>8.2f} dd{r['maxdd']*100:>4.0f}%"
                     f" r{r['min_ratio']:.2f}"
                     + (f" f{r['fires']}" if arm == "brake" else "   "))
        print(line)
    yrs = (qd[-1] - qd[0]).days / 365.25
    fires_py = qqq[("MAX", "brake")]["fires"] / yrs

    spy = fetch_daily("SPY", rng="max")
    qqqd = fetch_daily("QQQ", rng="max")
    data, dead = _fetch(UNIV_B, "max")
    live = [n for n in UNIV_B if n in data]
    core = {}
    print(f"\n  core book, universe B ({len(live)} names, monthly NAV)")
    for w0, w1, wl in WINDOWS_B:
        for mode in ("hold", "faithful"):
            dts, vals, _ = core_nav(live, data, spy, qqqd, mode, (w0, w1))
            line = f"  {wl}/{mode:<9}        "
            for arm in ARMS_5R:
                r = run_policy(dts, vals, labels, arm, FIN_BASE, ppy=12,
                               below_months=below_m if arm == "brake"
                               else None, **kw)
                core[(wl, mode, arm)] = r
                line += (f"{r['moic']:>8.2f} dd{r['maxdd']*100:>4.0f}%"
                         f" r{r['min_ratio']:.2f}"
                         + (" ⚠CALL" if r["breach"] else "      "))
            print(line)

    def worst_core(arm):
        return min(v["min_ratio"] for (w, m, a), v in core.items() if a == arm)

    reads = [n for n, _ in rows if n != "MAX"]
    inc = {n: qqq[(n, "ratchet")]["moic"] for n in reads}
    print("\n== §5r READOUT (pre-registered gates) ==")
    beat = sum(qqq[(n, "counter")]["moic"] >= inc[n] for n in reads)
    w_c = min(worst_core("counter"), qqq[("MAX", "counter")]["min_ratio"])
    w_r = min(worst_core("ratchet"), qqq[("MAX", "ratchet")]["min_ratio"])
    ok174 = beat >= 2 and w_c >= w_r
    print(f"  #174 counter: beats ratchet MOIC on {beat}/3 read windows; worst"
          f" equity/position {w_c:.2f} vs {w_r:.2f} → "
          + ("PASS" if ok174 else "NULL"))
    for arm, item, extra in (("house", "#175", None),
                             ("brake", "#170", fires_py)):
        wc, wr = worst_core(arm), worst_core("ratchet")
        ni = all(qqq[(n, arm)]["moic"] >= 0.97 * inc[n] for n in reads)
        ok = wc >= wr + 0.05 and ni and (extra is None or extra <= 4.0)
        print(f"  {item} {arm}: core worst equity/position {wc:.2f} vs"
              f" {wr:.2f} (needs +0.05) · MOIC ≥0.97× on all reads: {ni}"
              + (f" · fires {extra:.1f}/yr (≤4)" if extra is not None
                 else "") + " → " + ("PASS" if ok else "NULL"))


if __name__ == "__main__":
    import sys
    if sys.argv[1:] == ["--5r"]:
        main_5r()
    else:
        main()
