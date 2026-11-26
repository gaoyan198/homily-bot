"""Vol-hole port tests — homily validate [9] ported with the module, plus
the D-G3b parsimony fixture: the same bars must produce exactly ONE cluster
and ONE breakout (the detector must not spray signals)."""
import datetime

import gambit_vol as gv


def vbars(specs):
    """specs: list of (price, range) -> daily bars with that H-L range."""
    d0 = datetime.date(2024, 1, 1)
    return [(d0 + datetime.timedelta(days=i), p, p + r, p - r, p, 1e6)
            for i, (p, r) in enumerate(specs)]


DECLINE = [(200 - i, 4.0) for i in range(80)]        # volatile downtrend
QUIET = [(120, 0.3)] * 10                            # volatility hole


def test_hole_found_after_decline_zone_tight():
    vh = gv.find_hole(vbars(DECLINE + QUIET))
    assert vh is not None and vh.trend_before == "DOWN"
    assert vh.status == "INSIDE"
    assert vh.lower >= 119 and vh.upper <= 121.5


def test_upside_resolution_is_breakout():
    brk = gv.find_hole(vbars(DECLINE + QUIET + [(125, 2.0)] * 3))
    assert brk is not None and brk.status == "BREAKOUT"


def test_downside_resolution_is_breakdown():
    dn = gv.find_hole(vbars(DECLINE + QUIET + [(112, 2.0)] * 3))
    assert dn is not None and dn.status == "BREAKDOWN"


def test_too_short_series_returns_none():
    assert gv.find_hole(vbars(DECLINE[:30])) is None


def test_stale_hole_expires():
    # strictly RISING relative volatility after the hole (falling price,
    # constant range): no new hole days form, and after MAX_AGE bars the
    # old zone is no longer in force
    later = [(125 - 0.05 * i, 6.0) for i in range(gv.MAX_AGE + 5)]
    assert gv.find_hole(vbars(DECLINE + QUIET + later)) is None


def test_parsimony_one_cluster_one_breakout():
    # D-G3b fixture: walking the whole tape day by day, the detector must
    # yield exactly ONE zone (cluster id) and its BREAKOUT status must first
    # appear exactly once — no signal spray.
    bars = vbars(DECLINE + QUIET + [(125, 2.0)] * 15)
    holes = gv.hole_days(bars)
    zones, breakout_first_seen = set(), []
    prev_status = {}
    for i in range(len(bars)):
        h = gv.find_hole_at(bars, i, holes)
        if h is None:
            continue
        zones.add(h.cluster_start)      # stable id while the cluster grows
        if (h.status == "BREAKOUT"
                and prev_status.get(h.cluster_start) != "BREAKOUT"):
            breakout_first_seen.append(i)
        prev_status[h.cluster_start] = h.status
    assert len(zones) == 1, f"expected one cluster, got {len(zones)}"
    assert len(breakout_first_seen) == 1, \
        f"breakout must trigger once, got {len(breakout_first_seen)}"


def test_find_hole_at_is_point_in_time():
    # the zone visible at bar i must not change when future bars are added
    full = vbars(DECLINE + QUIET + [(125, 2.0)] * 3)
    trunc = full[:len(DECLINE) + len(QUIET)]
    h_full = gv.find_hole_at(full, len(trunc) - 1, gv.hole_days(full))
    h_trunc = gv.find_hole_at(trunc, len(trunc) - 1, gv.hole_days(trunc))
    assert h_full is not None and h_trunc is not None
    assert (h_full.upper, h_full.lower, h_full.status) == \
        (h_trunc.upper, h_trunc.lower, h_trunc.status)
