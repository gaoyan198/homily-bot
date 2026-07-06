#!/usr/bin/env python3
"""
Daily OHLCV fetch + weekly/monthly resample. Pure stdlib (urllib), key-free
Yahoo v8 chart API — same pattern as daily_run's weekly fetch, but daily bars
so the chip (cost-distribution) engine has volume-at-price to work with.
"""
import json, ssl, datetime, urllib.request


def fetch_daily(symbol, rng="2y"):
    """-> list of (date, open, high, low, close, volume), oldest first."""
    url = (f"https://query1.finance.yahoo.com/v8/finance/chart/{symbol}"
           f"?range={rng}&interval=1d")
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    ctx = ssl.create_default_context()
    with urllib.request.urlopen(req, timeout=20, context=ctx) as r:
        data = json.load(r)
    res = data["chart"]["result"][0]
    ts = res["timestamp"]
    q = res["indicators"]["quote"][0]
    bars = []
    for i, t in enumerate(ts):
        o, h, l, c, v = (q["open"][i], q["high"][i], q["low"][i],
                         q["close"][i], q["volume"][i])
        if None in (o, h, l, c) or not v:
            continue  # skip half-formed / zero-volume rows (holidays, today)
        bars.append((datetime.date.fromtimestamp(t), o, h, l, c, v))
    return bars


def resample(bars, key):
    """Aggregate daily bars into weekly/monthly closes by a date->bucket key."""
    out, cur, close = [], None, None
    for d, o, h, l, c, v in bars:
        k = key(d)
        if k != cur:
            if cur is not None:
                out.append(close)
            cur = k
        close = c
    if cur is not None:
        out.append(close)
    return out


def weekly_closes(bars):
    return resample(bars, lambda d: d.isocalendar()[:2])


def monthly_closes(bars):
    return resample(bars, lambda d: (d.year, d.month))


if __name__ == "__main__":
    bars = fetch_daily("NVDA")
    print(f"NVDA: {len(bars)} daily bars, "
          f"{len(weekly_closes(bars))} weekly, {len(monthly_closes(bars))} monthly")
    print("last bar:", bars[-1])
