#!/usr/bin/env python3
"""
GAMBIT engine freeze (EXECUTION §0.6 / homily #61). Once the paper ledger
starts accruing rows (G-S5), the signal engine is frozen: the modules that
compute universe, indicators, regime, and fills may not change silently. A
SHA-256 manifest pins their bytes; validate fails the build on any drift.

Changing a frozen module is a deliberate, gated action — max one promoted
behaviour change per quarter (R10) — and regenerating the manifest is explicit:
`python gambit_freeze.py --update`, eyeballed, committed with the reason.
Non-engine files (the P2 loop: weekly_run, gambit_paper, gambit_journal,
gambit_digest) are NOT frozen here — they freeze after their own first row.
"""
import hashlib
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
MANIFEST = ROOT / "engine_manifest.json"

# The frozen signal engine — the code that produced BACKTEST_RESULTS.md.
FROZEN = ("gambit_data.py", "gambit_universe.py", "gambit_vol.py",
          "gambit_backtest.py", "gambit_arms.py")


def _sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def compute(root=ROOT):
    return {f: _sha(Path(root) / f) for f in FROZEN}


def check(root=ROOT, manifest=MANIFEST):
    """-> list of failure strings. Empty manifest (not yet armed) => no fails."""
    manifest = Path(manifest)
    if not manifest.exists():
        return []
    pinned = json.loads(manifest.read_text())
    now = compute(root)
    fails = []
    for f in FROZEN:
        if f not in pinned:
            continue
        if now.get(f) != pinned[f]:
            fails.append(f"frozen engine file changed without a manifest bump: "
                         f"{f} (gated change + `gambit_freeze.py --update`)")
    return fails


def update(root=ROOT, manifest=MANIFEST):
    Path(manifest).write_text(json.dumps(compute(root), indent=2, sort_keys=True))
    print(f"engine_manifest.json updated over {len(FROZEN)} frozen files")


if __name__ == "__main__":
    if "--update" in sys.argv:
        update()
    else:
        fails = check()
        for f in fails:
            print("[FREEZE] FAIL:", f)
        sys.exit(1 if fails else 0)
