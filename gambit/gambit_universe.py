#!/usr/bin/env python3
"""
GAMBIT mechanical universe — DESIGNS D-G2, homily D-65 pattern.

Source: NASDAQ Trader symbol directory (nasdaqlisted.txt + otherlisted.txt,
published daily, key-free). Filters, in this order and no other (the spec is
pre-registered; changing a gate is a logged amendment, not an edit):

  1. common shares only — drop ETFs/NextShares (directory flags), test
     issues, and by name heuristic: warrants, rights, units, preferreds,
     notes/bonds/ETNs, closed-end funds, SPAC shells; off-exchange venues
     (only NYSE/NYSE-MKT/NYSE-Arca/NASDAQ survive); symbols with
     non-alphanumeric chars (class/preferred suffix conventions — this
     knowingly excludes BRK.B-style class shares, accepted for simplicity)
  2. last close >= $10
  3. 20-day median dollar volume >= US$25M
  4. keep the top 120 by 6-month (126-bar) median dollar volume

Output: universe.json with `constructed: <date>` (the construction-date
honesty stamp — only post-construction windows count as evidence, PRD G3)
and a full filter trace per symbol: every directory row appears with either
its drop reason or its gate values. Refresh is quarterly (first weekly run
of Jan/Apr/Jul/Oct — the scheduler lands in G-S6; refresh_due() is the
helper it will call). A dropped name with an open position keeps being
tracked until the position exits (enforced by the book, not this file).
"""
import concurrent.futures
import datetime
import json
import re
import ssl
import statistics
import urllib.request

import gambit_data

DIRECTORY_URLS = (
    "https://www.nasdaqtrader.com/dynamic/symdir/nasdaqlisted.txt",
    "https://www.nasdaqtrader.com/dynamic/symdir/otherlisted.txt",
)
# otherlisted Exchange codes: N=NYSE, A=NYSE MKT (AMEX), P=NYSE Arca
KEPT_EXCHANGES = {"N", "A", "P"}

# Pre-registered gates (D-G2) — do not tune outside a logged amendment
MIN_PRICE = 10.0          # last close, USD
MIN_MDV20 = 25e6          # 20-day median dollar volume, USD
TOP_N = 120               # capacity cut, by 6-month median dollar volume
MDV_LONG_WINDOW = 126     # "6-month" in trading days
MDV_SHORT_WINDOW = 20
FETCH_RANGE = "1y"        # enough bars for the 126-day median with margin
FETCH_WORKERS = 6

# Name heuristics for non-common securities. Word-ish matches so that e.g.
# "Bright Horizons" doesn't trip "right". "acquisition corp" is the SPAC
# shell tell (a post-merger operating company renames itself).
_NON_COMMON = re.compile(
    r"\b(warrant|warrants|right|rights|unit|units|preferred|preference|"
    r"pfd|notes?|bond|bonds|debenture|debentures|etn|closed[- ]end fund|"
    r"acquisition (corp|corporation|co|company|inc))\b",
    re.IGNORECASE)
_SYMBOL_OK = re.compile(r"^[A-Z]{1,5}$")


def fetch_directory(*, opener=urllib.request.urlopen):
    """Download both symbol-directory files -> (nasdaq_text, other_text)."""
    ctx = ssl.create_default_context()
    texts = []
    for url in DIRECTORY_URLS:
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with opener(req, timeout=30, context=ctx) as r:
            texts.append(r.read().decode("utf-8", errors="replace"))
    return texts[0], texts[1]


def parse_directory(nasdaq_text, other_text):
    """Pipe-delimited directory files -> list of candidate rows.

    Each row: {symbol, name, exchange, etf, test} with exchange 'Q' for
    NASDAQ-listed. Trailer lines ("File Creation Time...") are skipped.
    """
    rows = []
    for text, is_nasdaq in ((nasdaq_text, True), (other_text, False)):
        lines = [l for l in text.splitlines() if l.strip()]
        header = lines[0].split("|")
        idx = {h.strip(): i for i, h in enumerate(header)}
        sym_col = "Symbol" if is_nasdaq else "ACT Symbol"
        for line in lines[1:]:
            if line.startswith("File Creation Time"):
                continue
            f = line.split("|")
            if len(f) < len(header):
                continue
            rows.append({
                "symbol": f[idx[sym_col]].strip(),
                "name": f[idx["Security Name"]].strip(),
                "exchange": "Q" if is_nasdaq else f[idx["Exchange"]].strip(),
                "etf": f[idx["ETF"]].strip() == "Y",
                "test": f[idx["Test Issue"]].strip() == "Y",
                "nextshares": (f[idx["NextShares"]].strip() == "Y"
                               if "NextShares" in idx else False),
            })
    return rows


def name_filter(row):
    """Filter 1 (common shares only). -> None if kept, else the drop reason."""
    if row["test"]:
        return "test-issue"
    if row["etf"]:
        return "etf"
    if row["nextshares"]:
        return "nextshares"
    if row["exchange"] not in KEPT_EXCHANGES and row["exchange"] != "Q":
        return f"exchange:{row['exchange']}"
    if not _SYMBOL_OK.match(row["symbol"]):
        return "symbol-suffix"          # class shares / preferred conventions
    m = _NON_COMMON.search(row["name"])
    if m:
        return f"name:{m.group(1).lower()}"
    return None


def gate_metrics(bars):
    """Daily bars -> (last_close, mdv20, mdv126). Medians over the available
    tail when history is shorter than the window (a young listing's median
    is over what exists — no extra history gate is registered in D-G2)."""
    closes = [b[4] for b in bars]
    dollar = [b[4] * b[5] for b in bars]
    mdv20 = statistics.median(dollar[-MDV_SHORT_WINDOW:])
    mdv126 = statistics.median(dollar[-MDV_LONG_WINDOW:])
    return closes[-1], mdv20, mdv126


def build_universe(directory_rows, *, constructed, fetch=None, top_n=TOP_N,
                   workers=FETCH_WORKERS):
    """-> the universe dict (see module docstring). Deterministic for a given
    directory snapshot + fetch function: candidates are processed in sorted
    symbol order and the final cut is ranked (-mdv126, symbol).

    `fetch(symbol)` -> daily bars; defaults to gambit_data.fetch_daily over
    FETCH_RANGE. Fetch failures are recorded in the trace, never silent.
    """
    if fetch is None:
        def fetch(sym):
            return gambit_data.fetch_daily(sym, rng=FETCH_RANGE)

    trace = {}
    candidates = []
    for row in sorted(directory_rows, key=lambda r: r["symbol"]):
        sym = row["symbol"]
        if sym in trace:            # duplicate across the two files
            continue
        reason = name_filter(row)
        if reason:
            trace[sym] = {"drop": reason}
        else:
            candidates.append(row)

    metrics = {}
    with concurrent.futures.ThreadPoolExecutor(max_workers=workers) as pool:
        futs = {pool.submit(fetch, r["symbol"]): r for r in candidates}
        for fut in concurrent.futures.as_completed(futs):
            row = futs[fut]
            sym = row["symbol"]
            try:
                bars = fut.result()
                if not bars:
                    trace[sym] = {"drop": "no-bars"}
                    continue
                metrics[sym] = gate_metrics(bars)
            except Exception as e:              # noqa: BLE001 — trace, don't die
                trace[sym] = {"drop": f"fetch-error:{type(e).__name__}"}

    survivors = []
    for row in candidates:
        sym = row["symbol"]
        if sym not in metrics:
            continue                            # already traced above
        close, mdv20, mdv126 = metrics[sym]
        gates = {"last_close": round(close, 4),
                 "mdv20": round(mdv20), "mdv126": round(mdv126)}
        if close < MIN_PRICE:
            trace[sym] = {"drop": "price", **gates}
        elif mdv20 < MIN_MDV20:
            trace[sym] = {"drop": "mdv20", **gates}
        else:
            survivors.append((row, gates))

    survivors.sort(key=lambda x: (-x[1]["mdv126"], x[0]["symbol"]))
    kept, cut = survivors[:top_n], survivors[top_n:]
    for row, gates in cut:
        trace[row["symbol"]] = {"drop": "capacity-cut", **gates}
    members = []
    for rank, (row, gates) in enumerate(kept, 1):
        trace[row["symbol"]] = {"kept": True, **gates}
        members.append({"symbol": row["symbol"], "name": row["name"],
                        "exchange": row["exchange"], "rank": rank, **gates})

    return {
        "constructed": constructed.isoformat(),
        "spec": {"min_price": MIN_PRICE, "min_mdv20": MIN_MDV20,
                 "top_n": top_n, "mdv_long_window": MDV_LONG_WINDOW,
                 "mdv_short_window": MDV_SHORT_WINDOW},
        "directory_rows": len(directory_rows),
        "candidates_after_name_filter": len(candidates),
        "symbols": members,
        "trace": dict(sorted(trace.items())),
    }


def write_universe(universe, path="universe.json"):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(universe, f, indent=1, sort_keys=True)
        f.write("\n")


def refresh_due(constructed, today):
    """True when `today` has entered a later refresh quarter (Jan/Apr/Jul/Oct
    cycle) than the stamp. G-S6's weekly job calls this on its first run of
    each week; the first weekly run inside a new quarter rebuilds."""
    def q(d):
        return (d.year, (d.month - 1) // 3)
    return q(today) > q(constructed)


if __name__ == "__main__":
    today = datetime.date.today()
    nas, oth = fetch_directory()
    uni = build_universe(parse_directory(nas, oth), constructed=today)
    write_universe(uni)
    print(f"universe.json: {len(uni['symbols'])} names, "
          f"constructed {uni['constructed']}, "
          f"{uni['candidates_after_name_filter']} candidates screened "
          f"from {uni['directory_rows']} directory rows")
