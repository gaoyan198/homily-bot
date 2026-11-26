#!/usr/bin/env python3
"""
#135 · Bear re-entry: the measured rule vs the playbook's rule.
===============================================================

§36 finding 2: D-63's `run_mode` — the source of §4's "−1 pt/yr for
−76%→−29%" headline — starts the thirds re-entry on the first month-end
that is NOT BEAR (either index recovering is enough), while PLAYBOOK
§4.7 tells the owner to wait for the banner to read 🐂 (BOTH indices
above their 10m SMA). The census priced the divergence at up to 16 pt
(2000), 35 pt (2008 — EITHER re-entered into the May bull-trap), and
19 pt (2022) per episode, in BOTH directions. This study runs the two
rules through the full committed harness so §4.7 can prescribe the
measured winner.

RULE — FROZEN BEFORE THE FIRST RUN (mirrors the PRD §8.3 #135 row, do
not renegotiate after numbers):

  Arms (identical everything except the re-entry trigger; run_mode mode
  (d) "faithful", the §4 protocol):
    EITHER — reentry="either", the committed D-63 behaviour;
    BOTH   — reentry="both", §4.7's literal reading (powder idles
             through ⚖️ MIXED months, thirds arm on the first 🐂).
  Windows: universe B honest control, 5y (2021-07-22 → 2026-07-21) and
  10y (2016-07-22 → 2026-07-21) — the verdict windows; GRIND survivors
  33y (1993-01-01 → 2026-07-21) printed as CONTEXT (that is where §4's
  insurance pays; survivor-biased, never the verdict).
  Regression locks, both printed: (i) run_mode(faithful) with the kwarg
  omitted vs reentry="either" explicit must match at drift 0.00e+00 on
  every window (the kwarg is inert on the committed path); (ii) hold and
  sell_cash reproduce vs run_strategy via the committed
  _assert_regression on the full-history universe-B run.

  VERDICT (pre-registered): PLAYBOOK §4.7 keeps its BOTH wording ONLY if
  BOTH's MOIC ≥ EITHER's on the 5y AND the 10y honest windows with MaxDD
  not worse on both. Anything else → §4.7 is re-worded to the measured
  either-above rule (the code stays as committed either way — the loser
  is the PLAYBOOK sentence, not the harness). Part III rule 5: the §4.7
  edit ships in the follow-up docs item (#137), not here.
"""
import datetime

from homily_data import fetch_daily
from homily_strategy_backtest import UNIV_B, run_dca
from homily_bear_backtest import GRIND_UNIV, _assert_regression, _fetch, \
    run_mode

WINDOWS_B = [(datetime.date(2021, 7, 22), datetime.date(2026, 7, 21), "5y"),
             (datetime.date(2016, 7, 22), datetime.date(2026, 7, 21), "10y")]
WINDOW_G = [(datetime.date(1993, 1, 1), datetime.date(2026, 7, 21), "33y")]


def main():
    spy = fetch_daily("SPY", rng="max")
    qqq = fetch_daily("QQQ", rng="max")

    verdict = {}
    for tag, univ, wins, is_verdict in (
            ("B honest control", UNIV_B, WINDOWS_B, True),
            ("GRIND survivors (SURVIVOR BIAS, context)", GRIND_UNIV,
             WINDOW_G, False)):
        data, dead = _fetch(univ, "max")
        live = [n for n in univ if n in data]
        print(f"\n### {tag} — {len(live)} names"
              f"{' (dead: ' + ', '.join(dead) + ')' if dead else ''} ###",
              flush=True)
        if is_verdict:
            ok = _assert_regression(live, data, spy, qqq)
            print(f"  committed-harness regression: "
                  f"{'OK' if ok else 'DRIFT — RUN VOID'}")
        for w0, w1, wl in wins:
            win = (w0, w1)
            sm = run_dca(spy, spy, win=win)[0]
            qm = run_dca(qqq, spy, win=win)[0]
            base = run_mode(live, data, spy, qqq, "faithful",
                            index_bars=spy, win=win)
            either = run_mode(live, data, spy, qqq, "faithful",
                              index_bars=spy, win=win, reentry="either")
            drift = max(abs(a - b) for a, b in zip(base[:3], either[:3]))
            both = run_mode(live, data, spy, qqq, "faithful",
                            index_bars=spy, win=win, reentry="both")
            hold = run_mode(live, data, spy, qqq, "hold",
                            index_bars=spy, win=win)
            print(f"\n  --- {wl} ({w0} → {w1}) · kwarg-inert drift "
                  f"{drift:.2e} · DCA SPY {sm:.2f} / QQQ {qm:.2f} ---")
            print(f"  {'arm':<22}{'MOIC':>7}{'CAGR':>8}{'MaxDD':>8}")
            for label, r in (("hold (no §4)", hold),
                             ("faithful EITHER (D-63)", either),
                             ("faithful BOTH (§4.7)", both)):
                print(f"  {label:<22}{r[0]:>7.2f}{r[1] * 100:>7.1f}%"
                      f"{r[2] * 100:>7.0f}%")
            if is_verdict:
                verdict[wl] = (drift, either, both)

    print("\nPRE-REGISTERED VERDICT (B honest 5y AND 10y: BOTH keeps §4.7's")
    print("wording only if MOIC ≥ EITHER's with MaxDD not worse, both windows):")
    keep_both = True
    for wl, (drift, e, b) in verdict.items():
        cell = drift < 1e-9 and b[0] >= e[0] and b[2] >= e[2] - 1e-9
        keep_both = keep_both and cell
        print(f"  {wl}: BOTH {b[0]:.2f} MOIC/{b[2] * 100:.0f}% dd vs "
              f"EITHER {e[0]:.2f}/{e[2] * 100:.0f}% -> "
              f"{'BOTH holds' if cell else 'BOTH fails'}")
    print("  => " + ("§4.7 KEEPS the both-above wording; publish BOTH's "
                     "numbers as §4's cost"
                     if keep_both else
                     "RE-WORD §4.7 to the measured either-above rule "
                     "(ships via #137, Part III rule 5)"))


if __name__ == "__main__":
    print(__doc__.strip().splitlines()[1].strip("= "))
    main()
