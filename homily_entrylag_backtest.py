#!/usr/bin/env python3
"""
Entry lateness by TIER (#159) — when did our tiers reach his band?
==================================================================

§5p found the number on one name; this measures the method. His stated
PLTR band was $110-135 and #13's forward ledger printed CAUTION for 19
consecutive sessions inside it, reaching ACCUMULATE only at $179.01. The
question that generalises is NOT "were we late" as a single number: the
2%-capped WHALE-DIP tier marked the same shelf in June while the money
path said nothing, so a single lateness figure would average away the
only interesting structure.

So: for every scored claim in `danny_entry_claims.json`, report per TIER
the first date the engine reached it and that date's price relative to
his band, plus which gate was binding while it did not.

Four tiers, each read from the LIVE definition so this file cannot drift
from the digest (one-definition discipline, cf. validate [70]):

    WHALE-DIP  daily_run.whale_dip      — CAUTION at the shelf with the
                                          whale footprint; capped 2% (§12)
    ACCUMULATE sig.state == ACCUMULATE  — the star row
    BUY-DAY    #125 eligibility         — CONVICTION tier AND state in
                                          (ACCUMULATE, HOLD): the ONLY
                                          tier that spends money
    ROCKET     conv.gates_ok            — all five hard gates

METHOD, and the one thing that had to be fixed before any of it was
trustworthy (R6). The live digest runs in SGT morning, so the newest
COMPLETE US session is the previous calendar day: every #13 ledger row
dated D is computed from the bar of D-1, verified 29/29 on PLTR's close
column. A replay that reads bar D would therefore be testing different
arithmetic from the live engine — the #130/#138 failure mode. `replay()`
reads bars <= D-1 and is regression-locked against the ledger in
`verify_against_ledger()`: state, score, tier AND the failed-gate list
all reproduce 29/29 where the ledger overlaps.

Point-in-time by construction: bars are fetched once at 10y and every
as-of read takes the TRAILING 5-YEAR window ending at the as-of date —
what `fetch_series(rng="5y")` would have returned on that day. A plain
prefix would quietly shorten the series and inflate conviction's `age`
component on older dates.

Episode derivation is mechanical and uniform, so no claim gets a
hand-picked window: the scan starts at the beginning of the LAST
contiguous visit to the band before publication (gaps of up to
GAP_SESSIONS tolerated), and runs to SCAN_SESSIONS after that visit ends.
Where the source also states a week (the §5o zones), the derived episode
is checked against it and the agreement is reported, never used to
override the mechanical rule.

WHAT THIS MEASURES, AND WHAT IT CANNOT (frozen honesty clauses, both
directions, per the #159 gate):

  (a) The claim list is HIS, and he publishes winners. This measures
      lateness against his PUBLISHED ENTRIES ONLY. It is never evidence
      that his entries were good, and a write-up quoting it as his skill
      or our failure is wrong on its face.
  (b) EVERY claim in the corpus is RETROSPECTIVE — the band was named
      after price had left it (§51.1). So this is a REACHABILITY
      statistic, not a tradeable-lag one, except where our own forward
      ledger independently covers the window.
  (c) §5p's proprietary-indicator note: he states one input is never
      disclosed, so any gap can be attributed to a term we cannot see.
      A large lateness figure does not establish that our construct is
      wrong.

Ships nothing. No threshold moves, no digest surface, no R10 slot.
"""
import os
import json
import csv
import datetime

from homily_data import fetch_series
from homily_danny import danny_signal
from homily_conviction import conviction
import daily_run

HERE = os.path.dirname(os.path.abspath(__file__))
CLAIMS = os.path.join(HERE, "danny_entry_claims.json")
LEDGER = os.path.join(HERE, "homily_signals_log.csv")

WINDOW_YEARS = 5      # what the live digest fetches
GAP_SESSIONS = 10     # band-visit gap tolerance when deriving an episode
SCAN_SESSIONS = 252   # how far past the visit to keep looking for a tier

TIERS = ("WHALE-DIP", "ACCUMULATE", "BUY-DAY", "ROCKET")


def load_claims(path=CLAIMS):
    with open(path) as fh:
        return json.load(fh)


def trailing(bars, adj, asof, years=WINDOW_YEARS):
    """The bars the live engine would have held on `asof` — a trailing
    calendar window, not a prefix (a prefix shortens the series and
    inflates conviction's `age` points on older dates)."""
    lo = datetime.date(asof.year - years, asof.month, asof.day)
    keep = [i for i, b in enumerate(bars) if lo <= b[0] <= asof]
    return [bars[i] for i in keep], [adj[i] for i in keep]


def replay(ticker, bars, adj, sbars, sadj, run_date):
    """The engine as it stood on `run_date`, reading the PRIOR session's
    bar exactly as the live digest does. -> (sig, conv) or None."""
    asof = run_date - datetime.timedelta(days=1)
    b, a = trailing(bars, adj, asof)
    sb, sa = trailing(sbars, sadj, asof)
    if len(b) < 60 or not sb:
        return None
    sig = danny_signal(ticker, b)
    conv = conviction(sig, b, [x[4] for x in sb], adj=a, spy_adj=sa)
    return sig, conv


def tiers_reached(sig, conv):
    """Which tiers the row satisfies. Definitions come from the live
    modules so this study cannot drift from what the digest prints."""
    return {
        "WHALE-DIP": bool(daily_run.whale_dip(sig)),
        "ACCUMULATE": sig.state == "ACCUMULATE",
        # #125, as homily_buyday.star_candidates gates it
        "BUY-DAY": conv.tier == "CONVICTION" and sig.state in ("ACCUMULATE",
                                                               "HOLD"),
        "ROCKET": bool(conv.gates_ok),
    }


def band_episode(bars, lo, hi, published, gap=GAP_SESSIONS):
    """The last contiguous visit to [lo,hi] before `published`, tolerating
    `gap` sessions outside it. -> (start_date, end_date, n_sessions) or
    None. Mechanical and identical for every claim — no hand-picked
    windows."""
    idx = [i for i, b in enumerate(bars)
           if b[0] < published and lo <= b[4] <= hi]
    if not idx:
        return None
    end = idx[-1]
    start = end
    for i in reversed(idx):
        if start - i <= gap:
            start = i
        else:
            break
    inside = sum(1 for i in idx if start <= i <= end)
    return bars[start][0], bars[end][0], inside


def verify_against_ledger(rows_by_ticker, series, path=LEDGER):
    """R6 regression lock: where #13's forward ledger overlaps a claim's
    name, the replay must reproduce it EXACTLY — state, score, tier and
    the failed-gate list. Returns (matched, total, mismatches)."""
    if not os.path.exists(path):
        return 0, 0, []
    matched = total = 0
    bad = []
    with open(path) as fh:
        for r in csv.DictReader(fh):
            tk = r["ticker"]
            if tk not in series:
                continue
            bars, adj, sbars, sadj = series[tk]
            d = datetime.date.fromisoformat(r["date"])
            got = replay(tk, bars, adj, sbars, sadj, d)
            if got is None:
                continue
            sig, conv = got
            total += 1
            same = (sig.state == r["state"]
                    and str(conv.score) == r["conv_score"]
                    and conv.tier == r["conv_tier"]
                    and conv.gates_failed == [g for g in
                                              r["gates_failed"].split(";")
                                              if g])
            if same:
                matched += 1
            else:
                bad.append((tk, r["date"], sig.state, conv.score,
                            r["state"], r["conv_score"]))
    return matched, total, bad


def sessions_between(bars, d0, d1):
    return sum(1 for b in bars if d0 < b[0] <= d1)


def run(verbose=True):
    doc = load_claims()
    scored = [c for c in doc["claims"] if c.get("scored")]
    sbars, sadj = fetch_series("SPY", rng="10y")
    series, out = {}, []

    for c in scored:
        tk = c["ticker"]
        if tk not in series:
            bars, adj = fetch_series(tk, rng="10y")
            series[tk] = (bars, adj, sbars, sadj)
        bars, adj, _, _ = series[tk]
        pub = datetime.date.fromisoformat(c["published"])
        ep = band_episode(bars, c["band_lo"], c["band_hi"], pub)
        if ep is None:
            out.append({"claim": c, "episode": None})
            continue
        start, end, inside = ep
        last = bars[-1][0]
        scan = [b[0] for b in bars
                if start <= b[0] <= last][:inside + SCAN_SESSIONS]

        first = {t: None for t in TIERS}
        states, blocking = {}, {}
        for d in scan:
            got = replay(tk, bars, adj, sbars, sadj, d)
            if got is None:
                continue
            sig, conv = got
            if d <= end:
                states[sig.state] = states.get(sig.state, 0) + 1
                for g in conv.gates_failed:
                    blocking[g] = blocking.get(g, 0) + 1
            for t, hit in tiers_reached(sig, conv).items():
                if hit and first[t] is None:
                    first[t] = (d, sig.chips.last)

        # the §5o week check: reported, never used to move the window
        wk = c.get("zone_week")
        wk_ok = None
        if wk:
            wd = datetime.date.fromisoformat(wk)
            wk_ok = start <= wd <= end + datetime.timedelta(days=7)

        out.append({"claim": c, "episode": (start, end, inside),
                    "first": first, "states": states, "blocking": blocking,
                    "week_agrees": wk_ok,
                    "sessions": lambda d, b=bars, s=start: sessions_between(
                        b, s, d)})

    m, t, bad = verify_against_ledger(None, series)
    if verbose:
        _report(doc, out, (m, t, bad))
    return out, (m, t, bad)


def _pct(px, ref):
    return (px / ref - 1) * 100.0


def _report(doc, out, lock):
    m, t, bad = lock
    print("=" * 74)
    print("#159 ENTRY LATENESS BY TIER — danny_entry_claims.json "
          f"v{doc['_v']}, compiled {doc['compiled']}")
    print("=" * 74)
    print(f"\nR6 replay lock vs #13 forward ledger: {m}/{t} exact "
          "(state, score, tier, failed gates)")
    for b in bad:
        print("   MISMATCH", b)
    n_retro = sum(1 for c in doc["claims"] if c["timing"] == "retrospective")
    print(f"corpus: {len(doc['claims'])} claims, "
          f"{sum(c.get('scored', False) for c in doc['claims'])} scored, "
          f"{n_retro} retrospective, "
          f"{len(doc['claims']) - n_retro} contemporaneous")

    for r in out:
        c = r["claim"]
        print("\n" + "-" * 74)
        band = (f"${c['band_lo']:g}" if c["band_lo"] == c["band_hi"]
                else f"${c['band_lo']:g}-{c['band_hi']:g}")
        print(f"{c['ticker']}  band {band}  ({c['kind']}, "
              f"published {c['published']}, {c['timing']})")
        if not r["episode"]:
            print("  no visit to the band before publication — unscorable")
            continue
        start, end, inside = r["episode"]
        print(f"  band episode: {start} -> {end}  ({inside} sessions in band)")
        if r["week_agrees"] is not None:
            print(f"  stated week {c['zone_week']}: "
                  f"{'inside' if r['week_agrees'] else 'OUTSIDE'} "
                  "the derived episode")
        if r["states"]:
            tot = sum(r["states"].values())
            sd = ", ".join(f"{k} {v}" for k, v in
                           sorted(r["states"].items(), key=lambda x: -x[1]))
            print(f"  while price sat in his band ({tot} sessions): {sd}")
        if r["blocking"]:
            bd = ", ".join(f"{k} {v}" for k, v in
                           sorted(r["blocking"].items(), key=lambda x: -x[1]))
            print(f"  gates failing during the band: {bd}")
        for tier in TIERS:
            hit = r["first"][tier]
            if hit is None:
                print(f"  {tier:<11} never reached within "
                      f"{SCAN_SESSIONS} sessions")
                continue
            d, px = hit
            print(f"  {tier:<11} first {d} @ ${px:,.2f}  "
                  f"{_pct(px, c['band_lo']):+.0f}% on band low, "
                  f"{_pct(px, c['band_hi']):+.0f}% on band high, "
                  f"{r['sessions'](d)} sessions in")

    print("\n" + "=" * 74)
    for tier in TIERS:
        hits = [(r["claim"], r["first"][tier]) for r in out
                if r["episode"] and r["first"][tier]]
        n = len([r for r in out if r["episode"]])
        if not hits:
            print(f"{tier:<11} reached on 0/{n} claims")
            continue
        lates = sorted(_pct(px, c["band_lo"]) for c, (_, px) in hits)
        med = lates[len(lates) // 2]
        print(f"{tier:<11} reached on {len(hits)}/{n} claims, "
              f"median {med:+.0f}% above the band low "
              f"(range {lates[0]:+.0f}% .. {lates[-1]:+.0f}%)")
    print("\nReminder (frozen, module docstring): the claim list is his and "
          "he publishes\nwinners; every claim is retrospective; and one of "
          "his inputs is undisclosed.\nThis is a REACHABILITY statistic, "
          "never a verdict on his entries or ours.")


if __name__ == "__main__":
    run()
