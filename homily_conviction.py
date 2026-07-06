#!/usr/bin/env python3
"""
Multi-bagger conviction score — STRINGENT by design.
====================================================

Ranks names on Danny-style conviction criteria (he concentrated early in
TSLA/PLTR/NVDA: secular leaders bought in uptrends, not bargain bins) plus
"room to run". All inputs are price/volume derived and transparent; the full
rubric is documented in docs/index.html.

HARD GATES (all must pass before a name can appear as 🚀):
  G1 size    avg 20d dollar volume < $5B/day — megacaps by trading value
             (NVDA ~$32B/d, TSLA/AAPL/AMD...) can't 5x quickly. NB:
             $-volume is a PROXY for market cap and over-counts hot
             momentum names (real mcap needs authed APIs — PRD backlog).
  G2 trend   monthly UP and weekly RED — leaders only, no falling knives.
  G3 leader  12m return beats SPY by >= 20 points — relative strength.
  G4 basis   price above POC — the crowd's cost basis is defended.
  G5 data    >= 200 daily bars — too-fresh IPOs are unratable, skip.

SCORE (0-100) ranks the gated survivors and sets the sizing tier:
  trend 25 · relative strength 25 · structure 15 · vol-hole 10 ·
  size/room 15 · listing age 10

SIZING TIERS (guidance, not orders — hard cap regardless: no single name
above 10% of the account including what's already held):
  score >= 75  CONVICTION  up to 5% of account, add only at ⭐ zones
  score 60-74  STARTER     up to 2%, prove itself before sizing up
  score < 60   fails       watch only, no capital
"""
from dataclasses import dataclass

GATE_DVOL = 5e9     # G1: avg 20d dollar volume ceiling
GATE_RS12 = 20.0    # G3: 12m excess return vs SPY, percentage points
MIN_BARS = 200      # G5

TRADING_YEAR = 252


@dataclass
class Conviction:
    score: int
    tier: str            # CONVICTION / STARTER / fails
    gates_ok: bool
    gates_failed: list   # e.g. ["G1 size", "G3 leader"]
    rs12: float          # 12m excess return vs SPY, points
    dvol: float          # avg 20d dollar volume
    parts: dict          # component -> points, for the digest/page


def _ret(closes, n):
    n = min(n, len(closes) - 1)
    return (closes[-1] / closes[-1 - n] - 1) * 100


def conviction(sig, bars, spy_closes):
    """sig: homily_danny.DannySignal for the same bars."""
    closes = [b[4] for b in bars]
    dvol = sum(b[4] * b[5] for b in bars[-20:]) / min(20, len(bars))
    rs12 = _ret(closes, TRADING_YEAR) - _ret(spy_closes, TRADING_YEAR)
    rs6 = _ret(closes, TRADING_YEAR // 2) - _ret(spy_closes, TRADING_YEAR // 2)

    failed = []
    if dvol >= GATE_DVOL:                       failed.append("G1 size")
    if not (sig.monthly_up and sig.weekly.circle == "RED"):
                                                failed.append("G2 trend")
    if rs12 < GATE_RS12:                        failed.append("G3 leader")
    if closes[-1] <= sig.chips.poc:             failed.append("G4 basis")
    if len(bars) < MIN_BARS:                    failed.append("G5 data")

    p = {}
    p["trend"] = ((10 if sig.monthly_up else 0)
                  + (10 if sig.weekly.circle == "RED" else 0)
                  + (5 if sig.weekly.circle == "RED"
                     and sig.weekly.weeks_in_regime >= 8 else 0))
    p["rel strength"] = ((20 if rs12 >= 100 else 15 if rs12 >= 50
                          else 10 if rs12 >= GATE_RS12 else 0)
                         + (5 if rs6 >= 10 else 0))
    p["structure"] = ((5 if closes[-1] > sig.chips.poc else 0)
                      + (5 if sig.chips.pct_in_profit >= 60 else 0)
                      + (5 if sig.state == "ACCUMULATE" else 0))
    h = sig.vol_hole
    p["vol hole"] = (10 if h and h.status == "BREAKOUT" and h.age <= 30
                     else 5 if h and h.status == "INSIDE" else 0)
    p["size/room"] = (15 if dvol < 5e8 else 12 if dvol < 1.5e9
                      else 8 if dvol < 3e9 else 4 if dvol < GATE_DVOL else 0)
    years = len(bars) / TRADING_YEAR  # capped by fetch range; good enough
    p["age"] = 10 if years < 4.5 else 5  # 5y fetch: full history = mature

    score = sum(p.values())
    tier = ("CONVICTION" if score >= 75 else
            "STARTER" if score >= 60 else "fails")
    return Conviction(score, tier if not failed else "fails",
                      not failed, failed, rs12, dvol, p)


if __name__ == "__main__":
    from homily_data import fetch_daily
    from homily_danny import danny_signal
    spy = [b[4] for b in fetch_daily("SPY", rng="5y")]
    for sym in ("RKLB", "PLTR", "NVDA", "HOOD", "AXON", "ZETA"):
        bars = fetch_daily(sym, rng="5y")
        c = conviction(danny_signal(sym, bars), bars, spy)
        gate = "PASS" if c.gates_ok else "fail:" + ",".join(c.gates_failed)
        print(f"{sym:<5} score {c.score:>3} {c.tier:<10} {gate:<28} "
              f"RS12 {c.rs12:+6.0f}pts  $vol {c.dvol/1e9:.2f}B/d  {c.parts}")
