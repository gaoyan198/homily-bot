#!/usr/bin/env python3
"""
#165 · The confirmation ladder — "add plates as the strength shows" (PRD §5q).
==============================================================================

Danny (AMD weekly, 2026-09-25): "Add size as the setup confirms … You don't
load everything on the first lift. You add weight as the strength shows
up." Danny's bottom-timing post (2026-08-06, paywalled; the split reached us
only as a search-engine summary and stays UNVERIFIED — the owner is not a
subscriber) states the weights: 30% when the volatility hole appears with
a descending blue ribbon · +25% on a red candle · +25% when the longest
momentum bar breaks · +20% on the blue→red ribbon reversal. #50 tested
adding on WEAKNESS and lost 0/9; this is the first sizing rule here that
adds on STRENGTH. §5q Finding C priced it on AMD (ladder 5.08× vs lump at
stage 1 4.44×, lump at the first red candle 6.12×) and named the real
subject: a ladder is insurance against FALSE STARTS, which no winner's
retrospective can contain. This module displaced `homily_tranche_backtest.py`
(#50, the dip-side inverse) to docs/archive/ in the same commit (#116 cap).

Measured priors, both recorded BEFORE this run and both unflattering:
§52 (#143) — on the hype-2021 control "VH + descending blue" is a
coin-flip week; §54 (#166) — Danny's exact stage 2 (a confirmed red candle
inside a descending blue ribbon) is the worst control cell, −5.1% at 12w.

RULE — FROZEN BEFORE THE FIRST RUN (do not renegotiate after numbers):

  Bars: COMPLETED weekly OHLCV from 10y daily; QQQ aligned by ISO week.
  Stage events (weekly closes, point-in-time):
    S1  two definitions, BOTH must pass (no picking after the fact):
        VH   the #143 CONJ week — a new weekly hole appears (vh_appears)
             while the ribbon is blue + descending;
        RIB  ribbon ONSET — blue + descending this week, not last week
             (the computable stage 1, since our VH misses Danny's holes, #142).
    S2  the first #166 CONFIRMED ignition whose ignition week is ≥ S1:
        filled at its confirmation week (close above the ignition HIGH).
    S3  the first week after S1 whose close is above the HEAVIEST overhead
        chip shelf ("the longest momentum bar") in the profile built from
        the trailing 504 sessions through the PRIOR week's last session.
        (The row's word is "longest"; §5q Finding C's AMD pricing used the
        nearest shelf — the row is the pre-registration.)
    S4  the first week after S1 whose ribbon is not blue (EMA10 ≥ EMA30).
    Each stage fires at its own first occurrence after S1 (independent
    triggers, #50's convention); a stage that never fires inside the
    horizon leaves its tranche in QQQ.
  Campaign: opens at an S1 week; one campaign per name at a time (the next
  S1 counts only ≥ 52 weeks after the previous opening); requires 52 weeks
  of forward data, so the 26w and 52w reads use the SAME campaigns.
  Universes A and B from homily_strategy_backtest. The PRD row says
  "names the incumbent rule would already buy"; reconstructing the live
  buy-day selection point-in-time is #125's replay machinery and is NOT
  done here — every arm trades the SAME campaign, so selection is held
  constant across arms and only the shape of deployment differs.
  Money: $1 per campaign at the S1 close. Arms —
    LADDER  30% into the name at S1; 25/25/20 wait in QQQ and move into
            the name at S2 / S3 / S4 (each tranche's QQQ units grow until
            its stage fires);
    LUMP-S1 100% into the name at S1;
    LUMP-S2 100% in QQQ, moved into the name at S2 ("wait for one
            confirmation");
    LUMP-S4 100% in QQQ, moved at S4;
    QQQ     100% in QQQ (the §3.5 index leg — never cash).
  COST 10 bps on every buy and every sell. Value marked at the horizon
  close. MOIC = value / $1.

  VERDICT (pre-registered): PASS iff, for BOTH S1 definitions,
    (n) ≥ 30 campaigns in each universe;
    (a) mean MOIC(LADDER) ≥ 0.97 × mean MOIC(LUMP-S1) on BOTH universes at
        BOTH 26w and 52w (non-inferior);
    (b) on B (hype-2021), P10 MOIC(LADDER) − P10 MOIC(LUMP-S1) ≥ 0.05 at
        BOTH horizons (it must insure where false starts live);
    (c) mean MOIC(LADDER) > mean MOIC(QQQ) at BOTH horizons on at least
        one universe (§9.0: a ladder that loses to the index everywhere is
        NULL whatever (a)/(b) say).
  Also printed, never selected: the false-start rate (S1 with no S2
  inside 26w), stage fill rates, and whether LUMP-S2 beats the LADDER on
  both universes at both horizons — if so the finding is published as
  "wait for one confirmation", the simpler rule a promotion session would
  propose instead. A PASS ships nothing here (Part III rule 5); a sizing
  change is selection-class under R10 (next free slot 2027-Q3).

Reproduce:  python homily_ladder_backtest.py
"""
from homily_chips import build_profile
from homily_clone import ema
from homily_data import fetch_daily, weekly_ohlcv
from homily_redcandle_backtest import ignitions
from homily_ribbon_backtest import ribbon_state, vh_appears
from homily_strategy_backtest import UNIV_A, UNIV_B

WEIGHTS = (0.30, 0.25, 0.25, 0.20)
HORIZONS = (26, 52)
GAP_W = 52
CHIP_WIN = 504
COST = 0.001
FALSE_START_W = 26


def ribbon_arrays(cl):
    """blue[i], desc[i] in one pass (prefix EMA equality, R6); None before
    ribbon_state would answer. Spot-checked against ribbon_state below."""
    fast, slow = ema(cl, 10), ema(cl, 30)
    blue = [None] * len(cl)
    desc = [None] * len(cl)
    for i in range(31, len(cl)):
        blue[i], desc[i] = fast[i] < slow[i], slow[i] < slow[i - 1]
    return blue, desc


def stage_weeks(sym, wk, daily, s, blue, igns, heavy):
    """{stage: week index or None} for the campaign opened at week s."""
    end = s + GAP_W
    s2 = next((k for t, status, k, _ in igns
               if status == "CONFIRMED" and t >= s and k <= end), None)
    s3 = next((t for t in range(s + 1, end + 1)
               if heavy(t) is not None and wk[t][4] > heavy(t)), None)
    s4 = next((t for t in range(s + 1, end + 1) if blue[t] is False), None)
    return {"S1": s, "S2": s2, "S3": s3, "S4": s4}


def value(fills, p, q, s, h):
    """fills: [(week, frac)]; frac not filled by week s+h stays in QQQ."""
    shares, units = 0.0, 0.0
    for w, f in fills:
        if w is not None and w == s:
            shares += f * (1 - COST) / p[s]
        elif w is not None and w <= s + h:
            parked = f * (1 - COST) / q[s]
            shares += parked * q[w] * (1 - COST) * (1 - COST) / p[w]
        else:
            units += f * (1 - COST) / q[s]
    return shares * p[s + h] + units * q[s + h]


def campaigns(sym, qqq_by_key):
    daily = fetch_daily(sym, rng="10y")
    wk = weekly_ohlcv(daily)
    cl = [b[4] for b in wk]
    keys = [b[0].isocalendar()[:2] for b in wk]
    if not all(k in qqq_by_key for k in keys[-min(len(keys), 60):]):
        pass                                  # alignment checked per campaign
    didx = {b[0]: i for i, b in enumerate(daily)}
    blue, desc = ribbon_arrays(cl)
    for i in (40, len(cl) // 2, len(cl) - 1):  # R6 spot-check
        if i < len(cl) and blue[i] is not None:
            st = ribbon_state(cl[:i + 1])
            assert (st[0], st[1]) == (blue[i], desc[i]), f"{sym} ribbon drift"
    igns = ignitions(wk)
    cache = {}

    def heavy(t):
        if t not in cache:
            e = didx[wk[t - 1][0]]
            prof = build_profile(daily[max(0, e - CHIP_WIN + 1):e + 1])
            cache[t] = (max(prof.resistance, key=lambda r: r[1])[0]
                        if prof.resistance else None)
        return cache[t]

    s1 = {"VH": [i for i in vh_appears(wk) if blue[i] and desc[i]],
          "RIB": [i for i in range(32, len(cl))
                  if blue[i] and desc[i] and not (blue[i - 1] and desc[i - 1])]}
    out = {}
    for ver, cands in s1.items():
        last, rows = None, []
        for s in cands:
            if last is not None and s - last < GAP_W:
                continue
            if s + GAP_W >= len(wk):
                continue
            if not all(keys[j] in qqq_by_key for j in range(s, s + GAP_W + 1)):
                continue
            last = s
            sw = stage_weeks(sym, wk, daily, s, blue, igns, heavy)
            q = {j: qqq_by_key[keys[j]] for j in range(s, s + GAP_W + 1)}
            arms = {
                "LADDER": list(zip((sw["S1"], sw["S2"], sw["S3"], sw["S4"]), WEIGHTS)),
                "LUMP-S1": [(s, 1.0)], "LUMP-S2": [(sw["S2"], 1.0)],
                "LUMP-S4": [(sw["S4"], 1.0)], "QQQ": [(None, 1.0)]}
            moic = {(a, h): value(f, cl, q, s, h)
                    for a, f in arms.items() for h in HORIZONS}
            rows.append({"sym": sym, "s": s, "date": wk[s][0], "px": cl[s],
                         "stages": sw, "moic": moic,
                         "false_start": sw["S2"] is None
                         or sw["S2"] > s + FALSE_START_W,
                         "wk": wk})
        out[ver] = rows
    return out


def study():
    qqq = weekly_ohlcv(fetch_daily("QQQ", rng="10y"))
    qqq_by_key = {b[0].isocalendar()[:2]: b[4] for b in qqq}
    univ_all = UNIV_A + [n for n in UNIV_B if n not in UNIV_A]
    per, dead = {}, []
    for sym in univ_all:
        try:
            per[sym] = campaigns(sym, qqq_by_key)
        except Exception as e:                              # noqa: BLE001
            dead.append(f"{sym}({type(e).__name__})")
    avg = lambda xs: sum(xs) / len(xs) if xs else float("nan")
    p10 = lambda xs: sorted(xs)[int(0.1 * (len(xs) - 1))] if xs else float("nan")
    arms = ("LADDER", "LUMP-S1", "LUMP-S2", "LUMP-S4", "QQQ")
    print(f"#165 confirmation ladder — {len(per)} names, 10y weekly, weights "
          f"{'/'.join(str(int(w * 100)) for w in WEIGHTS)} (unverified, frozen)"
          + (f"; failed: {', '.join(dead)}" if dead else ""))
    verdict = True
    wait_one = True
    for ver in ("VH", "RIB"):
        print(f"\n=== S1 = {ver} "
              + ("(new weekly hole + blue/descending ribbon)" if ver == "VH"
                 else "(blue/descending ribbon onset)"))
        res = {}
        for g, u in (("A current", UNIV_A), ("B hype-2021", UNIV_B)):
            rows = [r for s in u if s in per for r in per[s][ver]]
            n = len(rows)
            fs = sum(r["false_start"] for r in rows)
            fill = {k: sum(r["stages"][k] is not None
                           and r["stages"][k] <= r["s"] + 52 for r in rows)
                    for k in ("S2", "S3", "S4")}
            print(f"\n{g}: {n} campaigns · false starts (no S2 in "
                  f"{FALSE_START_W}w) {fs}/{n}"
                  + (f" = {100 * fs / n:.0f}%" if n else "")
                  + " · stage fills in 52w: "
                  + " ".join(f"{k} {100 * v / n:.0f}%" if n else f"{k} -"
                             for k, v in fill.items()))
            print(f"  {'arm':<9}" + "".join(f"{'mean ' + str(h) + 'w':>11}{'P10':>7}"
                                           for h in HORIZONS))
            for a in arms:
                line = f"  {a:<9}"
                for h in HORIZONS:
                    xs = [r["moic"][(a, h)] for r in rows]
                    res[(g, a, h)] = (avg(xs), p10(xs))
                    line += f"{avg(xs):>11.3f}{p10(xs):>7.3f}"
                print(line)
            res[(g, "n")] = n
        m = lambda g, a, h: res[(g, a, h)][0]
        pn = all(res[(g, "n")] >= 30 for g in ("A current", "B hype-2021"))
        pa = all(m(g, "LADDER", h) >= 0.97 * m(g, "LUMP-S1", h)
                 for g in ("A current", "B hype-2021") for h in HORIZONS)
        pb = all(res[("B hype-2021", "LADDER", h)][1]
                 - res[("B hype-2021", "LUMP-S1", h)][1] >= 0.05 for h in HORIZONS)
        pc = any(all(m(g, "LADDER", h) > m(g, "QQQ", h) for h in HORIZONS)
                 for g in ("A current", "B hype-2021"))
        w1 = all(m(g, "LUMP-S2", h) > m(g, "LADDER", h)
                 for g in ("A current", "B hype-2021") for h in HORIZONS)
        wait_one = wait_one and w1
        print(f"\n  (n) ≥30 each universe: {'yes' if pn else 'NO'}  "
              f"(a) non-inferior to LUMP-S1: {'yes' if pa else 'NO'}  "
              f"(b) B P10 +0.05: {'yes' if pb else 'NO'}  "
              f"(c) beats QQQ somewhere: {'yes' if pc else 'NO'}")
        print(f"  LUMP-S2 beats LADDER on both universes, both horizons: "
              f"{'YES — wait-for-one-confirmation' if w1 else 'no'}")
        verdict = verdict and pn and pa and pb and pc
    if "AMD" in per:
        print("\nAMD context (§5q; not evidence):")
        for ver in ("VH", "RIB"):
            for r in per["AMD"][ver]:
                wk, sw = r["wk"], r["stages"]
                st = " ".join(f"{k} {wk[v][0]} ${wk[v][4]:.2f}" if v is not None
                              else f"{k} —" for k, v in sw.items())
                print(f"  {ver:<3} {st}  ladder 52w {r['moic'][('LADDER', 52)]:.2f}× "
                      f"vs lump-S1 {r['moic'][('LUMP-S1', 52)]:.2f}×")
    print(f"\nVerdict (pre-registered, both S1 definitions): "
          f"{'PASS' if verdict else 'NULL'}")
    return verdict


if __name__ == "__main__":
    study()
