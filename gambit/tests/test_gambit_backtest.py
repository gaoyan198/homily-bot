"""G-S3 gate tests: accounting hand-checks, cost model, no-margin, T+1 open
fills, point-in-time eligibility, and seed-reproducible random bands."""
import datetime
import math

import gambit_backtest as bt


def make_series(closes, *, start=datetime.date(2020, 1, 6), volume=1_000_000,
                opens=None):
    """Weekday tape: open defaults to prior close (so T+1-open fills differ
    from decision-day closes when the tape gaps)."""
    bars, d, prev = [], start, closes[0]
    i = 0
    while i < len(closes):
        if d.weekday() < 5:
            c = closes[i]
            o = opens[i] if opens else prev
            bars.append((d, o, max(o, c), min(o, c), c, volume))
            prev = c
            i += 1
        d += datetime.timedelta(days=1)
    return bt.Series(bars)


def test_cost_model_round_trip():
    pf = bt.Portfolio(20_000, cost_side=0.00125)
    pf.buy("X", 100.0, 20_000)
    pf.sell("X", 100.0)
    assert math.isclose(pf.cash, 20_000 * (1 - 0.00125) ** 2)
    assert pf.pos == {}


def test_no_margin_buy_clipped_to_cash():
    pf = bt.Portfolio(1_000)
    pf.buy("X", 10.0, 5_000)          # wants $5k, has $1k
    assert pf.cash == 0.0 and pf.cash >= 0
    assert math.isclose(pf.pos["X"], 1_000 * (1 - bt.COST_SIDE) / 10.0)


def test_buy_hold_moic_hand_check():
    # 100 -> 200 tape, entry at first open (=100): MOIC = 2 * (1-c), exactly
    s = make_series([100.0] * 10 + [200.0] * 10)
    cal = [d for d in s.dates]
    curve = bt.run_buy_hold(s, cal)
    p = bt.perf(curve)
    assert math.isclose(p["moic"], 2 * (1 - bt.COST_SIDE), rel_tol=1e-12)
    assert p["maxdd"] == 0.0


def test_perf_maxdd_and_mar():
    d0 = datetime.date(2020, 1, 6)
    curve = [(d0 + datetime.timedelta(days=i), eq) for i, eq in
             enumerate([20_000, 24_000, 18_000, 30_000])]
    p = bt.perf(curve)
    assert math.isclose(p["maxdd"], 18_000 / 24_000 - 1)
    assert p["moic"] == 1.5 and p["mar"] > 0


def test_fill_at_next_open_not_decision_close():
    # decision at Friday close (100); Monday opens gapped to 110 — the fill
    # must pay 110, not 100 (gaps taken in full, no fiction)
    closes = [100.0] * 5 + [110.0] * 5
    opens = [100.0] * 5 + [110.0] * 5
    s = make_series(closes, opens=opens, volume=10_000_000)
    series = {"AAA": s}
    cal = s.dates
    bounds = [cal[4]]                          # decide on the 5th session
    curve = bt.run_rotation(series, cal, lambda d, e: ["AAA"], bounds)
    qty = 20_000 * (1 - bt.COST_SIDE) / 110.0  # filled at Monday's open
    assert math.isclose(curve[-1][1], qty * 110.0, rel_tol=1e-9)


def test_point_in_time_eligibility():
    good = make_series([50.0] * 100, volume=1_000_000)   # $50M/day
    cheap = make_series([9.0] * 100, volume=90_000_000)
    thin = make_series([50.0] * 100, volume=100_000)     # $5M/day
    d = good.dates[50]
    assert good.eligible_at(d)
    assert not cheap.eligible_at(d)
    assert not thin.eligible_at(d)
    # too young: fewer than MIN_BARS bars before the date
    assert not good.eligible_at(good.dates[10])
    # and no history at all -> simply not eligible yet (Part II rule 1)
    assert not good.eligible_at(good.dates[0] - datetime.timedelta(days=9))


def test_adjust_bars_scales_opens_too():
    bars = [(datetime.date(2020, 1, 6), 100.0, 105.0, 95.0, 100.0, 1000)]
    out = bt.adjust_bars(bars, [90.0])         # dividend-adjusted close
    d, o, h, l, c, v = out[0]
    assert c == 90.0 and math.isclose(o, 90.0) and math.isclose(h, 94.5)
    assert v == 1000


def _toy_universe(n=12, days=300):
    series = {}
    for k in range(n):
        drift = 1.0 + 0.0005 * (k - n // 2)   # spread of trends
        closes = [50.0 * drift ** i for i in range(days)]
        series[f"S{k:02d}"] = make_series(closes, volume=5_000_000)
    return series


def test_random_band_reproducible_under_fixed_seed():
    series = _toy_universe()
    cal = series["S00"].dates
    a = bt.run_random_draws(series, cal, n_draws=40, seed_base=bt.SEED_BASE)
    b = bt.run_random_draws(series, cal, n_draws=40, seed_base=bt.SEED_BASE)
    assert a == b, "same seed must give a bit-identical band"
    c = bt.run_random_draws(series, cal, n_draws=40, seed_base=999)
    assert a != c, "a different seed must actually change the draws"
    p10, p50, p90 = bt.band(a)
    assert p10 <= p50 <= p90


def test_equal_weight_rotation_conserves_value_flat_tape():
    # flat tape, EW monthly: equity should only ever bleed costs, never grow
    series = {f"F{k}": make_series([40.0] * 260, volume=5_000_000)
              for k in range(4)}
    cal = series["F0"].dates
    curve = bt.run_rotation(series, cal, lambda d, e: e,
                            bt.month_boundaries(cal))
    p = bt.perf(curve)
    assert 0.985 < p["moic"] <= 1.0, f"flat EW should ~hold value, {p['moic']}"


def test_windows_shape_registered():
    assert len(bt.WINDOWS) == 9
    assert bt.WINDOWS[0][:2] == (datetime.date(2015, 1, 1),
                                 datetime.date(2020, 1, 1))
    assert [w for w in bt.WINDOWS if w[2] == "10y"] == [
        (datetime.date(2015, 1, 1), datetime.date(2025, 1, 1), "10y"),
        (datetime.date(2016, 1, 1), datetime.date(2026, 1, 1), "10y")]
    assert (bt.COST_SIDE, bt.STRESS_SIDE) == (0.00125, 0.00175)
    assert (bt.N_DRAWS, bt.DRAW_SIZE, bt.SEED_BASE) == (200, 5, 20260710)
