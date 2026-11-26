#!/usr/bin/env python3
"""
GAMBIT G-S5 — the weekly paper loop (PRD §5.1). One invocation:

  1. load bars (QQQ market calendar + universe.json names), build Series+Ind;
  2. advance the persisted paper book one step (gambit_paper.weekly_step):
     settle last week's proposals at T+1 open, decide on the latest Friday;
  3. append the resulting events to the hash-chained journal (gambit_journal);
  4. write snapshot.json and render the owner digest (gambit_digest).

Order is validate → run → commit (homily R5/#16): this module NEVER mutates the
ledger or "sends" a digest around the validate gate — CI runs gambit_validate.py
first, and a red suite means no run. Paper only: no order is placed; the arm is
S1-pure, promoted by Amendment A4, unlevered, cash ≥ 0 (G7).

Dates come from bar timestamps (US session date), never local now() — the R7
discipline. `--as-of YYYY-MM-DD` pins the run date; default is the last QQQ
session in the fetched data.
"""
import argparse
import datetime
import json
from pathlib import Path

import gambit_backtest as bt
import gambit_arms as ga
import gambit_data
import gambit_digest
import gambit_journal as gj
import gambit_paper

ROOT = Path(__file__).resolve().parent
JOURNAL = ROOT / "gambit_journal.csv"
SNAPSHOT = ROOT / "snapshot.json"


def load_live_series(universe_path=ROOT / "universe.json"):
    uni = json.load(open(universe_path))
    symbols = [m["symbol"] for m in uni["symbols"]]
    qqq_b, qqq_a = gambit_data.fetch_series("QQQ", rng="max")
    qqq = bt.Series(bt.adjust_bars(qqq_b, qqq_a))
    series, inds = {}, {}
    for sym in symbols:
        try:
            b, a = gambit_data.fetch_series(sym, rng="max")
            series[sym] = bt.Series(bt.adjust_bars(b, a))
            inds[sym] = ga.Ind(series[sym])
        except Exception:                     # noqa: BLE001 — report, don't die
            pass
    return series, inds, qqq


def run_once(state, series, inds, qqq, as_of, *, journal=JOURNAL,
             snapshot=SNAPSHOT, write=True):
    """Pure-ish core: advance one week, persist journal+snapshot+digest text.
    Returns (digest_text, rows). `write=False` runs it dry (tests)."""
    rows, digest = gambit_paper.weekly_step(state, series, inds, qqq, as_of)
    if write and rows:
        gj.append_rows(journal, rows)
    if write:
        gj.save_snapshot(snapshot, state)
    return gambit_digest.render(digest), rows


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--as-of", default=None,
                    help="run date YYYY-MM-DD (default: last fetched session)")
    args = ap.parse_args()

    series, inds, qqq = load_live_series()
    as_of = (datetime.date.fromisoformat(args.as_of) if args.as_of
             else qqq.dates[-1])

    state = gj.load_snapshot(SNAPSHOT)
    if state is None:
        # inception = the first decision this loop can act on
        frs = gambit_paper._fridays_upto(qqq.dates, as_of)
        state = gj.new_state(frs[-1] if frs else as_of)

    ok, bad = gj.verify(JOURNAL)
    if not ok:
        raise SystemExit(f"[K4] journal hash chain broken at row {bad} — "
                         "refusing to append to a tampered ledger")

    text, rows = run_once(state, series, inds, qqq, as_of)
    print(text)
    print(f"\n[journal] +{len(rows)} rows -> {JOURNAL.name}; "
          f"snapshot -> {SNAPSHOT.name}")


if __name__ == "__main__":
    main()
