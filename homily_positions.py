#!/usr/bin/env python3
"""
Position-aware book math (backlog #27).
========================================

Turns raw shares+cost (`holdings.json` schema `_v: 2`) into the per-name
view PLAYBOOK §1 talks about: % of the STOCK book (not the whole account —
Bucket A's index sleeve is a separate, never-sold pool) and a 10%-cap
proximity note. Pure math over prices the caller already fetched; never
touches money, never places an order.

Bucket A/B/C (PLAYBOOK §1):
  A — the index sleeve (CSPX today). Hardcoded via holdings.json's
      per-position "bucket" field. Never sold, never timed, excluded from
      the stock-book denominator and the cap.
  B — "earned core": a stock that GREW to >=10% of the book *while
      following the add rules* and passes fundamentals. There is no
      add-history to detect that mechanically yet (the signals ledger,
      #13, only started 2026-07-08) — so B is a MANUAL tag
      (`"bucket": "B"`) the owner sets once they've made that judgment
      call, same as PLAYBOOK already asks them to. Automating the
      detection is #28's job once enough ledger history accrues.
  C — everyone else. The default, and the only bucket the cap warning
      ever fires for.

R12: non-USD positions (9992.HK) are excluded from the USD stock-book
denominator — no cross-currency math until an FX line ships (#53), same
rule the buy-day copilot (#31) will use.
"""
import json
import os

HERE = os.path.dirname(os.path.abspath(__file__))
HOLDINGS_FILE = os.path.join(HERE, "holdings.json")

CAP_PCT = 10.0    # PLAYBOOK §1 / §5 Rule 1: the per-name hard cap
WARN_PCT = 8.0    # PRD #27 example: "NVDA 9.4% — next add breaches the cap"


def load_positions(path=HOLDINGS_FILE):
    """holdings.json (_v:2) -> {ticker: {"yahoo","shares","cost","bucket"?,
    "currency"?}}. `_v:1` files (bare ticker->yahoo maps) have no positions
    and yield {} — the digest just skips book-math annotation until synced."""
    raw = json.load(open(path))
    if raw.get("_v") != 2:
        return {}
    return dict(raw.get("positions", {}))


def stock_book_value(positions, prices):
    """Sum of shares*price across every USD, non-Bucket-A position with a
    known price. `prices` is {ticker: last_close}, using the same raw
    (non-adjusted) closes the digest already displays (R1)."""
    total = 0.0
    for tk, p in positions.items():
        if p.get("bucket") == "A" or p.get("currency", "USD") != "USD":
            continue
        px = prices.get(tk)
        if px is None:
            continue
        total += p["shares"] * px
    return total


def position_view(ticker, positions, prices, book_value):
    """-> {"pct", "bucket", "cap_note"} for a tracked, priced, USD, non-A
    position; None if the ticker isn't a position homily_ledger/daily_run
    should annotate (not held, no price yet, index sleeve, non-USD, or
    holdings.json hasn't been synced to _v:2)."""
    p = positions.get(ticker)
    if p is None:
        return None
    bucket = p.get("bucket", "C")
    if bucket == "A" or p.get("currency", "USD") != "USD":
        return None
    px = prices.get(ticker)
    if px is None or book_value <= 0:
        return None
    pct = 100.0 * p["shares"] * px / book_value
    if bucket == "B":
        cap_note = None                       # earned core: the cap doesn't apply
    elif pct >= CAP_PCT:
        cap_note = "OVER CAP — no more adds"
    elif pct >= WARN_PCT:
        cap_note = "next add breaches the cap"
    else:
        cap_note = None
    return {"pct": pct, "bucket": bucket, "cap_note": cap_note}
