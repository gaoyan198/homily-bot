#!/usr/bin/env python3
"""
Accumulation-window duration check (#107, PRD §5l) — our windows vs Danny's prior.
==================================================================================

Danny (Jul 2024, Patreon-adapted): "my accumulation period usually lasts
3 months to 1 year" — 13 to 52 weeks. If our ⭐ windows run far shorter
than that, the #50 tranche clock (not the signal) is the binding
constraint on ever deploying a full position the way he does.

Measurement, weekly grid (D-20 precedent — 5× cheaper, loses nothing at
these horizons): every Friday-equivalent cut, `danny_signal` on the
prefix (live function, R6), record the state and the 🐳 flag. A ⭐ spell
= consecutive weekly cuts in ACCUMULATE; a 🐳 spell = consecutive cuts
with the whale footprint active. Completed spells only — open
(right-censored) spells counted separately (#82's rule). The committed
ledger (live since 2026-07-08) is too young to contain a completed spell
and is noted, not pooled.

Pure measurement, gates nothing: the output is the p25/median/p75/p90
table vs the 13–52w band, and one info-only PLAYBOOK §3 sentence citing
the measured median (ships regardless of which side it lands on — the
point is the owner knowing whether an ⭐ window is a campaign or a
moment).
"""
from homily_danny import danny_signal
from homily_data import fetch_daily
from homily_strategy_backtest import UNIV_A, UNIV_B

WARMUP_W = 60          # ~300 daily bars before monthly/chip engines are credible
GRID = 5               # weekly cuts on the daily series

DANNY_LO_W, DANNY_HI_W = 13, 52


def spells(flags):
    """[(len_weeks)] completed runs of True, plus open-run length or None."""
    out, run = [], 0
    for f in flags:
        if f:
            run += 1
        elif run:
            out.append(run)
            run = 0
    return out, (run if run else None)


def dist(xs):
    if not xs:
        return None
    s = sorted(xs)
    q = lambda p: s[min(len(s) - 1, int(p * (len(s) - 1) + 0.5))]
    return {"n": len(s), "p25": q(0.25), "median": q(0.5), "p75": q(0.75),
            "p90": q(0.9)}


def fmt(d):
    return (f"n={d['n']:>4}  p25 {d['p25']:>3}w  median {d['median']:>3}w  "
            f"p75 {d['p75']:>3}w  p90 {d['p90']:>3}w") if d else "n=0"


def scan(names, label):
    star, whale, open_star, open_whale, dead = [], [], 0, 0, []
    for sym in names:
        try:
            bars = fetch_daily(sym, rng="5y")
        except Exception:
            dead.append(sym)
            continue
        cuts = range(WARMUP_W * GRID, len(bars), GRID)
        if not cuts:
            dead.append(sym)
            continue
        st_flags, wh_flags = [], []
        for i in cuts:
            s = danny_signal(sym, bars[:i + 1])
            st_flags.append(s.state == "ACCUMULATE")
            wh_flags.append(s.whale.whale)
        cs, os_ = spells(st_flags)
        cw, ow = spells(wh_flags)
        star.extend(cs)
        whale.extend(cw)
        open_star += os_ is not None
        open_whale += ow is not None
        print(f"  {sym:<6} ⭐ spells {len(cs):>3}"
              + (f" (open {os_}w)" if os_ else "")
              + f"  🐳 spells {len(cw):>3}", flush=True)
    return dict(label=label, star=star, whale=whale, open_star=open_star,
                open_whale=open_whale, dead=dead)


if __name__ == "__main__":
    ra = scan(UNIV_A, "A current univ (HINDSIGHT BIAS)")
    rb = scan([s for s in UNIV_B if s not in UNIV_A], "B hype-2021 control")
    comb_star = ra["star"] + rb["star"]
    comb_whale = ra["whale"] + rb["whale"]
    print("\nAccumulation-window durations (weekly grid, completed spells only)")
    for r in (ra, rb):
        print(f"\n{r['label']}"
              + (f"  (unfetchable: {', '.join(r['dead'])})" if r["dead"] else ""))
        print(f"  ⭐ ACCUMULATE spells   {fmt(dist(r['star']))}  "
              f"(open: {r['open_star']})")
        print(f"  🐳 footprint spells    {fmt(dist(r['whale']))}  "
              f"(open: {r['open_whale']})")
    print(f"\nCOMBINED")
    print(f"  ⭐ ACCUMULATE spells   {fmt(dist(comb_star))}")
    print(f"  🐳 footprint spells    {fmt(dist(comb_whale))}")
    ds, dw = dist(comb_star), dist(comb_whale)
    inb = lambda d: d and DANNY_LO_W <= d["median"] <= DANNY_HI_W
    print(f"\nDanny's prior: {DANNY_LO_W}–{DANNY_HI_W}w. Our ⭐ median "
          f"{'inside' if inb(ds) else 'OUTSIDE'} the band"
          f" ({ds['median']}w); 🐳 median "
          f"{'inside' if inb(dw) else 'OUTSIDE'} ({dw['median']}w).")
    print("Ledger note: live signal log starts 2026-07-08 — no completed "
          "spell yet; replay only.")
