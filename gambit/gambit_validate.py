#!/usr/bin/env python3
"""
GAMBIT validate — gates every commit and every CI job (homily #16 pattern:
red test = no send, no commit). CI runs ONLY this script; it must stay the
single entry point so nothing ships around it.

Order: [K6] safety gate first (prime directive — paper only), then the full
pytest suite (bars contract, granularity guard, session-date pin, ...).
Any failure exits nonzero.
"""
import os
import re
import subprocess
import sys
from pathlib import Path

import gambit_freeze

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

    rc = subprocess.call([sys.executable, "-m", "pytest", "-q", str(ROOT)])
    if rc != 0:
        print("pytest suite FAILED — nothing ships")
        sys.exit(rc)
    print("gambit_validate: ALL GREEN")


if __name__ == "__main__":
    main()
