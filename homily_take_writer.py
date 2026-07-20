#!/usr/bin/env python3
"""
#112 Danny-voice takes — the sidecar writer.
============================================

Narrates the board's OWN numbers in Danny's documented voice for the
index legs (QQQ, CSPX) + every holdings.json position. Runs OUTSIDE the
nightly pipeline (a scheduled Claude agent or a CI step invokes it —
never daily_run.py): the deterministic board must ship whether or not
this ever runs. Output is docs/danny_take.json; homily_dashboard renders
it fail-open and only when board_date matches the snapshot.

The LLM narrates, it never computes: the grounding post-check drops any
take containing a numeral that does not appear in that ticker's snapshot
fields (method constants 3/7/10/30 excepted — the quoted 3–7-day
pullback and the 10-period/MA30 lines). PRD §2 honesty constraints
carry over: no targets, no return predictions, no sell calls.

The Claude call is a `claude -p` subprocess — auth is whatever the
ambient CLI has (subscription login locally, CLAUDE_CODE_OAUTH_TOKEN or
an API key in CI). stdlib only; no anthropic package.

    python3 homily_take_writer.py            # write docs/danny_take.json
    python3 homily_take_writer.py --dry-run  # print the prompt, no call
    python3 homily_take_writer.py --verify   # re-check the committed file
"""
import json
import os
import re
import subprocess
import sys
from datetime import datetime, timezone

HERE = os.path.dirname(os.path.abspath(__file__))
SNAPSHOT = os.path.join(HERE, "docs", "snapshot.json")
TAKES = os.path.join(HERE, "docs", "danny_take.json")
VOICE = os.path.join(HERE, "danny_voice.md")

INDEX_LEGS = {"QQQ", "CSPX"}
# Numbers the voice card licenses without a snapshot source: the quoted
# "3 to 7 trading days", the 10-period lines, the MA30.
METHOD_CONSTANTS = {3.0, 7.0, 10.0, 30.0}
MAX_CHARS = 600


def take_tickers():
    import homily_positions
    return INDEX_LEGS | set(homily_positions.load_positions())


def select_rows(snap):
    want = take_tickers()
    rows = snap.get("holdings", []) + snap.get("discovery", [])
    return [r for r in rows if r["ticker"] in want]


def _numbers(obj, out):
    if isinstance(obj, bool):
        return
    if isinstance(obj, (int, float)):
        # prose states magnitudes ("RS6 down 5.19" for -5.19) — ground
        # the absolute value too
        out.add(float(obj))
        out.add(abs(float(obj)))
    elif isinstance(obj, dict):
        for v in obj.values():
            _numbers(v, out)
    elif isinstance(obj, (list, tuple)):
        for v in obj:
            _numbers(v, out)


def ground_check(text, row):
    """Every numeral in `text` must match a value in `row` (to the
    precision the text states) or a method constant. Returns the list
    of offending tokens — empty means grounded."""
    vals = set()
    _numbers(row, vals)
    bad = []
    for tok in re.findall(r"\d+(?:\.\d+)?", text.replace(",", "")):
        v = float(tok)
        decimals = len(tok.split(".")[1]) if "." in tok else 0
        tol = 10 ** -decimals          # "660" tolerates ±1, "660.6" ±0.1
        if v in METHOD_CONSTANTS:
            continue
        if any(abs(v - n) <= tol for n in vals):
            continue
        bad.append(tok)
    return bad


def build_prompt(rows, voice):
    facts = {r["ticker"]: r for r in rows}
    return (voice
            + "\n\n## Task\n\n"
            "For EACH ticker below, write one Danny-voice take from its "
            "JSON fields only. Use plain decimals (no thousands "
            "separators). Reply with ONE strict JSON object mapping "
            "ticker -> take string, nothing else — no markdown fences, "
            "no commentary.\n\n"
            + json.dumps(facts, indent=1, sort_keys=True))


def call_claude(prompt):
    cmd = ["claude", "-p", prompt]
    model = os.environ.get("HOMILY_TAKE_MODEL")
    if model:
        cmd += ["--model", model]
    out = subprocess.run(cmd, capture_output=True, text=True,
                         timeout=900).stdout
    start, end = out.find("{"), out.rfind("}")
    if start < 0 or end <= start:
        raise ValueError(f"no JSON object in claude output: {out[:200]!r}")
    return json.loads(out[start:end + 1])


def verify(path=TAKES, snapshot=SNAPSHOT):
    """Re-check a committed take file: date freshness + grounding.
    Returns a list of problem strings — empty means clean."""
    problems = []
    try:
        data = json.load(open(path))
        snap = json.load(open(snapshot))
    except Exception as e:
        return [f"unreadable: {e}"]
    if data.get("board_date") != snap.get("date"):
        problems.append(f'stale: board_date {data.get("board_date")} != '
                        f'snapshot {snap.get("date")}')
    rows = {r["ticker"]: r for r in select_rows(snap)}
    for tk, text in (data.get("takes") or {}).items():
        if tk not in rows:
            problems.append(f"{tk}: not a take ticker")
            continue
        bad = ground_check(text, rows[tk])
        if bad:
            problems.append(f"{tk}: ungrounded numbers {bad}")
        if len(text) > MAX_CHARS:
            problems.append(f"{tk}: {len(text)} chars > {MAX_CHARS}")
    return problems


def main(argv):
    snap = json.load(open(SNAPSHOT))
    rows = select_rows(snap)
    if "--verify" in argv:
        problems = verify()
        for p in problems:
            print("FAIL", p)
        return 1 if problems else 0
    prompt = build_prompt(rows, open(VOICE).read())
    if "--dry-run" in argv:
        print(prompt)
        return 0
    raw = call_claude(prompt)
    takes, dropped = {}, []
    for r in rows:
        tk = r["ticker"]
        text = (raw.get(tk) or "").strip()
        if not text:
            dropped.append((tk, "no take returned"))
            continue
        bad = ground_check(text, r)
        if bad:
            dropped.append((tk, f"ungrounded numbers {bad}"))
        elif len(text) > MAX_CHARS:
            dropped.append((tk, f"{len(text)} chars > {MAX_CHARS}"))
        else:
            takes[tk] = text
    doc = {"_v": 1, "board_date": snap["date"],
           "generated_utc": datetime.now(timezone.utc).isoformat(),
           "takes": takes}
    with open(TAKES, "w") as f:
        json.dump(doc, f, indent=1, sort_keys=True)
        f.write("\n")
    print(f"wrote {TAKES} — {len(takes)} takes"
          + (f", dropped {len(dropped)}: {dropped}" if dropped else ""))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
