#!/usr/bin/env python3
"""
Daily OHLCV fetch + weekly/monthly resample. Pure stdlib (urllib), key-free
Yahoo v8 chart API — same pattern as daily_run's weekly fetch, but daily bars
so the chip (cost-distribution) engine has volume-at-price to work with.
"""
import json, ssl, time, random, datetime, urllib.request

# #17 fetch hardening: rotate the two Yahoo chart hosts and retry with
# exponential backoff + jitter, so a transient 5xx / rate-limit blip doesn't
# blank a name (and a whole digest). The BARS CONTRACT IS UNCHANGED (R1):
# still raw (split-adjusted, non-dividend) 6-tuples (date,o,h,l,c,v); only the
# transport around it changed. Backoff constants are module-level so the
# flaky-fetch validate test can zero them.
HOSTS = ("query1.finance.yahoo.com", "query2.finance.yahoo.com")
RETRIES = 3
BACKOFF = 0.5      # seconds, doubled each retry
JITTER = 0.4       # seconds, uniform random added on top


def _fetch_json(symbol, rng, *, opener=urllib.request.urlopen):
    """One chart-API pull with host rotation + backoff/jitter retry. Raises the
    last error if every attempt fails. `opener` is injectable for testing."""
    ctx = ssl.create_default_context()
    last = None
    for attempt in range(RETRIES):
        host = HOSTS[attempt % len(HOSTS)]        # rotate query1 <-> query2
        url = (f"https://{host}/v8/finance/chart/{symbol}"
               f"?range={rng}&interval=1d")
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        try:
            with opener(req, timeout=20, context=ctx) as r:
                return json.load(r)
        except Exception as e:                    # noqa: BLE001 - retry any error
            last = e
            if attempt < RETRIES - 1:
                time.sleep(BACKOFF * (2 ** attempt) + random.uniform(0, JITTER))
    raise last


def fetch_daily(symbol, rng="2y", *, opener=urllib.request.urlopen):
    """-> list of (date, open, high, low, close, volume), oldest first."""
    data = _fetch_json(symbol, rng, opener=opener)
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
