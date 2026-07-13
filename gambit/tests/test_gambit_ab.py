"""#96 / D-96 — the A5 A/B reader's stop-cost attribution (read-only)."""
import datetime

import gambit_ab as ab


def _buy(sym, d, px, qty):
    return {"date": d, "event": "FILL", "symbol": sym, "side": "BUY",
            "qty": str(qty), "price": str(px), "reason_code": "ROTATE"}


def _sell(sym, d, px, qty, reason):
    return {"date": d, "event": reason, "symbol": sym, "side": "SELL",
            "qty": str(qty), "price": str(px), "reason_code": reason}


def test_parse_episode_closes_on_full_exit():
    eps = ab.parse_episodes([_buy("AAA", "2026-08-03", 100, 10),
                             _sell("AAA", "2026-09-01", 80, 10, "STOP")])
    assert len(eps) == 1 and eps[0]["closed"]
    assert abs(eps[0]["ret"] + 0.20) < 1e-9 and eps[0]["basis"] == 1000.0
    assert eps[0]["final_reason"] == "STOP"


def test_tp_half_then_stop_aggregates_value_weighted_exit():
    eps = ab.parse_episodes([_buy("AAA", "2026-08-03", 100, 10),
                             _sell("AAA", "2026-08-20", 140, 5, "TP"),
                             _sell("AAA", "2026-09-01", 80, 5, "STOP")])
    assert len(eps) == 1 and eps[0]["closed"]
    assert abs(eps[0]["exit_px"] - 110.0) < 1e-9   # (140*5 + 80*5)/10
    assert eps[0]["final_reason"] == "STOP"


def test_stop_that_cost_return_vs_paper_hold():
    # live STOP −20%; paper HELD and rotated out +30% → the stop COST +50% of
    # the live basis (1000) = $500
    live = ab.parse_episodes([_buy("AAA", "2026-08-03", 100, 10),
                              _sell("AAA", "2026-09-01", 80, 10, "STOP")])
    paper = ab.parse_episodes([_buy("AAA", "2026-08-03", 100, 20),
                               _sell("AAA", "2026-10-01", 130, 20, "ROTATE")])
    attr = ab.attribute(live, paper)
    assert attr["matched"] == 1 and attr["pending"] == 0
    e = attr["episodes"][0]
    assert abs(e["delta_ret"] - 0.50) < 1e-9
    assert abs(attr["cum_cost"] - 500.0) < 1e-6      # +cost
    assert abs(attr["size_ratio"] - 2.0) < 1e-9      # paper basis 2000 / 1000


def test_stop_that_saved_when_paper_kept_falling():
    live = ab.parse_episodes([_buy("BBB", "2026-08-03", 100, 10),
                              _sell("BBB", "2026-09-01", 80, 10, "STOP")])
    paper = ab.parse_episodes([_buy("BBB", "2026-08-03", 100, 10),
                               _sell("BBB", "2026-10-01", 50, 10, "ROTATE")])
    attr = ab.attribute(live, paper)
    # paper −50% vs live −20% → delta −0.30 → stop SAVED $300
    assert abs(attr["cum_cost"] + 300.0) < 1e-6      # negative = saving


def test_open_paper_leg_is_pending_not_marked():
    live = ab.parse_episodes([_buy("CCC", "2026-08-03", 100, 10),
                              _sell("CCC", "2026-09-01", 80, 10, "STOP")])
    paper = ab.parse_episodes([_buy("CCC", "2026-08-03", 100, 10)])  # still open
    attr = ab.attribute(live, paper)
    assert attr["matched"] == 0 and attr["pending"] == 1
    assert attr["cum_cost"] == 0.0                   # no fabricated mark


def test_rotate_exit_is_not_a_stop_episode():
    # a live ROTATE exit is NOT a stop the paper book skipped → excluded
    live = ab.parse_episodes([_buy("DDD", "2026-08-03", 100, 10),
                              _sell("DDD", "2026-09-01", 120, 10, "ROTATE")])
    paper = ab.parse_episodes([_buy("DDD", "2026-08-03", 100, 10),
                               _sell("DDD", "2026-09-01", 120, 10, "ROTATE")])
    assert ab.attribute(live, paper)["matched"] == 0


def test_ab_block_pending_then_verdict(tmp_path):
    live_csv = tmp_path / "live.csv"
    paper_csv = tmp_path / "paper.csv"
    import csv
    cols = ["date", "event", "symbol", "side", "qty", "price", "reason_code"]

    def write(path, rows):
        with path.open("w", newline="") as f:
            w = csv.DictWriter(f, fieldnames=cols)
            w.writeheader()
            for r in rows:
                w.writerow({c: r.get(c, "") for c in cols})

    write(live_csv, [_buy("AAA", "2026-08-03", 100, 10),
                     _sell("AAA", "2026-09-01", 80, 10, "STOP")])
    write(paper_csv, [_buy("AAA", "2026-08-03", 100, 20),
                      _sell("AAA", "2026-10-01", 130, 20, "ROTATE")])
    # early: bar not reached → block shows the episode + "verdict pending"
    early = ab.ab_block(datetime.date(2026, 9, 15), live_path=live_csv,
                        paper_path=paper_csv)
    assert "stops COST $500" in early and "verdict pending" in early
    # far future (>26 weeks from 2026-08-03) → the verdict row fires
    late = ab.ab_block(datetime.date(2027, 3, 1), live_path=live_csv,
                       paper_path=paper_csv)
    assert "VERDICT" in late and "REPORT-ONLY" in late


def test_no_live_journal_is_silent():
    assert ab.ab_block(datetime.date(2026, 9, 1),
                       live_path="/no/such/live.csv",
                       paper_path="/no/such/paper.csv") == ""


def test_module_is_read_only():
    # no write-mode open, no writer, no network — it only reads two journals
    src = open(ab.__file__).read()
    for forbidden in ('"w"', "'w'", ".write(", "DictWriter", "csv.writer",
                      "append_rows", "save_snapshot", "urlopen"):
        assert forbidden not in src, f"gambit_ab must be read-only: {forbidden}"
