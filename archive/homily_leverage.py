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


# --- #169 the ⚖️ line reads the real loan, every day ------------------------
# §5r Finding B: the line above keys its only loan reminder off MARGIN_ZERO,
# set 2026-08-17 to arm GAMBIT LIVE, and never looked at the actual loan —
# which then more than doubled under a silent line. The measured line below
# always prints when a loan exists, whatever MARGIN_ZERO says. Still pure:
# the caller passes gross/loan (USD) and the completed monthly closes.
MAINT = 0.25          # LEVERAGE.md's m; IBKR's concentrated maintenance can be
                      # higher, so the printed call distance FLATTERS (§1)


def if_closed_today(series):
    """{sym: (completed_closes, live_close)} -> the regime label the frozen
    month-end rule would print if the running month closed at `live` today:
    the 10m SMA rolls forward (drop the oldest, add live), same AND rule."""
    above = []
    for closes, live in series.values():
        if len(closes) < 9 or live is None:
            return None
        sma = (sum(closes[-9:]) + live) / 10.0
        above.append(live > sma)
    if not above:
        return None
    return "BULL" if all(above) else "BEAR" if not any(above) else "MIXED"


def paydown_to(gross, loan, cap):
    """Dollars of positions to sell (proceeds repay the loan) to bring
    gross/net down to `cap`. Net liq is unchanged by a sale that repays."""
    return max(0.0, gross - cap * (gross - loan))


def call_drop(gross, loan, maint=MAINT):
    """Uniform fall in every position at which equity hits maintenance:
    G(1-d)(1-m) = loan  ->  d = 1 - loan / (G(1-m)). None when no loan."""
    if loan <= 0 or gross <= 0:
        return None
    return 1.0 - loan / (gross * (1.0 - maint))


def measured_line(regime_label, gross, loan, *, if_label=None,
                  loan_note="", maint=MAINT, esc=lambda x: x):
    """-> the measured ⚖️ line, or "" without a regime read / a book."""
    k = lambda x: f"US${x / 1000:,.1f}k"
    if regime_label not in LADDER:
        return ""
    if gross <= 0 or gross - loan <= 0:
        # never silence about a loan just because the gross read failed
        return ("" if loan <= 0 else
                f"⚖️ <i>loan {k(loan)}"
                + (f" ({esc(loan_note)})" if loan_note else "")
                + " — gross unavailable today, leverage not computed; core-"
                "book target 0 (PLAYBOOK §6)</i>")
    if loan <= 0:
        return "⚖️ <i>measured: no margin loan — gross 1.00×</i>"
    lev = gross / (gross - loan)
    cap = LADDER[regime_label]
    parts = [f"measured gross <b>{lev:.2f}×</b> (loan {k(loan)}"
             + (f", {esc(loan_note)}" if loan_note else "") + ")"]
    if lev > cap + 1e-9:
        parts.append(f"⚠️ OVER the {cap:.2f}× {esc(regime_label)} cap — sell "
                     f"≈{k(paydown_to(gross, loan, cap))} to reach it")
    else:
        parts.append(f"within the {cap:.2f}× {esc(regime_label)} cap")
    if if_label and if_label != regime_label:
        c2 = LADDER[if_label]
        parts.append(f"if the month closed today: {esc(if_label)} cap "
                     f"{c2:.2f}× → ≈{k(paydown_to(gross, loan, c2))}")
    parts.append(f"core-book target 0 (PLAYBOOK §6): {k(loan)}")
    d = call_drop(gross, loan, maint)
    parts.append(f"margin call ≈ −{d:.0%} across every position "
                 f"(m={maint:.0%}; concentrated books call sooner)")
    return "⚖️ <i>" + " · ".join(parts) + "</i>"
