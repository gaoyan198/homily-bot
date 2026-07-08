#!/usr/bin/env python3
"""
State-change alerts (backlog #15) — the signal that stops drowning in the wall.
==============================================================================

The daily digest is the full picture; this is the *interrupt*. After the ledger
is built we diff today's per-name states against yesterday's committed ledger
row and fire a SECOND, tiny Telegram message ONLY on genuine transitions:

    ⭐ a name enters / lapses out of ACCUMULATE
    🔵 a BOTTOMING signal fires
    🐳 a whale-accumulation footprint appears
    🚀 a name passes / stops passing the 5 multi-bagger gates
    🐂/🐻 the market regime flips

A quiet day sends nothing. Pure ledger diff (#13 is the data source): it reads
the committed CSV + snapshot from BEFORE today's record() overwrites them, so it
must be called before homily_ledger.record(). No engine files are touched.

First-ever run (no prior ledger date) sends nothing — there is nothing to diff,
and diffing against emptiness would fire an alert for every screened name.
"""
import os
import json
import html

import homily_ledger

REGIME_ICON = {"BULL": "🐂", "BEAR": "🐻", "MIXED": "⚖️"}


def _e(x):
    """Escape a ticker/label for the Telegram HTML message (#34)."""
    return html.escape(str(x), quote=False)


def _truthy(v):
    """CSV cells are strings ('1'/'0'); today's state dicts carry real bools."""
    return v is True or v == "1"


def diff_alerts(today_states, today_regime, prev_rows, prev_regime):
    """Pure transition detector. `today_states` = homily_ledger.state_of dicts;
    `prev_rows` = committed CSV rows for the single prior date; `prev_regime` =
    yesterday's regime label or None. Returns a list of alert lines (possibly
    empty). A name with no prior row is skipped — new listings don't alert."""
    prev = {r["ticker"]: r for r in prev_rows}
    lines = []

    if prev_regime and today_regime is not None and \
            prev_regime != today_regime.label:
        icon = REGIME_ICON.get(today_regime.label, "")
        lines.append(f"{icon} REGIME flip: {_e(prev_regime)} → "
                     f"{_e(today_regime.label)}")

    for st in today_states:
        p = prev.get(st["ticker"])
        if p is None:
            continue                       # new to the ledger: nothing to diff
        tk, cur, was = _e(st["ticker"]), st["state"], p["state"]

        if cur == "ACCUMULATE" and was != "ACCUMULATE":
            lines.append(f"⭐ {tk} entered ACCUMULATE (was {was})")
        elif was == "ACCUMULATE" and cur != "ACCUMULATE":
            lines.append(f"⭐ {tk} left ACCUMULATE (now {cur})")

        if cur == "BOTTOMING" and was != "BOTTOMING":
            lines.append(f"🔵 {tk} BOTTOMING signal fired (was {was})")

        if _truthy(st["whale"]) and not _truthy(p["whale"]):
            lines.append(f"🐳 {tk} whale-accumulation footprint appeared")

        if _truthy(st["gates_ok"]) and not _truthy(p["gates_ok"]):
            lines.append(f"🚀 {tk} passed all 5 multi-bagger gates")
        elif not _truthy(st["gates_ok"]) and _truthy(p["gates_ok"]):
            lines.append(f"🚀 {tk} no longer passes the gates")

    return lines


def build_alerts(today_states, today_regime, day, *,
                 ledger=homily_ledger.LEDGER, snapshot=homily_ledger.SNAPSHOT):
    """Read the committed prior-day state and diff today against it. MUST run
    before homily_ledger.record() overwrites the ledger/snapshot."""
    rows = homily_ledger._read_rows(ledger)
    prior = sorted({r["date"] for r in rows if r["date"] < day.isoformat()})
    if not prior:
        return []                          # first-ever run: nothing to diff
    prev_date = prior[-1]
    prev_rows = [r for r in rows if r["date"] == prev_date]

    prev_regime = None
    if os.path.exists(snapshot):
        snap = json.load(open(snapshot))
        # only trust the snapshot's regime if it is actually yesterday's
        if snap.get("date") == prev_date and snap.get("regime"):
            prev_regime = snap["regime"]["label"]

    return diff_alerts(today_states, today_regime, prev_rows, prev_regime)


def format_alerts(lines, day):
    """Wrap the transition lines into the tiny second message, or '' for none."""
    if not lines:
        return ""
    head = f"🔔 <b>Homily alerts — {_e(day)}</b> (state changes only)"
    return "\n".join([head, ""] + lines)
