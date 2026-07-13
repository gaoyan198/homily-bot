#!/usr/bin/env python3
"""
GAMBIT LIVE weekly runner (#93 / Amendment A5). Runs AFTER weekly_run.py in
the same Saturday CI job: loads the committed paper snapshot (the single
source of names — this runner never ranks), advances the live overlay one
week (stops / TPs / time stops / ladder-sized mirrors of the paper
decisions / kill checks), appends to the hash-chained live journal, saves
the live book, and prints the owner's Monday ORDER SHEET.

Fetches only the handful of names the two books actually involve, plus the
regime pair — not the universe. `--as-of` pins the date (R7); default is
the last QQQ session. MARGIN_ZERO (the owner's clean-slate flag) arms the
first sheet; until it is set this prints a waiting line and exits 0.
"""
import argparse
import datetime
import os
import sys
from pathlib import Path

import gambit_backtest as bt
import gambit_data
import gambit_journal as gj
import gambit_live

ROOT = Path(__file__).resolve().parent
BOOK = ROOT / "gambit_live_book.json"
JOURNAL = ROOT / "gambit_live_journal.csv"
SNAPSHOT = ROOT / "snapshot.json"

sys.path.insert(0, str(ROOT.parent))            # homily_regime (frozen engine)
import homily_regime  # noqa: E402


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--as-of", default=None)
    args = ap.parse_args()

    paper = gj.load_snapshot(SNAPSHOT)
    if paper is None:
        raise SystemExit("no paper snapshot — run weekly_run.py first")
    book = gj.load_snapshot(BOOK) or gambit_live.new_book()

    ok, bad = gj.verify(JOURNAL)
    if not ok:
        raise SystemExit(f"[K4] live journal chain broken at row {bad}")

    qqq_b, qqq_a = gambit_data.fetch_series("QQQ", rng="max")
    qqq = bt.Series(bt.adjust_bars(qqq_b, qqq_a))
    as_of = (datetime.date.fromisoformat(args.as_of) if args.as_of
             else qqq.dates[-1])

    syms = (set(paper.get("positions", {}))
            | {p["sym"] for p in paper.get("pending", [])}
            | set(book.get("positions", {}))
            | {p["sym"] for p in book.get("pending", [])})
    series = {}
    for sym in sorted(syms):
        try:
            b, a = gambit_data.fetch_series(sym, rng="2y")
            series[sym] = bt.Series(bt.adjust_bars(b, a))
        except Exception as e:                   # noqa: BLE001
            print(f"[fetch] {sym}: {e}")

    regime_label = homily_regime.market_regime().label
    margin_zero = os.getenv("MARGIN_ZERO", "").lower() in ("1", "true",
                                                           "yes", "on")
    # #97 (G5): the core book's tickers, so the sheet can warn on cross-book
    # overlap. Read-only; a missing/other-format holdings file just disables
    # the warning (core_tickers stays empty).
    try:
        import homily_positions
        core_tickers = set(homily_positions.load_positions())
    except Exception:
        core_tickers = set()
    sheet, rows = gambit_live.live_step(book, paper, series, qqq,
                                        regime_label, as_of,
                                        margin_zero=margin_zero,
                                        core_tickers=core_tickers)
    if rows:
        gj.append_rows(JOURNAL, rows)
    gj.save_snapshot(BOOK, book)
    print(sheet)
    print(f"\n[live journal] +{len(rows)} rows -> {JOURNAL.name}; "
          f"book -> {BOOK.name}")


if __name__ == "__main__":
    main()
