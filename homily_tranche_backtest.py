#!/usr/bin/env python3
"""
#50 · Staged-add tranches (shelf / −7% / −14%) — THE OWNER'S DIP INSTINCT, TESTED.
=================================================================================

The question, in his words (2026-07-25): *"doesn't Danny aggressively
scale in when the price dips, seems counterintuitive to buy when the price
hasn't retraced."* PRD §8.3 row 50 pre-registered the answer's shape years
before it was asked: **avg-cost + MOIC vs single-add and DCA, both
universes.** This file freezes the rest of the rule BEFORE the run, per
EXECUTION.md Part III (a study never shops for its own result).

--------------------------------------------------------------------------
RULE, FROZEN 2026-07-25 BEFORE THE FIRST RUN — do not edit after data exists
--------------------------------------------------------------------------

Unit of test: ONE name, $1 of new money per month (D-86 keeps the
*cross-month* budget question; this is the *within-name* shaping question).
Every arm receives the identical cash on the identical dates, so selection
is held constant and only the SHAPE of deployment differs.

ARMS
  SINGLE   deploy the full $1 at that month's first close.  (incumbent —
           what PLAYBOOK §3 does today, and what #125 just re-pointed)
  STAGED   park the $1; deploy 1/3 at each trigger, in order, whichever
           comes first, evaluated on daily closes after the buy day:
             T1  close <= the name's chip SHELF at the buy day
                 (homily_chips.build_profile(...).support[0][0], computed
                 point-in-time from bars strictly before the buy day)
             T2  close <= buy-day close * 0.93   (−7%)
             T3  close <= buy-day close * 0.86   (−14%)
           Triggers are independent: a −20% crash on one day fires all
           three that are still unfilled, at that day's close.
  DCA      the same $1/month into the INDEX (SPY), never into the name —
           PRD row 50's third leg and the north-star benchmark.

DEADLINE (the parameter that decides the whole study, so it is frozen and
NOT tuned): an unfilled tranche deploys at market on its **6-month**
anniversary. Rationale stated in advance: a real staged-add investor does
not hold a tranche forever, and letting cash sit indefinitely would score
the arm on cash drag rather than on tranche shape. A 3m/12m sensitivity is
REPORTED, and by pre-commitment cannot be promoted over the 6m primary:
best-of-grid shopping is disallowed (the #86 clause) — if the primary
fails, the item is NULL regardless of what the grid shows.

Cash awaiting a trigger earns nothing (0%). Stated so the drag is honest.

METRICS (both required, per row 50)
  avg cost   total dollars deployed into the name / total shares bought.
             LOWER is better. Reported as % vs SINGLE's avg cost.
  MOIC       terminal value of everything the arm holds (shares at the
             window's last close + any never-deployed cash) / dollars
             contributed. HIGHER is better.
  Costs: COST (10 bps) charged on every deployment in every arm.

GATE (pre-committed — all three prongs, else NULL)
  (a) STAGED beats SINGLE on MOIC, median across names, in BOTH universes;
  (b) STAGED beats SINGLE on avg cost, median across names, in BOTH
      universes  (the mechanism must be the discount it claims, not luck);
  (c) STAGED beats DCA on MOIC in BOTH universes  (row 50's third leg).
  Windows: the standing WINDOWS harness (seven 5y + two 10y). A prong
  "passes a universe" only if it wins a MAJORITY of that universe's
  windows. Anything less = NULL, recorded beside §5f, and the tranche idea
  closes — the owner reads the number, not a softened summary.

ADOPTION NOTE, RECORDED BEFORE THE RUN (why a PASS still would not ship
today): D-66 §(c) made tranche automation conditional on the thesis-break
veto — "the machinery that sizes up into weakness refuses to run on names
whose business broke." That veto is DEAD: #66's wreck-separation gate
FAILED (BACKTEST_RESULTS §14 — ZM/DOCU/ROKU/W were Q1 on as-of filings),
so nothing stops a staged add from averaging down into a genuine wreck.
A PASS here is therefore a study result, not a ship: it would need its own
R10 selection slot (next free 2027-Q3 after #125) plus a replacement for
the missing veto. Part III rule 5 applies as always — this session runs
the study, a separate decision ships it.

Reproduce:  python homily_tranche_backtest.py
"""
import datetime
import statistics as st

from homily_data import fetch_daily
from homily_chips import build_profile
from homily_strategy_backtest import (COST, UNIV_A, UNIV_B, month_first_idx,
                                      close_on)
from homily_multiwindow_backtest import WINDOWS, _fetch_all

TRANCHE_PCTS = (0.07, 0.14)          # T2, T3 — T1 is the chip shelf
DEADLINE_M = 6                       # PRIMARY, frozen. 3/12 are sensitivity.
SENSITIVITY = (3, 12)
MIN_BARS = 260


def _shelf_at(bars, d):
    """The chip shelf as of the buy day, point-in-time: bars strictly
    before d. None when the profile has no support level."""
    hist = [b for b in bars if b[0] < d]
    if len(hist) < MIN_BARS:
        return None
    try:
        prof = build_profile(hist)
    except Exception:                                      # noqa: BLE001
        return None
    return prof.support[0][0] if prof.support else None


def _months_after(d, n):
    y, m = divmod(d.month - 1 + n, 12)
    try:
        return d.replace(year=d.year + y, month=m + 1)
    except ValueError:                                     # 31st -> short month
        return d.replace(year=d.year + y, month=m + 1, day=28)


def run_name(bars, buy_days, end, deadline_m=DEADLINE_M):
    """-> {arm: (shares, deployed, cash_left)} for one name."""
    idx = {b[0]: i for i, b in enumerate(bars)}
    res = {}

    # --- SINGLE -----------------------------------------------------------
    sh = dep = 0.0
    for d in buy_days:
        px = close_on(bars, d)
        if px:
            sh += 1.0 / (px * (1 + COST))
            dep += 1.0
    res["SINGLE"] = (sh, dep, 0.0)

    # --- STAGED -----------------------------------------------------------
    sh = dep = cash = 0.0
    for d in buy_days:
        px0 = close_on(bars, d)
        if not px0:
            continue
        shelf = _shelf_at(bars, d)
        # trigger prices; a missing shelf makes T1 unreachable except by the
        # deadline (stated, not silently re-pointed at another level)
        trig = [shelf, px0 * (1 - TRANCHE_PCTS[0]), px0 * (1 - TRANCHE_PCTS[1])]
        filled = [False, False, False]
        dead = _months_after(d, deadline_m)
        i0 = next((i for i, b in enumerate(bars) if b[0] > d), len(bars))
        for b in bars[i0:]:
            if b[0] > end:
                break
            if all(filled):
                break
            if b[0] >= dead:                       # deadline: deploy the rest
                for k in range(3):
                    if not filled[k]:
                        sh += (1.0 / 3) / (b[4] * (1 + COST))
                        dep += 1.0 / 3
                        filled[k] = True
                break
            for k, t in enumerate(trig):
                if not filled[k] and t is not None and b[4] <= t:
                    sh += (1.0 / 3) / (b[4] * (1 + COST))
                    dep += 1.0 / 3
                    filled[k] = True
        cash += sum(1.0 / 3 for f in filled if not f)   # window ended first
    res["STAGED"] = (sh, dep, cash)
    return res


def moic_and_cost(r, last_px):
    sh, dep, cash = r
    contributed = dep + cash
    if contributed <= 0 or sh <= 0:
        return None, None
    return (sh * last_px + cash) / contributed, dep / sh


def dca_moic(bars_ix, buy_days, w1):
    """Prong (c)'s leg: $1/month into the index over the same dates."""
    sh = dep = 0.0
    for d in buy_days:
        px = close_on(bars_ix, d)
        if px:
            sh += 1.0 / (px * (1 + COST))
            dep += 1.0
    last = close_on(bars_ix, w1)
    return (sh * last / dep) if dep and last else None


def run_universe(names, data, spy, w0, w1, deadline_m=DEADLINE_M):
    """-> (median MOIC by arm, median avg-cost ratio STAGED/SINGLE, n)."""
    months = [spy[i][0] for i in month_first_idx(spy)]
    buy_days = [m for m in months if w0 <= m <= w1]
    moics = {"SINGLE": [], "STAGED": []}
    cost_ratio = []
    for n in names:
        bars = data.get(n)
        if not bars or bars[0][0] > w0 - datetime.timedelta(days=400):
            continue
        last = close_on(bars, w1)
        if not last:
            continue
        r = run_name(bars, buy_days, w1, deadline_m)
        ms, cs = {}, {}
        ok = True
        for arm in ("SINGLE", "STAGED"):
            m, c = moic_and_cost(r[arm], last)
            if m is None:
                ok = False
                break
            ms[arm], cs[arm] = m, c
        if not ok:
            continue
        for arm in ms:
            moics[arm].append(ms[arm])
        cost_ratio.append(cs["STAGED"] / cs["SINGLE"])
    if not cost_ratio:
        return None
    return ({a: st.median(v) for a, v in moics.items()},
            st.median(cost_ratio), len(cost_ratio),
            dca_moic(spy, buy_days, w1))


def main():
    names = sorted(set(UNIV_A) | set(UNIV_B))
    print(f"fetching {len(names) + 1} names (max range) …")
    data, dead = _fetch_all(names + ["SPY"])
    spy = data.get("SPY")
    print(f"  {len(data)} fetched, {len(dead)} dead: {dead}\n")

    for label, univ in (("A momentum/quality", UNIV_A),
                        ("B hype-2021 control (THE HONEST ONE)", UNIV_B)):
        print(f"=== UNIVERSE {label} ===")
        print(f"{'window':<22}{'n':>4}{'SINGLE':>9}{'STAGED':>9}"
              f"{'MOIC won':>10}{'avg cost':>10}{'cost won':>10}"
              f"{'DCA SPY':>9}{'vs DCA':>8}")
        wins_moic = wins_cost = wins_dca = tot = 0
        for w0, w1, wl in WINDOWS:
            out = run_universe(univ, data, spy, w0, w1)
            if not out:
                continue
            ms, cr, n, dm = out
            mw = ms["STAGED"] > ms["SINGLE"]
            cw = cr < 1.0
            dw = dm is not None and ms["STAGED"] > dm
            wins_moic += mw
            wins_cost += cw
            wins_dca += dw
            tot += 1
            print(f"{w0.year}-{w1.year} {wl:<12}{n:>4}{ms['SINGLE']:>9.3f}"
                  f"{ms['STAGED']:>9.3f}{'YES' if mw else 'no':>10}"
                  f"{cr:>9.3f}x{'YES' if cw else 'no':>10}"
                  f"{dm:>9.3f}{'YES' if dw else 'no':>8}")
        print(f"  -> STAGED won MOIC in {wins_moic}/{tot} windows, "
              f"avg-cost in {wins_cost}/{tot}, vs DCA in {wins_dca}/{tot}\n")

    print("sensitivity (NOT promotable over the frozen 6m primary):")
    for dl in SENSITIVITY:
        for label, univ in (("A", UNIV_A), ("B", UNIV_B)):
            w = sum(1 for w0, w1, _ in WINDOWS
                    if (lambda o: o and o[0]["STAGED"] > o[0]["SINGLE"])(
                        run_universe(univ, data, spy, w0, w1, dl)))
            print(f"  deadline {dl}m · univ {label}: STAGED won MOIC "
                  f"{w}/{len(WINDOWS)} windows")


if __name__ == "__main__":
    main()
