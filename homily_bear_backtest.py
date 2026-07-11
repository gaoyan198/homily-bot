#!/usr/bin/env python3
"""
D-63 · Bear-regime rethink — decompose the 🐻 sell step.
=======================================================

The committed THE-test overlay (`homily_strategy_backtest.py`,
BACKTEST_RESULTS.md) sells value: idx-fallback 16.7%/19.2% CAGR (5y/10y)
drops to 6.4%/9.4% once the bear-sell overlay is switched on. But that
overlay is NOT PLAYBOOK §4 — it conflates three separable decisions:

    1. WHAT to sell   — everything, vs only weak satellites (§4 leaves
                        Bucket A/B, sells Bucket C).
    2. WHERE proceeds go — cash, vs "keep buying the index through the
                        bear" (§4 step 6).
    3. HOW to re-enter — lump on the first 🐂 month, vs thirds over three
                        months (§4 step 7).

This file isolates those decisions with a `bear_mode` switch, so the
measured −10 pts/yr can be attributed rather than asserted. Same
point-in-time machinery as the THE test (fund-unit NAV, 10bps/trade,
signals computed only from bars ≤ decision day) — we reuse its helpers
directly so the accounting is identical.

    (a) hold        — idx-fallback, no regime. THE-test champion. Baseline.
    (b) sell_cash   — the committed overlay: sell EVERYTHING on every 🐻
                      month, park + accumulate cash, lump re-enter on the
                      first 🐂 month.  *(regression: must reproduce (b) in
                      BACKTEST_RESULTS — 6.4% / 9.4% CAGR.)*
    (c) freeze      — hold everything; while 🐻 make NO satellite adds,
                      contributions → index core. No selling at all.
    (d) faithful    — §4 to the letter: sell satellites ONCE at 🐻 onset →
                      0% dry powder; contributions → index while 🐻; on 🐂
                      redeploy the powder into ⭐ picks in thirds / 3 months.
    (e) sell_index  — sell satellites at onset, proceeds straight into the
                      index core, never re-timed (kills the re-entry leg).
    (f) perstock    — no 🐻 selling at all; PLAYBOOK §5.2 is the ONLY
                      satellite exit: ⚪ CAUTION ≥12 weeks → sell half.

Modes (a)/(b) delegate their arithmetic to the exact same code path as the
THE test, and `_assert_regression()` proves it — if run_mode's (a)/(b)
diverge from `run_strategy`, the whole comparison is void.

CAVEATS baked into the header of every run:
  * These 5y/10y windows contain ONE bear (2022) and it was V-shaped. This
    is a DECOMPOSITION, not a proof — see Step 2 for the grinding-bear case.
  * Buckets are NOT modelled: every position here is a satellite (no Bucket
    A/B exemption). §4's "don't sell the earned core" can't help modes that
    sell — so modes (b)/(d)/(e) are the PESSIMISTIC bound on §4.
  * Mode (f) omits §5.2's F:0–1 fundamental gate — EDGAR fundamentals are
    not point-in-time reconstructable here, so (f) sells on the chart alone.
    That makes it the AGGRESSIVE upper bound on the per-name exit's benefit.

Golden numbers (5y, 2021-07 → 2026-07, universe B honest control) are in
GOLDEN below; `python homily_bear_backtest.py` reprints them (+ 10y, the
2022 episode in isolation, and the grinding-bear survivors of Step 2).
"""
import datetime

from homily_data import fetch_daily
from homily_danny import danny_signal
from homily_strategy_backtest import (
    COST, UNIV_A, UNIV_B, month_first_idx, regime_series, close_on,
    run_strategy, run_dca,
)

MODES = ("hold", "sell_cash", "freeze", "faithful", "sell_index", "perstock")
MODE_LABEL = {
    "hold":       "(a) hold-through",
    "sell_cash":  "(b) sell-all + cash",
    "freeze":     "(c) freeze-only",
    "faithful":   "(d) faithful §4",
    "sell_index": "(e) sell-into-index",
    "perstock":   "(f) §5.2 per-name",
}
CAUTION_MONTHS = 3       # §5.2 "12+ weeks" ≈ 3 completed months
REENTRY_TRANCHES = 3     # §4 step 7: thirds over three months

# Committed regression targets (BACKTEST_RESULTS.md, honest control univ B).
# run_mode's (a)/(b) are checked against run_strategy directly at runtime;
# these are the human-readable anchors the docstring promises.
GOLDEN = {
    "5y":  {"hold_cagr": 0.167, "sell_cash_cagr": 0.064},
    "10y": {"hold_cagr": 0.192, "sell_cash_cagr": 0.094},
}


def _screen(names, data, d, min_bars):
    """Point-in-time ⭐/🔵 candidates — identical to run_strategy's screen."""
    cands, backs = [], []
    for n in names:
        bars = [b for b in data[n] if b[0] <= d]
        if len(bars) < min_bars:
            continue
        try:
            st = danny_signal(n, bars).state
        except Exception:
            continue
        if st == "ACCUMULATE":
            cands.append(n)
        elif st == "BOTTOMING":
            backs.append(n)
    return cands or backs


def _bucketb_exempt(hold, data, d, val, bucketb):
    """#67 Step 3: names whose weight has EARNED core status (≥ threshold
    of the book) survive the 🐻 satellite sale, per PLAYBOOK §1."""
    if not bucketb or val <= 0:
        return set()
    return {n for n, sh in hold.items()
            if sh * (close_on(data[n], d) or 0) / val >= bucketb}


def _deploy(picks, cash, hold, core, data, d, ipx, index_bars):
    """The THE-test bull-month deployment, verbatim: split cash across picks;
    else buy the index core (§3.5); else let cash wait. Returns
    (cash, core, trades, cash_wait)."""
    trades = cash_wait = 0
    if picks and cash > 0:
        per = cash * (1 - COST) / len(picks)
        for n in picks:
            px = close_on(data[n], d)
            if px:
                hold[n] = hold.get(n, 0) + per / px
                trades += 1
        cash = 0.0
    elif index_bars and ipx > 0 and cash > 0:
        core += cash * (1 - COST) / ipx
        cash = 0.0
        trades += 1
    elif cash > 1.5:
        cash_wait += 1
    return cash, core, trades, cash_wait


def run_mode(names, data, spy, qqq, mode, min_bars=260, index_bars=None,
             win=None, bucketb=None):
    """Point-in-time backtest under one `bear_mode`. Returns
    (MOIC, TWR-CAGR, MaxDD, cash_months, trades). `win=(start,end)` isolates
    an episode: months outside the range are skipped but full bar history
    still feeds the SMA regime and the signals (no look-ahead lost).
    `bucketb` (#67 Step 3): §1's earned-core proxy — at a 🐻 onset, names
    whose weight ≥ this fraction of the book are EXEMPT from the satellite
    sale (modes faithful/sell_index only; None keeps D-63's no-bucket
    pessimistic bound, which is what the committed tables used)."""
    assert mode in MODES, mode
    is_bear = regime_series(spy, qqq)
    months = [spy[i][0] for i in month_first_idx(spy)][1:]
    if win:
        months = [m for m in months if win[0] <= m <= win[1]]

    cash = paid = 0.0
    hold = {}                 # name -> shares
    core = 0.0                # index-core shares (never sold)
    powder = 0.0              # mode (d): 0% dry-powder bucket
    reentry_left = 0          # mode (d): 🐂 months left to redeploy thirds
    caution = {}              # mode (f): name -> consecutive months in ⚪
    prev_bear = False
    nav, unit_val, units = [], 1.0, 0.0
    cash_months = trades = 0

    for d in months:
        ipx = (close_on(index_bars, d) or 0) if index_bars else 0
        val = (cash + powder + core * ipx
               + sum(sh * (close_on(data[n], d) or 0)
                     for n, sh in hold.items()))
        if units > 0:
            unit_val = val / units
        nav.append(unit_val)
        cash += 1.0
        paid += 1.0
        units += 1.0 / unit_val

        bear = is_bear(d)
        onset = bear and not prev_bear

        # ---- (b) sell-all + cash: the committed overlay ------------------
        if mode == "sell_cash":
            if bear:
                for n, sh in hold.items():
                    px = close_on(data[n], d)
                    if px:
                        cash += sh * px * (1 - COST)
                        trades += 1
                hold = {}
                cash_months += 1
                prev_bear = bear
                continue

        # ---- (d) faithful §4: sell once at onset -> 0% dry powder --------
        elif mode == "faithful":
            if onset:
                keep = _bucketb_exempt(hold, data, d, val, bucketb)
                for n, sh in hold.items():
                    if n in keep:
                        continue
                    px = close_on(data[n], d)
                    if px:
                        powder += sh * px * (1 - COST)
                        trades += 1
                hold = {n: hold[n] for n in keep}
                reentry_left = 0
            if bear:                       # contributions -> index (§4 step 6)
                if index_bars and ipx > 0 and cash > 0:
                    core += cash * (1 - COST) / ipx
                    cash = 0.0
                    trades += 1
                else:
                    cash_months += 1
                prev_bear = bear
                continue
            if prev_bear:                  # 🐂 resumes -> start thirds re-entry
                reentry_left = REENTRY_TRANCHES
            if reentry_left > 0 and powder > 0:
                tranche = powder / reentry_left
                cash += tranche            # this month's tranche joins the buy
                powder -= tranche
                reentry_left -= 1

        # ---- (e) sell-into-index: proceeds -> core, never re-timed -------
        elif mode == "sell_index":
            if onset:
                proceeds = 0.0
                keep = _bucketb_exempt(hold, data, d, val, bucketb)
                for n, sh in hold.items():
                    if n in keep:
                        continue
                    px = close_on(data[n], d)
                    if px:
                        proceeds += sh * px * (1 - COST)
                        trades += 1
                hold = {n: hold[n] for n in keep}
                if ipx > 0:
                    core += proceeds / ipx
                else:
                    cash += proceeds
            if bear:                       # contributions -> index
                if index_bars and ipx > 0 and cash > 0:
                    core += cash * (1 - COST) / ipx
                    cash = 0.0
                    trades += 1
                else:
                    cash_months += 1
                prev_bear = bear
                continue

        # ---- (c) freeze-only: hold, no adds while 🐻, contributions->idx -
        elif mode == "freeze":
            if bear:
                if index_bars and ipx > 0 and cash > 0:
                    core += cash * (1 - COST) / ipx
                    cash = 0.0
                    trades += 1
                else:
                    cash_months += 1
                prev_bear = bear
                continue

        # ---- (f) §5.2 per-name exit: ⚪ CAUTION >=12wk -> sell half ------
        elif mode == "perstock":
            for n in list(hold):
                bars = [b for b in data[n] if b[0] <= d]
                if len(bars) < min_bars:
                    continue
                try:
                    st = danny_signal(n, bars).state
                except Exception:
                    continue
                if st == "CAUTION":
                    caution[n] = caution.get(n, 0) + 1
                    if caution[n] >= CAUTION_MONTHS and hold[n] > 0:
                        px = close_on(data[n], d)
                        if px:
                            half = hold[n] * 0.5
                            cash += half * px * (1 - COST)
                            hold[n] -= half
                            trades += 1
                            caution[n] = 0        # §5.2: review in a quarter
                else:
                    caution[n] = 0

        # ---- bull-month deployment (shared by a/c/d/e/f) -----------------
        picks = _screen(names, data, d, min_bars)
        cash, core, tr, cw = _deploy(picks, cash, hold, core, data, d, ipx,
                                     index_bars)
        trades += tr
        cash_months += cw
        prev_bear = bear

    d_end = spy[-1][0] if not win else win[1]
    eipx = (close_on(index_bars, d_end) or 0) if index_bars else 0
    final = (cash + powder + core * eipx
             + sum(sh * (close_on(data[n], d_end) or 0)
                   for n, sh in hold.items()))
    unit_val = final / units
    nav.append(unit_val)
    yrs = len(months) / 12
    cagr = (nav[-1] / nav[0]) ** (1 / yrs) - 1
    mdd = min(nav[j] / max(nav[:j + 1]) - 1 for j in range(1, len(nav)))
    return final / paid, cagr, mdd, cash_months, trades


def _assert_regression(names, data, spy, qqq):
    """Prove run_mode's (a)/(b) share the THE-test arithmetic. Void the whole
    comparison if they drift — this is D-63's regression gate."""
    ref_hold = run_strategy(names, data, spy, qqq, use_regime=False,
                            index_bars=spy)
    ref_sell = run_strategy(names, data, spy, qqq, use_regime=True,
                            index_bars=spy)
    got_hold = run_mode(names, data, spy, qqq, "hold", index_bars=spy)
    got_sell = run_mode(names, data, spy, qqq, "sell_cash", index_bars=spy)
    ok = True
    for tag, ref, got in (("hold", ref_hold, got_hold),
                          ("sell_cash", ref_sell, got_sell)):
        drift = max(abs(a - b) for a, b in zip(ref[:3], got[:3]))
        flag = "OK" if drift < 1e-9 else "DRIFT"
        if drift >= 1e-9:
            ok = False
        print(f"  regression {tag:<10} MOIC/CAGR/MaxDD drift={drift:.2e} {flag}")
    return ok


def _fetch(names, rng):
    data, dead = {}, []
    for n in names:
        try:
            data[n] = fetch_daily(n, rng=rng)
        except Exception:
            dead.append(n)
    return data, dead


# 2000-02 + 2008 survivors — high-beta names alive through BOTH bears.
# Survivor-biased by construction (label it); the failure mode under test is
# holding THROUGH −80%, which survivors still exhibited (AMZN −94%; CSCO /
# INTC never reclaimed their 2000 highs).
GRIND_UNIV = ["AMZN", "NVDA", "AAPL", "MSFT", "ADBE", "INTC", "CSCO",
              "QCOM", "ORCL", "EBAY"]


def _run_window(title, names, rng, universe_tag, isolate_2022=False):
    print(f"\n{'='*74}\n{title}\n{'='*74}")
    spy = fetch_daily("SPY", rng=rng)
    qqq = fetch_daily("QQQ", rng=rng)
    print(f"window: {spy[0][0]} -> {spy[-1][0]}  ($1/month, 10bps/trade)")
    data, dead = _fetch(names, rng)
    live = [n for n in names if n in data]

    print("\n[regression — run_mode (a)/(b) vs the committed THE-test path]")
    _assert_regression(live, data, spy, qqq)

    print(f"\n{universe_tag}")
    print(f"{'mode':<22}{'MOIC':>6}{'CAGR':>9}{'MaxDD':>8}"
          f"{'cash-mo':>8}{'trades':>7}")
    for label, ix in (("DCA SPY", spy), ("DCA QQQ", qqq)):
        m, c, dd = run_dca(ix, spy)
        late = (f"  (index data starts {ix[0][0]})"
                if (ix[0][0] - spy[0][0]).days > 366 else "")
        print(f"{'  '+label:<22}{m:>6.2f}{c*100:>8.1f}%{dd*100:>7.0f}%"
              f"{'—':>8}{'—':>7}{late}")
    for mode in MODES:
        m, c, dd, cm, tr = run_mode(live, data, spy, qqq, mode, index_bars=spy)
        print(f"{MODE_LABEL[mode]:<22}{m:>6.2f}{c*100:>8.1f}%{dd*100:>7.0f}%"
              f"{cm:>8}{tr:>7}")
    if dead:
        print(f"  (unfetchable/delisted, excluded: {', '.join(dead)})")

    if isolate_2022:
        win = (datetime.date(2022, 1, 1), datetime.date(2022, 12, 31))
        print(f"\n  2022 episode in isolation ({win[0]} → {win[1]}):")
        print(f"  {'mode':<20}{'MOIC':>6}{'CAGR':>9}{'MaxDD':>8}")
        for mode in MODES:
            m, c, dd, _, _ = run_mode(live, data, spy, qqq, mode,
                                      index_bars=spy, win=win)
            print(f"  {MODE_LABEL[mode]:<20}{m:>6.2f}{c*100:>8.1f}%"
                  f"{dd*100:>7.0f}%")
    return live, dead


if __name__ == "__main__":
    import sys
    if "--bucketb" in sys.argv:
        # #67 Step 3: Bucket-B "earned core" threshold sensitivity {8,10,15}%
        # on the modes whose 🐻 sale the exemption actually gates. A
        # sensitivity table, never a headline (D-67); univ B, 5y — the one
        # window with a bear onset. None = the committed no-bucket bound.
        spy = fetch_daily("SPY", rng="5y")
        qqq = fetch_daily("QQQ", rng="5y")
        data, dead = _fetch(UNIV_B, "5y")
        live = [n for n in UNIV_B if n in data]
        print(f"#67 Step 3 — Bucket-B threshold sensitivity, univ B 5y "
              f"({spy[0][0]} → {spy[-1][0]})"
              + (f" (dead: {', '.join(dead)})" if dead else ""))
        print(f"{'mode':<22}{'exempt≥':<9}{'MOIC':>6}{'CAGR':>9}{'MaxDD':>8}")
        for mode in ("faithful", "sell_index"):
            for bb in (None, 0.08, 0.10, 0.15):
                m, c, dd, _, _ = run_mode(live, data, spy, qqq, mode,
                                          index_bars=spy, bucketb=bb)
                lbl = "none" if bb is None else f"{int(bb * 100)}%"
                print(f"{MODE_LABEL[mode]:<22}{lbl:<9}{m:>6.2f}"
                      f"{c * 100:>8.1f}%{dd * 100:>7.0f}%", flush=True)
        raise SystemExit(0)

    print("D-63 bear-regime decomposition. CAVEATS: 5y/10y windows hold ONE"
          " (V-shaped) bear — decomposition, not proof. No Bucket A/B model:"
          " every name is a satellite, so modes that SELL are §4's pessimistic"
          " bound. Mode (f) drops the F:0–1 gate (fundamentals not"
          " point-in-time) — aggressive upper bound on per-name exit.")

    # Step 1 — the decomposition matrix, both windows, honest control.
    _run_window("STEP 1 · decomposition — 5y · honest control (univ B)",
                UNIV_B, "5y", "B hype-2021 control", isolate_2022=True)
    _run_window("STEP 1 · decomposition — 5y · current univ (HINDSIGHT)",
                UNIV_A, "5y", "A current univ (upward-biased)")
    _run_window("STEP 1 · decomposition — 10y · honest control (univ B)",
                UNIV_B, "10y", "B hype-2021 control")
    _run_window("STEP 1 · decomposition — 10y · current univ (HINDSIGHT)",
                UNIV_A, "10y", "A current univ (upward-biased)")

    # Step 2 — the grinding-bear case (2000-02 + 2008). Survivor-biased.
    _run_window("STEP 2 · grinding-bear — 2000-02 + 2008 SURVIVORS (max range)",
                GRIND_UNIV, "max", "high-beta survivors (SURVIVOR BIAS)")

    print("\nMOIC = final value per $1 in. CAGR = time-weighted NAV return."
          " Modes: (a) hold-through champion · (b) committed overlay ·"
          " (c) freeze · (d) faithful §4 · (e) sell-into-index ·"
          " (f) §5.2 per-name. Decision rule: DESIGNS.md D-63.")
