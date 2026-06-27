#!/usr/bin/env python3
"""
Backtest for the Homily-clone red/white-circle strategy.
========================================================

Honest test of "hold when RED, sit in cash when WHITE" vs buy-and-hold, over 5y
of weekly data (IBKR). The circle is CAUSAL (week-t signal uses only data <= t),
so the sim has no look-ahead. Transaction cost charged on every position change.

Strategy variants:
  STRICT : invested only when circle == RED
  LOOSE  : invested when circle in {RED, AMBER}

Reports total return, CAGR, max drawdown, %time-in-market, #switches -- so you
can see whether momentum makes money or merely cuts drawdown.
"""
from homily_clone import ema, sma, macd

COST_BPS = 15          # 0.15% per position switch (commission+spread; SG has no CGT)

def circle_series(closes):
    e10, e30, s30 = ema(closes, 10), ema(closes, 30), sma(closes, 30)
    line, _, hist = macd(closes)
    out = []
    for i in range(len(closes)):
        sc = (closes[i] > e30[i]) + (e10[i] > e30[i]) + \
             (hist[i] > 0 and line[i] > 0) + \
             (s30[i] is not None and i >= 4 and s30[i-4] is not None and s30[i] > s30[i-4])
        out.append("RED" if sc >= 3 else ("WHITE" if sc <= 1 else "AMBER"))
    return out

def max_drawdown(equity):
    peak, mdd = equity[0], 0.0
    for v in equity:
        peak = max(peak, v)
        mdd = min(mdd, v / peak - 1)
    return mdd

def cagr(equity, n_weeks):
    yrs = n_weeks / 52.0
    return (equity[-1] / equity[0]) ** (1 / yrs) - 1 if yrs > 0 else 0.0

def backtest(closes, invested_when):
    """invested_when: set of circle colours that mean 'hold the asset'."""
    circ = circle_series(closes)
    cost = COST_BPS / 10000.0
    eq, pos, switches, weeks_in = [1.0], 0, 0, 0
    for i in range(len(closes) - 1):
        want = 1 if circ[i] in invested_when else 0
        if want != pos:
            eq[-1] *= (1 - cost)      # pay to switch
            switches += 1
            pos = want
        weeks_in += pos
        r = closes[i + 1] / closes[i]
        eq.append(eq[-1] * (r if pos else 1.0))   # cash earns 0
    return {
        "ret":   eq[-1] - 1,
        "cagr":  cagr(eq, len(closes) - 1),
        "mdd":   max_drawdown(eq),
        "tim":   weeks_in / (len(closes) - 1),
        "switch": switches,
        "now":   circ[-1],
    }

def buyhold(closes):
    eq = [closes[i] / closes[0] for i in range(len(closes))]
    return {"ret": eq[-1] - 1, "cagr": cagr(eq, len(closes) - 1),
            "mdd": max_drawdown(eq), "tim": 1.0, "switch": 0, "now": "-"}

# --- 5y weekly closes (IBKR, ending 2026-06-22) ---------------------------
from bt_data import BT  # close arrays live in bt_data.py to keep this readable

if __name__ == "__main__":
    print(f"5-year weekly backtest  |  switch cost {COST_BPS}bps  |  cash earns 0%\n")
    hdr = f"{'ASSET':<6} {'STRATEGY':<10} {'TotRet':>8} {'CAGR':>7} {'MaxDD':>7} {'InMkt':>6} {'Switch':>7}"
    agg = {}
    for tk, closes in BT.items():
        bh = buyhold(closes)
        st = backtest(closes, {"RED"})
        lo = backtest(closes, {"RED", "AMBER"})
        print("-" * len(hdr)); print(hdr); print("-" * len(hdr))
        for name, r in [("Buy&Hold", bh), ("Homily-STRICT", st), ("Homily-LOOSE", lo)]:
            print(f"{tk:<6} {name:<10} {r['ret']*100:>7.0f}% {r['cagr']*100:>6.1f}% "
                  f"{r['mdd']*100:>6.0f}% {r['tim']*100:>5.0f}% {r['switch']:>7}")
        agg.setdefault("bh", []).append(bh); agg.setdefault("st", []).append(st); agg.setdefault("lo", []).append(lo)
    # equal-weight average across the 4 names
    def avg(key, f): return sum(f(x) for x in agg[key]) / len(agg[key])
    print("\n" + "=" * len(hdr))
    print(f"{'EQUAL-WEIGHT AVG across 4 names':<40}  CAGR    MaxDD")
    print("=" * len(hdr))
    for name, key in [("Buy&Hold","bh"),("Homily-STRICT","st"),("Homily-LOOSE","lo")]:
        print(f"{name:<40}  {avg(key, lambda x:x['cagr'])*100:>5.1f}%  {avg(key, lambda x:x['mdd'])*100:>5.0f}%")
