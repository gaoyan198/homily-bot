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

    whale-dist +     #79, SHIPPED 2026-11-26 — HELD SATELLITES ONLY (never
    monthly LH/LL    Bucket A or an owner-set Bucket-B earned-core name: PRD
                     scope guard verbatim). Today is a rally day (≥5% over
                     the 60d closing low) carrying ≥2 of the 3 distribution
                     footprints AND the last two completed months printed
                     lower highs and lower lows — the sharp variant of
                     BACKTEST_RESULTS §10 (n=178, fwd120 −0.3% vs +19.6%
                     baseline). Computed by the PASSED study's own
                     `homily_dist_backtest` functions (R6: never restated);
                     validate [93] pins live == study day-for-day.
                     Honesty: the effect is carried by the 2021-wreck
                     universe; on the hindsight winners' universe the plain
                     tag was NOT predictive. The 🚀-candidacy veto half of
                     #79 is a behaviour change and stays queued (R10).

Honesty (the measured nulls stay attached to the print): VH breakdowns ran
ABOVE-baseline forward in these names (homily_vol_backtest.py) and dip age
past p90 resolves FASTER (homily_pullback_backtest.py, #78) — so this block
is context for the owner's MANUAL/margin decisions, never a DCA change, a
sell call, or an input to the copilot. Pure function of already-fetched
inputs; no IO, no state (R3).
"""
from homily_danny import daily_candle
import homily_dist_backtest as _dist   # #79: the PASSED study's own detector

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


def distribution_mlhll(bars):
    """#79 live tag: True iff the LAST bar is one of the study's
    `tagged + monthly LH/LL` days — the exact `homily_dist_backtest.scan`
    test applied to the final bar (rally context → monthly LH/LL → ≥2 of
    {prints, negative flow, shelf erosion}, the shelf only probed on the
    1-of-2 boundary, as the study does). Needs more than the study's
    WARMUP bars; fewer -> False (the study never tagged a warm-up day)."""
    if not bars or len(bars) <= _dist.WARMUP:
        return False
    closes = [b[4] for b in bars]
    if closes[-1] < min(closes[-_dist.DIP_WIN:]) * (1 + _dist.DIP_PCT / 100):
        return False                       # not in rally context
    if not _dist.monthly_lhll(bars):
        return False                       # cheap gate before the probes
    prints, neg_flow, _ = _dist.dist_footprints(bars, need_shelf=False)
    score = prints + neg_flow
    if score == 1:
        _, _, eroding = _dist.dist_footprints(bars, need_shelf=True)
        score += bool(eroding)
    return score >= 2


DIST_TELL = "whale-dist + monthly LH/LL"


def tells(sig, bars=None, satellite=False):
    """Active short-term bearish tells for one DannySignal -> list of
    dated strings. Reads frozen outputs only; `bars` is optional and used
    solely to date the tell (a missing series drops the date, never the
    tell) — except #79's distribution tell, which IS a bar computation and
    is evaluated only when `satellite` (the scope guard) and bars exist."""
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
    if satellite and bars and distribution_mlhll(bars):
        out.append(DIST_TELL)
    return out


def block(sigs, all_bars, held, esc=lambda x: x, satellites=frozenset()):
    """The digest block, or "" when no held name has >= TELLS_MIN active
    tells. `sigs` is screen()'s (DannySignal, Conviction, young) list,
    `all_bars` the ticker->bars map the run already fetched, `held` the
    set of book tickers, `satellites` the held names #79's distribution
    tell may reach (default empty: the tell is off unless the caller
    applies the scope guard)."""
    rows = []
    for s, _c, _y in sigs:
        if s.ticker not in held:
            continue
        t = tells(s, (all_bars or {}).get(s.ticker),
                  satellite=s.ticker in satellites)
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
           " faster; whale-dist (satellites only) measured weak forward"
           " mainly on the 2021-wreck names — never a DCA change, a sell"
           " call, or a copilot input</i>"])
