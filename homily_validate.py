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

# --- 17. Signals ledger (#13): idempotent per (date,ticker), snapshot shape --
# Reuses the golden fixtures -> live engines -> homily_ledger, into a temp dir
# so the committed ledger is never touched. Proves same-day re-runs OVERWRITE
# (no dupes, unlike the old refine log) and the snapshot carries every name.
import os, json, tempfile, datetime
import homily_ledger
from homily_golden import _up, _dn, _leader, BULL

with tempfile.TemporaryDirectory() as _td:
    _lg = os.path.join(_td, "signals.csv")
    _sn = os.path.join(_td, "snapshot.json")
    _hf = os.path.join(_td, "ledger_hash.json")
    _held = [_up("AAA"), _dn("BBB")]
    _disco = [_leader("LEAD")]
    _day = datetime.date(2026, 7, 8)
    _kw = dict(holdings_set={"AAA", "BBB"}, fund=lambda _t: "F:2/3",
               ledger=_lg, snapshot=_sn, hashfile=_hf)
    homily_ledger.record(_held, _disco, BULL, _day, **_kw)
    homily_ledger.record(_held, _disco, BULL, _day, **_kw)   # re-run same day
    _rows = homily_ledger._read_rows(_lg)
    assert len(_rows) == 3, f"same-day re-run must not dup: got {len(_rows)}"
    assert {r["ticker"] for r in _rows} == {"AAA", "BBB", "LEAD"}
    assert {r["held"] for r in _rows} == {"0", "1"}, "held flag must be 0/1"
    assert set(_rows[0].keys()) == set(homily_ledger.COLUMNS), "schema drift"
    _snap = json.load(open(_sn))
    assert _snap["date"] == "2026-07-08" and _snap["regime"]["label"] == "BULL"
    assert len(_snap["holdings"]) == 2 and len(_snap["discovery"]) == 1
    assert _snap["holdings"][0]["support"] is not None  # rich fields present
print("[17] Ledger: same-day re-run overwrites (no dupes), snapshot full ... PASS")

# --- 18. Ledger append-only guard (#62 / R3): retro-edits fail CI -----------
# A second day freezes the first; then any edit to that frozen row must make
# verify_history() raise. This is R3 enforced mechanically, not by convention.
with tempfile.TemporaryDirectory() as _td:
    _lg = os.path.join(_td, "signals.csv")
    _sn = os.path.join(_td, "snapshot.json")
    _hf = os.path.join(_td, "ledger_hash.json")
    _kw = dict(holdings_set={"AAA"}, fund=lambda _t: "F:2/3",
               ledger=_lg, snapshot=_sn, hashfile=_hf)
    homily_ledger.record([_up("AAA")], [], BULL, datetime.date(2026, 7, 7), **_kw)
    homily_ledger.record([_up("AAA")], [], BULL, datetime.date(2026, 7, 8), **_kw)
    homily_ledger.verify_history(ledger=_lg, hashfile=_hf)   # clean -> no raise
    _bad = homily_ledger._read_rows(_lg)
    for _r in _bad:                                          # tamper with day 1
        if _r["date"] == "2026-07-07":
            _r["close"] = "999999"
    homily_ledger._write_rows(_bad, _lg)
    try:
        homily_ledger.verify_history(ledger=_lg, hashfile=_hf)
        raise SystemExit("[18] FAIL: retro-edit of frozen history not caught")
    except AssertionError:
        pass
print("[18] Ledger guard: retro-edit of frozen history fails CI (R3) ...... PASS")

# --- 19. State-change alerts (#15): fire ONLY on transitions ----------------
# Pure ledger diff. A name that didn't move is silent; ⭐/🔵/🐳/🚀/regime
# transitions each surface exactly once; a brand-new ticker never alerts.
import homily_alerts
from homily_regime import Regime

_prev = [
    {"ticker": "AAA", "state": "HOLD", "whale": "0", "gates_ok": "0"},
    {"ticker": "BBB", "state": "BOTTOMING", "whale": "0", "gates_ok": "1"},
    {"ticker": "CCC", "state": "ACCUMULATE", "whale": "0", "gates_ok": "0"},
    {"ticker": "QUIET", "state": "HOLD", "whale": "0", "gates_ok": "0"},
]
_today = [
    {"ticker": "AAA", "state": "ACCUMULATE", "whale": True, "gates_ok": True},
    {"ticker": "BBB", "state": "HOLD", "whale": False, "gates_ok": False},
    {"ticker": "CCC", "state": "PULLBACK", "whale": False, "gates_ok": False},
    {"ticker": "QUIET", "state": "HOLD", "whale": False, "gates_ok": False},
    {"ticker": "NEW", "state": "ACCUMULATE", "whale": True, "gates_ok": True},
]
_bull = Regime("BULL", {}, "")
_al = homily_alerts.diff_alerts(_today, _bull, _prev, "BEAR")
assert any("REGIME flip: BEAR → BULL" in x for x in _al), "regime flip missed"
assert any("⭐ AAA entered ACCUMULATE" in x for x in _al)
assert any("🐳 AAA" in x for x in _al) and any("🚀 AAA" in x for x in _al)
assert any("⭐ CCC left ACCUMULATE" in x for x in _al)
assert any("🚀 BBB no longer passes" in x for x in _al)
assert not any("QUIET" in x for x in _al), "unchanged name must stay silent"
assert not any("NEW" in x for x in _al), "brand-new ticker must not alert"
# no prior regime + everyone unchanged -> empty (quiet day sends nothing)
_quiet = homily_alerts.diff_alerts(
    [{"ticker": "QUIET", "state": "HOLD", "whale": False, "gates_ok": False}],
    _bull, [{"ticker": "QUIET", "state": "HOLD", "whale": "0", "gates_ok": "0"}],
    None)
assert _quiet == [] and homily_alerts.format_alerts(_quiet, "2026-07-09") == ""
print("[19] Alerts: transitions fire once, quiet/new names silent ......... PASS")

# --- 20. HTML digest escaping (#34 F0 / R4): specials escaped, fallback safe -
# A hostile ticker (& < >) must come out as entities inside the HTML tags, and
# the plain-text fallback (strip_html) must remove every tag yet restore the
# real text — so a bad name degrades the digest, never drops it.
from daily_run import render_digest as _rd, strip_html
from homily_golden import _up as _up2, REFINE as _REF, TODAY as _TD

_hs, _hc, _hy = _up2("SAFE")
_hs.ticker = "A&B<C>"
_html = _rd([(_hs, _hc, _hy)], [], {}, None, _REF, [], _TD,
            fund=lambda _t: "f<x>")
assert "<code>A&amp;B&lt;C&gt;" in _html, "hostile ticker not HTML-escaped"
assert "A&B<C>" not in _html, "raw specials leaked into HTML body"
assert ("<blockquote expandable>" in _html
        and _html.rstrip().endswith("</blockquote>")), "footer not folded"
_plain = strip_html(_html)
assert not any(t in _plain for t in ("<b>", "<code>", "<blockquote", "<i>"))
assert "&amp;" not in _plain and "A&B<C>" in _plain, "fallback must restore text"
assert strip_html("<b>hi</b> x&amp;y") == "hi x&y"
print("[20] HTML digest: specials escaped, plain-text fallback strips tags . PASS")

# --- 21. Fetch hardening (#17 / R11): flaky retry, host rotation, threaded --
# A mocked opener fails twice then succeeds; fetch_daily must retry, rotate
# query1->query2, and return the SAME 6-tuple bars (R1 contract unchanged).
# screen() must fan out over threads yet stay deterministic and capture the
# one failing name in errs (never a silent short list).
import urllib.error as _ue
import homily_data

homily_data.BACKOFF = 0.0                       # no real sleeping in the test
homily_data.JITTER = 0.0
_PAYLOAD = json.dumps({"chart": {"result": [{
    "timestamp": [1700000000, 1700086400],
    "indicators": {"quote": [{"open": [10, 11], "high": [10.5, 11.5],
                              "low": [9.5, 10.5], "close": [10, 11],
                              "volume": [100, 110]}]}}]}}).encode()


class _Resp:
    def __init__(self, d): self._d = d
    def read(self): return self._d
    def __enter__(self): return self
    def __exit__(self, *a): return False


class _Flaky:
    def __init__(self, fail): self.fail, self.calls, self.hosts = fail, 0, []

    def __call__(self, req, timeout=None, context=None):
        self.hosts.append(req.full_url)
        self.calls += 1
        if self.calls <= self.fail:
            raise _ue.URLError("flaky")
        return _Resp(_PAYLOAD)


_op = _Flaky(2)
_bars = homily_data.fetch_daily("TEST", rng="1mo", opener=_op)
assert _bars[0][4] == 10 and _bars[1][4] == 11 and len(_bars[0]) == 6, "bars contract"
assert _op.calls == 3, f"should retry to success, got {_op.calls} calls"
assert "query1" in _op.hosts[0] and "query2" in _op.hosts[1], "no host rotation"
try:
    homily_data.fetch_daily("TEST", opener=_Flaky(99))
    raise SystemExit("[21] FAIL: exhausted retries must raise")
except _ue.URLError:
    pass

import daily_run
from homily_golden import _bars as _mkbars
_up_bars = _mkbars([100 * 1.003 ** i for i in range(900)], [1e6] * 900)


def _stub_fetch(sym, rng="5y"):
    if sym == "BAD":
        raise RuntimeError("boom")
    return _up_bars, [b[4] for b in _up_bars]


_orig_fetch = daily_run.fetch_series
daily_run.fetch_series = _stub_fetch
try:
    _errs = []
    _res = daily_run.screen({"AAA": "AAA", "BAD": "BAD", "BBB": "BBB"},
                            _errs, [100.0] * 900)
finally:
    daily_run.fetch_series = _orig_fetch
assert _errs == ["BAD"], f"failing fetch must land in errs, got {_errs}"
assert [x[0].ticker for x in _res] == ["AAA", "BBB"], "threaded screen not sorted"
print("[21] Fetch: retry+rotation, contract intact, threaded screen sorted . PASS")

# --- 22. Granularity guard: Yahoo range=max silently returns 1mo bars -------
# (found 2026-07-10: D-63 Step 2 ran signals on monthly bars). fetch_daily
# must (a) request epoch period params — not the max token — so history stays
# daily, and (b) refuse any response whose meta says the bars aren't 1d.
_ok_url = _Flaky(0)
homily_data.fetch_daily("TEST", rng="max", opener=_ok_url)
assert "period1=0" in _ok_url.hosts[0] and "range=max" not in _ok_url.hosts[0], \
    "rng=max must use epoch period params (range=max degrades to 1mo bars)"
_COARSE = json.dumps({"chart": {"result": [{
    "meta": {"dataGranularity": "1mo"},
    "timestamp": [1700000000],
    "indicators": {"quote": [{"open": [10], "high": [10.5], "low": [9.5],
                              "close": [10], "volume": [100]}]}}]}}).encode()


class _CoarseResp(_Flaky):
    def __call__(self, req, timeout=None, context=None):
        self.hosts.append(req.full_url)
        return _Resp(_COARSE)


try:
    homily_data.fetch_daily("TEST", rng="max", opener=_CoarseResp(0))
    raise SystemExit("[22] FAIL: coarse (non-1d) bars must raise")
except ValueError:
    pass
print("[22] Granularity guard: max=epoch params, non-1d bars refused ........ PASS")

# --- 23. Total-return correctness (#18 / R1): adjclose is a PARALLEL series --
# fetch_series must hand back the untouched raw 6-tuple bars plus dividend-
# adjusted closes at the same index. RS12/RS6 move to the adjusted series (a
# payer's total return beats its price return, so RS12 raw < RS12 adj); chip
# levels, $-volume and the G4 basis test stay on RAW prices — a level has to be
# a price you could have traded at. Falls back to raw when Yahoo omits adjclose.
_ADJ_PAYLOAD = json.dumps({"chart": {"result": [{
    "timestamp": [1700000000, 1700086400],
    "indicators": {
        "quote": [{"open": [10, 11], "high": [10.5, 11.5],
                   "low": [9.5, 10.5], "close": [10, 11],
                   "volume": [100, 110]}],
        "adjclose": [{"adjclose": [9.8, 11]}]}}]}}).encode()


class _AdjResp(_Flaky):
    def __call__(self, req, timeout=None, context=None):
        self.hosts.append(req.full_url)
        return _Resp(_ADJ_PAYLOAD)


_b, _a = homily_data.fetch_series("TEST", opener=_AdjResp(0))
assert [x[4] for x in _b] == [10, 11], "raw closes must survive untouched (R1)"
assert len(_b[0]) == 6 and len(_a) == len(_b), "bars contract / adj alignment"
assert _a == [9.8, 11], f"adjclose not parsed, got {_a}"
_b2, _a2 = homily_data.fetch_series("TEST", opener=_Flaky(0))   # no adjclose
assert _a2 == [x[4] for x in _b2], "missing adjclose must fall back to raw"

# A dividend payer: same tape, but each past close discounted by the dividends
# paid since. The benchmark is a flat non-payer, so the whole RS12 shift is the
# payer's own yield.
from homily_conviction import GATE_RS12
_N, _DIV = 600, 0.0002                     # ~5%/yr paid continuously
_pay_closes = [100 * 1.0006 ** i for i in range(_N)]
_pay_bars = _mkbars(_pay_closes, [1e6] * _N)
_pay_adj = [c * (1 - _DIV) ** (_N - 1 - i)
            for i, c in enumerate(_pay_closes)]
_bench = [100.0] * _N
_sig = danny_signal("PAY", _pay_bars)
_c_raw = conviction(_sig, _pay_bars, _bench)
_c_adj = conviction(_sig, _pay_bars, _bench, adj=_pay_adj, spy_adj=_bench)
assert _c_raw.rs12 < _c_adj.rs12, \
    f"payer's total return must beat its price return: {_c_raw.rs12} !< {_c_adj.rs12}"
# rs6 isn't on the dataclass; it shows up as the +5 bonus inside rel strength
assert (_c_raw.parts["rel strength"], _c_adj.parts["rel strength"]) == (0, 15), \
    "RS6 must migrate to adjusted closes too (10 for RS12>=20, +5 for RS6>=10)"
assert _c_raw.dvol == _c_adj.dvol, "$-volume must stay on raw prices"
assert (_c_raw.parts["structure"] == _c_adj.parts["structure"]
        and _c_raw.parts["trend"] == _c_adj.parts["trend"]), \
    "only relative strength may move; basis/trend read raw prices"
assert ("G4 basis" in _c_raw.gates_failed) == ("G4 basis" in _c_adj.gates_failed), \
    "G4 basis-vs-POC must be decided on the raw close (levels are tradeable)"
# and the whole point: dividends can carry a payer over the G3 leader gate
assert conviction(_sig, _pay_bars, _bench).rs12 < GATE_RS12 <= _c_adj.rs12, \
    "fixture should straddle G3 — otherwise the test proves nothing"
print("[23] Total return: adj parallel to raw, RS12 raw < adj, levels raw . PASS")

# --- 24. Corporate-action sanity check (#19) --------------------------------
# A mis-adjusted 10:1 split must be caught from the tape alone, and the digest
# must answer it by dropping the levels — never the name. Clean tapes, and the
# same gap left far enough back that the chip decay has buried it, stay silent.
import homily_corp
from homily_golden import split_bars, _split, _leader, _whale, REFINE, \
    TODAY, _fund

_split_bars = split_bars(ratio=10, at=880, n=900)
_hit = homily_corp.corp_action_bar(_split_bars)
assert _hit == _split_bars[880][0], f"10:1 split not detected, got {_hit}"
assert homily_corp.corp_action_bar(_mkbars([100 * 1.003 ** i for i in range(900)],
                                           [1e6] * 900)) is None, \
    "a clean uptrend must not be flagged"
# reverse split: price x10, volume /10 — the plan named only the volume SPIKE,
# but the collapse is the same event from the other side (see homily_corp)
_rev = _mkbars([100 * 1.003 ** i * (10 if i >= 880 else 1) for i in range(900)],
               [1e6 / 10 if i >= 880 else 1e6 for i in range(900)])
assert homily_corp.corp_action_bar(_rev) == _rev[880][0], "reverse split missed"
# a 45%+ move on ORDINARY volume is a crash, not a corporate action
_crash = _mkbars([100 * 1.003 ** i * (0.5 if i >= 880 else 1) for i in range(900)],
                 [1e6] * 900)
assert homily_corp.corp_action_bar(_crash) is None, "volume must gate the flag"
# and the gap ages out of the window once the chips it poisoned have decayed
assert homily_corp.corp_action_bar(split_bars(at=700, n=900)) is None, \
    "a gap older than the lookback must stop suspending levels"

# the digest answer: state row survives, every price disappears, and the 🐳
# add-tier can never be earned off a shelf we just said we don't trust
_srow = daily_run.fmt_row(_split("SPLT")[0], corp=_hit)
assert "⚠️ levels suspended" in _srow and str(_hit) in _srow, "no suspension note"
assert "⚪" in _srow and "wk WHITE/0" in _srow, "state row must survive (#19)"
assert not any(t in _srow for t in ("add ", "POC ", "res ", "in profit",
                                    "VH ", "🎯", "🐳")), \
    f"a suspended row must print no chip-derived price: {_srow}"
_clean = daily_run.fmt_row(_split("SPLT")[0])
assert "POC " in _clean and "VH " in _clean, "unsuspended rows keep their levels"
# rocket gates never read the histogram, so the name stays — only its zone goes
_lead, _lc, _ = _leader("LEAD")
_rrow = daily_run.fmt_rocket(_lead, _lc, False, fund=_fund, corp=_hit)
assert "score" in _rrow and "add " not in _rrow, f"rocket zone not suspended: {_rrow}"
# the 🐳 whale-dip promotion is defined by distance to a chip shelf: a suspect
# name must not reach the discovery list on a shelf we just disowned
_whl = _whale("WHL")
assert daily_run.whale_dip(_whl[0]), "fixture should be a whale-dip"
_shown = daily_run.render_digest([], [_whl], {}, None, REFINE, [], TODAY,
                                 fund=_fund)
_hidden = daily_run.render_digest([], [_whl], {}, None, REFINE, [], TODAY,
                                  fund=_fund, suspect={"WHL": _hit})
assert "WHL" in _shown and "WHL" not in _hidden, \
    "a suspect name must not be promoted into the 🐳 discovery tier"
print("[24] Corp action: 10:1 + reverse split caught, crash isn't, levels off  PASS")

# --- 25. RS12-rank column (#24 follow-up): measurement only, no behaviour ---
# change. Candidate set mirrors homily_selection_backtest._screen precedence
# (⭐ ACCUMULATE if any today, else 🔵 BOTTOMING fallback); rank is 12m RS
# descending among that set; everyone else gets no rank. This is the ledger
# column the promotion's forward-check (PRD §5j) will read from July onward.
def _st(ticker, state, rs12):
    return {"ticker": ticker, "state": state, "rs12": rs12}


_today25 = [_st("HI", "ACCUMULATE", 0.30), _st("LO", "ACCUMULATE", 0.05),
            _st("MID", "ACCUMULATE", 0.15), _st("HOLDER", "HOLD", 0.99),
            _st("BOT", "BOTTOMING", 0.10)]
_ranks25 = homily_ledger.rs12_ranks(_today25)
assert _ranks25 == {"HI": 1, "MID": 2, "LO": 3, "HOLDER": None, "BOT": None}, \
    f"⭐ present must rank only ⭐, best RS12 first: {_ranks25}"
# no ⭐ today -> fall back to ranking 🔵, exactly like _screen's `cands or backs`
_nobull25 = [_st("B1", "BOTTOMING", 0.20), _st("B2", "BOTTOMING", 0.40),
             _st("H1", "HOLD", 5.0)]
assert homily_ledger.rs12_ranks(_nobull25) == {"B1": 2, "B2": 1, "H1": None}, \
    "no ⭐ today must rank 🔵 candidates, not leave everyone unranked"
# neither state present -> nobody ranked (not an error, just an empty candidate set)
assert homily_ledger.rs12_ranks([_st("X", "HOLD", 1.0)]) == {"X": None}
print("[25] RS12 rank: ⭐ else 🔵 fallback, best-RS12-first, others blank .... PASS")

# --- 26. Position-aware book math (#27): % of book, bucket, cap note -------
# Fixture book on a fixture price map (unit-level), then a real render_digest
# pass (positions=None default is unaffected; a supplied book annotates only
# its own tracked, USD, non-Bucket-A names — the golden fixtures in check
# [16] use tickers no real holdings.json would ever contain, so they stay
# byte-exact without this check having to touch them).
import homily_positions

_pos26 = {
    "IDX": {"yahoo": "IDX", "shares": 10, "cost": 100, "bucket": "A"},
    "HK": {"yahoo": "HK.HK", "shares": 100, "cost": 50, "currency": "HKD"},
    "SAFE": {"yahoo": "SAFE", "shares": 1, "cost": 10},
    "HOT": {"yahoo": "HOT", "shares": 1, "cost": 10},
    "CORE": {"yahoo": "CORE", "shares": 1, "cost": 10, "bucket": "B"},
}
_px26 = {"IDX": 100, "HK": 50, "SAFE": 2, "HOT": 20, "CORE": 20}
# book value = SAFE(2) + HOT(20) + CORE(20) = 42; bucket-A (IDX) and non-USD
# (HK) are excluded from the denominator (R12)
_bv26 = homily_positions.stock_book_value(_pos26, _px26)
assert abs(_bv26 - 42.0) < 1e-9, f"bucket-A/non-USD must be excluded: {_bv26}"
assert homily_positions.position_view("IDX", _pos26, _px26, _bv26) is None, \
    "bucket A must not get a book %"
assert homily_positions.position_view("HK", _pos26, _px26, _bv26) is None, \
    "non-USD position must not get a book % (R12)"
_safe26 = homily_positions.position_view("SAFE", _pos26, _px26, _bv26)
assert abs(_safe26["pct"] - 100 * 2 / 42) < 1e-6 and _safe26["cap_note"] is None
_hot26 = homily_positions.position_view("HOT", _pos26, _px26, _bv26)
assert _hot26["cap_note"] == "OVER CAP — no more adds", \
    f"over 10% of book must warn: {_hot26}"
_core26 = homily_positions.position_view("CORE", _pos26, _px26, _bv26)
assert _core26["pct"] > 10 and _core26["cap_note"] is None, \
    "bucket B (earned core) never gets a cap note, however big it's grown"

from homily_golden import _up, _dn, REFINE, TODAY, _fund

_row_plain = daily_run.fmt_row(_up("AAA")[0])
_row_pos = daily_run.fmt_row(_up("AAA")[0], pos=_hot26)
assert "% of book" not in _row_plain, "untracked names print no book %"
assert "% of book" in _row_pos and "OVER CAP" in _row_pos, \
    f"tracked + over-cap row must show both: {_row_pos}"

_bigpos26 = {"AAA": {"yahoo": "AAA", "shares": 1000, "cost": 1}}
_out26 = daily_run.render_digest([_up("AAA"), _dn("BBB")], [], {}, BULL,
                                 REFINE, [], TODAY, fund=_fund,
                                 positions=_bigpos26)
_aaa_line = next(l for l in _out26.split("\n") if "AAA" in l)
_bbb_line = next(l for l in _out26.split("\n") if "BBB" in l)
assert "100.0% of book" in _aaa_line and "OVER CAP" in _aaa_line, \
    f"the sole tracked position must be 100% of book, over cap: {_aaa_line}"
assert "% of book" not in _bbb_line, "an untracked name must not be annotated"
print("[26] Position math: % of book, bucket A/B excluded, cap note fires . PASS")


# --- 27. Buy-day copilot (#31): budget in -> orders out, caps respected ----
# Fixture book + fixture ⭐ states through the PURE plan() (no env/clock/
# network), then the detection rule, the render, and the T2 basket CSV.
# Info-only feature: nothing here places an order (PRD §7).
import csv
import homily_buyday

# detection (D-31): first run of the month = no PRIOR ledger row this month;
# today's own rows don't count (same-day re-run stays a buy day); an empty
# ledger is conservatively NOT a buy day
_d27 = datetime.date(2026, 8, 3)
assert not homily_buyday.is_buy_day(_d27, []), "empty ledger: not a buy day"
assert homily_buyday.is_buy_day(_d27, [{"date": "2026-07-31"}]), \
    "prior-month rows only: first run of August IS the buy day"
assert homily_buyday.is_buy_day(_d27, [{"date": "2026-08-03"}]), \
    "same-day re-run must still be the buy day (idempotent)"
assert not homily_buyday.is_buy_day(_d27, [{"date": "2026-08-01"}]), \
    "a prior run this month: not a buy day"

_pos27 = {
    "CSPX": {"yahoo": "CSPX.L", "shares": 1, "cost": 100, "bucket": "A"},
    "BIG": {"yahoo": "BIG", "shares": 90, "cost": 5},
    "SML": {"yahoo": "SML", "shares": 1, "cost": 5},
}
def _bs(tk, close, ftag, rs12, state="ACCUMULATE"):
    return {"ticker": tk, "state": state, "close": close,
            "ftag": ftag, "rs12": rs12}
_yh27 = {"CSPX": "CSPX.L", "BIG": "BIG", "SML": "SML", "NEW": "NEW",
         "0700": "0700.HK"}
_st27 = [_bs("CSPX", 100, "F:—", 0, state="HOLD"),
         _bs("BIG", 10, "F:3/3", 5), _bs("SML", 10, "F:1/3", 50),
         _bs("NEW", 30, "F:2/3", 1), _bs("0700", 50, "F:—", 99)]

# ordering (PLAYBOOK §3.4 as promoted — #24, 2026-07-12): RS12 descending,
# no F grouping (SML's F:1/3 no longer demotes it below the F:2+ names);
# the HK name splits off as manual (R12), however strong its RS
_usd27, _man27 = homily_buyday.star_candidates(_st27, _pos27, _yh27)
assert [s["ticker"] for s in _usd27] == ["SML", "BIG", "NEW"], \
    f"RS12 descending (#24 promoted): {[s['ticker'] for s in _usd27]}"
assert [s["ticker"] for s in _man27] == ["0700"], "non-USD ⭐ -> manual (R12)"

# SRS covers the index (PRD §9.4): whole $1,000 to stars. Stock book =
# BIG 900 + SML 10 = 910 (bucket A out); post-deploy denom 1910 -> 25% cap
# (#92, 2026-07-12) $477.50/name. BIG (at $900) is STILL fully capped —
# the cap keeps binding, just later; equal split 333.33/name, BIG's share
# redistributes to SML/NEW (500 each), SML caps at 477.50-10=467.50 -> 46
# shares, NEW caps at 477.50 -> 15 whole shares; the rest is leftover.
_p27 = homily_buyday.plan(1000, _st27, _pos27, "BULL",
                          srs_covers_index=True, yahoo=_yh27)
assert _p27["mode"] == "normal" and _p27["index_amt"] == 0
_ord27 = {tk: n for tk, n, _px, _nt in _p27["orders"]}
assert _ord27 == {"SML": 46, "NEW": 15}, f"cap + whole-share floor: {_ord27}"
assert any(s.startswith("BIG:") for s in _p27["skipped"]), \
    "a name at the 25% cap is skipped loudly, not silently dropped"
assert abs(_p27["spent"] - 910) < 1e-9 and abs(_p27["leftover"] - 90) < 1e-9
assert _p27["manual"] == ["0700"]

# normal path: half to Bucket A (5 × CSPX@100), half to stars
_pn27 = homily_buyday.plan(1000, _st27, _pos27, "BULL", yahoo=_yh27)
assert _pn27["orders"][0][:2] == ("CSPX", 5) and _pn27["index_amt"] == 500

# no ⭐ -> full amount to Bucket A (§3.5); 🐻 -> same reroute (§4.6)
_flat27 = [_bs("CSPX", 100, "F:—", 0, state="HOLD")]
for _states, _reg, _mode in ((_flat27, "BULL", "nostars"),
                             (_st27, "BEAR", "bear")):
    _px27 = homily_buyday.plan(1000, _states, _pos27, _reg, yahoo=_yh27)
    assert _px27["mode"] == _mode and _px27["orders"] == \
        [("CSPX", 10, 100, "Bucket A index leg")], \
        f"{_mode}: entire budget must go to the index sleeve"

# render leads with 🛒, prints IBKR-ready lines, never places (§7)
_txt27 = homily_buyday.render(_p27, _d27)
assert _txt27.startswith("🛒") and "BUY  46 SML" in _txt27 \
    and "printed, never placed" in _txt27 and "manual: 0700" in _txt27, _txt27

# T2 basket CSV: same orders, IBKR BasketTrader header, USD-only rows
with tempfile.TemporaryDirectory() as _tmp27:
    _path27 = homily_buyday.write_basket(_p27, _d27, docs=_tmp27)
    assert os.path.basename(_path27) == "orders_2026-08.csv"
    _rows27 = list(csv.reader(open(_path27)))
    assert _rows27[0][:4] == ["Action", "Quantity", "Symbol", "SecType"]
    assert (sorted(r[2] for r in _rows27[1:]) == ["NEW", "SML"]
            and all(r[5] == "USD" for r in _rows27[1:])), _rows27
    # no orders -> no file (a bear month with no CSPX price writes nothing)
    assert homily_buyday.write_basket(
        {"orders": []}, _d27, docs=_tmp27) is None

# no BUY_BUDGET_USD configured -> the copilot stays dark, digest unchanged
os.environ.pop("BUY_BUDGET_USD", None)
assert homily_buyday.buyday_block(_st27, _pos27, None, _d27) == ("", None)
print("[27] Buy-day copilot: detection, RS12-top3 order, 10% cap, basket CSV  PASS")

# --- 28. Chart cards (#35): valid PNG, deterministic pixels, top-3 pick ----
# The gate D-35 pre-committed: a deterministic pixel-hash on fixture bars.
# Hashes pin the RAW RGB buffer (compressed PNG bytes aren't guaranteed
# stable across zlib builds). A DELIBERATE visual change re-pins them: run
# `python3 homily_png.py`, eyeball the rendered files, paste the two hashes.
import struct
import zlib
import homily_png
from homily_golden import _bottoming

_bars28u = _mkbars([100 * 1.003 ** i for i in range(900)], [1e6] * 900)
_bars28d = _mkbars([100 * 0.997 ** i for i in range(900)], [1e6] * 900)
_sig28u, _sig28d = _up("UPP")[0], _dn("DWN")[0]

# structural: signature, IHDR 900×500 RGB, chunk CRCs, filter-0 scanlines
_png28 = homily_png.chart_png("UPP", _bars28u, _sig28u)
assert _png28[:8] == b"\x89PNG\r\n\x1a\n", "PNG signature"
assert struct.unpack(">II", _png28[16:24]) == (900, 500), "IHDR dims"
_pos28, _idat28 = 8, b""
while _pos28 < len(_png28):
    _ln, _typ = struct.unpack(">I4s", _png28[_pos28:_pos28 + 8])
    _dat = _png28[_pos28 + 8:_pos28 + 8 + _ln]
    (_crc,) = struct.unpack(">I", _png28[_pos28 + 8 + _ln:_pos28 + 12 + _ln])
    assert zlib.crc32(_typ + _dat) == _crc, f"bad CRC in {_typ}"
    if _typ == b"IDAT":
        _idat28 += _dat
    _pos28 += 12 + _ln
_raw28 = zlib.decompress(_idat28)
_stride28 = 1 + 900 * 3
assert len(_raw28) == 500 * _stride28, "scanline payload size"
assert all(_raw28[i] == 0 for i in range(0, len(_raw28), _stride28)), \
    "every scanline must use filter 0"

# determinism + the pinned pixel hashes (the actual gate)
_cvU = homily_png.chart_canvas("UPP", _bars28u, _sig28u)
_cvU2 = homily_png.chart_canvas("UPP", _bars28u, _sig28u)
assert homily_png.pixel_hash(_cvU) == homily_png.pixel_hash(_cvU2), \
    "same inputs must render identical pixels"
_cvD = homily_png.chart_canvas("DWN", _bars28d, _sig28d)
_want28 = {
    "UPP": "8f28551d8a56cd03048dfbaa5463453ca96a73d1d93a99d3074e1d7975a5460a",
    "DWN": "949dbe1d39b1291b60917c68cddd41c0c336a611b7699ca6f80b7c575bf1bbea",
}
for _tk28, _cv28 in (("UPP", _cvU), ("DWN", _cvD)):
    _got28 = homily_png.pixel_hash(_cv28)
    assert _got28 == _want28[_tk28], (
        f"{_tk28} chart pixels changed: {_got28}\n"
        "If the visual change was DELIBERATE, re-pin: python3 homily_png.py, "
        "eyeball the output files, paste the printed hashes here.")

# top-3 selection: ⭐ then 🔵 then 🎯-at-support by conviction, suspects out
_upA, _upB = _up("AAA"), _up("BBB")
_bot28, _dip28 = _bottoming("BOT"), _dn("DIP")
assert _dip28[0].add_zone and _dip28[0].chips.last <= _dip28[0].add_zone[1], \
    "fixture drift: _dn must sit at its add zone (the 🎯 case)"
_picked = [s.ticker for s, _c in
           daily_run.select_charts([_upA, _upB, _bot28, _dip28])]
assert _picked == ["AAA", "BBB", "BOT"], \
    f"⭐⭐ then 🔵 must beat the ⚪ 🎯 for the 3 slots: {_picked}"
_picked = [s.ticker for s, _c in
           daily_run.select_charts([_upA, _upB, _bot28, _dip28],
                                   suspect={"BBB": "2026-01-02"})]
assert _picked == ["AAA", "BOT", "DIP"], \
    f"corp-suspect names never get a chart (#19): {_picked}"
_holdonly = [s.ticker for s, _c in daily_run.select_charts([_dn("ZZZ")])]
assert _holdonly == ["ZZZ"], "a ⚪ AT its add zone is actionable (🎯)"
print("[28] Chart cards: PNG valid, pixel-hash pinned, top-3 ⭐/🔵/🎯 pick . PASS")

# --- 29. Provenance column (#64): origin logged per row, END-appended ------
# The scorecard's referee split (screen vs owner-request vs holding). Pure
# measurement: no behaviour change anywhere; unknown names default to
# "owner-request" so nothing can masquerade as mechanically screened. NB the
# column append changed the guard-#62 hash serialisation — the checkpoint was
# regenerated DELIBERATELY in the same commit that added the column.
assert homily_ledger.COLUMNS.index("origin") \
    > homily_ledger.COLUMNS.index("rs12_rank"), \
    "append-only-columns rule: origin was appended after the earlier columns"

_sigU29, _convU29, _ = _up("ORG")
_stH29 = homily_ledger.state_of(_sigU29, _convU29, True, fund=_fund,
                                origin="holding")
_stD29 = homily_ledger.state_of(_sigU29, _convU29, False, fund=_fund)
assert _stH29["origin"] == "holding" and _stD29["origin"] == "owner-request", \
    "origin must land in the state dict; default is owner-request"
_d29 = datetime.date(2026, 7, 11)
assert homily_ledger.csv_row(_stH29, _d29)["origin"] == "holding", \
    "origin must flatten into the CSV row"

# round-trip through the real append/verify path in a sandbox ledger; a
# second day advances the checkpoint over origin-bearing rows and history
# still verifies (the hash covers the new column from day one here)
with tempfile.TemporaryDirectory() as _tmp29:
    _lg29 = os.path.join(_tmp29, "ledger.csv")
    _hf29 = os.path.join(_tmp29, "hash.json")
    homily_ledger.append_rows([homily_ledger.csv_row(_stH29, _d29)], _d29,
                              ledger=_lg29, hashfile=_hf29)
    _d29b = datetime.date(2026, 7, 12)
    homily_ledger.append_rows([homily_ledger.csv_row(_stD29, _d29b)], _d29b,
                              ledger=_lg29, hashfile=_hf29)
    _rows29 = homily_ledger._read_rows(_lg29)
    assert [r["origin"] for r in _rows29] == ["holding", "owner-request"], \
        f"origin must persist through the ledger round-trip: {_rows29}"
    homily_ledger.verify_history(ledger=_lg29, hashfile=_hf29)

# record()-level fallback: unmapped held ticker -> "holding", unmapped
# watch/discovery ticker -> "owner-request"; explicit map wins
_o29 = {"MECH": "screen"}
_org29 = lambda tk, held: (_o29.get(tk)
                           or ("holding" if held else "owner-request"))
assert _org29("MECH", False) == "screen" and _org29("AAA", True) == "holding" \
    and _org29("ASML", False) == "owner-request"
# and the real wiring: daily_run's ORIGINS map tags book vs hand-list
assert daily_run.ORIGINS.get("AAPL") == "holding" \
    and daily_run.ORIGINS.get("ASML") == "owner-request" \
    and daily_run.ORIGINS.get("MSFT") == "owner-request", \
    "daily_run.ORIGINS must tag holdings vs the hand-picked list"
print("[29] Provenance: origin column END-appended, defaults honest ....... PASS")

# --- 30. Bear-readiness rehearsal (#30): §4 order exactly, info-only -------
# Fixture book drives every §4 step-3 branch: (a) ⚪+F:0-1 sold whole,
# (b) remaining ⚪ largest-first until satellites ≤10% of the shrinking
# book, (c) ⭐/🟢 satellites kept, Bucket A/B never listed, non-USD names
# in the list by state but outside the % math (R12).
import homily_bearready

assert homily_bearready.first_monday(datetime.date(2026, 7, 6)) \
    and homily_bearready.first_monday(datetime.date(2026, 8, 3)) \
    and not homily_bearready.first_monday(datetime.date(2026, 7, 13)) \
    and not homily_bearready.first_monday(datetime.date(2026, 7, 7)), \
    "first Monday = weekday 0 AND day ≤ 7"

_pos30 = {
    "IDX": {"yahoo": "IDX", "shares": 1, "cost": 1, "bucket": "A"},
    "CORE": {"yahoo": "CORE", "shares": 1, "cost": 1, "bucket": "B"},
    "WEAK": {"yahoo": "WEAK", "shares": 1, "cost": 1},   # ⚪ F:0/3 -> (a)
    "BIGC": {"yahoo": "BIGC", "shares": 4, "cost": 1},   # ⚪ F:2/3, largest
    "SMLC": {"yahoo": "SMLC", "shares": 1, "cost": 1},   # ⚪ F:2/3, small
    "STAR": {"yahoo": "STAR", "shares": 1, "cost": 1},   # ⭐ -> keep note
    "HK": {"yahoo": "HK.HK", "shares": 1, "cost": 1, "currency": "HKD"},
}
def _brs(tk, state, ftag, held=True, close=100.0):
    return {"ticker": tk, "state": state, "ftag": ftag, "held": held,
            "close": close}
_st30 = [_brs("IDX", "HOLD", "F:—"), _brs("CORE", "HOLD", "F:3/3"),
         _brs("WEAK", "CAUTION", "F:0/3"), _brs("BIGC", "CAUTION", "F:2/3"),
         _brs("SMLC", "CAUTION", "F:2/3"), _brs("STAR", "ACCUMULATE", "F:2/3"),
         _brs("HK", "CAUTION", "F:—")]
# book (B+C, USD) = CORE 100 + WEAK 100 + BIGC 400 + SMLC 100 + STAR 100 = 800
_plan30 = homily_bearready.readiness(_st30, _pos30)
assert abs(_plan30["book"] - 800) < 1e-9
assert abs(_plan30["sat_pct"] - 100 * 700 / 800) < 1e-6, "C/book"
assert _plan30["sell_all"] == ["WEAK"], "step (a): ⚪ + F:0-1, all of it"
# step (b): after (a), sats 600 book 700; sell BIGC -> sats 200 book 300
# (still >10%); sell SMLC -> sats 100 book 200 (>10%); STAR is not ⚪, so
# the list is the two ⚪ names, largest first, and (c) notes STAR
assert _plan30["sell_until"] == ["BIGC", "SMLC"], _plan30["sell_until"]
assert _plan30["keep"] == ["STAR"], "step (c): ⭐/🟢 satellite noted, kept"
assert _plan30["offbook"] == ["HK (b)"], "non-USD ⚪ listed by state (R12)"
# F:— must not count as weak (unknown ≠ failed)
assert not homily_bearready._fweak("F:—") and homily_bearready._fweak("F:1/3")
# a small-enough ⚪ tail stops the (b) list early
_pos30b = {"CORE": {"yahoo": "C", "shares": 19, "cost": 1},
           "TINY": {"yahoo": "T", "shares": 1, "cost": 1}}
_plan30b = homily_bearready.readiness(
    [_brs("CORE", "HOLD", "F:3/3"), _brs("TINY", "CAUTION", "F:2/3")],
    {**_pos30b, "CORE": {**_pos30b["CORE"], "bucket": "B"}})
assert _plan30b["sell_until"] == [], \
    "satellites already ≤10% of book -> nothing forced in step (b)"
_txt30 = homily_bearready.render(_plan30, margin_zero=False, srs_covers=True)
assert "margin loan outstanding" in _txt30 and "BEAR READINESS" in _txt30 \
    and "info only" in _txt30 and "never sold" in _txt30, _txt30
_txt30z = homily_bearready.render(_plan30, margin_zero=True, srs_covers=False)
assert "zero, confirmed" in _txt30z and "index leg unconfirmed" in _txt30z
# render_digest carries the block only when supplied; default digest unchanged
_out30 = daily_run.render_digest([_up2("AAA")], [], {}, BULL, _REF, [], _TD,
                                 fund=_fund, bearready=_txt30z)
assert "BEAR READINESS" in _out30
print("[30] Bear readiness: §4 a/b/c order, margin+SRS nags, first-Monday . PASS")

# --- 31. Promotion registry (#69) + whale_rank column (#80) ---------------
# The 2026-10-01 decision must be a program's output: registry entries are
# structurally complete (no promotion without a pre-registered demotion
# rule), the forward-checker PASSes/FAILs/defers on synthetic ledgers, and
# the whale_rank column ranks by footprint intensity with RS12 tiebreak.
import homily_promotions

homily_promotions.verify_registry()          # every entry names its pieces
_ids31 = {e["id"] for e in homily_promotions.load_registry()}
assert "rs12-top3" in _ids31, "the §5j promotion candidate must be on file"

def _wst(tk, state, a, d, sh, rs):
    return {"ticker": tk, "state": state, "absorption": a, "divergence": d,
            "shelf_stable": sh, "rs12": rs}
_w31 = [_wst("HOT", "ACCUMULATE", True, True, True, 0.1),
        _wst("MID", "ACCUMULATE", True, False, False, 9.9),
        _wst("TIE", "ACCUMULATE", True, True, False, 0.5),
        _wst("TIE2", "ACCUMULATE", True, True, False, 0.4),
        _wst("HOLD", "HOLD", True, True, True, 9.9)]
_wr31 = homily_ledger.whale_ranks(_w31)
assert _wr31 == {"HOT": 1, "TIE": 2, "TIE2": 3, "MID": 4, "HOLD": None}, \
    f"intensity desc, RS12 tiebreak, non-candidates blank: {_wr31}"
assert homily_ledger.COLUMNS.index("whale_rank") \
    > homily_ledger.COLUMNS.index("origin"), "END-appended (#80)"

# forward-checker on a synthetic ledger: top-3 name compounds +1%/row,
# other name flat -> PASS; swap the ranks -> FAIL; tiny window -> INSUFFICIENT
def _rows31(n, top_rank, other_rank):
    rows = []
    for i in range(n):
        d = (datetime.date(2026, 7, 13) + datetime.timedelta(days=i)).isoformat()
        rows.append({"date": d, "ticker": "TOP", "state": "ACCUMULATE",
                     "close": f"{100 * 1.01 ** i:.4f}", "rs12_rank": top_rank})
        rows.append({"date": d, "ticker": "OTH", "state": "ACCUMULATE",
                     "close": "100", "rs12_rank": other_rank})
    return rows
_e31 = {"id": "fix", "forward_check": {
    "rank_column": "rs12_rank", "window": ["2026-07-13", "2026-12-31"],
    "horizon_rows": 5, "min_measured_rows": 10, "criterion": "test"}}
_r31 = homily_promotions.forward_check(_e31, _rows31(30, "1", "4"))
assert _r31["status"] == "PASS" and _r31["n_top"] == 25 \
    and _r31["mean_top"] > _r31["mean_other"], _r31
assert homily_promotions.forward_check(
    _e31, _rows31(30, "4", "1"))["status"] == "FAIL", "inverted ranks: FAIL"
assert homily_promotions.forward_check(
    _e31, _rows31(8, "1", "4"))["status"] == "INSUFFICIENT", \
    "too few measured rows must defer, never decide"
print("[31] Promotions: registry complete, checker PASS/FAIL/defer, 🐳rank . PASS")

# --- 32. Missed-run detector (#70): planted gap found, weekends aren't -----
# #16 catches a run that FAILS; this catches one that never STARTS. Rows on
# Mon 2026-07-06 and Wed 2026-07-08; Tue is a hole, Thu is a hole, the
# weekend is never expected, and today itself is not yet expected.
_rows32 = [{"date": "2026-07-06", "ticker": "A"},
           {"date": "2026-07-08", "ticker": "A"},
           {"date": "2026-07-08", "ticker": "B"}]
_cov32 = homily_ledger.coverage_of(_rows32, datetime.date(2026, 7, 10))
assert _cov32["missing"] == ["2026-07-07", "2026-07-09"] \
    and _cov32["expected"] == 4 and _cov32["have"] == 2, _cov32
_cov32b = homily_ledger.coverage_of(_rows32 + [
    {"date": "2026-07-07", "ticker": "A"}, {"date": "2026-07-09", "ticker": "A"}],
    datetime.date(2026, 7, 13))          # Monday after a Friday hole
assert _cov32b["missing"] == ["2026-07-10"] and _cov32b["pct"] == 80.0, \
    f"Fri hole survives the weekend, Sat/Sun never expected: {_cov32b}"
assert homily_ledger.coverage_of([], datetime.date(2026, 7, 10)) == \
    {"expected": 0, "have": 0, "missing": [], "pct": 100.0}, "empty ledger"
# the digest line renders only when gaps are passed; default is unchanged
_out32 = daily_run.render_digest([_up2("AAA")], [], {}, BULL, _REF, [], _TD,
                                 fund=_fund, gaps=["2026-07-09"])
assert "no ledger rows for 2026-07-09" in _out32 and "hole" in _out32
_out32q = daily_run.render_digest([_up2("AAA")], [], {}, BULL, _REF, [], _TD,
                                  fund=_fund)
assert "ledger rows for" not in _out32q, "no gaps -> no line"
print("[32] Missed runs: gaps found, weekends exempt, digest line renders . PASS")

# --- 33. Dashboard (#36) self-contained + snapshot contract (#75) ----------
# D-36's promise is longevity: one HTML file, zero JS, zero external assets,
# deterministic. And the snapshot the dashboard (and later T3) reads is now
# a pinned contract — a silently renamed field must fail CI, not cost money.
import homily_dashboard

_snap33 = {
    "_v": 1, "date": "2026-07-11", "generated_utc": "2026-07-11T01:00:00+00:00",
    "regime": {"label": "BULL", "action": "stay invested", "detail": {}},
    "coverage": {"expected": 3, "have": 2, "missing": ["2026-07-09"],
                 "pct": 66.67},
    "buyday": {"orders": [["TSM", 3, 434.0, ""]], "budget": 1550.0,
               "spent": 1302.0, "leftover": 248.0, "mode": "normal",
               "manual": [], "skipped": [], "index_amt": 0.0,
               "srs_covers_index": True},
    "holdings": [{"ticker": "AAA", "held": True, "state": "ACCUMULATE",
                  "close": 100.0,
                  "zone_lo": 95.0, "zone_hi": 101.0, "poc": 97.0,
                  "pct_in_profit": 88.0, "wk_circle": "RED", "wk_score": 4,
                  "wk_weeks": 12, "conv_score": 80, "conv_tier": "CONVICTION",
                  "rs12": 40.0, "ftag": "F:3/3", "origin": "holding",
                  "support": [[96.0, 1.0]], "resistance": [[110.0, 0.5]],
                  "whale": False, "book_pct": 9.0, "cap_note": None}],
    "discovery": [{"ticker": "DDD", "state": "BOTTOMING", "close": 20.0,
                   "zone_lo": None, "zone_hi": None, "poc": 21.0,
                   "pct_in_profit": 10.0, "wk_circle": "WHITE", "wk_score": 1,
                   "wk_weeks": 3, "conv_score": 40, "conv_tier": "fails",
                   "rs12": -5.0, "ftag": "F:—", "origin": "owner-request",
                   "support": [], "resistance": [], "whale": True}],
}
homily_ledger.verify_snapshot(_snap33)          # the #75 contract, green
try:                                            # ...and it bites on drift
    homily_ledger.verify_snapshot({**_snap33, "_v": 99})
    raise SystemExit("[33] FAIL: unknown _v must be refused")
except AssertionError:
    pass

_rows33 = [
    {"date": "2026-07-08", "ticker": "AAA", "state": "CAUTION", "close": "95",
     "whale": "0", "gates_ok": "0"},
    {"date": "2026-07-10", "ticker": "AAA", "state": "ACCUMULATE",
     "close": "100", "whale": "0", "gates_ok": "1"},
]
_ref33 = [{"date": "2026-07-08", "champion": "{'ef': 13}", "champ_oos": "0.3",
           "challenger_oos": "0.5", "adopted": "True"},
          {"date": "2026-07-10", "champion": "{'ef': 13}", "champ_oos": "0.5",
           "challenger_oos": "0.4", "adopted": "False"}]
_doc33 = homily_dashboard.render(_snap33, _rows33, _ref33)
assert _doc33 == homily_dashboard.render(_snap33, _rows33, _ref33), \
    "render must be deterministic"
# #83: bars in -> candle cards; still deterministic on both boards
_bmap33 = {"AAA": _mkbars([100 * 1.0002 ** i for i in range(300)],
                          [1e6] * 300),
           "DDD": _mkbars([30 * 0.999 ** i for i in range(300)],
                          [1e6] * 300)}
_doc33b = homily_dashboard.render(_snap33, _rows33, _ref33,
                                  bars_map=_bmap33)
assert _doc33b == homily_dashboard.render(_snap33, _rows33, _ref33,
                                          bars_map=_bmap33), \
    "bars render must be deterministic"
_doc33f = homily_dashboard.render(_snap33, _rows33, _ref33,
                                  bars_map=_bmap33, full=True)
for _doc in (_doc33, _doc33b, _doc33f):
    # self-containment: no external fetches of any kind (the svg xmlns is
    # an identifier, not a fetch — allow exactly that one URL)
    _leaks33 = [ln for ln in _doc.split("\n")
                if ("http" in ln or "src=" in ln or "url(" in ln)
                and "http://www.w3.org/2000/svg" not in ln]
    assert not _leaks33, f"external references leaked: {_leaks33[:3]}"
    # D-83: the search filter is the ONE inline script; nothing external —
    # the deliberate, recorded relaxation of D-36's zero-JS rule
    assert "<script src" not in _doc.lower(), "scripts must be inline (D-83)"
    assert _doc.lower().count("<script") == 1, "one inline script: the filter"
# content: card, discovery row, heatmap cells, reused alert wording, buy day
assert "AAA" in _doc33 and "DDD" in _doc33 and "<svg" in _doc33
assert "entered ACCUMULATE" in _doc33 and "passed all 5" in _doc33, \
    "timeline must reuse #15's alert wording via diff_alerts"
assert "BUY 3 TSM" in _doc33 and "never placed" in _doc33
assert "66.67" in _doc33 and "2026-07-09" in _doc33, "coverage + holes shown"
assert "chart unavailable" in _doc33, "no bars -> facts row, never a crash"
# #83 card anatomy: engine-coloured candles, ribbon, label rail, search bar,
# the pinned red=bullish legend; the committed board honours its size budget
assert homily_dashboard.BULL in _doc33b and "wk circle" in _doc33b
assert 'id="q"' in _doc33b and "bullish" in _doc33b and "med run" in _doc33b
assert 'id="AAA"' in _doc33b and 'data-tk="AAA"' in _doc33b
assert len(_doc33b) < 300_000, "small board must stay committable (<300 KB)"
print("[33] Dashboard: searchable candle board, deterministic + contract ... PASS")

# --- 34. Breadth canary (#26): math right, line only on a hostile tape -----
_bars34u = _mkbars([100 * 1.003 ** i for i in range(900)], [1e6] * 900)
_bars34d = _mkbars([100 * 0.997 ** i for i in range(900)], [1e6] * 900)
_scr34 = [_up("AAA"), _dn("BBB"), _dn("CCC")]
_ab34 = {"AAA": _bars34u, "BBB": _bars34d, "CCC": _bars34d}
_br34 = daily_run.breadth(_scr34, _ab34)
assert _br34["n"] == 3 and abs(_br34["above200"] - 100 / 3) < 1e-6, _br34
assert abs(_br34["red"] - 100 / 3) < 1e-6, "one RED uptrend of three"
_out34 = daily_run.render_digest([_up2("AAA")], [], {}, BULL, _REF, [], _TD,
                                 fund=_fund,
                                 breadth_read={"above200": 20.0, "red": 10.0,
                                               "n": 50})
assert "hostile tape" in _out34 and "20% of the 50-name screen" in _out34
_out34q = daily_run.render_digest([_up2("AAA")], [], {}, BULL, _REF, [], _TD,
                                  fund=_fund,
                                  breadth_read={"above200": 55.0, "red": 40.0,
                                                "n": 50})
assert "hostile tape" not in _out34q, "healthy breadth prints nothing (#26)"
print("[34] Breadth canary: 200d/RED math, line only under 30% ........... PASS")

# --- 35. Trim-rule flags (#28): §5 wording, right rows, info-only ----------
# (Rule-1 threshold = CAP_PCT, 25% since the #92 promotion — the fixture
# sits just over it so the flag still exercises the same path)
_r1 = homily_positions.trim_flags({"bucket": "C", "pct": 27.3, "cap_note": ""},
                                  "HOLD", 3, "F:3/3")
assert _r1 == ["RULE 1: 27% bought-not-earned — trim back to 25%, proceeds "
               "to ⭐/index (§5.1)"], _r1
assert homily_positions.trim_flags({"bucket": "B", "pct": 40.0,
                                    "cap_note": None}, "HOLD", 3, "F:3/3") \
    == [], "bucket B earned its size — §5 pass, no Rule 1"
_r2 = homily_positions.trim_flags(None, "CAUTION", 13, "F:1/3")
assert _r2 and "RULE 2 REVIEW" in _r2[0] and "sell half" in _r2[0], _r2
assert homily_positions.trim_flags(None, "CAUTION", 13, "F:—") == [], \
    "F:— is unknown, not failing — no Rule 2 (#28)"
assert homily_positions.trim_flags(None, "CAUTION", 11, "F:0/3") == [], \
    "12-week floor is §5.2 verbatim"
assert homily_positions.trim_flags(None, "HOLD", 30, "F:0/3") == [], \
    "Rule 2 is a ⚪ rule only"
print("[35] Trim flags: §5.1/§5.2 wording, B exempt, F:— exempt, ⚪-only .. PASS")

# --- 36. Concentration lens (#29): planted blocks recovered exactly --------
import homily_clusters
import math as _m

def _cbars(seed_moves, n=120):
    px, out = 100.0, []
    for i in range(n):
        px *= _m.exp(seed_moves[i % len(seed_moves)])
        out.append((datetime.date(2026, 1, 1) + datetime.timedelta(days=i),
                    px, px, px, px, 1e6))
    return out
# two planted blocks: A/B share one move series (ρ=1), C/D another; E runs
# a third series pre-computed to be near-orthogonal to both (|ρ| < 0.01),
# so it must stay a singleton
_mv1 = [0.01, -0.02, 0.015, -0.005, 0.02, -0.01]
_mv2 = [-0.01, 0.01, -0.01, 0.02, -0.02, 0.005]
_mv3 = [-0.0114, -0.002, 0.0109, -0.0125, -0.0186, -0.0139]
_ab36 = {"A": _cbars(_mv1), "B": _cbars(_mv1),
         "C": _cbars(_mv2), "D": _cbars(_mv2),
         "E": _cbars(_mv3)}
_pos36 = {t: {"yahoo": t, "shares": 1, "cost": 1, "sector": sec}
          for t, sec in (("A", "semis"), ("B", "semis"), ("C", "soft"),
                         ("D", "soft"), ("E", "other"))}
_px36 = {"A": 40, "B": 30, "C": 15, "D": 10, "E": 5}
_conc36 = homily_clusters.concentration(_ab36, _pos36, _px36)
_cl36 = {tuple(c["tickers"]): round(c["pct"]) for c in _conc36["clusters"]}
assert _cl36 == {("A", "B"): 70, ("C", "D"): 25, ("E",): 5}, \
    f"planted blocks must be recovered exactly (D-29): {_cl36}"
assert _conc36["clusters"][0]["label"] == "semis"
_lines36 = homily_clusters.render(_conc36, ["A"], lambda x: x)
assert "semis 70% (A B)" in _lines36[0] and "other 5%" in _lines36[0], _lines36
assert len(_lines36) == 2 and "deepens the 70% semis cluster" in _lines36[1], \
    "⭐ inside a >60% cluster must get the §3 nudge"
assert len(homily_clusters.render(_conc36, ["C"], lambda x: x)) == 1, \
    "⭐ outside the top cluster: no nudge"
# pairs below the 60-day overlap floor contribute no edge (D-29 / HK holidays)
assert homily_clusters.corr({}, {}) is None
_short36 = {d: 0.01 for d in range(30)}
assert homily_clusters.corr(_short36, _short36) is None
# #97 cross-book: the core book is A+B semis 70% / C+D soft 25% / E 5% on a
# $100 book (shares 1). Fold in a swing position deepening the semis cluster
# (ticker A overlap + a same-sector name) → semis rises, warning fires.
_extra97 = [{"ticker": "A", "book": "swing", "value": 40.0, "sector": "semis"},
            {"ticker": "Z", "book": "swing", "value": 20.0, "sector": "semis"}]
_cv97 = homily_clusters.combined_view(_conc36, _extra97)
_top97 = _cv97["rows"][0]
assert _top97["label"] == "semis" and _top97["comb_pct"] > _top97["core_pct"], \
    "swing semis exposure must deepen the semis cluster"
assert _cv97["overlap_names"] == ["A"], "A is held in both books (G5 watch)"
_cr97 = homily_clusters.combined_render(_cv97, lambda x: x)
assert any("core →" in ln and "semis" in ln for ln in _cr97)
assert any("across both books (G5)" in ln for ln in _cr97), \
    "combined >60% must raise the G5 warning"
# disjoint / empty extra → silent (no line invented)
assert homily_clusters.combined_view(_conc36, []) is None
assert homily_clusters.combined_render(None, lambda x: x) == []
_dis97 = [{"ticker": "Q", "book": "swing", "value": 1.0, "sector": "biotech"}]
assert homily_clusters.combined_render(
    homily_clusters.combined_view(_conc36, _dis97), lambda x: x) == [], \
    "a tiny disjoint add that changes nothing stays silent"
print("[36] Clusters: ρ≥0.6 blocks + #97 cross-book view + G5 warning ..... PASS")

# --- 37. Sunday deep-dive (#33): fetch-free weekly summary ------------------
import homily_weekly

def _wr37(d, tk, state, conv, whale="0", vh=""):
    return {"date": d, "ticker": tk, "state": state, "conv_score": conv,
            "whale": whale, "vh_status": vh}
_rows37 = [
    _wr37("2026-07-06", "AAA", "CAUTION", "40"),
    _wr37("2026-07-07", "AAA", "BOTTOMING", "45", whale="1"),
    _wr37("2026-07-08", "AAA", "ACCUMULATE", "52"),
    _wr37("2026-07-09", "AAA", "ACCUMULATE", "55"),
    _wr37("2026-07-10", "AAA", "ACCUMULATE", "58", vh="BREAKOUT"),
    _wr37("2026-07-10", "ZZZ", "HOLD", "70"),        # not held -> no row line
    _wr37("2026-06-30", "AAA", "CAUTION", "10"),     # last week -> excluded
]
_snap37 = {"holdings": [{"ticker": "AAA", "held": True, "close": 105.0,
                         "zone_lo": 95.0, "zone_hi": 100.0}],
           "coverage": {"pct": 100.0}}
_sun37 = datetime.date(2026, 7, 12)                  # the Sunday after
_txt37 = homily_weekly.weekly_summary(_rows37, _snap37, _sun37)
assert "WEEK IN REVIEW — w/e 2026-07-12" in _txt37 and "5 trading days" in _txt37
assert "⚪🔵⭐⭐⭐" in _txt37, f"Mon→Fri state timeline: {_txt37}"
assert "conv 40→58" in _txt37, "conviction drift first→last"
assert "5% above add zone" in _txt37, "distance to zone from the snapshot"
assert "🐳 AAA" in _txt37 and "VH↑ AAA" in _txt37, "the week's events"
assert "ZZZ" not in _txt37, "unheld names stay out of the weekly rows"
assert homily_weekly.weekly_summary(_rows37, _snap37,
                                    datetime.date(2026, 8, 2)) == "", \
    "a week with no rows sends nothing"
print("[37] Weekly: timeline, drift, zone distance, events, quiet week .... PASS")

# --- 38. Flex sync (#32): parser contract, owner fields survive, never adds -
import homily_flex

_XML38 = """<FlexQueryResponse queryName="pos" type="AF">
 <FlexStatements count="1"><FlexStatement accountId="U000">
  <OpenPositions>
   <OpenPosition symbol="NVDA" position="20.5" costBasisPrice="190.1" currency="USD"/>
   <OpenPosition symbol="AAA" position="7" costBasisPrice="10" currency="USD"/>
   <OpenPosition symbol="9992" position="600" costBasisPrice="182.37" currency="HKD"/>
  </OpenPositions>
 </FlexStatement></FlexStatements>
</FlexQueryResponse>"""
_fx38 = homily_flex.parse_positions(_XML38)
assert _fx38["NVDA"] == {"shares": 20.5, "cost": 190.1, "currency": "USD"}
assert set(_fx38) == {"NVDA", "AAA", "9992"}

with tempfile.TemporaryDirectory() as _t38:
    _hp38 = os.path.join(_t38, "holdings.json")
    json.dump({"_v": 2, "positions": {
        "NVDA": {"yahoo": "NVDA", "shares": 14.85, "cost": 186.99,
                 "sector": "AI/semis", "bucket": "B"},
        "GONE": {"yahoo": "GONE", "shares": 5, "cost": 1},
        "9992": {"yahoo": "9992.HK", "shares": 600, "cost": 182.37,
                 "currency": "HKD"}}}, open(_hp38, "w"))
    _diff38 = homily_flex.sync(_fx38, _hp38)
    _doc38 = json.load(open(_hp38))
    _nv38 = _doc38["positions"]["NVDA"]
    assert _nv38["shares"] == 20.5 and _nv38["cost"] == 190.1, _nv38
    assert _nv38["sector"] == "AI/semis" and _nv38["bucket"] == "B", \
        "owner-owned fields must survive a sync"
    assert "AAA" not in _doc38["positions"], "sync never auto-adds a symbol"
    assert "GONE" in _doc38["positions"], "sync never auto-deletes a symbol"
    assert any("AAA" in d and "add by hand" in d for d in _diff38), _diff38
    assert any("GONE" in d and "NOT at IBKR" in d for d in _diff38), _diff38
    assert any("NVDA: shares" in d for d in _diff38), _diff38
    # already in sync -> no rewrite, no diff
    _before38 = open(_hp38).read()
    _diff38b = homily_flex.sync(homily_flex.parse_positions(_XML38), _hp38)
    assert not any("->" in d for d in _diff38b) \
        and open(_hp38).read() == _before38, "in-sync book must be untouched"

# env-gated + never fatal: unset -> no-op; a raising fetch -> warning line
os.environ.pop("IBKR_FLEX_TOKEN", None)
assert homily_flex.auto_sync() == []
os.environ["IBKR_FLEX_TOKEN"] = "t"
os.environ["IBKR_FLEX_QUERY"] = "q"
def _boom38(t, q):
    raise RuntimeError("wire down")
_w38 = homily_flex.auto_sync(fetch=_boom38)
assert len(_w38) == 1 and "yesterday's committed book" in _w38[0], _w38
del os.environ["IBKR_FLEX_TOKEN"], os.environ["IBKR_FLEX_QUERY"]
print("[38] Flex sync: parse, owner fields kept, no add/delete, non-fatal . PASS")

# --- 39. Engine freeze (#61): frozen files match the committed manifest -----
# EXECUTION §0: these files ARE the algorithm. Any edit must update
# engine_freeze.json in the same commit -- and per the freeze rule that is
# only legitimate in a Phase-C session whose backtest gate passed. This test
# makes a silent engine drive-by impossible: touch an engine file without
# touching the manifest and CI goes red.
import hashlib

_FROZEN61 = ["homily_chips.py", "homily_clone.py", "homily_danny.py",
             "homily_vol.py", "homily_whale.py", "homily_conviction.py",
             "homily_regime.py", "homily_fund.py"]
_here61 = os.path.dirname(os.path.abspath(__file__))
_man61 = json.load(open(os.path.join(_here61, "engine_freeze.json")))
assert set(_man61) == set(_FROZEN61), \
    "engine_freeze.json must list exactly the EXECUTION §0 frozen files"
for _f61 in _FROZEN61:
    _sha61 = hashlib.sha256(
        open(os.path.join(_here61, _f61), "rb").read()).hexdigest()
    assert _sha61 == _man61[_f61], (
        f"[39] FAIL: {_f61} changed but engine_freeze.json was not updated. "
        "Engines are frozen (EXECUTION §0); if this edit passed a Phase-C "
        "gate, update the manifest in the SAME commit and say so in the "
        "commit message.")
print("[39] Engine freeze: 8 frozen files match engine_freeze.json ......... PASS")

# --- 40. Flip scorecard (#14a): flips only at logged dates, math correct ----
import homily_flipscore as _fs

_rows40 = [
    {"date": "2026-07-01", "ticker": "AAA", "state": "CAUTION"},
    {"date": "2026-07-02", "ticker": "AAA", "state": "BOTTOMING"},  # flip
    {"date": "2026-07-03", "ticker": "AAA", "state": "BOTTOMING"},  # no flip
    {"date": "2026-07-01", "ticker": "BBB", "state": "HOLD"},
    # BBB missed 07-02 (fetch error); its next row is 07-03 — the flip must
    # date to 07-03, the day the digest actually printed the new state (R3)
    {"date": "2026-07-03", "ticker": "BBB", "state": "ACCUMULATE"},
    {"date": "2026-07-01", "ticker": "CCC", "state": "HOLD"},       # never flips
    {"date": "2026-07-03", "ticker": "CCC", "state": "HOLD"},
]
_fl40 = _fs.flips(_rows40)
assert [(f["date"], f["ticker"], f["prev"], f["new"]) for f in _fl40] == [
    ("2026-07-02", "AAA", "CAUTION", "BOTTOMING"),
    ("2026-07-03", "BBB", "HOLD", "ACCUMULATE")], \
    f"[40] FAIL: flip detection wrong: {_fl40}"

# aligned daily series: AAA +2%/day, QQQ +1%/day -> +1d excess = 2%-1% ≈ +0.99%
_d40 = [datetime.date(2026, 7, 1) + datetime.timedelta(days=i)
        for i in range(30)]
_ser40 = {"AAA": (_d40, [100 * 1.02 ** i for i in range(30)]),
          "BBB": (_d40, [50 * 1.00 ** i for i in range(30)]),
          "QQQ": (_d40, [400 * 1.01 ** i for i in range(30)])}
_tab40, _n40 = _fs.scorecard(_rows40, _ser40)
assert _n40 == 2, f"[40] FAIL: expected 2 flips, got {_n40}"
_c40 = _tab40["CAUTION→BOTTOMING"][1]
assert _c40["n"] == 1 and abs(_c40["mean"] - (1.02 - 1.01)) < 1e-9, \
    f"[40] FAIL: +1d excess math wrong: {_c40}"
_b40 = _tab40["HOLD→ACCUMULATE"][5]
assert _b40["n"] == 1 and _b40["mean"] < 0, \
    "[40] FAIL: flat name must show negative excess vs a rising QQQ"
# immature horizon: flip near the series end -> zero-count cell, never a crash
_late40 = [{"date": "2026-07-28", "ticker": "AAA", "state": "HOLD"},
           {"date": "2026-07-29", "ticker": "AAA", "state": "CAUTION"}]
_tabl40, _ = _fs.scorecard(_late40, _ser40)
assert _tabl40["HOLD→CAUTION"][20]["n"] == 0, \
    "[40] FAIL: unmatured horizon must count 0, not invent a return"
_r40 = _fs.render(_tab40, _n40, ["2026-07-01", "2026-07-03"])
assert "CAUTION→BOTTOMING" in _r40 and "R3" in _r40, \
    "[40] FAIL: render must carry the transitions and the R3 honesty line"
print("[40] Flip scorecard: flips at logged dates only, excess math, R3 ... PASS")

# --- 41. Bootstrap CIs (#39): deterministic seed, caveat mandatory ----------
import homily_bootstrap as _bs

_r41 = [0.02, -0.03, 0.05, 0.01, -0.02, 0.04, 0.00, 0.03, -0.01, 0.02,
        0.06, -0.04] * 5                       # 60 synthetic monthly returns
_m41a = _bs.block_moics(_r41, n_resamples=200)
_m41b = _bs.block_moics(_r41, n_resamples=200)
assert _m41a == _m41b, "[41] FAIL: same seed must reproduce identical bands"
# constant returns -> every circular block is identical -> degenerate band
_flat41 = _bs.block_moics([0.01] * 60, n_resamples=50)
assert abs(_flat41[0] - _flat41[-1]) < 1e-12 and \
    abs(_flat41[0] - _bs.moic_of([0.01] * 60)) < 1e-12, \
    "[41] FAIL: constant-return series must band exactly on its point MOIC"
# paired P(A>B): A strictly dominates B every month -> probability 1
assert _bs.paired_beats([0.02] * 60, [0.01] * 60, n_resamples=50) == 1.0, \
    "[41] FAIL: a dominating series must win every paired draw"
_out41 = _bs.render(
    [("fixture", _bs.moic_of(_r41), _bs.percentiles(_m41a), 0.5)], 60)
assert _bs.CAVEAT in _out41, \
    "[41] FAIL: the D-39 caveat line is mandatory in every rendered table"
assert "p5" in _out41 and "p95" in _out41, "[41] FAIL: percentile header"
print("[41] Bootstrap CIs: deterministic, degenerate band exact, caveat .... PASS")

# --- 42. Pullback clock (#78): dip_age counts live non-RED candle days -----
from homily_pullback_backtest import dip_age as _dip42, DIP_SCAN as _scan42
from homily_danny import daily_candle as _cand42

_up42 = [100 * 1.003 ** i for i in range(895)]
_dipped42 = _up42 + [_up42[-1] * (0.98 ** (k + 1)) for k in range(5)]
assert _cand42(_up42) == "RED" and _cand42(_dipped42) != "RED", \
    "[42] FAIL: fixture must flip the daily candle off RED"
assert _dip42(_up42) == 0, "[42] FAIL: an intact uptrend has no dip age"
assert _dip42(_dipped42) == 5, \
    f"[42] FAIL: 5 falling days must count dip d5, got {_dip42(_dipped42)}"
_long42 = _up42 + [_up42[-1] * (0.99 ** (k + 1)) for k in range(60)]
assert _dip42(_long42) == _scan42, \
    "[42] FAIL: dip age must cap at the scan window, not walk the series"
assert _dip42([100.0] * 50) == 0, \
    "[42] FAIL: sub-warmup series must return 0, never guess"
print("[42] Pullback clock: dip age counts, caps, warmup-guarded .......... PASS")

# --- 43. Conviction backtest (#20): pure helpers + band determinism ---------
import homily_conviction_backtest as _cb

assert _cb.spearman([0, 1, 2, 3, 4], [10, 20, 30, 40, 50]) == 1.0 and \
    _cb.spearman([0, 1, 2, 3, 4], [50, 40, 30, 20, 10]) == -1.0, \
    "[43] FAIL: spearman must be ±1 on perfectly (anti)monotone input"
_d43 = _cb.deciles_of([(chr(97 + i), i) for i in range(20)])
assert _d43["t"] == 9 and _d43["a"] == 0 and _d43["j"] == 4, \
    f"[43] FAIL: within-day decile assignment wrong: {_d43}"
_obs43 = [0.01 * ((i % 7) - 3) for i in range(60)]
assert _cb.boot_band(_obs43) == _cb.boot_band(_obs43), \
    "[43] FAIL: same seed must reproduce the same 90% band (replay determinism)"
_lo43, _hi43 = _cb.boot_band(_obs43)
assert _lo43 <= sum(_obs43) / len(_obs43) <= _hi43, \
    "[43] FAIL: the point estimate must sit inside its own band"
print("[43] Conviction backtest: spearman, deciles, deterministic bands ... PASS")

# --- 44. Refine re-point (#21): objective math + lock-step + idempotence ----
import tempfile as _tmp44
import homily_refine_objective as _ro
from homily_refine import circle_series_p as _csp_ref, DEFAULT as _def44

# the objective's circle MUST stay in lock-step with the refine loop's
_ser44 = [100 * (1.004 ** i) for i in range(120)] \
    + [100 * (1.004 ** 119) * (0.99 ** i) for i in range(40)]
assert _ro.circle_series_p(_ser44, _def44) == \
    _csp_ref(_ser44, _def44["ef"], _def44["es"]), \
    "[44] FAIL: objective circle drifted from homily_refine's arithmetic"
assert _ro.circle_series_p(_ser44, _def44)[-1] != "RED" and \
    _ro.circle_series_p([100 * 1.004 ** i for i in range(160)],
                        _def44)[-1] == "RED", \
    "[44] FAIL: circle direction sanity"

# J math on synthetic bars: an uptrend under RED-fallback has ⭐ days and a
# finite J; a collapse-then-rally makes ⚪ days register false blocks
def _mk44(prices):
    d0 = _dt.date(2023, 1, 2)
    return [(d0 + _dt.timedelta(days=i), p, p + 0.5, p - 0.5, p, 1e6)
            for i, p in enumerate(prices)]

_up44 = _mk44([100 * 1.002 ** i for i in range(800)])
_ctx44 = _ro.day_context(_up44)
_m44, _n44, _fb44, _bl44 = _ro.j_of(_up44, _ctx44, _def44,
                                    fallback_red=True)
assert _n44 > 0 and _m44 == _m44, "[44] FAIL: uptrend must yield ⭐(p) days"
_px44 = [100 * 1.002 ** i for i in range(500)] \
    + [150 * 0.997 ** i for i in range(200)] \
    + [90 * 1.01 ** i for i in range(100)]
_dn44 = _mk44(_px44)
_ctx44b = _ro.day_context(_dn44)
_, _, _fbr44, _nb44 = _ro.j_of(_dn44, _ctx44b, _def44, span=(500, 740),
                               fallback_red=True)
assert _nb44 > 0 and _fbr44 > 0, \
    "[44] FAIL: a recovery after ⚪ days must register as false blocks"

# log_parallel: appends once per (date, params), never twice
_jf44 = os.path.join(_tmp44.mkdtemp(), "j.csv")
_bm44 = {"NVDA": _up44}
_keep44, _keepfb44 = _ro.BASKET_J, _ro.FALLBACK_RED
_ro.BASKET_J = ("NVDA",)
_ro.FALLBACK_RED = True     # fixture independence from chip-shelf geometry
_day44 = _dt.date(2026, 7, 11)
_n1 = _ro.log_parallel(_bm44, _def44, {"ef": 8, "es": 26, "inv": "RED"},
                       day=_day44, path=_jf44)
_n2 = _ro.log_parallel(_bm44, _def44, {"ef": 8, "es": 26, "inv": "RED"},
                       day=_day44, path=_jf44)
_ro.BASKET_J, _ro.FALLBACK_RED = _keep44, _keepfb44
assert _n1 == 2 and _n2 == 0, \
    f"[44] FAIL: parallel log must be idempotent per day ({_n1}/{_n2})"
with open(_jf44) as _f44:
    assert _f44.readline().strip() == _ro.J_HEADER.strip(), \
        "[44] FAIL: J log header drifted"
print("[44] Refine re-point: lock-step circle, J math, idempotent J log ... PASS")

# --- 45. Quality tier (#66): as-of honesty, scoring cuts, tier bounds -------
import homily_quality as _hq

# facts: FY2020 filed 2021-02, FY2021 filed 2022-02. As-of 2021-11 the
# second year is INVISIBLE — using it would be look-ahead.
_facts45 = {
    "rev": [("2019-12-31", "2020-02-10", 100.0),
            ("2020-12-31", "2021-02-10", 130.0),
            ("2021-12-31", "2022-02-10", 90.0)],
    "ni": [("2019-12-31", "2020-02-10", 5.0),
           ("2020-12-31", "2021-02-10", 12.0),
           ("2021-12-31", "2022-02-10", -40.0)],
    "ocf": [("2019-12-31", "2020-02-10", 10.0),
            ("2020-12-31", "2021-02-10", 20.0),
            ("2021-12-31", "2022-02-10", -30.0)],
    "capex": [("2019-12-31", "2020-02-10", 3.0),
              ("2020-12-31", "2021-02-10", 4.0),
              ("2021-12-31", "2022-02-10", 4.0)],
    "shares": [("2020-01-31", "2020-02-10", 1000.0),
               ("2021-01-31", "2021-02-10", 1050.0),
               ("2022-01-31", "2022-02-10", 1600.0)],
}
_q45a = _hq.q_points(_facts45, _dt.date(2021, 11, 1), rs3y=0.5)
_q45b = _hq.q_points(_facts45, _dt.date(2022, 11, 1), rs3y=-0.2)
assert _q45a and _q45a[0] == 7 and _hq.tier_of(_q45a[0]) == "Q1", \
    f"[45] FAIL: 2021 view must score the healthy year: {_q45a}"
assert _q45b and _q45b[0] <= 2 and _hq.tier_of(_q45b[0]) == "Q3", \
    f"[45] FAIL: 2022 view must see the broken year: {_q45b}"
assert not _q45a[1].get("dilution") is False, \
    "[45] FAIL: 5%/yr dilution must pass the <12% cut"
assert _q45b[1]["dilution"] is False, \
    "[45] FAIL: 52%/yr dilution must fail the cut"
assert _hq.q_points({"rev": [], "ni": [], "ocf": [], "capex": [],
                     "shares": []}, _dt.date(2024, 1, 1), None) is None \
    and _hq.q_points(None, _dt.date(2024, 1, 1), 0.1) is None, \
    "[45] FAIL: no data must yield None (prints Q:—), never a guess"
assert (_hq.tier_of(5), _hq.tier_of(4), _hq.tier_of(3), _hq.tier_of(2)) == \
    ("Q1", "Q2", "Q2", "Q3"), "[45] FAIL: tier cuts drifted from D-66"
print("[45] Quality tier: as-of filing honesty, cuts, Q:— on no data ...... PASS")

# --- 46. Mechanical universe (#65): L0 filters, gates, L2 cut, shadow rows --
import homily_universe as _hu

for _sym46, _nm46, _etf46, _tst46, _ex46, _want46 in (
        ("AAPL", "Apple Inc. - Common Stock", "N", "N", True, True),
        ("FOO", "Foo Corp Warrant", "N", "N", True, False),
        ("BARQ", "Bar Acquisition Corp", "N", "N", True, False),
        ("SPYX", "Some ETF", "Y", "N", True, False),
        ("TSTT", "Test Co", "N", "Y", True, False),
        ("BRK.A", "Berkshire Class A", "N", "N", True, False),
        ("SKHYV", "SK hynix when issued", "N", "N", True, False),
        ("XCHG", "Off-exchange Co", "N", "N", False, False)):
    assert _hu._l0_keep(_sym46, _nm46, _etf46, _tst46, _ex46) == _want46, \
        f"[46] FAIL: L0 filter wrong for {_sym46}"
assert _hu.gate("OK", (10.0, 60e6, 60)) and \
    _hu.gate("CHEAP", (4.0, 60e6, 60)) is None and \
    _hu.gate("THIN", (10.0, 40e6, 60)) is None and \
    _hu.gate("YNG", (10.0, 60e6, 30))["young"], \
    "[46] FAIL: L1 gate thresholds drifted"
_stats46 = {f"N{i:03d}": (10.0, (200 - i) * 1e6, 60) for i in range(200)}
_stats46["HELD"] = (10.0, 51e6, 60)
_stats46["STKY"] = (10.0, 52e6, 60)
_u46 = _hu.build(sorted(_stats46), _stats46, {"HELD"}, {"STKY"},
                 since="2026-07-11")
_names46 = {n["symbol"] for n in _u46["names"]}
assert len([n for n in _names46 if n.startswith("N")]) == _hu.TOP_N and \
    "HELD" in _names46 and "STKY" in _names46, \
    "[46] FAIL: L2 must keep top-N plus holdings plus sticky"
assert all(n["origin"] == "screen" for n in _u46["names"]), \
    "[46] FAIL: mechanical arrivals must carry origin=screen"

# shadow rows: origin shadow-screen, blank ranks, and the digest's rank
# cross-section must be IDENTICAL with and without shadow present
_shdir46 = os.path.join(_tmp44.mkdtemp(), "")
_led46 = os.path.join(_shdir46, "led.csv")
_hsh46 = os.path.join(_shdir46, "hash.json")
_snp46 = os.path.join(_shdir46, "snap.json")
_sigA46 = _up("AVIS")               # reuse the check-17 fixture builders
_sigB46 = _up("SHDW")
_day46 = _dt.date(2026, 7, 11)
homily_ledger.record([_sigA46], [], None, _day46,
                     set(), fund=lambda t: "F:—",
                     shadow=[(_sigB46[0], _sigB46[1])],
                     ledger=_led46, snapshot=_snp46, hashfile=_hsh46)
_rows46 = homily_ledger._read_rows(_led46)
_bytk46 = {r["ticker"]: r for r in _rows46}
assert _bytk46["SHDW"]["origin"] == "shadow-screen" and \
    _bytk46["SHDW"]["rs12_rank"] == "" and \
    _bytk46["SHDW"]["whale_rank"] == "", \
    f"[46] FAIL: shadow row malformed: {_bytk46.get('SHDW')}"
assert _bytk46["AVIS"]["rs12_rank"] == "1", \
    "[46] FAIL: shadow rows must not perturb the visible rank cross-section"
_snap46 = json.load(open(_snp46))
assert all(s["ticker"] != "SHDW"
           for s in _snap46["holdings"] + _snap46["discovery"]), \
    "[46] FAIL: shadow names must stay out of the snapshot"
print("[46] Mechanical universe: L0/L1/L2 rules, shadow rows fenced off ... PASS")

# --- 47. Any-ticker chart CLI (#84): deterministic ad-hoc card, R3 clean ----
import homily_chart
_row47 = dict(_snap33["holdings"][0])
_pg47 = homily_chart.chart_page(
    [(_row47, _bmap33["AAA"], "ad-hoc — not screened, no ledger history")],
    "2026-07-11")
assert _pg47 == homily_chart.chart_page(
    [(_row47, _bmap33["AAA"], "ad-hoc — not screened, no ledger history")],
    "2026-07-11"), "chart_page must be deterministic"
assert "ad-hoc" in _pg47 and "not screened" in _pg47, "honesty banner"
assert 'class="card"' in _pg47 and homily_dashboard.BULL in _pg47 and \
    "wk circle" in _pg47, "must reuse #83's card renderer, not re-draw"
assert "<script" not in _pg47.lower(), "single-card page stays zero-JS"
_leaks47 = [ln for ln in _pg47.split("\n")
            if ("http" in ln or "src=" in ln or "url(" in ln)
            and "http://www.w3.org/2000/svg" not in ln]
assert not _leaks47, f"external references leaked: {_leaks47[:3]}"
# R3, mechanically: the CLI module must contain no ledger/snapshot write —
# an ad-hoc chart is context, never a tracked call
_src47 = open(os.path.join(os.path.dirname(os.path.abspath(__file__)),
                           "homily_chart.py")).read()
assert ".record(" not in _src47 and "write_snapshot" not in _src47 and \
    "signals_log" not in _src47, "homily_chart must never write the ledger"
print("[47] Chart CLI: ad-hoc card deterministic, banner on, R3 clean ..... PASS")

# --- 48. SWING (paper) block (#90/D-90): deterministic, fenced, read-only --
import homily_swing
_st48 = {"inception": "2026-07-10", "as_of": "2026-07-10",
         "cash": 20000.0, "capital": 20000.0, "positions": {},
         "pending": [{"sym": "AAA", "side": "BUY", "reason": "ROTATE"}],
         "hwm": 20000.0, "closed_trades": 0}
_d48 = datetime.date(2026, 7, 24)
_blk48 = homily_swing.swing_block(_st48, _d48)
assert _blk48 == homily_swing.swing_block(_st48, _d48), \
    "swing block must be deterministic"
assert "wk 2/26" in _blk48 and "closed 0/20" in _blk48, \
    "P2 gate counters must print (weeks from inception, not clock)"
assert "PAPER" in _blk48 and "LIVE_ORDERS=off" in _blk48 and \
    "no real orders" in _blk48, "the paper fence must be explicit"
# (updated with #93's promotion: the paper block now states its A5 role —
# the no-stops counterfactual the live book is scored against)
assert "counterfactual" in _blk48 and "A5" in _blk48, \
    "the paper block must state its counterfactual role (A5)"
assert homily_swing.swing_block(None, _d48) == "" and \
    homily_swing.swing_block({"inception": "not-a-date"}, _d48) == "", \
    "missing/corrupt sleeve state must render nothing, never raise"
# R3, mechanically: the daily-side swing module must never write sleeve or
# homily state — the weekly loop alone owns the journal/snapshot
_src48 = open(os.path.join(os.path.dirname(os.path.abspath(__file__)),
                           "homily_swing.py")).read()
assert ".record(" not in _src48 and "append_rows" not in _src48 and \
    "save_snapshot" not in _src48 and "signals_log" not in _src48 and \
    "urlopen" not in _src48 and "write_text" not in _src48, \
    "homily_swing is read-only: no ledger/journal/snapshot writes, no network"
print("[48] SWING paper block: deterministic counters, fenced, read-only .. PASS")

# --- 49. Leverage ladder line (#91/LEVERAGE.md): constants + rendering ----
import homily_leverage
assert homily_leverage.LADDER == {"BULL": 1.30, "MIXED": 1.15,
                                  "BEAR": 1.00}, \
    "ladder constants are LEVERAGE.md §1 — any change is a §5 shrink event"
_l49 = homily_leverage.leverage_line("BULL", False)
assert "1.30" in _l49 and "margin NEVER" in _l49 and \
    "shrink-only" in _l49, "BULL line: cap + core ban + legacy reminder"
assert "shrink-only" not in homily_leverage.leverage_line("BULL", True), \
    "MARGIN_ZERO=true silences the legacy-margin reminder"
_b49 = homily_leverage.leverage_line("BEAR", False)
assert "MARGIN TO ZERO" in _b49 and "1.00" in _b49, \
    "BEAR line must order margin to zero (PLAYBOOK §4 step 1)"
assert "no NEW margin" in homily_leverage.leverage_line("MIXED", True), \
    "MIXED = no new margin"
assert homily_leverage.leverage_line("???", False) == "", \
    "unknown regime renders nothing, never raises"
assert homily_leverage.leverage_line("BULL", False) == \
    homily_leverage.leverage_line("BULL", False), "deterministic"
_src49 = open(os.path.join(os.path.dirname(os.path.abspath(__file__)),
                           "homily_leverage.py")).read()
assert "urlopen" not in _src49 and "write_text" not in _src49 and \
    ".record(" not in _src49, "the ladder line is pure render — no IO"
print("[49] Leverage ladder line: constants pinned, regimes render, pure .. PASS")

# --- 50. #92 add-cap promotion: constants interlocked, demotion watch ------
assert homily_positions.CAP_PCT == 25.0 and homily_positions.WARN_PCT == 20.0, \
    "#92: cap constants (a demotion reverts BOTH to 10.0/8.0)"
assert homily_buyday.CAP_FRAC == homily_positions.CAP_PCT / 100.0, \
    "D-27 interlock: the copilot cap IS homily_positions.CAP_PCT"
_reg50 = {e["id"]: e for e in homily_promotions.load_registry()}
assert "add-cap-25" in _reg50 and _reg50["add-cap-25"]["demotion_rule"], \
    "#92 must be in promotions.json with its demotion rule"
_pos50 = {"BIG": {"yahoo": "BIG", "shares": 100.0, "cost": 10.0},
          "SML": {"yahoo": "SML", "shares": 1.0, "cost": 10.0}}
_px50 = {"BIG": 40.0, "SML": 40.0}                 # BIG ≈ 99% of book
# halved from its post-promotion high (80 → 40) → banner fires
_ln50 = homily_positions.cap_demotion_line(_pos50, _px50, {"BIG": 80.0})
assert "DEMOTION TRIGGERED" in _ln50 and "BIG" in _ln50 and "10%" in _ln50, \
    f"halved ≥15% name must fire the banner: {_ln50!r}"
# −40% from high → quiet; small name halved → quiet; missing highs → quiet
assert homily_positions.cap_demotion_line(_pos50, _px50, {"BIG": 66.0}) == ""
assert homily_positions.cap_demotion_line(
    _pos50, _px50, {"SML": 80.0}) == ""
assert homily_positions.cap_demotion_line(_pos50, _px50, {}) == ""
assert homily_positions.cap_demotion_line({}, {}, None) == ""
print("[50] #92 add-cap 25%: interlock + registry + demotion watch fires .. PASS")

# --- 51. #93/A5 live blocks: waiting → armed → killed, monthly realized ----
assert homily_swing.KILL_FRAC == 0.70, "A5 kill fraction is pre-registered"
_lw51 = homily_swing.live_block({"armed": None, "contributed": 3000.0})
assert "waiting for the clean slate" in _lw51 and "MARGIN_ZERO" in _lw51
_bk51 = {"armed": "2026-08-01", "contributed": 3000.0, "equity": 2800.0,
         "hwm": 3100.0, "cash": -500.0, "killed": None,
         "positions": {"MU": {}}, "pending": [],
         "realized": [{"date": "2026-08-14", "sym": "STX", "reason": "STOP",
                       "pnl": -120.0},
                      {"date": "2026-09-02", "sym": "WDC", "reason": "TP",
                       "pnl": 260.0}]}
_lb51 = homily_swing.live_block(_bk51)
assert "$2,800" in _lb51 and "kill line $2,100" in _lb51 and \
    "HOLD per plan" in _lb51 and "+140" in _lb51, _lb51
assert _lb51 == homily_swing.live_block(_bk51), "deterministic"
_kb51 = dict(_bk51, killed={"date": "2026-09-10", "reason": "KILL-A: ..."})
assert "KILLED" in homily_swing.live_block(_kb51) and \
    "failure memo" in homily_swing.live_block(_kb51)
_mb51 = homily_swing.monthly_block(_bk51, datetime.date(2026, 9, 1))
assert "2026-08 realized report" in _mb51 and "-120.00" in _mb51 and \
    "STOP" in _mb51 and "flywheel" in _mb51 and "modeled" in _mb51, _mb51
assert homily_swing.monthly_block({"armed": None},
                                  datetime.date(2026, 9, 1)) == "", \
    "unarmed book prints no monthly report"
_src51 = open(os.path.join(os.path.dirname(os.path.abspath(__file__)),
                           "homily_swing.py")).read()
assert "urlopen" not in _src51 and "write_text" not in _src51, \
    "homily_swing stays read-only + fetch-free"
# #95 flywheel (homily read side): the monthly report shows banked skims +
# the sleeve score (equity + skims vs contributed); the buyday helper routes
# a skim into its OWN month only (no thrice-nag across the quarter).
_bk95 = dict(_bk51, skimmed=600.0,
             skims=[{"date": "2026-08-05", "usd": 600.0,
                     "quarter": "2026-Q3", "qqq": 500.0}])
_mb95 = homily_swing.monthly_block(_bk95, datetime.date(2026, 9, 1))
assert "flywheel" in _mb95 and "banked $600.00" in _mb95 and \
    "$600.00 this quarter" in _mb95 and "skims never soften" in _mb95, _mb95
assert homily_buyday.swing_skim_this_month(
    datetime.date(2026, 8, 3), _bk95) == 600.0                 # Aug sees Aug
assert homily_buyday.swing_skim_this_month(
    datetime.date(2026, 9, 7), _bk95) == 0.0                   # Sep does not
_p95 = {"budget": 1500, "mode": "normal", "srs_covers_index": False,
        "orders": [], "manual": [], "skipped": [], "spent": 0, "leftover": 1500}
_r95 = homily_buyday.render(_p95, datetime.date(2026, 8, 3), 600.0)
assert "swing skim $600" in _r95 and "routed in (#95)" in _r95, _r95
assert "swing skim" not in homily_buyday.render(_p95, datetime.date(2026, 8, 3))
# #96: the A5 A/B stop-cost section is wired into the monthly report,
# read-only + non-fatal (empty until a live stop-episode closes)
_ab96 = homily_swing._ab_block(datetime.date(2026, 9, 1), lambda x: x)
assert isinstance(_ab96, str), "A/B wiring must never raise"
# #100: the cost-reconcile section is wired the same way, read-only +
# non-fatal (empty until a committed ibkr_statement.json exists)
_rec100 = homily_swing._reconcile_block(lambda x: x)
assert isinstance(_rec100, str), "reconcile wiring must never raise"
print("[51] #93 live: kill/monthly + #95/#96 + #100 reconcile wired ...... PASS")

# --- 52. #94 household scorecard: adjclose counterfactual + missing nag -----
import homily_household as _hh
# monthly_adj keeps the LAST adjusted close of each month, and the
# counterfactual must run on ADJUSTED closes, not raw (R1 / #18): feed two
# series that differ only in the adjusted column and the QQQ value must move.
_d52 = [datetime.date(2026, 5, 29), datetime.date(2026, 6, 30),
        datetime.date(2026, 7, 31)]
_bars52 = [(d, 0, 0, 0, 100.0 + i, 0) for i, d in enumerate(_d52)]
_adjA52 = [90.0, 95.0, 100.0]          # dividend-adjusted (what returns use)
_adjB52 = [100.0, 100.0, 100.0]        # raw-equal control
_mapA = _hh.monthly_adj(_bars52, _adjA52)
_mapB = _hh.monthly_adj(_bars52, _adjB52)
assert _mapA == {"2026-05": 90.0, "2026-06": 95.0, "2026-07": 100.0}, _mapA
_flows52 = [{"month": "2026-05", "usd": 1000.0},
            {"month": "2026-07", "usd": 1000.0}]
_cfA = _hh.counterfactual(_flows52, _mapA)
_cfB = _hh.counterfactual(_flows52, _mapB)
# adjusted buys cheaper in May → more shares → higher value; raw-equal ≈ 2000
assert abs(_cfB["value"] - 2000.0) < 1e-6, _cfB
assert _cfA["value"] > _cfB["value"] + 1.0, "counterfactual must use adjclose"
assert _cfA["deployed"] == 2000.0 and not _cfA["uncovered"]
# a flow month older than the fetched QQQ range is reported, never dropped
_cfU = _hh.counterfactual([{"month": "2020-01", "usd": 500.0}] + _flows52,
                          _mapA)
assert _cfU["uncovered"] == ["2020-01"] and _cfU["deployed"] == 2000.0, _cfU
# missing-month nag: inception May, flows only May+July → June is missing
assert _hh.months_between("2026-05", "2026-07") == \
    ["2026-05", "2026-06", "2026-07"]
# book composition: USD-only sum (R12), Bucket-A tracked, swing when armed
_pos52 = {"NV": {"yahoo": "NV", "shares": 10.0, "cost": 1.0},
          "IX": {"yahoo": "IX", "shares": 2.0, "cost": 1.0, "bucket": "A"},
          "HK": {"yahoo": "HK", "shares": 100.0, "cost": 1.0,
                 "currency": "HKD"}}
_px52 = {"NV": 50.0, "IX": 100.0, "HK": 10.0}
_live52 = {"armed": "2026-08-01", "equity": 3200.0, "cash": -800.0}
_bal52 = {"srs_usd": 12000.0, "espp_external_usd": 3000.0,
          "margin_loan_usd": 5000.0}
_comp52 = _hh.book_value(_pos52, _px52, _live52, _bal52)
assert _comp52["core_gross"] == 700.0 and _comp52["core_index"] == 200.0, \
    _comp52                                   # HK excluded (R12), A counted
assert _comp52["swing_mv"] == 4000.0 and _comp52["swing_loan"] == 800.0
# net = 700 core + 12000 srs + 3000 espp + 4000 swing_mv − 5000 − 800
assert abs(_comp52["net"] - 13900.0) < 1e-6, _comp52
# combined IBKR gross leverage = (700+4000)/((700+4000)−(5000+800))... net<0
assert _hh.combined_leverage(_comp52) is None      # loans exceed IBKR gross
_comp52b = _hh.book_value(_pos52, _px52, _live52, {"margin_loan_usd": 0.0})
_lev52 = _hh.combined_leverage(_comp52b)            # 4700 / (4700−800)
assert abs(_lev52 - 4700.0 / 3900.0) < 1e-9, _lev52
# render is deterministic, HTML-safe, prints the nag and the ladder cap
_r52 = _hh.render(_comp52b, _cfA, 2000.0, _lev52, "BULL", 1.30,
                  ["2026-06"], esc=lambda x: str(x))
assert _r52 == _hh.render(_comp52b, _cfA, 2000.0, _lev52, "BULL", 1.30,
                          ["2026-06"], esc=lambda x: str(x)), "deterministic"
assert "HOUSEHOLD BOOK" in _r52 and "missing 1 month" in _r52 and \
    "2026-06" in _r52 and "QQQ counterfactual" in _r52 and \
    "ladder cap 1.30" in _r52, _r52
# 4700/3900 = 1.205× < 1.30 BULL cap → must NOT flag over-cap
assert "OVER LADDER CAP" not in _r52
# a book over its cap DOES flag: 1.205× vs a MIXED 1.15 cap
assert "OVER LADDER CAP" in _hh.render(
    _comp52b, _cfA, 2000.0, _lev52, "MIXED", 1.15, [], esc=lambda x: str(x))
# no flows logged → no counterfactual, honest note instead of a fake number
assert "counterfactual unavailable" in _hh.render(
    _comp52b, None, 0.0, _lev52, "BULL", 1.30, [], esc=lambda x: str(x))
# household_block returns "" on a non-first-Monday and never fetches then
assert _hh.household_block(_pos52, _px52,
                           datetime.date(2026, 7, 15)) == ""
# opening-balance honesty (the fix that turns a misleading +405% into a
# truthful comparison): the shell must seed opening_usd into the QQQ
# counterfactual at inception, so a book that merely rode QQQ prints ≈flat,
# not a giant fake edge. Stub fetch + contributions to pin it deterministically.
_tmp52 = os.path.join(tempfile.mkdtemp(), "c.json")
open(_tmp52, "w").write(json.dumps(
    {"_v": 1, "inception": "2026-06", "opening_usd": 10000.0,
     "balances": {}, "flows": [{"month": "2026-06", "usd": 0}],
     "usdsgd": 1.3}))
_saved52 = _hh.CONTRIB_FILE
_hh.CONTRIB_FILE = _tmp52
try:
    def _fx52(sym, rng="5y"):
        d = [datetime.date(2026, 6, 30), datetime.date(2026, 7, 31)]
        b = [(x, 0, 0, 0, 1, 0) for x in d]
        return (b, [500.0, 600.0]) if sym == "QQQ" else (b, [1.3, 1.3])
    # book that exactly rode QQQ +20% (10000 → 12000), no flows: must read
    # ≈flat vs the counterfactual, NOT +20% over "0 contributed"
    _blk = _hh.household_block(
        {"Q": {"yahoo": "Q", "shares": 120.0, "cost": 1.0}},
        {"Q": 100.0}, datetime.date(2026, 7, 6),
        regime_label="BULL", fetch_series=_fx52, esc=lambda x: str(x))
    assert "18,500" not in _blk and "on the same US$10,000 invested" in _blk, \
        _blk                                   # opening counted in the basis
    assert "ahead of by US$0" in _blk or "behind by US$0" in _blk, \
        f"opening-seeded book that rode QQQ must read ≈flat: {_blk!r}"
finally:
    _hh.CONTRIB_FILE = _saved52
print("[52] #94 household: adjclose counterfactual, leverage, missing nag .. PASS")

# --- 53. #99 ops-readiness: blockers line + one-shot KILL-A proximity -------
import homily_ops as _ops
# a fully unset board lists all blockers, with margin balance when given
_env53 = {"MARGIN_BALANCE": "9,800"}
_bl53 = _ops.blockers(_env53)
assert len(_bl53) == 3, _bl53           # margin + flex + budget
_ln53 = _ops.ops_line(_env53, esc=lambda x: x)
assert "SETUP" in _ln53 and "S$9,800 to clean slate" in _ln53 and \
    "IBKR Flex secrets unset" in _ln53 and "BUY_BUDGET_USD is 0" in _ln53, _ln53
# a clean board is silent (no green-checkmark nag)
_clean53 = {"MARGIN_ZERO": "true", "IBKR_FLEX_TOKEN": "t",
            "IBKR_FLEX_QUERY": "q", "BUY_BUDGET_USD": "1550"}
assert _ops.blockers(_clean53) == [] and _ops.ops_line(_clean53) == ""
# MARGIN_ZERO set but budget still 0 → only the budget blocker
_part53 = {"MARGIN_ZERO": "on", "IBKR_FLEX_TOKEN": "t",
           "IBKR_FLEX_QUERY": "q"}
assert len(_ops.blockers(_part53)) == 1 and \
    "BUY_BUDGET" in _ops.ops_line(_part53)
# #99 one-shot KILL-A proximity warning surfaces in the live block
_w53 = homily_swing.live_block(dict(_bk51, warned_80="2026-09-20"))
assert "KILL-A PROXIMITY" in _w53 and "do not average down" in _w53, _w53
assert "KILL-A PROXIMITY" not in homily_swing.live_block(_bk51)  # not flagged
print("[53] #99 ops-readiness: blockers line + KILL-A proximity warning ... PASS")

# --- 54. #101 daily-candle column in the ledger: END-appended, forward-only --
# daily_candle() (RED/YELLOW/NEUTRAL) is the one engine output the digest
# renders (dY + the #78 pullback clock) yet never persisted — wk_circle is the
# WEEKLY circle, a different signal. Pure measurement: the column feeds a later
# daily-candle event study and gates nothing. The append changed the guard-#62
# hash serialisation; the checkpoint was regenerated DELIBERATELY in this commit
# (same pattern as origin [29] / whale_rank [31]).
# (was COLUMNS[-1] until #89 END-appended rs6_rank after it — the ordering
# assert is the durable form, "last" belongs to whichever column is newest)
assert homily_ledger.COLUMNS.index("candle") \
    > homily_ledger.COLUMNS.index("whale_rank"), "after the earlier columns"
_sig54, _conv54, _ = _up("CDL")
assert _sig54.candle in ("RED", "YELLOW", "NEUTRAL"), _sig54.candle
_st54 = homily_ledger.state_of(_sig54, _conv54, True, fund=_fund)
assert _st54["candle"] == _sig54.candle, \
    "the DAILY candle must land in the state dict verbatim"
_d54 = datetime.date(2026, 7, 14)
assert homily_ledger.csv_row(_st54, _d54)["candle"] == _sig54.candle, \
    "candle must flatten into the CSV row"
# round-trip through the real append/verify path; history still verifies with
# the new column covered from day one (mirrors [29])
with tempfile.TemporaryDirectory() as _tmp54:
    _lg54 = os.path.join(_tmp54, "ledger.csv")
    _hf54 = os.path.join(_tmp54, "hash.json")
    homily_ledger.append_rows([homily_ledger.csv_row(_st54, _d54)], _d54,
                              ledger=_lg54, hashfile=_hf54)
    _d54b = datetime.date(2026, 7, 15)
    homily_ledger.append_rows([homily_ledger.csv_row(_st54, _d54b)], _d54b,
                              ledger=_lg54, hashfile=_hf54)
    assert [r["candle"] for r in homily_ledger._read_rows(_lg54)] \
        == [_sig54.candle, _sig54.candle], "candle persists through round-trip"
    homily_ledger.verify_history(ledger=_lg54, hashfile=_hf54)
# the committed checkpoint itself verifies with candle in COLUMNS (regen was
# deliberate, this commit) — a live guard on the real ledger, not just fixtures
homily_ledger.verify_history()
print("[54] #101 daily-candle: END-appended column, forward-only, R3 clean .. PASS")

# --- 55. #102 bearish-tells block: >=2 dated tells, held-only, additive ------
# The tells Danny reads pre-correction, consolidated info-only over HELD
# names. Three gate clauses under test: (a) the block renders ONLY when a
# held name shows >= TELLS_MIN concurrent tells; (b) the digest with the
# block is the digest without it plus the block, byte-for-byte — nothing
# else moves, so the buy-day/copilot text cannot be affected; (c) tells
# carry dates read from the same bars the run fetched.
import dataclasses
import homily_bearish
from homily_golden import (_up as _up55, _bars as _bars55, _sig as _mk55,
                           BULL as _B55, REFINE as _R55, TODAY as _T55,
                           _fund as _f55)
from homily_danny import daily_candle as _dc55
# a long downtrend whose last 15 days ACCELERATE: the weekly circle is WHITE
# and the daily candle YELLOW (a plain geometric decay converges to hist>0 =
# NEUTRAL — the acceleration is what re-arms the daily tell)
_dnpx55 = [100 * 0.997 ** i for i in range(885)]
_dnpx55 += [_dnpx55[-1] * 0.985 ** (k + 1) for k in range(15)]
_dnbars55 = _bars55(_dnpx55, [1e6] * 900)
_sig55 = danny_signal("BBB", _dnbars55)
_t55 = homily_bearish.tells(_sig55, _dnbars55)
assert len(_t55) >= 2 and any(x.startswith("candle YELLOW") for x in _t55) \
    and any(x.startswith("wk ") for x in _t55), _t55
# YELLOW dating is self-consistent on a fresh flip (flat -> 15 down days):
# the prefix ending the day BEFORE the dated start was not YELLOW
_flip55 = _bars55([100.0] * 200 + [100 - 1.5 * (k + 1) for k in range(15)],
                  [1e6] * 215)
_ys55 = homily_bearish.yellow_since(_flip55)
_yi55 = [b[0] for b in _flip55].index(_ys55)
assert _yi55 >= 200 and _dc55([b[4] for b in _flip55[:_yi55]]) != "YELLOW"
# VH↓ topping tell: uptrend -> volatility hole -> close below its lower
# boundary; the tell is dated to the FIRST close below (bar 810 here)
_uppx55 = [100 * 1.003 ** i for i in range(800)]
_tb55 = _vbars([(p, p * 0.03) for p in _uppx55]
               + [(_uppx55[-1], _uppx55[-1] * 0.002)] * 10
               + [(_uppx55[-1] * 0.95, _uppx55[-1] * 0.01)] * 3)
_ts55 = danny_signal("TOP", _tb55)
assert _ts55.vol_hole and _ts55.vol_hole.status == "BREAKDOWN" \
    and _ts55.vol_hole.trend_before == "UP"
_tt55 = homily_bearish.tells(_ts55, _tb55)
assert any(x.startswith("VH↓ topping ") for x in _tt55), _tt55
assert homily_bearish.breakdown_since(_tb55, _ts55.vol_hole.lower) \
    == _tb55[810][0], "VH↓ dates to the first close below the boundary"
# (a) held-only + confluence: AAA (0 tells) never prints; BBB prints only
# when held; a single tell (candle stripped) stays silent
_held55 = sorted([_up55("AAA"), _mk55("BBB", _dnbars55)],
                 key=lambda x: daily_run.digest_sort_key(x[0], x[1]))
_bk55 = homily_bearish.block(_held55, {"BBB": _dnbars55}, {"AAA", "BBB"})
assert "BBB" in _bk55 and "AAA" not in _bk55 and "since" in _bk55, _bk55
assert "gates nothing" in _bk55, "the honesty text ships inside the block"
assert homily_bearish.block(_held55, {"BBB": _dnbars55}, {"AAA"}) == ""
_one55 = dataclasses.replace(_sig55, candle="NEUTRAL")
assert len(homily_bearish.tells(_one55, _dnbars55)) == 1
assert homily_bearish.block([(_one55, None, False)], {}, {"BBB"}) == ""
# (b) additive-only: with-block == without-block + the block, byte-level
_wo55 = daily_run.render_digest(_held55, [], {}, _B55, _R55, [], _T55,
                                fund=_f55)
_w55 = daily_run.render_digest(_held55, [], {}, _B55, _R55, [], _T55,
                               fund=_f55, bear=_bk55)
assert _bk55 in _w55 and _w55.replace("\n\n" + _bk55, "", 1) == _wo55, \
    "the block must add lines and change NOTHING else"
print("[55] #102 bearish-tells: >=2 dated tells, held-only, additive-only ... PASS")

# --- 56. #89 rs6 exposed + rs6_rank column: Phase-C additive, forward-only ---
# The one engine edit is an END-appended dataclass field (default 0.0 keeps
# any positional constructor valid); the score consumed rs6 all along via
# "rel strength", so behaviour is provably unchanged — goldens [16] pin the
# digest and the freeze manifest was regenerated DELIBERATELY this commit
# (guard #61, same for the #62 checkpoint serialisation).
assert homily_ledger.COLUMNS[-1] == "rs6_rank", "rs6_rank END-appended (#89)"
_sig56, _conv56, _ = _up("RS6")
assert isinstance(_conv56.rs6, float), "rs6 must ride the Conviction"
_st56 = homily_ledger.state_of(_sig56, _conv56, True, fund=_fund)
assert _st56["rs6"] == round(_conv56.rs6, 2), "rs6 lands in the state dict"
# rank semantics mirror rs12_ranks: ⭐ set ranked by rs6 desc, 🔵 fallback,
# non-candidates blank; ties break by ticker so the rank is deterministic
_sts56 = [{"ticker": "A", "state": "ACCUMULATE", "rs6": 5.0},
          {"ticker": "B", "state": "ACCUMULATE", "rs6": 9.0},
          {"ticker": "C", "state": "HOLD", "rs6": 99.0}]
assert homily_ledger.rs6_ranks(_sts56) == {"A": 2, "B": 1, "C": None}
_sts56b = [{"ticker": "D", "state": "BOTTOMING", "rs6": 1.0},
           {"ticker": "E", "state": "CAUTION", "rs6": 8.0}]
assert homily_ledger.rs6_ranks(_sts56b) == {"D": 1, "E": None}, "🔵 fallback"
# round-trip through the real append/verify path (mirrors [54]/[31])
_st56["rs6_rank"] = 1
_d56 = datetime.date(2026, 7, 17)
assert homily_ledger.csv_row(_st56, _d56)["rs6_rank"] == "1"
with tempfile.TemporaryDirectory() as _tmp56:
    _lg56 = os.path.join(_tmp56, "ledger.csv")
    _hf56 = os.path.join(_tmp56, "hash.json")
    homily_ledger.append_rows([homily_ledger.csv_row(_st56, _d56)], _d56,
                              ledger=_lg56, hashfile=_hf56)
    _d56b = datetime.date(2026, 7, 18)
    homily_ledger.append_rows([homily_ledger.csv_row(_st56, _d56b)], _d56b,
                              ledger=_lg56, hashfile=_hf56)
    assert [r["rs6_rank"] for r in homily_ledger._read_rows(_lg56)] == ["1", "1"]
    homily_ledger.verify_history(ledger=_lg56, hashfile=_hf56)
# the committed checkpoint verifies with rs6_rank in COLUMNS (regen was
# deliberate, this commit) — live guard on the real ledger
homily_ledger.verify_history()
print("[56] #89 rs6_rank: engine field additive, rank column forward-only ... PASS")

# --- 57. #88 top-3 turnover: month-scoped ledger read, info-only footer ------
# rs12_rank prints daily but money moves monthly; the stat counts how many
# runs this month still show the buy-day's exact top-3 set. Pure read.
_mk57 = lambda d, tk, rk: {"date": d, "ticker": tk, "rs12_rank": rk}
_rows57 = ([_mk57("2026-07-01", t, str(i + 1)) for i, t in enumerate("ABC")]
           + [_mk57("2026-07-02", t, str(i + 1)) for i, t in enumerate("ABC")]
           + [_mk57("2026-07-03", t, str(i + 1)) for i, t in enumerate("ABD")]
           + [_mk57("2026-07-03", "Z", "")]          # blank rank ignored
           + [_mk57("2026-06-30", t, str(i + 1)) for i, t in enumerate("XYZ")])
_t57 = homily_ledger.top3_turnover(_rows57, datetime.date(2026, 7, 17))
assert _t57 == {"stable": 2, "days": 3, "ref": ["A", "B", "C"],
                "first": "2026-07-01"}, _t57
assert homily_ledger.top3_turnover([], datetime.date(2026, 7, 17)) is None
assert homily_ledger.top3_turnover(_rows57,
                                   datetime.date(2026, 8, 1)) is None, \
    "month-scoped: August sees no July rows"
# footer line is additive-only: with-line == without-line + the line
from homily_golden import _up as _u57, BULL as _B57, REFINE as _R57, \
    TODAY as _T57, _fund as _f57
_ln57 = "top-3 ⭐ set stable 2/3 runs this month vs the buy-day set (A · B · C)"
_wo57 = daily_run.render_digest([_u57("AAA")], [], {}, _B57, _R57, [], _T57,
                                fund=_f57)
_w57 = daily_run.render_digest([_u57("AAA")], [], {}, _B57, _R57, [], _T57,
                               fund=_f57, turnover=_ln57)
assert _ln57 in _w57 and \
    _w57.replace(f"\n<i>{_ln57}</i>", "", 1) == _wo57, \
    "the footer line must add itself and change NOTHING else"
print("[57] #88 top-3 turnover: month-scoped, buy-day ref, additive footer .. PASS")

# --- 58. #73 digest line budget: the header zone is CAPPED by CI ------------
# The wall-of-text happened by additive-only growth; the budget makes the
# standing rule mechanical: a new digest feature must displace a line or
# live on the dashboard (#36). Zone under budget = everything above the
# first state-group heading (title, regime, ladder, ops, breadth, lens,
# cross-book — the lines every single digest carries). Cadenced blocks
# (buy-day/bear-rehearsal/household/promotions) are exempt: they earn their
# rows a few days a month. Checked on the committed goldens AND on a
# synthetic fully-loaded header so a line invisible to the fixtures (#99's
# ops line, #91's ladder) still counts.
_BUDGET73 = 12
_GROUPS73 = ("⭐", "🟢", "🟡", "🔵", "⚪")


def _header_zone(text):
    out = []
    for ln in text.split("\n"):
        if ln.startswith("<b>") and any(ic in ln for ic in _GROUPS73):
            break
        if ln.strip():
            out.append(ln)
    return out


for _n73 in ("populated", "empty", "corp"):
    _t73 = open(os.path.join(os.path.dirname(os.path.abspath(__file__)),
                             "tests", f"digest_{_n73}.golden.txt")).read()
    _hz73 = _header_zone(_t73)
    assert len(_hz73) <= _BUDGET73, \
        (f"[58] golden '{_n73}' header zone {len(_hz73)} lines > budget "
         f"{_BUDGET73}: {_hz73}")
    assert "<blockquote expandable>" in _t73, "legend must stay collapsed"
# fully-loaded standing header: BULL + ladder + ops + hostile breadth
_ops58 = _ops.ops_line({"MARGIN_BALANCE": "9,800"}, esc=lambda x: x)
_lev58 = homily_leverage.leverage_line("BULL", False, esc=lambda x: x)
_full58 = daily_run.render_digest(
    [_up("AAA")], [], {}, _B55, _R55, [], _T55, fund=_f55,
    lev=_lev58, ops=_ops58,
    breadth_read={"above200": 20.0, "red": 10.0, "n": 60})
_hz58 = _header_zone(_full58)
assert 0 < len(_hz58) <= _BUDGET73, \
    f"[58] fully-loaded header {len(_hz58)} lines > budget: {_hz58}"
print("[58] #73 line budget: header zone capped at 12, goldens + full load .. PASS")

# --- 59. #59 flash-crash pre-script: fires at -7%/5d, additive, info-only ----
_calm59 = [100.0] * 10
_crash59 = [100.0] * 5 + [100, 99, 96, 94, 92.9]     # -7.1% over 5 sessions
assert daily_run.crash_line(_calm59) == ""
assert daily_run.crash_line([100.0] * 3) == ""        # too little history
_ln59 = daily_run.crash_line(_crash59)
assert "FLASH-CRASH" in _ln59 and "-7.1%" in _ln59 and "gates nothing" in _ln59
_edge59 = [100.0] * 5 + [100, 98, 97, 95, 93.0001]    # just above the line
assert daily_run.crash_line(_edge59) == ""
# additive-only in the header zone, and the zone stays inside #73's budget
_wo59 = daily_run.render_digest([_up("AAA")], [], {}, _B55, _R55, [], _T55,
                                fund=_f55)
_w59 = daily_run.render_digest([_up("AAA")], [], {}, _B55, _R55, [], _T55,
                               fund=_f55, crash=_ln59)
assert _ln59 in _w59 and _w59.replace("\n" + _ln59, "", 1) == _wo59
assert len(_header_zone(_w59)) <= _BUDGET73, "pre-script must fit the budget"
print("[59] #59 flash-crash pre-script: -7%/5d trigger, additive, budgeted .. PASS")

# --- 60. #60 data-QA: freshness + second-source agreement, warning-only ------
import io as _io60
import homily_data as _hd60
_mkb60 = lambda d, c: (d, c, c, c, c, 1e6)
_fri60 = datetime.date(2026, 7, 10)                    # a Friday
# fresh through a weekend (Mon today, Fri last bar = 1 weekday gap)
assert _hd60.freshness_note([_mkb60(_fri60, 100.0)],
                            datetime.date(2026, 7, 13)) == ""
# stale: Fri bar seen the NEXT Friday = 5 weekday gap
_n60 = _hd60.freshness_note([_mkb60(_fri60, 100.0)],
                            datetime.date(2026, 7, 17))
assert "stale" in _n60 and "2026-07-10" in _n60
assert "no bars" in _hd60.freshness_note([], datetime.date(2026, 7, 17))
# stooq CSV parser via a canned opener (no network in validate, ever)
_csv60 = b"Date,Open,High,Low,Close,Volume\n2026-07-16,1,1,1,628.5,9\n" \
         b"2026-07-17,1,1,1,630.25,9\n"


class _Resp60:
    def __init__(self, b):
        self._b = b
    def read(self):
        return self._b
    def __enter__(self):
        return self
    def __exit__(self, *a):
        return False


_st60 = _hd60.stooq_daily("SPY", opener=lambda req, timeout: _Resp60(_csv60))
assert _st60 == [(datetime.date(2026, 7, 16), 628.5),
                 (datetime.date(2026, 7, 17), 630.25)], _st60
# agreement on the last COMMON date; 1% tolerance; disagreement notes
_ours60 = [_mkb60(datetime.date(2026, 7, 16), 628.9),
           _mkb60(datetime.date(2026, 7, 17), 630.0)]
assert _hd60.agreement_note(_ours60, _st60) == ""
_bad60 = [_mkb60(datetime.date(2026, 7, 17), 700.0)]
assert "disagree" in _hd60.agreement_note(_bad60, _st60)
assert "no common" in _hd60.agreement_note(
    [_mkb60(datetime.date(2026, 1, 2), 1.0)], _st60)
# render: notes land in the housekeeping zone, additive-only
_wo60 = daily_run.render_digest([_up("AAA")], [], {}, _B55, _R55, [], _T55,
                                fund=_f55)
_w60 = daily_run.render_digest([_up("AAA")], [], {}, _B55, _R55, [], _T55,
                               fund=_f55, dataqa=["SPY: tape may be stale"])
assert "⚠️ data-QA: SPY: tape may be stale" in _w60 and \
    _w60.replace("\n⚠️ data-QA: SPY: tape may be stale", "", 1) == _wo60
print("[60] #60 data-QA: freshness gap math, stooq parse, tol, additive .... PASS")

# --- 61. #54 weekly what-changed diff: pure ledger read, closing-row diff ----
import homily_weekly as _hw61
_r61 = lambda d, tk, st, gates="1", rk="": {
    "date": d, "ticker": tk, "state": st, "gates_ok": gates, "rs12_rank": rk}
_rows61 = [
    # last week (w/e Sun 07-12): AAA ⭐ rank1, BBB ⚪, CCC present
    _r61("2026-07-06", "AAA", "ACCUMULATE", rk="1"),
    _r61("2026-07-10", "AAA", "ACCUMULATE", rk="1"),
    _r61("2026-07-10", "BBB", "CAUTION", gates="0"),
    _r61("2026-07-10", "CCC", "HOLD"),
    # this week (w/e Sun 07-19): AAA → HOLD + lost rank, BBB gates flip on,
    # DDD arrives, CCC gone
    _r61("2026-07-17", "AAA", "HOLD", rk=""),
    _r61("2026-07-17", "BBB", "CAUTION", gates="1", rk="1"),
    _r61("2026-07-17", "DDD", "ACCUMULATE", rk="2"),
]
_sun61 = datetime.date(2026, 7, 19)
_d61 = _hw61.week_diff(_rows61, _sun61)
assert "AAA ⭐→🟢" in _d61 and "BBB 🚀✓" in _d61, _d61
assert "top-3 ⭐: AAA → BBB DDD" in _d61, _d61
assert "new to screen: DDD" in _d61 and "left screen: CCC" in _d61, _d61
# quiet week (identical closing rows) says nothing; bootstrap week is ""
_same61 = [_r61("2026-07-10", "AAA", "HOLD"), _r61("2026-07-17", "AAA", "HOLD")]
assert _hw61.week_diff(_same61, _sun61) == ""
assert _hw61.week_diff(_rows61[-3:], _sun61) == "", "no prior week -> ''"
# the diff must not disturb the summary itself (it is appended by the
# sunday shell, not injected into weekly_summary)
assert "WHAT CHANGED" not in _hw61.weekly_summary(
    _rows61, {"holdings": []}, _sun61)
print("[61] #54 weekly diff: transitions, gate flips, top-3 move, arrivals .. PASS")

# --- 62. #106 provisional-bar mark: point-in-time only, display-only ---------
# Gate clauses: (a) marks() fires m only inside the month's first 10
# sessions counted from the name's own bars, w only on a Mon-Thu print;
# (b) the suffix renders ONLY when the prov kwarg carries it — default-off
# keeps every golden byte-identical; (c) the mark changes presentation
# only: the same DannySignal in, nothing downstream reads it.
import homily_provisional as _hp62
_mkb62 = lambda d: (d, 100.0, 100.5, 99.5, 100.0, 1e6)
_jul62 = [datetime.date(2026, 6, 29), datetime.date(2026, 6, 30),
          datetime.date(2026, 7, 1), datetime.date(2026, 7, 2),
          datetime.date(2026, 7, 3), datetime.date(2026, 7, 6),
          datetime.date(2026, 7, 7), datetime.date(2026, 7, 8),
          datetime.date(2026, 7, 9), datetime.date(2026, 7, 10),
          datetime.date(2026, 7, 13), datetime.date(2026, 7, 14),
          datetime.date(2026, 7, 15), datetime.date(2026, 7, 16),
          datetime.date(2026, 7, 17)]
_bs62 = [_mkb62(d) for d in _jul62]
assert _hp62.marks(_bs62[:3]) == "mw"     # Wed Jul 1, session 1
assert _hp62.marks(_bs62[:5]) == "m"      # Fri Jul 3, session 3
assert _hp62.marks(_bs62[:13]) == "w"     # Wed Jul 15, session 11
assert _hp62.marks(_bs62) == ""           # Fri Jul 17, session 13
assert _hp62.marks([]) == ""
# render: default-off leaves the row untouched; prov adds ONLY the dots
_s62, _c62, _ = _up62 = _up("PRV")
_row62 = daily_run.fmt_row(_s62)
assert "…" not in _row62
_rowp62 = daily_run.fmt_row(_s62, prov="mw")
assert "mUP…" in _rowp62 and f"wk {_s62.weekly.circle}…/" in _rowp62
assert _rowp62.replace("…", "") == _row62, "prov must add only the dots"
# digest-level: absent/empty prov is byte-identical to the pre-#106 render
_wo62 = daily_run.render_digest([_up62], [], {}, _B55, _R55, [], _T55,
                                fund=_f55)
assert _wo62 == daily_run.render_digest([_up62], [], {}, _B55, _R55, [],
                                        _T55, fund=_f55, prov={})
_w62 = daily_run.render_digest([_up62], [], {}, _B55, _R55, [], _T55,
                               fund=_f55, prov={"PRV": "mw"})
assert _w62.replace("…", "") == _wo62, "mark is presentation-only"
print("[62] #106 provisional-bar mark: session/weekday rule, default-off .... PASS")

# --- 63. #105 ⤴ breakout tag: fires on the whale-confirmed break only -------
# Synthetic 320-bar tape: 270 bars build the overhead shelf at 100, a dip
# bases at 90, bar 310 prints the absorption day (3x volume, probes the
# floor, closes high -> 🐳), the rally closes back under the shelf, and the
# final bar closes 101.5 over it — the §23 event, point-in-time.
import homily_breakout as _hb63


def _bars63(absorb=True):
    d0 = datetime.date(2025, 1, 1)
    day = lambda i: d0 + datetime.timedelta(days=i)
    bs = [(day(i), 100, 100.5, 99.5, 100.0, 1_000_000) for i in range(270)]
    for i in range(270, 286):
        px = 100 - (i - 269) * 0.625
        bs.append((day(i), px + 0.3, px + 0.5, px - 0.5, px, 200_000))
    bs += [(day(i), 90, 90.3, 89.8, 90.0, 200_000) for i in range(286, 310)]
    bs.append((day(310), 89.5, 92.0, 89.0, 91.5,
               3_000_000 if absorb else 200_000))
    for i, c in zip(range(311, 319),
                    (91.5, 93, 94.5, 96, 97, 98, 98.5, 99.0)):
        bs.append((day(i), c - 0.5, c + 0.3, c - 0.8, c, 400_000))
    bs.append((day(319), 100, 102, 99.5, 101.5, 500_000))
    return bs


_b63 = _bars63()
assert _hb63.breakout_today(_b63), "whale-confirmed shelf-break must fire"
assert not _hb63.breakout_today(_b63[:-1]), "no cross yet -> no tag"
assert not _hb63.breakout_today(_bars63(absorb=False)), "no 🐳 -> no tag"
assert not _hb63.breakout_today(_b63[:100]), "short history -> no tag"
# render: kwarg-gated suffix — default OFF (goldens byte-identical)
_s63, _, _ = _up("BRK")
_row63 = daily_run.fmt_row(_s63)
assert "⤴" not in _row63
_rowb63 = daily_run.fmt_row(_s63, brk=True)
assert "⤴break+🐳" in _rowb63
assert _rowb63.replace(" · ⤴break+🐳", "") == _row63, "tag must add only itself"
print("[63] #105 ⤴ breakout tag: fires/no-cross/no-whale/short, default-off . PASS")

# --- 64. #111 IPO↓ tag: data-file sanity + kwarg-gated render ---------------
# Gate clauses: (a) every ipo_ref.json entry is sane (positive ref, known
# listing type, YYYY-MM date) — a corrupt hand-collected row must fail CI,
# not silently mistag; (b) the suffix renders only via the ipo kwarg —
# default-off keeps goldens byte-identical; (c) the tag adds only itself.
import re as _re64
from homily_ipo_backtest import REFS as _refs64
assert len(_refs64) >= 30 and "_note" not in _refs64
for _tk64, _m64 in _refs64.items():
    assert _m64["ref"] > 0 and _m64["type"] in ("ipo", "direct", "spac"), _tk64
    assert _re64.fullmatch(r"20[0-2]\d-[01]\d", _m64["listed"]), _tk64
_s64, _, _ = _up("IPO")
_row64 = daily_run.fmt_row(_s64)
assert "IPO↓" not in _row64
_rowi64 = daily_run.fmt_row(_s64, ipo=True)
assert "· IPO↓" in _rowi64
assert _rowi64.replace(" · IPO↓", "") == _row64, "tag must add only itself"
print("[64] #111 IPO↓ tag: ref-file sanity, kwarg-gated, default-off ....... PASS")

print("\nAll structural assertions passed.")
