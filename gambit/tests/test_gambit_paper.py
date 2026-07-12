"""G-S5 paper-simulator tests: the S1-pure paper loop advances a persisted book
one weekly invocation at a time and must (a) fill at the NEXT open (T+1, no
look-ahead), (b) size equal-weight eq/5, (c) never take cash below zero (G7),
(d) hold the strong names and rotate out the weak, (e) liquidate on a regime
flip, and (f) replay bit-for-bit deterministically.
"""
import datetime

import gambit_arms as ga
import gambit_backtest as bt
import gambit_journal as gj
import gambit_paper as gp

MON = datetime.date(2019, 1, 7)          # a Monday


def tape(specs, start=MON):
    bars, d, i = [], start, 0
    while i < len(specs):
        if d.weekday() < 5:
            bars.append((d,) + specs[i])
            i += 1
        d += datetime.timedelta(days=1)
    return bt.Series(bars)


def rise(n, start=50.0, rate=0.003, v=6e6):
    out = []
    for i in range(n):
        c = start * (1 + rate) ** i
        o = start * (1 + rate) ** (i - 1) if i else start
        out.append((o, c * 1.002, o * 0.997, c, v))
    return out


def world(n=340, k=8):
    """k rising names with monotonically increasing trend strength, plus a
    steadily-rising QQQ (=> BULL regime, cap 1.0 throughout)."""
    series, inds = {}, {}
    for j in range(k):
        s = tape(rise(n, rate=0.0015 + 0.0004 * j))
        series[f"N{j:02d}"] = s
        inds[f"N{j:02d}"] = ga.Ind(s)
    qqq = tape([(100 + 0.1 * i, 100 + 0.1 * i, 100 + 0.1 * i,
                 100 + 0.1 * i, 1e7) for i in range(n)])
    return series, inds, qqq


def late_fridays(qqq, count=8):
    frs = ga.fridays(list(qqq.dates))
    return [f for f in frs if qqq.idx_at(f) >= ga.MIN_RS_BARS + 5][:count]


def replay(state, series, inds, qqq, run_fridays):
    """Advance the book across a list of run dates, returning all journal rows."""
    allrows = []
    for f in run_fridays:
        rows, _ = gp.weekly_step(state, series, inds, qqq, f)
        allrows += rows
    return allrows


def test_first_week_proposes_but_does_not_fill():
    series, inds, qqq = world()
    frs = late_fridays(qqq)
    state = gj.new_state(frs[0])
    rows, digest = gp.weekly_step(state, series, inds, qqq, frs[0])
    assert not state["positions"], "no fills on the decision week itself (T+1)"
    props = [r for r in rows if r["event"] == "PROPOSE" and r["side"] == "BUY"]
    assert len(props) == gp.N, "the initial decision proposes the full top-5"
    assert digest["equity"] == state["capital"], "equity unchanged before any fill"


def test_second_week_fills_next_open_equal_weight_and_cash_nonneg():
    series, inds, qqq = world()
    frs = late_fridays(qqq)
    state = gj.new_state(frs[0])
    gp.weekly_step(state, series, inds, qqq, frs[0])       # propose
    rows, _ = gp.weekly_step(state, series, inds, qqq, frs[1])   # settle+decide
    fills = [r for r in rows if r["event"] == "FILL" and r["side"] == "BUY"]
    assert len(fills) == gp.N, "all five proposals fill at the next open"
    assert state["cash"] >= -1e-9, "cash must never go negative (G7)"
    # equal-weight: entry notionals within a hair of each other
    notionals = [p["qty"] * p["entry"] for p in state["positions"].values()]
    assert max(notionals) - min(notionals) < 1.0, \
        f"equal-weight sizing expected, got {notionals}"


def test_holds_strong_rotates_weak():
    series, inds, qqq = world()
    frs = late_fridays(qqq)
    state = gj.new_state(frs[0])
    replay(state, series, inds, qqq, frs[:2])
    held = set(state["positions"])
    strong = {f"N{j:02d}" for j in range(3, 8)}    # the 5 strongest trends
    assert held == strong, f"top-5 by RS expected {strong}, held {held}"


def test_fill_price_is_the_next_session_open():
    series, inds, qqq = world()
    frs = late_fridays(qqq)
    state = gj.new_state(frs[0])
    gp.weekly_step(state, series, inds, qqq, frs[0])
    rows, _ = gp.weekly_step(state, series, inds, qqq, frs[1])
    fill = next(r for r in rows if r["event"] == "FILL")
    sym = fill["symbol"]
    fill_date = datetime.date.fromisoformat(fill["date"])
    i = series[sym].idx_at(fill_date)
    assert series[sym].dates[i] == fill_date, "fill must land on a real session"
    o, c = series[sym].bars[i][1], series[sym].bars[i][4]
    px = float(fill["price"])
    assert abs(px - o) < abs(px - c), \
        "fill price must be that session's OPEN, not its close (T+1 open model)"
    assert abs(px - o) < 1e-3, "fill price ties to the open within ledger precision"


def test_deterministic_replay():
    s1, i1, q1 = world()
    s2, i2, q2 = world()
    frs = late_fridays(q1, count=8)
    a = replay(gj.new_state(frs[0]), s1, i1, q1, frs)
    b = replay(gj.new_state(frs[0]), s2, i2, q2, frs)
    assert a == b, "same bars + same run dates => identical journal rows"
    assert any(r["event"] == "FILL" for r in a), "the replay must actually trade"


def test_regime_flip_liquidates_and_blocks_entry():
    series, inds, _ = world()
    n = len(series["N00"].bars)
    # QQQ rises for 3/4 then collapses -> a bear flip late in the tape
    up = [(100 + 0.2 * i,) * 4 + (1e7,) for i in range(n * 3 // 4)]
    dn0 = up[-1][0]
    down = [(dn0 - 0.9 * i,) * 4 + (1e7,) for i in range(1, n - len(up) + 1)]
    qqq = tape(up + down)
    regime = ga.Regime(qqq)
    bears = [d for d in qqq.dates if regime.at(d)[0]]
    assert bears, "crafted QQQ collapse must flip the regime"
    frs = [f for f in ga.fridays(list(qqq.dates))
           if qqq.idx_at(f) >= ga.MIN_RS_BARS + 5]
    state = gj.new_state(frs[0])
    saw_positions = False
    for f in frs:
        gp.weekly_step(state, inds and series, inds, qqq, f)
        if state["positions"]:
            saw_positions = True
        if f >= bears[0] and not state["pending"]:
            # once bear and settled, the book must be flat and stay flat
            assert not state["positions"], "regime bear must liquidate the book"
    assert saw_positions, "the book must have traded before the flip"
