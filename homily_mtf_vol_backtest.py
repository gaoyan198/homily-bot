#!/usr/bin/env python3
"""
Multi-timeframe volatility hole (#77, PRD §5k) — weekly/monthly VH, tested.
===========================================================================

Danny's claimed sequence (COIN Feb 2026): the DAILY volatility hole is the
early tell, the WEEKLY/MONTHLY hole is the confirmation; and his SPY
monthly study (Apr 11 2026) claims "every volatility hole, once surpassed,
has triggered a strong subsequent rally" — a perfect breakout record since
Dec 2013. Our VH engine is daily-only. This study:

  1. REPLICATES the SPY-monthly claim directly: every monthly-VH breakout
     since Dec 2013 listed with forward 6m/12m returns. If it doesn't
     replicate on our approximation, that is a §8.5-worthy finding on its
     own (the deliverable the PRD names).
  2. Runs the weekly-VH event study on both universes (incl. the 2021
     control), same protocol as the committed daily study
     (homily_vol_backtest.py: fwd 20d/60d ≈ 4w/12w here), so the weekly
     numbers read against the daily baseline.
  3. Tests the SEQUENCE claim: weekly breakouts split by whether a daily-VH
     breakout preceded them within the prior 40 trading days.

R10 note: #77/#81/#74 are R4 timing modifiers sharing ONE study slot per
quarter; this run takes 2026-Q3's slot (whale already holds Q3's PROMOTION
slot, so nothing here can be promoted before Q4 regardless of results —
info-only by construction). The hole detector is the LIVE, frozen
`homily_vol.find_hole`, fed resampled bars; only the resampler and the
event walker live here (same pattern as the daily study).
"""
from homily_vol import find_hole, VOL_WIN
from homily_data import fetch_daily
from homily_strategy_backtest import UNIV_A, UNIV_B

import datetime

FWD_W = (4, 12)            # weeks ≈ the daily study's 20d/60d
FWD_M = (6, 12)            # months, for the SPY replication
SINCE = datetime.date(2013, 12, 1)


def resample_ohlcv(bars, key):
    """Daily 6-tuples -> completed-bucket 6-tuples (o first, h max, l min,
    c last, v sum); the running (last) bucket is DROPPED — a study bar must
    be a completed bar."""
    out, cur = [], None
    for d, o, h, l, c, v in bars:
        k = key(d)
        if k != cur:
            out.append([d, o, h, l, c, v])
            cur = k
        else:
            b = out[-1]
            b[0] = d
            b[2] = max(b[2], h)
            b[3] = min(b[3], l)
            b[4] = c
            b[5] += v
    return [tuple(b) for b in out[:-1]]


def weekly_bars(bars):
    return resample_ohlcv(bars, lambda d: d.isocalendar()[:2])


def monthly_bars(bars):
    return resample_ohlcv(bars, lambda d: (d.year, d.month))


def events(bars, ref_win, max_age):
    """First resolution of each armed hole, point-in-time — the walker from
    homily_vol_backtest, parameterised for coarse bars."""
    warmup = ref_win + VOL_WIN + 5
    out, armed = [], None
    for i in range(warmup, len(bars) - 1):
        h = find_hole(bars[:i + 1], ref_win=ref_win, max_age=max_age)
        if h is None:
            continue
        zone = (round(h.lower, 4), round(h.upper, 4))
        if h.status == "INSIDE":
            armed = zone
        elif zone == armed:
            out.append((i, h.status))
            armed = None
    return out


def fwd(closes, i, n):
    return closes[i + n] / closes[i] - 1 if i + n < len(closes) else None


avg = lambda xs: sum(xs) / len(xs) if xs else float("nan")
win = lambda xs: 100 * sum(x > 0 for x in xs) / len(xs) if xs else float("nan")


def spy_monthly_replication():
    print("1 · SPY MONTHLY replication of the Apr-2026 claim "
          f"(breakouts since {SINCE})")
    spy = fetch_daily("SPY", rng="max")
    mo = monthly_bars(spy)
    closes = [b[4] for b in mo]
    # the scale that decides whether "positive after breakout" means anything:
    # SPY's unconditional forward returns over the same claim period
    idx = [i for i in range(len(mo)) if mo[i][0] >= SINCE]
    for n in FWD_M:
        rs = [r for i in idx if (r := fwd(closes, i, n)) is not None]
        print(f"  unconditional fwd{n}m since {SINCE}: n={len(rs)} "
              f"mean {avg(rs) * 100:+.1f}% · {win(rs):.0f}% positive")
    for ref_win, label in ((24, "ref 24mo (chart-scale reading)"),
                           (60, "ref 60 bars (engine default)")):
        evs = [(i, st) for i, st in events(mo, ref_win, max_age=18)
               if st == "BREAKOUT" and mo[i][0] >= SINCE]
        print(f"\n  {label}: {len(evs)} monthly-VH breakouts")
        wins6 = wins12 = n6 = n12 = 0
        for i, _ in evs:
            r6, r12 = fwd(closes, i, 6), fwd(closes, i, 12)
            print(f"    {mo[i][0]}  close {closes[i]:>7.2f}  "
                  f"fwd6m {r6 * 100:>+6.1f}%" if r6 is not None else
                  f"    {mo[i][0]}  close {closes[i]:>7.2f}  fwd6m      —",
                  end="")
            print(f"  fwd12m {r12 * 100:>+6.1f}%" if r12 is not None
                  else "  fwd12m      —")
            if r6 is not None:
                n6 += 1
                wins6 += r6 > 0
            if r12 is not None:
                n12 += 1
                wins12 += r12 > 0
        print(f"    record: fwd6m {wins6}/{n6} positive · "
              f"fwd12m {wins12}/{n12} positive "
              f"-> {'PERFECT' if wins6 == n6 and wins12 == n12 and n6 else 'NOT perfect'}")


def weekly_event_study():
    print("\n2 · WEEKLY-VH event study — both universes, vs the committed "
          "daily baseline\n    (daily study, 8 names: breakout fwd20 +4.4% "
          "vs base +2.8%; fwd60 +11.5% vs +8.5%)")
    univ_all = UNIV_A + [n for n in UNIV_B if n not in UNIV_A]
    data, dead = {}, []
    for n in univ_all:
        try:
            data[n] = fetch_daily(n, rng="5y")
        except Exception:
            dead.append(n)
    groups = {"A current": [n for n in UNIV_A if n in data],
              "B hype-2021": [n for n in UNIV_B if n in data],
              "ALL": [n for n in univ_all if n in data]}
    ev, base, seq = {}, {}, {}
    for sym in groups["ALL"]:
        bars = data[sym]
        wk = weekly_bars(bars)
        wcl = [b[4] for b in wk]
        warmup = 60 + VOL_WIN + 5
        for i in range(warmup, len(wcl)):
            for n in FWD_W:
                r = fwd(wcl, i, n)
                if r is not None:
                    base.setdefault((sym, n), []).append(r)
        # daily-VH breakout days, for the sequence split
        dcl = [b[4] for b in bars]
        d_evs = {i for i, st in events(bars, 60, 90) if st == "BREAKOUT"}
        d_dates = sorted(bars[i][0] for i in d_evs)
        for i, st in events(wk, 60, 52):
            preceded = any(0 <= (wk[i][0] - dd).days <= 56 for dd in d_dates)
            for n in FWD_W:
                r = fwd(wcl, i, n)
                if r is None:
                    continue
                ev.setdefault((sym, st, n), []).append(r)
                if st == "BREAKOUT":
                    seq.setdefault((sym, preceded, n), []).append(r)
        print(f"  scanned {sym}", flush=True)

    for g, names in groups.items():
        print(f"\n  {g} ({len(names)} names)")
        print(f"  {'event':<22}{'n':>5}{'fwd4w':>8}{'win':>5}{'fwd12w':>9}{'win':>5}")
        b4 = [r for s in names for r in base.get((s, 4), [])]
        b12 = [r for s in names for r in base.get((s, 12), [])]
        print(f"  {'baseline (all weeks)':<22}{len(b4):>5}{avg(b4)*100:>7.1f}%"
              f"{win(b4):>4.0f}%{avg(b12)*100:>8.1f}%{win(b12):>4.0f}%")
        for st in ("BREAKOUT", "BREAKDOWN"):
            e4 = [r for s in names for r in ev.get((s, st, 4), [])]
            e12 = [r for s in names for r in ev.get((s, st, 12), [])]
            print(f"  {'weekly ' + st:<22}{len(e4):>5}{avg(e4)*100:>7.1f}%"
                  f"{win(e4):>4.0f}%{avg(e12)*100:>8.1f}%{win(e12):>4.0f}%")
        if g == "ALL":
            print("\n  3 · sequence claim (weekly breakout preceded by a "
                  "daily-VH breakout ≤56 cal days)")
            for label, flag in (("daily preceded", True),
                                ("no daily tell", False)):
                s4 = [r for s in names for r in seq.get((s, flag, 4), [])]
                s12 = [r for s in names for r in seq.get((s, flag, 12), [])]
                print(f"  {label:<22}{len(s4):>5}{avg(s4)*100:>7.1f}%"
                      f"{win(s4):>4.0f}%{avg(s12)*100:>8.1f}%{win(s12):>4.0f}%")
    if dead:
        print(f"\n  (unfetchable: {', '.join(dead)})")


if __name__ == "__main__":
    print(__doc__.strip().splitlines()[1].strip("= "))
    spy_monthly_replication()
    weekly_event_study()
    print("\nInfo-only by construction: Q3's promotion slot is held by the "
          "whale tier (R10); any\npromotion candidate here queues behind #24 "
          "for Q4+ and needs its own pre-registered gate.")
