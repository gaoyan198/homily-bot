#!/usr/bin/env python3
"""
#147 — THE CRYPTO CYCLE SLEEVE: how much leverage survives, and what actually
accumulates BTC.  (BACKTEST_RESULTS §41)

Owner question (2026-08-20), verbatim in substance: "use IBIT and ETHA as proxy
to work out the optimum DCA strategy so I can capture this entire bull cycle,
and work out how much leverage is safe … I am thinking DCA 2k at 3x leverage
for each asset … when will I be liquidated if ever."  Refined mid-session to:
venue is **Hyperliquid perps** (not IBKR margin), max 3x considered, and the
objective is **BTC UNITS accumulated**, not USD MOIC, because the owner holds
zero BTC after the 2026-08 reset and believes in a $1M long-run BTC.

────────────────────────────────────────────────────────────────────────────
RULES FROZEN BEFORE THE FIRST FETCH (Part-III discipline)
────────────────────────────────────────────────────────────────────────────
R1  Objective = BTC UNITS held at the end of the accumulation window, per
    dollar contributed.  USD MOIC is reported but is NOT the verdict metric:
    a strategy that ends with more dollars and fewer coins LOSES.
R2  Liquidation is tested on the daily LOW, never the close.  A margin call is
    an intraday event.
R3  Perp maintenance margin = (1 / maxLeverage) / 2, read LIVE from the
    Hyperliquid `meta` endpoint (BTC 40x -> 1.25%, ETH 25x -> 2.00%).
R4  Funding is charged on NOTIONAL, not on borrowings, from real 8h history.
    This is the mechanism no prior leverage study here has modelled (§15/§39
    both assume a broker margin loan, which charges only the borrowed part).
R5  Hyperliquid market-closes the FULL position on liquidation, so a hit is a
    wipe of the whole accumulated stack, not a partial trim.  Modelled as such.
R6  The cycle-timing estimator is scored OUT OF SAMPLE: each trough is
    projected using only the peak->trough gaps of PRIOR cycles.
R7  PASS for "leverage belongs in the sleeve" requires the levered arm to beat
    unlevered SPOT on UNITS in BOTH accumulation-phase analogs.  One win and
    one wipe is a FAIL, not a coin flip to be re-shopped.

FROZEN CHRONOLOGY (public, checkable, written before any run):
    halvings  2012-11-28 · 2016-07-09 · 2020-05-11 · 2024-04-19
    peaks     2013-11-30 · 2017-12-17 · 2021-11-10 · 2025-10-06
    troughs   2015-01-14 · 2018-12-15 · 2022-11-21 · (open)

DATA
    spot daily OHLC   Yahoo v8 via homily_data.fetch_series (repo standard)
    funding 8h        Binance fapi fundingRate, 2019-09 -> live.  Used as the
                      long-history proxy because Hyperliquid launched 2023;
                      validated against HL's own fundingHistory (Part C).
    margins           Hyperliquid /info meta, live.

CAVEATS THAT MUST TRAVEL WITH ANY QUOTE OF THESE NUMBERS
  * Two completed accumulation-phase analogs only (c2, c3).  n=2.  Every
    "median"/"mean" here is a statement about two paths.
  * The 2013-11 peak predates the Yahoo BTC series (2014-09), so the first
    peak->trough drawdown is quoted from the chronology, not measured here.
  * Funding before 2019-09 is unmeasured; the model charges the 0.01%/8h
    baseline there.  Pre-2019 results are therefore OPTIMISTIC.
  * Binance funding != Hyperliquid funding.  Part C measures the gap on the
    overlapping window and reports it rather than assuming it away.
"""
import json, ssl, sys, time, datetime, urllib.request, statistics, os

HERE = os.path.dirname(os.path.abspath(__file__))
CACHE = os.path.join(HERE, "homily_cryptocycle_cache.json")
D = datetime.date.fromisoformat

HALVINGS = ["2012-11-28", "2016-07-09", "2020-05-11", "2024-04-19"]
PEAKS    = ["2013-11-30", "2017-12-17", "2021-11-10", "2025-10-06"]
TROUGHS  = ["2015-01-14", "2018-12-15", "2022-11-21"]
TAKER    = 0.00045          # Hyperliquid taker fee
BASE_8H  = 0.0001           # 0.01% per 8h baseline where funding is unmeasured


# ─────────────────────────── data ────────────────────────────
def _load_cache():
    if os.path.exists(CACHE):
        try:    return json.load(open(CACHE))
        except Exception: pass
    return {}


def _save_cache(c):
    json.dump(c, open(CACHE, "w"))


def spot(cache, sym):
    """Daily OHLC via the repo's standard key-free Yahoo fetcher."""
    if sym in cache.get("spot", {}):
        return [(D(r[0]), r[1], r[2], r[3], r[4]) for r in cache["spot"][sym]]
    sys.path.insert(0, HERE)
    import homily_data as hd
    bars, _ = hd.fetch_series(sym, rng="max")
    rows = [[str(b[0]), b[1], b[2], b[3], b[4]] for b in bars]
    cache.setdefault("spot", {})[sym] = rows
    _save_cache(cache)
    return [(D(r[0]), r[1], r[2], r[3], r[4]) for r in rows]


def funding(cache, sym):
    """Binance 8h funding history -> {date: summed_rate_that_day}."""
    if sym in cache.get("funding", {}):
        return {D(k): v for k, v in cache["funding"][sym].items()}
    ctx = ssl.create_default_context()
    rows, start = [], int(datetime.datetime(2019, 1, 1).timestamp() * 1000)
    while True:
        url = (f"https://fapi.binance.com/fapi/v1/fundingRate?symbol={sym}"
               f"&startTime={start}&limit=1000")
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=25, context=ctx) as r:
            b = json.load(r)
        if not b:
            break
        rows += [(x["fundingTime"], float(x["fundingRate"])) for x in b]
        if len(b) < 1000:
            break
        start = b[-1]["fundingTime"] + 1
        time.sleep(0.25)
    agg = {}
    for t, r in rows:
        d = datetime.datetime.fromtimestamp(t / 1000, datetime.UTC).date()
        agg[d] = agg.get(d, 0.0) + r
    cache.setdefault("funding", {})[sym] = {str(k): v for k, v in agg.items()}
    _save_cache(cache)
    return agg


def hl_margins(cache):
    """Live Hyperliquid max leverage -> maintenance margin = (1/maxLev)/2."""
    if "hl" in cache:
        return cache["hl"]
    ctx = ssl.create_default_context()
    req = urllib.request.Request(
        "https://api.hyperliquid.xyz/info", data=json.dumps({"type": "meta"}).encode(),
        headers={"Content-Type": "application/json", "User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req, timeout=25, context=ctx) as r:
        meta = json.load(r)
    out = {a["name"]: {"maxLeverage": a["maxLeverage"],
                       "mm": (1.0 / a["maxLeverage"]) / 2.0}
           for a in meta["universe"] if a["name"] in ("BTC", "ETH")}
    cache["hl"] = out
    _save_cache(cache)
    return out


# ──────────────────────── perp engine ────────────────────────
def run_perp(bars, fund, start, end, contrib, L, mm, mode="const"):
    """Levered perp DCA.  AV(p) = coll + sz*(p-entry); liquidation when
    AV < mm*sz*p, i.e. at p_liq = (sz*entry - coll) / (sz*(1-mm)) (R2, R5)."""
    w = [b for b in bars if start <= b[0] <= end]
    coll = sz = entry = 0.0
    invested = fees = paid = 0.0
    liqs, seen = [], set()
    fstart = min(fund) if fund else None
    for dt, o, h, lo, c in w:
        key = (dt.year, dt.month)
        if key not in seen:                       # monthly contribution
            seen.add(key); invested += contrib; coll += contrib
            av = coll + sz * (o - entry)
            if mode == "const":
                if av > 0:
                    tsz = (L * av) / o
                    tr = tsz - sz
                    f = abs(tr) * o * TAKER; fees += f; coll -= f
                    if tr < 0:  coll += (-tr) * (o - entry)
                    else:       entry = (sz * entry + tr * o) / tsz if tsz else o
                    sz = tsz
                else:
                    sz = entry = 0.0
            else:                                  # 'entry': never trim
                tr = (contrib * L) / o
                f = tr * o * TAKER; fees += f; coll -= f
                entry = (sz * entry + tr * o) / (sz + tr); sz += tr
        rate = fund.get(dt, BASE_8H * 3 if (fstart and dt < fstart) else 0.0)
        cost = sz * c * rate; paid += cost; coll -= cost
        if sz > 0:                                 # R2: test the LOW
            pliq = (sz * entry - coll) / (sz * (1 - mm))
            if lo <= pliq:                         # R5: full close
                coll += sz * (pliq - entry)
                liqs.append((dt, pliq)); sz = entry = 0.0
                if coll < 0: coll = 0.0
    dt, o, h, lo, c = w[-1]
    return dict(invested=invested, final=coll + sz * (c - entry), end_px=c,
                n_liq=len(liqs), first_liq=liqs[0][0] if liqs else None,
                funding=paid, fees=fees)


def spot_dca(bars, start, end, contrib, weights=None):
    """Unlevered spot accumulation -> BTC UNITS (R1)."""
    w = [b for b in bars if start <= b[0] <= end]
    seen, units, inv, ms = set(), 0.0, 0.0, []
    for dt, o, h, lo, c in w:
        key = (dt.year, dt.month)
        if key not in seen:
            seen.add(key); ms.append((dt, o))
    if weights is None:
        weights = [1.0] * len(ms)
    k = (contrib * len(ms)) / sum(weights)
    for (dt, o), wt in zip(ms, weights):
        units += (k * wt) / o; inv += k * wt
    return units, inv, w[-1][4], ms


# ──────────────────────────── parts ──────────────────────────
def part_a():
    print("\n" + "=" * 78)
    print("A · CYCLE CHRONOLOGY — and an OUT-OF-SAMPLE trough estimator (R6)")
    print("=" * 78)
    print("\n  halving -> peak:")
    for h, p in zip(HALVINGS, PEAKS):
        print(f"    {h} -> {p}   {(D(p)-D(h)).days:>4}d ({(D(p)-D(h)).days/30.44:.1f}mo)")
    print("\n  peak -> trough:")
    for p, t in zip(PEAKS, TROUGHS):
        print(f"    {p} -> {t}   {(D(t)-D(p)).days:>4}d ({(D(t)-D(p)).days/30.44:.1f}mo)")
    print("\n  trough -> trough:")
    for a, b in zip(TROUGHS, TROUGHS[1:]):
        print(f"    {a} -> {b}   {(D(b)-D(a)).days:>4}d ({(D(b)-D(a)).days/365.25:.2f}y)")
    print("\n  OUT-OF-SAMPLE projection (prior gaps only) — the honest test:")
    gaps, errs = [], []
    for i, (p, t) in enumerate(zip(PEAKS, TROUGHS)):
        if i == 0:
            gaps.append((D(t) - D(p)).days)
            print(f"    {t}: seeds the estimator (gap {gaps[-1]}d)")
            continue
        est = D(p) + datetime.timedelta(days=int(statistics.mean(gaps)))
        err = (D(t) - est).days; errs.append(err)
        print(f"    {t}: projected {est} -> error {err:+d}d")
        gaps.append((D(t) - D(p)).days)
    mg = int(statistics.mean(gaps))
    est = D(PEAKS[3]) + datetime.timedelta(days=mg)
    print(f"\n    CURRENT CYCLE: {PEAKS[3]} + {mg}d -> projected trough {est}")
    print(f"    prior |error| {[abs(e) for e in errs]}d -> quote a WINDOW, not a date:")
    print(f"      {est-datetime.timedelta(days=60)} .. {est+datetime.timedelta(days=60)}")
    return est


def part_b(hl, btc, eth):
    print("\n" + "=" * 78)
    print("B · LIQUIDATION ARITHMETIC under live Hyperliquid margins (R3)")
    print("=" * 78)
    print("\n  d* = (1 - mL) / (L(1-m))  — uniform drawdown from entry that liquidates")
    for name, bars in (("BTC", btc), ("ETH", eth)):
        mm = hl[name]["mm"]
        print(f"\n  {name}  maxLev {hl[name]['maxLeverage']}x -> maintenance {mm:.2%}")
        for L in (1.5, 2.0, 2.5, 3.0, 5.0):
            print(f"    {L:>4}x liquidates at -{(1-mm*L)/(L*(1-mm)):>5.1%}")
    print("\n  FREQUENCY: months whose drawdown from the month's OPEN is deep enough")
    for name, bars in (("BTC", btc), ("ETH", eth)):
        mm = hl[name]["mm"]
        mth = {}
        for b in bars:
            mth.setdefault((b[0].year, b[0].month), []).append(b)
        dds = [1 - min(x[3] for x in v) / v[0][1] for v in mth.values()]
        n = len(dds)
        print(f"\n    {name} ({n} months from {bars[0][0]}):")
        for L in (2.0, 2.5, 3.0):
            d = (1 - mm * L) / (L * (1 - mm))
            hit = sum(1 for x in dds if x >= d)
            per = f"~1 per {n/hit:.0f} months" if hit else "never in sample"
            print(f"      {L}x (-{d:.1%}): {hit:>3}/{n} = {hit/n:>5.1%}   {per}")


def part_c(cache, fb, fe):
    print("\n" + "=" * 78)
    print("C · FUNDING — charged on NOTIONAL (R4).  The new mechanism.")
    print("=" * 78)
    for nm, f in (("BTC", fb), ("ETH", fe)):
        allr = statistics.mean(f.values()) * 365
        print(f"\n  {nm}: mean {allr:.2%} annualised over {len(f)} days "
              f"({min(f)} -> {max(f)})")
        by = {}
        for d, r in f.items():
            by.setdefault(d.year, []).append(r)
        print("     by year: " + "  ".join(
            f"{y}:{statistics.mean(v)*365:>6.1%}" for y, v in sorted(by.items())))
        for L in (2, 3):
            print(f"     -> at {L}x this is {L*allr:>5.1%} of YOUR EQUITY per year")
    print("\n  BULL-PHASE funding (when you are long and it hurts most):")
    for lbl, a, b in (("2020-10 -> 2021-04", "2020-10-01", "2021-04-14"),
                      ("2024-10 -> 2025-01", "2024-10-01", "2025-01-20"),
                      ("2026-01 -> 2026-08", "2026-01-01", "2026-08-20")):
        o = f"    {lbl}"
        for nm, f in (("BTC", fb), ("ETH", fe)):
            rr = [r for d, r in f.items() if D(a) <= d <= D(b)]
            o += f"   {nm} {statistics.mean(rr)*365:>6.1%}" if rr else f"   {nm}  n/a"
        print(o)
    # HL validation
    try:
        ctx = ssl.create_default_context()
        now = int(datetime.datetime.now(datetime.UTC).timestamp() * 1000)
        for coin, proxy in (("BTC", fb), ("ETH", fe)):
            req = urllib.request.Request(
                "https://api.hyperliquid.xyz/info",
                data=json.dumps({"type": "fundingHistory", "coin": coin,
                                 "startTime": now - 30 * 86400 * 1000}).encode(),
                headers={"Content-Type": "application/json",
                         "User-Agent": "Mozilla/5.0"})
            with urllib.request.urlopen(req, timeout=25, context=ctx) as r:
                rows = json.load(r)
            rs = [float(x["fundingRate"]) for x in rows]
            cut = datetime.date.today() - datetime.timedelta(days=30)
            pr = [v for d, v in proxy.items() if d >= cut]
            if rs and pr:
                print(f"\n  PROXY CHECK {coin}: Hyperliquid {statistics.mean(rs)*24*365:>6.2%} "
                      f"vs Binance proxy {statistics.mean(pr)*365:>6.2%} (last 30d)")
    except Exception as e:
        print(f"\n  PROXY CHECK skipped ({e!r})")


def part_d(hl, btc, fb):
    print("\n" + "=" * 78)
    print("D · THE VERDICT METRIC — BTC UNITS, perp vs spot (R1, R7)")
    print("=" * 78)
    print("\n  Accumulation-phase analogs: peak+10mo -> peak+27mo, i.e. exactly")
    print("  the phase the sleeve is in on 2026-08-20 (10.4mo past the peak).")
    mm = hl["BTC"]["mm"]
    verdict = []
    for cyc, pk in (("c2", PEAKS[1]), ("c3", PEAKS[2])):
        a = D(pk) + datetime.timedelta(days=int(10 * 30.44))
        b = D(pk) + datetime.timedelta(days=int(27 * 30.44))
        if b > btc[-1][0]:
            continue
        units, inv, endpx, _ = spot_dca(btc, a, b, 2000.0)
        print(f"\n  {cyc}  {a} -> {b}   BTC ends ${endpx:,.0f}")
        print(f"    SPOT DCA          ${inv:>8,.0f} -> {units:>8.4f} BTC  "
              f"avg ${inv/units:>9,.0f}/BTC")
        for L in (2.0, 3.0):
            for mode in ("const", "entry"):
                r = run_perp(btc, fb, a, b, 2000.0, L, mm, mode)
                u = r["final"] / r["end_px"]
                tag = f"LIQ x{r['n_liq']}" if r["n_liq"] else ""
                print(f"    PERP {L}x {mode:<5}    ${r['invested']:>8,.0f} -> "
                      f"{u:>8.4f} BTC  {u/units-1:>+7.1%} vs spot  {tag}")
                verdict.append((cyc, L, mode, u > units))
    print("\n  R7 READ (levered must beat spot on UNITS in BOTH analogs):")
    for L in (2.0, 3.0):
        for mode in ("const", "entry"):
            wins = [v for (c, l, m, v) in verdict if l == L and m == mode]
            print(f"    {L}x {mode:<5}: {sum(wins)}/{len(wins)} analogs -> "
                  f"{'PASS' if all(wins) and wins else 'FAIL'}")


def part_e(btc, proj):
    print("\n" + "=" * 78)
    print("E · DCA SCHEDULE on UNITS — does cycle-weighting beat flat?")
    print("=" * 78)
    print("\n  NOTE: the weighted/all-in arms use the trough date, so they are")
    print("  CONDITIONAL on the estimator.  Part A's out-of-sample errors")
    print("  (-47d, -10d) are the honest uncertainty around that conditioning.")
    for cyc, pk, tr in (("c2", PEAKS[1], TROUGHS[1]), ("c3", PEAKS[2], TROUGHS[2])):
        a = D(pk) + datetime.timedelta(days=int(10 * 30.44))
        b = D(pk) + datetime.timedelta(days=int(27 * 30.44))
        if b > btc[-1][0]:
            continue
        flat, inv, _, ms = spot_dca(btc, a, b, 2000.0)
        wts = [2.5 if abs((d - D(tr)).days) <= 183 else 0.4 for d, _ in ms]
        wtd, _, _, _ = spot_dca(btc, a, b, 2000.0, weights=wts)
        tgt = min(ms, key=lambda x: abs((x[0] - D(tr)).days))
        allin = inv / tgt[1]
        w = [x for x in btc if a <= x[0] <= b]
        low = min(w, key=lambda x: x[3])
        print(f"\n  {cyc}  budget ${inv:,.0f}   (trough {tr})")
        for lbl, u in (("flat DCA", flat),
                       ("cycle-weighted 2.5x within +/-6mo", wtd),
                       ("all-in at PROJECTED trough month", allin),
                       ("all-in at TRUE low (hindsight bound)", inv / low[3])):
            print(f"    {lbl:<38} {u:>8.4f} BTC  avg ${inv/u:>9,.0f}  {u/flat-1:>+7.1%}")


def part_f(btc, hl):
    print("\n" + "=" * 78)
    print("F · THE CONFLICT — believing the cycle IS the argument against leverage")
    print("=" * 78)
    pk_px = 124753.0
    now = btc[-1][4]
    mm = hl["BTC"]["mm"]
    print(f"\n  peak ${pk_px:,.0f} (2025-10-06) · today ${now:,.0f} = -{1-now/pk_px:.1%}")
    print("\n  completed cycle peak->trough drawdowns: -83.1% (2018), -75.7% (2022)")
    print("  [the 2013 peak predates the series; quoted from chronology only]\n")
    print("  implied trough for THIS cycle, and distance from today:")
    for dd in (0.60, 0.70, 0.757, 0.831):
        b = pk_px * (1 - dd)
        print(f"    -{dd:>5.1%} -> ${b:>9,.0f}   {b/now-1:>+7.1%} from today")
    print("\n  price at which a position opened TODAY is liquidated:")
    for L in (1.5, 2.0, 2.5, 3.0):
        d = (1 - mm * L) / (L * (1 - mm))
        print(f"    {L}x -> ${now*(1-d):>9,.0f}  (-{d:.1%})")
    print("\n  => the MILDEST completed drawdown (-75.7% = $30,315) sits BELOW")
    print("     every levered liquidation price above.  You cannot hold the")
    print("     cycle thesis and leverage through the trough at the same time.")


def main():
    cache = _load_cache()
    hl = hl_margins(cache)
    btc = spot(cache, "BTC-USD")
    eth = spot(cache, "ETH-USD")
    fb = funding(cache, "BTCUSDT")
    fe = funding(cache, "ETHUSDT")
    print("#147 · CRYPTO CYCLE SLEEVE — run", datetime.date.today())
    print(f"BTC {len(btc)} bars {btc[0][0]}..{btc[-1][0]} · ETH {len(eth)} bars")
    print(f"HL margins: BTC {hl['BTC']['mm']:.2%} · ETH {hl['ETH']['mm']:.2%}")
    proj = part_a()
    part_b(hl, btc, eth)
    part_c(cache, fb, fe)
    part_d(hl, btc, fb)
    part_e(btc, proj)
    part_f(btc, hl)
    print("\n" + "=" * 78)
    print("VERDICT: see BACKTEST_RESULTS §41.  Leverage FAILS R7 (one analog")
    print("wiped, one won).  Sleeve ships UNLEVERED spot until the trough is")
    print("confirmed; leverage is a post-trough instrument, capped at 2x BTC.")
    print("=" * 78)


if __name__ == "__main__":
    main()
