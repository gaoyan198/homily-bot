#!/usr/bin/env python3
"""
Volatility-hole event study — the honest check for Danny's claim.
=================================================================

Claim under test (his SPY monthly post): "every volatility hole, once
surpassed, has triggered a strong subsequent rally."

Design (no look-ahead): walk each 5y daily series; an EVENT fires on the
first close above the upper boundary (breakout) or below the lower boundary
(breakdown) of a hole detected using only data up to that day. Measure
forward 20d and 60d returns from the event close and compare with the
unconditional forward returns of every day in the same series. One event max
per hole (re-arming only when a new hole forms).
"""
from homily_data import fetch_daily
from homily_vol import find_hole, REF_WIN, VOL_WIN

TICKERS = ["NVDA", "TSLA", "TSM", "PLTR", "CSPX.L", "AAPL", "GOOG", "AMD"]
FWD = (20, 60)
WARMUP = REF_WIN + VOL_WIN + 5


def events(bars):
    out, armed_zone = [], None
    for i in range(WARMUP, len(bars) - 1):
        h = find_hole(bars[:i + 1])
        if h is None:
            continue
        zone = (round(h.lower, 4), round(h.upper, 4))
        if h.status == "INSIDE":
            armed_zone = zone            # a hole is live and unresolved
        elif zone == armed_zone:         # first resolution of the armed hole
            out.append((i, h.status, h.trend_before))
            armed_zone = None
    return out


def fwd_ret(closes, i, n):
    if i + n >= len(closes):
        return None
    return closes[i + n] / closes[i] - 1


# ---------------------------------------------------------------------------
# #167 · VH POLARITY by ribbon colour (PRD §5q, Danny's IBIT post 2026-09-07:
# holes "with the red ribbons signaled topping … with the blue ribbon
# hinted at early bottoming"). `python homily_vol_backtest.py --polarity`;
# the default run above is untouched so §3's July re-run still reproduces.
#
# RULE — FROZEN BEFORE THE FIRST RUN (do not renegotiate after numbers):
#
#   Events: the SAME daily walker as `events()` (first resolution of each
#   armed hole, live `find_hole`, 5y daily), on universes A and B from
#   homily_strategy_backtest (overlap names in both) — the 8-name TICKERS
#   list is too small for per-cell n.
#   Labels at the resolution day i: RIBBON = `ribbon_state` (#143) on the
#   weekly closes through day i, running week included (what a digest
#   would read that morning) → BLUE / RED; TREND = the incumbent
#   `trend_before` (20-bar price lookback) → DOWN / UP.
#   Bottom arm vs top arm under each labelling:
#     ribbon: BLUE-BREAKOUT  vs RED-BREAKDOWN
#     trend:  DOWN-BREAKOUT  vs UP-BREAKDOWN
#   Forward 20d / 60d from the event close; BASE = every day, same names.
#
#   VERDICT (pre-registered): PASS iff, on BOTH universe A and B,
#     (a) mean fwd60(RED-BREAKDOWN) < mean fwd60(BASE)   — Danny's tops are
#         real tops (would overturn §3: breakdowns preceded ABOVE-baseline
#         returns, which is why topping is a note and never a veto), AND
#     (b) fwd60 separation bottom − top under RIBBON > the same under
#         TREND, AND
#     (c) n ≥ 30 in each of the four cells used, per universe.
#   Anything else = NULL: §3's finding stands and is re-labelled as
#   surviving Danny's polarity rule too. A PASS ships nothing here (Part III
#   rule 5) — `danny_signal`'s polarity source would switch in its own
#   Phase-C session with an engine_freeze re-pin.
#   Reported, not gated: the FALSE-BREAKDOWN rate — a BREAKDOWN from a
#   BLUE-ribbon hole followed by a close back above the same zone's upper
#   boundary within 65 sessions (13 weeks). Our walker disarms a zone on
#   first resolution, so it discards exactly this event (#145's H1).
# ---------------------------------------------------------------------------
FALSE_BD_WIN = 65


def polarity_events(bars):
    """(i, status, trend_before, zone) — events()'s walker, keeping the
    zone so the false-breakdown count can look forward."""
    out, armed_zone = [], None
    for i in range(WARMUP, len(bars) - 1):
        h = find_hole(bars[:i + 1])
        if h is None:
            continue
        zone = (round(h.lower, 4), round(h.upper, 4))
        if h.status == "INSIDE":
            armed_zone = zone
        elif zone == armed_zone:
            out.append((i, h.status, h.trend_before, zone))
            armed_zone = None
    return out


def polarity_study():
    from homily_data import weekly_closes
    from homily_ribbon_backtest import ribbon_state
    from homily_strategy_backtest import UNIV_A, UNIV_B
    univ_all = UNIV_A + [n for n in UNIV_B if n not in UNIV_A]
    cells, base, fbd, dead = {}, {}, {}, []
    for sym in univ_all:
        try:
            bars = fetch_daily(sym, rng="5y")
        except Exception:
            dead.append(sym)
            continue
        closes = [b[4] for b in bars]
        groups = [g for g, u in (("A current", UNIV_A), ("B hype-2021", UNIV_B))
                  if sym in u]
        for i in range(WARMUP, len(closes)):
            for n in FWD:
                r = fwd_ret(closes, i, n)
                if r is not None:
                    for g in groups:
                        base.setdefault((g, n), []).append(r)
        for i, status, trend, zone in polarity_events(bars):
            st = ribbon_state(weekly_closes(bars[:i + 1]))
            if st is None:
                continue
            rib = "BLUE" if st[0] else "RED"
            for g in groups:
                for lab in (f"{rib}-{status}", f"{trend}-{status}"):
                    for n in FWD:
                        r = fwd_ret(closes, i, n)
                        if r is not None:
                            cells.setdefault((g, lab, n), []).append(r)
                if rib == "BLUE" and status == "BREAKDOWN":
                    back = any(c > zone[1] for c in
                               closes[i + 1:i + 1 + FALSE_BD_WIN])
                    k = fbd.setdefault(g, [0, 0])
                    k[0] += back
                    k[1] += 1
    avg = lambda xs: sum(xs) / len(xs) if xs else float("nan")
    win = lambda xs: 100 * sum(x > 0 for x in xs) / len(xs) if xs else float("nan")
    print(f"#167 VH polarity by ribbon colour — {len(univ_all) - len(dead)} "
          "names, 5y daily, first resolution of each armed hole"
          + (f"; unfetchable: {', '.join(dead)}" if dead else ""))
    ok = True
    for g in ("A current", "B hype-2021"):
        print(f"\n{g}")
        print(f"  {'cell':<16}{'n':>6}{'fwd20':>9}{'win':>6}{'fwd60':>9}{'win':>6}")
        for lab in ("BLUE-BREAKOUT", "RED-BREAKDOWN", "BLUE-BREAKDOWN",
                    "RED-BREAKOUT", "DOWN-BREAKOUT", "UP-BREAKDOWN",
                    "DOWN-BREAKDOWN", "UP-BREAKOUT"):
            a, b = cells.get((g, lab, 20), []), cells.get((g, lab, 60), [])
            print(f"  {lab:<16}{len(b):>6}{avg(a) * 100:>8.1f}%{win(a):>5.0f}%"
                  f"{avg(b) * 100:>8.1f}%{win(b):>5.0f}%")
        b20, b60 = base[(g, 20)], base[(g, 60)]
        print(f"  {'BASE':<16}{len(b60):>6}{avg(b20) * 100:>8.1f}%"
              f"{win(b20):>5.0f}%{avg(b60) * 100:>8.1f}%{win(b60):>5.0f}%")
        m = lambda lab: avg(cells.get((g, lab, 60), []))
        n_ = lambda lab: len(cells.get((g, lab, 60), []))
        sep_r = m("BLUE-BREAKOUT") - m("RED-BREAKDOWN")
        sep_t = m("DOWN-BREAKOUT") - m("UP-BREAKDOWN")
        pa = m("RED-BREAKDOWN") < avg(b60)
        pb = sep_r > sep_t
        pc = min(n_(l) for l in ("BLUE-BREAKOUT", "RED-BREAKDOWN",
                                 "DOWN-BREAKOUT", "UP-BREAKDOWN")) >= 30
        fb = fbd.get(g, [0, 0])
        print(f"  (a) RED-BREAKDOWN fwd60 {m('RED-BREAKDOWN') * 100:+.1f}% vs base "
              f"{avg(b60) * 100:+.1f}% -> {'below' if pa else 'NOT below'}")
        print(f"  (b) separation bottom−top fwd60: ribbon {sep_r * 100:+.1f}pt vs "
              f"trend {sep_t * 100:+.1f}pt -> {'ribbon wider' if pb else 'ribbon NOT wider'}")
        print(f"  (c) min cell n {'≥' if pc else '<'} 30")
        print(f"  false breakdowns (BLUE hole broken, back above its upper "
              f"within {FALSE_BD_WIN}d): {fb[0]}/{fb[1]}"
              + (f" = {100 * fb[0] / fb[1]:.0f}%" if fb[1] else ""))
        ok = ok and pa and pb and pc
    print(f"\nVerdict (pre-registered): {'PASS' if ok else 'NULL'}")
    return ok


if __name__ == "__main__" and "--polarity" in __import__("sys").argv:
    polarity_study()
elif __name__ == "__main__":
    ev_rets = {("BREAKOUT", n): [] for n in FWD}
    ev_rets.update({("BREAKDOWN", n): [] for n in FWD})
    base = {n: [] for n in FWD}
    n_ev = {"BREAKOUT": 0, "BREAKDOWN": 0}
    for sym in TICKERS:
        bars = fetch_daily(sym, rng="5y")
        closes = [b[4] for b in bars]
        for i in range(WARMUP, len(closes)):
            for n in FWD:
                r = fwd_ret(closes, i, n)
                if r is not None:
                    base[n].append(r)
        for i, status, trend in events(bars):
            n_ev[status] += 1
            for n in FWD:
                r = fwd_ret(closes, i, n)
                if r is not None:
                    ev_rets[(status, n)].append(r)

    avg = lambda xs: sum(xs) / len(xs) if xs else float("nan")
    win = lambda xs: 100 * sum(x > 0 for x in xs) / len(xs) if xs else float("nan")
    print(f"Volatility-hole event study — {len(TICKERS)} names, 5y daily "
          f"({n_ev['BREAKOUT']} breakouts, {n_ev['BREAKDOWN']} breakdowns)")
    print(f"{'event':<12}{'fwd':>5}{'avg ret':>9}{'win%':>7}{'baseline':>10}{'base win%':>10}")
    print("-" * 55)
    for status in ("BREAKOUT", "BREAKDOWN"):
        for n in FWD:
            xs = ev_rets[(status, n)]
            print(f"{status:<12}{n:>4}d{avg(xs)*100:>8.1f}%{win(xs):>6.0f}%"
                  f"{avg(base[n])*100:>9.1f}%{win(base[n]):>9.0f}%")
    print("-" * 55)
    print("baseline = unconditional forward return of every day, same names.")
    print("Danny's claim holds only if BREAKOUT rows beat baseline clearly.")
