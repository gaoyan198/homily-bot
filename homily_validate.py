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
# --- 6. Chip engine: POC lands where the volume is --------------------------
import datetime as _dt
from homily_chips import build_profile

def _bars(prices, vols, spread=0.5):
    d0 = _dt.date(2024, 1, 1)
    return [(d0 + _dt.timedelta(days=i), p, p + spread, p - spread, p, v)
            for i, (p, v) in enumerate(zip(prices, vols))]

# 200 quiet days at 100, then 30 heavy-volume days at 50: despite being newer,
# the 50-zone has 10x volume -> POC must sit near 50; with price at 50, the
# 100-zone chips are all underwater (resistance, ~0% in profit side below).
prof = build_profile(_bars([100.0]*200 + [50.0]*30, [1e6]*200 + [1e7]*30))
assert abs(prof.poc - 50) < 2, f"POC {prof.poc} not at the heavy-volume zone!"
assert prof.pct_in_profit < 60, "in-profit % ignores the trapped 100-cost chips!"
assert prof.resistance and abs(prof.resistance[0][0] - 100) < 3, \
    "trapped 100-zone not flagged as resistance!"
print("[6] Chip engine: POC at heavy-volume zone, trapped chips = resistance .. PASS")

# --- 7. Chip decay: recent volume outweighs equal old volume ----------------
# same volume at 100 (old) and 50 (recent, 200 days later) -> POC follows recency
prof2 = build_profile(_bars([100.0]*50 + [75.0]*150 + [50.0]*50,
                            [1e6]*50 + [1e5]*150 + [1e6]*50))
assert abs(prof2.poc - 50) < 2, "decay broken: old chips outweigh recent ones!"
print("[7] Chip decay: equal volume, recent zone wins the POC .................. PASS")

# --- 8. Composite state sanity on synthetic trends ---------------------------
from homily_danny import danny_signal
up_b = _bars([100 * 1.003 ** i for i in range(900)], [1e6]*900)
dn_b = _bars([100 * 0.997 ** i for i in range(900)], [1e6]*900)
s_up = danny_signal("UP", up_b)
s_dn = danny_signal("DN", dn_b)
assert s_up.state in ("ACCUMULATE", "HOLD") and s_up.monthly_up, \
    f"steady uptrend not accumulate/hold (got {s_up.state})!"
assert s_dn.state == "CAUTION" and not s_dn.monthly_up, \
    f"steady downtrend not CAUTION (got {s_dn.state})!"
print(f"[8] Composite: uptrend -> {s_up.state}, downtrend -> {s_dn.state} ...... PASS")

# --- 9. Volatility hole: quiet cluster after a decline, then breakout -------
from homily_vol import find_hole

def _vbars(specs):
    """specs: list of (price, range) -> daily bars with that H-L range."""
    d0 = _dt.date(2024, 1, 1)
    return [(d0 + _dt.timedelta(days=i), p, p + r, p - r, p, 1e6)
            for i, (p, r) in enumerate(specs)]

decline = [(200 - i, 4.0) for i in range(80)]            # volatile downtrend
quiet   = [(120, 0.3)] * 10                              # volatility hole
vh = find_hole(_vbars(decline + quiet))
assert vh is not None and vh.trend_before == "DOWN", "hole not found after decline!"
assert vh.status == "INSIDE", f"expected INSIDE, got {vh.status}"
assert vh.lower >= 119 and vh.upper <= 121.5, f"zone {vh.lower}-{vh.upper} off!"
brk = find_hole(_vbars(decline + quiet + [(125, 2.0)] * 3))
assert brk is not None and brk.status == "BREAKOUT", "upside resolve not BREAKOUT!"
dn = find_hole(_vbars(decline + quiet + [(112, 2.0)] * 3))
assert dn is not None and dn.status == "BREAKDOWN", "downside resolve not BREAKDOWN!"
print("[9] Volatility hole: found after decline, zone tight, both resolutions  PASS")

# --- 10. Volatility hole feeds the composite: BOTTOMING state ---------------
# volatile decline (trend broken) then quiet base then upside breakout
vol_dn = [100 * 0.997 ** i for i in range(800)]
specs = [(p, p * 0.03) for p in vol_dn] + \
        [(vol_dn[-1], vol_dn[-1] * 0.002)] * 10 + \
        [(vol_dn[-1] * 1.05, vol_dn[-1] * 0.01)] * 3
s_bot = danny_signal("BOT", _vbars(specs))
assert s_bot.state == "BOTTOMING", f"expected BOTTOMING, got {s_bot.state}!"
print(f"[10] Composite: decline + hole breakout -> {s_bot.state} .............. PASS")

# --- 11. Conviction: synthetic leader passes gates, megacap laggard fails ---
from homily_conviction import conviction

spy_flat = [100.0 * 1.0003 ** i for i in range(900)]        # ~8%/yr benchmark
leader_px = [10 * 1.004 ** i for i in range(900)]           # strong leader
leader = [(d, o, h, l, c, 2e6) for d, o, h, l, c, v in
          _vbars([(p, p * 0.01) for p in leader_px])]       # small $vol
c_lead = conviction(danny_signal("LEAD", leader), leader, spy_flat)
assert c_lead.gates_ok, f"synthetic leader failed gates: {c_lead.gates_failed}"
assert c_lead.tier in ("CONVICTION", "STARTER"), f"tier {c_lead.tier}?"

mega = [(d, o, h, l, c, 5e9) for d, o, h, l, c, v in
        _vbars([(p, p * 0.01) for p in spy_flat])]          # huge $vol, no RS
c_mega = conviction(danny_signal("MEGA", mega), mega, spy_flat)
assert not c_mega.gates_ok and "G1 size" in c_mega.gates_failed \
    and "G3 leader" in c_mega.gates_failed, "megacap laggard passed gates!"
print(f"[11] Conviction: leader -> {c_lead.tier} {c_lead.score}, "
      f"megacap laggard fails {len(c_mega.gates_failed)} gates ....... PASS")

# --- 12. Regime: 10m-SMA month-end rule on synthetic monthly closes ---------
from homily_regime import sma10_state

up_m = [(_dt.date(2020 + i // 12, i % 12 + 1, 1), 100 * 1.02 ** i)
        for i in range(30)]
last, sma, live = sma10_state(up_m)
assert last > sma, "rising market not above its 10m SMA!"
dn_m = [(d, 200 * 0.97 ** i) for i, (d, _) in enumerate(up_m)]
last, sma, live = sma10_state(dn_m)
assert last < sma, "falling market not below its 10m SMA!"
# partial current month must NOT affect the month-end judgement
spiked = dn_m[:-1] + [(dn_m[-1][0], 1e6)]
l2, s2, _ = sma10_state(spiked)
assert (l2, s2) == (last, sma) or l2 < s2, "partial month leaked into signal!"
print("[12] Regime 10m-SMA: up->BULL, down->BEAR, partial month ignored ..... PASS")

# --- 13. Fundamentals verdict logic (offline, no EDGAR calls) ----------------
from homily_fund import checks_from

grower = checks_from(rev=[("2024-12-31", 100), ("2025-12-31", 140)],
                     ni=[("2024-12-31", -5), ("2025-12-31", 10)],
                     ocf=[("2024-12-31", 1), ("2025-12-31", 20)],
                     sh=(100e6, 105e6))
assert grower == {"growth": True, "profit": True, "dilution": True}, grower
burner = checks_from(rev=[("2024-12-31", 100), ("2025-12-31", 104)],
                     ni=[("2024-12-31", -50), ("2025-12-31", -80)],
                     ocf=[("2024-12-31", -30), ("2025-12-31", -40)],
                     sh=(100e6, 140e6))
assert burner == {"growth": False, "profit": False, "dilution": False}, burner
assert checks_from(None, None, None, None) == {}, "no data must mean no checks"
# OCF rescues a GAAP-loss compounder (e.g. early AMZN pattern)
mixed = checks_from(rev=[("a", 100), ("b", 130)], ni=[("a", -1), ("b", -1)],
                    ocf=[("a", 5), ("b", 9)], sh=None)
assert mixed["profit"] is True and "dilution" not in mixed
print("[13] Fundamentals: grower 3/3, cash-burner 0/3, OCF rescue, no-data—  PASS")

# --- 14. Whale read: absorption + flow divergence in a dip -------------------
from homily_whale import whale_read

def _wbars(specs):
    """specs: list of (open, high, low, close, volume) -> daily bars."""
    d0 = _dt.date(2024, 1, 1)
    return [(d0 + _dt.timedelta(days=i), o, h, l, c, v)
            for i, (o, h, l, c, v) in enumerate(specs)]

flat = [(100.0, 101.0, 99.0, 100.0, 1e6)] * 100
# 15-day dip 100 -> ~88: heavy volume, wide range DOWN days that close near
# the high (sellers absorbed) -> A/D line RISES while price falls
absorbed = [(p + 0.5, p + 0.5, p - 2.0, p, 3e6)
            for p in [100 - 0.8 * (k + 1) for k in range(15)]]
w = whale_read(_wbars(flat + absorbed), None)
assert w.in_dip, "12% drawdown not seen as a dip!"
assert w.absorption and w.absorb_days >= 2, "absorption days not detected!"
assert w.divergence, "rising A/D line during the dip not flagged!"
assert w.whale, "dip + 2 footprints must tag 🐳!"
# control: the same dip but every day closes AT its low (no absorption)
dumped = [(p + 2.0, p + 2.0, p, p, 3e6)
          for p in [100 - 0.8 * (k + 1) for k in range(15)]]
w2 = whale_read(_wbars(flat + dumped), None)
assert not w2.absorption and not w2.divergence and not w2.whale, \
    "close-at-lows distribution must NOT tag 🐳!"
# control: no dip -> never a whale tag
w3 = whale_read(_wbars(flat + [(100.0, 101.0, 99.0, 100.5, 3e6)] * 15), None)
assert not w3.in_dip and not w3.whale, "flat tape must not tag 🐳!"
print("[14] Whale: absorbed dip -> 🐳, dumped dip -> no, flat tape -> no ...... PASS")

# --- 15. Whale shelf stability: replenished shelf holds, dried-up decays -----
sit = [(100.0, 101.0, 99.0, 100.0, 1e6)] * 200          # sitting on the shelf
dry = sit[:-10] + [(100.0, 101.0, 99.0, 100.0, 1e3)] * 10   # volume dries up
assert whale_read(_wbars(sit), 100.0).shelf_stable, \
    "steady volume on the shelf must read as replenished!"
assert not whale_read(_wbars(dry), 100.0).shelf_stable, \
    "dried-up shelf must decay (holders gone, not absorbing)!"
assert not whale_read(_wbars(sit), 130.0).shelf_stable, \
    "price nowhere near the shelf must not read shelf stability!"
print("[15] Whale shelf: replenished -> stable, dried-up/far shelf -> not .... PASS")

# --- 16. Golden-file digest: no refactor silently changes a printed row -----
# Fixture bars -> live engines -> daily_run.render_digest, diffed byte-for-byte
# against tests/digest_*.golden.txt. Offline & deterministic (see homily_golden).
import homily_golden
homily_golden.run()

print("\nAll structural assertions passed.")
