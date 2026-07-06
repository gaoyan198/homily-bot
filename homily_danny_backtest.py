#!/usr/bin/env python3
"""
Accumulate-on-dip vs plain DCA — the honest check for the Danny-style layer.
============================================================================

Question it answers: if you commit the SAME monthly budget to the SAME stock,
does waiting for the ⭐ ACCUMULATE state (trend intact + price at chip
support) get you a better average cost than mechanically buying on the 1st
trading day of each month?

Design (no look-ahead):
  * 5y daily bars; first 300 days are warm-up for both strategies.
  * $1 of budget arrives at each month's first trading day (both strategies).
  * DCA deploys immediately at that day's close.
  * Danny-gated holds cash and deploys ALL accrued cash at the close of the
    first day whose signal — computed only from bars up to that day — is
    ACCUMULATE. Leftover cash at the end stays cash (reported).
  * Metric: average cost per share vs DCA, plus final value per $ budgeted.

This is deliberately a cost-basis comparison, not a market-timing system:
core-position exits are out of scope by design (Danny never sells).
"""
from homily_data import fetch_daily
from homily_danny import danny_signal

TICKERS = ["NVDA", "TSLA", "TSM", "PLTR", "CSPX.L"]
WARMUP = 300


def month_starts(bars, start):
    idx, cur = [], None
    for i in range(start, len(bars)):
        k = (bars[i][0].year, bars[i][0].month)
        if k != cur:
            idx.append(i); cur = k
    return set(idx)


def run(sym):
    bars = fetch_daily(sym, rng="5y")
    starts = month_starts(bars, WARMUP)
    dca_units = dca_cost = 0.0
    dan_units = dan_cost = cash = 0.0
    wait_days = waits = 0
    pending_since = None
    for i in range(WARMUP, len(bars)):
        close = bars[i][4]
        if i in starts:
            dca_units += 1.0 / close; dca_cost += 1.0
            cash += 1.0
            if pending_since is None:
                pending_since = i
        if cash > 0 and danny_signal(sym, bars[:i + 1]).state == "ACCUMULATE":
            dan_units += cash / close; dan_cost += cash; cash = 0.0
            wait_days += i - pending_since; waits += 1
            pending_since = None
    last = bars[-1][4]
    dca_avg = dca_cost / dca_units
    dan_avg = dan_cost / dan_units if dan_units else float("nan")
    dca_val = dca_units * last
    dan_val = dan_units * last + cash
    return (dca_avg, dan_avg, dca_val / dca_cost, dan_val / (dan_cost + cash),
            cash, wait_days / waits if waits else 0)


if __name__ == "__main__":
    print("Accumulate-on-dip (⭐-gated) vs monthly DCA — same budget, 5y daily")
    print(f"{'NAME':<7}{'DCA avg':>9}{'⭐ avg':>9}{'edge':>7}"
          f"{'DCA $/1':>9}{'⭐ $/1':>8}{'idle$':>7}{'avg wait':>9}")
    print("-" * 65)
    for sym in TICKERS:
        dca_avg, dan_avg, dca_v, dan_v, cash, wait = run(sym)
        edge = (1 - dan_avg / dca_avg) * 100
        print(f"{sym:<7}{dca_avg:>9.2f}{dan_avg:>9.2f}{edge:>6.1f}%"
              f"{dca_v:>9.2f}{dan_v:>8.2f}{cash:>7.0f}{wait:>7.0f}d")
    print("-" * 65)
    print("edge = % cheaper avg cost than DCA (negative = gating hurt)")
    print("$/1 = final value per $1 budgeted · idle$ = never-deployed cash")
