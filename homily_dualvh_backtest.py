#!/usr/bin/env python3
"""
#131 · Dual volatility-hole bottom marker (PRD §5n, INTC Jul 2026).
===================================================================

Danny's INTC monthly bottom call (Jul 1 2026) rests on TWO volatility
holes stacked at one base — "dual volatility holes" marked the major
long-term bottom at $25–27. Our `find_hole` returns only the most recent
cluster, so a second hole forming while the first is unresolved is
structurally invisible to the live engine. This study measures whether
that dual shape carries information the single hole does not.

RULE — FROZEN BEFORE THE FIRST RUN (do not renegotiate after numbers):

  Detector (point-in-time, live `find_hole` on truncated bars — R6; only
  the walker lives here, same pattern as homily_vol_backtest /
  homily_mtf_vol_backtest):
    * walk each daily series; at bar i call find_hole(bars[:i+1]);
    * an INSIDE print arms the hole; its cluster end = i − age. A later
      INSIDE print whose cluster end advances by ≤ MAX_GAP bars is the
      SAME cluster growing (zone/end update, flags kept); an advance
      > MAX_GAP is a DISTINCT new cluster;
    * DUAL: a distinct new cluster appears while the previously armed
      hole is UNRESOLVED (no BREAKOUT/BREAKDOWN printed) and the gap
      between cluster ends is ≤ N_BARS = 40 trading days. A chain of ≥2
      qualifying holes keeps the flag. A gap > 40 bars re-arms as SINGLE;
    * event = first close resolving the armed zone (the walker's usual
      BREAKOUT/BREAKDOWN match), tagged with the dual flag.
  Scope: the headline comparison is BOTTOM markers only — events whose
  resolving hole has trend_before == "DOWN" (the 🔵 process) and status
  BREAKOUT. Everything else is printed as context.
  Measure: forward 60d and 120d returns from the event close; 5y daily
  bars; universes A (current) and B (hype-2021 control) + ALL, per
  homily_strategy_backtest.
  🐳/⤴ decorations and coarser timeframes are OUT of scope (the
  monthly-TF half of the INTC claim already ran NULL — #77).

  VERDICT (pre-registered): PASS iff, on ALL names combined,
    (i)  n(dual bottoming BREAKOUT with fwd60 available) ≥ 20, and
    (ii) mean fwd60  (dual) ≥ mean fwd60  (single bottoming BREAKOUT), and
    (iii)mean fwd120 (dual) ≥ mean fwd120 (single bottoming BREAKOUT).
  Anything else = NULL → item closed honestly (#77 precedent). A PASS
  ships nothing from this session (Part III rule 5): the would-be
  surface, a display-only `×2` mark on the existing 🔵 row, needs its own
  session, validate case and untouched goldens.
"""
from homily_data import fetch_daily
from homily_strategy_backtest import UNIV_A, UNIV_B
from homily_vol import find_hole, MAX_GAP, REF_WIN, VOL_WIN

N_BARS = 40                # max bars between cluster ends for a dual chain
FWD = (60, 120)
WARMUP = REF_WIN + VOL_WIN + 5


def events(bars):
    """(i, status, trend_before, dual) — first resolution of each armed
    hole; dual per the frozen rule."""
    out = []
    armed = None               # [zone, cluster_end, dual]
    for i in range(WARMUP, len(bars) - 1):
        h = find_hole(bars[:i + 1])
        if h is None:
            continue
        zone = (round(h.lower, 4), round(h.upper, 4))
        cend = i - h.age
        if h.status == "INSIDE":
            if armed is None:
                armed = [zone, cend, False]
            elif cend - armed[1] > MAX_GAP:        # distinct new cluster
                dual = cend - armed[1] <= N_BARS   # ...while armed unresolved
                armed = [zone, cend, dual]
            else:                                  # same cluster growing
                armed[0], armed[1] = zone, cend
        elif armed is not None and zone == armed[0]:
            out.append((i, h.status, h.trend_before, armed[2]))
            armed = None
    return out


def fwd_ret(closes, i, n):
    return closes[i + n] / closes[i] - 1 if i + n < len(closes) else None


avg = lambda xs: sum(xs) / len(xs) if xs else float("nan")
win = lambda xs: 100 * sum(x > 0 for x in xs) / len(xs) if xs else float("nan")


def main():
    univ_all = UNIV_A + [n for n in UNIV_B if n not in UNIV_A]
    data, dead = {}, []
    for n in univ_all:
        try:
            data[n] = fetch_daily(n, rng="5y")
        except Exception:
            dead.append(n)
    groups = {"A current": [n for n in UNIV_A if n in data],
              "B hype-2021": [n for n in UNIV_B if n in data],
              "ALL": sorted(data)}

    # rets[(sym, arm, status, trend, n)] = [fwd returns]
    rets, counts = {}, {}
    for sym in groups["ALL"]:
        bars = data[sym]
        closes = [b[4] for b in bars]
        for i, status, trend, dual in events(bars):
            arm = "DUAL" if dual else "SINGLE"
            counts[(sym, arm, status, trend)] = \
                counts.get((sym, arm, status, trend), 0) + 1
            for n in FWD:
                r = fwd_ret(closes, i, n)
                if r is not None:
                    rets.setdefault((sym, arm, status, trend, n), []).append(r)
        print(f"  scanned {sym}", flush=True)
    if dead:
        print(f"  (unfetchable: {', '.join(dead)})")

    def pool(names, arm, status, trend, n):
        return [r for s in names for r in rets.get((s, arm, status, trend, n), [])]

    for g, names in groups.items():
        print(f"\n{g} ({len(names)} names) — bottoming (trend DOWN) headline"
              f" + context rows")
        print(f"  {'event':<28}{'n60':>5}{'fwd60':>8}{'win':>5}"
              f"{'n120':>6}{'fwd120':>8}{'win':>5}")
        for arm, status, trend, label in (
                ("SINGLE", "BREAKOUT", "DOWN", "single 🔵 breakout (base)"),
                ("DUAL", "BREAKOUT", "DOWN", "DUAL 🔵 breakout"),
                ("SINGLE", "BREAKDOWN", "DOWN", "single bottoming breakdown"),
                ("DUAL", "BREAKDOWN", "DOWN", "dual bottoming breakdown"),
                ("SINGLE", "BREAKOUT", "UP", "single topping breakout"),
                ("DUAL", "BREAKOUT", "UP", "dual topping breakout")):
            xs60 = pool(names, arm, status, trend, 60)
            xs120 = pool(names, arm, status, trend, 120)
            print(f"  {label:<28}{len(xs60):>5}{avg(xs60)*100:>7.1f}%"
                  f"{win(xs60):>4.0f}%{len(xs120):>6}{avg(xs120)*100:>7.1f}%"
                  f"{win(xs120):>4.0f}%")

    names = groups["ALL"]
    d60, d120 = pool(names, "DUAL", "BREAKOUT", "DOWN", 60), \
        pool(names, "DUAL", "BREAKOUT", "DOWN", 120)
    s60, s120 = pool(names, "SINGLE", "BREAKOUT", "DOWN", 60), \
        pool(names, "SINGLE", "BREAKOUT", "DOWN", 120)
    ok_n = len(d60) >= 20
    ok60 = len(d60) > 0 and avg(d60) >= avg(s60)
    ok120 = len(d120) > 0 and avg(d120) >= avg(s120)
    print(f"\nPRE-REGISTERED VERDICT (ALL, bottoming BREAKOUT):")
    print(f"  (i)   n dual ≥ 20 ............ {len(d60):>4}  "
          f"{'PASS' if ok_n else 'FAIL'}")
    print(f"  (ii)  fwd60  dual ≥ single ... {avg(d60)*100:>+6.1f}% vs "
          f"{avg(s60)*100:>+6.1f}%  {'PASS' if ok60 else 'FAIL'}")
    print(f"  (iii) fwd120 dual ≥ single ... {avg(d120)*100:>+6.1f}% vs "
          f"{avg(s120)*100:>+6.1f}%  {'PASS' if ok120 else 'FAIL'}")
    verdict = ("PASS — surface ships only via its own later session"
               if ok_n and ok60 and ok120 else "NULL — item closes honestly")
    print(f"  => {verdict}")


if __name__ == "__main__":
    print(__doc__.strip().splitlines()[1].strip("= "))
    main()
