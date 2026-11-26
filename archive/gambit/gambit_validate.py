#!/usr/bin/env python3
"""
GAMBIT validate — gates every commit and every CI job (homily #16 pattern:
red test = no send, no commit). CI runs ONLY this script; it must stay the
single entry point so nothing ships around it.

Order: [K6] safety gate first (prime directive — paper only), then the full
pytest suite (bars contract, granularity guard, session-date pin, ...).
Any failure exits nonzero.
"""
import json
import os
import re
import subprocess
import sys
from pathlib import Path

import gambit_freeze
import gambit_live

ROOT = Path(__file__).resolve().parent

# LIVE_ORDERS tri-state (DESIGNS D-G1): 'off' (default) / 'dry' (format + log
# MCP payloads, never send) / 'on' (P3+, forbidden while the PRD defers P3).
ALLOWED_FLAGS = ("off", "dry")
P3_DEFERRED_MARKER = "deferred sine die"   # PRD §3.4 — P3 parked by the owner


def check_k6(env=None, root=ROOT):
    """[K6] Safety gate (PRD §5.3). Returns a list of failure strings.

    Flipping live is a deliberate TWO-artifact action: env flag `on` AND a
    committed owner-signed LIVE_ENABLE.md — and even then only once the PRD
    no longer defers P3. This check fails the build if:
      a) LIVE_ORDERS has any value outside off/dry/on;
      b) LIVE_ORDERS=on without LIVE_ENABLE.md;
      c) LIVE_ENABLE.md exists while the PRD still says P3 is deferred
         (someone staged the file early — that alone is a breach);
      d) LIVE_ENABLE.md exists but lacks an owner line with a date.
    """
    env = os.environ if env is None else env
    root = Path(root)
    fails = []
    flag = env.get("LIVE_ORDERS", "off").strip().lower()
    enable = root / "LIVE_ENABLE.md"
    prd = root / "PRD.md"
    prd_defers_p3 = prd.exists() and P3_DEFERRED_MARKER in prd.read_text(
        encoding="utf-8")

    if flag not in ALLOWED_FLAGS + ("on",):
        fails.append(f"LIVE_ORDERS={flag!r} is not a legal state "
                     f"(off/dry/on)")
    if flag == "on" and not enable.exists():
        fails.append("LIVE_ORDERS=on without owner-signed LIVE_ENABLE.md")
    if flag == "on" and prd_defers_p3:
        fails.append("LIVE_ORDERS=on while PRD still defers P3")
    if enable.exists():
        if prd_defers_p3:
            fails.append("LIVE_ENABLE.md exists while PRD still defers P3 — "
                         "remove one or the other; live is a gate action")
        # owner line must carry a date (YYYY-MM-DD) — a blank file is not a
        # signature
        text = enable.read_text(encoding="utf-8")
        if not re.search(r"\d{4}-\d{2}-\d{2}", text):
            fails.append("LIVE_ENABLE.md has no dated owner line")
    return fails


def _step_named(text, step):
    """True if the A5 text names this dollar step in any usual form."""
    k = int(step / 1000)
    forms = (f"{int(step):,}", str(int(step)), f"{k}k", f"{k}K", f"US${k}k")
    return any(form in text for form in forms)


def check_scale(root=ROOT, book_path=None):
    """[SCALE] #98 / D-98 — the swing bankroll is EARNED, not topped up on a
    hot month. K6 pattern: policy breaches fail CI, loudly. The live book's
    `contributed` must sit exactly on the pre-registered ladder
    (3k → 6k → 12k), and every step ABOVE the base must be authorized by a
    dated owner line in AMENDMENT_A5.md naming that step (the two-artifact
    record the owner appends only after `gambit_live.py --scale-check`
    passes). Steps DOWN are free; nothing above 12k is adoptable without a
    new amendment. A book at the base (or no book yet) is silently fine."""
    root = Path(root)
    book_path = Path(book_path or root / "gambit_live_book.json")
    fails = []
    try:
        contrib = float(json.loads(book_path.read_text()).get("contributed"))
    except Exception:
        return fails                       # no book / unreadable → nothing to guard
    if contrib <= 0:
        return fails
    if contrib not in gambit_live.SCALE_STEPS:
        fails.append(f"contributed ${contrib:,.0f} is OFF the pre-registered "
                     f"ladder {tuple(int(s) for s in gambit_live.SCALE_STEPS)}"
                     " — a top-up must land exactly on a step (D-98)")
    a5 = root / "AMENDMENT_A5.md"
    text = a5.read_text(encoding="utf-8") if a5.exists() else ""
    dated = bool(re.search(r"\d{4}-\d{2}-\d{2}", text))
    for step in gambit_live.SCALE_STEPS[1:]:
        if contrib >= step and not (dated and _step_named(text, step)):
            fails.append(f"contributed reached ${step:,.0f} without a dated "
                         "AMENDMENT_A5 owner line naming the step (#98 "
                         "two-artifact — run --scale-check, then sign)")
    return fails


def main():
    print("GAMBIT validate — paper only; validate gates the send")
    fails = check_k6()
    if fails:
        for f in fails:
            print(f"[K6] FAIL: {f}")
        sys.exit(1)
    print("[K6] LIVE_ORDERS safety gate .......................... PASS")

    freeze_fails = gambit_freeze.check()
    if freeze_fails:
        for f in freeze_fails:
            print(f"[FREEZE] FAIL: {f}")
        sys.exit(1)
    print("[FREEZE] engine manifest (signal code frozen) ......... PASS")

    scale_fails = check_scale()
    if scale_fails:
        for f in scale_fails:
            print(f"[SCALE] FAIL: {f}")
        sys.exit(1)
    print("[SCALE] swing bankroll on the earned ladder (#98) ..... PASS")

    rc = subprocess.call([sys.executable, "-m", "pytest", "-q", str(ROOT)])
    if rc != 0:
        print("pytest suite FAILED — nothing ships")
        sys.exit(rc)
    print("gambit_validate: ALL GREEN")


if __name__ == "__main__":
    main()
