#!/usr/bin/env python3
"""
Market regime — the decisive bull/bear signal.
==============================================

Per-stock trend-cutting failed our backtests twice, but INDEX-level regime
timing is the one trend rule with a long honest record: the 10-month SMA
rule (Faber, "A Quantitative Approach to Tactical Asset Allocation"). At
each MONTH END: index close above its 10-month SMA -> BULL (invested);
below -> BEAR (cash). It is deliberately slow — it fires a handful of times
a decade, which is what makes it decisive rather than noisy.

Protocol encoded for the digest (user's plan, 2026-07-06):
  BEAR fires  -> halt all adds, exit satellite/🚀 names, raise dry powder;
                 long-horizon SRS index core stays (30y horizon ≠ timing).
  BULL resumes-> redeploy dry powder via the ⭐/🚀 screens.

The regime is judged on BOTH SPY and QQQ month-end closes:
  BULL    both above their 10m SMA
  BEAR    both below            -> the decisive sell signal
  MIXED   split — no action, watch月末 (month-end)

homily_regime_backtest.py holds the honest 30y comparison vs buy-and-hold;
headline numbers are also on docs/index.html.
"""
import datetime
from dataclasses import dataclass

from homily_data import fetch_daily  # noqa: F401  (re-export convenience)
import json, ssl, urllib.request


@dataclass
class Regime:
    label: str            # BULL / BEAR / MIXED
    detail: dict          # sym -> (last_close, sma10, pct_above, month_end_done)
    action: str


def fetch_monthly(symbol, rng="max"):
    """-> [(date, close)] month-end closes; last row may be a partial month."""
    url = (f"https://query1.finance.yahoo.com/v8/finance/chart/{symbol}"
           f"?range={rng}&interval=1mo")
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req, timeout=20,
                                context=ssl.create_default_context()) as r:
        data = json.load(r)
    res = data["chart"]["result"][0]
    out = []
    for t, c in zip(res["timestamp"],
                    res["indicators"]["quote"][0]["close"]):
        if c is not None:
            out.append((datetime.date.fromtimestamp(t), c))
    return out


def sma10_state(monthly):
    """State from COMPLETED month-ends only (last row = current partial)."""
    closes = [c for _, c in monthly[:-1]]         # completed months
    sma = sum(closes[-10:]) / 10
    last_completed = closes[-1]
    live = monthly[-1][1]                          # intramonth, for context
    return last_completed, sma, live


def market_regime(symbols=("SPY", "QQQ")):
    detail, above = {}, []
    for sym in symbols:
        m = fetch_monthly(sym)
        last_done, sma, live = sma10_state(m)
        ok = last_done > sma
        above.append(ok)
        detail[sym] = (live, sma, (live / sma - 1) * 100, ok)
    if all(above):
        label, action = "BULL", ("stay invested; adds via ⭐/🚀 screens; "
                                 "sell trigger = BOTH month-end closes "
                                 "below 10m SMA")
    elif not any(above):
        label, action = "BEAR", ("DECISIVE SELL: halt adds, exit satellite/"
                                 "🚀 names, raise dry powder; SRS index core "
                                 "stays; re-enter when a month-end close "
                                 "regains the 10m SMA")
    else:
        label, action = "MIXED", ("split signal — no action; judge at the "
                                  "next month-end close")
    return Regime(label, detail, action)


if __name__ == "__main__":
    r = market_regime()
    print(f"REGIME: {r.label}")
    for sym, (live, sma, pct, ok) in r.detail.items():
        print(f"  {sym}: live {live:.2f} vs 10m SMA {sma:.2f} ({pct:+.1f}%) "
              f"month-end {'above' if ok else 'BELOW'}")
    print(f"  action: {r.action}")
