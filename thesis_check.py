#!/usr/bin/env python3
"""
Monthly thesis check — the contract between the checker agent and the bot.
=========================================================================

A cloud routine (Sonnet, monthly) researches each satellite stock and
writes `thesis_scores.json`, judging EVERY line the owner wrote:
  thesis    holding / mixed / weakening            (bull case)
  bear_case not_happening / partly / happening     (bear case)
  breaks_if triggered true / false                 (the owner's sell rule)
each with evidence and a source URL. The agent JUDGES LINES; this file
COMPUTES the scores and the verdict, so neither can drift with the agent:

  bull = 10 × Σ / (2 × lines)   holding 2 · mixed 1 · weakening 0
  bear = 10 × Σ / (2 × lines)   happening 2 · partly 1 · not_happening 0
  🚨 SELL                 any break condition met (the owner's own rule)
  🔴 CONSIDER SELLING     bull ≤ 3 or bear ≥ 7 (thesis mostly broken)
  🟢 HOLD                 bull ≥ 6 and bear ≤ 4
  🟡 HOLD, WATCH CLOSELY  anything in between
The agent's one-sentence `summary` is printed as the "why". A check older
than 45 days prints as stale. Information, not advice: the owner decides.

    python3 thesis_check.py --prompt   the exact lines to check (JSON) for the agent
    python3 thesis_check.py --verify   schema check; exit 1 on any problem

The agent never edits crash_plan.json, never gives buy/sell advice, and
keys every judgment to the EXACT line text — a rewritten or missing line
fails --verify. Stdlib only.
"""
import datetime
import html
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
PLAN_FILE = os.path.join(HERE, "crash_plan.json")
SCORES_FILE = os.path.join(HERE, "thesis_scores.json")
POINTS = {"holding": 2, "mixed": 1, "weakening": 0}
BEAR_POINTS = {"happening": 2, "partly": 1, "not_happening": 0}
STALE_DAYS = 45


def _load(path):
    with open(path) as f:
        return json.load(f)


def task(plan):
    """-> what the agent must judge: {ticker: {name, thesis[], breaks_if[],
    bear_case[]}} straight from crash_plan.json."""
    return {tk: {"name": c.get("name", tk), "thesis": c.get("thesis", []),
                 "breaks_if": c.get("breaks_if", []),
                 "bear_case": c.get("bear_case", [])}
            for tk, c in (plan.get("satellite") or {}).items()}


def verify(scores, plan):
    """-> list of problems (empty = valid). Every planned line must be judged
    exactly once, by its exact text, with evidence and an http(s) source."""
    probs = []
    try:
        datetime.date.fromisoformat(scores.get("checked", ""))
    except ValueError:
        probs.append("checked: not an ISO date")
    want = task(plan)
    got = scores.get("stocks") or {}
    for tk, t in want.items():
        s = got.get(tk)
        if not s:
            probs.append(f"{tk}: missing")
            continue
        for kind, key, field in (("thesis", "thesis", "status"),
                                 ("bear", "bear_case", "bear_status"),
                                 ("breaks", "breaks_if", "triggered")):
            rows = s.get(kind) or []
            lines = [r.get("line") for r in rows]
            if sorted(lines) != sorted(t[key]):
                probs.append(f"{tk}.{kind}: lines must match crash_plan.json "
                             "exactly, once each")
            for r in rows:
                v = r.get("status" if field == "bear_status" else field)
                if field == "status" and v not in POINTS:
                    probs.append(f"{tk}: status {v!r} not in {sorted(POINTS)}")
                if field == "bear_status" and v not in BEAR_POINTS:
                    probs.append(f"{tk}: bear status {v!r} not in "
                                 f"{sorted(BEAR_POINTS)}")
                if field == "triggered" and not isinstance(v, bool):
                    probs.append(f"{tk}: triggered must be true/false")
                if not (r.get("evidence") or "").strip():
                    probs.append(f"{tk}: a line has no evidence")
                if not str(r.get("source", "")).startswith(("http://", "https://")):
                    probs.append(f"{tk}: a line has no source URL")
        if not (s.get("summary") or "").strip():
            probs.append(f"{tk}: no summary")
    for tk in got:
        if tk not in want:
            probs.append(f"{tk}: not a satellite in crash_plan.json")
    return probs


def _ten(rows, pts):
    return round(10 * sum(pts.get(r.get("status"), 0) for r in rows)
                 / (2 * len(rows))) if rows else None


def score(stock):
    """-> dict(bull 0..10, bear 0..10|None, weak n, met [lines], verdict)."""
    bull = _ten(stock.get("thesis") or [], POINTS) or 0
    bear = _ten(stock.get("bear") or [], BEAR_POINTS)
    weak = sum(r.get("status") == "weakening" for r in stock.get("thesis") or [])
    met = [r["line"] for r in stock.get("breaks") or [] if r.get("triggered")]
    b = bear if bear is not None else 0
    if met:
        verdict = "🚨 SELL — your own sell rule fired"
    elif bull <= 3 or b >= 7:
        verdict = "🔴 CONSIDER SELLING — thesis mostly broken"
    elif bull >= 6 and b <= 4:
        verdict = "🟢 HOLD"
    else:
        verdict = "🟡 HOLD, WATCH CLOSELY"
    return {"bull": bull, "bear": bear, "weak": weak, "met": met,
            "verdict": verdict}


def line_for(tk, scores, today, esc=lambda x: html.escape(str(x), quote=False)):
    """-> the daily-message lines for `tk` (one string, may hold a newline),
    or None if never checked."""
    if not scores or tk not in (scores.get("stocks") or {}):
        return None
    st = scores["stocks"][tk]
    r = score(st)
    checked = datetime.date.fromisoformat(scores["checked"])
    when = f"checked {checked:%d %b}" + (
        " — STALE, the monthly check didn't run"
        if (today - checked).days > STALE_DAYS else "")
    bear = f" · bear {r['bear']}/10" if r["bear"] is not None else ""
    head = (f"  <b>{esc(r['verdict'])}</b> — bull {r['bull']}/10{bear} ("
            f"{esc(when)})")
    if r["met"]:
        head += f"\n  🚨 sell condition met: {esc(' · '.join(r['met']))}"
    if st.get("summary"):
        head += f"\n  <i>why: {esc(st['summary'])}</i>"
    return head


def load_scores(path=SCORES_FILE):
    try:
        return _load(path)
    except (OSError, ValueError):
        return None


if __name__ == "__main__":
    plan = _load(PLAN_FILE)
    if "--prompt" in sys.argv:
        print(json.dumps(task(plan), indent=1, ensure_ascii=False))
    elif "--verify" in sys.argv:
        sc = load_scores()
        probs = ["thesis_scores.json missing or not JSON"] if sc is None \
            else verify(sc, plan)
        for p in probs:
            print("FAIL", p)
        if probs:
            sys.exit(1)
        for tk, s in sc["stocks"].items():
            r = score(s)
            print(tk, f"bull {r['bull']}/10 · bear {r['bear']}/10 · {r['verdict']}")
        print("thesis_scores.json OK")
    else:
        print(__doc__)
