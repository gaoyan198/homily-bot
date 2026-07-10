#!/usr/bin/env python3
"""
THE test: full strategy vs DCA into SPY/QQQ.
============================================

Question: does "accumulate conviction names on ⭐ dips, sell everything on
🐻 regime, redeploy on 🐂" beat mechanically DCA-ing the same money into an
index fund? Point-in-time, monthly, no look-ahead, 10bps per trade.

Mechanics (exactly what the digest advises):
  * $1 of new money arrives at the first trading day of each month.
  * Regime = month-end 10m-SMA on SPY AND QQQ (completed months only).
      BEAR  -> liquidate all stock positions, hold cash, keep contributing.
      else  -> deploy ALL available cash equally into names whose signal —
               computed only from bars up to that day — is ⭐ ACCUMULATE
               (fallback: 🔵 BOTTOMING). No candidates -> cash waits.
  * Positions are held (never sold per-name) until a BEAR liquidation.

Two universes, because WHICH LIST YOU FEED IT decides the result:
  A  "current"  — today's bot universe. HINDSIGHT-PICKED 2026 winners; any
                  result is upward-biased. Reported, but not trusted.
  B  "hype2021" — what a growth investor plausibly held in mid-2021:
                  winners AND still-listed wrecks (PTON, ZM, DOCU, ROKU,
                  LCID, TDOC...). The honest control: can the signals dodge
                  losers they haven't seen die? (Fully delisted names can't
                  be fetched key-free -> residual survivorship remains.)

Scoring uses fund-unit NAV accounting (contributions buy units at NAV), so
CAGR is time-weighted and MaxDD is real, plus MOIC = final value / $ paid in.
Benchmarks: same $1/month DCA'd into SPY and into QQQ, no timing.
"""
import datetime
from homily_data import fetch_daily, monthly_closes
from homily_danny import danny_signal

COST = 0.001
UNIV_A = ["NVDA","TSM","AVGO","AMD","ASML","TSLA","PLTR","MSFT","AMZN",
          "META","NFLX","ORCL","MU","QCOM","ANET","VRT","LRCX","AMAT",
          "CRM","CRWD","PANW","NET","DDOG","SNOW","ZS","APP","SHOP","UBER",
          "AXON","RBLX","SOFI","HIMS","DUOL","TOST","IOT","RKLB"]
UNIV_B = ["PTON","ZM","DOCU","SNAP","ROKU","TDOC","CHWY","LCID","AFRM",
          "UPST","U","DKNG","BYND","PYPL","ETSY","PINS","W","RBLX","COIN",
          "SHOP","NET","PLTR","SPOT","CRWD","DDOG","SE","ZS","OKTA","TWLO"]


def month_first_idx(bars):
    out, cur = [], None
    for i, b in enumerate(bars):
        k = (b[0].year, b[0].month)
        if k != cur:
            out.append(i); cur = k
    return out


def regime_series(spy, qqq):
    """date -> True if BEAR (both completed-month closes < their 10m SMA)."""
    def bear_at(bars, d):
        mos = monthly_closes([b for b in bars if b[0] < d.replace(day=1)])
        if len(mos) < 11:
            return False
        done = mos  # all months fully before current month are complete
        return done[-1] < sum(done[-10:]) / 10
    return lambda d: bear_at(spy, d) and bear_at(qqq, d)


def close_on(bars, d):
    px = None
    for b in bars:
        if b[0] <= d:
            px = b[4]
        else:
            break
    return px


def run_strategy(names, data, spy, qqq, use_regime=True, min_bars=260,
                 index_bars=None):
    """index_bars set -> PLAYBOOK §3.5: months with no ⭐/🔵 buy the INDEX
    core (never sold) instead of parking cash. None -> legacy cash-waits."""
    is_bear = regime_series(spy, qqq)
    months = [spy[i][0] for i in month_first_idx(spy)][1:]
    cash = paid = 0.0
    hold = {}                      # name -> shares (sold on bear)
    core = 0.0                     # index-core shares (never sold)
    nav, unit_val, units = [], 1.0, 0.0
    cash_months = trades = 0
    for d in months:
        # mark portfolio, update NAV before today's contribution
        ipx = (close_on(index_bars, d) or 0) if index_bars else 0
        val = cash + core * ipx + sum(sh * (close_on(data[n], d) or 0)
                                      for n, sh in hold.items())
        if units > 0:
            unit_val = val / units
        nav.append(unit_val)
        cash += 1.0; paid += 1.0
        units += 1.0 / unit_val

        if use_regime and is_bear(d):
            for n, sh in hold.items():
                px = close_on(data[n], d)
                if px:
                    cash += sh * px * (1 - COST); trades += 1
            hold = {}
            cash_months += 1
            continue
        # point-in-time signals over names with enough history
        cands, backs = [], []
        for n in names:
            bars = [b for b in data[n] if b[0] <= d]
            if len(bars) < min_bars:
                continue
            try:
                st = danny_signal(n, bars).state
            except Exception:
                continue
            if st == "ACCUMULATE":
                cands.append(n)
            elif st == "BOTTOMING":
                backs.append(n)
        picks = cands or backs
        if picks and cash > 0:
            per = cash * (1 - COST) / len(picks)
            for n in picks:
                px = close_on(data[n], d)
                if px:
                    hold[n] = hold.get(n, 0) + per / px; trades += 1
            cash = 0.0
        elif index_bars and ipx > 0 and cash > 0:   # §3.5: no stars -> index
            core += cash * (1 - COST) / ipx; cash = 0.0; trades += 1
        elif cash > 1.5:
            cash_months += 1
    d_end = spy[-1][0]
    eipx = (close_on(index_bars, d_end) or 0) if index_bars else 0
    final = cash + core * eipx + sum(sh * (close_on(data[n], d_end) or 0)
                                     for n, sh in hold.items())
    unit_val = final / units
    nav.append(unit_val)
    yrs = len(months) / 12
    cagr = (nav[-1] / nav[0]) ** (1 / yrs) - 1
    mdd = min(nav[j] / max(nav[:j + 1]) - 1 for j in range(1, len(nav)))
    return final / paid, cagr, mdd, cash_months, trades


def run_dca(bars_ix, spy, win=None):
    """$1/month into one index on the SPY month calendar. `win=(start,end)`
    restricts contribution months (multi-window re-tests). Months before the
    index has data are skipped — on a max-range calendar QQQ only exists from
    1999-03, so its DCA (and CAGR clock) starts at its first bar, not 1993."""
    months = [spy[i][0] for i in month_first_idx(spy)][1:]
    if win:
        months = [m for m in months if win[0] <= m <= win[1]]
    units = paid = 0.0
    nav = []
    for d in months:
        px = close_on(bars_ix, d)
        if px is None:
            continue
        nav.append(px)
        units += 1.0 / px; paid += 1.0
    final = units * ((close_on(bars_ix, win[1]) or nav[-1]) if win
                     else bars_ix[-1][4])
    yrs = len(nav) / 12
    cagr = (nav[-1] / nav[0]) ** (1 / yrs) - 1
    mdd = min(nav[j] / max(nav[:j + 1]) - 1 for j in range(1, len(nav)))
    return final / paid, cagr, mdd


if __name__ == "__main__":
    spy = fetch_daily("SPY", rng="5y")
    qqq = fetch_daily("QQQ", rng="5y")
    print(f"window: {spy[0][0]} -> {spy[-1][0]}  ($1/month, 10bps/trade)")
    print(f"\n{'':34}{'MOIC':>6}{'TWR CAGR':>10}{'MaxDD':>8}{'cash-mo':>8}{'trades':>7}")
    for label, ix in (("DCA SPY (benchmark)", spy),
                      ("DCA QQQ (benchmark)", qqq)):
        m, c, dd = run_dca(ix, spy)
        print(f"{label:<34}{m:>6.2f}{c*100:>9.1f}%{dd*100:>7.0f}%{'—':>8}{'—':>7}")
    for label, names in (("A current univ (HINDSIGHT BIAS)", UNIV_A),
                         ("B hype-2021 control", UNIV_B)):
        data, dead = {}, []
        for n in names:
            try:
                data[n] = fetch_daily(n, rng="5y")
            except Exception:
                dead.append(n)
        live = [n for n in names if n in data]
        # ix=None -> legacy cash-waits; ix=spy -> PLAYBOOK §3.5 index fallback
        for rg, ix, tag in ((False, None, "cash-wait     "),
                            (False, spy,  "idx-fallback  "),
                            (True,  spy,  "idx-fb+regime ")):
            m, c, dd, cm, tr = run_strategy(live, data, spy, qqq, rg,
                                            index_bars=ix)
            print(f"{label[:18]:<18} {tag:<15}{m:>6.2f}{c*100:>9.1f}%"
                  f"{dd*100:>7.0f}%{cm:>8}{tr:>7}")
        if dead:
            print(f"{'':18} (unfetchable/delisted, excluded: {', '.join(dead)})")
    print("\nMOIC = final value per $1 contributed. TWR = time-weighted NAV")
    print("return. idx-fallback = no-⭐ months buy the index (PLAYBOOK §3.5),")
    print("the faithful strategy; cash-wait is the old under-invested variant.")
    print("Universe A is hindsight-picked — read B for the truth.")
