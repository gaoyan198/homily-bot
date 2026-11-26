#!/usr/bin/env python3
"""
Triple-red continuation stat (#108, PRD §5l) — IBRX Feb 2026.
=============================================================

Danny: "Triple Red (Bullish) candles remain in force despite the recent
retracement" — three consecutive daily RED closes read as a continuation
marker. Rides #82's harness pattern: the LIVE `daily_candle` on close
prefixes decides the colour (R6 — prefix EMA/MACD equal the full-series
values, so one O(n) pass over the full series gives every day's printed
colour; a spot-check below asserts the equality against the real
prefix call). Event = the day a RED run first reaches 3; re-arms after
the run breaks. Forward 5/10/20d vs the unconditional baseline over the
same eligible days, both universes incl. the 2021 control.

Pre-committed verdict rule (written before the run, #82's own precedent
— its ribbon conditioning ran null and shipped nothing): a `3R` row
suffix (one word, info-only) ships ONLY if event days beat the baseline
at ALL THREE horizons on BOTH universes. Anything else → null, closed,
nothing ships.
"""
import random
from homily_clone import ema, macd
from homily_danny import daily_candle
from homily_data import fetch_daily
from homily_strategy_backtest import UNIV_A, UNIV_B

FWD = (5, 10, 20)
WARMUP = 60
RUN_LEN = 3


def red_days(closes):
    """[bool RED per day] in one pass — R6 prefix equality."""
    e10 = ema(closes, 10)
    _, _, hist = macd(closes)
    return [c > e and h > 0 for c, e, h in zip(closes, e10, hist)]


def events(reds, warmup=WARMUP):
    """Days where a RED run first reaches RUN_LEN."""
    out, run = [], 0
    for i, r in enumerate(reds):
        run = run + 1 if r else 0
        if run == RUN_LEN and i >= warmup:
            out.append(i)
    return out


def fwd_ret(closes, i, n):
    if i + n >= len(closes):
        return None
    return closes[i + n] / closes[i] - 1


def scan(names, label):
    ev = {n: [] for n in FWD}
    base = {n: [] for n in FWD}
    n_ev, dead = 0, []
    for sym in names:
        try:
            bars = fetch_daily(sym, rng="5y")
        except Exception:
            dead.append(sym)
            continue
        closes = [b[4] for b in bars]
        if len(closes) < WARMUP + 50:
            dead.append(sym)
            continue
        reds = red_days(closes)
        # R6 spot-check: the one-pass colours equal the live prefix call
        for i in random.Random(42).sample(range(WARMUP, len(closes)), 5):
            assert reds[i] == (daily_candle(closes[:i + 1]) == "RED"), sym
        for i in range(WARMUP, len(closes)):
            for n in FWD:
                r = fwd_ret(closes, i, n)
                if r is not None:
                    base[n].append(r)
        for i in events(reds):
            n_ev += 1
            for n in FWD:
                r = fwd_ret(closes, i, n)
                if r is not None:
                    ev[n].append(r)
        print(f"  {sym:<6} events so far {n_ev:>4}", flush=True)
    return dict(label=label, ev=ev, base=base, n_ev=n_ev, dead=dead)


AVG = lambda xs: sum(xs) / len(xs) if xs else float("nan")
WIN = lambda xs: 100 * sum(x > 0 for x in xs) / len(xs) if xs else float("nan")


def report(r):
    print(f"\n{r['label']}  ({r['n_ev']} triple-red events"
          + (f"; unfetchable/short: {', '.join(r['dead'])}" if r["dead"] else "")
          + ")")
    print(f"{'fwd':>5}{'avg ret':>9}{'win%':>7}{'baseline':>10}{'base win%':>11}{'n':>7}")
    for n in FWD:
        xs = r["ev"][n]
        print(f"{n:>4}d{AVG(xs)*100:>8.2f}%{WIN(xs):>6.0f}%"
              f"{AVG(r['base'][n])*100:>9.2f}%{WIN(r['base'][n]):>10.0f}%{len(xs):>7}")


def beats(r):
    return all(AVG(r["ev"][n]) > AVG(r["base"][n]) for n in FWD)


if __name__ == "__main__":
    ra = scan(UNIV_A, "A current univ (HINDSIGHT BIAS)")
    rb = scan([s for s in UNIV_B if s not in UNIV_A], "B hype-2021 control")
    comb = dict(label="COMBINED", dead=ra["dead"] + rb["dead"],
                n_ev=ra["n_ev"] + rb["n_ev"],
                ev={n: ra["ev"][n] + rb["ev"][n] for n in FWD},
                base={n: ra["base"][n] + rb["base"][n] for n in FWD})
    for r in (ra, rb, comb):
        report(r)
    ok = beats(ra) and beats(rb)
    print(f"\nPre-committed rule: `3R` suffix ships only if events beat "
          f"baseline at ALL horizons on BOTH universes -> "
          f"{'PASS — suffix earns a session' if ok else 'NULL — closed, nothing ships'}")
