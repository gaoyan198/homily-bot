#!/usr/bin/env python3
"""
Retail-crowding warning study (#110, PRD §5m) — the CELH Aug-2024 tell.
=======================================================================

Danny's bearish checklist counts "lots of green bars (heavy retail
accumulation)" WITH "no red bar (whale accumulation)" as a distribution
tell — activity without committed buyers. The mirror of 🐳-present,
which #12 measured and shipped; whale-ABSENCE-under-heat has never been
cut here.

Tag (pre-registered; all point-in-time on prefix bars, weekly grid):

    rally     close >= 5% above the 60d closing low (mirror of the
              #12/#79 dip definition)
    heat      trailing-20d avg volume >= 1.3x trailing-50d avg
              (VOL_MULT reused from the frozen whale engine)
    no whale  the rally-compatible footprints both absent — no
              absorption print, no shelf replenishment (whale_read on
              the prefix; its third footprint, flow divergence, is
              dip-gated and cannot fire in a rally — recorded honestly:
              this tag tests TWO absences, not three)
    churn     OBV today <= OBV 21 sessions ago — the heat produced no
              net flow while price rose (the crowd is churning, nobody
              is accumulating)

Forward 60/120d vs (a) the unconditional baseline and (b) untagged
rally days — the proper control, rallies as a class run hot (#79's own
design). Verdict rule copied verbatim from #79: the tag earns a #102
tell candidacy ONLY if tagged days underperform BOTH baselines at BOTH
horizons on the combined universe. Null → closed, recorded. Scope guard
regardless of outcome: held satellites/🚀 candidacy only — core names
and the index never get a sell-flavoured tag.
"""
from homily_chips import build_profile
from homily_data import fetch_daily
from homily_strategy_backtest import UNIV_A, UNIV_B
from homily_whale import whale_read, VOL_MULT

FWD = (60, 120)
WARMUP = 300
GRID = 5
RALLY_WIN = 60
RALLY_PCT = 5.0
OBV_LOOK = 21


def obv_series(bars):
    obv, out = 0.0, []
    for i, (d, o, h, l, c, v) in enumerate(bars):
        if i:
            pc = bars[i - 1][4]
            obv += v if c > pc else -v if c < pc else 0.0
        out.append(obv)
    return out


def fwd_ret(closes, i, n):
    if i + n >= len(closes):
        return None
    return closes[i + n] / closes[i] - 1


def scan(names, label):
    tag = {n: [] for n in FWD}
    rally_un = {n: [] for n in FWD}
    base = {n: [] for n in FWD}
    n_tag = n_rally = 0
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
        vols = [b[5] for b in bars]
        obv = obv_series(bars)
        for i in range(WARMUP, len(bars), GRID):
            rets = {n: fwd_ret(closes, i, n) for n in FWD}
            if rets[FWD[0]] is None:
                continue
            for n in FWD:
                if rets[n] is not None:
                    base[n].append(rets[n])
            lo60 = min(closes[i - RALLY_WIN + 1:i + 1])
            rally = closes[i] >= lo60 * (1 + RALLY_PCT / 100)
            if not rally:
                continue
            n_rally += 1
            hot = (sum(vols[i - 19:i + 1]) / 20
                   >= VOL_MULT * sum(vols[i - 49:i + 1]) / 50)
            churn = obv[i] <= obv[i - OBV_LOOK]
            tagged = False
            if hot and churn:
                pre = bars[:i + 1]
                p = build_profile(pre)
                sh = p.support[0][0] if p.support else None
                w = whale_read(pre, sh)
                tagged = not w.absorption and not w.shelf_stable
            for n in FWD:
                if rets[n] is None:
                    continue
                (tag if tagged else rally_un)[n].append(rets[n])
            n_tag += tagged
        print(f"  {sym:<6} tagged {n_tag:>5} / rally {n_rally:>6} cumulative",
              flush=True)
    return dict(label=label, tag=tag, rally_un=rally_un, base=base,
                n_tag=n_tag, dead=dead)


AVG = lambda xs: sum(xs) / len(xs) if xs else float("nan")
WIN = lambda xs: 100 * sum(x > 0 for x in xs) / len(xs) if xs else float("nan")


def report(r):
    print(f"\n{r['label']}  ({r['n_tag']} tagged obs"
          + (f"; unfetchable/short: {', '.join(r['dead'])}" if r["dead"] else "")
          + ")")
    print(f"  {'arm':<22}{'fwd':>5}{'avg ret':>9}{'win%':>7}{'n':>7}")
    for arm, xs in (("RETAIL-HEAT tag", r["tag"]),
                    ("untagged rally days", r["rally_un"]),
                    ("unconditional", r["base"])):
        for n in FWD:
            print(f"  {arm:<22}{n:>4}d{AVG(xs[n])*100:>8.1f}%"
                  f"{WIN(xs[n]):>6.0f}%{len(xs[n]):>7}")


if __name__ == "__main__":
    ra = scan(UNIV_A, "A current univ (HINDSIGHT BIAS)")
    rb = scan([s for s in UNIV_B if s not in UNIV_A], "B hype-2021 control")
    comb = dict(label="COMBINED", n_tag=ra["n_tag"] + rb["n_tag"], dead=[],
                **{k: {n: ra[k][n] + rb[k][n] for n in FWD}
                   for k in ("tag", "rally_un", "base")})
    for r in (ra, rb, comb):
        report(r)
    under = all(AVG(comb["tag"][n]) < AVG(comb[b][n])
                for n in FWD for b in ("rally_un", "base"))
    print(f"\nPre-committed rule (#79 verbatim): tell candidacy only if the "
          f"tag underperforms BOTH baselines at BOTH horizons, combined -> "
          f"{'PASS — #102 tell candidacy earns its own session' if under else 'NULL — closed, nothing ships'}")
