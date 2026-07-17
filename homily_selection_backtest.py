#!/usr/bin/env python3
"""
#24 · Selection inside the ⭐ set — can ranking lift us over QQQ?
=================================================================

Owner directive 2026-07-10: the north star stays *beat QQQ DCA*; the lever
with any evidence behind it is SELECTION (which candidates get the money),
not entry timing. This file tests, point-in-time, whether concentrating
each month's contribution into the *best-ranked* ⭐/🔵 candidates beats the
current equal-split-everything — and whether any ranking beats luck.

Arms (identical screening & accounting; only the pick differs):
  equal-all    equal-split across every candidate — the THE-test baseline
  alpha-top5   first 5 alphabetically — what PLAYBOOK §3.4's "max 5 names"
               accidentally does today; any adopted rule must beat this
  rs12-top5/3  rank by 12m return minus SPY's (raw closes, same caveat as
               conviction G3), take the strongest N
  conv-top5/3  rank by the live `homily_conviction.conviction()` score
               (gates ignored, score only; tie-break RS12) — the
               "multibagger rubric", finally replayed (a #20 down-payment)
  random-5     200 seeded draws of 5 — the honesty benchmark: a ranking
               that can't beat random's median is astrology with extra
               steps

Protocol: same fund-unit NAV accounting as the THE test (regression-checked
against `run_mode("hold")` each window); $1/month, 10 bps, idx-fallback
SPY; full-history bars (names eligible at window open, the cleaner
protocol); windows and construction-date honesty per
`homily_multiwindow_backtest.py` — on universe B only windows opening
2020-07 or later are read as evidence, plus the 2016→2026 10y straddle as
supporting context; universe A is a hindsight upper bound, never the
verdict.

PRE-REGISTERED DECISION RULE (written before the first run; D-24 extended
to portfolio level — do not renegotiate after seeing numbers):
  A ranking arm is adoption-worthy ONLY if, on universe B's three read
  windows (2020→2025, 2021→2026, 2016→2026):
    (i)   MOIC beats equal-all in ≥2 of 3, and
    (ii)  MOIC beats random-5's *median* in ≥2 of 3, and
    (iii) MaxDD is not worse than equal-all by >5 pts in any of them, and
    (iv)  MOIC beats alpha-top5 in ≥2 of 3.
  If no arm qualifies: the null is the result — equal-split stands, the 🚀
  score stays a shortlist (its digest framing already says so), and the
  next selection lever is the universe itself (#65), not more ranking.
  If an arm qualifies: it ships as digest ORDERING + copilot (#31)
  allocation in a FOLLOW-UP session (Part III rule 5 — never promoted in
  the session that measured it).
"""
import datetime
import random

from homily_data import fetch_daily
from homily_conviction import conviction, _ret, TRADING_YEAR
from homily_danny import danny_signal
from homily_strategy_backtest import (COST, UNIV_A, UNIV_B, month_first_idx,
                                      close_on, run_dca)
from homily_bear_backtest import run_mode, _screen

N_RANDOM = 200
WINDOWS = ([(datetime.date(y, 7, 1), datetime.date(y + 5, 7, 1), "5y")
            for y in range(2015, 2022)]
           + [(datetime.date(2015, 7, 1), datetime.date(2025, 7, 1), "10y"),
              (datetime.date(2016, 7, 1), datetime.date(2026, 7, 1), "10y")])
B_READ = {(datetime.date(2020, 7, 1), datetime.date(2025, 7, 1)),
          (datetime.date(2021, 7, 1), datetime.date(2026, 7, 1)),
          (datetime.date(2016, 7, 1), datetime.date(2026, 7, 1))}


def build_month_cache(names, data, spy, months, min_bars=260):
    """One live screening + ranking pass per month; every arm replays from
    this cache. Candidates come from the same `_screen` the THE-test path
    uses; ranks call the live conviction()/_ret on the same truncated bars
    (R6: no reimplementation, just memoisation)."""
    cache = {}
    for d in months:
        cands = _screen(names, data, d, min_bars)
        spy_closes = [b[4] for b in spy if b[0] <= d]
        rows = []
        for n in cands:
            bars = [b for b in data[n] if b[0] <= d]
            closes = [b[4] for b in bars]
            rs = _ret(closes, TRADING_YEAR) - _ret(spy_closes, TRADING_YEAR)
            try:
                score = conviction(danny_signal(n, bars), bars,
                                   spy_closes).score
            except Exception:
                score = 0
            rows.append((n, rs, score))
        cache[d] = rows
    return cache


def run_selected(cache, data, spy, win, index_bars, picker):
    """run_mode("hold") accounting, candidates from cache, picks from
    `picker(rows)` (rows = [(name, rs12, conv_score)])."""
    months = [spy[i][0] for i in month_first_idx(spy)][1:]
    months = [m for m in months if win[0] <= m <= win[1]]
    cash = paid = 0.0
    hold, core = {}, 0.0
    nav, unit_val, units = [], 1.0, 0.0
    for d in months:
        ipx = (close_on(index_bars, d) or 0) if index_bars else 0
        val = (cash + core * ipx
               + sum(sh * (close_on(data[n], d) or 0)
                     for n, sh in hold.items()))
        if units > 0:
            unit_val = val / units
        nav.append(unit_val)
        cash += 1.0
        paid += 1.0
        units += 1.0 / unit_val

        picks = picker(cache[d])
        if picks and cash > 0:
            per = cash * (1 - COST) / len(picks)
            for n in picks:
                px = close_on(data[n], d)
                if px:
                    hold[n] = hold.get(n, 0) + per / px
            cash = 0.0
        elif index_bars and ipx > 0 and cash > 0:
            core += cash * (1 - COST) / ipx
            cash = 0.0
    d_end = win[1]
    eipx = (close_on(index_bars, d_end) or 0) if index_bars else 0
    final = (cash + core * eipx
             + sum(sh * (close_on(data[n], d_end) or 0)
                   for n, sh in hold.items()))
    unit_val = final / units
    nav.append(unit_val)
    yrs = len(months) / 12
    cagr = (nav[-1] / nav[0]) ** (1 / yrs) - 1
    mdd = min(nav[j] / max(nav[:j + 1]) - 1 for j in range(1, len(nav)))
    return final / paid, cagr, mdd


def pick_all(rows):
    return [n for n, _, _ in rows]


def pick_alpha(k):
    return lambda rows: sorted(n for n, _, _ in rows)[:k]


def pick_rs(k):
    return lambda rows: [n for n, _, _ in
                         sorted(rows, key=lambda r: -r[1])[:k]]


def pick_conv(k):
    return lambda rows: [n for n, _, _ in
                         sorted(rows, key=lambda r: (-r[2], -r[1]))[:k]]


ARMS = (("equal-all", pick_all), ("alpha-top5", pick_alpha(5)),
        ("rs12-top5", pick_rs(5)), ("rs12-top3", pick_rs(3)),
        ("conv-top5", pick_conv(5)), ("conv-top3", pick_conv(3)))


def main():
    spy = fetch_daily("SPY", rng="max")
    qqq = fetch_daily("QQQ", rng="max")
    all_months = [spy[i][0] for i in month_first_idx(spy)][1:]
    span = [m for m in all_months
            if WINDOWS[0][0] <= m <= WINDOWS[-1][1]]

    for tag, names in (("B hype-2021 control", UNIV_B),
                       ("A current univ (HINDSIGHT)", UNIV_A)):
        data = {}
        for n in names:
            try:
                data[n] = fetch_daily(n, rng="max")
            except Exception:
                pass
        live = sorted(data)
        print(f"\n{'#' * 74}\n# {tag} — {len(live)} names\n{'#' * 74}")
        cache = build_month_cache(live, data, spy, span)

        results = {}
        for w0, w1, wl in WINDOWS:
            win = (w0, w1)
            # regression: equal-all from the cache must equal the live path
            ref = run_mode(live, data, spy, qqq, "hold", index_bars=spy,
                           win=win)
            got = run_selected(cache, data, spy, win, spy, pick_all)
            drift = max(abs(a - b) for a, b in zip(ref[:3], got))
            flag = "OK" if drift < 1e-9 else "DRIFT-VOID"
            dm, _, _ = run_dca(spy, spy, win=win)
            qm, _, _ = run_dca(qqq, spy, win=win)
            read = ("READ" if win in B_READ else "context") \
                if tag.startswith("B") else "upper-bound"
            print(f"\n── {w0} → {w1} ({wl}) · {read} · regression {flag}"
                  f" · DCA SPY {dm:.2f} / QQQ {qm:.2f} MOIC ──")
            print(f"  {'arm':<12}{'MOIC':>6}{'CAGR':>8}{'MaxDD':>7}"
                  f"{'>QQQ':>6}")
            for arm, picker in ARMS:
                m, c, dd = run_selected(cache, data, spy, win, spy, picker)
                results[(arm, win)] = (m, dd)
                print(f"  {arm:<12}{m:>6.2f}{c * 100:>7.1f}%"
                      f"{dd * 100:>6.0f}%{'✓' if m > qm else '✗':>6}")
            moics = []
            for i in range(N_RANDOM):
                rng = random.Random(1000 + i)
                m, _, _ = run_selected(
                    cache, data, spy, win, spy,
                    lambda rows, r=rng: [n for n, _, _ in
                                         r.sample(rows, min(5, len(rows)))]
                    if rows else [])
                moics.append(m)
            moics.sort()
            med = moics[N_RANDOM // 2]
            results[("random-med", win)] = (med, None)
            print(f"  {'random-5':<12}{med:>6.2f}  (p10 "
                  f"{moics[N_RANDOM // 10]:.2f} · p90 "
                  f"{moics[-N_RANDOM // 10]:.2f}, {N_RANDOM} draws)")

        if tag.startswith("B"):
            print(f"\n  PRE-REGISTERED VERDICT (universe B read windows):")
            reads = sorted(B_READ)
            for arm, _ in ARMS[1:]:
                beat_eq = sum(results[(arm, w)][0]
                              > results[("equal-all", w)][0] for w in reads)
                beat_rnd = sum(results[(arm, w)][0]
                               > results[("random-med", w)][0]
                               for w in reads)
                dd_ok = all(results[(arm, w)][1]
                            >= results[("equal-all", w)][1] - 0.05
                            for w in reads)
                beat_alpha = sum(results[(arm, w)][0]
                                 > results[("alpha-top5", w)][0]
                                 for w in reads)
                ok = (beat_eq >= 2 and beat_rnd >= 2 and dd_ok
                      and beat_alpha >= 2)
                print(f"    {arm:<12} beats equal {beat_eq}/3 ·"
                      f" beats random-med {beat_rnd}/3 ·"
                      f" dd-ok {dd_ok} ·"
                      f" beats alpha {beat_alpha}/3"
                      f"  → {'ADOPTION-WORTHY' if ok else 'no'}")

    print("\nMOIC per $1 contributed · ranking applied to the same monthly"
          " candidate set the digest would print · adoption rule in the"
          " docstring — the verdict lines apply it mechanically.")



# --- #87 · concentration regime conditioner (D-87) — flag-gated arm ---------
# Appended to homily_selection_backtest.py behind `--conditioner`; the
# committed run's numbers stay byte-identical (nothing above this line
# changes, no existing path takes a new parameter).
#
# Conditioners are PRE-EXISTING frozen outputs, thresholds pre-registered
# here before the run (no fitting):
#   regime  — 3-way 10m-SMA label on SPY+QQQ completed months (the frozen
#             homily_regime rule on prefix bars); hostile = NOT BULL.
#   breadth — % of eligible names above their 200d SMA at the month's
#             first day; hostile = < 30 (the #26 canary's own line).
#   qqq3m   — trailing 63-trading-day QQQ raw-close return; hostile = < 0.
#
# D-87 rule (verbatim): a conditioner earns promotion candidacy ONLY if on
# BOTH universes top-3 beats equal-all in its favourable state AND loses
# in its hostile state (sign flip), and the implied conditional strategy
# (equal-split hostile months, top-3 otherwise) beats always-top-3 by
# ≥ +0.05 MOIC on ≥2 of the 3 construction-honest windows without losing
# any. Two passing → the SIMPLER (regime > breadth > qqq3m). None = NULL.

from homily_data import monthly_closes as _mcloses


def _label_at(spy, qqq, d):
    """BULL/BEAR/MIXED at month-first d from completed-month 10m SMAs —
    the regime_series() arithmetic, kept 3-way."""
    above = []
    for bars in (spy, qqq):
        mos = _mcloses([b for b in bars if b[0] < d.replace(day=1)])
        if len(mos) < 11:
            return None
        above.append(mos[-1] > sum(mos[-10:]) / 10)
    return "BULL" if all(above) else "BEAR" if not any(above) else "MIXED"


def _breadth_at(names, data, d, min_bars=260):
    vals = []
    for n in names:
        closes = [b[4] for b in data[n] if b[0] <= d]
        if len(closes) < min_bars:
            continue
        vals.append(closes[-1] > sum(closes[-200:]) / 200)
    return 100.0 * sum(vals) / len(vals) if vals else None


def _qqq3m_at(qqq, d):
    closes = [b[4] for b in qqq if b[0] <= d]
    return (closes[-1] / closes[-64] - 1) if len(closes) > 64 else None


def month_tags(names, data, spy, qqq, months):
    """month -> {"regime": bool_hostile, "breadth": ..., "qqq3m": ...}."""
    tags = {}
    for d in months:
        lb = _label_at(spy, qqq, d)
        br = _breadth_at(names, data, d)
        q3 = _qqq3m_at(qqq, d)
        tags[d] = {
            "regime": (lb is not None and lb != "BULL"),
            "breadth": (br is not None and br < 30.0),
            "qqq3m": (q3 is not None and q3 < 0.0),
        }
    return tags


def run_selected_monthly(cache, data, spy, win, index_bars, picker_of_month):
    """run_selected's accounting with a month-aware picker; returns
    (MOIC, CAGR, MaxDD, [(month, unit_ret)]) so per-state slices can be
    compounded without a second replay."""
    months = [spy[i][0] for i in month_first_idx(spy)][1:]
    months = [m for m in months if win[0] <= m <= win[1]]
    cash = paid = core = 0.0
    hold = {}
    nav, unit_val, units = [], 1.0, 0.0
    rets = []
    for d in months:
        ipx = (close_on(index_bars, d) or 0) if index_bars else 0
        val = (cash + core * ipx
               + sum(sh * (close_on(data[n], d) or 0)
                     for n, sh in hold.items()))
        new_unit = val / units if units > 0 else 1.0
        if nav:
            rets.append((d, new_unit / nav[-1] - 1))
        unit_val = new_unit
        nav.append(unit_val)
        cash += 1.0
        paid += 1.0
        units += 1.0 / unit_val
        picks = picker_of_month(d, cache[d])
        if picks and cash > 0:
            per = cash * (1 - COST) / len(picks)
            for n in picks:
                px = close_on(data[n], d)
                if px:
                    hold[n] = hold.get(n, 0) + per / px
            cash = 0.0
        elif index_bars and ipx > 0 and cash > 0:
            core += cash * (1 - COST) / ipx
            cash = 0.0
    d_end = win[1]
    eipx = (close_on(index_bars, d_end) or 0) if index_bars else 0
    final = (cash + core * eipx
             + sum(sh * (close_on(data[n], d_end) or 0)
                   for n, sh in hold.items()))
    unit_val = final / units
    nav.append(unit_val)
    yrs = len(months) / 12
    cagr = (nav[-1] / nav[0]) ** (1 / yrs) - 1
    mdd = min(nav[j] / max(nav[:j + 1]) - 1 for j in range(1, len(nav)))
    return final / paid, cagr, mdd, rets


def _compound(rets, months_in_state):
    x = 1.0
    for d, r in rets:
        if d in months_in_state:
            x *= 1 + r
    return x


def conditioner_main():
    spy = fetch_daily("SPY", rng="max")
    qqq = fetch_daily("QQQ", rng="max")
    all_months = [spy[i][0] for i in month_first_idx(spy)][1:]
    span = [m for m in all_months
            if WINDOWS[0][0] <= m <= WINDOWS[-1][1]]
    read = sorted(B_READ)
    flip_ok = {c: True for c in ("regime", "breadth", "qqq3m")}
    cond_wins = {c: 0 for c in flip_ok}
    cond_loses = {c: 0 for c in flip_ok}

    for tag, names in (("B", UNIV_B), ("A", UNIV_A)):
        data, dead = {}, []
        for n in names:
            try:
                data[n] = fetch_daily(n, rng="max")
            except Exception:
                dead.append(n)
        live = [n for n in names if n in data]
        print(f"\n{'='*74}\n#87 conditioner — universe {tag}"
              + (f"  (dead: {', '.join(dead)})" if dead else "") + f"\n{'='*74}",
              flush=True)
        cache = build_month_cache(live, data, spy, span)
        tags = month_tags(live, data, spy, qqq, span)

        # sign-flip test over the full span, per conditioner
        top3 = lambda d, rows: pick_rs(3)(rows)
        equal = lambda d, rows: pick_all(rows)
        full = (span[0], span[-1])
        _, _, _, r3 = run_selected_monthly(cache, data, spy, full, spy, top3)
        _, _, _, re = run_selected_monthly(cache, data, spy, full, spy, equal)
        print(f"\n  sign-flip test (full span {full[0]} → {full[1]}):")
        for c in flip_ok:
            host = {d for d in span if tags[d][c]}
            fav = {d for d in span if not tags[d][c]}
            t3h, t3f = _compound(r3, host), _compound(r3, fav)
            eqh, eqf = _compound(re, host), _compound(re, fav)
            flips = t3f > eqf and t3h < eqh
            flip_ok[c] = flip_ok[c] and flips
            print(f"    {c:<8} hostile {len(host):>3}mo: top3 {t3h:5.2f} vs"
                  f" equal {eqh:5.2f} | favourable {len(fav):>3}mo:"
                  f" top3 {t3f:5.2f} vs equal {eqf:5.2f}"
                  f"  {'FLIP' if flips else 'no flip'}")

        # conditional strategy vs always-top-3 on the read windows
        print(f"\n  conditional (equal in hostile) vs always-top3,"
              f" read windows:")
        for w0, w1 in read:
            m3, _, _, _ = run_selected_monthly(cache, data, spy, (w0, w1),
                                               spy, top3)
            for c in cond_wins:
                pk = (lambda cc: lambda d, rows:
                      pick_all(rows) if tags[d][cc] else pick_rs(3)(rows))(c)
                mc, _, _, _ = run_selected_monthly(cache, data, spy, (w0, w1),
                                                   spy, pk)
                mark = ""
                if tag == "B":
                    if mc >= m3 + 0.05:
                        cond_wins[c] += 1
                        mark = " (+)"
                    elif mc < m3:
                        cond_loses[c] += 1
                        mark = " (−)"
                print(f"    [{w0.year}→{w1.year}] {c:<8}"
                      f" cond {mc:5.2f} vs top3 {m3:5.2f}{mark}", flush=True)

    print(f"\n{'='*74}\nD-87 PRE-REGISTERED VERDICT\n{'='*74}")
    passing = [c for c in ("regime", "breadth", "qqq3m")
               if flip_ok[c] and cond_wins[c] >= 2 and cond_loses[c] == 0]
    if passing:
        print(f"  PASS: {passing[0]} (simpler-first order) — promotion"
              " candidacy 2027-Q1+ via registry + demotion rule; nothing"
              " ships this session")
    else:
        print("  NULL — no conditioner cleared both clauses on both"
              " universes; the live demotion rule remains the only guard;"
              " item closes")


# in __main__: `--conditioner` branches here before the committed main()


if __name__ == "__main__":
    import sys
    if "--conditioner" in sys.argv:
        conditioner_main()          # #87, flag-gated
    else:
        main()
