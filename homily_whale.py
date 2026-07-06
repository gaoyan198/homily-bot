#!/usr/bin/env python3
"""
Whale-accumulation read (main-force absorption approximation).
==============================================================

PRD backlog #12, born from the PLTR June-2026 case: Danny added aggressively
at the 113-119 chip shelf during the June 22-26 dip to 106 while the bot said
⚪ CAUTION — the LEVEL agreed, the trend gate blocked the add, and that
week's bounce proved him right. Homily's "main force" (主力) line claims to
track institutional cost; that input is proprietary, so this approximates
the observable footprint big buyers leave in public OHLCV while a dip is
being absorbed:

  1. absorption days — heavy-volume down days that close well off their lows
     (sellers hit bids all day, someone bigger took every share);
  2. flow divergence — OBV or the accumulation/distribution line holds or
     rises from the pre-dip peak while price falls (money in, price down);
  3. shelf stability — the decayed chip weight of the support band price
     sits on has NOT decayed over the last two weeks: fresh volume is
     replenishing the shelf at the same prices (holders absorbing, not
     fleeing).

The 🐳 tag needs an actual dip (close >= DIP_PCT below the DIP_WIN-day
closing high) plus at least 2 of the 3 footprints. Pure stdlib, no
look-ahead: uses only the bars it is given.
"""
from dataclasses import dataclass

DIP_WIN = 60        # dip reference window, trading days
DIP_PCT = 5.0       # close this % below the window's closing high = a dip
ABSORB_WIN = 15     # hunt for absorption days in this recent window
VOL_MULT = 1.3      # heavy volume = this x the trailing 50d average
CLOSE_POS = 0.5     # close must land in the upper half of the day's range
FLOOR_PCT = 3.0     # day's low within this % of the 20d min low = "probing"
MIN_ABSORB = 1      # one clean absorption print is the Danny pattern
SHELF_LOOK = 10     # compare shelf weight now vs this many bars ago
SHELF_BAND = 0.02   # +/-2% band around the shelf peak
HALF_LIFE = 60      # same chip decay as homily_chips


@dataclass
class WhaleRead:
    whale: bool          # in a dip + >= 2 of the 3 footprints
    in_dip: bool
    absorb_days: int
    absorption: bool     # check 1
    divergence: bool     # check 2
    shelf_stable: bool   # check 3


def _adl_obv(bars):
    """Cumulative accumulation/distribution line and OBV over the bars."""
    adl = obv = 0.0
    adls, obvs = [], []
    for i, (d, o, h, l, c, v) in enumerate(bars):
        rng = h - l
        adl += v * (((c - l) - (h - c)) / rng if rng else 0.0)
        if i:
            pc = bars[i - 1][4]
            obv += v if c > pc else -v if c < pc else 0.0
        adls.append(adl)
        obvs.append(obv)
    return adls, obvs


def _band_weight(bars, lo, hi, half_life=HALF_LIFE):
    """Decayed volume weight landing in [lo, hi], uniform over each H-L."""
    decay = 0.5 ** (1.0 / half_life)
    n, w = len(bars), 0.0
    for idx, (d, o, h, l, c, v) in enumerate(bars):
        if h <= l:
            frac = 1.0 if lo <= c <= hi else 0.0
        else:
            frac = max(0.0, min(h, hi) - max(l, lo)) / (h - l)
        if frac:
            w += v * frac * decay ** (n - 1 - idx)
    return w


def whale_read(bars, shelf):
    """bars: [(date,o,h,l,c,v)] oldest-first; shelf: nearest chip-support
    peak price (homily_chips support[0]) or None."""
    if len(bars) < DIP_WIN + SHELF_LOOK + 5:
        return WhaleRead(False, False, 0, False, False, False)
    closes = [b[4] for b in bars]
    last = closes[-1]

    win = closes[-DIP_WIN:]
    peak_rel = max(range(len(win)), key=lambda j: win[j])
    in_dip = last <= win[peak_rel] * (1 - DIP_PCT / 100)

    # 1. heavy-volume days probing the dip's floor that close well off it
    # (PLTR 2026-06-26: opened near the capitulation low, 1.4x volume,
    # closed at 0.8 of the range — the print that proved Danny right)
    n_abs = 0
    for i in range(len(bars) - ABSORB_WIN, len(bars)):
        d, o, h, l, c, v = bars[i]
        prior = bars[max(0, i - 50):i]
        avg_v = sum(b[5] for b in prior) / len(prior)
        rng = h - l
        floor = min(b[3] for b in bars[max(0, i - 19):i + 1])
        if (v >= VOL_MULT * avg_v and l <= floor * (1 + FLOOR_PCT / 100)
                and rng > 0 and (c - l) / rng >= CLOSE_POS):
            n_abs += 1
    absorption = n_abs >= MIN_ABSORB

    # 2. money flowed IN from the pre-dip peak while price fell
    adls, obvs = _adl_obv(bars[-DIP_WIN:])
    divergence = in_dip and (adls[-1] >= adls[peak_rel]
                             or obvs[-1] >= obvs[peak_rel])

    # 3. shelf weight replenished (not decaying) while price sits on it
    shelf_stable = False
    if shelf and shelf * 0.90 <= last <= shelf * 1.03:
        lo, hi = shelf * (1 - SHELF_BAND), shelf * (1 + SHELF_BAND)
        w_now = _band_weight(bars, lo, hi)
        w_then = _band_weight(bars[:-SHELF_LOOK], lo, hi)
        # with zero fresh volume w_now = w_then * 0.5^(10/60) ~= 0.89*w_then;
        # holding the full weight means fresh volume >= the decay loss
        shelf_stable = w_then > 0 and w_now >= w_then

    whale = in_dip and (absorption + divergence + shelf_stable) >= 2
    return WhaleRead(whale, in_dip, n_abs, absorption, divergence,
                     shelf_stable)


if __name__ == "__main__":
    # replay THE case: PLTR June 22-26 2026 dip to ~106 on the 113-119 shelf
    import datetime
    from homily_data import fetch_daily
    from homily_danny import danny_signal
    bars = fetch_daily("PLTR", rng="5y")
    print("PLTR point-in-time replay around the June-2026 dip:")
    print(f"{'date':<12}{'close':>8}  {'state':<10} {'dip':<4}"
          f"{'absorb':>7}{'flow':>6}{'shelf':>7}{'  🐳':<4}")
    for i, b in enumerate(bars):
        if not (datetime.date(2026, 6, 15) <= b[0] <= datetime.date(2026, 7, 6)):
            continue
        s = danny_signal("PLTR", bars[:i + 1])
        w = s.whale
        print(f"{b[0]!s:<12}{b[4]:>8.2f}  {s.state:<10} "
              f"{'Y' if w.in_dip else '·':<4}{w.absorb_days:>5}d"
              f"{'  ↗' if w.divergence else '  ·':>6}"
              f"{'hold' if w.shelf_stable else '·':>7}"
              f"{'  🐳' if w.whale else ''}")
