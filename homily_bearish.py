#!/usr/bin/env python3
"""
Short-term bearish-tells block (#102) — info-only, gates NOTHING.
=================================================================

The tells Danny reads before a correction were already computed here but
scattered across per-row suffixes (dY · state icon · VH↓ note); the owner's
2026-07-16 margin adds were placed with none of them consolidated in view.
This module folds the active ones into one dated ⚠️🐻 block over HELD names,
printed only on confluence (>= TELLS_MIN tells at once).

Tells (all read off the frozen DannySignal — no engine edit, no new signal):

    candle YELLOW   daily close < EMA10 with MACD hist < 0 (#101's column),
                    dated to the first day of the current YELLOW run
    wk AMBER/WHITE  the weekly circle has degraded (the state icon already
                    says so; here it is named next to its age)
    VH↓ topping     close below the lower boundary of a volatility hole
                    formed in an UPtrend, dated to the first close below

When #79's whale-distribution tag ships (its own gated session, QUEUED
behind R10), it joins this list; the block does not advance that queue.

Honesty (the measured nulls stay attached to the print): VH breakdowns ran
ABOVE-baseline forward in these names (homily_vol_backtest.py) and dip age
past p90 resolves FASTER (homily_pullback_backtest.py, #78) — so this block
is context for the owner's MANUAL/margin decisions, never a DCA change, a
sell call, or an input to the copilot. Pure function of already-fetched
inputs; no IO, no state (R3).
"""
from homily_danny import daily_candle

TELLS_MIN = 2    # one tell is tape noise; the block waits for confluence
LOOKBACK = 60    # how far back a tell's start date is chased (bars)


def _md(d):
    return f"{d.month}/{d.day}"


def yellow_since(bars, cap=LOOKBACK):
    """Date the current daily-YELLOW run began, or None if today isn't
    YELLOW. Recomputes daily_candle() on close *prefixes*: EMA/MACD are
    seeded from the series start, so the prefix state is exactly what that
    day's run printed — not an approximation."""
    closes = [b[4] for b in bars]
    if daily_candle(closes) != "YELLOW":
        return None
    start = len(bars) - 1
    for i in range(len(bars) - 2, max(len(bars) - 2 - cap, 0), -1):
        if daily_candle(closes[:i + 1]) != "YELLOW":
            break
        start = i
    return bars[start][0]


def breakdown_since(bars, lower, cap=LOOKBACK):
    """First day of the current run of closes below the hole's lower
    boundary (the VH↓ date). Falls back to the last bar if the whole
    lookback sat below — the date is then 'at least since'."""
    start = len(bars) - 1
    for i in range(len(bars) - 1, max(len(bars) - 1 - cap, -1), -1):
        if bars[i][4] < lower:
            start = i
        else:
            break
    return bars[start][0]


def tells(sig, bars=None):
    """Active short-term bearish tells for one DannySignal -> list of
    dated strings. Reads frozen outputs only; `bars` is optional and used
    solely to date the tell (a missing series drops the date, never the
    tell)."""
    out = []
    if sig.candle == "YELLOW":
        d = yellow_since(bars) if bars else None
        out.append(f"candle YELLOW since {_md(d)}" if d else "candle YELLOW")
    if sig.weekly.circle in ("AMBER", "WHITE"):
        out.append(f"wk {sig.weekly.circle} {sig.weekly.weeks_in_regime}w")
    h = sig.vol_hole
    if h and h.status == "BREAKDOWN" and h.trend_before == "UP":
        d = breakdown_since(bars, h.lower) if bars else None
        out.append(f"VH↓ topping{f' {_md(d)}' if d else ''}")
    return out


def block(sigs, all_bars, held, esc=lambda x: x):
    """The digest block, or "" when no held name has >= TELLS_MIN active
    tells. `sigs` is screen()'s (DannySignal, Conviction, young) list,
    `all_bars` the ticker->bars map the run already fetched, `held` the
    set of book tickers."""
    rows = []
    for s, _c, _y in sigs:
        if s.ticker not in held:
            continue
        t = tells(s, (all_bars or {}).get(s.ticker))
        if len(t) >= TELLS_MIN:
            rows.append(f"<code>{esc(f'{s.ticker:<5}')}</code> "
                        + " · ".join(esc(x) for x in t))
    if not rows:
        return ""
    return "\n".join(
        ["⚠️🐻 <b>SHORT-TERM BEARISH TELLS — info only, gates nothing</b>"]
        + rows
        + ["<i>the tells Danny reads before corrections, consolidated for"
           " manual/margin decisions only. Measured nulls stay attached:"
           " VH breakdowns ran above-baseline forward, long dips resolve"
           " faster — never a DCA change, a sell call, or a copilot"
           " input</i>"])
