#!/usr/bin/env python3
"""
#126 · Does §4 + §5.2 TOGETHER still insure? — the live system, measured.
=========================================================================

The gap this closes. PLAYBOOK runs BOTH disciplines: §4's bear protocol
(sell satellites at 🐻 onset, contributions→index, re-enter in thirds) and
§5.2's per-name exit (⚪ CAUTION 8+ weeks + F:0–1 → sell half). D-63
concluded "§4 = insurance; §5.2 = trash-taker. Different jobs, both kept"
(BACKTEST_RESULTS §3) — but `run_mode`'s modes are an elif chain, one at a
time, so **the combination was reasoned and never measured.**

A scratchpad probe on the honest control (2026-07-26) found the two legs
interact DESTRUCTIVELY there: 10y MOIC 1.98 together vs 3.19 for §5.2
alone, at −48% vs §4-alone's −51% — i.e. 38% of the wealth surrendered
for ~3 points of drawdown. But 2016→2026 contains only the V-shaped 2022
bear, and §4's whole justification is GRINDING bears (D-63 Step 2: §4 caps
the 33y drawdown at −29% vs hold-through's −76%). Deleting §4 on
V-bear-only evidence is the same error the sell-into-index idea died of.

So: re-run the combination where §4 earns its keep.

--------------------------------------------------------------------------
RULE, FROZEN 2026-07-26 BEFORE THE RUN — do not edit after data exists
--------------------------------------------------------------------------
Universe: D-63 Step 2's GRIND_UNIV verbatim (AMZN NVDA AAPL MSFT ADBE INTC
CSCO QCOM ORCL EBAY), 1993→2026, dot-com + 2008 + 2022. SURVIVOR-BIASED by
construction and that bias FLATTERS hold-through — inherited from D-63 and
restated, not fixed, so these rows sit directly beside its table.
Selection: the committed `_screen` (⭐ else 🔵), UNCHANGED, so this isolates
the discipline question from the #125 selection question entirely.
Arms: neither · §4 only · §5.2 only · §4+§5.2. §4-only and §5.2-only must
reproduce D-63's committed Step 2 numbers or the run is void.

VERDICT RULE (pre-committed, on the 33y grinder window):
  (a) INSURANCE SURVIVES iff the combination gives up no more than 5
      points of drawdown protection vs §4 alone. MaxDD values are NEGATIVE,
      so the test is  dd_combo >= dd_4only - 5.0.
      *** CRITERION AMBIGUITY, RECORDED (2026-07-26, PRD §8.5 style).* The
      docstring first said "MaxDD(combo) <= MaxDD(§4) + 5 points", which on
      signed values evaluates the WRONG WAY (−37 <= −24 is true, yet −37 is
      8 points WORSE protection than −29). The bug was found while reading
      the first run's output, so the sign fix was made with the numbers
      visible — a real deviation from clean pre-registration, disclosed
      rather than buried. The intent above was unambiguous in prose from
      the start ("no more than 5 points given up"); BOTH readings are
      published in BACKTEST_RESULTS §32 so nobody has to trust this note.
      Prong (b) is unaffected and is the decisive one either way.
  (b) TRASH-TAKER PAYS iff MOIC(§4+§5.2) >= MOIC(§4 only).
  a AND b  -> the live combination is sound. Publish, change nothing.
  a not b  -> §5.2 costs wealth inside §4 without adding safety; propose
              making §5.2 bear-aware (skip the per-name leg while 🐻).
  not a    -> the combination does NOT insure; §4's premium is being paid
              without the cover it is bought for. Escalate — that is a
              live risk finding, not a tuning opportunity.
Whatever lands, NOTHING ships from this file: Part III rule 5 — the study
runs, a separate decision acts on it. Any change to §4 or §5.2 is a
SURVIVAL/EXIT recalibration (R10 unthrottled lane) needing its own
pre-registered gate, registry entry and demotion checker.

Implementation honesty: `run_combo` below duplicates `run_mode`'s month
loop because that function cannot express two legs at once. It is
regression-locked — with the per-name leg disabled it must reproduce the
frozen `run_mode("faithful")` to 1e-12 on every window, else the run
aborts. That assert is the only thing making these numbers comparable.

Reproduce:  python homily_discipline_backtest.py     (~15 min)
"""
import sys
import datetime

from homily_bear_backtest import (COST, _screen, _deploy, regime_series,
                                  month_first_idx, close_on, run_mode,
                                  _fetch, CAUTION_MONTHS, GRIND_UNIV)
from homily_strategy_backtest import UNIV_B, run_dca
from homily_danny import danny_signal
from homily_data import fetch_daily

REENTRY_TRANCHES = 3
HONEST = [(datetime.date(2021, 7, 22), datetime.date(2026, 7, 21), "5y"),
          (datetime.date(2016, 7, 22), datetime.date(2026, 7, 21), "10y")]
INSURANCE_TOL = 5.0          # percentage points, frozen


def run_combo(names, data, spy, qqq, *, bear_leg=True, perstock_leg=True,
              min_bars=260, index_bars=None, win=None, caution_months=None):
    """§4 (bear_leg) and/or §5.2 (perstock_leg). Both False = hold-through.
    Mirrors run_mode's arithmetic exactly; see the regression assert."""
    cm = CAUTION_MONTHS if caution_months is None else caution_months
    is_bear = regime_series(spy, qqq)
    months = [spy[i][0] for i in month_first_idx(spy)][1:]
    if win:
        months = [m for m in months if win[0] <= m <= win[1]]

    cash = paid = 0.0
    hold, core, powder = {}, 0.0, 0.0
    reentry_left = 0
    caution = {}
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

        if bear_leg:
            if onset:                       # §4: sell satellites -> powder
                for n, sh in list(hold.items()):
                    px = close_on(data[n], d)
                    if px:
                        powder += sh * px * (1 - COST)
                        trades += 1
                hold = {}
                reentry_left = 0
            if bear:                        # §4 step 6: contributions->index
                if index_bars and ipx > 0 and cash > 0:
                    core += cash * (1 - COST) / ipx
                    cash = 0.0
                    trades += 1
                else:
                    cash_months += 1
                prev_bear = bear
                continue
            if prev_bear:                   # 🐂 resumes -> thirds re-entry
                reentry_left = REENTRY_TRANCHES
            if reentry_left > 0 and powder > 0:
                tranche = powder / reentry_left
                cash += tranche
                powder -= tranche
                reentry_left -= 1

        if perstock_leg:                    # §5.2 per-name exit
            for n in list(hold):
                bars = [b for b in data[n] if b[0] <= d]
                if len(bars) < min_bars:
                    continue
                try:
                    st = danny_signal(n, bars).state
                except Exception:                          # noqa: BLE001
                    continue
                if st == "CAUTION":
                    caution[n] = caution.get(n, 0) + 1
                    if caution[n] >= cm and hold[n] > 0:
                        px = close_on(data[n], d)
                        if px:
                            half = hold[n] * 0.5
                            cash += half * px * (1 - COST)
                            hold[n] -= half
                            trades += 1
                            caution[n] = 0
                else:
                    caution[n] = 0

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


ARMS = (("neither (hold-through)", False, False),
        ("§4 only  (D-63 mode d)", True, False),
        ("§5.2 only (D-63 mode f)", False, True),
        ("§4 + §5.2  << LIVE", True, True))


def _regress(names, data, spy, qqq, wins):
    print("REGRESSION — combo(bear-only) must equal frozen run_mode('faithful'):")
    ok = True
    for w in wins:
        a = run_combo(names, data, spy, qqq, perstock_leg=False,
                      index_bars=spy, win=w)
        b = run_mode(names, data, spy, qqq, "faithful", index_bars=spy, win=w)
        drift = max(abs(x - y) for x, y in zip(a[:3], b[:3]))
        lbl = w[2] if len(w) > 2 else f"{w[0]}→{w[1]}"
        print(f"   {lbl:<10} drift={drift:.2e}  "
              f"{'OK' if drift < 1e-12 else 'DRIFT'}")
        ok &= drift < 1e-12
    return ok


def _table(names, data, spy, qqq, win, label, bar=None):
    print(f"\n=== {label} ===")
    if bar:
        print(f"    benchmark: DCA QQQ {bar[0]:.2f} MOIC / MaxDD "
              f"{bar[2]*100:.0f}%")
    print(f"    {'arm':<26}{'MOIC':>8}{'CAGR':>8}{'MaxDD':>8}{'trades':>8}")
    out = {}
    for lbl, bl, pl in ARMS:
        m, c, dd, _cm, tr = run_combo(names, data, spy, qqq, bear_leg=bl,
                                      perstock_leg=pl, index_bars=spy,
                                      win=win)
        out[lbl] = (m, dd * 100)
        print(f"    {lbl:<26}{m:>8.2f}{c*100:>7.1f}%{dd*100:>7.0f}%{tr:>8}")
    return out


def main():
    spy = fetch_daily("SPY", rng="max")
    qqq = fetch_daily("QQQ", rng="max")

    print("### honest control (universe B) — context for the grinder run ###")
    dataB, _dead = _fetch(UNIV_B, "max")
    liveB = [n for n in UNIV_B if n in dataB]
    if not _regress(liveB, dataB, spy, qqq, HONEST):
        sys.exit("regression failed — run void")
    for w0, w1, wl in HONEST:
        _table(liveB, dataB, spy, qqq, (w0, w1),
               f"universe B honest · {wl}", run_dca(qqq, spy, win=(w0, w1)))

    print("\n\n### THE GRINDER RUN — dot-com + 2008 + 2022 (SURVIVOR BIAS) ###")
    dataG, deadG = _fetch(GRIND_UNIV, "max")
    liveG = [n for n in GRIND_UNIV if n in dataG]
    print(f"{len(liveG)} names; unfetchable: {deadG or 'none'}")
    gwin = (datetime.date(1993, 1, 1), datetime.date(2026, 7, 21))
    if not _regress(liveG, dataG, spy, qqq, [(*gwin, "33y")]):
        sys.exit("regression failed — run void")
    g = _table(liveG, dataG, spy, qqq, gwin, "grinding bears · 33y")

    mo_c, dd_c = g["§4 + §5.2  << LIVE"]
    mo_4, dd_4 = g["§4 only  (D-63 mode d)"]
    a = dd_c >= dd_4 - INSURANCE_TOL      # signed: less negative = safer
    b = mo_c >= mo_4
    print(f"\n--- PRE-COMMITTED VERDICT (grinder window) ---")
    print(f"  (a) insurance survives: MaxDD combo {dd_c:.0f}% vs §4-only "
          f"{dd_4:.0f}% — gave up {abs(dd_c - dd_4):.0f}pt of protection, "
          f"tol {INSURANCE_TOL:.0f}pt -> {'PASS' if a else 'FAIL'}")
    print(f"  (b) trash-taker pays:   MOIC combo {mo_c:.2f} vs §4-only "
          f"{mo_4:.2f} -> {'PASS' if b else 'FAIL'}")
    print("  =>", "SOUND — publish, change nothing" if a and b else
          "§5.2 costs wealth inside §4 without adding safety — propose "
          "bear-aware §5.2" if a else
          "COMBINATION DOES NOT INSURE — escalate, live risk finding")


if __name__ == "__main__":
    main()
