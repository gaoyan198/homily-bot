#!/usr/bin/env python3
"""
GAMBIT Part-II protocol runner (G-S4). Runs every pre-registered cell —
4 strategy arms × 9 windows × 2 cost levels, plus benchmarks and the
random band at both cost levels — and writes BACKTEST_RESULTS.md with the
gate scored mechanically (PRD §4 + Part II margin; zero editorializing:
the verdict lines are computed, not written).

Gate (restated): a candidate is promotable iff on ≥2 of the 3 most recent
5y windows (2019→2024, 2020→2025, 2021→2026) it
  (a) beats QQQ B&H MOIC by ≥ +0.10,
  (b) beats QQQ B&H on MAR (CAGR/MaxDD),
  (c) sits above the RANDOM-5 p90,
  (d) still clears (a)–(c) at 0.35% RT stress (stress arm vs stress band;
      QQQ benchmark stays at base cost — it pays one entry either way).
S1-pure is reported but NOT promotable regardless of numbers (owner
directive: only the stopped version may promote). All results are
survivorship-flattered UPPER BOUNDS (Part II); the paper ledger is the
real test.
"""
import datetime
import json

import gambit_backtest as bt
import gambit_arms as ga

QUALIFYING = [(datetime.date(2019, 1, 1), datetime.date(2024, 1, 1)),
              (datetime.date(2020, 1, 1), datetime.date(2025, 1, 1)),
              (datetime.date(2021, 1, 1), datetime.date(2026, 1, 1))]
MARGIN = 0.10


def run_protocol(series, inds, qqq, spy, regime):
    results = {}                      # (w0,w1) -> dict of arm/benchmark cells
    for w0, w1, wl in bt.WINDOWS:
        cal = bt.calendar(qqq, w0, w1)
        cell = {"label": wl, "cal": (cal[0], cal[-1])}
        cell["eligible"] = sum(
            1 for s in series.values()
            if s.eligible_at(cal[0] - datetime.timedelta(days=1)))
        cell["QQQ"] = bt.perf(bt.run_buy_hold(qqq, cal))
        cell["SPY"] = bt.perf(bt.run_buy_hold(spy, cal))
        cell["EW"] = bt.perf(bt.run_rotation(series, cal, lambda d, e: e,
                                             bt.month_boundaries(cal)))
        for tag, cs in (("base", bt.COST_SIDE), ("stress", bt.STRESS_SIDE)):
            cell[f"band_{tag}"] = bt.band(
                bt.run_random_draws(series, cal, cost_side=cs))
        for name, mode, sig in ga.ARMS:
            for tag, cs in (("base", bt.COST_SIDE), ("stress", bt.STRESS_SIDE)):
                curve, trades, events = ga.run_arm(
                    series, inds, cal, regime, mode=mode, cost_side=cs,
                    signal=sig)
                p = bt.perf(curve)
                p["trades"] = trades
                p["events"] = events
                cell[f"{name}|{tag}"] = p
        results[(w0, w1)] = cell
        print(f"  window {w0}→{w1} done")
    return results


def trade_stats(trades):
    closed = [t for t in trades if t["reason"] != "ROTATE" or True]
    if not closed:
        return "0 trades"
    rs = [t["R"] * t["frac"] for t in closed]
    full = [t["R"] for t in closed]
    wins = sum(1 for r in full if r > 0)
    return (f"{len(closed)} fills · win {wins / len(closed):.0%} · "
            f"avg {sum(full) / len(full):+.2f}R · ΣR {sum(rs):+.1f}")


def score_gate(results):
    verdicts = {}
    for name, mode, _ in ga.ARMS:
        rows = []
        for w0, w1 in QUALIFYING:
            c = results[(w0, w1)]
            qqq_moic, qqq_mar = c["QQQ"]["moic"], c["QQQ"]["mar"]
            base = c[f"{name}|base"]
            stress = c[f"{name}|stress"]
            a = base["moic"] >= qqq_moic + MARGIN
            b = base["mar"] > qqq_mar
            p90b = c["band_base"][2]
            cc = base["moic"] > p90b
            p90s = c["band_stress"][2]
            dd = (stress["moic"] >= qqq_moic + MARGIN
                  and stress["mar"] > qqq_mar and stress["moic"] > p90s)
            rows.append({"window": (w0, w1), "a": a, "b": b, "c": cc,
                         "d": dd, "pass": a and b and cc and dd})
        n_pass = sum(r["pass"] for r in rows)
        promotable = name != "S1-pure"
        verdicts[name] = {
            "rows": rows, "n_pass": n_pass,
            "verdict": ("PASS" if n_pass >= 2 and promotable else
                        "FAIL" if promotable else
                        f"NOT PROMOTABLE (owner directive; {n_pass}/3 "
                        "windows cleared)")}
    return verdicts


def render(results, verdicts, dead):
    L = []
    A = L.append
    A("# GAMBIT BACKTEST_RESULTS — Phase-1 protocol run "
      f"({datetime.date.today().isoformat()})")
    A("")
    A("**Every number here is a survivorship-flattered UPPER BOUND** (Part "
      "II): the universe was constructed 2026-07-10 from current listings; "
      "point-in-time eligibility gates are applied, but 2015-era delistings "
      "cannot be recovered. The paper ledger is the real test; P2's gate "
      "inherits nothing from this file.")
    A("")
    A("Protocol as registered in DESIGNS Part II + Amendment A1; "
      "implementation choices registered in gambit_arms.py's docstring "
      "before this run (incl. Amendment A3: cluster cap → concurrency caps, "
      "no key-free sector source). Costs 0.25% RT, stress 0.35% RT. "
      "Fills T+1 open, gaps taken in full. Random band: 200 seeded draws, "
      "5 names, 4-week rotation, recomputed at each cost level.")
    if dead:
        A(f"\nUnfetchable universe names excluded: {', '.join(dead)}.")
    A("\n## Windows\n")
    for (w0, w1), c in results.items():
        A(f"### {w0} → {w1} ({c['label']}) — eligible at open: "
          f"{c['eligible']}/120\n")
        A("| arm | MOIC | CAGR | MaxDD | MAR | MOIC@0.35% | MAR@0.35% | "
          "trades (base) |")
        A("|---|---:|---:|---:|---:|---:|---:|---|")
        for label in ("QQQ", "SPY", "EW"):
            p = c[label]
            nm = {"QQQ": "QQQ B&H", "SPY": "SPY B&H",
                  "EW": "EW-universe monthly"}[label]
            A(f"| {nm} | {p['moic']:.2f} | {p['cagr']:.1%} | "
              f"{p['maxdd']:.1%} | {p['mar']:.2f} | — | — | — |")
        for name, mode, _ in ga.ARMS:
            pb, ps = c[f"{name}|base"], c[f"{name}|stress"]
            A(f"| {name} | {pb['moic']:.2f} | {pb['cagr']:.1%} | "
              f"{pb['maxdd']:.1%} | {pb['mar']:.2f} | {ps['moic']:.2f} | "
              f"{ps['mar']:.2f} | {trade_stats(pb['trades'])} |")
        b, s = c["band_base"], c["band_stress"]
        A(f"| RANDOM-5 ×200 | p10 {b[0]:.2f} · p50 {b[1]:.2f} · **p90 "
          f"{b[2]:.2f}** | | | | p90 {s[2]:.2f} | | |")
        bd = sum(c[f"S3 vol-hole|base"]["events"]["VOLHOLE_BREAKDOWN"]
                 for _ in [0])
        A(f"\nS3 journal-only VOLHOLE_BREAKDOWN events (base): {bd}\n")
    A("## Gate — scored mechanically (PRD §4 + Part-II margin)\n")
    A("Qualifying windows: 2019→2024, 2020→2025, 2021→2026. A window "
      "clears iff (a) MOIC ≥ QQQ+0.10 AND (b) MAR > QQQ AND (c) MOIC > "
      "random p90 AND (d) all three repeat at 0.35% RT. Candidate passes "
      "iff ≥2 of 3 windows clear.\n")
    A("| candidate | window | a:MOIC+0.10 | b:MAR | c:>p90 | d:stress | "
      "window clears |")
    A("|---|---|---|---|---|---|---|")
    for name, v in verdicts.items():
        for r in v["rows"]:
            w0, w1 = r["window"]
            A(f"| {name} | {w0.year}→{w1.year} | "
              f"{'✓' if r['a'] else '✗'} | {'✓' if r['b'] else '✗'} | "
              f"{'✓' if r['c'] else '✗'} | {'✓' if r['d'] else '✗'} | "
              f"{'YES' if r['pass'] else 'no'} |")
    A("\n### Verdicts\n")
    for name, v in verdicts.items():
        A(f"* **{name}: {v['verdict']}** ({v['n_pass']}/3 qualifying "
          "windows cleared)")
    A("")
    A("Per Part II: no candidate passing → kill memo and the project stops "
      "at Phase 1 (PRD §5.2). Any PASS advances that candidate to G-S5 "
      "paper, where the P2 gate applies with no credit inherited from "
      "this file.")
    return "\n".join(L)


def main():
    uni = json.load(open("universe.json"))
    symbols = [m["symbol"] for m in uni["symbols"]]
    print(f"P1 protocol: {len(symbols)} names, fetching…")
    import gambit_data
    qqq_b, qqq_a = gambit_data.fetch_series("QQQ", rng="max")
    spy_b, spy_a = gambit_data.fetch_series("SPY", rng="max")
    qqq = bt.Series(bt.adjust_bars(qqq_b, qqq_a))
    spy = bt.Series(bt.adjust_bars(spy_b, spy_a))
    series, dead = bt.load_universe_series(symbols)
    print(f"fetched {len(series)} names"
          + (f", dead: {dead}" if dead else ""))
    inds = {s: ga.Ind(ser) for s, ser in series.items()}
    regime = ga.Regime(qqq)
    results = run_protocol(series, inds, qqq, spy, regime)
    verdicts = score_gate(results)
    doc = render(results, verdicts, dead)
    with open("BACKTEST_RESULTS.md", "w", encoding="utf-8") as f:
        f.write(doc + "\n")
    print("\nBACKTEST_RESULTS.md written. Verdicts:")
    for name, v in verdicts.items():
        print(f"  {name}: {v['verdict']}")


if __name__ == "__main__":
    main()
