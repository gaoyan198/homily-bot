#!/usr/bin/env python3
"""
Sunday deep-dive (backlog #33) — the weekly edition, fetch-free.
================================================================

Sunday's run (new cron, 10:00 SGT) sends ONE summary message + the #36
dashboard file, built entirely from committed artifacts — the week's
ledger rows and Friday's snapshot. No market fetch, no engine call, no
ledger write on a non-trading day (R3: rows are weekday-only; #70's
coverage math already expects that).

Per held name: the week's state timeline (Mon→Fri icons), conviction
drift (first→last conv_score), distance to the add zone, and the week's
🐳/VH events. Plus coverage and the reconstructed alert count. #14's
scorecard refresh joins this message once the ledger is 3 months old.

Replaces "more text" with the dashboard link/file — the summary is the
teaser, the dashboard is the deep dive. Engines frozen (§0).
"""
import datetime
import html

ICON = {"ACCUMULATE": "⭐", "HOLD": "🟢", "PULLBACK": "🟡",
        "BOTTOMING": "🔵", "CAUTION": "⚪"}
E = lambda x: html.escape(str(x), quote=False)


def week_rows(rows, week_end):
    """Rows from the calendar week ending at `week_end` (a Sunday):
    Monday..Friday of that week, whatever subset actually ran."""
    mon = week_end - datetime.timedelta(days=week_end.weekday())
    lo, hi = mon.isoformat(), week_end.isoformat()
    return [r for r in rows if lo <= r["date"] <= hi]


def weekly_summary(rows, snap, week_end):
    """Pure: this week's ledger rows + the latest snapshot -> the Sunday
    message ('' when the week has no rows — a full-holiday week)."""
    wk = week_rows(rows, week_end)
    if not wk:
        return ""
    dates = sorted({r["date"] for r in wk})
    held = [s["ticker"] for s in snap.get("holdings", []) if s.get("held")]
    zone = {s["ticker"]: s for s in snap.get("holdings", [])}
    by = {}
    for r in wk:
        by.setdefault(r["ticker"], {})[r["date"]] = r

    lines = [f"📒 <b>WEEK IN REVIEW — w/e {E(week_end.isoformat())}</b> "
             f"({len(dates)} trading days logged)"]
    events = []
    for tk in held:
        drows = by.get(tk, {})
        if not drows:
            continue
        seq = "".join(ICON.get(drows[d]["state"], "·") if d in drows else "·"
                      for d in dates)
        first, last = drows[min(drows)], drows[max(drows)]
        drift = ""
        try:
            d0, d1 = int(first["conv_score"]), int(last["conv_score"])
            if d1 != d0:
                drift = f" · conv {d0}→{d1}"
        except (KeyError, ValueError):
            pass
        dist = ""
        s = zone.get(tk) or {}
        if s.get("zone_hi") is not None and s.get("close"):
            gap = 100.0 * (float(s["close"]) / float(s["zone_hi"]) - 1)
            dist = (" · at add zone" if gap <= 0
                    else f" · {gap:.0f}% above add zone")
        lines.append(f"<code>{E(f'{tk:<5}')}</code> {seq}{drift}{dist}")
        for d in sorted(drows):
            if drows[d].get("whale") == "1":
                events.append(f"{d} 🐳 {tk}")
                break
        for d in sorted(drows):
            vh = drows[d].get("vh_status")
            if vh in ("BREAKOUT", "BREAKDOWN"):
                events.append(f"{d} VH{'↑' if vh == 'BREAKOUT' else '↓'} {tk}")
                break
    if events:
        lines += ["", "events: " + " · ".join(E(e) for e in sorted(set(events)))]
    cov = snap.get("coverage") or {}
    if cov:
        lines += ["", f"<i>ledger coverage {E(cov.get('pct', '—'))}% · full "
                  "detail in the dashboard file below (offline, zero JS) · "
                  "scorecard joins at the 3-month mark (#14)</i>"]
    return "\n".join(lines)
