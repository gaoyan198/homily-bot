#!/usr/bin/env python3
"""
POC-cross event study (#104, PRD §5l) — do POC crosses carry information?
=========================================================================

Danny's level hierarchy (JD Feb 2026) puts the POC above candle colour,
with explicit semantics from his definition posts: "a close above the POC
is bullish; a close below it may signal a pullback, correction, or the
start of a downtrend." We compute the chip POC every run
(`homily_chips.build_profile`) and print it with zero event semantics.
This measures whether the cross itself predicts anything.

Design (no look-ahead): for day i the reference level is the PRIOR day's
POC — `build_profile(bars[:i]).poc`, bars through i-1 only. A DOWN cross
fires when yesterday's close sat above yesterday's reference and today's
close is below today's; UP is the mirror. Forward 20/60d returns vs the
unconditional baseline over the same eligible days, per universe and
combined, plus the down-cross split by the LIVE digest state on the event
day (danny_signal on the prefix — R6): Danny's "pullback" read is a POC
loss inside an intact trend, so the uptrend cut (⭐/🟢/🟡) is reported
next to the broken-trend cut (⚪/🔵).

Pre-committed verdict rule (written before the run, #79 precedent):

  POC↓ joins #102's tell list (info-only, dated) ONLY if down-cross days
  underperform the unconditional baseline at BOTH horizons on the
  COMBINED pool AND the direction agrees (underperform at both horizons)
  in EACH universe separately. The up-cross earns at most a row note
  under the mirrored rule. Anything else → null, closed, nothing ships.
"""
from homily_chips import build_profile
from homily_danny import danny_signal
from homily_data import fetch_daily
from homily_strategy_backtest import UNIV_A, UNIV_B

FWD = (20, 60)
WARMUP = 300          # bars before the decayed chip profile is credible
UPTREND = ("ACCUMULATE", "HOLD", "PULLBACK")


def above_series(bars, warmup=WARMUP):
    """[(i, close_i > prior-day POC)] for i >= warmup."""
    out = []
    for i in range(warmup, len(bars)):
        poc = build_profile(bars[:i]).poc
        out.append((i, bars[i][4] > poc))
    return out


def crosses(above):
    """-> [(i, 'DOWN'|'UP')] state-flip days."""
    out = []
    for (pi, pa), (i, a) in zip(above, above[1:]):
        if pa and not a:
            out.append((i, "DOWN"))
        elif a and not pa:
            out.append((i, "UP"))
    return out


def fwd_ret(closes, i, n):
    if i + n >= len(closes):
        return None
    return closes[i + n] / closes[i] - 1


def scan(names, label):
    ev = {("DOWN", n): [] for n in FWD}
    ev.update({("UP", n): [] for n in FWD})
    state_cut = {("uptrend", n): [] for n in FWD}
    state_cut.update({("broken", n): [] for n in FWD})
    base = {n: [] for n in FWD}
    n_ev, dead = {"DOWN": 0, "UP": 0}, []
    for sym in names:
        try:
            bars = fetch_daily(sym, rng="5y")
        except Exception:
            dead.append(sym)
            continue
        if len(bars) < WARMUP + 100:
            dead.append(sym)
            continue
        closes = [b[4] for b in bars]
        for i in range(WARMUP + 1, len(closes)):
            for n in FWD:
                r = fwd_ret(closes, i, n)
                if r is not None:
                    base[n].append(r)
        for i, side in crosses(above_series(bars)):
            n_ev[side] += 1
            cut = None
            if side == "DOWN":
                st = danny_signal(sym, bars[:i + 1]).state
                cut = "uptrend" if st in UPTREND else "broken"
            for n in FWD:
                r = fwd_ret(closes, i, n)
                if r is not None:
                    ev[(side, n)].append(r)
                    if cut:
                        state_cut[(cut, n)].append(r)
        print(f"  {sym:<6} {n_ev['DOWN']:>4}↓ {n_ev['UP']:>4}↑ cumulative",
              flush=True)
    return dict(label=label, ev=ev, base=base, n_ev=n_ev, dead=dead,
                state_cut=state_cut)


AVG = lambda xs: sum(xs) / len(xs) if xs else float("nan")
WIN = lambda xs: 100 * sum(x > 0 for x in xs) / len(xs) if xs else float("nan")


def report(r):
    print(f"\n{r['label']}  ({r['n_ev']['DOWN']}↓ / {r['n_ev']['UP']}↑ events"
          + (f"; unfetchable/short: {', '.join(r['dead'])}" if r["dead"] else "")
          + ")")
    print(f"{'event':<16}{'fwd':>5}{'avg ret':>9}{'win%':>7}{'baseline':>10}{'n':>7}")
    for side in ("DOWN", "UP"):
        for n in FWD:
            xs = r["ev"][(side, n)]
            print(f"POC {side:<12}{n:>4}d{AVG(xs)*100:>8.1f}%{WIN(xs):>6.0f}%"
                  f"{AVG(r['base'][n])*100:>9.1f}%{len(xs):>7}")
    for cut in ("uptrend", "broken"):
        for n in FWD:
            xs = r["state_cut"][(cut, n)]
            print(f"  ↓ {cut:<12}{n:>4}d{AVG(xs)*100:>8.1f}%{WIN(xs):>6.0f}%"
                  f"{AVG(r['base'][n])*100:>9.1f}%{len(xs):>7}")


def under(r, side, sign):
    """True if `side` events differ from baseline with `sign` at both
    horizons (sign=-1: underperform, +1: outperform)."""
    return all(sign * (AVG(r["ev"][(side, n)]) - AVG(r["base"][n])) > 0
               for n in FWD)


if __name__ == "__main__":
    ra = scan(UNIV_A, "A current univ (HINDSIGHT BIAS)")
    rb = scan([s for s in UNIV_B if s not in UNIV_A], "B hype-2021 control")
    comb = dict(label="COMBINED", dead=ra["dead"] + rb["dead"],
                n_ev={k: ra["n_ev"][k] + rb["n_ev"][k] for k in ra["n_ev"]},
                ev={k: ra["ev"][k] + rb["ev"][k] for k in ra["ev"]},
                base={k: ra["base"][k] + rb["base"][k] for k in ra["base"]},
                state_cut={k: ra["state_cut"][k] + rb["state_cut"][k]
                           for k in ra["state_cut"]})
    for r in (ra, rb, comb):
        report(r)
    down = under(comb, "DOWN", -1) and under(ra, "DOWN", -1) and under(rb, "DOWN", -1)
    up = under(comb, "UP", +1) and under(ra, "UP", +1) and under(rb, "UP", +1)
    print("\nPre-committed verdicts:")
    print(f"  POC↓ tell (joins #102 only on pass): "
          f"{'PASS' if down else 'NULL — closed, nothing ships'}")
    print(f"  POC↑ row note: {'PASS' if up else 'NULL — closed, nothing ships'}")
