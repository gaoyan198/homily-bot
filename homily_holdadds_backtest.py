#!/usr/bin/env python3
"""
#125 gate artifact — buy-day eligibility: ⭐-only vs CONVICTION ACC|HOLD.
=========================================================================

Pre-registered rule (frozen before the run; results in BACKTEST_RESULTS
§29): widen homily_buyday.star_candidates from `state == ACCUMULATE` to
`conv_tier == CONVICTION and state in (ACCUMULATE, HOLD)`. Gate: the NEW
rule beats the OLD rule on final-value-per-dollar in BOTH honest windows
(buys 2023-08..2025-07 and buys 2025-08..2026-07, both valued at the end).

Procedure (the LIVE engines, never a reimplementation — EXECUTION.md R6):
  1. every ticker the signals log screens, daily bars via fetch_series
     (rng="max"), truncated per-day to the trailing-5y window the live
     rng="5y" fetch would have returned;
  2. walk forward daily: danny_signal() + conviction() on bars through
     day i == what the next 09:00 SGT digest printed (replay validated
     against the live log 2026-07-25: 1602/1610 = 99.5% state match; all
     8 misses were HK/SG/LSE closes, every US row exact);
  3. DCA sim, the buy-day mechanics minus whole-share rounding and the
     25% cap (both hit the arms identically): first replay date of each
     month, $1,000 split equally across the top-3 by RS12 among that
     arm's eligible set, USD names only (R12), never sells; a month with
     no eligible name buys SPY (§3.5). Benchmarks: $1,000/m SPY / QQQ.

Raw closes throughout, dividends ignored — consistent across arms AND
benchmarks, same caveat homily_promotions.forward_check states.

CAVEATS FROZEN WITH THE GATE (recorded in promotions.json `hold-adds`):
  * the universe file is as of 2026-07-11 replayed backwards, so every
    name survived to be selected — ABSOLUTE returns (and the margin over
    SPY/QQQ) are inflated; the OLD-vs-NEW spread is within-universe,
    within-day and unaffected;
  * monthly-mark MaxDD is DEEPER under NEW (-36.4% vs -28.9% on the
    2026-07-25 run) — more return, deeper dips, accepted by the owner.

Runtime warning: fetches ~150 names' full history and replays ~100k
signals — ≈10 minutes. A study script, not CI; run it for the yearly #40
re-test or a demotion review.

Gate result 2026-07-25 (37 buy days 2023-07..2026-07, valued 2026-07-24):
  OLD 1.944 $/$ (windows 2.322 / 1.156) · NEW 2.266 (2.758 / 1.243)
  SPY 1.308 · QQQ 1.395 — NEW > OLD on both windows -> PASS.
"""
import csv
import bisect
import datetime
import collections

from homily_data import fetch_series
from homily_danny import danny_signal
from homily_conviction import conviction
import daily_run

MONTHLY = 1000.0
MAX_PICKS = 3                    # mirrors homily_buyday.MAX_STARS
START = datetime.date(2023, 7, 25)
FIVE_Y = datetime.timedelta(days=365 * 5 + 1)

RULES = {
    "OLD": lambda st, tier: st == "ACCUMULATE",
    "NEW": lambda st, tier: tier == "CONVICTION" and st in ("ACCUMULATE",
                                                            "HOLD"),
}


def _yahoo_map():
    tick = sorted({r["ticker"]
                   for r in csv.DictReader(open("homily_signals_log.csv"))})
    m = {**daily_run.UNIVERSE, **daily_run.WATCH, **daily_run.HOLDINGS}
    return {t: m.get(t, t) for t in tick}


def _window(bars, adj, i):
    lo = bisect.bisect_left([b[0] for b in bars], bars[i][0] - FIVE_Y)
    return bars[lo:i + 1], adj[lo:i + 1]


def replay(cache):
    """-> rows of (date, ticker, state, tier, rs12, close) for every
    ticker-day from START; cache: ticker -> (bars, adj)."""
    spy_bars, spy_adj = cache["SPY"]
    spy_dates = [b[0] for b in spy_bars]
    rows = []
    for t, (bars, adj) in sorted(cache.items()):
        if t in ("SPY", "QQQ") or len(bars) < 300:
            continue
        dates = [b[0] for b in bars]
        for i in range(max(bisect.bisect_left(dates, START), 260),
                       len(bars)):
            j = bisect.bisect_right(spy_dates, dates[i]) - 1
            if j < 260:
                continue
            b, a = _window(bars, adj, i)
            sb, sa = _window(spy_bars, spy_adj, j)
            try:
                sig = danny_signal(t, b)
                cv = conviction(sig, b, [x[4] for x in sb],
                                adj=a, spy_adj=sa)
            except Exception:                          # noqa: BLE001
                continue
            rows.append((dates[i].isoformat(), t, sig.state, cv.tier,
                         cv.rs12, b[-1][4]))
    return rows


def dca(rows, cache, mid="2025-07-24"):
    """The sim. -> {arm: (per$_all, per$_winA, per$_winB, maxdd_pct)}."""
    px = {t: ([b[0].isoformat() for b in bars], [b[4] for b in bars])
          for t, (bars, _a) in cache.items()}

    def price(t, d):
        ds, cs = px[t]
        return cs[bisect.bisect_right(ds, d) - 1]

    by_date = collections.defaultdict(list)
    for r in rows:
        by_date[r[0]].append(r)
    dates = sorted(by_date)
    seen, buy_days = set(), []
    for d in dates:
        if d[:7] not in seen:
            seen.add(d[:7])
            buy_days.append(d)
    end = dates[-1]
    foreign = {t for t, y in _yahoo_map().items() if "." in y}

    out = {}
    arms = dict(RULES, SPY=None, QQQ=None)
    for arm, rule in arms.items():
        books = {"all": collections.defaultdict(float),
                 "A": collections.defaultdict(float),
                 "B": collections.defaultdict(float)}
        inv = collections.Counter()
        peak = mdd = 0.0
        run = 0.0
        bset = set(buy_days)
        for d in dates:
            if d in bset:
                w = "A" if d <= mid else "B"
                inv[w] += MONTHLY
                run += MONTHLY
                if rule is None:
                    for k in ("all", w):
                        books[k][arm] += MONTHLY / price(arm, d)
                else:
                    cand = [r for r in by_date[d]
                            if rule(r[2], r[3]) and r[1] not in foreign]
                    cand.sort(key=lambda r: (-r[4], r[1]))
                    picks = cand[:MAX_PICKS] or None
                    for k in ("all", w):
                        if picks is None:              # §3.5 fallback
                            books[k]["SPY"] += MONTHLY / price("SPY", d)
                        else:
                            for r in picks:
                                books[k][r[1]] += (MONTHLY / len(picks)
                                                   ) / r[5]
            if run and (d[8:10] in ("01", "15") or d == end):
                ratio = sum(sh * price(t, d)
                            for t, sh in books["all"].items()) / run
                peak = max(peak, ratio)
                mdd = min(mdd, (ratio - peak) / peak * 100)
        val = {k: sum(sh * price(t, end) for t, sh in books[k].items())
               for k in books}
        out[arm] = (val["all"] / sum(inv.values()),
                    val["A"] / inv["A"], val["B"] / inv["B"], mdd)
    return out


if __name__ == "__main__":
    ym = _yahoo_map()
    ym.update({"SPY": "SPY", "QQQ": "QQQ"})
    print(f"fetching {len(ym)} symbols (rng=max) …")
    cache = {}
    for t, y in ym.items():
        try:
            cache[t] = fetch_series(y, rng="max")
        except Exception as e:                         # noqa: BLE001
            print(f"  skip {t}: {e!r:.60}")
    print(f"replaying {len(cache)} tickers …")
    rows = replay(cache)
    print(f"{len(rows):,} signals; running the DCA sim …\n")
    res = dca(rows, cache)
    print(f"{'arm':<5}{'per $1':>8}{'win A':>8}{'win B':>8}{'MaxDD':>8}")
    for arm, (a, wa, wb, dd) in res.items():
        print(f"{arm:<5}{a:>8.3f}{wa:>8.3f}{wb:>8.3f}{dd:>7.1f}%")
    ok = (res["NEW"][1] > res["OLD"][1]) and (res["NEW"][2] > res["OLD"][2])
    print(f"\nGATE (NEW > OLD on BOTH windows): {'PASS' if ok else 'FAIL'}")
