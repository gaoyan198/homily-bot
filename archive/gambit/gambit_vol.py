#!/usr/bin/env python3
"""
Volatility hole detector — copied (never imported) from homily_vol.py per
EXECUTION §0.5; tests ported alongside. S3's setup input (DESIGNS D-G3b).

A "hole" day is a new REF_WIN-day low in relative volatility (5-day average
true range / close). Consecutive hole days (gaps <= MAX_GAP) form a cluster;
the zone is that cluster's high/low, valid until closed through on either
side. Homily's §5b event study (the reason S3 exists, Amendment A1):
closes ABOVE the upper bound preceded strength (+11.5% vs +8.5% baseline
fwd 60d); closes BELOW did NOT predict weakness — breakdowns are journal-
only warnings, never trade signals.

GAMBIT addition for walk-forward use: hole_days() precomputes the hole-day
indices once per series (each depends only on trailing data — no look-
ahead), so the backtest can ask "zone in force as of bar i?" cheaply via
find_hole_at().
"""
from dataclasses import dataclass

VOL_WIN = 5      # ATR window for the volatility series
REF_WIN = 60     # a hole = new low in relvol vs this many trailing days
MAX_GAP = 3      # hole days this close together belong to one cluster
MAX_AGE = 90     # only a hole formed within this many bars is "in force"


@dataclass
class VolHole:
    upper: float
    lower: float
    age: int          # bars since the cluster ended
    status: str       # BREAKOUT / BREAKDOWN / INSIDE
    trend_before: str  # DOWN -> bottoming process, UP -> topping process
    cluster_start: int = -1  # first hole day — STABLE zone identity while
    cluster_end: int = -1    # the cluster grows; end = last hole day


def _relvol(bars):
    trs, out = [], []
    for i, (d, o, h, l, c, v) in enumerate(bars):
        pc = bars[i - 1][4] if i else c
        trs.append(max(h, pc) - min(l, pc))
        w = trs[-VOL_WIN:]
        out.append(sum(w) / len(w) / c)
    return out


def hole_days(bars, ref_win=REF_WIN):
    """All hole-day indices for the series (point-in-time safe: day i uses
    only rv[i-ref_win:i])."""
    rv = _relvol(bars)
    return [i for i in range(ref_win, len(bars))
            if rv[i] <= min(rv[i - ref_win:i])]


def _cluster_ending_before(holes, upto):
    """Latest cluster among hole days <= upto (gap rule), or None."""
    import bisect
    j = bisect.bisect_right(holes, upto) - 1
    if j < 0:
        return None
    cluster = [holes[j]]
    for k in range(j - 1, -1, -1):
        if cluster[0] - holes[k] <= MAX_GAP:
            cluster.insert(0, holes[k])
        else:
            break
    return cluster


def find_hole_at(bars, i, holes, max_age=MAX_AGE):
    """Zone in force as of bar index i (uses bars[:i+1] only), or None.
    `holes` is the precomputed hole_days(bars) list."""
    if i < REF_WIN + VOL_WIN + 4:
        return None
    cluster = _cluster_ending_before(holes, i)
    if not cluster:
        return None
    age = i - cluster[-1]
    if age > max_age:
        return None
    upper = max(bars[k][2] for k in cluster)
    lower = min(bars[k][3] for k in cluster)
    last = bars[i][4]
    status = ("BREAKOUT" if last > upper else
              "BREAKDOWN" if last < lower else "INSIDE")
    look = max(0, cluster[0] - 20)
    trend_before = "DOWN" if bars[cluster[0]][4] < bars[look][4] else "UP"
    return VolHole(upper, lower, age, status, trend_before,
                   cluster[0], cluster[-1])


def find_hole(bars, ref_win=REF_WIN, max_age=MAX_AGE):
    """Latest volatility hole still in force, or None (homily-compatible)."""
    if len(bars) < ref_win + VOL_WIN + 5:
        return None
    return find_hole_at(bars, len(bars) - 1, hole_days(bars, ref_win),
                        max_age)


if __name__ == "__main__":
    from gambit_data import fetch_daily
    for sym in ("PLTR", "TSLA", "NVDA"):
        h = find_hole(fetch_daily(sym, rng="2y"))
        if h is None:
            print(f"{sym:<8} no volatility hole in force")
            continue
        proc = "bottoming" if h.trend_before == "DOWN" else "topping"
        print(f"{sym:<8} zone {h.lower:.2f}-{h.upper:.2f}  {h.status:<9} "
              f"age {h.age}d  ({proc} process)")
