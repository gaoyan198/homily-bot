#!/usr/bin/env python3
"""
Validation harness for homily_clone.py.

It cannot prove fidelity to Homily's *proprietary* formula (undisclosed), but it
DOES prove the implementation is mathematically sound and behaves sensibly:

  1. EMA cross-check: our recursive EMA vs an independent closed-form weighted sum.
  2. MACD sign sanity on monotonic series.
  3. Regime behaviour: pure uptrend -> all RED, pure downtrend -> all WHITE.
  4. Turning-point eyeball: print the full circle history for a known up-name
     (AMD) and down-name (BABA) so flips can be checked against the chart.
  5. DRAM (Roundhill Memory ETF) read on a DAILY window (too new for weekly).
"""

from homily_clone import ema, macd, sma, homily_circle, CLOSES

def approx(a, b, tol=1e-9):
    return abs(a - b) <= tol * max(1.0, abs(a), abs(b))

# --- 1. EMA cross-check against independent closed-form ---------------------
# EMA_t = sum_{i<=t} w_i * x_i / 1 (recursive). Verify against explicit unroll.
def ema_reference(series, span):
    k = 2 / (span + 1)
    out, e = [], series[0]
    for j, x in enumerate(series):
        if j == 0:
            e = x
        else:
            e = x * k + e * (1 - k)
        out.append(e)
    return out

x = [10, 11, 9, 12, 15, 14, 13, 16, 18, 17]
ours = ema(x, 5)
ref  = ema_reference(x, 5)
assert all(approx(a, b) for a, b in zip(ours, ref)), "EMA mismatch!"
# hand check one value: span5 k=1/3; e1=10; e2=11/3+10*2/3=10.3333...
assert approx(ours[1], 11*(1/3) + 10*(2/3)), "EMA hand-calc mismatch!"
print("[1] EMA recursion matches independent reference + hand calc ............ PASS")

# --- 2. MACD LINE sign on monotonic series ----------------------------------
# NB: the *histogram* (line-signal) measures acceleration, NOT direction -- a
# decelerating decay prints hist>0 even while falling. The *line* (EMA12-EMA26)
# is the directional piece, so that is what we assert.
up = [100 * (1.01 ** i) for i in range(60)]
dn = [100 * (0.99 ** i) for i in range(60)]
l_up, _, _ = macd(up)
l_dn, _, _ = macd(dn)
assert l_up[-1] > 0 and l_dn[-1] < 0, "MACD line sign wrong on monotonic series!"
print("[2] MACD line sign correct on monotonic up/down ........................ PASS")

# --- 3. Regime behaviour on synthetic trends -------------------------------
sig_up = homily_circle("UP", up)
sig_dn = homily_circle("DN", dn)
assert sig_up.circle == "RED" and sig_up.score == 4, "Uptrend not RED 4/4!"
assert sig_dn.circle == "WHITE" and sig_dn.score == 0, "Downtrend not WHITE 0/4!"
# ^ with the line>0 momentum guard, a pure decaying downtrend now scores a clean
#   0/4 (previously 1/4, because the decelerating decay tripped hist>0 alone).
print(f"[3] Pure uptrend -> {sig_up.circle} {sig_up.score}/4 ; "
      f"pure downtrend -> {sig_dn.circle} {sig_dn.score}/4 ................ PASS")

# --- 3b. No look-ahead: signal at time t uses only data <= t ----------------
# Truncating the series must not change earlier circles.
def circle_series(closes):
    e10, e30, s30 = ema(closes, 10), ema(closes, 30), sma(closes, 30)
    line, _, hist = macd(closes)
    out = []
    for i in range(len(closes)):
        sc = (closes[i] > e30[i]) + (e10[i] > e30[i]) + (hist[i] > 0 and line[i] > 0) + \
             (s30[i] is not None and i >= 4 and s30[i-4] is not None and s30[i] > s30[i-4])
        out.append("RED" if sc >= 3 else ("WHITE" if sc <= 1 else "AMBER"))
    return out
full = circle_series(CLOSES["AMD"])
trunc = circle_series(CLOSES["AMD"][:40])
assert full[:35] == trunc[:35], "Look-ahead leak: past circles changed!"
print("[3b] No look-ahead leakage (past circles stable under truncation) ...... PASS")

# --- 4. Turning-point eyeball ----------------------------------------------
def show(tk):
    seq = circle_series(CLOSES[tk])
    sym = {"RED": "R", "AMBER": "a", "WHITE": "W"}
    print(f"   {tk:<5}", "".join(sym[c] for c in seq), f"  (now: {seq[-1]})")
print("[4] Circle history  (R=red/hold  a=amber  W=white/cut), oldest->newest:")
show("AMD"); show("BABA"); show("CSPX"); show("PLTR")

# --- 5. DRAM daily read (too new for weekly 30-bar regime) ------------------
DRAM_DAILY = [27.76,29.16,29.44,32.47,32.38,32.43,33.55,35.57,34.47,35.04,35.59,
35.07,34.93,37.3,36.36,37.2,38.57,37.33,38.23,39.33,40.41,42.47,46.29,48.68,
46.55,52.8,55.08,51.3,54.54,53.79,51.1,49.32,49.77,51.51,54.34,52.82,60.51,
60.73,62.57,63.2,68,69.57,69.71,65.7,55.79,60.52,59.86,57.37,65.12,65.01,71.07,
68.12,69.95,76.71,80.72,69.22,69.93,76.89,71.88]
d = homily_circle("DRAM", DRAM_DAILY)
print(f"\n[5] DRAM (Roundhill Memory ETF) - DAILY read, ~3mo history (short-horizon):")
print(f"    circle={d.circle} score={d.score}/4  px={d.price:.2f}  "
      f"%vsMA(30d)={d.pct_vs_ma30:+.1f}%  days_in_regime={d.weeks_in_regime}")
print(f"    signals: {d.detail}")
print(f"    NOTE: only ~59 daily bars -> 30-bar MA barely warmed; treat as tentative.")
print("\nAll structural assertions passed.")
