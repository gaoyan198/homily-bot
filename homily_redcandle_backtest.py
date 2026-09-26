#!/usr/bin/env python3
"""
#166 · Weekly red-candle ignition, with Danny's confirm/negate rule (PRD §5q).
=============================================================================

Our candle is a daily STATE (PRD §2: close vs EMA10 + MACD-hist, printed in
the ledger's `candle` column). His red candle is an EVENT with a published
operational rule we had never used — "to confirm a bullish trend, the price
must surpass the high point of the red candle; a close below the low would
negate" (ROOT, 2024-07-09) — and his 2026 posts read it on WEEKLY bars (AMD's
"five bullish red candles", 2026-09-25; IBRX's "red candle together with the
descending blue ribbon marked the trend reversal", 2026-09-23). The daily
triple-red run already ran NULL (#108, BACKTEST_RESULTS §22); the untested
axes are the weekly timeframe and his confirm/negate rule, nothing else.
This module displaced `homily_triplered_backtest.py` to docs/archive/ in the
same commit (census at cap, #116).

RULE — FROZEN BEFORE THE FIRST RUN (do not renegotiate after numbers):

  Bars: COMPLETED weekly OHLCV (`homily_data.weekly_ohlcv`) from 10y daily.
  RED week ⇔ close > EMA10 and MACD-hist > 0 on weekly closes (the §2 rule,
  one pass — prefix EMA/MACD equal the full-series values, R6).
  IGNITION at week t ⇔ RED at t and NOT RED at t−1, t ≥ WARMUP_W.
  Within the next CONFIRM_W = 8 weeks, the FIRST of:
    a weekly close > the ignition week's HIGH  → CONFIRMED at that week;
    a weekly close < the ignition week's LOW   → NEGATED at that week;
  neither → PENDING, resolved at week t + 8.
  Every forward return is measured from the week the status becomes KNOWN
  (confirmation / negation / t+8) — never from the ignition week, which
  would use the outcome to pick the entry. Horizons 4 / 12 / 26 weeks.
  BASE = every post-warmup week, same universe. Ribbon at ignition
  (`ribbon_state`, #143: blue+descending vs not) is REPORTED as a split —
  his stage 2 is "a red candle inside a blue ribbon" — never gated.
  Universes A (current) and B (hype-2021 control), overlap in both.

  VERDICT (pre-registered): PASS iff, on BOTH universes,
    (a) mean fwd(CONFIRMED) > mean fwd(BASE) at 12w AND 26w, and
    (b) mean fwd(CONFIRMED) > mean fwd(NEGATED+PENDING) at 12w AND 26w
        (else the confirm rule adds nothing and the event is just "the
        weekly candle"), and
    (c) n(CONFIRMED with a 26w forward) ≥ 30 per universe.
  Anything else = NULL, closed; #165 then uses the CONFIRMED week only as
  the definition of its stage 2. A PASS ships nothing here (Part III rule
  5): an info-only weekly-ignition mark needs its own session.

Reproduce:  python homily_redcandle_backtest.py
"""
from homily_clone import ema, macd
from homily_data import fetch_daily, weekly_ohlcv
from homily_ribbon_backtest import ribbon_state
from homily_strategy_backtest import UNIV_A, UNIV_B

WARMUP_W = 40
CONFIRM_W = 8
FWD_W = (4, 12, 26)


def red_weeks(closes):
    e10 = ema(closes, 10)
    _, _, hist = macd(closes)
    return [c > e and h > 0 for c, e, h in zip(closes, e10, hist)]


def ignitions(wk):
    """[(t, status, k, blue_desc)] — k = the week the status became known."""
    cl = [b[4] for b in wk]
    red = red_weeks(cl)
    out = []
    for t in range(max(WARMUP_W, 1), len(wk)):
        if not red[t] or red[t - 1]:
            continue
        hi, lo = wk[t][2], wk[t][3]
        status, k = "PENDING", t + CONFIRM_W
        for j in range(t + 1, min(t + CONFIRM_W, len(wk) - 1) + 1):
            if cl[j] > hi:
                status, k = "CONFIRMED", j
                break
            if cl[j] < lo:
                status, k = "NEGATED", j
                break
        if k >= len(wk):
            continue                        # unresolved at the data edge
        st = ribbon_state(cl[:t + 1])
        out.append((t, status, k, bool(st and st[0] and st[1])))
    return out


def fwd(cl, i, n):
    return cl[i + n] / cl[i] - 1 if i + n < len(cl) else None


def study():
    univ_all = UNIV_A + [n for n in UNIV_B if n not in UNIV_A]
    data, dead = {}, []
    for sym in univ_all:
        try:
            data[sym] = weekly_ohlcv(fetch_daily(sym, rng="10y"))
        except Exception:
            dead.append(sym)
    avg = lambda xs: sum(xs) / len(xs) if xs else float("nan")
    win = lambda xs: 100 * sum(x > 0 for x in xs) / len(xs) if xs else float("nan")
    print(f"#166 weekly red-candle ignition — {len(data)} names, 10y weekly "
          "(completed bars), returns from the week the status is known"
          + (f"; unfetchable: {', '.join(dead)}" if dead else ""))
    ok = True
    for g, u in (("A current", UNIV_A), ("B hype-2021", UNIV_B)):
        cells = {}
        for sym in (s for s in u if s in data):
            wk = data[sym]
            cl = [b[4] for b in wk]
            for i in range(WARMUP_W, len(cl)):
                for n in FWD_W:
                    r = fwd(cl, i, n)
                    if r is not None:
                        cells.setdefault(("BASE", n), []).append(r)
            for t, status, k, bd in ignitions(wk):
                labs = [status, "ALL-IGN"]
                if status != "CONFIRMED":
                    labs.append("NEG+PEND")
                if status == "CONFIRMED":
                    labs.append("CONF·blue-desc" if bd else "CONF·other")
                for n in FWD_W:
                    r = fwd(cl, k, n)
                    if r is not None:
                        for lab in labs:
                            cells.setdefault((lab, n), []).append(r)
        print(f"\n{g}")
        print(f"  {'cell':<16}" + "".join(f"{'n':>7}{str(n) + 'w':>8}{'win':>6}"
                                          for n in FWD_W))
        for lab in ("CONFIRMED", "NEGATED", "PENDING", "NEG+PEND", "ALL-IGN",
                    "CONF·blue-desc", "CONF·other", "BASE"):
            line = f"  {lab:<16}"
            for n in FWD_W:
                xs = cells.get((lab, n), [])
                line += f"{len(xs):>7}{avg(xs) * 100:>7.1f}%{win(xs):>5.0f}%"
            print(line)
        m = lambda lab, n: avg(cells.get((lab, n), []))
        pa = all(m("CONFIRMED", n) > m("BASE", n) for n in (12, 26))
        pb = all(m("CONFIRMED", n) > m("NEG+PEND", n) for n in (12, 26))
        nc = len(cells.get(("CONFIRMED", 26), []))
        pc = nc >= 30
        print(f"  (a) CONFIRMED > BASE at 12w & 26w: {'yes' if pa else 'NO'}"
              f"  (b) > NEG+PEND at 12w & 26w: {'yes' if pb else 'NO'}"
              f"  (c) n={nc} {'≥' if pc else '<'} 30")
        ok = ok and pa and pb and pc
    amd = data.get("AMD")
    if amd:
        print("\nAMD context (§5q probe; not evidence): ignitions since 2025")
        for t, status, k, bd in ignitions(amd):
            if amd[t][0].year >= 2025:
                print(f"  {amd[t][0]} close {amd[t][4]:8.2f}  {status:<9} known "
                      f"{amd[k][0]} at {amd[k][4]:8.2f}"
                      + ("  (in blue+descending ribbon)" if bd else ""))
    print(f"\nVerdict (pre-registered): {'PASS' if ok else 'NULL'}")
    return ok


if __name__ == "__main__":
    study()
