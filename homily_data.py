#!/usr/bin/env python3
"""
Daily OHLCV fetch + weekly/monthly resample. Pure stdlib (urllib), key-free
Yahoo v8 chart API — same pattern as daily_run's weekly fetch, but daily bars
so the chip (cost-distribution) engine has volume-at-price to work with.
"""
import os, re, json, ssl, time, random, datetime, threading, urllib.request
import urllib.error

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

# #114 fetch failover chain. Yahoo is the reference tape; the chain below is
# consulted ONLY after Yahoo hard-fails for a symbol (every retry spent, or
# a response the parser rejects), in order, first source that serves wins,
# and the SOURCE is recorded per symbol so nothing downstream can mix tapes
# silently: `failover_note()` prints the line the day any name is not
# Yahoo, and daily_run writes NO verdict-feeding state that day (ledger,
# snapshot, refine-J, alerts, dashboard) — a row on a foreign tape is not
# a reference row (R1). The digest still sends (R4).
#   nasdaq  api.nasdaq.com historical — key-free, US-listed names only,
#           ~10y, split-adjusted OHLCV, NO dividend adjustment (adj = raw
#           close for these names that day)
#   vault   #113's committed Yahoo copy — any vaulted name, up to a month
#           STALE; freshness_note flags SPY, the source line names the rest
# Stooq (#60's second source) is NOT in the chain: since ≤2026-09 it serves
# a JavaScript proof-of-work challenge instead of CSV. Solving that would
# be anti-bot circumvention, so the source is retired (PRD §8.5) and #60's
# agreement check now compares today's Yahoo tape against the vault's.
# The breaker: BREAKER consecutive transport failures (timeouts, 5xx, 429,
# connection errors — never a 404 on a delisted name) mark Yahoo DOWN for
# the rest of the process, so a dead endpoint costs seconds, not 199 names
# × 3 retries × 20 s.
BREAKER = 5
NASDAQ_HOST = "api.nasdaq.com"
SOURCES = {}            # symbol -> (source, last bar date) when not Yahoo
_state = {"fails": 0, "down": False}
_lock = threading.Lock()


class YahooDown(Exception):
    """Breaker tripped: Yahoo declared dead for this process."""


def reset_breaker():
    """Per-process state; tests and the CLI call it explicitly."""
    with _lock:
        _state["fails"], _state["down"] = 0, False
    SOURCES.clear()


def _transport_failure(e):
    """A dead endpoint, not a dead symbol: 4xx other than 429 is the symbol's
    problem and must not count toward the breaker."""
    if isinstance(e, urllib.error.HTTPError):
        return e.code == 429 or e.code >= 500
    return True


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
    if _state["down"]:
        raise YahooDown(f"{symbol}: Yahoo breaker open")
    for attempt in range(RETRIES):
        host = HOSTS[attempt % len(HOSTS)]        # rotate query1 <-> query2
        url = (f"https://{host}/v8/finance/chart/{symbol}"
               f"?{span}&interval=1d")
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        try:
            with opener(req, timeout=20, context=ctx) as r:
                data = json.load(r)
            with _lock:
                _state["fails"] = 0
            return data
        except Exception as e:                    # noqa: BLE001 - retry any error
            last = e
            if attempt < RETRIES - 1:
                time.sleep(BACKOFF * (2 ** attempt) + random.uniform(0, JITTER))
    if _transport_failure(last):
        with _lock:
            _state["fails"] += 1
            if _state["fails"] >= BREAKER:
                _state["down"] = True
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
    # #113 restore path: HOMILY_BARS_SOURCE=vault serves the committed bars
    # vault instead of the network — same contract, same rng windows (cut
    # relative to the vault's as-of date). Nothing downstream can tell.
    if os.getenv("HOMILY_BARS_SOURCE", "").lower() == "vault":
        import homily_vault
        return homily_vault.read_series(symbol, rng)
    try:
        return _yahoo_series(symbol, rng, opener=opener)
    except Exception as primary:                  # noqa: BLE001 - hard failure
        for name, fn in FALLBACKS:
            try:
                bars, adj = fn(symbol, rng, opener=opener)
            except Exception:                     # noqa: BLE001 - next source
                continue
            if bars:
                SOURCES[symbol] = (name, bars[-1][0])
                return bars, adj
        raise primary


def _yahoo_series(symbol, rng, *, opener=urllib.request.urlopen):
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


# --- #114 fallback sources ---------------------------------------------------
_US = re.compile(r"^[A-Z]{1,5}$")


def _rng_years(rng):
    m = re.fullmatch(r"(\d+)(y|mo|d)", rng or "")
    if not m:
        return 10                                 # "max" → Nasdaq's ~10y
    n, u = int(m.group(1)), m.group(2)
    return {"y": n, "mo": n / 12, "d": n / 365}[u]


def nasdaq_series(symbol, rng="2y", *, opener=urllib.request.urlopen):
    """api.nasdaq.com historical -> (bars, adj) in the R1 contract. US
    listings only; adj IS the raw close (no dividend adjustment exists
    here — the source line says so). Tries the stock endpoint, then the
    ETF one. Raises on anything unusable, like every source."""
    if not _US.match(symbol):
        raise ValueError(f"{symbol}: not a US-listed symbol, no Nasdaq tape")
    years = max(1, int(_rng_years(rng) + 0.999))
    since = (datetime.date.today() - datetime.timedelta(days=365 * years))
    ctx = ssl.create_default_context()
    last = None
    for cls in ("stocks", "etf"):
        url = (f"https://{NASDAQ_HOST}/api/quote/{symbol}/historical"
               f"?assetclass={cls}&fromdate={since.isoformat()}&limit=9999")
        req = urllib.request.Request(url, headers={
            "User-Agent": "Mozilla/5.0", "Accept": "application/json"})
        try:
            with opener(req, timeout=20, context=ctx) as r:
                doc = json.load(r)
            rows = doc["data"]["tradesTable"]["rows"]
            if rows:
                break
        except Exception as e:                    # noqa: BLE001
            last = e
            rows = None
    if not rows:
        raise last or ValueError(f"{symbol}: Nasdaq returned no rows")
    num = lambda x: float(str(x).replace("$", "").replace(",", "").strip())
    bars = []
    for r in rows:                                # newest first on the wire
        try:
            m, d, y = r["date"].split("/")
            v = int(num(r["volume"])) if r.get("volume") not in (None, "", "N/A") else 0
            if not v:
                continue
            bars.append((datetime.date(int(y), int(m), int(d)), num(r["open"]),
                         num(r["high"]), num(r["low"]), num(r["close"]), v))
        except (KeyError, ValueError):
            continue
    bars.sort(key=lambda b: b[0])
    if not bars:
        raise ValueError(f"{symbol}: Nasdaq rows unparseable")
    return bars, [b[4] for b in bars]


def vault_series(symbol, rng="2y", *, opener=None):
    """#113's committed copy — the terminal fallback. Stale by up to a
    month; the caller's source line carries the as-of date."""
    import homily_vault
    return homily_vault.read_series(symbol, rng)


def vault_daily(symbol):
    """[(date, close)] from the vault, for agreement_note — #60's second
    opinion now that Stooq is gone: today's Yahoo tape vs our own frozen
    copy of Yahoo's tape catches a silent rewrite on the day."""
    bars, _ = vault_series(symbol, "max")
    return [(b[0], b[4]) for b in bars]


FALLBACKS = (("nasdaq", nasdaq_series), ("vault", vault_series))


def failover_note(today=None, sources=None, bars_by_symbol=None,
                  vault_daily=vault_daily):
    """The digest line for a day any name was not served by Yahoo — one
    line, counts + names + what it means, plus #60's agreement check run
    against the vault for every name a LIVE alternate served (a vault-
    served name has nothing independent to check against). -> str or ''."""
    src = SOURCES if sources is None else sources
    if not src:
        return ""
    today = today or datetime.date.today()
    by = {}
    for sym, (name, asof) in sorted(src.items()):
        by.setdefault(name, []).append((sym, asof))
    parts = []
    if "nasdaq" in by:
        names = [s for s, _ in by["nasdaq"]]
        parts.append(f"Nasdaq served {len(names)} ({', '.join(names[:8])}"
                     f"{'…' if len(names) > 8 else ''}) — adj = raw close "
                     "for these today, RS12 on dividend payers is raw")
    if "vault" in by:
        names = [s for s, _ in by["vault"]]
        oldest = min(a for _, a in by["vault"])
        parts.append(f"vault served {len(names)} ({', '.join(names[:8])}"
                     f"{'…' if len(names) > 8 else ''}) — STALE, as-of "
                     f"{oldest.isoformat()}: levels/signals on those names "
                     "are that old")
    ok, bad = 0, []
    for sym, _ in by.get("nasdaq", []):
        bars = (bars_by_symbol or {}).get(sym)
        if not bars:
            continue
        try:
            n = agreement_note(bars, vault_daily(sym), symbol=sym)
        except Exception:                         # noqa: BLE001 - not vaulted
            continue
        if n:
            bad.append(n.split(" — ")[0])
        else:
            ok += 1
    if ok or bad:
        parts.append(f"agreement vs the vault's Yahoo tape: {ok} OK"
                     + (f", {len(bad)} DISAGREE ({'; '.join(bad[:3])})"
                        if bad else ""))
    return ("📡 SOURCE: Yahoo failed for "
            f"{len(src)} name{'s' if len(src) != 1 else ''} this run — "
            + "; ".join(parts) + ". No ledger/snapshot/refine/alert state "
            "written today (a foreign tape is not a reference row)")


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
    callers treat this whole probe as optional.
    RETIRED 2026-09-11 (#114): Stooq now answers with a JavaScript proof-of-
    work challenge, not CSV, so this has raised on every call for weeks and
    the #60 line silently stopped. Kept as the parser of record (validate
    [60]) and for the day the CSV comes back; nothing calls it live."""
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
