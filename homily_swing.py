#!/usr/bin/env python3
"""
#90 (D-90) — the SWING (paper) digest section for the merged gambit sleeve.

Renders a short fenced block from the sleeve's committed `gambit/snapshot.json`:
P2 paper state + gate progress toward the #93 live-arming read. Pure function
of the snapshot dict + the pinned run date — no fetching, no clock, no
valuation (the weekly ♟️ digest from `gambit/weekly_run.py` carries the priced
book; this block only reports state the repo already committed) — so the
golden digest stays deterministic and the daily run can never be slowed or
broken by the sleeve. Non-fatal by construction: no snapshot, no block.

The P2 gate (gambit PRD §5.2, unchanged by the merge): ≥26 weeks of paper AND
≥20 closed trades AND expectancy > 0 AND green vs the QQQ bar — no backtest
credit. The counters print daily so every reader knows exactly how far the
sleeve is from earning real money (#93/D-93). This module never writes the
ledger, the journal, or the snapshot (R3): the sleeve's state belongs to the
weekly loop alone.
"""
import datetime
import json
from pathlib import Path

_GAMBIT = Path(__file__).resolve().parent / "gambit"
SNAPSHOT = _GAMBIT / "snapshot.json"
LIVE_BOOK = _GAMBIT / "gambit_live_book.json"
P2_WEEKS = 26          # gambit PRD §5.2 — calendar weeks of paper ledger
P2_TRADES = 20         # gambit PRD §5.2 — closed trades
KILL_FRAC = 0.70       # mirror of gambit_live.KILL_EQUITY_FRAC (A5)


def load_state(path=SNAPSHOT):
    """The committed paper-book state, or None (missing/corrupt = no block)."""
    path = Path(path)
    if not path.exists():
        return None
    try:
        return json.loads(path.read_text())
    except Exception:
        return None


def swing_block(state, today, esc=lambda x: x):
    """-> the fenced SWING (paper) block, or "" when there is no sleeve state.

    `today` is the pinned SGT run date (R7); weeks accrue from the paper
    book's own inception stamp, never from a local clock. Deterministic:
    same state + same date = same text, which is what check [48] pins."""
    if not state:
        return ""
    try:
        inception = datetime.date.fromisoformat(str(state["inception"]))
        weeks = max(0, (today - inception).days // 7)
        npos = len(state.get("positions") or {})
        pend = len(state.get("pending") or [])
        closed = int(state.get("closed_trades") or 0)
        cash = float(state.get("cash") or 0.0)
    except Exception:
        return ""
    exp = ("expectancy: weekly ♟️ digest" if closed
           else "expectancy n/a (0 closed)")
    return "\n".join([
        "♟️ <b>SWING sleeve — PAPER (S1-pure, Amendment A4)</b> · "
        f"P2 gate: wk {weeks}/{P2_WEEKS} · closed {closed}/{P2_TRADES} · "
        f"{esc(exp)}",
        f"<i>book: {npos} open · {pend} pending · cash ${cash:,.0f} · "
        "LIVE_ORDERS=off — this book places no real orders; it is the "
        "no-stops counterfactual the LIVE book (A5, below) is scored "
        "against</i>",
    ])


def load_live(path=LIVE_BOOK):
    """The committed live-book state, or None (missing/corrupt = no block)."""
    path = Path(path)
    if not path.exists():
        return None
    try:
        return json.loads(path.read_text())
    except Exception:
        return None


def live_block(book, esc=lambda x: x):
    """#93/A5 — the daily LIVE status: where the bets stand, kill-line
    distance, hold/kill state. Numbers are the last weekly mark (the live
    runner owns valuation; this stays fetch-free and deterministic)."""
    if not book:
        return ""
    try:
        if book.get("killed"):
            k = book["killed"]
            return ("🚨 <b>SWING LIVE — KILLED "
                    f"{esc(str(k.get('date', '')))}</b>: "
                    f"{esc(str(k.get('reason', '')))} — liquidate per the "
                    "last order sheet; failure memo owed; experiment over.")
        if not book.get("armed"):
            return ("♟️ <i>SWING LIVE — waiting for the clean slate: set "
                    "MARGIN_ZERO once the legacy loan clears; the first "
                    "order sheet prints the Saturday after (A5)</i>")
        eq = float(book.get("equity") or 0.0)
        contrib = float(book.get("contributed") or 0.0)
        kill = KILL_FRAC * contrib
        realized = round(sum(float(r.get("pnl", 0.0))
                             for r in book.get("realized") or []), 2)
        npos = len(book.get("positions") or {})
        pend = len(book.get("pending") or [])
        room = eq - kill
        state = ("HOLD per plan" if not pend
                 else f"{pend} order(s) on Monday's sheet")
        return "\n".join([
            f"♟️ <b>SWING LIVE (A5)</b> · equity ${eq:,.0f} of "
            f"${contrib:,.0f} contributed · realized {realized:+,.0f} · "
            f"{npos} open · {esc(state)}",
            f"<i>kill line ${kill:,.0f} (${room:,.0f} of room) — breach = "
            "liquidate + failure memo, mandatory; stops/TPs sit at IBKR, "
            "adjust only at re-ranks (PLAYBOOK §9)</i>",
        ])
    except Exception:
        return ""


def monthly_block(book, today, esc=lambda x: x):
    """First-run-of-month realized report (A5): last month's closed trades
    with reasons, cumulative realized, and the sweep suggestion — proceeds
    fund the monthly DCA; losses are the recorded cost of business."""
    if not book or not book.get("armed"):
        return ""
    try:
        first = today.replace(day=1)
        prev_last = first - datetime.timedelta(days=1)
        prev = prev_last.strftime("%Y-%m")
        rows = [r for r in (book.get("realized") or [])
                if str(r.get("date", "")).startswith(prev)]
        total = round(sum(float(r["pnl"]) for r in rows), 2)
        cum = round(sum(float(r.get("pnl", 0.0))
                        for r in book.get("realized") or []), 2)
        eq = float(book.get("equity") or 0.0)
        contrib = float(book.get("contributed") or 0.0)
        sweep = max(0.0, eq - contrib)
        lines = [f"♟️ <b>SWING LIVE — {esc(prev)} realized report (A5)</b>: "
                 f"{total:+,.2f} this month · {cum:+,.2f} cumulative"]
        for r in rows[:8]:
            lines.append(f"　{esc(str(r['sym']))} {float(r['pnl']):+,.2f} "
                         f"[{esc(str(r['reason']))}]")
        if not rows:
            lines.append("　no trades closed last month — open book holds "
                         "per rank; that is the system working")
        lines.append(
            f"<i>sweepable → BUY_BUDGET: ${sweep:,.2f}"
            + ("" if sweep else " (nothing above contributed capital)")
            + " · fills are modeled (Monday opens / trigger prices) — "
            "reconcile against IBKR statements, drift is honest noise</i>")
        return "\n".join(lines)
    except Exception:
        return ""
