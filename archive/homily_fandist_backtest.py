#!/usr/bin/env python3
"""
Fan-distribution study index (#103) — builds `fandist.json`.
============================================================

Weekly-grid replay (D-20 precedent), live `danny_signal` on prefix bars,
BOTH universes pooled (the spec's rule — per-universe cells would slice
n below usefulness and invite cherry-picking). Every observation is
keyed by `homily_fandist.sig_key` — the SAME function the live board
uses (R6: no reimplementation). Forward 20/60/120d simple returns from
the cut's close; percentiles are the deterministic nearest-rank kind
(no interpolation), rounded to 4dp, keys sorted — the emitted JSON is
byte-reproducible from the same bars.

Run: python homily_fandist_backtest.py   (rewrites fandist.json)
"""
import json
import os
from homily_danny import danny_signal
from homily_data import fetch_daily
from homily_fandist import sig_key, HORIZONS
from homily_strategy_backtest import UNIV_A, UNIV_B

GRID = 5
WARMUP_W = 60
FWD = {"20": 20, "60": 60, "120": 120}
assert tuple(FWD) == HORIZONS

OUT = os.path.join(os.path.dirname(__file__), "fandist.json")


def collect(sym, bars, obs):
    closes = [b[4] for b in bars]
    for i in range(WARMUP_W * GRID, len(bars), GRID):
        key = sig_key(danny_signal(sym, bars[:i + 1]))
        for h, n in FWD.items():
            if i + n < len(closes):
                obs.setdefault(key, {}).setdefault(h, []).append(
                    closes[i + n] / closes[i] - 1)


def _q(xs, p):
    """Deterministic nearest-rank percentile (validate [65] re-checks it)."""
    s = sorted(xs)
    return s[min(len(s) - 1, int(p * (len(s) - 1) + 0.5))]


def build_table(obs):
    """obs {key: {h: [rets]}} -> {key: {h: [n, p10, p25, p50, p75]}}."""
    table = {}
    for key in sorted(obs):
        cell = {}
        for h in HORIZONS:
            xs = obs[key].get(h, [])
            cell[h] = ([len(xs)] + [round(_q(xs, p), 4)
                                    for p in (0.10, 0.25, 0.50, 0.75)]
                       if xs else [0, 0.0, 0.0, 0.0, 0.0])
        table[key] = cell
    return table


def emit_json(table, built, protocol):
    doc = {"_meta": {"built": built, "protocol": protocol,
                     "grid": GRID, "warmup_w": WARMUP_W}}
    doc.update(table)
    return json.dumps(doc, indent=1, sort_keys=False, ensure_ascii=False) + "\n"


if __name__ == "__main__":
    import datetime
    univ = UNIV_A + [s for s in UNIV_B if s not in UNIV_A]
    obs, dead = {}, []
    for sym in univ:
        try:
            bars = fetch_daily(sym, rng="5y")
        except Exception:
            dead.append(sym)
            continue
        if len(bars) < WARMUP_W * GRID + 130:
            dead.append(sym)
            continue
        collect(sym, bars, obs)
        print(f"  {sym:<6} cumulative keys {len(obs):>3}", flush=True)
    table = build_table(obs)
    txt = emit_json(table, str(datetime.date.today()),
                    "5y weekly-grid prefix replay, univ A+B pooled")
    open(OUT, "w").write(txt)
    print(f"\nfandist.json written — {len(table)} confluence cells"
          + (f" (unfetchable/short: {', '.join(dead)})" if dead else ""))
    for key, cell in sorted(table.items(),
                            key=lambda kv: -kv[1]["60"][0])[:12]:
        n, p10, p25, p50, p75 = cell["60"]
        print(f"  {key:<28} n={n:>5}  60d p10 {p10*100:+6.1f}%  "
              f"med {p50*100:+6.1f}%  p75 {p75*100:+6.1f}%")
