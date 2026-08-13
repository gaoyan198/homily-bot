#!/usr/bin/env python3
"""
#133 · Bear-regime census — every signal the LIVE dual-index rule ever gave.
============================================================================

Owner request 2026-08-13: "timing of the bear market is more important
than ever … relook at our bear market indicators and scrutinize them."
§4 is, per our own studies, effectively the ONLY bear defence (the gated
§5.2 fires once in 33y — §33; the live combo equals §4 alone in grinders
— §33's retraction of §32), so this census walks the exact LIVE rule
over its whole joint history and prints what following it would have
meant, episode by episode. DIAGNOSTIC ONLY — there is no pass/fail gate,
nothing ships, and no engine file is touched.

RULE UNDER CENSUS (the live one, replicated to the letter):
  * month-end closes of SPY and QQQ (Yahoo 1mo, the live fetch path);
    the LAST row is dropped as the current partial month — exactly
    homily_regime.sma10_state's convention;
  * at each completed month t (both series aligned on (year, month)):
    per index, above = close_t > mean(close_{t-9..t}) (SMA includes t,
    matching sma10_state);
    BULL = both above · BEAR = both below · MIXED = split;
  * valid from the first month both indices have 10 completed months
    (QQQ lists 1999-03 → dual rule speaks from 1999-12).

REPORTED PER BEAR SPELL (consecutive BEAR month-ends):
  * onset date; how far SPY/QQQ already sat below their running peak at
    the onset close (the "it will feel late" number, made exact);
  * the further fall from onset to the episode trough (what obeying the
    signal SAVED, before re-entry costs);
  * re-entry two ways, priced on both indices:
      EITHER — first month-end not BEAR (one index recovers). This is
               what the MEASURED numbers (D-63 run_mode, §4's −1pt/yr
               headline) actually assume;
      BOTH   — first month-end BULL (both recover). This is what
               PLAYBOOK §4 step 7 ("when the banner returns to 🐂")
               tells the OWNER to do;
    round-trip = re-entry close / onset close − 1 (positive = bought
    back higher = premium paid; negative = bought back cheaper = the
    insurance paid out), printed for each rule so the divergence is a
    number, not an argument.
  * MIXED near-misses (spells never reaching BEAR) and, context, months
    where SPY alone was below (single-index bear) but QQQ vetoed.

Honesty notes frozen with the rule: price-only closes (no dividends —
repo-wide caveat, §31); Yahoo monthly bars as-served today (no
point-in-time vault for index closes; #113 would cure); indices are
survivorship-clean by construction. The last-row-partial probe at the
top prints what Yahoo actually returned TODAY so the sma10_state
boundary assumption is checked against live behaviour, not folklore.
"""
import datetime

from homily_regime import fetch_monthly

REENTRY_MODES = ("EITHER", "BOTH")


def aligned_series():
    spy = fetch_monthly("SPY")
    qqq = fetch_monthly("QQQ")
    print("last-row probe (sma10_state drops the final row as partial):")
    today = datetime.date.today()
    for sym, m in (("SPY", spy), ("QQQ", qqq)):
        d, c = m[-1]
        partial = (d.year, d.month) == (today.year, today.month)
        print(f"  {sym} last row {d} close {c:.2f} — "
              f"{'current month (partial, dropped: OK)' if partial else '⚠ NOT the current month — boundary assumption violated today'}")
    # DISCOVERY 2026-08-13, kept loud: Yahoo 1mo returns the current
    # partial month TWICE (a period row stamped the 1st + a live row
    # stamped at the last trade), so the live sma10_state's single [:-1]
    # leaves one partial row in and judges a MID-MONTH price as the
    # completed month-end (today: QQQ 718.45 partial-Aug instead of July's
    # 687.99). The census drops EVERY row of the final row's month.
    def completed(m):
        ly, lm = m[-1][0].year, m[-1][0].month
        out = [(d, c) for d, c in m if (d.year, d.month) != (ly, lm)]
        dropped = len(m) - len(out)
        print(f"    ({dropped} current-month row(s) dropped — live "
              f"sma10_state drops only 1{'; ⚠ it is reading a partial month today' if dropped > 1 else ''})")
        return out
    spy, qqq = completed(spy), completed(qqq)
    s = {(d.year, d.month): c for d, c in spy}
    q = {(d.year, d.month): c for d, c in qqq}
    keys = sorted(k for k in s if k in q)
    dates = [datetime.date(y, m, 1) for y, m in keys]
    return dates, [s[k] for k in keys], [q[k] for k in keys]


def states(sc, qc):
    out = []
    for t in range(len(sc)):
        if t < 9:
            out.append(None)
            continue
        sa = sc[t] > sum(sc[t - 9:t + 1]) / 10
        qa = qc[t] > sum(qc[t - 9:t + 1]) / 10
        out.append("BULL" if sa and qa else "BEAR" if not sa and not qa
                   else "MIXED")
    return out


def main():
    dates, sc, qc = aligned_series()
    st = states(sc, qc)
    first = next(i for i, x in enumerate(st) if x is not None)
    print(f"\ndual-rule history: {dates[first]:%Y-%m} → {dates[-1]:%Y-%m} "
          f"({len(dates) - first} month-ends)")
    n = len(st)

    counts = {"BULL": 0, "BEAR": 0, "MIXED": 0}
    for x in st[first:]:
        counts[x] += 1
    print("  months: " + " · ".join(f"{k} {v} ({100 * v / (n - first):.0f}%)"
                                    for k, v in counts.items()))
    sma_s, sma_q = sum(sc[-10:]) / 10, sum(qc[-10:]) / 10
    print(f"  latest completed month-end ({dates[-1]:%Y-%m}): {st[-1]} — "
          f"SPY {100 * (sc[-1] / sma_s - 1):+.1f}% / "
          f"QQQ {100 * (qc[-1] / sma_q - 1):+.1f}% vs own 10m SMA")
    spy_only = sum(1 for t in range(first, n)
                   if sc[t] <= sum(sc[t - 9:t + 1]) / 10 and st[t] == "MIXED")
    print(f"  QQQ-veto months (SPY below, dual says MIXED): {spy_only}")

    # ---- BEAR spells ----------------------------------------------------
    print("\nBEAR spells (the decisive signal), episode by episode:")
    t = first
    spells = 0
    agg = {m: [] for m in REENTRY_MODES}
    while t < n:
        if st[t] != "BEAR":
            t += 1
            continue
        t0 = t
        while t < n and st[t] == "BEAR":
            t += 1
        t_end = t                      # first non-BEAR month, or n
        spells += 1
        peak_s = max(sc[:t0 + 1])
        peak_q = max(qc[:t0 + 1])
        # trailing-12m month-end peak — the "recent top" a reader means by
        # "already down"; the all-time column stays (frozen wording) but is
        # misleading whenever an old mania peak (QQQ 2000) is still standing
        p12_s = max(sc[max(0, t0 - 12):t0 + 1])
        p12_q = max(qc[max(0, t0 - 12):t0 + 1])
        re_either = t_end if t_end < n else None
        re_both = next((i for i in range(t_end, n) if st[i] == "BULL"), None)
        horizon = re_both if re_both is not None else n - 1
        trough_s = min(sc[t0:horizon + 1])
        print(f"\n  onset {dates[t0]:%Y-%m} month-end · {t_end - t0} BEAR "
              f"month(s)")
        print(f"    already down at onset: SPY {100 * (sc[t0] / p12_s - 1):+.0f}% "
              f"/ QQQ {100 * (qc[t0] / p12_q - 1):+.0f}% from 12m peak "
              f"(SPY {100 * (sc[t0] / peak_s - 1):+.0f}% / "
              f"QQQ {100 * (qc[t0] / peak_q - 1):+.0f}% from all-time)")
        print(f"    further fall onset→trough (what obeying saved, gross): "
              f"SPY {100 * (trough_s / sc[t0] - 1):+.0f}%")
        for mode, ri in (("EITHER", re_either), ("BOTH", re_both)):
            tag = ("measured rule (D-63)" if mode == "EITHER"
                   else "PLAYBOOK §4.7 rule")
            if ri is None:
                print(f"    re-entry {mode:<6} — still pending at data end "
                      f"({tag})")
                continue
            rs = 100 * (sc[ri] / sc[t0] - 1)
            rq = 100 * (qc[ri] / qc[t0] - 1)
            agg[mode].append((rs, rq))
            print(f"    re-entry {mode:<6} {dates[ri]:%Y-%m} "
                  f"({ri - t0:>2}mo out) round-trip SPY {rs:+.1f}% / "
                  f"QQQ {rq:+.1f}%  ({tag})")

    print(f"\nsummary over {spells} spells "
          "(round-trip < 0 = re-entered cheaper = insurance paid out):")
    for mode in REENTRY_MODES:
        xs = agg[mode]
        if not xs:
            continue
        ms = sum(r for r, _ in xs) / len(xs)
        mq = sum(r for _, r in xs) / len(xs)
        paid = sum(1 for r, _ in xs if r > 0)
        print(f"  {mode:<6} avg round-trip SPY {ms:+.1f}% / QQQ {mq:+.1f}% · "
              f"premium paid (re-entered higher) in {paid}/{len(xs)}")

    # ---- MIXED near-misses ---------------------------------------------
    print("\nMIXED spells that never became BEAR (near-misses — these move "
          "the LEVERAGE.md ladder to 1.15×, nothing else):")
    t = first
    while t < n:
        if st[t] != "MIXED":
            t += 1
            continue
        t0 = t
        while t < n and st[t] == "MIXED":
            t += 1
        prev_bear = st[t0 - 1] == "BEAR" if t0 > first else False
        next_bear = t < n and st[t] == "BEAR"
        if not prev_bear and not next_bear:
            print(f"  {dates[t0]:%Y-%m} × {t - t0}mo")
    print("\nDIAGNOSTIC ONLY — no gate, nothing ships; findings feed the "
          "2026-08-13 bear-audit write-up.")


if __name__ == "__main__":
    print(__doc__.strip().splitlines()[1].strip("= "))
    main()
