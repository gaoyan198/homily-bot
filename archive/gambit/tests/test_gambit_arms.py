"""G-S4 engine tests: the D-G3 exit stack with the honest fill model,
risk-parity sizing, regime kill-switch, T+1-open entries, and the S2/S3
signal triggers on crafted tapes.

Tape notes: the registered trail rule (stop = max(initial, 20-day low),
active from entry) means any FLAT tape self-stops — its 20-day low sits one
tick under price. Holding-period fixtures therefore use gently RISING
tapes, whose lows never revisit the trailing 20-day low.
"""
import datetime
import math

import gambit_arms as ga
import gambit_backtest as bt

D0 = datetime.date(2020, 1, 6)     # a Monday
FRI = D0 + datetime.timedelta(days=4)
MON2 = D0 + datetime.timedelta(days=7)


def tape(specs, start=D0):
    """specs: list of (o, h, l, c, v) -> weekday bars."""
    bars, d, i = [], start, 0
    while i < len(specs):
        if d.weekday() < 5:
            o, h, l, c, v = specs[i]
            bars.append((d, o, h, l, c, v))
            i += 1
        d += datetime.timedelta(days=1)
    return bt.Series(bars)


def rise(n, start=100.0, rate=0.004, v=5e6):
    """Strictly rising closes AND lows (open = prev close, low = open-0.3%)."""
    out = []
    for i in range(n):
        c = start * (1 + rate) ** i
        o = start * (1 + rate) ** (i - 1) if i else start
        out.append((o, c * 1.002, o * 0.997, c, v))
    return out


def bull_qqq(n=400):
    return tape([(100 + 0.1 * i,) * 4 + (1e7,) for i in range(n)])


def fire_once(day=FRI, r=4.0):
    def sig(d, decile, inds, series, consumed, events):
        return [("AAA", r)] if d == day else []
    return sig


def run(specs, *, qqq=None, mode="setup", signal=None):
    s = tape(specs)
    series = {"AAA": s}
    inds = {"AAA": ga.Ind(s)}
    regime = ga.Regime(qqq or bull_qqq(len(s.bars)))
    return ga.run_arm(series, inds, list(s.dates), regime,
                      mode=mode, signal=signal), s


def test_entry_fills_next_open_after_friday():
    specs = rise(70)
    o, h, l, c, v = specs[5]                      # the Monday after FRI
    specs[5] = (103.0, 103.5, 102.5, c, v)        # force a distinctive open
    (curve, trades, _), s = run(specs, signal=fire_once())
    assert trades, "entry then a later exit must exist"
    t = trades[0]
    assert t["entry"] == 103.0 and t["entry_date"] == MON2, \
        "signal on Friday close must fill at Monday's open, not before"


def test_stop_gap_through_fills_at_open():
    specs = rise(30) + [(80.0, 81.0, 79.0, 80.0, 5e6)] + \
        [(80.0, 88.0, 72.0, 80.0, 5e6)] * 5
    (curve, trades, _), s = run(specs, signal=fire_once())
    stops = [t for t in trades if t["reason"] == "STOP"]
    assert stops and stops[0]["exit"] == 80.0, \
        "gap through the stop fills at the open — the gap is taken in full"
    assert math.isclose(stops[0]["R"], (80.0 - stops[0]["entry"]) / 4.0)


def test_stop_touch_fills_at_stop_price():
    # early spike-low keeps the 20-day low (88) under the initial stop, so
    # the stop stays exactly at entry-4 = 96; then a bar touches it
    base = [(100.0, 100.5, 99.5, 100.0, 5e6)] * 8
    base[2] = (100.0, 100.5, 88.0, 100.0, 5e6)
    base[7] = (97.0, 98.0, 95.9, 97.0, 5e6)
    specs = base + [(98.0, 98.5, 97.5, 98.0, 5e6)] * 5
    (curve, trades, _), s = run(specs, signal=fire_once())
    stops = [t for t in trades if t["reason"] == "STOP"]
    assert stops and stops[0]["exit"] == 96.0, \
        "open above the stop + low through it must fill AT the stop"
    assert math.isclose(stops[0]["R"], -1.0)


def test_tp_half_at_plus_2r_remainder_runs():
    specs = rise(70, rate=0.006)
    (curve, trades, _), s = run(specs, signal=fire_once())
    tps = [t for t in trades if t["reason"] == "TP"]
    assert tps, f"no TP fill in {set(t['reason'] for t in trades)}"
    t = tps[0]
    assert t["frac"] == 0.5 and math.isclose(t["R"], 2.0), \
        "TP must close HALF at exactly +2R"
    assert math.isclose(t["exit"], t["entry"] + 8.0)
    later = [x for x in trades if x["exit_date"] > t["exit_date"]]
    assert later, "the remaining half must exit later (trail/time)"


def test_time_stop_after_8_weeks():
    specs = rise(70)
    (curve, trades, _), s = run(specs, signal=fire_once())
    times = [t for t in trades if t["reason"] == "TIME"]
    assert times
    held = (times[0]["exit_date"] - times[0]["entry_date"]).days
    assert 56 <= held <= 60, f"time stop fired after {held} days"


def test_trail_ratchets_up_and_locks_profit():
    specs = rise(40, rate=0.006)
    stop_after_rise = specs[21][2]           # low20 ≈ low of ~20 sessions ago
    crash = (stop_after_rise + 1.0, stop_after_rise + 1.5,
             stop_after_rise - 10.0, stop_after_rise - 8.0, 5e6)
    specs = specs + [crash] + [(90.0, 91.0, 89.0, 90.0, 5e6)] * 3
    (curve, trades, _), s = run(specs, signal=fire_once())
    stops = [t for t in trades if t["reason"] == "STOP"]
    assert stops, "crash must trigger the trailed stop"
    t = stops[-1]
    assert t["exit"] > t["entry"], \
        f"trail should lock profit: exit {t['exit']} vs entry {t['entry']}"


def test_risk_parity_sizing_and_accounting():
    specs = rise(70)
    (curve, trades, _), s = run(specs, signal=fire_once())
    c = bt.COST_SIDE
    qty0 = (ga.RISK_FRAC * 20_000 / 4.0) * (1 - c)    # 0.75% eq / 1R shares
    dollars = qty0 / (1 - c) * trades[0]["entry"]
    assert dollars < ga.MAX_NOTIONAL_FRAC * 20_000, "notional cap respected"
    q, proceeds = qty0, 0.0
    for t in trades:                # replay fills: TP half then TIME remainder
        sold = q * t["frac"]
        proceeds += sold * t["exit"] * (1 - c)
        q -= sold
    assert q < 1e-9, "position fully closed by the stack"
    assert math.isclose(curve[-1][1], 20_000 - dollars + proceeds,
                        rel_tol=1e-9), \
        "final equity must equal capital ± the position's P&L and costs"


def test_regime_flip_liquidates_and_blocks_entries():
    n = 500
    qqq_specs = ([(100 + 0.2 * i,) * 4 + (1e7,) for i in range(300)]
                 + [(160 - 0.4 * i,) * 4 + (1e7,) for i in range(n - 300)])
    qqq = tape(qqq_specs)
    regime = ga.Regime(qqq)
    bear_days = [d for d in qqq.dates if regime.at(d)[0]]
    assert bear_days, "crafted QQQ collapse must flip the regime"
    first_bear = bear_days[0]
    s = tape(rise(n, rate=0.001))
    series, inds = {"AAA": s}, {"AAA": ga.Ind(s)}
    # signal fires EVERY Friday — but no entry may open during bear
    def always(d, decile, i_, s_, c_, e_):
        return [("AAA", 4.0)]
    curve, trades, _ = ga.run_arm(series, inds, list(s.dates), regime,
                                  mode="setup", signal=always)
    assert trades
    for t in trades:
        if t["entry_date"] <= first_bear <= t["exit_date"]:
            assert t["reason"] == "REGIME", \
                "a position held into the flip must be closed by REGIME"
        assert not regime.at(t["entry_date"])[0], "entered during bear!"


def test_s1_rotation_never_holds_weak_names():
    series, inds = {}, {}
    n = 300
    for k in range(12):
        rate = 0.0002 + 0.0004 * k
        series[f"N{k:02d}"] = tape(rise(n, start=30.0, rate=rate))
        inds[f"N{k:02d}"] = ga.Ind(series[f"N{k:02d}"])
    cal = list(series["N00"].dates)
    regime = ga.Regime(bull_qqq(n))
    curve, trades, _ = ga.run_arm(series, inds, cal, regime, mode="s1_pure")
    held = {t["sym"] for t in trades}
    weak = {f"N{k:02d}" for k in range(5)}
    assert not (held & weak), f"weak names traded: {held & weak}"
    assert curve[-1][1] > 20_000, "top-5 of rising tapes must gain"


def test_s2_signal_fires_on_pullback_reclaim():
    up = rise(300)
    peak = up[-1][3]
    pull, px = [], peak
    for _ in range(6):                        # ~6% pullback
        px *= 0.99
        pull.append((px, px * 1.005, px * 0.995, px, 5e6))
    rc = px * 1.02                            # reclaim bar
    pull.append((px, rc * 1.001, px * 0.99, rc, 5e6))
    s = tape(up + pull)
    out = ga.s2_signal(s.dates[-1], [("AAA", 1.0)], {"AAA": ga.Ind(s)},
                       {"AAA": s}, set(), {})
    assert out and out[0][0] == "AAA"
    # without the reclaim bar there must be NO signal
    s2 = tape(up + pull[:-1])
    out2 = ga.s2_signal(s2.dates[-1], [("AAA", 1.0)], {"AAA": ga.Ind(s2)},
                        {"AAA": s2}, set(), {})
    assert not out2


def _vol_tape(resolution):
    decline = [(200.0 - i, 204.0 - i, 196.0 - i, 200.0 - i, 5e6)
               for i in range(200)]
    quiet = [(120.0, 120.3, 119.7, 120.0, 3e6)] * 10
    return tape(decline + quiet + resolution)


def test_s3_signal_volume_gate_and_zone_consumed():
    s = _vol_tape([(126.0, 127.0, 125.0, 126.0, 12e6)] * 2)   # 4x volume
    consumed, events = set(), {"VOLHOLE_BREAKDOWN": 0}
    out = ga.s3_signal(s.dates[-1], [("AAA", 1.0)], {"AAA": ga.Ind(s)},
                       {"AAA": s}, consumed, events)
    assert out and out[0][0] == "AAA"
    out2 = ga.s3_signal(s.dates[-1], [("AAA", 1.0)], {"AAA": ga.Ind(s)},
                        {"AAA": s}, consumed, events)
    assert not out2, "one zone, one entry — ever (parsimony)"
    s_lo = _vol_tape([(126.0, 127.0, 125.0, 126.0, 3e6)] * 2)  # no vol expans.
    out3 = ga.s3_signal(s_lo.dates[-1], [("AAA", 1.0)], {"AAA": ga.Ind(s_lo)},
                        {"AAA": s_lo}, set(), {"VOLHOLE_BREAKDOWN": 0})
    assert not out3


def test_s3_breakdown_is_journal_only():
    s = _vol_tape([(112.0, 113.0, 111.0, 112.0, 12e6)] * 2)
    events = {"VOLHOLE_BREAKDOWN": 0}
    out = ga.s3_signal(s.dates[-1], [("AAA", 1.0)], {"AAA": ga.Ind(s)},
                       {"AAA": s}, set(), events)
    assert not out, "breakdown must never be a trade signal"
    assert events["VOLHOLE_BREAKDOWN"] == 1, "…but it must be journaled"
