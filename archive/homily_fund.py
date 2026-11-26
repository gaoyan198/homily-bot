#!/usr/bin/env python3
"""
Fundamentals flag — SEC EDGAR, informational only (PRD backlog #4).
===================================================================

Division of labour (docs §3): fundamentals decide what DESERVES a place in
the universe / what you may hold through CAUTION; the tape decides when
money flows. So this NEVER touches ⭐/🚀 logic — it only prints a tag on
new-money rows:

    F:3/3  all checks pass      F:1/3  weak      F:—  no EDGAR data (non-US)

Checks (annual figures, latest vs prior fiscal year):
    growth    revenue up > 10%
    profit    net income > 0 OR operating cash flow > 0
    dilution  shares outstanding up < 12%/yr

Plumbing: key-free EDGAR APIs (company_tickers.json for ticker→CIK, then
companyconcept per tag; us-gaap with ifrs-full fallback for 20-F filers).
SEC asks for a descriptive User-Agent and <10 req/s — we send one and touch
only the handful of names on display, with a 7-day cache committed back to
the repo by the workflow.
"""
import json, os, ssl, time, datetime, urllib.request

UA = {"User-Agent": "homily-bot personal research gaoyan157@gmail.com"}
HERE = os.path.dirname(os.path.abspath(__file__))
CACHE = os.path.join(HERE, "homily_fund_cache.json")
MAX_AGE_DAYS = 7

REV_TAGS = [("us-gaap", "RevenueFromContractWithCustomerExcludingAssessedTax"),
            ("us-gaap", "Revenues"),
            ("us-gaap", "SalesRevenueNet"),
            ("ifrs-full", "Revenue")]
NI_TAGS = [("us-gaap", "NetIncomeLoss"), ("ifrs-full", "ProfitLoss")]
OCF_TAGS = [("us-gaap", "NetCashProvidedByUsedInOperatingActivities"),
            ("us-gaap",
             "NetCashProvidedByUsedInOperatingActivitiesContinuingOperations"),
            ("ifrs-full", "CashFlowsFromUsedInOperatingActivities")]

_ctx = ssl.create_default_context()
_cik = None


def _get(url):
    req = urllib.request.Request(url, headers=UA)
    with urllib.request.urlopen(req, timeout=20, context=_ctx) as r:
        return json.load(r)


def cik_of(ticker):
    global _cik
    if _cik is None:
        raw = _get("https://www.sec.gov/files/company_tickers.json")
        _cik = {v["ticker"].upper(): f'{v["cik_str"]:010d}'
                for v in raw.values()}
    return _cik.get(ticker.upper())


def _annual(cik, candidates, unit_prefix="USD"):
    """Latest two fiscal-year values [(end, val), ...] for the first tag
    that has them."""
    for ns, tag in candidates:
        try:
            d = _get(f"https://data.sec.gov/api/xbrl/companyconcept/"
                     f"CIK{cik}/{ns}/{tag}.json")
        except Exception:
            continue
        rows = []
        for unit, items in d.get("units", {}).items():
            if not unit.upper().startswith(unit_prefix.upper()):
                continue
            for r in items:
                if r.get("fp") == "FY" and \
                        r.get("form", "").endswith(("10-K", "20-F", "40-F")):
                    rows.append((r["end"], r.get("filed", ""), r["val"]))
        by_end = {}
        for end, filed, val in sorted(rows, key=lambda x: x[1]):
            by_end[end] = val                      # latest filing wins
        series = sorted(by_end.items())
        if len(series) >= 2:
            return series[-2:]
        time.sleep(0.15)                           # stay well under 10 req/s
    return None


def _shares(cik):
    """(value ~1y ago, latest) shares outstanding from dei cover-page data."""
    try:
        d = _get(f"https://data.sec.gov/api/xbrl/companyconcept/"
                 f"CIK{cik}/dei/EntityCommonStockSharesOutstanding.json")
    except Exception:
        return None
    rows = sorted({(r["end"], r["val"])
                   for items in d.get("units", {}).values() for r in items})
    if len(rows) < 2:
        return None
    latest_d = datetime.date.fromisoformat(rows[-1][0])
    past = [r for r in rows if (latest_d -
            datetime.date.fromisoformat(r[0])).days >= 300]
    if not past:
        return None
    return past[-1][1], rows[-1][1]


def checks_from(rev, ni, ocf, sh):
    """Pure verdict logic (offline-testable)."""
    out = {}
    if rev:
        out["growth"] = rev[1][1] > rev[0][1] * 1.10
    prof = None
    if ni:
        prof = ni[1][1] > 0
    if ocf:
        prof = bool(prof) or ocf[1][1] > 0
    if prof is not None:
        out["profit"] = prof
    if sh and sh[0] > 0:
        out["dilution"] = sh[1] <= sh[0] * 1.12
    return out


def _load_cache():
    try:
        return json.load(open(CACHE))
    except Exception:
        return {}


def fund_tag(ticker):
    """-> 'F:3/3' style tag; cached 7 days; never raises."""
    try:
        cache = _load_cache()
        e = cache.get(ticker)
        today = datetime.date.today()
        if e and (today - datetime.date.fromisoformat(e["asof"])).days \
                < MAX_AGE_DAYS:
            return e["tag"]
        cik = cik_of(ticker)
        if cik is None:
            tag = "F:—"
        else:
            ck = checks_from(_annual(cik, REV_TAGS),
                             _annual(cik, NI_TAGS),
                             _annual(cik, OCF_TAGS), _shares(cik))
            tag = (f"F:{sum(ck.values())}/{len(ck)}" if ck else "F:—")
        cache[ticker] = {"asof": str(today), "tag": tag}
        json.dump(cache, open(CACHE, "w"), indent=0, sort_keys=True)
        return tag
    except Exception:
        return "F:—"


if __name__ == "__main__":
    for t in ("NVDA", "PLTR", "ALAB", "NBIS", "HOOD", "LCID", "9992"):
        print(f"{t:<6} {fund_tag(t)}")
