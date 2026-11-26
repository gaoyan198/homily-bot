#!/usr/bin/env python3
"""
Complexity budget (#116, ROADMAP §5) — the July prune, made mechanical.

Nulls are supposed to be closed, not accreted, and by 2026-09 the top
level held 89 modules of which 44 are reachable from no entry point. The
rule the ROADMAP row states — every module holds ONE of {live consumer ·
dated pending read · archive} — is enforced here, with the count capped:

  live     derived, never declared: reachable by import from an entry
           point (daily_run · homily_vault · homily_weekly · homily_chart
           · the gambit runners)
  tool     validate-consumed machinery with no market claim of its own
           (the validate harness itself, the bootstrap, the verdict pin …)
  gate     the harness of record for a rule or promotion that is LIVE —
           kept top-level because #40 re-runs it every July; its record
           section is named so the re-run has a number to reproduce
  pending  a study with a DATED read still ahead of it (`read`); a read
           more than 90 days past without reclassification fails validate
  null     closed honestly; stays top-level ONLY until `archive_by` (the
           next July prune), after which validate fails until it moves to
           docs/archive/ with its BACKTEST_RESULTS pointer

`module_budget.json` is the registry + the cap. The cap is the top-level
count on the day it was set; the count may not exceed it, and raising it
is an edit to `cap`/`cap_set` PLUS a PRD §8.5 note dated the same day
naming #116 — validate [85] checks both, the #117 idiom. `python
homily_budget.py` prints the census the July session works from.
"""
import os, re, ast, sys, json, glob, datetime

HERE = os.path.dirname(os.path.abspath(__file__))
REGISTRY = os.path.join(HERE, "module_budget.json")
ROOTS = ("daily_run", "homily_vault", "homily_weekly", "homily_chart")
STATUSES = ("tool", "gate", "pending", "null")
PENDING_GRACE_DAYS = 90


def modules():
    return sorted(os.path.basename(f)[:-3]
                  for f in glob.glob(os.path.join(HERE, "*.py")))


def _imports(path, universe):
    deps = set()
    for n in ast.walk(ast.parse(open(path, encoding="utf-8").read())):
        if isinstance(n, ast.Import):
            deps |= {a.name.split(".")[0] for a in n.names}
        elif isinstance(n, ast.ImportFrom) and n.module:
            deps.add(n.module.split(".")[0])
    return deps & universe


def live_set():
    """Modules reachable from an entry point, incl. what gambit/ imports."""
    mods = set(modules())
    graph = {m: _imports(os.path.join(HERE, m + ".py"), mods) for m in mods}
    roots = set(ROOTS)
    for f in glob.glob(os.path.join(HERE, "gambit", "*.py")):
        roots |= _imports(f, mods)
    live, stack = set(), list(roots)
    while stack:
        m = stack.pop()
        if m in live or m not in mods:
            continue
        live.add(m)
        stack.extend(graph[m])
    return live


def load():
    with open(REGISTRY) as f:
        return json.load(f)


def census(today=None, reg=None):
    """-> (rows, problems). rows: (module, status, of, record, when)."""
    today = today or datetime.date.today()
    reg = reg or load()
    live = live_set()
    rows, problems = [], []
    for m in modules():
        e = reg["registry"].get(m)
        if m in live:
            rows.append((m, "live", (e or {}).get("of", ""), (e or {}).get("record", ""), ""))
            continue
        if not e:
            problems.append(f"{m}: not live and not in the registry — classify it")
            rows.append((m, "UNCLASSIFIED", "", "", ""))
            continue
        st = e.get("status")
        if st not in STATUSES:
            problems.append(f"{m}: status {st!r} not in {STATUSES}")
        when = ""
        if st == "pending":
            when = e.get("read", "")
            try:
                d = datetime.date.fromisoformat(when)
                if (today - d).days > PENDING_GRACE_DAYS:
                    problems.append(f"{m}: pending read {when} is "
                                    f"{(today - d).days}d past — reclassify")
            except ValueError:
                problems.append(f"{m}: pending needs an ISO `read` date")
        elif st == "null":
            when = e.get("archive_by", "")
            try:
                if today > datetime.date.fromisoformat(when):
                    problems.append(f"{m}: closed null past archive_by {when} — "
                                    "move to docs/archive/ with its record pointer")
            except ValueError:
                problems.append(f"{m}: null needs an ISO `archive_by` date")
            if not e.get("record"):
                problems.append(f"{m}: a null must name its BACKTEST_RESULTS section")
        elif st == "gate" and not e.get("record"):
            problems.append(f"{m}: a gate must name its record section")
        rows.append((m, st, e.get("of", ""), e.get("record", ""), when))
    n = len(rows)
    if n > reg["cap"]:
        problems.append(f"top-level module count {n} exceeds the cap {reg['cap']} "
                        f"set {reg['cap_set']} — prune, or raise the cap with a "
                        "same-day PRD §8.5 note naming #116")
    return rows, problems


def prd_note_dated(day, prd=None):
    text = open(prd or os.path.join(HERE, "PRD.md"), encoding="utf-8").read()
    sec = text[text.index("### 8.5 Execution notes"):]
    return any(day in ln and "#116" in ln
               for ln in sec.split("\n\n") if ln.startswith(f"**{day}"))


if __name__ == "__main__":
    rows, problems = census()
    reg = load()
    by = {}
    for r in rows:
        by.setdefault(r[1], []).append(r)
    print(f"top-level modules: {len(rows)} (cap {reg['cap']}, set {reg['cap_set']})")
    for st in ("live", "tool", "gate", "pending", "null", "UNCLASSIFIED"):
        if st in by:
            print(f"\n{st} ({len(by[st])}):")
            for m, _, of, rec, when in by[st]:
                print(f"  {m:34s} {of:8s} {rec:28s} {when}")
    if problems:
        print("\nPROBLEMS:")
        for p in problems:
            print("  " + p)
    sys.exit(1 if problems else 0)
