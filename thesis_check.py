#!/usr/bin/env python3
"""
Monthly thesis check — the contract between the checker agent and the bot.
=========================================================================

A cloud routine (Sonnet, the 1st of each month) researches each satellite
stock and writes `thesis_scores.json`: for every thesis line a status
(holding / mixed / weakening) with evidence and a source URL, and for every
"would break if" line whether it has been met. The agent JUDGES LINES; this
file COMPUTES THE SCORE, so the number can't be talked up:

    score = 10 × Σ points / (2 × lines)   holding = 2 · mixed = 1 · weakening = 0

Any break condition met → 🚨 in the daily message ("review — your own sell
rule says so"). A check older than 45 days prints as stale.

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
                                 ("breaks", "breaks_if", "triggered")):
            rows = s.get(kind) or []
            lines = [r.get("line") for r in rows]
            if sorted(lines) != sorted(t[key]):
                probs.append(f"{tk}.{kind}: lines must match crash_plan.json "
                             "exactly, once each")
            for r in rows:
                v = r.get(field)
                if field == "status" and v not in POINTS:
                    probs.append(f"{tk}: status {v!r} not in {sorted(POINTS)}")
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


def score(stock):
    """-> (0..10 int, n_weakening, [met break lines]) for one stock entry."""
    rows = stock.get("thesis") or []
    pts = sum(POINTS.get(r.get("status"), 0) for r in rows)
    sc = round(10 * pts / (2 * len(rows))) if rows else 0
    weak = sum(r.get("status") == "weakening" for r in rows)
    met = [r["line"] for r in stock.get("breaks") or [] if r.get("triggered")]
    return sc, weak, met


def line_for(tk, scores, today, esc=lambda x: html.escape(str(x), quote=False)):
    """-> the one daily-message line for `tk`, or None if never checked."""
    if not scores or tk not in (scores.get("stocks") or {}):
        return None
    sc, weak, met = score(scores["stocks"][tk])
    checked = datetime.date.fromisoformat(scores["checked"])
    age = (today - checked).days
    when = f"checked {checked:%d %b}" + (" — STALE, the monthly check didn't run"
                                         if age > STALE_DAYS else "")
    if met:
        return (f"  🚨 <b>BREAK CONDITION MET</b> — {esc(' · '.join(met))} — "
                f"review: your own sell rule says so ({esc(when)})")
    return (f"  🧪 thesis {sc}/10 ({esc(when)})"
            + (f" · {weak} point{'s' * (weak != 1)} weakening" if weak else "")
            + " · no break condition met")


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
            print(tk, score(s))
        print("thesis_scores.json OK")
    else:
        print(__doc__)
