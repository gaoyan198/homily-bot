#!/usr/bin/env python3
"""
Corporate-action sanity check (backlog #19).
===========================================

A mis-adjusted split is the quietest way this system prints nonsense. The chip
histogram spreads every bar's volume across its high-low range and decays it
with a 60-day half-life, so one un-adjusted 10:1 gap sitting in the window
drags the POC, the support shelf and the add zone for *weeks* — and every row
looks perfectly normal while it does.

There is no key-free corporate-actions feed, so the detector reads the bars
themselves: a one-day move past `MOVE_PCT` on abnormal volume is either a
mis-adjustment or a genuine event large enough that the cost basis of every
holder just changed. Both mean the same thing here — the chip levels are not
tradeable prices today. The digest suspends the levels and keeps the state row
(`daily_run.fmt_row`); nothing upstream is touched, and no engine is frozen out
of its own behaviour.

Deliberately conservative: a real +50% takeover pop suspends levels too. The
cost of that false positive is one day of missing numbers; the cost of a false
negative is a month of add zones pointing at prices that never existed.

Pure stdlib, no network. Gate: homily_validate.py check [24] (synthetic 10:1).
"""
import statistics

MOVE_PCT = 45.0     # |1-day close-to-close move| that no normal tape prints
VOL_MULT = 3.0      # ...on volume this far off its own trailing median
VOL_WINDOW = 20     # trailing bars the median volume is taken over
LOOKBACK = 120      # ~2 chip half-lives: older bars can't move the histogram


def _abnormal(vol, med):
    """A split mis-adjustment moves volume as hard as it moves price, and the
    direction tells you which kind. A 10:1 forward split leaves the volume
    multiplied ~10x against unadjusted prices (spike); a 1:10 reverse split
    divides it (collapse). The plan (#19) named only the spike — the collapse
    is the same event seen from the other side, so both count."""
    if med <= 0:
        return False
    return vol >= VOL_MULT * med or vol * VOL_MULT <= med


def corp_action_bar(bars, *, lookback=LOOKBACK, move_pct=MOVE_PCT):
    """-> date of the most recent suspect bar within `lookback`, else None.

    bars: the R1 6-tuples (date,o,h,l,c,v), oldest first.
    """
    hit = None
    for i in range(max(1, len(bars) - lookback), len(bars)):
        prev_close, close, vol = bars[i - 1][4], bars[i][4], bars[i][5]
        if prev_close <= 0:
            continue
        if abs(close / prev_close - 1) * 100.0 < move_pct:
            continue
        window = [b[5] for b in bars[max(0, i - VOL_WINDOW):i]]
        if window and _abnormal(vol, statistics.median(window)):
            hit = bars[i][0]
    return hit


def suspended_note(day):
    return f"⚠️ levels suspended — corporate action? ({day})"


if __name__ == "__main__":
    from homily_data import fetch_daily
    for sym in ("NVDA", "GOOGL", "AAPL"):
        print(f"{sym:<6} {corp_action_bar(fetch_daily(sym, rng='2y')) or 'clean'}")
