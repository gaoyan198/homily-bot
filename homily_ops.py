#!/usr/bin/env python3
"""
Ops-readiness block (#99 / D-99) — the owner's own queue, kept visible.
======================================================================

§9.0's north star includes closing the behaviour gap (#58): an unexecuted
setup step has zero alpha the same way an unexecuted signal does. The
integration era armed leverage and a live sleeve, but several switches only
the OWNER can flip are still off — and nothing in the digest reminds them.
This is a standing ⏳ line that lists exactly what is unset, plus the
margin-paydown progress toward the swing sleeve's arming condition.

Pure R0, info-only, no fetch: it reads repo variables (env) the owner
controls. When everything is set the line disappears — a clean board is
silence, not a green checkmark every day.

The blockers, each a real owner action:
  * MARGIN_ZERO — the clean-slate flag; the swing sleeve (A5) will not print
    its first order sheet until this is set (after the legacy loan clears).
  * MARGIN_BALANCE — a manual figure (S$) the owner updates as they pay the
    loan down, so the digest can show "S$X to clean slate" until #32's Flex
    sync automates it. Optional; absent = just the MARGIN_ZERO reminder.
  * IBKR_FLEX_TOKEN / IBKR_FLEX_QUERY — the Flex secrets (#32); until set,
    holdings sync + the #100 cost reconcile stay on their manual fallback.
  * BUY_BUDGET_USD — 0 during the paydown; the copilot stays dark until the
    owner restores it (PLAYBOOK §7).
"""


def _flag(env, name):
    return str(env.get(name, "")).strip().lower() in ("1", "true", "yes", "on")


def blockers(env):
    """-> list of (icon, text) for every owner switch still unset. Empty when
    the board is clean. Pure function of the environment mapping."""
    out = []
    if not _flag(env, "MARGIN_ZERO"):
        bal = str(env.get("MARGIN_BALANCE", "")).strip()
        if bal:
            out.append(("💳", f"margin paydown: S${bal} to clean slate — set "
                        "MARGIN_ZERO when it hits 0 (arms the swing sleeve, A5)"))
        else:
            out.append(("💳", "MARGIN_ZERO not set — clear the legacy loan, "
                        "then set it (arms the swing sleeve, A5)"))
    if not (env.get("IBKR_FLEX_TOKEN") and env.get("IBKR_FLEX_QUERY")):
        out.append(("🔌", "IBKR Flex secrets unset — holdings sync (#32) + "
                    "cost reconcile (#100) stay on manual fallback"))
    try:
        budget = float(env.get("BUY_BUDGET_USD", "") or 0)
    except ValueError:
        budget = 0.0
    if budget <= 0:
        out.append(("🛒", "BUY_BUDGET_USD is 0 — the buy-day copilot stays "
                    "dark; restore it after the paydown (PLAYBOOK §7)"))
    return out


def ops_line(env, esc=lambda x: x):
    """-> the standing ⏳ digest line, or "" when nothing is pending. One
    compact line (a new digest feature must not bloat the wall-of-text —
    PRD #73), items joined with · so it stays a single row."""
    items = blockers(env)
    if not items:
        return ""
    body = " · ".join(f"{icon} {esc(text)}" for icon, text in items)
    return f"⏳ <b>SETUP</b> ({len(items)} owner to-do): {body}"
