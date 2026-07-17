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
    # rng="max" via the range token silently DOWNGRADES granularity (Yahoo
    # returns 1mo bars while honouring interval=1d for shorter tokens) —
    # found 2026-07-10 when D-63 Step 2 ran signals on monthly bars. Epoch
    # period params keep true daily bars for the full listing history.
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
    """-> (bars, adj): the R1 6-tuple bars AND a parallel adjusted-close list.

    `bars` are RAW (split-adjusted, non-dividend) prices — the contract every
    chip/level/whale engine depends on; a level must be a price you could have
    traded at. `adj[i]` is the dividend-adjusted close for `bars[i]`, same
    index, same length: the series ALL return math must use (#18), because raw
    closes make every dividend payer look permanently behind a zero-div growth
    name. One HTTP pull feeds both — Yahoo already returns adjclose alongside
    quote. Names without an adjclose block (or with a null in it) fall back to
    the raw close, i.e. to the pre-#18 behaviour.
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
        bars.append((datetime.date.fromtimestamp(t), o, h, l, c, v))
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
    bars = fetch_daily("NVDA")
    print(f"NVDA: {len(bars)} daily bars, "
          f"{len(weekly_closes(bars))} weekly, {len(monthly_closes(bars))} monthly")
    print("last bar:", bars[-1])


# --- #60 · data-QA cross-checks (feeds #17's hardening) ----------------------
# Two cheap honesty probes on the tape the whole system runs on. Pure
# functions + one optional second-source fetch; every consumer treats a
# note as a WARNING line, never a halt (R4: the digest always sends).
def freshness_note(bars, today, symbol="SPY", max_weekdays=3):
    """A tape whose last bar is older than `max_weekdays` weekdays is stale
    (holiday + weekend fits inside 3) — the digest would be advising on old
    prices without saying so. -> note string or ""."""
    if not bars:
        return f"{symbol}: no bars at all"
    last, gap, d = bars[-1][0], 0, bars[-1][0]
    while d < today:
        d += datetime.timedelta(days=1)
        if d.weekday() < 5:
            gap += 1
    if gap > max_weekdays:
        return (f"{symbol}: last bar {last.isoformat()} is {gap} weekdays old "
                "— tape may be stale, levels/signals are as-of that date")
    return ""


def stooq_daily(symbol, *, opener=urllib.request.urlopen):
    """Second-source daily closes from Stooq (CSV, key-free) -> [(date,
    close)]. US symbols only ('SPY' -> 'spy.us'). Raises on any problem —
    callers treat this whole probe as optional."""
    url = f"https://stooq.com/q/d/l/?s={symbol.lower()}.us&i=d"
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    with opener(req, timeout=20) as r:
        text = r.read().decode()
    out = []
    for ln in text.strip().split("\n")[1:]:
        parts = ln.split(",")
        if len(parts) < 5 or not parts[4]:
            continue
        try:                          # anti-bot/challenge pages parse as
            out.append((datetime.date.fromisoformat(parts[0]),
                        float(parts[4])))
        except ValueError:            # garbage -> zero rows -> clean raise
            continue
    if not out:
        raise ValueError(f"stooq: no usable rows for {symbol}")
    return out


def agreement_note(bars, second, symbol="SPY", tol=0.01):
    """Compare the most recent COMMON date's close across sources; relative
    disagreement > tol earns a note (a silently mis-adjusted primary tape
    poisons every level downstream — #19's lesson, checked daily on the
    benchmark). -> note string or ""."""
    ours = {b[0]: b[4] for b in bars}
    theirs = dict(second)
    common = sorted(set(ours) & set(theirs))
    if not common:
        return f"{symbol}: no common dates with the second source"
    d = common[-1]
    a, b = ours[d], theirs[d]
    if abs(a - b) / b > tol:
        return (f"{symbol} {d.isoformat()}: Yahoo {a:g} vs Stooq {b:g} "
                f"({(a / b - 1) * 100:+.1f}%) — sources disagree, treat "
                "levels with suspicion")
    return ""
