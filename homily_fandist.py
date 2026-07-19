#!/usr/bin/env python3
"""
Conditional forward-distribution card (#103) — a FAN, never a path.
===================================================================

Owner ask: "tell stories from charts about the most likely path". The
honest version prints the measured point-in-time forward DISTRIBUTION
for the name's current state-confluence — median with p25/p75 and p10
alongside, so the downside is never below the fold. HOW_TO_READ §7
stays law: no price targets, no measured moves, no single-path arrows.

The confluence KEY is pre-registered (PRD #103) to kill combinatorial
cherry-picking: exactly (state, 🐳 bool, 🎯 bool, VH status), nothing
else, and ONE function (`conf_key`) computes it for both the study
index (`homily_fandist_backtest.py`, which emits `fandist.json`) and
the live board card (`homily_dashboard`) — R6 pattern, no
reimplementation. Distributions are pooled over BOTH universes on
prefix bars; cells with n < MIN_N print "insufficient history" instead
of a number; the construction-date caveat prints on the card.

Info-only: gates nothing, changes no engine, feeds nothing downstream.
"""
import json
import os

MIN_N = 30
HORIZONS = ("20", "60", "120")

_PATH = os.path.join(os.path.dirname(__file__), "fandist.json")
try:
    _RAW = json.load(open(_PATH))
except Exception:                     # missing/corrupt file -> no chips, no crash
    _RAW = {}
FAN = {k: v for k, v in _RAW.items() if not k.startswith("_")}
META = _RAW.get("_meta", {})


def conf_key(state, whale, at_support, vh_status):
    """THE pre-registered confluence key — the only dimensions there are."""
    return (f"{state}|{'W' if whale else '·'}|{'T' if at_support else '·'}"
            f"|{vh_status or '—'}")


def sig_key(sig):
    """Key from a live DannySignal (the study's adapter). 🎯 is exactly the
    digest's flag: a non-⭐ name whose close reached the add zone."""
    at = (sig.state != "ACCUMULATE" and sig.add_zone is not None
          and sig.chips.last <= sig.add_zone[1])
    return conf_key(sig.state, bool(sig.whale.whale), at,
                    sig.vol_hole.status if sig.vol_hole else None)


def row_key(s):
    """Key from a snapshot row (the board's adapter) — same primitives."""
    at = (s["state"] != "ACCUMULATE" and s.get("zone_lo") is not None
          and s["close"] <= s["zone_hi"])
    return conf_key(s["state"], bool(s.get("whale")), at, s.get("vh_status"))


def _pct(x):
    return f"{x * 100:+.0f}%"


def fan_chips(key, fan=None, meta=None):
    """-> list of card-chip strings for this confluence, or [] when the
    table is absent. Median + p25/p75 + p10 side by side, n always shown."""
    fan = FAN if fan is None else fan
    meta = META if meta is None else meta
    if not fan:
        return []
    cell = fan.get(key)
    if not cell:
        return [f"fan: no history for this confluence"]
    out = []
    for h in HORIZONS:
        n, p10, p25, p50, p75 = cell[h]
        if n < MIN_N:
            out.append(f"fan{h}: insufficient history (n={n})")
        else:
            out.append(f"fan{h} med {_pct(p50)} · p25 {_pct(p25)} / "
                       f"p75 {_pct(p75)} · p10 {_pct(p10)} · n={n}")
    out.append(f"fan = measured distribution, not a forecast "
               f"({meta.get('protocol', 'point-in-time replay')}, "
               f"built {meta.get('built', '?')})")
    return out
