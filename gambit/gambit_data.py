#!/usr/bin/env python3
"""
GAMBIT data layer — daily OHLCV fetch + weekly/monthly resample.

Copied (never imported) from homily-bot's homily_data.py per EXECUTION §0.5,
tests ported alongside. Pure stdlib (urllib), key-free Yahoo v8 chart API.

Bars contract (the R1 rule this repo inherits):
  fetch_series(sym) -> (bars, adj)
  bars = raw (split-adjusted, non-dividend) 6-tuples (date, o, h, l, c, v),
         oldest first — a level must be a price you could have traded at.
  adj  = dividend-adjusted closes, same index, same length — ALL return math
         uses this series; falls back to the raw close when Yahoo omits it.

Date discipline (homily R7 / DESIGNS D-G7): every bar date is the US exchange
SESSION date derived from the bar timestamp in America/New_York — never the
local machine's timezone, never now(). session_date() is the one helper; it
is pinned by test before any journal row exists.
"""
import json, ssl, time, random, datetime, urllib.request
from zoneinfo import ZoneInfo

# #17 fetch hardening: rotate the two Yahoo chart hosts and retry with
# exponential backoff + jitter, so a transient 5xx / rate-limit blip doesn't
# blank a name. Backoff constants are module-level so tests can zero them.
HOSTS = ("query1.finance.yahoo.com", "query2.finance.yahoo.com")
RETRIES = 3
BACKOFF = 0.5      # seconds, doubled each retry
JITTER = 0.4       # seconds, uniform random added on top

US_MARKET_TZ = ZoneInfo("America/New_York")


def session_date(ts):
    """US exchange session date for a Yahoo bar timestamp (epoch seconds).

    Yahoo stamps daily bars at the session open (14:30/13:30 UTC); converting
    in America/New_York yields the trading date regardless of where this code
    runs (the R7 TZ-drift bug class: local fromtimestamp() shifts dates for
    anyone east of UTC-5).
    """
    return datetime.datetime.fromtimestamp(ts, tz=US_MARKET_TZ).date()


def _fetch_json(symbol, rng, *, opener=urllib.request.urlopen):
    """One chart-API pull with host rotation + backoff/jitter retry. Raises the
    last error if every attempt fails. `opener` is injectable for testing."""
    ctx = ssl.create_default_context()
    last = None
    # rng="max" via the range token silently DOWNGRADES granularity (Yahoo
    # returns 1mo bars while honouring interval=1d for shorter tokens) —
    # homily validate [22], found 2026-07-10. Epoch period params keep true
    # daily bars for the full listing history.
    span = (f"period1=0&period2={int(time.time())}" if rng == "max"
            else f"range={rng}")
    for attempt in range(RETRIES):
        host = HOSTS[attempt % len(HOSTS)]        # rotate query1 <-> query2
        url = (f"https://{host}/v8/finance/chart/{symbol}"
               f"?{span}&interval=1d")
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        try:
            with opener(req, timeout=20, context=ctx) as r:
                return json.load(r)
        except Exception as e:                    # noqa: BLE001 - retry any error
            last = e
            if attempt < RETRIES - 1:
                time.sleep(BACKOFF * (2 ** attempt) + random.uniform(0, JITTER))
    raise last


def fetch_series(symbol, rng="2y", *, opener=urllib.request.urlopen):
    """-> (bars, adj) per the module docstring's bars contract.

    Refuses any response whose meta granularity isn't 1d — Yahoo degrades
    long ranges to monthly bars while still claiming daily in the request
    (the validate-[22] bug class); coarse data must never feed a signal.
    """
    data = _fetch_json(symbol, rng, opener=opener)
    res = data["chart"]["result"][0]
    gran = (res.get("meta") or {}).get("dataGranularity")
    if gran and gran != "1d":
        raise ValueError(f"{symbol}: Yahoo returned {gran} bars, not 1d"
                         f" (rng={rng}) — refusing coarse data")
    ts = res["timestamp"]
    q = res["indicators"]["quote"][0]
    ac = ((res["indicators"].get("adjclose") or [{}])[0]).get("adjclose") or []
    bars, adj = [], []
    for i, t in enumerate(ts):
        o, h, l, c, v = (q["open"][i], q["high"][i], q["low"][i],
                         q["close"][i], q["volume"][i])
        if None in (o, h, l, c) or not v:
            continue  # skip half-formed / zero-volume rows (holidays, today)
        a = ac[i] if i < len(ac) and ac[i] is not None else c
        bars.append((session_date(t), o, h, l, c, v))
        adj.append(a)
    return bars, adj


def fetch_daily(symbol, rng="2y", *, opener=urllib.request.urlopen):
    """-> list of (date, open, high, low, close, volume), oldest first."""
    return fetch_series(symbol, rng, opener=opener)[0]


def fetch_adj(symbol, rng="2y", *, opener=urllib.request.urlopen):
    """-> list of dividend-adjusted closes, aligned to fetch_daily()'s bars."""
    return fetch_series(symbol, rng, opener=opener)[1]


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
    bars = fetch_daily("QQQ")
    print(f"QQQ: {len(bars)} daily bars, "
          f"{len(weekly_closes(bars))} weekly, {len(monthly_closes(bars))} monthly")
    print("last bar:", bars[-1])
