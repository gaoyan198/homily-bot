#!/usr/bin/env python3
"""
#67b — can the ≤2% whale-dip cap be RAISED? (owner-directed, 2026-07-22)
========================================================================

PLAYBOOK §3.6b caps a whale-dip add at ≤2% of the account per name. #67
Step 4 derived 1.6% from EPISODE dispersion and queued a tightening. The
owner declined that direction and asked the opposite question: 🐳
WHALE-DIP is the only entry trigger that beat DCA (+10.9% vs +9.5%
fwd60), so is the cap mis-set on the LOW side?

WHY THE DISPERSION STUDY CANNOT ANSWER THIS. Per-episode contribution is
c × E[r] and the worst episode is c × p5 — both linear in the cap, so a
one-episode-at-a-time view makes "bigger" win trivially.

FIRST ATTEMPT, AND WHY IT WAS DISCARDED (recorded per PRD §8.5 — a
discarded design is a finding about the method, and hiding it would let a
future session repeat it). v1 laid every episode on a shared calendar and
capped AGGREGATE concurrent exposure. It returned NULL, but the null was
an artifact: the model let all ~70 names fund simultaneously, so p95
concurrency was 52 legs and the INCUMBENT 2% cap scored 104% of book
against its own 10% limit. When the status quo fails a clause by 10×, the
clause is measuring the model, not the cap. The diagnostic that fell out
of that failure is the premise of v2: with a ~3.5%-of-book monthly budget
you can fund ~1.75 legs a month at 2%, i.e. ~5 concurrent over a 60-day
hold — never 52. THE MONTHLY BUDGET BINDS LONG BEFORE THE CAP DOES.

WHAT v2 THEREFORE ASKS. Under a FIXED monthly whale-dip allowance, the
cap does not control total exposure at all — it controls GRANULARITY.
A high cap buys few big legs; a low cap buys many small ones. Same money
either way. So the real question is concentration vs diversification
INSIDE the sleeve, and that is what this measures.

Method (no look-ahead; reuses #12's scanner verbatim). `scan()` →
`episode_starts()` gives whale-dip entries point-in-time. Walking the
calendar month by month, episodes beginning that month are funded in date
order at c of book each, until the month's allowance is spent; unfunded
episodes are SKIPPED and counted (the cost of a coarse cap). Each funded
leg is held HOLD_DAYS and marked daily. Sleeve NAV = cash + open legs.

DECISION RULE (frozen here, before any v2 run):

    Grid c ∈ {1.0, 1.6, 2.0, 2.5, 3.0, 4.0}% of book per name; 2.0 =
    incumbent. Allowance = MONTHLY_FRAC of book per month. Universes A
    (hindsight, reported not trusted) and B (honest control), 5y.

    A raise above 2.0% is ADOPTABLE only if, on universe B:
      (a) the challenger's 5th-percentile sleeve MOIC across BOOTSTRAP
          resamples exceeds the incumbent's MEDIAN, AND
      (b) its median sleeve MaxDD stays within +5 pts of the incumbent's.
    Among passers the LARGEST c wins — the tie-break is deliberately the
    OPPOSITE of #51's minimal-change clause and is declared here, before
    the numbers exist, because this study was commissioned looking for
    room to raise. Stating the direction up front is what stops a
    post-hoc reading of an ambiguous table.

    CLAUSE (a) WAS TIGHTENED MID-BUILD — recorded because amending a
    "frozen" rule is exactly the move this file exists to police. As first
    written, (a) read "sleeve MOIC beats the incumbent's" on a single
    deterministic pass. A SYNTHETIC smoke test (3 legs, one month, no
    market data) then showed the design's central confound: under a fixed
    allowance a higher cap funds FEWER episodes, so caps are scored on
    different SUBSETS, and a lone winner arriving first by date can hand a
    coarse cap a flattering MOIC and a 0.0% MaxDD outright. The amendment
    adds the bootstrap and requires the challenger's p5 to clear the
    incumbent's p50, so a median drifting upward inside overlapping bands
    reads as the ordering luck it is. The change was made BEFORE any v2
    run touched real bars — no market number existed to tune toward — and
    it makes the bar STRICTER, never looser. Both conditions matter: a
    loosening amendment, or one made after seeing results, would be a
    rule-fitting exercise and the study would have to be discarded.

    A LOWER c winning clause (a) is reported but is NOT a ship — the
    owner declined the tightening direction on 2026-07-22; it would go
    back to them as a fresh decision.

    If no c > 2.0 passes: NULL, the cap stays 2%.

Gate: the rule above. A null closed honestly is a successful run.
Reproduce: `python3 homily_whalecap_backtest.py`.
"""
import random
from homily_data import fetch_daily
from homily_whale_backtest import scan, episode_starts
from homily_strategy_backtest import UNIV_A, UNIV_B

GRID_C = (0.010, 0.016, 0.020, 0.025, 0.030, 0.040)
INCUMBENT = 0.020
HOLD_DAYS = 60
BOOTSTRAP = 200           # resamples of within-month funding order
MONTHLY_FRAC = 0.035      # ~US$1,550/mo on the ~US$44k book (2026-07)


def legs_for(sym, bars):
    """-> [(entry_date, [(date, leg_return)])] for one name, point-in-time."""
    closes = [b[4] for b in bars]
    dates = [b[0] for b in bars]
    out = []
    for i in episode_starts(scan(sym, bars)["dip+shelf+whale"]):
        if closes[i] <= 0:
            continue
        path = [(dates[j], closes[j] / closes[i] - 1)
                for j in range(i, min(i + HOLD_DAYS + 1, len(closes)))]
        if len(path) > 1:
            out.append((dates[i], path))
    return out


def sleeve_result(all_legs, c, rng=None):
    """Realised sleeve MOIC (per unit of book committed) + marked MaxDD."""
    per_month = {}
    for entry, path in all_legs:
        per_month.setdefault((entry.year, entry.month), []).append(
            (entry, path))
    chosen, marks = [], {}
    funded = skipped = 0
    for mon in sorted(per_month):
        spent = 0.0
        # key on the date alone — two episodes can share an entry date and
        # the paths beside them are not orderable. `rng` shuffles instead:
        # which episodes a month can afford is the study's main CONFOUND
        # (a higher cap funds fewer, so caps are compared on different
        # SUBSETS), and resampling the order is how the sizing effect is
        # separated from ordering luck.
        order = sorted(per_month[mon], key=lambda x: x[0])
        if rng is not None:
            rng.shuffle(order)
        for entry, path in order:
            if spent + c > MONTHLY_FRAC + 1e-12:
                skipped += 1
                continue
            spent += c
            funded += 1
            chosen.append(path)
            for d, r in path:
                marks[d] = marks.get(d, 0.0) + r * c
    if not chosen:
        return None
    paid = funded * c
    gained = sum(p[-1][1] * c for p in chosen)
    moic = (paid + gained) / paid if paid else 1.0
    days = sorted(marks)
    peak, mdd = -1e9, 0.0
    for d in days:
        v = 1.0 + marks[d]
        peak = max(peak, v)
        mdd = min(mdd, v / peak - 1)
    return moic, mdd, funded, skipped


def table(all_legs, tag):
    print(f"\n{tag}  ({BOOTSTRAP} resamples of within-month funding order)")
    print(f"{'cap':>6}{'MOIC p50':>10}{'p5':>8}{'p95':>8}"
          f"{'MaxDD p50':>11}{'funded':>8}{'skipped':>9}")
    out = {}
    for c in GRID_C:
        moics, mdds, fu, sk = [], [], 0, 0
        for s in range(BOOTSTRAP):
            r = sleeve_result(all_legs, c, rng=random.Random(s))
            if r is None:
                continue
            moics.append(r[0])
            mdds.append(r[1])
            fu, sk = r[2], r[3]
        if not moics:
            continue
        moics.sort()
        mdds.sort()
        q = lambda xs, p: xs[min(len(xs) - 1, int(p * (len(xs) - 1) + 0.5))]
        lo, mid, hi = q(moics, 0.05), q(moics, 0.5), q(moics, 0.95)
        mdd = q(mdds, 0.5)
        mark = "  <- incumbent" if c == INCUMBENT else ""
        print(f"{c * 100:>5.1f}%{mid:>10.3f}{lo:>8.3f}{hi:>8.3f}"
              f"{mdd * 100:>10.1f}%{fu:>8}{sk:>9}{mark}")
        out[c] = (mid, mdd, lo, hi)
    return out


def main():
    results = {}
    for univ, names in (("B", UNIV_B), ("A", UNIV_A)):
        legs = []
        for sym in names:
            try:
                bars = fetch_daily(sym, rng="5y")
            except Exception:
                continue
            legs.extend(legs_for(sym, bars))
            print(f"  scanned {sym}", flush=True)
        results[univ] = table(legs, f"[{univ} · 5y] {len(legs)} whale-dip "
                                    f"episodes, {MONTHLY_FRAC*100:.1f}%/mo "
                                    f"allowance")

    b, inc = results["B"], results["B"].get(INCUMBENT)
    print()
    if not inc:
        print("RULE: INCONCLUSIVE — incumbent produced no funded legs.")
        return
    # clause (a) now requires the challenger's p5 to clear the incumbent's
    # p50 — a median that merely drifts up inside overlapping bands is
    # ordering luck, not a sizing effect. Added 2026-07-22 after the smoke
    # test showed caps are compared on different funded SUBSETS.
    passing = [c for c in GRID_C if c > INCUMBENT and c in b
               and b[c][2] > inc[0] and b[c][1] >= inc[1] - 0.05]
    if passing:
        best = max(passing)
        print(f"RULE: PASS — raise the cap to {best*100:.1f}% (passing: "
              f"{[f'{c*100:.1f}%' for c in passing]}; largest wins).")
    else:
        print("RULE: NULL — no cap above 2.0% clears both clauses on the "
              "honest control. The cap STAYS 2%.")
    lower = [c for c in GRID_C if c < INCUMBENT and c in b
             and b[c][0] > inc[0]]
    if lower:
        print(f"  (reported, NOT a ship: lower caps beating the incumbent "
              f"on MOIC: {[f'{c*100:.1f}%' for c in lower]} — the owner "
              "declined the tightening direction; this returns to them.)")


if __name__ == "__main__":
    main()
