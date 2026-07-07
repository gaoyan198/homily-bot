#!/usr/bin/env python3
"""
Golden-file digest tests (backlog #49) — the executing model's safety net.
==========================================================================

Fixture bars -> the LIVE engines (danny_signal / conviction, never a
reimplementation, per EXECUTION.md R6) -> daily_run.render_digest() -> compared
byte-for-byte against committed golden text under tests/. Any refactor that
silently changes a printed digest row now fails `python homily_validate.py`.
This is why the plan says build it FIRST, before any digest-touching change.

Offline and deterministic: render_digest() takes every network/clock/state
input as an argument, so nothing here fetches, calls market_regime(),
daily_refine(), or reads the wall clock. Two scenarios:

  populated  regime line, all state groups, whale/young/at-support rows,
             a rocket, discovery hits, the full legend + algo-health footer
  empty      regime unavailable, both "nothing today" fallbacks, fetch-error
             line — the branches the populated case can't reach

Regenerate DELIBERATELY (and eyeball the git diff) after an intended change:

    python homily_golden.py --update

Gate: none (test infra).
"""
import os
import sys
import difflib
import datetime

from homily_danny import danny_signal
from homily_conviction import conviction
from homily_regime import Regime
from daily_run import render_digest, ORDER

HERE = os.path.dirname(os.path.abspath(__file__))
GOLDEN_DIR = os.path.join(HERE, "tests")

# --- deterministic fixture bars (same builders as homily_validate.py) -------
D0 = datetime.date(2024, 1, 1)


def _bars(prices, vols, spread=0.5):
    return [(D0 + datetime.timedelta(days=i), p, p + spread, p - spread, p, v)
            for i, (p, v) in enumerate(zip(prices, vols))]


def _vbars(specs):
    """specs: (price, half-range) -> dated OHLCV bars."""
    return [(D0 + datetime.timedelta(days=i), p, p + r, p - r, p, 1e6)
            for i, (p, r) in enumerate(specs)]


def _ohlcv(rows):
    """rows: (o, h, l, c, v) -> dated 6-tuple bars."""
    return [(D0 + datetime.timedelta(days=i), o, h, l, c, v)
            for i, (o, h, l, c, v) in enumerate(rows)]


# ~8%/yr benchmark closes; conviction() measures relative strength against it
SPY = [100.0 * 1.0003 ** i for i in range(900)]


def _sig(ticker, bars, young=False):
    """(DannySignal, Conviction, young) tuple, exactly as screen() emits."""
    s = danny_signal(ticker, bars)
    return s, conviction(s, bars, SPY), young


# --- archetypes: each drives the engines into a distinct rendered branch -----
def _up(tk, young=False):                       # steady uptrend -> ACCUMULATE/HOLD
    return _sig(tk, _bars([100 * 1.003 ** i for i in range(900)],
                          [1e6] * 900), young)


def _dn(tk, young=False):                        # steady downtrend -> CAUTION
    return _sig(tk, _bars([100 * 0.997 ** i for i in range(900)],
                          [1e6] * 900), young)


def _bottoming(tk, young=False):                 # decline + vol-hole breakout
    vol_dn = [100 * 0.997 ** i for i in range(800)]
    specs = ([(p, p * 0.03) for p in vol_dn]
             + [(vol_dn[-1], vol_dn[-1] * 0.002)] * 10
             + [(vol_dn[-1] * 1.05, vol_dn[-1] * 0.01)] * 3)
    return _sig(tk, _vbars(specs), young)


def _leader(tk, young=False):                    # strong small-$vol leader -> rocket
    px = [10 * 1.004 ** i for i in range(900)]
    bars = [(d, o, h, l, c, 2e6)
            for d, o, h, l, c, v in _vbars([(p, p * 0.01) for p in px])]
    return _sig(tk, bars, young)


def _whale(tk, young=False):                     # absorbed dip -> CAUTION + 🐳
    flat = [(100.0, 101.0, 99.0, 100.0, 1e6)] * 100
    absorbed = [(p + 0.5, p + 0.5, p - 2.0, p, 3e6)
                for p in [100 - 0.8 * (k + 1) for k in range(15)]]
    return _sig(tk, _ohlcv(flat + absorbed), young)


# --- fixed non-signal inputs -------------------------------------------------
BULL = Regime(
    "BULL",
    {"SPY": (802.05, 740.10, 8.37, True),
     "QQQ": (601.20, 548.90, 9.53, True)},
    "stay invested; adds via ⭐/🚀 screens; sell trigger = BOTH month-end "
    "closes below 10m SMA")

# (champion, challenger, oos_chal, oos_def, champ_oos, adopted) as daily_refine
REFINE = ({"params": {"ef": 10, "es": 30, "inv": "RED"}, "since": "2026-07-01"},
          {"ef": 10, "es": 30, "inv": "RED"}, 1.10, 1.05, 1.23, False)

# stand-in for fund_tag(): deterministic, no EDGAR call
def _fund(_ticker):
    return "F:2/3"


TODAY = datetime.date(2026, 7, 7)


# --- scenarios ---------------------------------------------------------------
def scenario_populated():
    held = [_up("AAA"), _dn("BBB"), _bottoming("CCC", young=True), _whale("WHL")]
    held.sort(key=lambda x: (ORDER[x[0].state], x[0].ticker))  # as screen() does
    disco = [_leader("LEAD"), _bottoming("GEM")]
    return render_digest(held, disco, {}, BULL, REFINE, [], TODAY, fund=_fund)


def scenario_empty():
    # one held CAUTION name (no rocket, no discovery hit), regime unavailable,
    # and a fetch failure -> exercises every fallback branch at once
    return render_digest([_dn("SOLO")], [_dn("NOHIT")], {}, None, REFINE,
                         ["ZZZ"], TODAY, fund=_fund)


SCENARIOS = {"populated": scenario_populated, "empty": scenario_empty}


def _path(name):
    return os.path.join(GOLDEN_DIR, f"digest_{name}.golden.txt")


def update():
    os.makedirs(GOLDEN_DIR, exist_ok=True)
    for name, fn in SCENARIOS.items():
        with open(_path(name), "w") as f:
            f.write(fn())
    print(f"[golden] wrote {len(SCENARIOS)} scenario(s) to {GOLDEN_DIR}/")


def run():
    """Assert every scenario still renders byte-exact. Raises on drift."""
    for name, fn in SCENARIOS.items():
        got = fn()
        try:
            with open(_path(name)) as f:
                want = f.read()
        except FileNotFoundError:
            raise AssertionError(
                f"golden missing: {_path(name)} — run "
                "`python homily_golden.py --update` and commit it")
        if got != want:
            diff = "\n".join(difflib.unified_diff(
                want.splitlines(), got.splitlines(),
                fromfile=f"{name}.golden", tofile=f"{name}.current",
                lineterm=""))
            raise AssertionError(
                f"[golden] digest changed for scenario '{name}':\n{diff}\n"
                "If this change is intentional, run "
                "`python homily_golden.py --update` and commit the new golden.")
    print(f"[16] Golden digest: {len(SCENARIOS)} scenarios render byte-exact . PASS")


if __name__ == "__main__":
    if "--update" in sys.argv:
        update()
    else:
        run()
