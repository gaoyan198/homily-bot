"""#93 / Amendment A5 — the live overlay's pre-registered behaviours."""
import datetime
import json

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


# --- #95 flywheel skim (D-95): quarter-end profit banked to the DCA ---------

def _profit_book(cash=3600.0, equity=3600.0, skimmed=0.0):
    """An armed live book sitting on realized profit in CASH (no open
    positions) — the clean case for exercising maybe_skim in isolation."""
    b = gl.new_book()
    b.update({"armed": "2026-08-01", "cash": cash, "equity": equity,
              "hwm": equity, "skimmed": skimmed,
              "realized": [{"date": "2026-08-14", "sym": "X",
                            "reason": "TP", "pnl": 600.0}]})
    return b


def test_skim_banks_profit_at_quarter_end():
    b = _profit_book()
    rows = []
    s = gl.maybe_skim(b, None, D("2026-10-03"), rows)   # Oct = quarter-end
    assert s == 600.0 and b["skimmed"] == 600.0
    assert b["cash"] == 3000.0 and b["equity"] == 3000.0   # equity −= skim
    assert b["skims"] == [{"date": "2026-10-03", "usd": 600.0,
                           "quarter": "2026-Q4", "qqq": None}]
    assert any(r["event"] == "SKIM" for r in rows)


def test_skim_is_kill_safe_contributed_and_realized_untouched():
    """The pre-registered kills must not be softened by the sleeve's own
    successes: a skim never touches `contributed` and never enters
    `realized` (KILL-B's expectancy list). The kill CHECK is byte-identical
    before and after the SKIM."""
    b = _profit_book()
    before_realized = [dict(r) for r in b["realized"]]
    before_contrib = b["contributed"]
    rows = []
    gl.maybe_skim(b, None, D("2026-10-03"), rows)
    assert b["realized"] == before_realized     # skim is NOT a trade
    assert b["contributed"] == before_contrib   # skim is NOT principal
    assert not any(r.get("reason_code") == "SKIM" for r in b["realized"])
    # KILL-B expectancy reads only `realized` → identical result post-skim
    ser = {}
    gl.check_kill(b, ser, D("2026-10-03"), [])
    assert not b["killed"]                       # +600 expectancy, no kill


def test_no_skim_below_baseline_or_off_quarter():
    # a drawdown (equity below contributed) skims nothing — G8: red pays $0
    b = _profit_book(cash=200.0, equity=2500.0)
    assert gl.maybe_skim(b, None, D("2026-10-03"), []) == 0.0
    assert b["skimmed"] == 0.0
    # a normal (non-quarter-end) month never skims, even flush with profit
    b2 = _profit_book()
    assert gl.maybe_skim(b2, None, D("2026-11-07"), []) == 0.0
    assert b2["last_skim_q"] is None             # untouched off-quarter


def test_skim_bounded_by_free_cash_not_paper_profit():
    # profit exists (equity 3600 > baseline 3000) but only $250 is free cash
    b = _profit_book(cash=250.0, equity=3600.0)
    s = gl.maybe_skim(b, None, D("2026-10-03"), [])
    assert s == 250.0 and b["cash"] == 0.0       # can't skim tied-up money


def test_no_double_skim_same_quarter_and_ratchet():
    b = _profit_book()
    assert gl.maybe_skim(b, None, D("2026-10-03"), []) == 600.0
    # same quarter, run again → nothing more
    assert gl.maybe_skim(b, None, D("2026-10-10"), []) == 0.0
    assert b["skimmed"] == 600.0
    # next quarter, equity back at baseline (3000) → ratchet blocks re-skim
    assert gl.maybe_skim(b, None, D("2027-01-02"), []) == 0.0
    # next quarter WITH fresh profit above the ratcheted baseline → skims it
    b["cash"] += 150.0
    b["equity"] += 150.0
    assert gl.maybe_skim(b, None, D("2027-04-03"), []) == 150.0
    assert b["skimmed"] == 750.0


def test_killed_book_never_skims():
    b = _profit_book()
    b["killed"] = {"date": "2026-09-10", "reason": "KILL-A: ..."}
    assert gl.maybe_skim(b, None, D("2026-10-03"), []) == 0.0


# --- #98 scale ladder (D-98): the bankroll is earned -----------------------

def test_scale_check_not_earned_at_base():
    b = gl.new_book()                              # contributed 3000, 0 trades
    sc = gl.scale_check(b)
    assert sc["next_step"] == 6000.0 and not sc["earned_mechanical"]
    assert sc["conditions"]["on-ladder"] is True
    assert sc["conditions"]["closed>=20 (since inception)"] is False


def test_scale_check_earned_when_conditions_met():
    b = gl.new_book()
    b["realized"] = [{"date": "2026-08-01", "sym": "X", "reason": "TP",
                      "pnl": 5.0}] * 20            # 20 closed, expectancy +5
    sc = gl.scale_check(b)
    assert sc["earned_mechanical"] and sc["next_step"] == 6000.0
    b["killed"] = {"date": "x", "reason": "KILL-A"}   # a kill blocks it
    assert not gl.scale_check(b)["earned_mechanical"]


def test_check_scale_passes_at_base_and_no_book(tmp_path):
    import gambit_validate as gv
    assert gv.check_scale(root=tmp_path) == []     # no book → nothing to guard
    (tmp_path / "gambit_live_book.json").write_text(
        json.dumps(gl.new_book()))                 # base 3000, no A5 needed
    assert gv.check_scale(root=tmp_path) == []


def test_check_scale_fails_off_ladder_and_unsigned_step(tmp_path):
    import gambit_validate as gv
    bp = tmp_path / "gambit_live_book.json"
    # off-ladder amount → fail
    bp.write_text(json.dumps(dict(gl.new_book(), contributed=5000.0)))
    fails = gv.check_scale(root=tmp_path)
    assert any("OFF the pre-registered ladder" in f for f in fails)
    # on a step (6000) but no dated A5 owner line → fail
    bp.write_text(json.dumps(dict(gl.new_book(), contributed=6000.0)))
    assert any("without a dated AMENDMENT_A5" in f
               for f in gv.check_scale(root=tmp_path))
    # add a dated owner line naming the step → passes
    (tmp_path / "AMENDMENT_A5.md").write_text(
        "2026-11-02 — owner: scale the sleeve to US$6,000 (6k), "
        "preconditions met per --scale-check.")
    assert gv.check_scale(root=tmp_path) == []
