#!/usr/bin/env python3
"""
Sticky quality tier Q (#66, design D-66) — business quality that does not
move with the tape.
=========================================================================

The two failure modes D-66 names are one missing fact: a per-name quality
judgment that survives a drawdown. Everything price-derived collapses in a
drawdown by definition; NVDA-2022 (−60%, business intact) and PTON-2022
(−60%, business broken) must not print the same row.

Q score, 0–7 points, EDGAR-only plus exactly ONE price input (cuts
PRE-COMMITTED here before the gate backtest ran):

    +1  revenue growth ≥ 10% (latest FY vs prior, as-of filings)
    +1  revenue growth ≥ 25%
    +1  profitable: net income > 0 OR operating cash flow > 0
    +1  net margin improved vs prior FY
    +1  free cash flow positive (OCF − capex)
    +1  dilution < 12%/yr (shares outstanding)
    +1  3y total RS ≥ SPY (the "market has voted for YEARS" check — never
        a shorter window; this is deliberately the only tape input)

    Q1 compounder-grade  ≥ 5 · Q2 unproven 3–4 · Q3 broken-or-unknown ≤ 2

Sticky by construction: computed at quarterly refresh, cached in
`homily_quality_cache.json` (90-day age), frozen between refreshes — no
tape feedback loop. Non-US names print `Q:—` honestly (same stance as
F:—). This module is a SIBLING of the frozen homily_fund.py, not an edit
to it: the engine freeze stays untouched whichever way #66's gates land.
Live use today is the info-only label ONLY (D-66's cheap forward step);
the 💎 row and the thesis-break veto stay dead until their own gates pass
in their own sessions.

Point-in-time honesty: every EDGAR fact carries its `filed` date and
`asof` selection uses filed ≤ asof — the same functions serve the live
label (asof=today) and the #66 replay (asof=2021-11-01), so the backtest
cannot quietly test different arithmetic (R6).
"""
import json
import os
import time
import datetime

from homily_fund import _get, cik_of, REV_TAGS, NI_TAGS, OCF_TAGS

HERE = os.path.dirname(os.path.abspath(__file__))
CACHE = os.path.join(HERE, "homily_quality_cache.json")
MAX_AGE_DAYS = 90                     # quarterly refresh cadence
CAPEX_TAGS = [("us-gaap", "PaymentsToAcquirePropertyPlantAndEquipment"),
              ("ifrs-full", "PurchaseOfPropertyPlantAndEquipment")]
SHARES_TAG = ("dei", "EntityCommonStockSharesOutstanding")
RS_WINDOW = 756                       # 3y of trading days

Q1_MIN, Q2_MIN = 5, 3


def concept_rows(cik, candidates, unit_prefix="USD"):
    """All (end, filed, val) FY rows for the first tag that has any —
    UNFILTERED by date, so the caller picks its own as-of view."""
    for ns, tag in candidates:
        try:
            d = _get(f"https://data.sec.gov/api/xbrl/companyconcept/"
                     f"CIK{cik}/{ns}/{tag}.json")
        except Exception:
            continue
        rows = []
        for unit, items in d.get("units", {}).items():
            if ns != "dei" and not unit.upper().startswith(unit_prefix):
                continue
            for r in items:
                if ns == "dei" or (r.get("fp") == "FY" and r.get("form", "")
                                   .endswith(("10-K", "20-F", "40-F"))):
                    rows.append((r["end"], r.get("filed", ""), r["val"]))
        if rows:
            time.sleep(0.12)          # SEC courtesy, <10 req/s
            return sorted(set(rows))
        time.sleep(0.12)
    return []


def fetch_facts(ticker):
    """One EDGAR pass -> {'rev','ni','ocf','capex','shares'} row lists, or
    None for non-US / unknown names."""
    cik = cik_of(ticker)
    if cik is None:
        return None
    return {"rev": concept_rows(cik, REV_TAGS),
            "ni": concept_rows(cik, NI_TAGS),
            "ocf": concept_rows(cik, OCF_TAGS),
            "capex": concept_rows(cik, CAPEX_TAGS),
            "shares": concept_rows(cik, [SHARES_TAG])}


def asof_two(rows, asof):
    """Latest two fiscal periods among facts FILED on/before `asof`
    (latest filing per end date wins) -> [(end, val), (end, val)] or None."""
    cut = asof.isoformat()
    by_end = {}
    for end, filed, val in rows:
        if filed and filed <= cut:
            by_end[end] = val
    series = sorted(by_end.items())
    return series[-2:] if len(series) >= 2 else None


def q_points(facts, asof, rs3y):
    """-> (points 0..7, detail dict) or None when EDGAR gives nothing."""
    if not facts:
        return None
    rev = asof_two(facts["rev"], asof)
    ni = asof_two(facts["ni"], asof)
    ocf = asof_two(facts["ocf"], asof)
    capex = asof_two(facts["capex"], asof)
    sh = asof_two(facts["shares"], asof)
    if not (rev or ni or ocf):
        return None
    d = {}
    if rev and rev[0][1]:
        g = rev[1][1] / rev[0][1] - 1
        d["growth10"] = g >= 0.10
        d["growth25"] = g >= 0.25
    prof = None
    if ni:
        prof = ni[1][1] > 0
    if ocf:
        prof = bool(prof) or ocf[1][1] > 0
    if prof is not None:
        d["profit"] = prof
    if ni and rev and rev[0][1] and rev[1][1]:
        d["margin_dir"] = ni[1][1] / rev[1][1] >= ni[0][1] / rev[0][1]
    if ocf and capex:
        d["fcf"] = ocf[1][1] - capex[1][1] > 0
    elif ocf:
        d["fcf"] = ocf[1][1] > 0
    if sh and sh[0][1]:
        yrs = max(0.5, (datetime.date.fromisoformat(sh[1][0])
                        - datetime.date.fromisoformat(sh[0][0])).days / 365)
        d["dilution"] = (sh[1][1] / sh[0][1]) ** (1 / yrs) <= 1.12
    if rs3y is not None:
        d["rs3y"] = rs3y >= 0
    return sum(d.values()), d


def tier_of(points):
    return ("Q1" if points >= Q1_MIN else
            "Q2" if points >= Q2_MIN else "Q3")


def rs3y_of(closes, spy_closes):
    """3y total RS vs SPY in return points; None below 2y of history (a
    shorter window would be exactly the momentum leak D-66 forbids)."""
    if len(closes) < RS_WINDOW * 2 // 3 or len(spy_closes) < RS_WINDOW:
        return None
    n = min(RS_WINDOW, len(closes) - 1, len(spy_closes) - 1)
    return ((closes[-1] / closes[-1 - n])
            - (spy_closes[-1] / spy_closes[-1 - n]))


def quality_tag(ticker, closes=None, spy_closes=None):
    """-> 'Q1'/'Q2'/'Q3'/'Q:—', cached ~quarterly; never raises. The
    info-only label (D-66 cheap forward step) — gates NOTHING."""
    try:
        cache = json.load(open(CACHE)) if os.path.exists(CACHE) else {}
        e = cache.get(ticker)
        today = datetime.date.today()
        if e and (today - datetime.date.fromisoformat(e["asof"])).days \
                < MAX_AGE_DAYS:
            return e["tag"]
        facts = fetch_facts(ticker)
        rs = rs3y_of(closes, spy_closes) if closes and spy_closes else None
        qp = q_points(facts, today, rs)
        tag = tier_of(qp[0]) if qp else "Q:—"
        cache[ticker] = {"asof": str(today), "tag": tag}
        json.dump(cache, open(CACHE, "w"), indent=0, sort_keys=True)
        return tag
    except Exception:
        return "Q:—"


if __name__ == "__main__":
    from homily_data import fetch_daily
    spy = [b[4] for b in fetch_daily("SPY", rng="5y")]
    for t in ("NVDA", "META", "PLTR", "PTON", "LCID", "HOOD", "9992"):
        try:
            closes = [b[4] for b in fetch_daily(t if t != "9992"
                                                else "9992.HK", rng="5y")]
        except Exception:
            closes = None
        print(f"{t:<6} {quality_tag(t, closes, spy)}")
