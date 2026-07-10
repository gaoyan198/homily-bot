#!/usr/bin/env python3
"""
Multi-window re-test — the strategy vs SPY/QQQ DCA over EVERY ≥5y window.
=========================================================================

Owner's bar (2026-07-10): *"if the strategy cannot clear backtest comparison
with the S&P 500 or the Nasdaq over multiple long-enough time periods (5
years or longer), our efforts are not worth it."* This file IS that test,
in one reproducible place. It is also the standing harness for the yearly
re-test (PRD #40).

Protocol
--------
* ONE max-range fetch per name; every window replays point-in-time on the
  same bars (signals see only bars ≤ decision day). Full pre-window history
  counts toward the 260-bar eligibility, so a name is investable the day a
  window opens if it was already a year old — the committed 5y table in
  BACKTEST_RESULTS.md fetched rng="5y" and therefore starved its first year
  of candidates; numbers here use the cleaner protocol and differ slightly.
* Rolling 5y windows, July→July, starts 2015-07 … 2021-07 (7 windows),
  plus the 2015-07→2025-07 and 2016-07→2026-07 10y windows.
* $1/month on the SPY month calendar, 10 bps per trade, fund-unit NAV
  (TWR CAGR, real MaxDD), same accounting as the THE test — `run_mode` and
  `run_dca` are imported, never reimplemented (EXECUTION.md R6).
* Arms: (a) hold-through (the champion), (c) freeze-only (D-63 candidate),
  (f) §5.2 per-name exit — each with SPY *and* QQQ as the no-⭐ fallback
  index (PLAYBOOK Bucket A is a blend; the two fallbacks bracket it).
* Universes: A = current bot universe (HINDSIGHT-picked 2026 winners — an
  upper bound, never the verdict); B = hype-2021 control (the honest one).
  Both still exclude fully-delisted names (fetch constraint) — residual
  survivorship remains; the delisted-inclusive control is PRD #45.

Read the per-universe verdict block at the end: it counts windows whose
strategy MOIC beat DCA SPY / DCA QQQ. The bar is judged on universe B.
"""
import datetime

from homily_data import fetch_daily
from homily_strategy_backtest import UNIV_A, UNIV_B, run_dca
from homily_bear_backtest import run_mode, MODE_LABEL

MW_MODES = ("hold", "freeze", "perstock")
FIVE_Y_STARTS = range(2015, 2022)
WINDOWS = ([(datetime.date(y, 7, 1), datetime.date(y + 5, 7, 1), "5y")
            for y in FIVE_Y_STARTS]
           + [(datetime.date(2015, 7, 1), datetime.date(2025, 7, 1), "10y"),
              (datetime.date(2016, 7, 1), datetime.date(2026, 7, 1), "10y")])


def _fetch_all(names, rng="max"):
    data, dead = {}, []
    for n in names:
        try:
            data[n] = fetch_daily(n, rng=rng)
        except Exception:
            dead.append(n)
    return data, dead


def _eligible_at(names, data, d, min_bars=260):
    return sum(1 for n in names
               if len([b for b in data[n] if b[0] <= d]) >= min_bars)


def main():
    spy = fetch_daily("SPY", rng="max")
    qqq = fetch_daily("QQQ", rng="max")
    print(__doc__.strip().splitlines()[1].strip("= "))
    print(f"data: SPY {spy[0][0]}→{spy[-1][0]} · QQQ from {qqq[0][0]} ·"
          " $1/month · 10bps · point-in-time")

    for tag, names in (("B hype-2021 control (THE HONEST UNIVERSE)", UNIV_B),
                       ("A current univ (HINDSIGHT — upper bound only)",
                        UNIV_A)):
        data, dead = _fetch_all(names)
        live = [n for n in names if n in data]
        print(f"\n{'#' * 74}\n# universe {tag} — {len(live)} names"
              + (f" (unfetchable: {', '.join(dead)})" if dead else "")
              + f"\n{'#' * 74}")
        beats = {}          # (mode, fb_label) -> [beat_spy, beat_qqq, n]
        for w0, w1, wl in WINDOWS:
            dm, dc, ddd = run_dca(spy, spy, win=(w0, w1))
            qm, qc, qdd = run_dca(qqq, spy, win=(w0, w1))
            elig = _eligible_at(live, data, w0)
            print(f"\n── {w0} → {w1} ({wl}) · eligible at open:"
                  f" {elig}/{len(live)} ──")
            print(f"  {'arm':<26}{'MOIC':>6}{'CAGR':>8}{'MaxDD':>7}"
                  f"{'>SPY':>6}{'>QQQ':>6}")
            print(f"  {'DCA SPY':<26}{dm:>6.2f}{dc * 100:>7.1f}%"
                  f"{ddd * 100:>6.0f}%{'—':>6}{'—':>6}")
            print(f"  {'DCA QQQ':<26}{qm:>6.2f}{qc * 100:>7.1f}%"
                  f"{qdd * 100:>6.0f}%{'—':>6}{'—':>6}")
            for mode in MW_MODES:
                for fb_label, fb in (("SPY-fb", spy), ("QQQ-fb", qqq)):
                    m, c, dd, _, _ = run_mode(live, data, spy, qqq, mode,
                                              index_bars=fb, win=(w0, w1))
                    k = (mode, fb_label)
                    b = beats.setdefault(k, [0, 0, 0])
                    b[0] += m > dm
                    b[1] += m > qm
                    b[2] += 1
                    print(f"  {MODE_LABEL[mode] + ' ' + fb_label:<26}"
                          f"{m:>6.2f}{c * 100:>7.1f}%{dd * 100:>6.0f}%"
                          f"{'✓' if m > dm else '✗':>6}"
                          f"{'✓' if m > qm else '✗':>6}")

        print(f"\n  VERDICT — universe {tag.split()[0]}:"
              f" windows won on MOIC (out of {len(WINDOWS)}):")
        for (mode, fb_label), (bs, bq, n) in beats.items():
            print(f"    {MODE_LABEL[mode] + ' ' + fb_label:<26}"
                  f" beats SPY {bs}/{n} · beats QQQ {bq}/{n}")

    print("\nMOIC = final value per $1 contributed (money-weighted; the"
          " number a saver experiences). CAGR = time-weighted NAV return."
          " ✓/✗ compare MOIC. Early windows on universe B are mostly the"
          " fallback index — few control names existed yet; that IS the"
          " honest answer for those years, not a bug.")


if __name__ == "__main__":
    main()
