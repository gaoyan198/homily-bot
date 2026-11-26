#!/usr/bin/env python3
"""
⤴ breakout tag (#105 ship) — whale-confirmed shelf-break, info-only.
====================================================================

The live mirror of `homily_breakout_backtest.py`'s PASSED event
(BACKTEST_RESULTS §23): today printed the FIRST close above the nearest
major overhead chip shelf, with the 🐳 footprint active somewhere in the
last 10 sessions. Same point-in-time convention as the study — the
reference for day i is the PRIOR day's profile (`build_profile` through
i-1), because the same-day profile reclassifies a broken shelf as
support before the row could ever tag it.

Measured honesty, attached here because the tag inherits it: the edge
is a 60d phenomenon (+1.2pt over DCA in universe A, +1.5pt in the 2021
control) with a SHALLOWER control drawdown than the ⭐-dip entry — but
there is NO edge at 20d in the control (the tag runs a month early) and
none left by 120d in universe A. The shelf-break without 🐳 was never
tested and does not tag. Info-only: discretionary context in the ≤2%
WHALE-DIP spirit at most; it gates nothing, feeds nothing downstream,
and any money-flow use needs its own R10 slot (PRD §5l).

Pure function of the bars it is given — no IO, no state (R3). Cost:
two chip profiles per name per run; the whale probes only run on the
rare cross day.
"""
from homily_chips import build_profile
from homily_whale import whale_read

WHALE_LOOK = 10          # 🐳 must have fired within this many sessions
MIN_BARS = 320


def _r0(bars_prefix):
    p = build_profile(bars_prefix)
    return p.resistance[0][0] if p.resistance else None


def breakout_today(bars):
    """True iff the LAST bar is a whale-confirmed shelf-break event day."""
    if not bars or len(bars) < MIN_BARS:
        return False
    ref_today = _r0(bars[:-1])
    ref_prev = _r0(bars[:-2])
    if ref_today is None or ref_prev is None:
        return False
    if not (bars[-1][4] > ref_today and bars[-2][4] <= ref_prev):
        return False
    last = len(bars) - 1
    for j in range(last, max(last - WHALE_LOOK, 0) - 1, -1):
        pre = bars[:j + 1]
        p = build_profile(pre)
        sh = p.support[0][0] if p.support else None
        if whale_read(pre, sh).whale:
            return True
    return False
