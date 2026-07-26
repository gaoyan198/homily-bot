#!/usr/bin/env python3
"""
#130 · §5.2 WITH its F-gate — the repo's best-measured arm, tested for real.
============================================================================

The gap. BACKTEST_RESULTS §3 (D-63) concluded: *"The per-name §5.2 exit (f)
is the only mode that ADDED return on the honest control (+3.4 pts/yr over
hold at 10y)"* — and then admitted in its own footnote: *"(Caveat: (f) was
tested without its F-gate — an aggressive upper bound.)"* Every later
decision leaned on the headline and not the footnote: §16b's league table,
#51's 12→8 week promotion, and this session's #126 all measure a §5.2 that
sells on the ⚪ clock ALONE.

The live rule (PLAYBOOK §5.2, `homily_positions.trim_flags`) needs BOTH:
⚪ CAUTION for 8+ weeks **AND** fundamentals failing, F:0–1. Counted on the
live signals log, that second condition blocks **85% of the sells the
backtest made** (88 of 593 ⚪ rows carry F:0–1; a further 13.5% are F:—,
which can never fire). So the arm this repo calls its best is being scored
on a rule that pulls the trigger ~6.7× more often than the real one.

--------------------------------------------------------------------------
RULE, FROZEN 2026-07-26 BEFORE THE RUN — do not edit after data exists
--------------------------------------------------------------------------
POINT-IN-TIME F. At month `d`, F is rebuilt from EDGAR facts whose `filed`
date is <= d — never the current cache, which would leak the future into
every sell decision. The SCORING is `homily_fund.checks_from` itself (R6:
live logic, never a reimplementation); only the as-of *selection* is new,
and it mirrors `homily_quality`'s (filed <= asof), the machinery already
trusted for the #66 replay.

ARMS (selection identical throughout — the committed `_screen`; this is a
discipline question, not a selection one):
  hold      no per-name exit at all
  ungated   sell half after CAUTION_MONTHS in ⚪            <- what D-63 measured
  gated     sell half after CAUTION_MONTHS in ⚪ AND F:0–1  <- the LIVE rule
Benchmarks: DCA SPY / DCA QQQ over the same months.
Windows: honest control B at 5y and 10y, plus the 33y grinder universe.

VERDICT RULE (pre-committed, decided on the HONEST 10y window):
  (a) gated MOIC > hold MOIC  -> §5.2 still adds return; D-63's claim
      survives, and the correct magnitude is whatever this prints.
  (b) gated MOIC <= hold MOIC -> the "+3.4 pts/yr, the only mode that ADDED
      return" claim is an artefact of the ungated test and must be RETRACTED
      in §3 and §16b. That would also undercut #51's 12→8wk promotion, whose
      whole subject is this clock, and this session's "the alpha is in the
      exits" conclusion.
Either way NOTHING SHIPS from this file: Part III rule 5. A retraction is a
docs change proposed to the owner, not executed here.

KNOWN ISSUE, RECORDED NOT FIXED: `trim_flags` tests `int(F_numerator) <= 1`,
so **F:1/1 fires while F:2/2 does not** — both are 100% pass rates. 24 live
rows carry F:1/1. That is the live rule's behaviour and this study
reproduces it faithfully rather than quietly improving it; whether the
numerator test should be a RATIO is a separate question for its own item.

Reproduce:  python homily_fgate_backtest.py      (~20 min; ~40 EDGAR pulls)
"""
import sys
import datetime

from homily_bear_backtest import (COST, _screen, _deploy, regime_series,
                                  month_first_idx, close_on, _fetch,
                                  CAUTION_MONTHS, GRIND_UNIV)
from homily_strategy_backtest import UNIV_B, run_dca
from homily_danny import danny_signal
from homily_data import fetch_daily
from homily_fund import cik_of, checks_from, REV_TAGS, NI_TAGS, OCF_TAGS
from homily_quality import concept_rows

SHARES_TAG = [("dei", "EntityCommonStockSharesOutstanding")]


def f_series(ticker):
    """-> the raw as-of-able fact rows for one name, or None."""
    cik = cik_of(ticker)
    if cik is None:
        return None
    out = {}
    for key, tags in (("rev", REV_TAGS), ("ni", NI_TAGS),
                      ("ocf", OCF_TAGS), ("sh", SHARES_TAG)):
        try:
            out[key] = concept_rows(cik, tags) or []
        except Exception:                                  # noqa: BLE001
            out[key] = []
    return out


def _asof_pairs(rows, d):
    """Last two ANNUAL (end, val) points visible at `d` — latest filing per
    period end, filings after `d` discarded."""
    seen = {}
    iso = d.isoformat()
    for end, filed, val in rows:
        if filed and filed > iso:
            continue                       # not published yet at `d`
        prev = seen.get(end)
        if prev is None or (filed or "") >= prev[0]:
            seen[end] = (filed or "", val)
    series = sorted((e, v) for e, (_f, v) in seen.items())
    return series[-2:] if len(series) >= 2 else None


def f_tag_at(series, d):
    """Point-in-time 'F:n/m' via the LIVE checks_from, or None when nothing
    is computable (the honest F:— — which never fires the §5.2 rule)."""
    if not series:
        return None
    rev = _asof_pairs(series["rev"], d)
    ni = _asof_pairs(series["ni"], d)
    ocf = _asof_pairs(series["ocf"], d)
    shp = _asof_pairs(series["sh"], d)
    sh = (shp[0][1], shp[1][1]) if shp else None
    checks = checks_from(rev, ni, ocf, sh)
    if not checks:
        return None
    return sum(1 for v in checks.values() if v), len(checks)


def run(names, data, spy, qqq, mode, fdata, *, index_bars=None, win=None):
    """mode: 'hold' | 'ungated' | 'gated'. Mirrors run_mode's arithmetic for
    the no-exit path; the per-name leg is the only thing that varies."""
    is_bear = regime_series(spy, qqq)
    months = [spy[i][0] for i in month_first_idx(spy)][1:]
    if win:
        months = [m for m in months if win[0] <= m <= win[1]]
    cash = paid = 0.0
    hold, core = {}, 0.0
    caution = {}
    nav, unit_val, units = [], 1.0, 0.0
    trades = blocked = fired = 0

    for d in months:
        ipx = (close_on(index_bars, d) or 0) if index_bars else 0
        val = (cash + core * ipx
               + sum(sh * (close_on(data[n], d) or 0)
                     for n, sh in hold.items()))
        if units > 0:
            unit_val = val / units
        nav.append(unit_val)
        cash += 1.0
        paid += 1.0
        units += 1.0 / unit_val

        if mode != "hold":
            for n in list(hold):
                bars = [b for b in data[n] if b[0] <= d]
                if len(bars) < 260:
                    continue
                try:
                    st = danny_signal(n, bars).state
                except Exception:                          # noqa: BLE001
                    continue
                if st != "CAUTION":
                    caution[n] = 0
                    continue
                caution[n] = caution.get(n, 0) + 1
                if caution[n] < CAUTION_MONTHS or hold[n] <= 0:
                    continue
                if mode == "gated":
                    ft = f_tag_at(fdata.get(n), d)
                    # live trim_flags: fires on numerator <= 1; F:— never
                    if ft is None or ft[0] > 1:
                        blocked += 1
                        continue
                px = close_on(data[n], d)
                if px:
                    half = hold[n] * 0.5
                    cash += half * px * (1 - COST)
                    hold[n] -= half
                    trades += 1
                    fired += 1
                    caution[n] = 0

        picks = _screen(names, data, d, 260)
        cash, core, tr, _cw = _deploy(picks, cash, hold, core, data, d, ipx,
                                      index_bars)
        trades += tr

    d_end = spy[-1][0] if not win else win[1]
    eipx = (close_on(index_bars, d_end) or 0) if index_bars else 0
    final = (cash + core * eipx
             + sum(sh * (close_on(data[n], d_end) or 0)
                   for n, sh in hold.items()))
    nav.append(final / units)
    yrs = len(months) / 12
    cagr = (nav[-1] / nav[0]) ** (1 / yrs) - 1
    mdd = min(nav[j] / max(nav[:j + 1]) - 1 for j in range(1, len(nav)))
    return final / paid, cagr, mdd, fired, blocked


def main():
    spy = fetch_daily("SPY", rng="max")
    qqq = fetch_daily("QQQ", rng="max")
    universes = [("B honest", UNIV_B,
                  [(datetime.date(2021, 7, 22), datetime.date(2026, 7, 21), "5y"),
                   (datetime.date(2016, 7, 22), datetime.date(2026, 7, 21), "10y")]),
                 ("GRIND (survivor-biased)", GRIND_UNIV,
                  [(datetime.date(1993, 1, 1), datetime.date(2026, 7, 21), "33y")])]
    for ulabel, univ, wins in universes:
        data, dead = _fetch(univ, "max")
        live = [n for n in univ if n in data]
        print(f"\n### {ulabel} — {len(live)} names "
              f"{'(dead: ' + ', '.join(dead) + ')' if dead else ''} ###")
        print("  building point-in-time F from EDGAR …", flush=True)
        fdata = {}
        for n in live:
            fdata[n] = f_series(n)
        got = sum(1 for v in fdata.values() if v)
        print(f"  F reconstructable for {got}/{len(live)} names")
        for w0, w1, wl in wins:
            q = run_dca(qqq, spy, win=(w0, w1))
            s = run_dca(spy, spy, win=(w0, w1))
            print(f"\n  --- {wl} ({w0} → {w1}) ---")
            print(f"  {'arm':<26}{'MOIC':>8}{'CAGR':>8}{'MaxDD':>8}"
                  f"{'sells':>7}{'blocked':>9}")
            res = {}
            for mode in ("hold", "ungated", "gated"):
                m, c, dd, fired, blk = run(live, data, spy, qqq, mode, fdata,
                                           index_bars=spy, win=(w0, w1))
                res[mode] = m
                print(f"  {mode:<26}{m:>8.2f}{c*100:>7.1f}%{dd*100:>7.0f}%"
                      f"{fired:>7}{blk:>9}")
            print(f"  {'DCA SPY':<26}{s[0]:>8.2f}")
            print(f"  {'DCA QQQ  << the bar':<26}{q[0]:>8.2f}")
            if wl == "10y" and ulabel.startswith("B"):
                ok = res["gated"] > res["hold"]
                print(f"\n  *** PRE-COMMITTED VERDICT (honest 10y): gated "
                      f"{res['gated']:.2f} vs hold {res['hold']:.2f} -> "
                      f"{'(a) §5.2 STILL ADDS' if ok else '(b) RETRACT §3/§16b'}"
                      f" ***")
                print(f"      ungated (what D-63 published) {res['ungated']:.2f}"
                      f" — the gap is the footnote's cost")


if __name__ == "__main__":
    main()
