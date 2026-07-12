#!/usr/bin/env python3
"""
Position-aware book math (backlog #27).
========================================

Turns raw shares+cost (`holdings.json` schema `_v: 2`) into the per-name
view PLAYBOOK §1 talks about: % of the STOCK book (not the whole account —
Bucket A's index sleeve is a separate, never-sold pool) and an add-cap
proximity note (CAP_PCT — 25% since the #92 promotion, 2026-07-12; the
demotion watch below can send it back to 10%). Pure math over prices the
caller already fetched; never touches money, never places an order.

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
import re

HERE = os.path.dirname(os.path.abspath(__file__))
HOLDINGS_FILE = os.path.join(HERE, "holdings.json")

CAP_PCT = 25.0    # PLAYBOOK §3.4 / §5 Rule 1: the per-name ADD cap.
                  # PROMOTED 10→25 on 2026-07-12 (#92/D-92, owner override;
                  # promotions.json "add-cap-25"): D-67 priced the move as
                  # formally adoptable (§12) at a recorded cost — half the
                  # −95% single-name shock payout. Demotion rule armed:
                  # cap_demotion_line() below; revert to 10.0 is mandatory
                  # when it fires, not a discussion.
WARN_PCT = 20.0   # "next add breaches the cap" nudge, scaled with the cap
CAP_DEMOTION_WATCH_PCT = 15.0   # D-92: names this big are on the wreck watch
CAP_DEMOTION_DRAWDOWN = 0.50    # halved from held high-water since promotion
CAP_PROMOTED = "2026-07-12"     # HWM epoch start for the demotion watch


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


def trim_flags(pos_view, state, wk_weeks, ftag):
    """#28: PLAYBOOK §5 as executable flags, wording mirrored from §5 —
    info only, there is still no SELL state (PRD §1 survives).
      Rule 1 (§5.1): a position BOUGHT (not grown) above 10% of the stock
        book → trim back to 10%. Bucket B (earned core) gets the §5 pass,
        so only bucket C fires; #27's cap note handles the adds side, this
        flag is the trim side.
      Rule 2 (§5.2): ⚪ CAUTION 12+ weeks AND fundamentals failing (F:0–1)
        → sell half, review the remainder in one quarter. The weekly
        WHITE-circle run length stands in for "weeks in CAUTION" (the
        state is gated on that circle). F:— is unknown, not failing.
      Rule 3 (need the money / margin exists) is a human rule — no flag.
    """
    flags = []
    if pos_view and pos_view.get("bucket") == "C" \
            and pos_view.get("pct") is not None \
            and pos_view["pct"] > CAP_PCT:
        flags.append(f"RULE 1: {pos_view['pct']:.0f}% bought-not-earned — "
                     f"trim back to {CAP_PCT:.0f}%, proceeds to ⭐/index "
                     "(§5.1)")
    m = re.match(r"F:(\d)", ftag or "")
    if state == "CAUTION" and wk_weeks >= 12 and m and int(m.group(1)) <= 1:
        flags.append(f"RULE 2 REVIEW: ⚪ {wk_weeks}w + {ftag} — sell half, "
                     "review the remainder in one quarter (§5.2)")
    return flags


def cap_demotion_line(positions, prices, highs):
    """#92 (D-92) — the promoted cap's pre-registered demotion watch, checked
    every run: a held name ≥ CAP_DEMOTION_WATCH_PCT of the stock book whose
    last close sits ≤ (1−CAP_DEMOTION_DRAWDOWN)× its highest close SINCE the
    promotion date is exactly the wreck the old 10% cap insured against.

    `highs` = {ticker: max close since CAP_PROMOTED} — computed by the caller
    from bars it already fetched (no fetching here). Returns "" (quiet) or
    the 🚨 banner. The banner does not edit constants: the revert of CAP_PCT
    to 10.0 is executed in the next session, MANDATORY per promotions.json
    ("add-cap-25"), and this line keeps printing until it happens."""
    if not positions or not prices:
        return ""
    book = stock_book_value(positions, prices)
    if book <= 0:
        return ""
    hits = []
    for tk, p in positions.items():
        if p.get("bucket") == "A" or p.get("currency", "USD") != "USD":
            continue
        px, hi = prices.get(tk), (highs or {}).get(tk)
        if px is None or not hi:
            continue
        pct = 100.0 * p["shares"] * px / book
        if pct >= CAP_DEMOTION_WATCH_PCT and \
                px <= (1.0 - CAP_DEMOTION_DRAWDOWN) * hi:
            hits.append(f"{tk} {pct:.0f}% of book, {px / hi - 1.0:+.0%} from "
                        f"its post-promotion high")
    if not hits:
        return ""
    return ("🚨 <b>ADD-CAP DEMOTION TRIGGERED (#92)</b> — " +
            "; ".join(hits) +
            f". Per promotions.json the {CAP_PCT:.0f}% cap REVERTS to 10% "
            "in the next session — mandatory, not a discussion; this line "
            "prints until the revert lands.")
