#!/usr/bin/env python3
"""
IBKR Flex auto-sync (backlog #32) — positions without manual edits.
===================================================================

At run start, if `IBKR_FLEX_TOKEN` + `IBKR_FLEX_QUERY` are configured
(repo secrets: a Flex Web Service token and the queryId of an
Open-Positions Flex query), fetch current positions and sync
`holdings.json`'s shares/cost. Everything else in a position entry —
`bucket`, `currency`, `sector`, `source`, the `yahoo` mapping — is
OWNER-OWNED and survives a sync untouched.

Conservative by design (the risk is silent book drift, SPECS #32):
  * shares/cost update ONLY for symbols already in holdings.json;
  * a NEW IBKR symbol is never auto-added (its yahoo mapping/sector are
    judgment calls) — it's reported in the diff for the owner to add;
  * a position gone to zero is never auto-deleted — reported likewise;
  * every change is printed as a one-line diff, and the digest carries a
    book-synced note only when something actually changed;
  * ANY failure -> yesterday's committed book + a printed warning; the
    sync is never fatal to the digest (fallback stays: tell Claude after
    trades / edit the JSON by hand).

Flex is a two-step API: SendRequest returns a reference code, then
GetStatement (with retry while the report generates). The parser pins the
fields this repo needs from the FlexQueryResponse XML — `symbol`,
`position`, `costBasisPrice`, `currency` on <OpenPosition> — and the
validate fixture (check [38]) is the contract for it.
"""
import os
import json
import time
import urllib.request
import urllib.parse
import xml.etree.ElementTree as ET

HERE = os.path.dirname(os.path.abspath(__file__))
HOLDINGS_FILE = os.path.join(HERE, "holdings.json")

BASE = ("https://gdcdyn.interactivebrokers.com"
        "/Universal/servlet/FlexStatementService")
RETRIES = 5
WAIT = 5           # seconds between GetStatement attempts while generating


def fetch_flex(token, query_id, *, opener=urllib.request.urlopen,
               sleep=time.sleep):
    """Two-step Flex fetch -> raw statement XML text. Raises on failure."""
    q = urllib.parse.urlencode({"t": token, "q": query_id, "v": "3"})
    with opener(f"{BASE}.SendRequest?{q}", timeout=30) as r:
        first = ET.fromstring(r.read())
    if (first.findtext("Status") or "").strip() != "Success":
        raise RuntimeError(f"Flex SendRequest failed: "
                           f"{first.findtext('ErrorMessage') or 'unknown'}")
    code = (first.findtext("ReferenceCode") or "").strip()
    url = (first.findtext("Url") or f"{BASE}.GetStatement").strip()
    q2 = urllib.parse.urlencode({"t": token, "q": code, "v": "3"})
    for _ in range(RETRIES):
        with opener(f"{url}?{q2}", timeout=60) as r:
            text = r.read().decode(errors="replace")
        if "<FlexQueryResponse" in text:
            return text
        sleep(WAIT)                      # report still generating
    raise RuntimeError("Flex statement not ready after retries")


def parse_positions(xml_text):
    """FlexQueryResponse XML -> {symbol: {"shares","cost","currency"}}."""
    root = ET.fromstring(xml_text)
    out = {}
    for p in root.iter("OpenPosition"):
        sym = (p.get("symbol") or "").strip().split(" ")[0]
        if not sym:
            continue
        out[sym] = {"shares": float(p.get("position") or 0),
                    "cost": float(p.get("costBasisPrice") or 0),
                    "currency": (p.get("currency") or "USD").strip()}
    return out


def sync(flex_positions, holdings_path=HOLDINGS_FILE):
    """Update shares/cost of known symbols in holdings.json; never add,
    never delete, never touch owner-owned fields. -> list of diff lines
    (empty = book already in sync, file untouched)."""
    with open(holdings_path) as f:
        doc = json.load(f)
    if doc.get("_v") != 2:
        return ["holdings.json is not _v:2 — sync skipped"]
    pos = doc["positions"]
    diff = []
    for tk, held in pos.items():
        fx = flex_positions.get(tk)
        if fx is None:
            continue
        if abs(fx["shares"] - held["shares"]) > 1e-6:
            diff.append(f"{tk}: shares {held['shares']:g} -> "
                        f"{fx['shares']:g}")
            held["shares"] = fx["shares"]
        if fx["cost"] > 0 and abs(fx["cost"] - held["cost"]) > 1e-4:
            diff.append(f"{tk}: cost {held['cost']:g} -> {fx['cost']:g}")
            held["cost"] = fx["cost"]
    for sym in sorted(set(flex_positions) - set(pos)):
        diff.append(f"NEW at IBKR, not in holdings.json (add by hand — "
                    f"yahoo/sector are judgment calls): {sym}")
    for tk in sorted(set(pos) - set(flex_positions)):
        if pos[tk].get("bucket") != "A":     # index sleeve may sit elsewhere
            diff.append(f"{tk}: in holdings.json but NOT at IBKR — "
                        "sold? remove by hand if so")
    changed = any("->" in d for d in diff)
    if changed:
        with open(holdings_path, "w") as f:
            json.dump(doc, f, indent=2, ensure_ascii=False)
            f.write("\n")
    return diff


def auto_sync(holdings_path=HOLDINGS_FILE, *, fetch=fetch_flex):
    """daily_run's entry: env-gated, never raises. -> diff lines (possibly
    a single warning line) or [] when unconfigured/in-sync."""
    token = os.getenv("IBKR_FLEX_TOKEN")
    query = os.getenv("IBKR_FLEX_QUERY")
    if not (token and query):
        return []
    try:
        flex = parse_positions(fetch(token, query))
        return sync(flex, holdings_path)
    except Exception as e:
        return [f"Flex sync failed ({e}) — using yesterday's committed book"]


if __name__ == "__main__":
    for line in auto_sync() or ["(unconfigured or in sync)"]:
        print(line)
