#!/usr/bin/env python3
"""
#91 (D-91) — the leverage-ladder digest line. Pure rendering: the ladder
constants live here (single source for any future consumer), the line is a
deterministic function of the regime label + the MARGIN_ZERO env flag, and
nothing is fetched or written (the account's actual gross leverage cannot be
computed without #32's Flex sync — until those secrets exist the line
REMINDS and the owner reconciles; LEVERAGE.md §5).

Policy provenance: LEVERAGE.md (signed 2026-07-12, owner override), constants
pinned by homily_leverage_backtest.py — BULL ≤1.30× / MIXED ≤1.15× (no new
margin) / BEAR = margin zero at onset. The core monthly book never carries
margin (the −59…−76% measured paths sit inside the call boundary at any
constant ≥1.25× — arithmetic, not caution).
"""

LADDER = {"BULL": 1.30, "MIXED": 1.15, "BEAR": 1.00}
SIGNED = "2026-07-12"


def leverage_line(regime_label, margin_zero, esc=lambda x: x):
    """-> one ⚖️ ladder line for the digest, or "" without a regime read.

    `margin_zero` is the MARGIN_ZERO env truthiness (#30's flag): while the
    legacy 1.23× margin exists it is False and the shrink-only reminder
    prints; once the owner clears the loan the line goes quiet about it."""
    if regime_label not in LADDER:
        return ""
    cap = LADDER[regime_label]
    if regime_label == "BEAR":
        body = ("cap 1.00× — MARGIN TO ZERO at onset (PLAYBOOK §4 step 1); "
                "re-lever only on the §4.7 thirds re-entry")
    elif regime_label == "MIXED":
        body = f"cap {cap:.2f}× — no NEW margin, paydown drift"
    else:
        body = (f"account gross cap {cap:.2f}× — borrowed $ may fund ONLY "
                "gate-passed swing entries (paper until #93); core book: "
                "margin NEVER")
    tail = ("" if margin_zero else
            " · legacy margin is shrink-only (LEVERAGE.md §4) — paydown "
            "outranks new levered buys")
    return f"⚖️ <i>LEVERAGE ladder ({esc(regime_label)}): {esc(body)}{tail}</i>"
