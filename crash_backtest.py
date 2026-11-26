#!/usr/bin/env python3
"""
Owner's crash-buying rule vs plain monthly DCA — S&P 500 (SPY) and Nasdaq-100 (QQQ).
RULES FROZEN HERE BEFORE ANY RUN (2026-11-26). Do not edit after seeing results.

RESULT (run 2026-11-26): DCA stands on both indices. CRASH beat DCA in
S&P 4/17 and Nasdaq 3/17 ten-year windows; full history S&P 5.73 vs 5.79,
Nasdaq 10.63 vs 10.66 per $1 (0% cash; 2% cash barely moves it). Worst
decade S&P 2012-2022: 2.24 vs 2.40 (-7%). CRASH-LADDER is worse; HYBRID
(80/20, -20%) is ~even on S&P. Not an edge — a cheap discipline game.

Data: dividend-adjusted daily closes (homily_data.fetch_series, rng="max").
Contribution: $1 on the first trading day of every month, per index.
Drawdown = adj close / running max adj close - 1 (all-time high to date).

Arms:
  DCA          invest the $1 immediately, every month.
  CRASH        (owner's rule) the $1 waits in cash. The first day drawdown
               reaches -10%, "crash mode" starts: the WHOLE cash pile is
               invested that day, and every monthly $1 is invested on arrival
               until the index closes at a new all-time high (recovered);
               then money waits again.
  CRASH-LADDER same, but the pile goes in thirds: 1/3 at -10%, half of what
               is left at -20%, the rest at -30%. Any pile not deployed when
               the index recovers stays as cash for the next crash.
  HYBRID       80% of each $1 invested immediately; 20% waits and is deployed
               whole the first day drawdown reaches -20% (mode ends at a new
               high, same as CRASH).
Cash earns 0% (main table) and 2%/yr (sensitivity, roughly the T-bill
average since 2000). Undeployed cash counts at face value at the end.

Windows: every 10-year window starting each January 2000..2016, and the
full history (QQQ's first month to today). Metric: ending value / total
contributed.

DECISION RULE (frozen): a waiting arm "beats DCA" for an index only if it
ends higher than DCA in >= 60% of the 10-year windows AND on the full
history. Otherwise DCA stands for that index.
"""
import datetime

from crash_bot import fetch as load   # the same Yahoo adj-close series the bot reads


def simulate(series, start, end, arm, cash_rate=0.0):
    rows = [(d, p) for d, p in series if d <= end]
    peak = 0.0
    units = cash = contributed = 0.0
    mode = False
    stage = 0
    pile0 = 0.0
    last_month = None
    prev_d = None
    daily = (1 + cash_rate) ** (1 / 365.0)
    for d, p in rows:
        if prev_d is not None and cash > 0:
            cash *= daily ** (d - prev_d).days
        prev_d = d
        peak = max(peak, p)
        if d < start:
            continue
        dd = p / peak - 1
        # recovery ends crash mode
        if mode and p >= peak:
            mode = False
            stage = 0
        # monthly contribution
        ym = (d.year, d.month)
        if ym != last_month:
            last_month = ym
            contributed += 1.0
            if arm == "DCA":
                units += 1.0 / p
            elif arm == "HYBRID":
                units += 0.8 / p
                if mode:
                    units += 0.2 / p
                else:
                    cash += 0.2
            else:
                if mode:
                    units += 1.0 / p
                else:
                    cash += 1.0
        # triggers
        if arm == "CRASH" and not mode and dd <= -0.10:
            mode = True
            units += cash / p
            cash = 0.0
        elif arm == "HYBRID" and not mode and dd <= -0.20:
            mode = True
            units += cash / p
            cash = 0.0
        elif arm == "CRASH-LADDER":
            if not mode and dd <= -0.10:
                mode, stage, pile0 = True, 0, cash
            if mode:
                if stage == 0 and dd <= -0.10:
                    amt = cash / 3
                    units += amt / p; cash -= amt; stage = 1
                if stage == 1 and dd <= -0.20:
                    amt = cash / 2
                    units += amt / p; cash -= amt; stage = 2
                if stage == 2 and dd <= -0.30:
                    units += cash / p; cash = 0.0; stage = 3
        last_p = p
    return (units * last_p + cash) / contributed if contributed else None


ARMS = ("DCA", "CRASH", "CRASH-LADDER", "HYBRID")


def main():
    for sym in ("SPY", "QQQ"):
        s = load(sym)
        first = s[0][0]
        today = s[-1][0]
        qstart = datetime.date(1999, 3, 10)
        print(f"\n=== {sym} ({first} → {today}) ===")
        for rate in (0.0, 0.02):
            print(f"-- cash yield {rate:.0%} --")
            wins = {a: 0 for a in ARMS[1:]}
            n = 0
            print("window      " + "  ".join(f"{a:>12}" for a in ARMS))
            for y in range(2000, 2017):
                st = datetime.date(y, 1, 1)
                en = datetime.date(y + 10, 1, 1)
                r = {a: simulate(s, st, en, a, rate) for a in ARMS}
                n += 1
                for a in ARMS[1:]:
                    wins[a] += r[a] > r["DCA"]
                print(f"{y}-{y+10}   " + "  ".join(f"{r[a]:12.2f}" for a in ARMS))
            full = {a: simulate(s, qstart, today, a, rate) for a in ARMS}
            print(f"full {qstart.year}+  " + "  ".join(f"{full[a]:12.2f}" for a in ARMS))
            for a in ARMS[1:]:
                ok = wins[a] / n >= 0.6 and full[a] > full["DCA"]
                print(f"  {a:12} beats DCA in {wins[a]}/{n} 10y windows; "
                      f"full {full[a]:.2f} vs {full['DCA']:.2f} -> "
                      f"{'BEATS DCA' if ok else 'DCA stands'}")


if __name__ == "__main__":
    main()
