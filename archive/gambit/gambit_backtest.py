#!/usr/bin/env python3
"""
GAMBIT Phase-1 backtest harness — G-S3: accounting + benchmark arms ONLY.

Pre-registered protocol (DESIGNS Part II, frozen 2026-07-10; this docstring
restates it and registers the implementation choices — changing any of these
after G-S3 begins is a logged amendment, never a silent edit):

* Windows: rolling 5-year, starting every Jan 1 from 2015 through 2021,
  plus the two 10-year windows (2015→2025, 2016→2026).
* Capital: US$20,000 lump at each window open (the paper book's notional).
* Prices: ALL accounting uses dividend-ADJUSTED prices — bars are rescaled
  by (adjclose/close) per bar, so opens are adjusted too (homily #18: raw
  closes make every dividend payer look permanently behind). MOIC is
  therefore total-return, matching the PRD §1 bar.
* Fills: decisions on day T's close, fills at day T+1's open. No look-ahead:
  selection functions receive only bars dated ≤ T.
* Costs: 0.125% per side (0.25% RT); stress arm 0.35% RT. Applied to every
  fill including rebalances.
* No margin, even simulated: a buy that would take cash below zero is
  clipped to available cash (G7 applies to paper and backtest alike).
* Point-in-time eligibility: at any decision date, a universe name is
  eligible iff its bars BEFORE that date satisfy the D-G2 numeric gates
  (last close ≥ $10, 20-day median dollar volume ≥ $25M, ≥ 20 bars). A name
  with no history yet simply isn't eligible — the survivorship mitigation
  #1 of Part II. (The 2026 capacity cut cannot be undone; every result
  stays labeled an UPPER BOUND.)
* Benchmark arms (this file, G-S3):
    QQQ B&H · SPY B&H — lump buy at first window open, hold to window end.
    EW-universe — equal-weight across all point-in-time-eligible universe
      names, rebalanced at each month's first session.
    RANDOM-5 × 200 — the luck band: every 4 weeks (28 calendar days),
      rotate to 5 names drawn uniformly from the then-eligible universe,
      equal-weight. Draw i uses random.Random(SEED_BASE + i) over the
      SORTED eligible list → bit-for-bit reproducible. The 4-week rotation
      deliberately mirrors S1's cadence so the luck band pays the same
      turnover costs the strategy will.
* Strategy arms: NOT here. G-S4 builds them on this same engine.
"""
import bisect
import datetime
import random
import statistics

import gambit_data

CAPITAL = 20_000.0
COST_SIDE = 0.00125          # 0.25% round trip
STRESS_SIDE = 0.00175        # 0.35% round trip stress arm
SEED_BASE = 20260710         # registration date — do not reroll
N_DRAWS = 200
DRAW_SIZE = 5
ROTATION_DAYS = 28

MIN_PRICE = 10.0             # D-G2 gates, applied point-in-time
MIN_MDV20 = 25e6
MIN_BARS = 20

FIVE_Y_STARTS = range(2015, 2022)
WINDOWS = ([(datetime.date(y, 1, 1), datetime.date(y + 5, 1, 1), "5y")
            for y in FIVE_Y_STARTS]
           + [(datetime.date(2015, 1, 1), datetime.date(2025, 1, 1), "10y"),
              (datetime.date(2016, 1, 1), datetime.date(2026, 1, 1), "10y")])


# ---------------------------------------------------------------- data ----

def adjust_bars(bars, adj):
    """Raw 6-tuple bars + parallel adjclose -> total-return bars (same shape,
    o/h/l/c rescaled by adj/close so any two prices give total return)."""
    out = []
    for (d, o, h, l, c, v), a in zip(bars, adj):
        f = a / c if c else 1.0
        out.append((d, o * f, h * f, l * f, a, v))
    return out


class Series:
    """Date-indexed adjusted bars for one symbol (bisect lookups)."""

    def __init__(self, bars):
        self.bars = bars
        self.dates = [b[0] for b in bars]
        self._elig = {}              # date -> bool (boundaries repeat per draw)

    def idx_at(self, d):
        """Index of the last bar dated <= d, or None."""
        i = bisect.bisect_right(self.dates, d) - 1
        return i if i >= 0 else None

    def close_at(self, d):
        i = self.idx_at(d)
        return self.bars[i][4] if i is not None else None

    def next_open(self, d):
        """(date, open) of the first session strictly after d, or None."""
        i = bisect.bisect_right(self.dates, d)
        return (self.dates[i], self.bars[i][1]) if i < len(self.bars) else None

    def eligible_at(self, d):
        """D-G2 numeric gates over bars <= d (point-in-time)."""
        if d in self._elig:
            return self._elig[d]
        i = self.idx_at(d)
        if i is None or i + 1 < MIN_BARS:
            ok = False
        else:
            window = self.bars[i - MIN_BARS + 1:i + 1]
            mdv20 = statistics.median(b[4] * b[5] for b in window)
            ok = self.bars[i][4] >= MIN_PRICE and mdv20 >= MIN_MDV20
        self._elig[d] = ok
        return ok


# ---------------------------------------------------------- accounting ----

class Portfolio:
    """Cash + positions with per-side costs. Cash can never go below zero:
    buys are clipped to available cash (no margin, simulated or otherwise)."""

    def __init__(self, capital=CAPITAL, cost_side=COST_SIDE):
        self.cash = capital
        self.cost = cost_side
        self.pos = {}                       # symbol -> qty

    def buy(self, sym, price, dollars):
        spend = min(dollars, self.cash)
        if spend <= 0 or price <= 0:
            return 0.0
        qty = spend * (1 - self.cost) / price
        self.cash -= spend
        self.pos[sym] = self.pos.get(sym, 0.0) + qty
        return qty

    def sell(self, sym, price, qty=None):
        held = self.pos.get(sym, 0.0)
        qty = held if qty is None else min(qty, held)
        if qty <= 0:
            return 0.0
        proceeds = qty * price * (1 - self.cost)
        self.cash += proceeds
        left = held - qty
        if left > 1e-12:
            self.pos[sym] = left
        else:
            self.pos.pop(sym, None)
        return proceeds

    def equity(self, series, d):
        eq = self.cash
        for sym, qty in self.pos.items():
            px = series[sym].close_at(d)
            if px:
                eq += qty * px
        return eq


def perf(curve, capital=CAPITAL):
    """Equity curve [(date, equity)] -> dict(moic, cagr, maxdd, mar)."""
    if not curve:
        return {"moic": 1.0, "cagr": 0.0, "maxdd": 0.0, "mar": 0.0}
    final = curve[-1][1]
    moic = final / capital
    years = max((curve[-1][0] - curve[0][0]).days / 365.25, 1e-9)
    cagr = moic ** (1 / years) - 1
    peak, maxdd = -1e18, 0.0
    for _, eq in curve:
        peak = max(peak, eq)
        maxdd = min(maxdd, eq / peak - 1)
    mar = cagr / abs(maxdd) if maxdd else 0.0
    return {"moic": moic, "cagr": cagr, "maxdd": maxdd, "mar": mar}


# ---------------------------------------------------------------- arms ----

def calendar(series, w0, w1):
    """Trading calendar for a window: the benchmark's session dates."""
    return [d for d in series.dates if w0 <= d < w1]


def run_buy_hold(sym_series, cal, capital=CAPITAL, cost_side=COST_SIDE):
    """Lump buy at the first session's open inside the window, hold."""
    pf = Portfolio(capital, cost_side)
    first = cal[0]
    i = sym_series.idx_at(first)
    entry_open = sym_series.bars[i][1]
    pf.buy(sym_series.bars[i][0].isoformat(), entry_open, capital)
    key = sym_series.bars[i][0].isoformat()
    return [(d, pf.cash + pf.pos[key] * (sym_series.close_at(d) or entry_open))
            for d in cal]


def run_rotation(series, cal, select, boundaries, capital=CAPITAL,
                 cost_side=COST_SIDE):
    """Generic periodic-rebalance arm (EW-universe and RANDOM-5 both ride it;
    G-S4's rotation arms will too).

    `boundaries`: decision dates (fills happen at the NEXT session's open).
    `select(decision_date, eligible_sorted)` -> list of symbols to hold,
    equal-weight, until the next boundary. No look-ahead: selection sees
    only the eligible list, prices only through decision date.
    """
    pf = Portfolio(capital, cost_side)
    plan = []                    # (fill_date, targets)
    for b in boundaries:
        eligible = sorted(s for s, ser in series.items() if ser.eligible_at(b))
        picks = select(b, eligible)
        nxt = [ser.next_open(b) for s, ser in series.items() if s in picks]
        fill_dates = [x[0] for x in nxt if x]
        if not fill_dates:
            continue
        plan.append((min(fill_dates), picks))

    curve, pi = [], 0
    for d in cal:
        while pi < len(plan) and plan[pi][0] <= d:
            _, picks = plan[pi]
            pi += 1
            # execute at today's open: sell dropped names, rebalance to EW
            opens = {}
            for sym in set(picks) | set(pf.pos):
                i = series[sym].idx_at(d)
                opens[sym] = (series[sym].bars[i][1]
                              if i is not None and series[sym].dates[i] == d
                              else series[sym].close_at(d))
            for sym in list(pf.pos):
                if sym not in picks and opens.get(sym):
                    pf.sell(sym, opens[sym])
            live = [s for s in picks if opens.get(s)]
            if not live:
                continue
            eq = pf.cash + sum(q * opens[s] for s, q in pf.pos.items()
                               if opens.get(s))
            target = eq / len(live)
            for sym in sorted(pf.pos, key=lambda s: -pf.pos[s] * opens[s]):
                if opens.get(sym):
                    val = pf.pos[sym] * opens[sym]
                    if val > target * 1.001:
                        pf.sell(sym, opens[sym], (val - target) / opens[sym])
            for sym in live:
                val = pf.pos.get(sym, 0.0) * opens[sym]
                if val < target * 0.999:
                    pf.buy(sym, opens[sym], target - val)
        curve.append((d, pf.equity(series, d)))
    return curve


def month_boundaries(cal):
    """Last session of each month inside the window (decision dates), plus
    the day before the first session so the arm is invested from the start."""
    out = [cal[0] - datetime.timedelta(days=1)]
    for a, b in zip(cal, cal[1:]):
        if a.month != b.month:
            out.append(a)
    return out


def rotation_boundaries(cal, days=ROTATION_DAYS):
    out = [cal[0] - datetime.timedelta(days=1)]
    while True:
        nxt = out[-1] + datetime.timedelta(days=days)
        if nxt >= cal[-1]:
            return out
        out.append(nxt)


def run_random_draws(series, cal, n_draws=N_DRAWS, draw_size=DRAW_SIZE,
                     seed_base=SEED_BASE, cost_side=COST_SIDE):
    """-> sorted list of n_draws MOICs (the luck band)."""
    bounds = rotation_boundaries(cal)
    moics = []
    for i in range(n_draws):
        rng = random.Random(seed_base + i)

        def pick(_d, eligible, rng=rng):
            if len(eligible) <= draw_size:
                return list(eligible)
            return rng.sample(eligible, draw_size)

        curve = run_rotation(series, cal, pick, bounds, cost_side=cost_side)
        moics.append(perf(curve)["moic"])
    return sorted(moics)


def band(moics):
    """p10/p50/p90 by nearest-rank on the sorted list."""
    n = len(moics)
    return (moics[max(0, int(0.10 * n) - 1)],
            moics[max(0, int(0.50 * n) - 1)],
            moics[max(0, int(0.90 * n) - 1)])


# ---------------------------------------------------------------- main ----

def load_universe_series(symbols):
    series, dead = {}, []
    for sym in symbols:
        try:
            bars, adj = gambit_data.fetch_series(sym, rng="max")
            series[sym] = Series(adjust_bars(bars, adj))
        except Exception:                     # noqa: BLE001 — report, don't die
            dead.append(sym)
    return series, dead


def main():
    import json
    uni = json.load(open("universe.json"))
    symbols = [m["symbol"] for m in uni["symbols"]]
    print(f"G-S3 benchmark arms — universe constructed {uni['constructed']}, "
          f"{len(symbols)} names; ALL results are survivorship-flattered "
          f"UPPER BOUNDS (Part II)")
    qqq_b, qqq_a = gambit_data.fetch_series("QQQ", rng="max")
    spy_b, spy_a = gambit_data.fetch_series("SPY", rng="max")
    qqq, spy = Series(adjust_bars(qqq_b, qqq_a)), Series(adjust_bars(spy_b, spy_a))
    series, dead = load_universe_series(symbols)
    if dead:
        print(f"unfetchable ({len(dead)}): {', '.join(dead)}")

    for w0, w1, wl in WINDOWS:
        cal = calendar(qqq, w0, w1)
        elig = sorted(s for s, ser in series.items()
                      if ser.eligible_at(cal[0] - datetime.timedelta(days=1)))
        print(f"\n── {w0} → {w1} ({wl}) · eligible at open: "
              f"{len(elig)}/{len(series)} ──")
        rows = []
        for label, ser in (("QQQ B&H", qqq), ("SPY B&H", spy)):
            p = perf(run_buy_hold(ser, cal))
            rows.append((label, p))
        ew = perf(run_rotation(series, cal, lambda d, e: e,
                               month_boundaries(cal)))
        rows.append(("EW-universe monthly", ew))
        moics = run_random_draws(series, cal)
        p10, p50, p90 = band(moics)
        for label, p in rows:
            print(f"  {label:<22}MOIC {p['moic']:>6.2f}  CAGR {p['cagr']:>7.1%}"
                  f"  MaxDD {p['maxdd']:>7.1%}  MAR {p['mar']:>5.2f}")
        print(f"  {'RANDOM-5 ×200':<22}p10 {p10:.2f} · p50 {p50:.2f} · "
              f"p90 {p90:.2f}")
        # independent hand-check (G-S3 gate): recompute QQQ B&H from the raw
        # fetch with no engine code — same convention (enter at the first
        # session's adjusted open, mark at the last adjusted close), gross of
        # the one entry cost, which is divided back out of the engine number.
        i0 = next(i for i, b in enumerate(qqq_b) if b[0] >= cal[0])
        i1 = max(i for i, b in enumerate(qqq_b) if b[0] < w1)
        entry = qqq_b[i0][1] * (qqq_a[i0] / qqq_b[i0][4])   # adjusted open
        hc = qqq_a[i1] / entry
        eng_gross = rows[0][1]["moic"] / (1 - COST_SIDE)
        drift = abs(eng_gross - hc) / hc
        print(f"  QQQ hand-check: engine(gross) {eng_gross:.4f} vs "
              f"independent {hc:.4f} ({drift:.2%} drift) "
              f"{'OK' if drift < 0.01 else '** >1% **'}")


if __name__ == "__main__":
    main()
