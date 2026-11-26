#!/usr/bin/env python3
"""
Bootstrap CIs on THE test (#39, design D-39) — one window, honestly banded.
===========================================================================

The committed THE-test numbers are ONE realized path per arm. This turns
each arm's monthly NAV-return series (~60 obs) into a distribution: a
circular block bootstrap (block length 6 ≈ a regime half-year, 10,000
resamples) rebuilds synthetic 5y paths from the observed months, and the
$1/month MOIC of each path gives 5/25/50/75/95th-percentile bands, plus
P(strategy > QQQ DCA) from PAIRED draws (the same blocks applied to both
series, preserving their correlation — unpaired draws would overstate
independence and flatter the strategy).

Mandatory caveat, printed with every table (D-39): CAVEAT below. A
bootstrap reshuffles the months the window actually contained; it cannot
invent a regime the window never saw.

Machinery is importable on purpose — D-20's decile bands and #71's noise
band reuse block_moics()/paired_beats() rather than re-deriving them.
"""
import random

BLOCK = 6
N_RESAMPLES = 10_000
SEED = 39            # fixed: the gate is determinism, not luck
PCTS = (5, 25, 50, 75, 95)
CAVEAT = ("bootstrap cannot manufacture unseen regimes — these are "
          "within-window uncertainty bands, not forecasts.")


def monthly_returns(nav):
    """NAV path (unit values, len n+1) -> n monthly returns."""
    return [nav[i + 1] / nav[i] - 1 for i in range(len(nav) - 1)]


def resample_indices(n, rng, block=BLOCK):
    """One circular-block draw: index list of length n built from blocks of
    `block` consecutive positions, wrapping at the series end."""
    out = []
    while len(out) < n:
        start = rng.randrange(n)
        out.extend((start + j) % n for j in range(block))
    return out[:n]


def moic_of(returns):
    """$1 contributed at the start of each month, fund-unit accounting —
    the same arithmetic the THE test scores (MOIC = final value / paid)."""
    nav, units = 1.0, 0.0
    for r in returns:
        units += 1.0 / nav
        nav *= 1.0 + r
    n = len(returns)
    return units * nav / n if n else float("nan")


def block_moics(returns, n_resamples=N_RESAMPLES, block=BLOCK, seed=SEED):
    """-> sorted list of resampled MOICs (deterministic for a given seed)."""
    rng = random.Random(seed)
    n = len(returns)
    out = []
    for _ in range(n_resamples):
        idx = resample_indices(n, rng, block)
        out.append(moic_of([returns[i] for i in idx]))
    out.sort()
    return out


def percentiles(sorted_xs, pcts=PCTS):
    n = len(sorted_xs)
    return {p: sorted_xs[min(n - 1, max(0, round(p / 100 * (n - 1))))]
            for p in pcts}


def paired_beats(returns_a, returns_b, n_resamples=N_RESAMPLES, block=BLOCK,
                 seed=SEED):
    """P(MOIC_a > MOIC_b) under PAIRED circular-block draws: one index draw
    per resample, applied to both aligned series."""
    assert len(returns_a) == len(returns_b), "paired series must align"
    rng = random.Random(seed)
    n, wins = len(returns_a), 0
    for _ in range(n_resamples):
        idx = resample_indices(n, rng, block)
        wins += (moic_of([returns_a[i] for i in idx])
                 > moic_of([returns_b[i] for i in idx]))
    return wins / n_resamples


def render(rows, months, caveat=CAVEAT):
    """rows: [(label, realized_moic, {pct: moic}, p_beat_qqq or None)]."""
    lines = [f"Bootstrap CIs (#39) — circular block (len {BLOCK}), "
             f"{N_RESAMPLES:,} resamples, {months} monthly returns/arm, "
             f"seed {SEED}"]
    lines.append(f"{'arm':<30}{'real':>6}" + "".join(f"{f'p{p}':>7}"
                                                     for p in PCTS)
                 + f"{'P(>QQQ DCA)':>13}")
    for label, real, bands, p in rows:
        lines.append(f"{label:<30}{real:>6.2f}"
                     + "".join(f"{bands[q]:>7.2f}" for q in PCTS)
                     + (f"{p * 100:>12.1f}%" if p is not None else f"{'—':>13}"))
    lines.append(f"CAVEAT: {caveat}")
    return "\n".join(lines)


if __name__ == "__main__":
    from homily_data import fetch_daily
    from homily_strategy_backtest import (UNIV_A, UNIV_B, run_strategy,
                                          run_dca, month_first_idx, close_on)

    spy = fetch_daily("SPY", rng="5y")
    qqq = fetch_daily("QQQ", rng="5y")
    months = [spy[i][0] for i in month_first_idx(spy)][1:]

    # DCA arms: unit value IS the index price on the same month calendar
    def index_returns(ix):
        px = [close_on(ix, d) for d in months] + [ix[-1][4]]
        return [b / a - 1 for a, b in zip(px, px[1:]) if a and b]

    dca = {lbl: index_returns(ix) for lbl, ix in (("SPY", spy), ("QQQ", qqq))}

    rows = []
    for lbl in ("SPY", "QQQ"):
        r = dca[lbl]
        rows.append((f"DCA {lbl} (benchmark)", moic_of(r),
                     percentiles(block_moics(r)), None))

    for label, names in (("A current univ (HINDSIGHT)", UNIV_A),
                         ("B hype-2021 control", UNIV_B)):
        data = {}
        for n in names:
            try:
                data[n] = fetch_daily(n, rng="5y")
            except Exception:
                pass
        live = [n for n in names if n in data]
        nav = []
        run_strategy(live, data, spy, qqq, use_regime=True, index_bars=spy,
                     nav_out=nav)
        r = monthly_returns(nav)
        rows.append((f"strategy {label}", moic_of(r),
                     percentiles(block_moics(r)),
                     paired_beats(r, dca["QQQ"][:len(r)])))
        print(f"[ran strategy {label}: {len(live)} names, "
              f"{len(r)} monthly returns]", flush=True)

    print()
    print(render(rows, len(months)))
