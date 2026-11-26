#!/usr/bin/env python3
"""
#86 — dip war-chest backtest (owner instinct, D-86; rule frozen in D-86
BEFORE this file existed).
========================================================================

Danny doesn't DCA — he holds ammunition and "FOMOs in" when whales offer a
discount. Three of our own measurements point the other way and are the
NULL HYPOTHESIS: per-name ⭐-waiting lost 1–13% avg cost (§5f); ~52–54% of
⚪-blocked days ran +15% within 60d (§13); whale-dip p5 −31.7% (§12). This
run gives the instinct its one honest, pre-registered shot (D-86 verbatim).

Mechanics (extends the selection-harness accounting; fund-unit NAV,
$1/month, 10 bps, idx-fallback SPY):
  * each month the stock dollar splits: (1−f) deploys per the protocol arm
    (BOTH modelled: "equal-all ⭐" pre-rule and "rs12-top3" the live rule),
    f accrues to a cash reserve;
  * the reserve deploys WHOLE at the first qualifying event month, split
    equally across that month's event names (decision recorded here —
    D-86 said "the FIRST qualifying event" without a same-month tie rule):
      fresh ⭐ (state ⭐ this month, not last) · fresh 🔵 fire ·
      ⚪+🎯+🐳 whale-dip (per-name deployment capped at 2% of book, §3.6b)
      · 🟡+🎯 (PULLBACK at its shelf);
  * reserve tranches older than k months sweep to the index core.
  * grid: f ∈ {0.25, 0.50} × k ∈ {2, 3, 6}; baseline = same arm, f=0.

Point-in-time: every state/flag comes from the frozen engines on bar
prefixes (danny_signal — R6, no reimplementation). Windows + read rule:
the §3 harness — universe B's three construction-honest windows
(2020→2025, 2021→2026, 2016→2026) are the verdict, universe A is the
hindsight upper bound, reported never trusted.

DECISION RULE (D-86, copied verbatim): a (f,k) cell is adoptable ONLY if,
versus the idx-fallback baseline, it (a) wins MOIC on ≥2 of the 3
construction-honest windows, (b) keeps MaxDD within +5 pts, and (c) is
not behind BOTH indexes in any straddle window where the baseline isn't.
Best-of-grid shopping is disallowed: if two cells pass, the SMALLER f
wins; ties → smaller k. Anything less = NULL, recorded beside §5f, and
the war-chest idea closes. Adoption, if earned, is a 2027-Q1+ registry
promotion (R10) with a written demotion rule.
"""
import datetime

from homily_data import fetch_daily
from homily_danny import danny_signal
from homily_strategy_backtest import COST, UNIV_A, UNIV_B, month_first_idx, \
    close_on, run_dca
from homily_bear_backtest import _fetch
from homily_selection_backtest import WINDOWS, B_READ

GRID = [(f, k) for f in (0.25, 0.50) for k in (2, 3, 6)]
TRADING_YEAR = 252
WHALE_DIP_CAP = 0.02          # §3.6b: ≤2% of book per whale-dip deployment


def _ret(closes, n):
    n = min(n, len(closes) - 1)
    return (closes[-1] / closes[-1 - n] - 1) * 100 if n > 0 else 0.0


def build_state_cache(names, data, spy, months, min_bars=260):
    """month -> name -> (state, at_support, whale, rs12). One frozen-engine
    pass per (name, month); every grid cell replays from here."""
    cache = {}
    for d in months:
        spy_closes = [b[4] for b in spy if b[0] <= d]
        row = {}
        for n in names:
            bars = [b for b in data[n] if b[0] <= d]
            if len(bars) < min_bars:
                continue
            try:
                s = danny_signal(n, bars)
            except Exception:
                continue
            at = bool(s.add_zone and s.chips.last <= s.add_zone[1])
            closes = [b[4] for b in bars]
            rs = _ret(closes, TRADING_YEAR) - _ret(spy_closes, TRADING_YEAR)
            row[n] = (s.state, at, bool(s.whale.whale), rs)
        cache[d] = row
    return cache


def _picks(row, arm):
    stars = [n for n, (st, _, _, _) in row.items() if st == "ACCUMULATE"]
    cands = stars or [n for n, (st, _, _, _) in row.items()
                      if st == "BOTTOMING"]
    if arm == "rs12-top3":
        return sorted(cands, key=lambda n: -row[n][3])[:3]
    return cands                                    # equal-all


def _events(row, prev_row):
    """This month's war-chest triggers -> [(name, capped)] per D-86."""
    out = []
    for n, (st, at, wh, _) in row.items():
        pst = prev_row.get(n, (None,))[0] if prev_row else None
        if st == "ACCUMULATE" and pst != "ACCUMULATE":
            out.append((n, False))                  # fresh ⭐
        elif st == "BOTTOMING" and pst != "BOTTOMING":
            out.append((n, False))                  # fresh 🔵 fire
        elif st == "CAUTION" and at and wh:
            out.append((n, True))                   # ⚪+🎯+🐳, 2% cap binds
        elif st == "PULLBACK" and at:
            out.append((n, False))                  # 🟡+🎯
    return out


def run_cell(cache, data, spy, win, index_bars, arm, f, k):
    """The (f,k) war-chest replay under one deployment arm. f=0 IS the
    baseline (the committed protocol, same code path — no drift possible)."""
    months = [m for m in sorted(cache) if win[0] <= m <= win[1]]
    cash = paid = core = 0.0
    hold = {}
    reserve = []                          # (month_idx, amount) tranches
    nav, unit_val, units = [], 1.0, 0.0
    prev_row = None
    for i, d in enumerate(months):
        ipx = (close_on(index_bars, d) or 0) if index_bars else 0
        val = (cash + sum(a for _, a in reserve) + core * ipx
               + sum(sh * (close_on(data[n], d) or 0)
                     for n, sh in hold.items()))
        if units > 0:
            unit_val = val / units
        nav.append(unit_val)
        paid += 1.0
        units += 1.0 / unit_val
        row = cache[d]

        # k-month sweep of stale reserve tranches into the index core
        stale = [a for m0, a in reserve if i - m0 >= k]
        if stale and ipx > 0:
            core += sum(stale) * (1 - COST) / ipx
        reserve = [(m0, a) for m0, a in reserve if i - m0 < k]

        # the month's $1: f to the reserve, the rest per the protocol arm
        cash += 1.0 - f
        if f > 0:
            reserve.append((i, f))
        picks = _picks(row, arm)
        if picks and cash > 0:
            per = cash * (1 - COST) / len(picks)
            for n in picks:
                px = close_on(data[n], d)
                if px:
                    hold[n] = hold.get(n, 0) + per / px
            cash = 0.0
        elif ipx > 0 and cash > 0:
            core += cash * (1 - COST) / ipx
            cash = 0.0

        # war-chest trigger: the whole reserve fires on the FIRST event
        ev = _events(row, prev_row) if reserve else []
        if ev:
            pot = sum(a for _, a in reserve)
            reserve = []
            per = pot / len(ev)
            spill = 0.0
            for n, capped in ev:
                amt = min(per, WHALE_DIP_CAP * val) if capped else per
                spill += per - amt
                px = close_on(data[n], d)
                if px and amt > 0:
                    hold[n] = hold.get(n, 0) + amt * (1 - COST) / px
                else:
                    spill += amt
            if spill > 0 and ipx > 0:
                core += spill * (1 - COST) / ipx    # capped overflow -> index
        prev_row = row

    d_end = win[1]
    eipx = (close_on(index_bars, d_end) or 0) if index_bars else 0
    final = (cash + sum(a for _, a in reserve) + core * eipx
             + sum(sh * (close_on(data[n], d_end) or 0)
                   for n, sh in hold.items()))
    unit_val = final / units
    nav.append(unit_val)
    yrs = len(months) / 12
    cagr = (nav[-1] / nav[0]) ** (1 / yrs) - 1
    mdd = min(nav[j] / max(nav[:j + 1]) - 1 for j in range(1, len(nav)))
    return final / paid, cagr, mdd


def main():
    spy = fetch_daily("SPY", rng="max")
    qqq = fetch_daily("QQQ", rng="max")
    all_months = [spy[i][0] for i in month_first_idx(spy)][1:]
    span = [m for m in all_months if WINDOWS[0][0] <= m <= WINDOWS[-1][1]]

    for tag, names in (("B hype-2021 control", UNIV_B),
                       ("A current univ (HINDSIGHT)", UNIV_A)):
        data, dead = _fetch(names, "max")
        live = [n for n in names if n in data]
        print(f"\n{'='*74}\n#86 war-chest — universe {tag}"
              + (f"  (dead: {', '.join(dead)})" if dead else "") + f"\n{'='*74}",
              flush=True)
        cache = build_state_cache(live, data, spy, span)
        read = [w for w in WINDOWS if (w[0], w[1]) in B_READ]
        verdict = {}
        for w0, w1, wl in read:
            print(f"\n[{w0} → {w1} ({wl})]")
            m_spy, _, _ = run_dca([b for b in spy if w0 <= b[0] <= w1], spy)
            m_qqq, _, _ = run_dca([b for b in qqq if w0 <= b[0] <= w1],
                                  [b for b in spy if w0 <= b[0] <= w1])
            print(f"  DCA SPY {m_spy:.2f} · DCA QQQ {m_qqq:.2f}")
            print(f"  {'arm':<14}{'f':>5}{'k':>3}{'MOIC':>7}{'CAGR':>9}{'MaxDD':>8}")
            for arm in ("equal-all", "rs12-top3"):
                base = run_cell(cache, data, spy, (w0, w1), spy, arm, 0.0, 99)
                print(f"  {arm:<14}{'0%':>5}{'—':>3}{base[0]:>7.2f}"
                      f"{base[1]*100:>8.1f}%{base[2]*100:>7.0f}%  <- baseline")
                verdict[(tag[0], arm, (w0, w1), 0)] = base + (m_spy, m_qqq)
                for f, k in GRID:
                    r = run_cell(cache, data, spy, (w0, w1), spy, arm, f, k)
                    print(f"  {arm:<14}{f*100:>4.0f}%{k:>3}{r[0]:>7.2f}"
                          f"{r[1]*100:>8.1f}%{r[2]*100:>7.0f}%", flush=True)
                    verdict[(tag[0], arm, (w0, w1), (f, k))] = r + (m_spy, m_qqq)

    # D-86 rule, mechanically applied on universe B, per arm
    print(f"\n{'='*74}\nD-86 PRE-REGISTERED VERDICT (universe B read windows)"
          f"\n{'='*74}")
    reads = sorted({w for (u, a, w, c) in verdict if u == "B"})
    for arm in ("equal-all", "rs12-top3"):
        passing = []
        for f, k in GRID:
            wins = dd_ok = 0
            behind_both = False
            for w in reads:
                b = verdict[("B", arm, w, 0)]
                c = verdict[("B", arm, w, (f, k))]
                if c[0] > b[0]:
                    wins += 1
                if c[2] >= b[2] - 0.05:
                    dd_ok += 1
                base_ok = b[0] >= min(b[3], b[4])
                cell_bad = c[0] < min(c[3], c[4])
                if base_ok and cell_bad:
                    behind_both = True
            if wins >= 2 and dd_ok == len(reads) and not behind_both:
                passing.append((f, k))
        if passing:
            best = sorted(passing)[0]      # smaller f, then smaller k
            print(f"  {arm}: PASS — f={best[0]:.0%}, k={best[1]} "
                  f"(passing: {passing}); adoption = 2027-Q1+ registry"
                  " promotion with a demotion rule, NOT this session")
        else:
            print(f"  {arm}: NULL — no (f,k) cell cleared D-86's three"
                  " clauses; the war-chest closes beside §5f")


if __name__ == "__main__":
    main()
