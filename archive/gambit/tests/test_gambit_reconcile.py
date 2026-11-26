"""#100 / D-100 — realized-cost reconcile (financing + fill slippage)."""
import csv
import json

import gambit_reconcile as gr


def _journal(path, fills):
    cols = ["date", "event", "symbol", "side", "qty", "price", "reason_code"]
    with path.open("w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=cols)
        w.writeheader()
        for d, sym, side, px in fills:
            w.writerow({"date": d, "event": "FILL", "symbol": sym,
                        "side": side, "qty": "1", "price": px,
                        "reason_code": "ROTATE"})


def test_effective_rate_annualizes():
    r = gr.effective_rate({"interest_usd": 4.0, "avg_loan_usd": 800.0,
                           "days": 31})
    assert abs(r - (4.0 / 800.0 * 365.0 / 31.0)) < 1e-12
    assert gr.effective_rate({"interest_usd": 4.0, "avg_loan_usd": 0.0,
                              "days": 31}) is None      # no loan → no rate
    assert gr.effective_rate(None) is None


def test_slippage_adverse_by_side_and_stress_flag(tmp_path):
    jp = tmp_path / "j.csv"
    _journal(jp, [("2026-08-04", "MU", "BUY", "100.00"),
                  ("2026-08-20", "MU", "SELL", "120.00")])
    rows = gr.read_journal(jp)
    # BUY filled 0.30% higher, SELL filled 0.25% lower → both adverse
    trades = [{"date": "2026-08-04", "sym": "MU", "side": "BUY",
               "price": 100.30},
              {"date": "2026-08-20", "sym": "MU", "side": "SELL",
               "price": 119.70}]
    sl = gr.slippage(rows, trades)
    assert sl["n"] == 2 and sl["unmatched"] == 0
    assert sl["mean_side"] > 0                        # net adverse
    # mean ~0.275%/side → implied RT 2*(0.125%+0.275%)=0.8% > 0.35% stress
    assert sl["over_stress"] is True


def test_slippage_within_model_is_not_flagged(tmp_path):
    jp = tmp_path / "j.csv"
    _journal(jp, [("2026-08-04", "MU", "BUY", "100.00")])
    # a favourable fill (paid less) → not adverse, not over stress
    sl = gr.slippage(gr.read_journal(jp),
                     [{"date": "2026-08-04", "sym": "MU", "side": "BUY",
                       "price": 99.95}])
    assert sl["n"] == 1 and not sl["over_stress"]


def test_slippage_unmatched_counts_not_crash(tmp_path):
    jp = tmp_path / "j.csv"
    _journal(jp, [("2026-08-04", "MU", "BUY", "100.00")])
    sl = gr.slippage(gr.read_journal(jp),
                     [{"date": "2026-08-04", "sym": "ZZ", "side": "BUY",
                       "price": 10.0}])
    assert sl["n"] == 0 and sl["unmatched"] == 1


def test_reconcile_block_renders_with_red_flag(tmp_path):
    jp = tmp_path / "j.csv"
    _journal(jp, [("2026-08-04", "MU", "BUY", "100.00")])
    sp = tmp_path / "stmt.json"
    sp.write_text(json.dumps({
        "period": {"from": "2026-08-01", "to": "2026-08-31", "days": 31},
        "financing": {"interest_usd": 8.0, "avg_loan_usd": 800.0},
        "trades": [{"date": "2026-08-04", "sym": "MU", "side": "BUY",
                    "price": 101.00}]}))            # 1% adverse → red
    blk = gr.reconcile_block(statement_path=sp, journal_path=jp)
    assert "cost reconcile" in blk and "financing" in blk
    assert "LEVERAGE.md §5" in blk and "🔴 OVER the 0.35%" in blk
    # 8.0/800 * 365/31 = 11.77% actual vs 5.8% modeled → material gap note
    assert "actual 11.77%" in blk and "material gap" in blk


def test_no_statement_is_silent():
    assert gr.reconcile_block(statement_path="/no/such.json",
                              journal_path="/no/such.csv") == ""
    assert gr.reconcile(gr.read_journal("/no/such.csv"), None) is None


def test_module_is_read_only():
    src = open(gr.__file__).read()
    for forbidden in ('"w"', "'w'", ".write(", "DictWriter", "csv.writer",
                      "urlopen", "save_snapshot", "append_rows"):
        assert forbidden not in src, f"gambit_reconcile read-only: {forbidden}"
