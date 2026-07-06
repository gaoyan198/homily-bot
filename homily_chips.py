#!/usr/bin/env python3
"""
Chip / cost-distribution engine (筹码分布 approximation).
========================================================

Danny Cheng's "proprietary chip system" and Homily's momentum bars are both
volume-at-price constructs: horizontal bars showing where volume (i.e. holder
cost basis) is concentrated. Heavy bars below price act as support (holders in
profit defend their basis); heavy bars above act as resistance (trapped
holders sell into rallies).

Approximation here: each day's volume is spread triangularly across that day's
high-low range (peak at the midpoint), and past days are decayed exponentially
with a 60-trading-day half-life so recent accumulation dominates — the
"dynamic POC" behaviour Danny describes. True chip models decay by turnover
rate against float; float isn't available key-free, so a fixed half-life is
the transparent stand-in.

Outputs per ticker: POC, top chip peaks below price (support) and above
(resistance), and % of chips in profit. Pure stdlib.
"""
from dataclasses import dataclass

HALF_LIFE = 60   # trading days for old chips to lose half their weight
NBINS = 120


@dataclass
class ChipProfile:
    poc: float                 # heaviest bin price (point of control)
    support: list              # [(price, rel_weight)] peaks below last close
    resistance: list           # [(price, rel_weight)] peaks above last close
    pct_in_profit: float       # % of chip weight below last close
    last: float


def build_profile(bars, nbins=NBINS, half_life=HALF_LIFE):
    """bars: [(date,o,h,l,c,v)] oldest-first. Uses closes/H-L/volume only."""
    lo = min(b[3] for b in bars)
    hi = max(b[2] for b in bars)
    if hi <= lo:
        hi = lo * 1.001
    width = (hi - lo) / nbins
    weights = [0.0] * nbins
    decay = 0.5 ** (1.0 / half_life)
    n = len(bars)
    for idx, (d, o, h, l, c, v) in enumerate(bars):
        w = v * (decay ** (n - 1 - idx))
        b_lo = int((l - lo) / width)
        b_hi = int((h - lo) / width)
        b_lo = max(0, min(nbins - 1, b_lo))
        b_hi = max(0, min(nbins - 1, b_hi))
        span = b_hi - b_lo + 1
        if span == 1:
            weights[b_lo] += w
            continue
        # triangular: weight peaks at the middle of the day's range
        mid = (b_lo + b_hi) / 2.0
        tri = [1.0 - abs(j - mid) / (span / 2.0 + 1e-9) + 0.1
               for j in range(b_lo, b_hi + 1)]
        tsum = sum(tri)
        for j, t in zip(range(b_lo, b_hi + 1), tri):
            weights[j] += w * t / tsum

    total = sum(weights) or 1.0
    price_of = lambda j: lo + (j + 0.5) * width
    last = bars[-1][4]

    poc = price_of(max(range(nbins), key=lambda j: weights[j]))
    pct_in_profit = 100.0 * sum(w for j, w in enumerate(weights)
                                if price_of(j) <= last) / total

    # local maxima = chip peaks ("momentum bars")
    peaks = []
    for j in range(nbins):
        wl = weights[j - 1] if j > 0 else 0.0
        wr = weights[j + 1] if j < nbins - 1 else 0.0
        if weights[j] >= wl and weights[j] >= wr and weights[j] > 0:
            peaks.append((price_of(j), weights[j] / max(weights)))
    peaks.sort(key=lambda p: -p[1])
    # keep the strongest, then de-duplicate peaks closer than 2% apart
    kept = []
    for p, w in peaks:
        if all(abs(p / q - 1) > 0.02 for q, _ in kept):
            kept.append((p, w))
        if len(kept) >= 8:
            break
    # a shelf within one bin of the close is where price *sits* -> support
    near = max(width, last * 0.005)
    support = sorted([p for p in kept if p[0] <= last + near],
                     key=lambda p: -p[0])[:2]
    resistance = sorted([p for p in kept if p[0] > last + near],
                        key=lambda p: p[0])[:2]
    return ChipProfile(poc, support, resistance, pct_in_profit, last)


if __name__ == "__main__":
    from homily_data import fetch_daily
    for sym in ("NVDA", "TSLA", "PLTR"):
        p = build_profile(fetch_daily(sym))
        fmt = lambda ps: ", ".join(f"{x:.0f}({w:.0%})" for x, w in ps) or "—"
        print(f"{sym:<5} last {p.last:8.2f}  POC {p.poc:8.2f}  "
              f"in-profit {p.pct_in_profit:4.0f}%  "
              f"support: {fmt(p.support)}  resistance: {fmt(p.resistance)}")
