#!/usr/bin/env python3
"""
Conviction-score backtest (#20, design D-20) — does the 0–100 score rank?
=========================================================================

Point-in-time weekly replay, 2021-07 → 2026-07: every Friday, every name,
`conviction(danny_signal(tk, w), w, spy_w)` — the LIVE functions (R6) on a
trailing 5y window `w` (exactly the bars a live 5y fetch would have shown
that day, so the `age` component reads as it does in production). Two
universes: today's live screening book (HINDSIGHT-biased — labelled) and
the frozen hype-2021 control. Raw-close RS12 (the committed backtest
convention; the live/adj spread is a near-constant −1.3 pts, BACKTEST
§5 footnote). Delisted names still missing (#45) — survivorship remains.

Outputs (D-20):
  a. WITHIN-DAY cross-sectional score deciles → forward 126d/252d mean &
     median excess vs SPY (within-day assignment controls for regime).
     Block-bootstrap 90% bands on decile means; a decile row prints only
     with ≥30 observations.
  b. Tier table by EPISODE (first Friday of a tier spell, so overlapping
     day-rows don't fake sample size): P(≥2× within 500 bars), P(≥5×),
     P(−50% first).
  c. The wreck list the gates passed (gates_ok episodes that hit −50%
     before doubling).

Decision rule (PRE-COMMITTED in D-20, restated before this ran): hold out
2024-07 → 2026-07. Weight changes are adoptable only if the OOS decile
ranking is monotone-ish (Spearman ρ ≥ 0.5 on fwd126 means) AND top-decile
excess > 0. Otherwise the digest 🚀 footer is relabelled "score =
shortlist, no measured edge" — and that is a fine outcome; the gates alone
may be the product.
"""
import bisect
import datetime
import random

from homily_data import fetch_daily
from homily_danny import danny_signal
from homily_conviction import conviction
from homily_strategy_backtest import UNIV_B
from homily_bootstrap import resample_indices

START = datetime.date(2021, 7, 1)
END = datetime.date(2026, 7, 1)
OOS_START = datetime.date(2024, 7, 1)
WINDOW = 1250            # trailing bars ≈ a live 5y fetch
MIN_BARS = 260
FWD = (126, 252)
EPISODE_BARS = 500
MIN_DECILE_OBS = 30

# today's live screening book (HOLDINGS + WATCH + UNIVERSE), ticker->yahoo
import homily_positions
_positions = homily_positions.load_positions()
UNIV_LIVE = sorted({**{k: v["yahoo"] for k, v in _positions.items()},
                    "ASML": "ASML",
                    **__import__("daily_run").UNIVERSE}.items())


def fridays(spy_bars):
    return [b[0] for b in spy_bars
            if b[0].weekday() == 4 and START <= b[0] <= END]


def spearman(xs, ys):
    """Spearman rank correlation, stdlib; ties get order ranks (inputs here
    are decile indexes vs distinct means — ties are not a concern)."""
    def ranks(v):
        order = sorted(range(len(v)), key=lambda i: v[i])
        r = [0] * len(v)
        for rank, i in enumerate(order):
            r[i] = rank
        return r
    rx, ry = ranks(xs), ranks(ys)
    n = len(xs)
    if n < 3:
        return float("nan")
    d2 = sum((a - b) ** 2 for a, b in zip(rx, ry))
    return 1 - 6 * d2 / (n * (n ** 2 - 1))


def deciles_of(day_scores):
    """[(name, score)] one day -> {name: decile 0..9 (9 = top scores)}."""
    ranked = sorted(day_scores, key=lambda kv: kv[1])
    n = len(ranked)
    return {name: min(9, i * 10 // n) for i, (name, _) in enumerate(ranked)}


def boot_band(obs, seed=20):
    """90% band on the mean via circular-block resampling (D-39 machinery),
    obs in date order so blocks respect the overlap structure."""
    if len(obs) < 2:
        return (float("nan"), float("nan"))
    rng = random.Random(seed)
    means = []
    for _ in range(2000):
        idx = resample_indices(len(obs), rng, block=6)
        means.append(sum(obs[i] for i in idx) / len(idx))
    means.sort()
    return means[int(0.05 * len(means))], means[int(0.95 * len(means))]


def replay(names_map, data, spy, label):
    """-> (day_rows, episodes). day_rows: (date, name, score, tier,
    gates_ok, {h: excess}). episodes: (date, name, tier, gates_ok,
    outcome) with outcome in 2X/5X/WRECK/none."""
    spy_dates = [b[0] for b in spy]
    spy_closes = [b[4] for b in spy]
    idx_of = {n: [b[0] for b in data[n]] for n, _ in names_map
              if n in data}
    rows = []
    last_tier = {}
    episodes = []
    for f in fridays(spy):
        si = bisect.bisect_right(spy_dates, f) - 1
        spy_w = spy_closes[max(0, si + 1 - WINDOW):si + 1]
        day_scores = []
        day = {}
        for n, _ in names_map:
            if n not in data:
                continue
            di = bisect.bisect_right(idx_of[n], f) - 1
            if di + 1 < MIN_BARS:
                continue
            w = data[n][max(0, di + 1 - WINDOW):di + 1]
            try:
                sig = danny_signal(n, w)
                c = conviction(sig, w, spy_w)
            except Exception:
                continue
            closes = [b[4] for b in data[n]]
            exc = {}
            for h in FWD:
                if di + h < len(closes) and si + h < len(spy_closes):
                    exc[h] = ((closes[di + h] / closes[di] - 1)
                              - (spy_closes[si + h] / spy_closes[si] - 1))
            day[n] = (c, di, exc)
            day_scores.append((n, c.score))
        decs = deciles_of(day_scores)
        for n, (c, di, exc) in day.items():
            rows.append((f, n, c.score, decs[n], c.tier, c.gates_ok, exc))
            # tier episodes: entry = tier changed since the last Friday seen
            if c.tier != last_tier.get(n):
                closes = [b[4] for b in data[n]]
                out, px0 = "none", closes[di]
                for j in range(di + 1, min(di + 1 + EPISODE_BARS,
                                           len(closes))):
                    r = closes[j] / px0
                    if r <= 0.5:
                        out = "WRECK"
                        break
                    if r >= 5:
                        out = "5X"
                        break
                    if r >= 2 and out == "none":
                        out = "2X"        # keep scanning: 5X may still come
                episodes.append((f, n, c.tier, c.gates_ok, out))
            last_tier[n] = c.tier
        print(f"  [{label}] {f} scored {len(day)}", flush=True)
    return rows, episodes


def decile_table(rows, span, spy_label):
    print(f"\n  score deciles, WITHIN-DAY, {spy_label} "
          f"(mean/median excess vs SPY; ≥{MIN_DECILE_OBS} obs to print)")
    print(f"  {'decile':<8}" + "".join(
        f"{'n':>6}{f'fwd{h} mean':>12}{'  90% band':>16}{'med':>7}"
        for h in FWD))
    oos_means = {}
    for d in range(10):
        line = f"  {'D' + str(d):<8}"
        for h in FWD:
            obs = [(r[0], r[6][h]) for r in rows
                   if r[3] == d and h in r[6] and span[0] <= r[0] < span[1]]
            obs.sort()
            xs = [x for _, x in obs]
            if len(xs) < MIN_DECILE_OBS:
                line += f"{len(xs):>6}{'—':>12}{'—':>16}{'—':>7}"
                continue
            lo, hi = boot_band(xs)
            med = sorted(xs)[len(xs) // 2]
            line += (f"{len(xs):>6}{sum(xs)/len(xs)*100:>+11.1f}%"
                     f"  [{lo*100:>+5.1f},{hi*100:>+5.1f}]%{med*100:>+6.1f}%")
            if h == 126:
                oos_means[d] = sum(xs) / len(xs)
        print(line)
    return oos_means


if __name__ == "__main__":
    spy = fetch_daily("SPY", rng="max")
    for label, nm in (("A live book (HINDSIGHT)",
                       [(k, v) for k, v in UNIV_LIVE]),
                      ("B hype-2021 control",
                       [(n, n) for n in UNIV_B])):
        data, dead = {}, []
        for n, sym in nm:
            try:
                data[n] = fetch_daily(sym, rng="max")
            except Exception:
                dead.append(n)
        rows, eps = replay(nm, data, spy, label[:1])
        print(f"\n{'#' * 74}\n# {label} — {len(data)} names, "
              f"{len(rows)} Friday-rows, {len(eps)} tier episodes"
              + (f" (dead: {', '.join(dead)})" if dead else "")
              + f"\n{'#' * 74}")
        decile_table(rows, (START, END), "FULL window")
        oos = decile_table(rows, (OOS_START, END),
                           "OOS 2024-07→2026-07 (the decision window)")

        print("\n  tier episodes (entry Fridays), outcome within "
              f"{EPISODE_BARS} bars:")
        print(f"  {'tier':<12}{'episodes':>9}{'P(≥2x)':>9}{'P(≥5x)':>9}"
              f"{'P(-50% first)':>15}")
        for tier in ("CONVICTION", "STARTER", "fails"):
            es = [e for e in eps if e[2] == tier]
            if not es:
                continue
            n = len(es)
            p2 = sum(e[4] in ("2X", "5X") for e in es) / n
            p5 = sum(e[4] == "5X" for e in es) / n
            pw = sum(e[4] == "WRECK" for e in es) / n
            print(f"  {tier:<12}{n:>9}{p2*100:>8.0f}%{p5*100:>8.0f}%"
                  f"{pw*100:>14.0f}%")
        wrecks = [e for e in eps if e[3] and e[4] == "WRECK"]
        print(f"\n  wreck list the gates passed ({len(wrecks)}): "
              + ", ".join(f"{e[1]}@{e[0]}" for e in wrecks[:12])
              + (" …" if len(wrecks) > 12 else ""))

        ds = sorted(d for d in oos if oos[d] == oos[d])
        rho = spearman(ds, [oos[d] for d in ds])
        top = oos.get(9, float("nan"))
        ok = rho >= 0.5 and top > 0
        judge = ("the honest judge" if label.startswith("B")
                 else "hindsight upper bound")
        print(f"\n  DECISION input ({judge}): OOS Spearman ρ = {rho:+.2f} "
              f"(need ≥ +0.50), top-decile fwd126 excess = "
              f"{top*100:+.1f}% (need > 0)")
        print(f"  → {'weight changes MAY queue behind R10' if ok else 'relabel the 🚀 footer: score = shortlist, no measured edge'}")
