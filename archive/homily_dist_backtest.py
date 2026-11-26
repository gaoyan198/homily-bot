#!/usr/bin/env python3
"""
Whale-DISTRIBUTION warning study (#79, PRD §5k — the LULU sell anatomy).
========================================================================

The inverse of #12's accumulation footprints: does the observable footprint
of big holders SELLING into strength predict forward underperformance?
Danny's LULU thread (Sep 2025) called the top from: rallies absorbed by
sellers, declining whale accumulation, support eroding, monthly
lower-highs/lower-lows.

Approximated footprints, each the mirror of a `homily_whale` check (the
engine itself is frozen and untouched — these live here until/unless the
study earns them a home):

  1. distribution prints — heavy-volume days probing the rally's CEILING
     (day high within 3% of the 20d max) that close in the LOWER half of
     their range: buyers lifted offers all day, someone bigger fed them.
  2. negative flow divergence — price up from the pre-rally trough while
     OBV *and* A/D failed to make it back (money out on the way up).
     (Mirror-asymmetry note: accumulation used OR — generous toward the
     bull read; the warning uses AND — conservative toward tagging.)
  3. shelf erosion — the top support shelf's decayed chip weight received
     essentially NO fresh volume over the last two weeks (weight ≤ pure
     time-decay): holders are not defending the shelf under the rally.

Tag = rally context (close ≥5% above the 60d closing low, mirroring the
dip definition) + ≥2 of the 3. Monthly lower-highs/lower-lows is reported
as a SPLIT, not folded into the tag (it is a different timescale).

Event study, point-in-time, 5y daily, both universes incl. the 2021
control: forward 60/120d returns of tagged days vs (a) every-day baseline
and (b) untagged rally days — the proper control, since rallies as a class
run hot. Sector-matched baselines (the PRD's ideal) need sector data we
don't have; (b) is the honest stand-in and is labelled as such.

Pre-committed verdict rule: the tag earns a digest surface ONLY if tagged
days underperform BOTH baselines at BOTH horizons on the combined
universe. Honest precedent: VH breakdowns were null (§5b). A null here is
closed, nothing ships, recorded so nobody re-derives it. Scope guard from
the PRD stands regardless: if it ever ships, held satellites/Bucket-B rows
and 🚀 candidacy only — core names and the index never get a sell tag.
"""
from homily_chips import build_profile
from homily_whale import (_adl_obv, _band_weight, DIP_WIN, DIP_PCT,
                          VOL_MULT, CLOSE_POS, SHELF_LOOK, HALF_LIFE)
from homily_data import fetch_daily, monthly_closes
from homily_strategy_backtest import UNIV_A, UNIV_B

FWD = (60, 120)
WARMUP = 300
CEIL_PCT = 3.0        # day's high within this % of the 20d max high
DIST_WIN = 15         # hunt for distribution prints in this recent window
MIN_DIST = 1


def dist_footprints(bars, need_shelf):
    """(prints, neg_flow, shelf_eroding_or_None) for the last bar. The
    shelf check is only computed when `need_shelf` (it needs a chip
    profile — the expensive part); None means 'not evaluated'."""
    closes = [b[4] for b in bars]
    # 1. heavy-volume weak closes at the rally ceiling
    n_dist = 0
    for i in range(len(bars) - DIST_WIN, len(bars)):
        d, o, h, l, c, v = bars[i]
        prior = bars[max(0, i - 50):i]
        avg_v = sum(b[5] for b in prior) / len(prior)
        rng = h - l
        ceil = max(b[2] for b in bars[max(0, i - 19):i + 1])
        if (v >= VOL_MULT * avg_v and h >= ceil * (1 - CEIL_PCT / 100)
                and rng > 0 and (c - l) / rng <= CLOSE_POS):
            n_dist += 1
    prints = n_dist >= MIN_DIST

    # 2. money left between the trough and here, on BOTH flow lines
    win = closes[-DIP_WIN:]
    trough_rel = min(range(len(win)), key=lambda j: win[j])
    adls, obvs = _adl_obv(bars[-DIP_WIN:])
    neg_flow = adls[-1] <= adls[trough_rel] and obvs[-1] <= obvs[trough_rel]

    eroding = None
    if need_shelf:
        eroding = False
        prof = build_profile(bars)
        shelf = prof.support[0][0] if prof.support else None
        if shelf and shelf <= closes[-1] <= shelf * 1.25:
            lo, hi = shelf * 0.98, shelf * 1.02
            w_now = _band_weight(bars, lo, hi)
            w_then = _band_weight(bars[:-SHELF_LOOK], lo, hi)
            pure_decay = 0.5 ** (SHELF_LOOK / HALF_LIFE)
            eroding = w_then > 0 and w_now <= w_then * pure_decay * 1.02
    return prints, neg_flow, eroding


def monthly_lhll(bars):
    """Last two completed months both lower-high AND lower-low."""
    mo, cur, rows = [], None, []
    for d, o, h, l, c, v in bars:
        k = (d.year, d.month)
        if k != cur:
            rows.append([h, l])
            cur = k
        else:
            rows[-1][0] = max(rows[-1][0], h)
            rows[-1][1] = min(rows[-1][1], l)
    done = rows[:-1]                       # running month excluded
    if len(done) < 3:
        return False
    return (done[-1][0] < done[-2][0] and done[-1][1] < done[-2][1]
            and done[-2][0] < done[-3][0])


def scan(sym, bars):
    """-> (rally_days, tagged_days, tagged_lhll_days), point-in-time."""
    closes = [b[4] for b in bars]
    rally, tagged, tagged_m = [], [], []
    for i in range(WARMUP, len(bars) - 1):
        win = closes[max(0, i - DIP_WIN + 1):i + 1]
        if closes[i] < min(win) * (1 + DIP_PCT / 100):
            continue                       # not in rally context
        rally.append(i)
        pit = bars[:i + 1]
        prints, neg_flow, _ = dist_footprints(pit, need_shelf=False)
        score = prints + neg_flow
        if score == 0:
            continue
        if score == 1:                     # boundary: the shelf decides
            _, _, eroding = dist_footprints(pit, need_shelf=True)
            score += bool(eroding)
        if score >= 2:
            tagged.append(i)
            if monthly_lhll(pit):
                tagged_m.append(i)
    return rally, tagged, tagged_m


def fwd(closes, i, n):
    return closes[i + n] / closes[i] - 1 if i + n < len(closes) else None


avg = lambda xs: sum(xs) / len(xs) if xs else float("nan")


if __name__ == "__main__":
    univ_all = UNIV_A + [n for n in UNIV_B if n not in UNIV_A]
    data, dead = {}, []
    for n in univ_all:
        try:
            data[n] = fetch_daily(n, rng="5y")
        except Exception:
            dead.append(n)
    groups = {"A current": [n for n in UNIV_A if n in data],
              "B hype-2021": [n for n in UNIV_B if n in data],
              "ALL combined": [n for n in univ_all if n in data]}

    rets = {}      # (group, arm, horizon) -> [returns]
    counts = {}    # (group, arm) -> day count
    scanned = {}
    for sym in groups["ALL combined"]:
        bars = data[sym]
        closes = [b[4] for b in bars]
        rally, tagged, tagged_m = scan(sym, bars)
        scanned[sym] = (rally, tagged, tagged_m)
        print(f"  {sym:<6} rally {len(rally):>4}  tagged {len(tagged):>3}"
              f"  +monthlyLHLL {len(tagged_m):>3}", flush=True)

    for g, names in groups.items():
        for sym in names:
            closes = [b[4] for b in data[sym]]
            rally, tagged, tagged_m = scanned[sym]
            tag_set = set(tagged)
            arms = (("BASE all days", range(WARMUP, len(closes))),
                    ("rally untagged", [i for i in rally if i not in tag_set]),
                    ("rally TAGGED", tagged),
                    ("tagged +mLHLL", tagged_m))
            for arm, idxs in arms:
                cnt = 0
                for i in idxs:
                    cnt += 1
                    for n in FWD:
                        r = fwd(closes, i, n)
                        if r is not None:
                            rets.setdefault((g, arm, n), []).append(r)
                counts[(g, arm)] = counts.get((g, arm), 0) + cnt

    print(f"\nWhale-distribution warning (#79) — {len(data)} names, 5y "
          f"daily, warmup {WARMUP}"
          + (f" (unfetchable: {', '.join(dead)})" if dead else ""))
    for g in groups:
        print(f"\n{g}")
        print(f"{'arm':<18}{'days':>7}{'fwd60':>9}{'fwd120':>9}")
        for arm in ("BASE all days", "rally untagged", "rally TAGGED",
                    "tagged +mLHLL"):
            r60 = rets.get((g, arm, 60), [])
            r120 = rets.get((g, arm, 120), [])
            print(f"{arm:<18}{counts.get((g, arm), 0):>7}"
                  f"{avg(r60)*100:>8.1f}%{avg(r120)*100:>8.1f}%")

    g = "ALL combined"
    t = [avg(rets.get((g, "rally TAGGED", n), [])) for n in FWD]
    u = [avg(rets.get((g, "rally untagged", n), [])) for n in FWD]
    b = [avg(rets.get((g, "BASE all days", n), [])) for n in FWD]
    hit = all(tt < uu and tt < bb for tt, uu, bb in zip(t, u, b))
    print("\nPre-committed rule: tag earns a surface ONLY if tagged < "
          "untagged-rally AND < baseline\nat BOTH horizons on ALL combined.")
    print(f"  fwd60: tagged {t[0]*100:+.1f}% vs untagged {u[0]*100:+.1f}% / "
          f"base {b[0]*100:+.1f}%")
    print(f"  fwd120: tagged {t[1]*100:+.1f}% vs untagged {u[1]*100:+.1f}% / "
          f"base {b[1]*100:+.1f}%")
    print(f"  VERDICT: {'PREDICTIVE — queue a gated ship (scope guard: satellites/Bucket-B only)' if hit else 'NULL — closed, nothing ships (same fate as VH breakdowns, §5b)'}")
