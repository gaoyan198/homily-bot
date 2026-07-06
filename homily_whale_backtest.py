#!/usr/bin/env python3
"""
Whale-tag gate — is a ⚪ dip-buy conditioned on shelf + 🐳 actually better?
===========================================================================

PRD backlog #12 shipping gate. The PLTR June-2026 case showed Danny buying a
⚪-state dip at the chip shelf and being right; before the digest gets a new
tier, the pattern must survive an honest replay: do ⚪-state dip-buys
CONDITIONED on (price at the chip shelf + whale-accumulation footprint) beat
both unconditioned ⚪ dip-buys and plain DCA?

Design (no look-ahead): 5y daily bars, 300-bar warmup. A "dip day" closes
>= DIP_PCT below the DIP_WIN-day closing high. On each dip day the composite
signal is computed from bars up to that day only. Arms, each "invest $1 at
today's close":

  ⚪ dip           state CAUTION on a dip day (unconditioned)
  ⚪ dip 🎯        + price at/below the chip-shelf add zone
  ⚪ dip 🎯+🐳     + whale footprint (the candidate discretionary tier)

Baseline = forward return of EVERY day, same names — what DCA money earns on
an average day. Consecutive qualifying days cluster, so distinct episodes
(gaps > 5 days) are reported: judge sample size by episodes, not day-rows.

Universes from homily_strategy_backtest: A = current bot list (hindsight-
biased), B = hype-2021 control with the wrecks. Promotion rule per PRD:
the 🎯+🐳 arm must beat BOTH baseline and the unconditioned ⚪ arm at both
horizons on the COMBINED universe — otherwise the tag ships info-only.
"""
from homily_data import fetch_daily
from homily_danny import danny_signal
from homily_whale import DIP_WIN, DIP_PCT
from homily_strategy_backtest import UNIV_A, UNIV_B

FWD = (20, 60)
WARMUP = 300
ARMS = ("dip", "dip+shelf", "dip+shelf+whale")


def scan(sym, bars):
    """Qualifying day-indexes per arm, point-in-time."""
    closes = [b[4] for b in bars]
    hits = {a: [] for a in ARMS}
    for i in range(WARMUP, len(bars) - 1):
        win = closes[max(0, i - DIP_WIN + 1):i + 1]
        if closes[i] > max(win) * (1 - DIP_PCT / 100):
            continue                      # cheap pre-filter: not a dip day
        sig = danny_signal(sym, bars[:i + 1])
        if sig.state != "CAUTION":
            continue
        hits["dip"].append(i)
        if not (sig.add_zone and closes[i] <= sig.add_zone[1]):
            continue
        hits["dip+shelf"].append(i)
        if sig.whale.whale:
            hits["dip+shelf+whale"].append(i)
    return hits


def episodes(idxs, gap=5):
    n, prev = 0, None
    for i in idxs:
        if prev is None or i - prev > gap:
            n += 1
        prev = i
    return n


def fwd(closes, i, n):
    return closes[i + n] / closes[i] - 1 if i + n < len(closes) else None


if __name__ == "__main__":
    univ_all = UNIV_A + [n for n in UNIV_B if n not in UNIV_A]
    data, dead = {}, []
    for n in univ_all:
        try:
            data[n] = fetch_daily(n, rng="5y")
        except Exception:
            dead.append(n)

    # per-name scan once, aggregate per universe
    rets = {}   # (group, arm|BASE, horizon) -> [returns]
    eps = {}    # (group, arm) -> episode count
    groups = {"A current": [n for n in UNIV_A if n in data],
              "B hype-2021": [n for n in UNIV_B if n in data],
              "ALL combined": [n for n in univ_all if n in data]}
    scanned = {}
    for sym in [n for n in univ_all if n in data]:
        scanned[sym] = scan(sym, data[sym])
        print(f"  scanned {sym:<6} " + " ".join(
            f"{a}:{len(scanned[sym][a])}" for a in ARMS), flush=True)

    for g, names in groups.items():
        for sym in names:
            closes = [b[4] for b in data[sym]]
            for n in FWD:
                key = (g, "BASE", n)
                rets.setdefault(key, []).extend(
                    r for i in range(WARMUP, len(closes))
                    if (r := fwd(closes, i, n)) is not None)
            for a in ARMS:
                eps[(g, a)] = eps.get((g, a), 0) + episodes(scanned[sym][a])
                for n in FWD:
                    key = (g, a, n)
                    rets.setdefault(key, []).extend(
                        r for i in scanned[sym][a]
                        if (r := fwd(closes, i, n)) is not None)

    avg = lambda xs: sum(xs) / len(xs) if xs else float("nan")
    win = lambda xs: (100 * sum(x > 0 for x in xs) / len(xs)
                      if xs else float("nan"))
    print(f"\nWhale-tag gate — {len(data)} names, 5y daily, warmup {WARMUP}"
          + (f" (unfetchable: {', '.join(dead)})" if dead else ""))
    for g, names in groups.items():
        print(f"\n{g} ({len(names)} names)")
        print(f"{'arm':<18}{'days':>6}{'epis':>6}"
              f"{'fwd20':>8}{'win20':>7}{'fwd60':>8}{'win60':>7}")
        b20, b60 = rets[(g, 'BASE', 20)], rets[(g, 'BASE', 60)]
        print(f"{'DCA baseline':<18}{len(b20):>6}{'—':>6}"
              f"{avg(b20)*100:>7.1f}%{win(b20):>6.0f}%"
              f"{avg(b60)*100:>7.1f}%{win(b60):>6.0f}%")
        for a in ARMS:
            r20, r60 = rets[(g, a, 20)], rets[(g, a, 60)]
            print(f"{'⚪ ' + a:<18}{len(r20):>6}{eps[(g, a)]:>6}"
                  f"{avg(r20)*100:>7.1f}%{win(r20):>6.0f}%"
                  f"{avg(r60)*100:>7.1f}%{win(r60):>6.0f}%")

    g = "ALL combined"
    cond = [avg(rets[(g, "dip+shelf+whale", n)]) for n in FWD]
    base = [avg(rets[(g, "BASE", n)]) for n in FWD]
    unc = [avg(rets[(g, "dip", n)]) for n in FWD]
    promote = all(c > b and c > u for c, b, u in zip(cond, base, unc))
    print("\nPromotion rule (PRD #12): 🎯+🐳 must beat baseline AND the")
    print("unconditioned ⚪ dip arm at BOTH horizons on ALL combined.")
    print(f"  fwd20: 🐳 {cond[0]*100:+.1f}% vs base {base[0]*100:+.1f}% / "
          f"⚪ {unc[0]*100:+.1f}%   fwd60: 🐳 {cond[1]*100:+.1f}% vs "
          f"base {base[1]*100:+.1f}% / ⚪ {unc[1]*100:+.1f}%")
    print(f"  VERDICT: {'PROMOTE to discretionary tier' if promote else 'INFO-ONLY tag'}")
