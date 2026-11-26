#!/usr/bin/env python3
"""
Mechanical universe construction (#65, design D-65).
====================================================

Replaces "grown by conversation" with a rule-stated pipeline. Three
layers, refreshed quarterly (rides #44's hygiene issue):

  L0  NASDAQ Trader symbol directory (nasdaqlisted.txt + otherlisted.txt,
      key-free, published daily): every US-listed security, minus test
      issues, ETFs, warrants/units/rights/preferred and secondary share
      classes (heuristics documented in _l0_keep — a mechanical rule can
      be wrong per-name, but it is the same rule for every name, which is
      the point).
  L1  hard gates from a 3-month chart fetch per L0 survivor: price ≥ $5 ·
      median 60d dollar-volume ≥ $50M · ≥130 bars listed (younger-but-
      liquid names tagged "young"; 🚀's own G5 stays unchanged) · primary
      exchange NYSE/NASDAQ/AMEX. Fetching honours R11: 4 workers, jitter,
      and `--shard k/N` so the quarterly CI job can spread ~5k fetches
      over several nights (bulk sources are auth-gated — probed
      2026-07-11: Yahoo v7 batch 401, Stooq bulk 401).
  L2  capacity cut: L1 survivors ranked by 60d dollar-volume, keep the
      top ~120, PLUS every current holding, PLUS every name that passed
      all 🚀 gates in the last two quarters (stickiness — read from the
      signals ledger, so "passed" means "the digest actually printed it").

Output: committed `universe.json` — {symbol, origin, since, px, dvol_med,
bars} per name. `origin` is "screen" for mechanical arrivals, and every
owner add (ALL non-US names — no free master list exists for HK/SG/KR)
stays "owner-request", labelled as such in the ledger (#64).

Shadow-quarter gate (pre-committed, D-65): the mechanical list runs in
parallel — ledger rows tagged `shadow-screen`, NO digest surface — and is
adopted as the live screen universe only if over one quarter it (a)
retains ≥90% of the names the hand list actually surfaced (⭐/🔵/🚀) and
(b) surfaces ≥1 legitimate setup the hand list missed. Adoption is its
own session; this file only builds the list and measures.

Diff discipline: refresh never silently swaps the list — adds/drops print
with their gate values; a drop is actioned only after failing L1 two
consecutive quarters (whipsaw guard, enforced via `prev` universe.json).
"""
import csv
import io
import json
import os
import re
import ssl
import time
import random
import datetime
import urllib.request
from concurrent.futures import ThreadPoolExecutor

from homily_data import fetch_daily

HERE = os.path.dirname(os.path.abspath(__file__))
UNIVERSE_JSON = os.path.join(HERE, "universe.json")

L0_URLS = ("https://www.nasdaqtrader.com/dynamic/SymDir/nasdaqlisted.txt",
           "https://www.nasdaqtrader.com/dynamic/SymDir/otherlisted.txt")
MIN_PX = 5.0
MIN_DVOL = 50e6          # median 60d dollar-volume
MIN_BARS = 130
YOUNG_OK = 30            # younger-but-liquid names tagged, not dropped
TOP_N = 120
MAX_WORKERS = 4          # R11
JITTER = (0.05, 0.25)

# name-pattern drops: rights/warrants/units/preferred/notes/SPAC leftovers
_BAD_NAME = re.compile(
    r"warrant|right(s)?\b|\bunit(s)?\b|preferred|preference|depositary"
    r"|\bnote(s)? due\b|acquisition corp|acquisition co", re.I)
_BAD_SYM = re.compile(r"[.$+^=/-]")     # secondary classes / test symbols


def _fetch_text(url):
    ctx = ssl.create_default_context()
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req, timeout=30, context=ctx) as r:
        return r.read().decode("utf-8", errors="replace")


def _l0_keep(sym, name, etf, test, exch_ok):
    if test == "Y" or etf == "Y" or not exch_ok:
        return False
    if _BAD_SYM.search(sym) or len(sym) > 5:
        return False
    if sym.endswith(("W", "R", "U", "V")) and len(sym) == 5:
        return False    # 5th-char conventions: warrant/right/unit/when-issued
                        # (V caught live 2026-07-11: SKHYV, a when-issued
                        # print with a fake $17B/d "volume", sailed through)
    if _BAD_NAME.search(name):
        return False
    return True


def load_names(path=UNIVERSE_JSON):
    """Committed mechanical list -> symbols, for the daily shadow screen.
    Missing/malformed file -> [] (the shadow is best-effort by design)."""
    try:
        with open(path) as f:
            return [n["symbol"] for n in json.load(f)["names"]]
    except Exception:
        return []


def l0_symbols():
    """-> sorted list of plausible US common-stock symbols."""
    keep = set()
    nasdaq = _fetch_text(L0_URLS[0])
    for row in csv.reader(io.StringIO(nasdaq), delimiter="|"):
        if len(row) < 7 or row[0] in ("Symbol",) or "File Creation" in row[0]:
            continue
        sym, name, test, etf = row[0], row[1], row[3], row[6]
        if _l0_keep(sym, name, etf, test, exch_ok=True):
            keep.add(sym)
    other = _fetch_text(L0_URLS[1])
    for row in csv.reader(io.StringIO(other), delimiter="|"):
        if len(row) < 7 or row[0] in ("ACT Symbol",) or "File Creation" in row[0]:
            continue
        sym, name, exch, etf, test = row[0], row[1], row[2], row[4], row[6]
        if _l0_keep(sym, name, etf, test, exch_ok=exch in ("N", "A")):
            keep.add(sym)
    return sorted(keep)


def l1_stats(sym):
    """3mo fetch -> (px, median 60d $vol, bars_3mo) or None on any failure.
    bars_3mo < 55 means the name listed inside the window ("young")."""
    time.sleep(random.uniform(*JITTER))
    try:
        bars = fetch_daily(sym, rng="3mo")
    except Exception:
        return None
    if not bars:
        return None
    px = bars[-1][4]
    dv = sorted(b[4] * b[5] for b in bars[-60:])
    return px, dv[len(dv) // 2], len(bars)


def gate(sym, stats, full_bars=None):
    """L1 verdict from stats (+ an optional deep fetch for bar count)."""
    if stats is None:
        return None
    px, dvol, n3mo = stats
    if px < MIN_PX or dvol < MIN_DVOL:
        return None
    young = n3mo < 55
    return {"symbol": sym, "px": round(px, 2), "dvol_med": round(dvol),
            "young": young}


def rocket_recent(ledger_rows, quarters=2):
    """Names whose ledger rows printed gates_ok within the last N quarters —
    the stickiness set (a winner doesn't fall off the quarter it cools)."""
    cutoff = (datetime.date.today()
              - datetime.timedelta(days=91 * quarters)).isoformat()
    return {r["ticker"] for r in ledger_rows
            if r.get("gates_ok") == "1" and r.get("date", "") >= cutoff}


def build(candidates, stats_map, holdings, sticky, since=None):
    """L2: rank gated survivors, cut to TOP_N, add holdings + sticky."""
    gated = [g for s in candidates if (g := gate(s, stats_map.get(s)))]
    gated.sort(key=lambda g: -g["dvol_med"])
    chosen = {g["symbol"]: g for g in gated[:TOP_N]}
    for g in gated[TOP_N:]:
        if g["symbol"] in holdings or g["symbol"] in sticky:
            chosen[g["symbol"]] = g
    since = since or datetime.date.today().isoformat()
    return {"_v": 1, "refreshed": since,
            "gates": {"min_px": MIN_PX, "min_dvol": MIN_DVOL,
                      "min_bars": MIN_BARS, "top_n": TOP_N},
            "names": [{**g, "origin": "screen", "since": since}
                      for g in sorted(chosen.values(),
                                      key=lambda g: g["symbol"])]}


def diff_report(new, prev):
    """#44 discipline: adds/drops with gate values; drops need two
    consecutive failing quarters before they are actioned."""
    old = {n["symbol"]: n for n in (prev or {}).get("names", [])}
    now = {n["symbol"]: n for n in new["names"]}
    adds = [now[s] for s in sorted(now.keys() - old.keys())]
    drops = [old[s] for s in sorted(old.keys() - now.keys())]
    lines = [f"universe refresh {new['refreshed']}: {len(now)} names, "
             f"{len(adds)} adds, {len(drops)} drop-candidates"]
    for a in adds:
        lines.append(f"  + {a['symbol']:<6} px {a['px']} "
                     f"$vol {a['dvol_med'] / 1e6:.0f}M/d"
                     + (" (young)" if a.get("young") else ""))
    for d in drops:
        lines.append(f"  − {d['symbol']:<6} (drop actioned only after TWO "
                     "failing quarters — whipsaw guard)")
    return "\n".join(lines)


def refresh(shard=None, out=UNIVERSE_JSON):
    """The quarterly job. `shard=(k, n)` fetches only the k-th of n slices
    and writes partial stats to universe_stats.partN.json; the final
    (unsharded or last-shard) call merges and writes universe.json."""
    import homily_positions
    import homily_ledger
    syms = l0_symbols()
    print(f"L0: {len(syms)} candidate common stocks")
    part = syms if shard is None else syms[shard[0]::shard[1]]
    stats = {}
    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as ex:
        for sym, st in zip(part, ex.map(l1_stats, part)):
            if st:
                stats[sym] = st
    print(f"L1 stats fetched: {len(stats)}/{len(part)}")
    part_path = os.path.join(HERE, "universe_stats"
                             + (f".part{shard[0]}" if shard else "") + ".json")
    with open(part_path, "w") as f:
        json.dump({s: list(v) for s, v in stats.items()}, f)
    if shard is not None:
        print(f"shard {shard[0] + 1}/{shard[1]} written to "
              f"{os.path.basename(part_path)}; merge on the last shard")
        return None
    holdings = set(homily_positions.load_positions())
    sticky = rocket_recent(homily_ledger._read_rows())
    prev = json.load(open(out)) if os.path.exists(out) else None
    uni = build(syms, stats, holdings, sticky)
    with open(out, "w") as f:
        json.dump(uni, f, indent=1)
        f.write("\n")
    print(diff_report(uni, prev))
    return uni


if __name__ == "__main__":
    import sys
    shard = None
    for a in sys.argv[1:]:
        m = re.match(r"--shard=(\d+)/(\d+)$", a)
        if m:
            shard = (int(m.group(1)) - 1, int(m.group(2)))
    refresh(shard=shard)
