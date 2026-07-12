"""#93 / Amendment A5 — the live overlay's pre-registered behaviours."""
import datetime

import gambit_backtest as bt
import gambit_live as gl


def D(s):
    return datetime.date.fromisoformat(s)


def mk_series(rows):
    """rows: [(date, o, h, l, c)] -> Series (volume constant)."""
    return bt.Series([(D(d), o, h, l, c, 1_000_000)
                      for d, o, h, l, c in rows])


BARS = [("2026-07-10", 100, 101, 99, 100),
        ("2026-07-13", 100, 102, 98, 101),
        ("2026-07-14", 101, 103, 99, 102),
        ("2026-07-17", 102, 104, 100, 103),
        ("2026-07-20", 103, 105, 101, 104),
        ("2026-07-24", 104, 106, 102, 105)]


def armed_book(series, sym="AAA"):
    paper = {"last_decision": "2026-07-10",
             "positions": {}, "pending": [{"side": "BUY", "sym": sym,
                                           "reason": "ROTATE"}]}
    book = gl.new_book()
    sheet, rows = gl.live_step(book, paper, series, series[sym], "BULL",
                               D("2026-07-10"), margin_zero=True)
    assert book["armed"] and book["pending"], "arming must queue the mirror"
    return book, paper


def advance(book, paper, series, sym, as_of, regime="BULL"):
    return gl.live_step(book, paper, series, series[sym], regime, D(as_of),
                        margin_zero=True)


def test_waiting_until_margin_zero():
    s = {"AAA": mk_series(BARS)}
    book = gl.new_book()
    sheet, rows = gl.live_step(book, {"last_decision": "2026-07-10",
                                      "positions": {}, "pending": []},
                               s, s["AAA"], "BULL", D("2026-07-10"),
                               margin_zero=False)
    assert "waiting for the clean slate" in sheet and not book["armed"]


def test_entry_sized_by_ladder_with_stop_and_tp():
    s = {"AAA": mk_series(BARS)}
    book, paper = armed_book(s)
    sheet, rows = advance(book, paper, s, "AAA", "2026-07-17")
    p = book["positions"]["AAA"]
    # filled at Monday 07-13 open 100; BULL target = 3000*1.30/5 = 780
    assert p["entry"] == 100 and abs(p["basis"] - 780.0) < 1e-6
    assert p["stop"] == 80.0 and p["tp"] == 140.0
    assert any(r["event"] == "FILL" and r["stop"] == "80.00" for r in rows)


def test_mixed_regime_sizes_smaller():
    s = {"AAA": mk_series(BARS)}
    book, paper = armed_book(s)
    advance(book, paper, s, "AAA", "2026-07-17", regime="MIXED")
    assert abs(book["positions"]["AAA"]["basis"] - 3000 * 1.15 / 5) < 1e-6


def test_stop_hit_realizes_loss_full_exit():
    bars = BARS[:2] + [("2026-07-14", 95, 96, 70, 75)] + BARS[3:]
    s = {"AAA": mk_series(bars)}
    book, paper = armed_book(s)
    advance(book, paper, s, "AAA", "2026-07-17")
    assert "AAA" not in book["positions"], "low 70 <= stop 80 -> full exit"
    r = book["realized"][-1]
    assert r["reason"] == "STOP" and r["pnl"] < 0


def test_gap_below_stop_fills_at_open_not_stop():
    bars = BARS[:2] + [("2026-07-14", 60, 62, 58, 61)] + BARS[3:]
    s = {"AAA": mk_series(bars)}
    book, paper = armed_book(s)
    sheet, rows = advance(book, paper, s, "AAA", "2026-07-17")
    stop_rows = [r for r in rows if r["event"] == "STOP"]
    assert stop_rows and float(stop_rows[0]["price"]) == 60.0, \
        "gap through the stop fills at the gapped open — modeled, not wished"


def test_tp_takes_half_once():
    bars = BARS[:2] + [("2026-07-14", 120, 150, 118, 145)] + BARS[3:]
    s = {"AAA": mk_series(bars)}
    book, paper = armed_book(s)
    advance(book, paper, s, "AAA", "2026-07-17")
    p = book["positions"]["AAA"]
    assert p["tp_taken"] and abs(p["basis"] - 390.0) < 1e-6, \
        "half the basis realized at TP, remainder rides"
    assert book["realized"][-1]["reason"] == "TP" \
        and book["realized"][-1]["pnl"] > 0


def test_kill_a_liquidates_and_stays_dead():
    s = {"AAA": mk_series(BARS)}
    book, paper = armed_book(s)
    advance(book, paper, s, "AAA", "2026-07-17")
    book["cash"] -= 1500.0                      # simulate a huge drawdown
    sheet, rows = advance(book, paper, s, "AAA", "2026-07-24")
    assert book["killed"] and "KILL-A" in book["killed"]["reason"]
    assert all(p["side"] == "SELL" for p in book["pending"]), \
        "kill = liquidate everything on the sheet"
    assert "KILLED" in sheet and "LIQUIDATE" in sheet


def test_kill_b_expectancy():
    s = {"AAA": mk_series(BARS)}
    book, paper = armed_book(s)
    advance(book, paper, s, "AAA", "2026-07-17")
    book["realized"] = [{"date": "2026-07-14", "sym": "X", "reason": "STOP",
                         "pnl": -1.0}] * gl.KILL_EXPECTANCY_N
    gl.check_kill(book, s, D("2026-07-20"), [])
    assert book["killed"] and "KILL-B" in book["killed"]["reason"]


def test_time_stop_proposes_sell():
    s = {"AAA": mk_series(BARS)}
    book, paper = armed_book(s)
    advance(book, paper, s, "AAA", "2026-07-17")
    book["positions"]["AAA"]["entry_date"] = "2026-04-01"   # >12 weeks old
    paper2 = dict(paper, last_decision="2026-07-24", pending=[])
    sheet, rows = gl.live_step(book, paper2, s, s["AAA"], "BULL",
                               D("2026-07-24"), margin_zero=True)
    assert any(p["reason"] == "TIME" and p["side"] == "SELL"
               for p in book["pending"]), "12-week time stop must fire"


def test_order_sheet_reports_kill_line_and_gross():
    s = {"AAA": mk_series(BARS)}
    book, paper = armed_book(s)
    sheet, _ = advance(book, paper, s, "AAA", "2026-07-17")
    assert "KILL line $2,100.00" in sheet and "cap 1.30 BULL" in sheet
    assert "stops move only at re-ranks" in sheet
