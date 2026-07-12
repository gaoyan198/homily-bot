#!/usr/bin/env python3
"""
GAMBIT G-S5 — the trading journal (= ledger): append-only, SHA-256 hash-chained
from row 1 (homily #62 pattern), plus the paper-book snapshot.

The track record IS the product (PRD §0.2); it starts un-fakeable. Every row
carries `row_sha = SHA-256(prev_sha | this row's fields)`, so any retro-edit or
deletion breaks the chain at the tampered row — verify() finds it, and validate
gates the send on it (a K4 integrity breach, PRD §5.3). Nothing here places a
real order; the journal only records the paper simulator's decisions and fills.

Schema (DESIGNS D-G6), one row per event:
  date · event · symbol · side · qty · price · stop · tp · r_distance ·
  reason_code · rank_rs · regime · equity_after · notes · row_sha

event ∈ {SCAN, PROPOSE, FILL, STOP, TP, TRAIL, TIME, REGIME, SKIP}. S1-pure
emits SCAN/PROPOSE/FILL/REGIME/SKIP only (it carries no stop stack — Amendment
A4); the stop-family events exist for arms that do.
"""
import csv
import datetime
import hashlib
import json
from pathlib import Path

COLUMNS = ["date", "event", "symbol", "side", "qty", "price", "stop", "tp",
           "r_distance", "reason_code", "rank_rs", "regime", "equity_after",
           "notes"]
_ALL = COLUMNS + ["row_sha"]
GENESIS = "0" * 64
EVENTS = {"SCAN", "PROPOSE", "FILL", "STOP", "TP", "TRAIL", "TIME",
          "REGIME", "SKIP"}


def _canon(row):
    """Deterministic field serialization for hashing (order-fixed, no floats
    left to platform repr drift — everything is stringified as stored)."""
    return "|".join("" if row.get(c) is None else str(row.get(c, ""))
                    for c in COLUMNS)


def row_hash(prev_sha, row):
    return hashlib.sha256(f"{prev_sha}|{_canon(row)}".encode()).hexdigest()


def read_rows(path):
    path = Path(path)
    if not path.exists():
        return []
    with path.open(newline="") as f:
        return list(csv.DictReader(f))


def last_sha(path):
    rows = read_rows(path)
    return rows[-1]["row_sha"] if rows else GENESIS


def append_rows(path, rows):
    """Append event rows, extending the hash chain. `rows` are dicts over
    COLUMNS (missing keys default blank). Returns the new tip sha."""
    path = Path(path)
    prev = last_sha(path)
    new_exists = path.exists()
    for r in rows:
        if r.get("event") not in EVENTS:
            raise ValueError(f"unknown event {r.get('event')!r}")
    with path.open("a", newline="") as f:
        w = csv.DictWriter(f, fieldnames=_ALL)
        if not new_exists:
            w.writeheader()
        for r in rows:
            full = {c: r.get(c, "") for c in COLUMNS}
            full["row_sha"] = prev = row_hash(prev, full)
            w.writerow(full)
    return prev


def verify(path):
    """Recompute the chain. -> (ok: bool, bad_index: int | None). bad_index is
    the 0-based row where the stored sha diverges (retro-edit / deletion /
    reorder), or None when the ledger is intact."""
    prev = GENESIS
    for i, row in enumerate(read_rows(path)):
        expect = row_hash(prev, row)
        if row.get("row_sha") != expect:
            return False, i
        prev = row["row_sha"]
    return True, None


# ----------------------------------------------------------------- snapshot --

def load_snapshot(path):
    path = Path(path)
    if not path.exists():
        return None
    return json.loads(path.read_text())


def save_snapshot(path, state):
    """Write the paper-book state. `as_of` is stamped from the state's own
    session date, never local now() (R7 discipline)."""
    Path(path).write_text(json.dumps(state, indent=2, sort_keys=True,
                                     default=str))


def new_state(inception, capital=20_000.0):
    d = inception.isoformat() if isinstance(inception, datetime.date) \
        else inception
    return {"inception": d, "as_of": None, "last_decision": None,
            "rotation_anchor": None, "cash": capital, "capital": capital,
            "positions": {}, "pending": [], "hwm": capital,
            "qqq_shares": None, "closed_trades": 0}
