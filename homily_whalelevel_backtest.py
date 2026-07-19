#!/usr/bin/env python3
"""
Whale-level thresholds study (#109, PRD §5m) — "50% to run, 75% to surge".
==========================================================================

Danny quotes Panel-3 whale accumulation as an absolute 0–100% level with
named thresholds: whales "need to reach 50% for the stock to run and 75%
to surge" (WULF 94% vs MARA 9.1%, Jun 2024; FICO 92%; AMD 93.4%). Our 🐳
is a binary dip-context tag and #80's `whale_rank` a cross-sectional
rank — nobody here owns level semantics. His % is proprietary; this
tests whether ANY honest absolute level built from public OHLCV carries
his threshold *shape*. We never claim to reproduce his numbers.

Pre-registered proxy (fixed here before the run, no tuning after):

    acc_share  = share of the trailing 60 sessions where the close lands
                 in the upper half of the day's range on >= trailing-50d
                 average volume (the classic accumulation-day count)
    flow_share = share of the trailing 60 sessions where OBV rose
    LEVEL      = 100 * (acc_share + flow_share) / 2

Pooled day-level observations (weekly grid to tame autocorrelation),
forward 60/120d, both universes. Cuts: level quintiles (within-universe)
and Danny's absolute marks (<50 / 50–75 / >=75).

Pre-committed verdicts:
  SEPARATION (ships `wh:n%` next to whale_rank, own session, info-only):
    top quintile beats bottom quintile at BOTH horizons on BOTH universes.
  KINK (descriptive only, no ship semantics): 50–75 beats <50 AND >=75
    beats 50–75 at both horizons on the combined pool.
  Anything else → null, closed, recorded.
"""
from homily_data import fetch_daily
from homily_strategy_backtest import UNIV_A, UNIV_B

WIN = 60
VOL_WIN = 50
WARMUP = 150
GRID = 5
FWD = (60, 120)


def levels(bars):
    """LEVEL per bar index (None until warmed)."""
    n = len(bars)
    acc = [False] * n
    obv_up = [False] * n
    obv = 0.0
    prev_obv = 0.0
    for i, (d, o, h, l, c, v) in enumerate(bars):
        if i:
            pc = bars[i - 1][4]
            obv += v if c > pc else -v if c < pc else 0.0
        obv_up[i] = obv > prev_obv
        prev_obv = obv
        if i >= VOL_WIN:
            avg_v = sum(b[5] for b in bars[i - VOL_WIN:i]) / VOL_WIN
            rng = h - l
            acc[i] = rng > 0 and (c - l) / rng >= 0.5 and v >= avg_v
    out = [None] * n
    for i in range(WARMUP, n):
        a = sum(acc[i - WIN + 1:i + 1]) / WIN
        f = sum(obv_up[i - WIN + 1:i + 1]) / WIN
        out[i] = 100 * (a + f) / 2
    return out


def fwd_ret(closes, i, n):
    if i + n >= len(closes):
        return None
    return closes[i + n] / closes[i] - 1


def scan(names, label):
    obs = []          # (level, {fwd: ret})
    dead = []
    for sym in names:
        try:
            bars = fetch_daily(sym, rng="5y")
        except Exception:
            dead.append(sym)
            continue
        if len(bars) < WARMUP + 130:
            dead.append(sym)
            continue
        closes = [b[4] for b in bars]
        lv = levels(bars)
        for i in range(WARMUP, len(bars), GRID):
            if lv[i] is None:
                continue
            rets = {n: fwd_ret(closes, i, n) for n in FWD}
            if rets[FWD[0]] is not None:
                obs.append((lv[i], rets))
        print(f"  {sym:<6} obs {len(obs):>6} cumulative", flush=True)
    return dict(label=label, obs=obs, dead=dead)


AVG = lambda xs: sum(xs) / len(xs) if xs else float("nan")


def bucket_stats(obs, lo, hi):
    xs = [(r) for l, r in obs if lo <= l < hi]
    return {n: AVG([r[n] for r in xs if r[n] is not None]) for n in FWD}, len(xs)


def report(r):
    obs = r["obs"]
    lv_sorted = sorted(l for l, _ in obs)
    q = lambda p: lv_sorted[min(len(lv_sorted) - 1, int(p * len(lv_sorted)))]
    quints = [q(k / 5) for k in range(6)]
    quints[-1] = quints[-1] + 1
    print(f"\n{r['label']}  ({len(obs)} weekly-grid obs"
          + (f"; unfetchable/short: {', '.join(r['dead'])}" if r["dead"] else "")
          + f")\n  level distribution: p10 {q(0.1):.0f}  median {q(0.5):.0f}"
          f"  p90 {q(0.9):.0f}  max {lv_sorted[-1]:.0f}")
    print(f"  {'bucket':<16}{'n':>7}{'fwd60':>8}{'fwd120':>8}")
    rows = {}
    for k in range(5):
        st, n = bucket_stats(obs, quints[k], quints[k + 1])
        rows[f"Q{k+1}"] = st
        print(f"  Q{k+1} [{quints[k]:>4.0f},{quints[k+1]:>4.0f})"
              f"{n:>7}{st[60]*100:>7.1f}%{st[120]*100:>7.1f}%")
    for name, lo, hi in (("<50", 0, 50), ("50-75", 50, 75), (">=75", 75, 999)):
        st, n = bucket_stats(obs, lo, hi)
        rows[name] = st
        print(f"  {name:<16}{n:>7}{st[60]*100:>7.1f}%{st[120]*100:>7.1f}%")
    return rows


if __name__ == "__main__":
    ra = scan(UNIV_A, "A current univ (HINDSIGHT BIAS)")
    rb = scan([s for s in UNIV_B if s not in UNIV_A], "B hype-2021 control")
    rows_a = report(ra)
    rows_b = report(rb)
    comb = dict(label="COMBINED", obs=ra["obs"] + rb["obs"], dead=[])
    rows_c = report(comb)
    sep = all(rows["Q5"][n] > rows["Q1"][n] for rows in (rows_a, rows_b)
              for n in FWD)
    kink = all(rows_c["50-75"][n] > rows_c["<50"][n]
               and rows_c[">=75"][n] > rows_c["50-75"][n] for n in FWD)
    print(f"\nPre-committed verdicts:")
    print(f"  SEPARATION (Q5>Q1, both horizons, both universes): "
          f"{'PASS — wh:n% column earns its own gated session' if sep else 'NULL'}")
    print(f"  KINK at 50/75 (descriptive): {'present' if kink else 'absent'}")
