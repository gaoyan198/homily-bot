#!/usr/bin/env python3
"""
Provisional-bar mark (#106) — "to be finalized", display-only.
==============================================================

Danny annotates higher-timeframe charts "to be finalized" until the bar
closes. Our trend engines deliberately include the in-progress bar (R1:
the signal math is frozen and keeps doing so); the measured cost of
presenting that read as settled (homily_provisional_backtest.py, 5y,
both universes, 54,072 day-name obs): the mid-period `monthly_up` later
disagreed with its settled month on 9.9% of days — two-thirds of that
inside the month's first 10 sessions — the weekly circle on 4.2%, and
7.5% of days printed a digest STATE CLASS the completed bar would
contradict. Past the 2% pre-committed materiality bar → this mark.

`marks(bars)` says which trend engines are reading an unfinished bar
RIGHT NOW, from point-in-time facts only:

    "m"  the last bar sits in the first PROV_M_SESSIONS sessions of its
         month (counted from the name's own bars — HK/US calendars
         differ), where 66% of the measured monthly divergence lives
    "w"  the last bar is a Mon–Thu print, so the weekly bar almost
         surely extends next session (a Friday-holiday week escapes the
         mark; accepted and documented, the mark is info-only)

Rendered as a `…` on the digest's existing mUP/mDN and wk tokens, wired
through a defaulting kwarg — goldens and the state machine byte-identical
with the mark off. Zero engine edit; nothing downstream reads it.
"""

PROV_M_SESSIONS = 10


def marks(bars):
    """-> subset of 'mw' for the engines whose deciding bar is unfinished."""
    if not bars:
        return ""
    last = bars[-1][0]
    ym = (last.year, last.month)
    sessions = sum(1 for b in bars[-31:] if (b[0].year, b[0].month) == ym)
    out = "m" if sessions <= PROV_M_SESSIONS else ""
    if last.isoweekday() < 5:
        out += "w"
    return out
