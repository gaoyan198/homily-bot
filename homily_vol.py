#!/usr/bin/env python3
"""
Volatility hole (Danny Cheng's reversal-process indicator).
===========================================================

Danny calls this "the most crucial and important part of my technical
analysis": a spot where volatility collapses to an extreme low, printed on
the chart as a ZONE with an upper and lower boundary. His documented rules:

  * it appears during temporary bottoming (after declines) or topping
    (after rallies) processes — candles alone flip too easily to be trusted;
  * the zone "remains valid until invalidated by either side";
  * a close ABOVE the upper boundary has preceded strong rallies ("every
    volatility hole, once surpassed, has triggered a strong subsequent
    rally" — his SPY monthly study); a close BELOW the lower boundary is the
    bearish invalidation.

Approximation (his exact construction is proprietary, like the chip system):
a "hole" day is a new REF_WIN-day low in relative volatility (5-day average
true range / close). Consecutive hole days (gaps <= 3) form a cluster; the
zone is that cluster's high/low. Status is judged from the latest close.
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
    trend_before: str # DOWN -> bottoming process, UP -> topping process


def _relvol(bars):
    trs, out = [], []
    for i, (d, o, h, l, c, v) in enumerate(bars):
        pc = bars[i - 1][4] if i else c
        trs.append(max(h, pc) - min(l, pc))
        w = trs[-VOL_WIN:]
        out.append(sum(w) / len(w) / c)
    return out

def find_hole(bars, ref_win=REF_WIN, max_age=MAX_AGE):
    """Latest volatility hole still in force, or None."""
    if len(bars) < ref_win + VOL_WIN + 5:
        return None
    rv = _relvol(bars)
    hole_days = [i for i in range(ref_win, len(bars))
                 if rv[i] <= min(rv[i - ref_win:i])]
    if not hole_days:
        return None
    # latest cluster of hole days
    cluster = [hole_days[-1]]
    for i in reversed(hole_days[:-1]):
        if cluster[0] - i <= MAX_GAP:
            cluster.insert(0, i)
        else:
            break
    age = len(bars) - 1 - cluster[-1]
    if age > max_age:
        return None
    upper = max(bars[i][2] for i in cluster)
    lower = min(bars[i][3] for i in cluster)
    last = bars[-1][4]
    status = ("BREAKOUT" if last > upper else
              "BREAKDOWN" if last < lower else "INSIDE")
    # what the hole is resolving: price into the cluster from above = decline
    # -> bottoming process; from below = rally -> topping process
    look = max(0, cluster[0] - 20)
    trend_before = "DOWN" if bars[cluster[0]][4] < bars[look][4] else "UP"
    return VolHole(upper, lower, age, status, trend_before)


if __name__ == "__main__":
    from homily_data import fetch_daily
    for sym in ("PLTR", "TSLA", "NVDA", "BABA", "9992.HK"):
        h = find_hole(fetch_daily(sym, rng="2y"))
        if h is None:
            print(f"{sym:<8} no volatility hole in force")
            continue
        proc = "bottoming" if h.trend_before == "DOWN" else "topping"
        print(f"{sym:<8} zone {h.lower:.2f}-{h.upper:.2f}  {h.status:<9} "
              f"age {h.age}d  ({proc} process)")
