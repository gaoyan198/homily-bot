#!/usr/bin/env python3
"""
Danny-Cheng-style composite signal.
===================================

Combines three timeframes plus chip context into an accumulation call — the
way @dannycheng2022 uses Homily charts: signals time ADDS on conviction
names, never exits. There is deliberately no SELL state.

    monthly trend  : close > EMA10(monthly) and EMA10 rising
    weekly circle  : existing homily_clone 4-factor engine (unchanged)
    daily candle   : RED  = close > EMA10(daily) and MACD hist > 0
                     YELLOW = close < EMA10(daily) and MACD hist < 0
    chip context   : homily_chips profile (POC / support / resistance)

States:
    ACCUMULATE  monthly UP + weekly RED + price at/near a major chip-support
    HOLD        monthly UP + weekly RED, extended above support — wait
    PULLBACK    weekly AMBER while monthly UP — dip forming, watch support
    BOTTOMING   trend still broken BUT price broke out above a volatility
                hole formed in a downtrend — Danny's early bottoming signal
    CAUTION     weekly WHITE or monthly trend down — pause adds

The volatility hole ("the most crucial part" of Danny's analysis) upgrades
CAUTION to BOTTOMING on an upside breakout. A downside breakdown from a
topping hole is flagged as a note only — the event study
(homily_vol_backtest.py) shows breakdowns were followed by ABOVE-baseline
forward returns in these names, so it earns a warning, not a veto on adds.
"""
from dataclasses import dataclass
from homily_clone import ema, macd, homily_circle
from homily_chips import build_profile
from homily_data import weekly_closes, monthly_closes
from homily_vol import find_hole
from homily_whale import whale_read

NEAR_SUPPORT_PCT = 3.0   # "at support" = within 3% above the peak (or below it)


@dataclass
class DannySignal:
    ticker: str
    state: str          # ACCUMULATE / HOLD / PULLBACK / CAUTION
    monthly_up: bool
    weekly: object      # homily_clone.Signal
    candle: str         # RED / YELLOW / NEUTRAL
    chips: object       # homily_chips.ChipProfile
    add_zone: tuple     # (lo, hi) suggested accumulate zone, or None
    vol_hole: object    # homily_vol.VolHole or None
    whale: object       # homily_whale.WhaleRead
    note: str


def daily_candle(closes):
    e10 = ema(closes, 10)
    _, _, hist = macd(closes)
    if closes[-1] > e10[-1] and hist[-1] > 0:
        return "RED"
    if closes[-1] < e10[-1] and hist[-1] < 0:
        return "YELLOW"
    return "NEUTRAL"


def danny_signal(ticker, bars):
    dcloses = [b[4] for b in bars]
    wk, mo = weekly_closes(bars), monthly_closes(bars)
    weekly = homily_circle(ticker, wk)
    candle = daily_candle(dcloses)
    chips = build_profile(bars)

    e10m = ema(mo, 10)
    monthly_up = len(mo) >= 12 and mo[-1] > e10m[-1] and e10m[-1] > e10m[-2]

    last = dcloses[-1]
    add_zone, near_support = None, False
    if chips.support:
        s_price = chips.support[0][0]
        near_support = last <= s_price * (1 + NEAR_SUPPORT_PCT / 100)
        add_zone = (round(s_price * 0.98, 2), round(s_price * 1.03, 2))
    whale = whale_read(bars, chips.support[0][0] if chips.support else None)

    hole = find_hole(bars)
    # any upside resolution counts (Danny: "every volatility hole, once
    # surpassed, has triggered a strong subsequent rally") — the event study
    # edge holds without conditioning on the prior trend
    bottoming = hole is not None and hole.status == "BREAKOUT"
    topping = (hole is not None and hole.trend_before == "UP"
               and hole.status == "BREAKDOWN")

    if not monthly_up or weekly.circle == "WHITE":
        if bottoming:
            src = ("formed in the decline" if hole.trend_before == "DOWN"
                   else "formed in the recovery")
            state = "BOTTOMING"
            note = (f"broke ABOVE the {hole.lower:.0f}-{hole.upper:.0f} "
                    f"volatility hole {src} — early bottoming signal, watch "
                    "for the trend engines to confirm")
        else:
            state = "CAUTION"
            note = "trend broken — pause adds (long-term thesis review, not a sell call)"
    elif weekly.circle == "AMBER":
        state = "PULLBACK"
        note = "dip forming — stalk the chip-support zone"
    elif near_support:
        state = "ACCUMULATE"
        note = "price at major chip support with trend intact — Danny-style add zone"
    else:
        state = "HOLD"
        note = "trend intact but extended above support — wait for pullback"
    if topping:
        note += f" · ⚠ topping-process breakdown below {hole.lower:.0f}-{hole.upper:.0f}"
    if whale.whale and state in ("CAUTION", "PULLBACK"):
        note += " · 🐳 whale-accumulation footprint in the dip"
    return DannySignal(ticker, state, monthly_up, weekly, candle, chips,
                       add_zone, hole, whale, note)


if __name__ == "__main__":
    from homily_data import fetch_daily
    for sym in ("NVDA", "TSLA", "PLTR", "TSM"):
        s = danny_signal(sym, fetch_daily(sym, rng="5y"))
        z = f"{s.add_zone[0]:.0f}-{s.add_zone[1]:.0f}" if s.add_zone else "—"
        vh = (f"{s.vol_hole.lower:.0f}-{s.vol_hole.upper:.0f} {s.vol_hole.status}"
              if s.vol_hole else "—")
        print(f"{sym:<5} {s.state:<10} monthlyUp={s.monthly_up} "
              f"weekly={s.weekly.circle}/{s.weekly.score} candle={s.candle} "
              f"POC={s.chips.poc:.0f} zone={z} VH={vh}")
        print(f"      {s.note}")
