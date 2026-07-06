#!/usr/bin/env python3
"""
Volatility-hole event study — the honest check for Danny's claim.
=================================================================

Claim under test (his SPY monthly post): "every volatility hole, once
surpassed, has triggered a strong subsequent rally."

Design (no look-ahead): walk each 5y daily series; an EVENT fires on the
first close above the upper boundary (breakout) or below the lower boundary
(breakdown) of a hole detected using only data up to that day. Measure
forward 20d and 60d returns from the event close and compare with the
unconditional forward returns of every day in the same series. One event max
per hole (re-arming only when a new hole forms).
"""
from homily_data import fetch_daily
from homily_vol import find_hole, REF_WIN, VOL_WIN

TICKERS = ["NVDA", "TSLA", "TSM", "PLTR", "CSPX.L", "AAPL", "GOOG", "AMD"]
FWD = (20, 60)
WARMUP = REF_WIN + VOL_WIN + 5


def events(bars):
    out, armed_zone = [], None
    for i in range(WARMUP, len(bars) - 1):
        h = find_hole(bars[:i + 1])
        if h is None:
            continue
        zone = (round(h.lower, 4), round(h.upper, 4))
        if h.status == "INSIDE":
            armed_zone = zone            # a hole is live and unresolved
        elif zone == armed_zone:         # first resolution of the armed hole
            out.append((i, h.status, h.trend_before))
            armed_zone = None
    return out


def fwd_ret(closes, i, n):
    if i + n >= len(closes):
        return None
    return closes[i + n] / closes[i] - 1


if __name__ == "__main__":
    ev_rets = {("BREAKOUT", n): [] for n in FWD}
    ev_rets.update({("BREAKDOWN", n): [] for n in FWD})
    base = {n: [] for n in FWD}
    n_ev = {"BREAKOUT": 0, "BREAKDOWN": 0}
    for sym in TICKERS:
        bars = fetch_daily(sym, rng="5y")
        closes = [b[4] for b in bars]
        for i in range(WARMUP, len(closes)):
            for n in FWD:
                r = fwd_ret(closes, i, n)
                if r is not None:
                    base[n].append(r)
        for i, status, trend in events(bars):
            n_ev[status] += 1
            for n in FWD:
                r = fwd_ret(closes, i, n)
                if r is not None:
                    ev_rets[(status, n)].append(r)

    avg = lambda xs: sum(xs) / len(xs) if xs else float("nan")
    win = lambda xs: 100 * sum(x > 0 for x in xs) / len(xs) if xs else float("nan")
    print(f"Volatility-hole event study — {len(TICKERS)} names, 5y daily "
          f"({n_ev['BREAKOUT']} breakouts, {n_ev['BREAKDOWN']} breakdowns)")
    print(f"{'event':<12}{'fwd':>5}{'avg ret':>9}{'win%':>7}{'baseline':>10}{'base win%':>10}")
    print("-" * 55)
    for status in ("BREAKOUT", "BREAKDOWN"):
        for n in FWD:
            xs = ev_rets[(status, n)]
            print(f"{status:<12}{n:>4}d{avg(xs)*100:>8.1f}%{win(xs):>6.0f}%"
                  f"{avg(base[n])*100:>9.1f}%{win(base[n]):>9.0f}%")
    print("-" * 55)
    print("baseline = unconditional forward return of every day, same names.")
    print("Danny's claim holds only if BREAKOUT rows beat baseline clearly.")
