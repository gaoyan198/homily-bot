#!/usr/bin/env python3
"""
#146 — does 🐳 have precognition? Do whale tags precede large upside GAPS?
==========================================================================

Born 2026-08-20 from the MRNA case: the stock gapped +84% at the open and
closed +177% on cancer-trial news, and the owner asked the obvious question
— did the bot see whales accumulating BEFORE the news? For MRNA the answer
was trivially no (it is capacity-cut from the universe, and a point-in-time
replay of the run-up tagged 🐳 on zero of 32 sessions — volume never once
reached the 50d average). This item asks the GENERAL version, because one
name proves nothing either way.

The claim under test is NOT "does 🐳 pay" (that is #12/#67, answered: 680
episodes, median +7.3%/60d). It is the sharper one: **does the whale
footprint carry information about news that has not broken yet** — i.e.
does a 🐳 day precede a large upside gap more often than a comparable
non-🐳 day?

Why gaps and not returns: a gap is the part of a news move that NOBODY can
trade. If informed accumulation is detectable in public OHLCV, the payoff
shows up as being positioned before gaps. If 🐳 only predicts ordinary drift,
it is a dip-buying edge (which we already own) and not precognition.

------------------------------------------------------------------------
PRE-REGISTERED RULE — frozen 2026-08-20, BEFORE the first run
------------------------------------------------------------------------
Universes   A = current bot list (36, hindsight-biased) and B = hype-2021
            control with the wrecks (29). Reported SEPARATELY; the gate
            requires agreement (the #109 failure mode: a result that holds
            in A and flips in B is not a result).
Bars        5y daily, 300-bar warmup, point-in-time only: every signal is
            computed from bars[:i+1], never past it.
Event       an upside gap on day j = open[j]/close[j-1] - 1 >= GAP_PCT.
Tag day     🐳 = whale_read().whale on day i (needs dip + >=2 of 3
            footprints, per homily_whale).
COMPARATOR  in_dip AND NOT whale, same names, same period. **Not all-days.**
            🐳 requires a dip by construction, and dips are elevated-
            volatility states which raise gap probability on their own;
            scoring 🐳 against all days would credit the tag for the dip
            it is standing in. The all-days rate is printed as CONTEXT
            ONLY and may not be used to promote anything.
Clustering  episode starts (gap > 5 days), same convention as
            homily_whale_backtest — a 12-day 🐳 cluster is ONE observation,
            not twelve. Rates are computed on episode starts.

PRIMARY ENDPOINT (the only gated number, one endpoint by design — no
multiplicity to shop):
    P(any upside gap >= 10% within 21 sessions after the tag day)
    for 🐳 episodes vs in-dip-non-🐳 episodes.

GATE — 🐳 is credited with pre-news information ONLY if BOTH hold:
    (1) relative lift over the in-dip comparator >= +25%
        (e.g. 8.0% -> 10.0% clears; 8.0% -> 9.5% does not), AND
    (2) the lift has the SAME SIGN in universe A and universe B.
Anything else = NULL, closed honestly, no re-cut and no threshold
shopping. A null here does not touch the existing 🐳 tier, which was
promoted on dip-buy returns (#12/#67) and is not on trial in this item.

SECONDARIES — info-only, never gated, no promotion may rest on them:
    · GAP_PCT in {5, 10, 20} x horizon in {10, 21, 63}, printed as a grid;
    · DIRECTION SKEW = up-gap rate minus down-gap rate. This separates the
      two ways the primary could pass: real directional foresight, versus
      🐳 merely marking high-variance states where gaps of EITHER sign are
      likelier. A primary pass with a flat skew is a volatility detector
      wearing a precognition costume, and is reported as such.
------------------------------------------------------------------------

Run: python homily_whalegap_backtest.py [--quick]
"""
import sys
from homily_data import fetch_daily
from homily_danny import danny_signal
from homily_whale import DIP_WIN, DIP_PCT
from homily_strategy_backtest import UNIV_A, UNIV_B

WARMUP = 300
PRIMARY_GAP = 10.0        # %
PRIMARY_HORIZON = 21      # sessions
GATE_LIFT = 0.25          # +25% relative
GAP_GRID = (5.0, 10.0, 20.0)
HZN_GRID = (10, 21, 63)
CLUSTER = 5               # episode separation, days


def scan(sym, bars):
    """-> (whale_idxs, diponly_idxs, all_idxs), point-in-time.

    A day lands in exactly one of the first two buckets when it is in a dip;
    all_idxs is every evaluated day (the context baseline)."""
    closes = [b[4] for b in bars]
    whale, diponly, alld = [], [], []
    for i in range(WARMUP, len(bars) - 1):
        alld.append(i)
        win = closes[max(0, i - DIP_WIN + 1):i + 1]
        if closes[i] > max(win) * (1 - DIP_PCT / 100):
            continue                      # cheap pre-filter: not a dip day
        sig = danny_signal(sym, bars[:i + 1])
        w = sig.whale
        if not w.in_dip:
            continue
        (whale if w.whale else diponly).append(i)
    return whale, diponly, alld


def episode_starts(idxs, gap=CLUSTER):
    out, prev = [], None
    for i in idxs:
        if prev is None or i - prev > gap:
            out.append(i)
        prev = i
    return out


def gap_within(bars, i, horizon, pct, direction=1):
    """Did an open-gap of >= pct% in `direction` occur within `horizon`
    sessions after day i? Uses open[j] vs close[j-1] on raw bars."""
    for j in range(i + 1, min(i + 1 + horizon, len(bars))):
        g = (bars[j][1] / bars[j - 1][4] - 1) * 100
        if direction > 0 and g >= pct:
            return True
        if direction < 0 and g <= -pct:
            return True
    return False


def rate(bars_by_sym, starts_by_sym, horizon, pct, direction=1):
    """Share of episode starts followed by a qualifying gap."""
    hit = tot = 0
    for sym, starts in starts_by_sym.items():
        bars = bars_by_sym[sym]
        for i in starts:
            if i + 1 + horizon > len(bars):
                continue                  # no full forward window: excluded
            tot += 1
            hit += gap_within(bars, i, horizon, pct, direction)
    return (100.0 * hit / tot if tot else 0.0), tot


def run_universe(name, syms):
    bars_by_sym, wh, dp, al = {}, {}, {}, {}
    for s in syms:
        try:
            b = fetch_daily(s, rng="5y")
        except Exception as e:                      # noqa: BLE001
            print(f"  ! {s}: fetch failed ({e}) — excluded")
            continue
        if len(b) < WARMUP + PRIMARY_HORIZON + 5:
            print(f"  ! {s}: {len(b)} bars < warmup — excluded")
            continue
        w, d, a = scan(s, b)
        bars_by_sym[s] = b
        wh[s], dp[s], al[s] = (episode_starts(w), episode_starts(d),
                               episode_starts(a, gap=0))
        print(f"  {s:<6} {len(b):>5}b  🐳 {len(wh[s]):>3} ep  "
              f"dip-only {len(dp[s]):>3} ep", flush=True)
    return bars_by_sym, wh, dp, al


def report(tag, bars_by_sym, wh, dp, al):
    print(f"\n{'='*72}\nUNIVERSE {tag}\n{'='*72}")
    w_r, w_n = rate(bars_by_sym, wh, PRIMARY_HORIZON, PRIMARY_GAP)
    d_r, d_n = rate(bars_by_sym, dp, PRIMARY_HORIZON, PRIMARY_GAP)
    a_r, a_n = rate(bars_by_sym, al, PRIMARY_HORIZON, PRIMARY_GAP)
    lift = (w_r / d_r - 1) if d_r else float("nan")
    print(f"\nPRIMARY  P(up-gap >= {PRIMARY_GAP:.0f}% within {PRIMARY_HORIZON}d)")
    print(f"  🐳            {w_r:>6.2f}%   (n={w_n} episodes)")
    print(f"  in-dip, no 🐳 {d_r:>6.2f}%   (n={d_n} episodes)   <- comparator")
    print(f"  all days      {a_r:>6.2f}%   (n={a_n})            <- context only")
    print(f"  RELATIVE LIFT {lift*100:>+6.1f}%   (gate needs >= +25%)")

    print(f"\nSECONDARY grid — P(up-gap >= X% within Nd), 🐳 vs in-dip-no-🐳")
    print(f"  {'':<8}" + "".join(f"{f'{h}d':>18}" for h in HZN_GRID))
    for g in GAP_GRID:
        row = f"  >={g:>4.0f}% "
        for h in HZN_GRID:
            a, _ = rate(bars_by_sym, wh, h, g)
            b, _ = rate(bars_by_sym, dp, h, g)
            row += f"{a:>7.1f}/{b:<6.1f}   "
        print(row)

    print(f"\nSECONDARY direction skew (up-rate minus down-rate, {PRIMARY_HORIZON}d)")
    for g in GAP_GRID:
        wu, _ = rate(bars_by_sym, wh, PRIMARY_HORIZON, g, +1)
        wd, _ = rate(bars_by_sym, wh, PRIMARY_HORIZON, g, -1)
        du, _ = rate(bars_by_sym, dp, PRIMARY_HORIZON, g, +1)
        dd, _ = rate(bars_by_sym, dp, PRIMARY_HORIZON, g, -1)
        print(f"  >={g:>4.0f}%   🐳 up {wu:>5.1f} dn {wd:>5.1f} skew {wu-wd:>+6.1f}"
              f"   |  dip-only up {du:>5.1f} dn {dd:>5.1f} skew {du-dd:>+6.1f}")
    return lift


if __name__ == "__main__":
    quick = "--quick" in sys.argv
    a_syms = UNIV_A[:6] if quick else UNIV_A
    b_syms = UNIV_B[:6] if quick else UNIV_B
    print(f"#146 whale-gap precognition · A={len(a_syms)} B={len(b_syms)}"
          f"{' (QUICK — not a verdict)' if quick else ''}\n")
    print("scanning universe A...")
    A = run_universe("A", a_syms)
    print("\nscanning universe B...")
    B = run_universe("B", b_syms)
    la = report("A (current bot list, hindsight-biased)", *A)
    lb = report("B (hype-2021 control, with wrecks)", *B)

    print(f"\n{'='*72}\nPRE-REGISTERED GATE\n{'='*72}")
    c1 = (la >= GATE_LIFT) and (lb >= GATE_LIFT)
    c2 = (la > 0) == (lb > 0)
    print(f"  (1) lift >= +25% in both:  A {la*100:+.1f}%  B {lb*100:+.1f}%"
          f"   -> {'PASS' if c1 else 'FAIL'}")
    print(f"  (2) same sign in A and B:  -> {'PASS' if c2 else 'FAIL'}")
    print(f"\n  VERDICT: {'PASS — 🐳 carries pre-gap information' if (c1 and c2) else 'NULL — closed, no re-cut'}")
