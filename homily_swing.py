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

SNAPSHOT = Path(__file__).resolve().parent / "gambit" / "snapshot.json"
P2_WEEKS = 26          # gambit PRD §5.2 — calendar weeks of paper ledger
P2_TRADES = 20         # gambit PRD §5.2 — closed trades


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
        "LIVE_ORDERS=off — no real orders; live money + leverage arrive only "
        "via #93's gate (paper ledger green + owner sign-off)</i>",
    ])
