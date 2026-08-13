#!/usr/bin/env python3
"""
#91 (D-91) — the leverage-ladder backtest. Two questions, pre-registered:

  (a) SURVIVAL: does the regime-gated ladder ever cross its own margin-call
      boundary on any measured path — every rolling ≥5y window since 2015
      AND the max-history path (QQQ inception 1999-03, dot-com + 2008 +
      2022 inside) — at base AND stress financing?
  (b) EDGE: does ladder-levered QQQ beat unlevered QQQ B&H net of financing
      on ≥2 of the 3 construction-honest read windows (2020→2025,
      2021→2026, 2016→2026)?

PRE-REGISTERED DECISION RULE (frozen before the first run; Part III rule 6
— if the numbers disagree with D-91's expectation, the honest number ships
and the LADDER SHRINKS; nothing here is tuned after a result is seen):

  * The LEVERAGE.md policy signs at the LARGEST L ≤ 1.30 that passes BOTH
    (a) and (b). 1.50 is simulated for information only — D-91 already
    excludes it (one fast gap from a call at concentrated maintenance).
  * A single margin-call breach in ANY window at ANY financing cell fails
    that L. No re-runs with softer maintenance, no window shopping.
  * If no L passes, the policy does not sign and §8.2's leverage carve-out
    is re-frozen until a new design.

MODEL (all constants fixed a priori):
  * Maintenance m = 0.25 (IBKR-like; concentrated books run HIGHER — this
    flatters leverage, so a breach here is certainly a breach live).
  * Financing: base 5.8%/yr (≈ 2026 IBKR USD BM+1.5%), stress 7.8%
    (LEVERAGE_MEMO L3's rate+2%), ACT/252 daily accrual on the borrowed
    balance. Constant across history — DELIBERATE: the ZIRP decade's real
    ~1.5–2.5% margin would flatter every levered arm; the constant biases
    AGAINST adoption (recorded, not a bug).
  * Regime: month-end completed closes of SPY AND QQQ vs their own 10m SMA
    (both above = BULL · none above = BEAR · else MIXED) — the frozen
    §4/#63 rule recomputed point-in-time from daily bars; the label known
    at a month's last close is applied from the FIRST session of the next
    month (no look-ahead).
  * Exposure map (the D-91 ladder on an index book):
        BULL → L · MIXED → min(L, 1.15) · BEAR → 1.00 (margin zero — the
        ladder removes margin, it never exits the market; exiting is the
        CORE book's 🐻 protocol, a different product).
    Timed arm (context): BULL/MIXED → 1.0, BEAR → 0.0 in cash at 0%.
  * Releverage on the first session of each month to the target; between
    rebalances position value and debt drift (leverage RISES as price
    falls — that is exactly the path a margin call lives on).
  * Margin call: equity/position < m on any daily close → BREACH recorded;
    the arm continues delevered (1.0×) for reporting, but the L is FAILED.
  * Returns: dividend-adjusted closes (#18 — total return on both sides);
    MOIC = end equity / start equity, lump-sum NAV paths. Contributions
    are omitted deliberately: the ladder governs the whole account's gross
    exposure and the call boundary is a NAV-path property; a DCA schedule
    changes neither.

Also printed: the CORE-BOOK BAN table — pure arithmetic, no simulation.
d*(L) = (1 − mL)/(L(1 − m)) is the uniform drop that margin-calls gross L;
the §3 multiwindow strategy arms measured −59…−76% MaxDD. Any constant
L ≥ 1.25 puts d* inside that range: the core monthly book never carries
margin, and no backtest can soften arithmetic.

Reproduce: python homily_leverage_backtest.py            (~2 fetches)
Results → BACKTEST_RESULTS.md new section (#91).
"""
import datetime

from homily_data import fetch_series

M_MAINT = 0.25
FIN_BASE = 0.058
FIN_STRESS = 0.078
LADDER_LS = (1.15, 1.30, 1.50)
MIXED_CAP = 1.15
READ_WINDOWS = (("2020-07", 60), ("2021-07", 60), ("2016-07", 120))
POLICIES = ("rebal", "ratchet", "fixed")

# #138 regression lock: the committed §15 MOICs for the ladder-1.30 arm under
# the DEFAULT policy. Only the date-anchored read windows are locked — §15's
# "MAX 1999→2026" row ends at the run date, so it drifts by construction and
# cannot be asserted. If one of these moves, the policy refactor changed the
# pre-#138 behaviour and the whole §15 table is invalid.
SEC15_REBAL_L130 = {("2020-07", 60): 2.57, ("2021-07", 60): 2.29,
                    ("2016-07", 120): 9.43}


def d_star(L, m=M_MAINT):
    """Uniform drop that triggers the margin call at gross leverage L."""
    return (1 - m * L) / (L * (1 - m))


# ------------------------------------------------------------------ regime --

def month_key(d):
    return (d.year, d.month)


def month_end_closes(dates, closes):
    """[(month_key, last close of that month)] — completed months only get
    decided by the caller (the last listed month may be partial)."""
    out, cur = [], None
    for d, c in zip(dates, closes):
        k = month_key(d)
        if cur is None or k != cur[0]:
            if cur is not None:
                out.append(cur)
            cur = (k, c)
        else:
            cur = (k, c)
    if cur is not None:
        out.append(cur)
    return out


def regime_by_month(spy_d, spy_c, qqq_d, qqq_c):
    """month_key -> label to APPLY during that month (from the previous
    month's completed closes; needs 10 completed months of both)."""
    lab = {}
    me = {"SPY": month_end_closes(spy_d, spy_c),
          "QQQ": month_end_closes(qqq_d, qqq_c)}
    # walk months present in QQQ (the shorter series)
    keys = [k for k, _ in me["QQQ"]]
    for i, k in enumerate(keys):
        above = []
        for sym in ("SPY", "QQQ"):
            hist = [c for kk, c in me[sym]
                    if kk < k]                    # completed months before k
            if len(hist) < 10:
                above = None
                break
            sma = sum(hist[-10:]) / 10
            above.append(hist[-1] > sma)
        if above is None:
            lab[k] = "BULL"                       # warm-up: unlevered anyway
        elif all(above):
            lab[k] = "BULL"
        elif not any(above):
            lab[k] = "BEAR"
        else:
            lab[k] = "MIXED"
    return lab


# --------------------------------------------------------------------- sim --

def target(L, label):
    if label == "BEAR":
        return 1.0
    if label == "MIXED":
        return min(L, MIXED_CAP)
    return L


def run_arm(dates, adj, labels, L, fin, timed=False, policy="rebal",
            periods_per_year=252):
    """One NAV path. -> dict(moic, cagr, maxdd, breach, min_ratio, max_lev).

    `policy` (#138) selects what happens at each month boundary — the axis
    the ladder was never tested across, and the reason §15's survival table
    does not describe the live account:

      "rebal"   — reset position AND debt to the target every month, in both
                  directions. The pre-#138 behaviour, and the one every
                  committed §15 number was produced by. In a decline it
                  SELLS and pays debt down; that delever is what keeps the
                  drifted ratio off the call boundary.
      "ratchet" — LEVERAGE.md as actually written: lever UP to the cap on a
                  🐂 month only, NEVER sell to delever (§5 never-sell), debt
                  to zero at a 🐻 onset (§1). ⚖️ MIXED adds no new margin and
                  is allowed to drift (§1's "paydown drift" is funded by
                  contributions, which a lump-sum NAV path excludes).
      "fixed"   — borrow once at entry, never adjust again, not even at a 🐻
                  onset: the floor case where the owner does not act on the
                  signal at all.

    `max_lev` is the highest gross leverage the arm ever carried — for the
    never-delever policies that is the drift number, i.e. the answer to
    "1.30× became what?", and it is descriptive only (no pass/fail).

    `periods_per_year` sets the financing accrual to the series' own step,
    252 for the daily QQQ path this file runs. #138's core-book arm feeds a
    MONTHLY NAV and must pass 12, or interest is undercharged ~21× and every
    levered core cell is flattered into surviving.
    """
    eq, pos, debt = 1.0, 0.0, 0.0
    peak, maxdd = 1.0, 0.0
    breach, min_ratio, max_lev = None, 1.0, 0.0
    cur_m, entered = None, False
    daily_fin = fin / float(periods_per_year)
    for i, d in enumerate(dates):
        k = month_key(d)
        if k != cur_m:                            # first session of the month
            cur_m = k
            lbl = labels.get(k, "BULL")
            tgt = (0.0 if (timed and lbl == "BEAR")
                   else (1.0 if timed else target(L, lbl)))
            if breach is not None:
                tgt = min(tgt, 1.0)               # failed arms stay delevered
            if policy == "rebal" or not entered:
                pos, debt = tgt * eq, max(0.0, tgt - 1.0) * eq
            elif policy == "ratchet":
                if breach is not None or lbl == "BEAR":
                    # the ONLY delever the live policy performs (§1)
                    pos, debt = tgt * eq, max(0.0, tgt - 1.0) * eq
                elif lbl == "BULL" and pos < tgt * eq:
                    # 🐂 may lever UP into unused headroom
                    pos, debt = tgt * eq, max(0.0, tgt - 1.0) * eq
                # ⚖️ MIXED: no new margin, drift. 🐂 already above its cap:
                # left alone, because §5 forbids the sale that would fix it.
            # "fixed": never touched after entry, by construction
            entered = True
        if i:
            pos *= adj[i] / adj[i - 1]
            debt *= 1.0 + daily_fin
            eq = pos - debt if pos else eq        # cash leg: eq unchanged
        if pos:
            ratio = eq / pos
            min_ratio = min(min_ratio, ratio)
            if eq > 0:
                max_lev = max(max_lev, pos / eq)
            if ratio < M_MAINT and breach is None:
                breach = d.isoformat()
                pos, debt = eq, 0.0               # forced full delever
        peak = max(peak, eq)
        maxdd = min(maxdd, eq / peak - 1.0)
    yrs = (dates[-1] - dates[0]).days / 365.25
    return {"moic": eq, "cagr": eq ** (1 / yrs) - 1 if yrs > 0 else 0.0,
            "maxdd": maxdd, "breach": breach, "min_ratio": min_ratio,
            "max_lev": max_lev}


def window_slice(dates, start_ym, months):
    y, m = int(start_ym[:4]), int(start_ym[5:7])
    lo = datetime.date(y, m, 1)
    ey, em = y + (m - 1 + months) // 12, (m - 1 + months) % 12 + 1
    hi = datetime.date(ey, em, 1)
    idx = [i for i, d in enumerate(dates) if lo <= d < hi]
    return (idx[0], idx[-1] + 1) if idx else None


def main():
    (qqq_bars, qqq_adj) = fetch_series("QQQ", rng="max")
    (spy_bars, spy_adj) = fetch_series("SPY", rng="max")
    qd = [b[0] for b in qqq_bars]
    sd = [b[0] for b in spy_bars]
    labels = regime_by_month(sd, spy_adj, qd, qqq_adj)

    first = qd[0]
    print(f"QQQ daily {first} → {qd[-1]}  ({len(qd)} bars) · "
          f"maintenance {M_MAINT} · financing base {FIN_BASE:.1%} / "
          f"stress {FIN_STRESS:.1%}")

    # windows: rolling 5y July starts 2015..2021 + 10y 2015/2016 + max
    wins = [(f"{y}-07", 60) for y in range(2015, 2022)]
    wins += [("2015-07", 120), ("2016-07", 120)]
    wins += [("MAX", None)]

    def cells(sl, fin):
        i0, i1 = sl
        dts, adj = qd[i0:i1], qqq_adj[i0:i1]
        row = {"qqq": run_arm(dts, adj, labels, 1.0, 0.0),
               "timed": run_arm(dts, adj, labels, 1.0, 0.0, timed=True)}
        for L in LADDER_LS:
            row[f"L{L}"] = run_arm(dts, adj, labels, L, fin)
        return row

    results = {}
    print("\n== ladder arms, base financing "
          "(MOIC · CAGR · MaxDD · breach date · worst equity/position) ==")
    hdr = f"{'window':<14}" + "".join(
        f"{a:>26}" for a in ("QQQ B&H", "timed", "L1.15", "L1.30", "L1.50"))
    print(hdr)
    for start, months in wins:
        sl = ((0, len(qd)) if start == "MAX"
              else window_slice(qd, start, months))
        if not sl or sl[1] - sl[0] < 200:
            continue
        row = cells(sl, FIN_BASE)
        results[(start, months)] = row
        lab = (f"{start}+{months // 12}y" if months else "MAX(1999→)")
        line = f"{lab:<14}"
        for a in ("qqq", "timed", "L1.15", "L1.3", "L1.5"):
            key = {"L1.3": "L1.3", "L1.5": "L1.5"}.get(a, a)
            r = row.get(key) or row[{"L1.3": "L1.30", "L1.5": "L1.50"}
                                    .get(a, a)]
            br = ("" if not r["breach"] else " ⚠CALL")
            line += (f"  {r['moic']:6.2f} {r['cagr']*100:5.1f}% "
                     f"{r['maxdd']*100:5.0f}% {r['min_ratio']:.2f}{br:<6}")
        print(line)

    print("\n== stress financing (7.8%) — read windows + MAX ==")
    stress_ok = {L: True for L in LADDER_LS}
    for start, months in list(READ_WINDOWS) + [("MAX", None)]:
        sl = ((0, len(qd)) if start == "MAX"
              else window_slice(qd, start, months))
        if not sl:
            continue
        row = cells(sl, FIN_STRESS)
        lab = (f"{start}+{months // 12}y" if months else "MAX(1999→)")
        parts = []
        for L in LADDER_LS:
            r = row[f"L{L}"]
            if r["breach"]:
                stress_ok[L] = False
            parts.append(f"L{L}: {r['moic']:.2f}"
                         f"{' ⚠CALL ' + r['breach'] if r['breach'] else ''}")
        print(f"{lab:<14} " + " · ".join(parts))

    # readout (a): breaches anywhere, base cells
    base_ok = {L: all(not results[w][f"L{L}"]["breach"] for w in results)
               for L in LADDER_LS}
    # readout (b): beat unlevered QQQ on >=2/3 read windows, base financing
    edge = {}
    for L in LADDER_LS:
        wins_b = 0
        for start, months in READ_WINDOWS:
            r = results.get((start, months))
            if r and r[f"L{L}"]["moic"] > r["qqq"]["moic"]:
                wins_b += 1
        edge[L] = wins_b

    print("\n== CORE-BOOK BAN (arithmetic, no simulation) ==")
    print("gross L → uniform drop that margin-calls it (m=0.25):")
    for L in (1.15, 1.25, 1.30, 1.50, 2.00):
        flag = ("  ← INSIDE the strategy book's measured −59…−76% range"
                if d_star(L) <= 0.76 else "")
        print(f"  L={L:4.2f} → d* = −{d_star(L)*100:.1f}%{flag}")
    print("the core monthly book never carries margin (D-91, re-confirmed).")

    print("\n== PRE-REGISTERED READOUT ==")
    adopt = None
    for L in LADDER_LS:
        ok = base_ok[L] and stress_ok[L]
        e = edge[L]
        verdict = ("PASS" if (ok and e >= 2) else "FAIL")
        print(f"  L={L}: breaches base={'none' if base_ok[L] else 'YES'} "
              f"stress={'none' if stress_ok[L] else 'YES'} · beats QQQ on "
              f"{e}/3 read windows → {verdict}"
              + ("  (info only — excluded by D-91)" if L > 1.30 else ""))
        if L <= 1.30 and ok and e >= 2:
            adopt = L
    if adopt:
        print(f"\nADOPT: ladder BULL cap = {adopt:.2f}× "
              f"(MIXED {min(adopt, MIXED_CAP):.2f}× · BEAR 1.00×) — "
              "LEVERAGE.md may sign at these constants.")
    else:
        print("\nNO L ≤ 1.30 passed — the policy does NOT sign; "
              "the ladder shrinks per D-91.")

    policy_axis(qd, qqq_adj, labels, results)


def policy_axis(qd, qqq_adj, labels, results):
    """#138 · the axis §15 never varied: WHAT HAPPENS AT THE MONTH BOUNDARY.

    Everything above this line rebalances to target monthly in both
    directions, which in a decline sells and pays debt down. The live policy
    never performs that sale (§5 never-sell; §4 grandfathered shrink-only).
    Same asset, same financing, same regime labels — only the policy moves.
    """
    print("\n== #138 · REGRESSION LOCK (the policy refactor must be inert) ==")
    bad = []
    for w, want in SEC15_REBAL_L130.items():
        got = results.get(w, {}).get("L1.3", {}).get("moic")
        if got is None:
            bad.append(f"{w}: window missing")
        elif abs(got - want) > 0.015:
            bad.append(f"{w}: §15 says {want:.2f}, got {got:.2f}")
        else:
            print(f"  {str(w):<20} §15 {want:.2f} · rebuilt {got:.2f}  OK")
    if bad:
        print("  ⚠ REGRESSION FAILED — §15 is invalid, do not read further:")
        for b in bad:
            print(f"    {b}")
    else:
        print("  default policy reproduces §15 — the arms below are"
              " comparable to it.")

    print("\n== #138 · POLICY AXIS, QQQ, base financing ==")
    print("  rebal   = monthly reset both ways (what §15 measured)")
    print("  ratchet = LEVERAGE.md as written: up in 🐂, never sell,"
          " debt→0 at 🐻")
    print("  fixed   = borrow once, never act on the 🐻 signal at all")
    print(f"\n{'window':<14}{'policy':<9}"
          + "".join(f"{f'L{L}':>26}" for L in LADDER_LS))
    print(f"{'':<23}" + "".join(f"{'moic  minR  maxL':>26}"
                                for _ in LADDER_LS))
    drift = {}
    for start, months in list(READ_WINDOWS) + [("MAX", None)]:
        sl = ((0, len(qd)) if start == "MAX"
              else window_slice(qd, start, months))
        if not sl:
            continue
        dts, adj = qd[sl[0]:sl[1]], qqq_adj[sl[0]:sl[1]]
        lab = (f"{start}+{months // 12}y" if months else "MAX(1999→)")
        for pol in POLICIES:
            line = f"{lab if pol == POLICIES[0] else '':<14}{pol:<9}"
            for L in LADDER_LS:
                r = run_arm(dts, adj, labels, L, FIN_BASE, policy=pol)
                drift[(start, pol, L)] = r
                br = " ⚠CALL" if r["breach"] else ""
                line += (f"{r['moic']:>10.2f}{r['min_ratio']:>7.2f}"
                         f"{r['max_lev']:>7.2f}{br:<2}")
            print(line)

    print("\n== #138 · READOUT (a) SURVIVAL — breach ⇔ equity/position <"
          f" {M_MAINT} ==")
    for pol in POLICIES:
        for L in LADDER_LS:
            cells = [(w, drift[(w, pol, L)]) for w, _ in
                     list(READ_WINDOWS) + [("MAX", None)]
                     if (w, pol, L) in drift]
            breaches = [(w, r["breach"]) for w, r in cells if r["breach"]]
            worst = min(r["min_ratio"] for _, r in cells)
            print(f"  {pol:<8} L={L:<5} worst equity/position {worst:.2f}"
                  + ("  → PASS (zero breaches)" if not breaches else
                     "  → BREACH " + ", ".join(f"{w} {b}"
                                               for w, b in breaches)))

    print("\n== #138 · READOUT (b) DRIFT — descriptive, no pass/fail ==")
    for L in LADDER_LS:
        for pol in POLICIES:
            peak = max(r["max_lev"] for (w, p, ll), r in drift.items()
                       if p == pol and ll == L)
            print(f"  {pol:<8} started {L:.2f}× → peaked {peak:.2f}×")

    print("\n== #138 · READOUT (c) COST OF DELEVERING (sign-safe) ==")
    print("  MaxDD are NEGATIVE fractions; the test is"
          " maxdd_ratchet >= maxdd_rebal − 0.05")
    print("  (worked: rebal −0.29, ratchet −0.37 → −0.37 >= −0.34 is"
          " FALSE → ratchet worse by more than tolerance)")
    for start, _ in list(READ_WINDOWS) + [("MAX", None)]:
        if (start, "rebal", 1.30) not in drift:
            continue
        a = drift[(start, "rebal", 1.30)]
        b = drift[(start, "ratchet", 1.30)]
        ok = b["maxdd"] >= a["maxdd"] - 0.05
        print(f"  {start:<10} rebal {a['maxdd']*100:>5.0f}%  "
              f"ratchet {b['maxdd']*100:>5.0f}%  "
              f"moic {a['moic']:.2f} vs {b['moic']:.2f}  → "
              + ("within tolerance" if ok else "ratchet WORSE by >5pt"))


if __name__ == "__main__":
    main()
