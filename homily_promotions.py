#!/usr/bin/env python3
"""
Promotion lifecycle registry + forward-checker (backlog #69).
=============================================================

The promotion machinery was prose scattered across PRD §5h/§5j/R10; this
makes it mechanical. `promotions.json` holds one entry per gate-passed
candidate (or pre-registered challenger): the rule verbatim, the gate
artifact, the earliest promotion date, frozen forward-check criteria, and
— the standing rule this file exists to enforce — a **demotion rule
written before promotion**. The 2026-10-01 rs12-top3 decision becomes
this program's output, not a fresh judgment call made with the result
already visible.

The forward check reads ONLY the #13 ledger (what the digest actually
printed): for each ⭐ row inside the frozen window carrying the entry's
rank column, the forward return is the same ticker's ledger close
`horizon_rows` ledger-dates later. Raw closes — the ledger doesn't carry
adjclose, and over a ≤3-month horizon the dividend drag on both groups is
near-identical; stated here so nobody mistakes it for total return.
Rows whose forward date hasn't happened yet simply aren't measured, so
the same command is runnable any day: it reports INSUFFICIENT until the
window has enough measured rows, then PASS/FAIL per the frozen criterion.

Engines frozen (§0): pure read of the ledger CSV and the registry.
"""
import os
import json
import datetime

import homily_ledger

HERE = os.path.dirname(os.path.abspath(__file__))
REGISTRY = os.path.join(HERE, "promotions.json")


def load_registry(path=REGISTRY):
    with open(path) as f:
        return json.load(f)["entries"]


def forward_check(entry, rows):
    """One entry's frozen forward check against ledger rows.
    -> {"id", "status": PASS|FAIL|INSUFFICIENT, "n_top", "n_other",
        "mean_top", "mean_other"} — means are simple averages of per-row
    forward returns (%), top = rank <= 3, other = rank > 3, ⭐ rows only."""
    fc = entry["forward_check"]
    col, hor = fc["rank_column"], fc["horizon_rows"]
    lo, hi = fc["window"]
    dates = sorted({r["date"] for r in rows})
    idx = {d: i for i, d in enumerate(dates)}
    close = {(r["date"], r["ticker"]): float(r["close"])
             for r in rows if r.get("close")}
    top, other = [], []
    for r in rows:
        if not (lo <= r["date"] <= hi and r.get("state") == "ACCUMULATE"
                and r.get(col)):
            continue
        i = idx[r["date"]] + hor
        if i >= len(dates):
            continue                       # forward date hasn't happened yet
        fwd = close.get((dates[i], r["ticker"]))
        px = close.get((r["date"], r["ticker"]))
        if fwd is None or px is None or px <= 0:
            continue
        ret = 100.0 * (fwd / px - 1)
        (top if int(r[col]) <= 3 else other).append(ret)
    need = fc["min_measured_rows"]
    out = {"id": entry["id"], "n_top": len(top), "n_other": len(other),
           "mean_top": (sum(top) / len(top) if top else None),
           "mean_other": (sum(other) / len(other) if other else None)}
    if len(top) < need or len(other) < need:
        out["status"] = "INSUFFICIENT"
    else:
        out["status"] = "PASS" if out["mean_top"] > out["mean_other"] else "FAIL"
    return out


def _windowed(entry, lo, hi):
    """Entry copy whose forward check runs over [lo, hi] instead of the
    frozen window — the rolling demotion read. The registry file itself is
    never touched (frozen criteria stay frozen)."""
    fc = dict(entry["forward_check"], window=[lo, hi])
    return dict(entry, forward_check=fc)


def _fmt_check(r):
    mt = f"{r['mean_top']:+.2f}%" if r["mean_top"] is not None else "—"
    mo = f"{r['mean_other']:+.2f}%" if r["mean_other"] is not None else "—"
    return (f"{r['status']} (top-3 n={r['n_top']} mean {mt} vs other "
            f"n={r['n_other']} mean {mo})")


def month_start_block(rows, day, esc=lambda x: x):
    """The month-start digest block (wired 2026-07-12 as a condition of the
    rs12-top3 early promotion). Two reads per entry, both mandatory-by-rule:

      1. the FROZEN pre-registered window — so the 2026-10-01 rs12-top3
         read is published on schedule whether or not the promotion already
         happened (the owner's explicit instruction: show the live-data
         test in October regardless);
      2. for promoted entries, the rolling-6-month demotion check — a FAIL
         is a mandatory demotion per the entry's demotion_rule, and the
         digest says so in bold rather than leaving it to memory.

    Pure read of the ledger rows + registry; Telegram-HTML via esc()."""
    lines = ["📋 <b>PROMOTIONS — month-start forward check (#69)</b>"]
    for e in load_registry():
        fc = e["forward_check"]
        frozen = forward_check(e, rows)
        lines.append(f"[{esc(e['id'])}] {esc(e['status'])}"
                     + (f" {esc(e['promoted'])}" if e.get("promoted") else "")
                     + f" · frozen window {esc(fc['window'][0])}→"
                     f"{esc(fc['window'][1])}: {esc(_fmt_check(frozen))}")
        if e["status"] == "promoted":
            lo = (day - datetime.timedelta(days=183)).isoformat()
            rolling = forward_check(_windowed(e, lo, day.isoformat()), rows)
            lines.append(f"　demotion check (rolling 6m): "
                         f"{esc(_fmt_check(rolling))}"
                         + (" — <b>FAIL = demote, mandatory (registry "
                            "demotion_rule)</b>"
                            if rolling["status"] == "FAIL" else ""))
    return "\n".join(lines)


def verify_registry(path=REGISTRY):
    """CI guard (validate check [31]): every entry must name its gate
    artifact, a demotion rule, and a frozen criterion — the standing rule
    'nothing promotes without a pre-registered demotion rule' is enforced
    here, mechanically."""
    for e in load_registry(path):
        for field in ("gate_artifact", "demotion_rule", "if_promoted",
                      "earliest_promotion", "status"):
            assert e.get(field), f"registry entry {e.get('id')}: missing {field}"
        fc = e.get("forward_check") or {}
        for field in ("rank_column", "window", "horizon_rows",
                      "min_measured_rows", "criterion"):
            assert fc.get(field), \
                f"registry entry {e.get('id')}: forward_check missing {field}"


if __name__ == "__main__":
    rows = homily_ledger._read_rows()
    today = datetime.date.today().isoformat()
    print(f"promotions registry — {len(rows)} ledger rows, as of {today}\n")
    for e in load_registry():
        r = forward_check(e, rows)
        mt = f"{r['mean_top']:+.2f}%" if r["mean_top"] is not None else "—"
        mo = f"{r['mean_other']:+.2f}%" if r["mean_other"] is not None else "—"
        print(f"[{e['id']}] {e['status']} · earliest {e['earliest_promotion']}\n"
              f"  forward check: {r['status']} "
              f"(top-3 n={r['n_top']} mean {mt} vs other n={r['n_other']} "
              f"mean {mo}, horizon {e['forward_check']['horizon_rows']} rows)\n"
              f"  demotion rule on file: yes\n")
