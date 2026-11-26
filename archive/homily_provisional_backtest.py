#!/usr/bin/env python3
"""
Provisional-bar honesty check (#106, PRD §5l) — how settled is a mid-period read?
=================================================================================

Danny marks monthly charts "to be finalized" (TSM Dec 2025). Our
`monthly_closes`/`weekly_closes` include the in-progress bar, so the
digest's `monthly_up` and weekly circle are computed on bars he would
call unfinished. Before styling anything, measure it: replay 5y daily,
both universes, comparing each day's LIVE read (in-progress bar included
— exactly what the digest printed) against the verdict the SAME period
produced once its bar completed (computed at the period's final trading
day; retrospective truth, fine for measurement, never a signal).

Digest-state impact needs no `danny_signal` call: `near_support`,
`bottoming` and the hole are daily-frequency and identical across the
counterfactual, so the state label changes iff the state CLASS changes,
where class(mu, circle) = BROKEN if (not mu or circle==WHITE), PULLBACK
if (mu and AMBER), BULL if (mu and RED) — BULL covers ACCUMULATE/HOLD,
whose split (near_support) is the same on both sides. This mirrors the
frozen branch order in homily_danny.danny_signal verbatim.

Pre-committed rule (written before the run): the finding is NEGLIGIBLE —
record the numbers in HOW_IT_WORKS, close, ship nothing — if
state-class-changing divergent days are < 2% of day-name observations on
the combined pool. At >= 2% the `m…`/`w…` display-only mark (PRD #106)
gets built in this same session, goldens additive, engines untouched.
"""
from homily_clone import ema, homily_circle
from homily_data import fetch_daily, weekly_closes, monthly_closes
from homily_strategy_backtest import UNIV_A, UNIV_B

WARMUP = 320          # ~13 months of dailies + weekly-engine credibility


def monthly_up(tk_mo):
    """Verbatim monthly-trend formula from homily_danny.danny_signal."""
    e10m = ema(tk_mo, 10)
    return len(tk_mo) >= 12 and tk_mo[-1] > e10m[-1] and e10m[-1] > e10m[-2]


def state_class(mu, circle):
    if not mu or circle == "WHITE":
        return "BROKEN"
    return "PULLBACK" if circle == "AMBER" else "BULL"


def scan(names, label):
    tot = mdiv = wdiv = sdiv = early_m = 0
    dead = []
    for sym in names:
        try:
            bars = fetch_daily(sym, rng="5y")
        except Exception:
            dead.append(sym)
            continue
        if len(bars) < WARMUP + 60:
            dead.append(sym)
            continue
        # final verdicts per period, computed at each period's last bar
        month_of = [(b[0].year, b[0].month) for b in bars]
        week_of = [b[0].isocalendar()[:2] for b in bars]
        last_bar_m = {m: i for i, m in enumerate(month_of)}
        last_bar_w = {w: i for i, w in enumerate(week_of)}
        mu_final, ci_final = {}, {}
        for m, i in last_bar_m.items():
            mu_final[m] = monthly_up(monthly_closes(bars[:i + 1]))
        for w, i in last_bar_w.items():
            ci_final[w] = homily_circle(sym, weekly_closes(bars[:i + 1])).circle
        # daily live reads vs the settled verdicts
        sessions_in = 0
        for i in range(WARMUP, len(bars)):
            pre = bars[:i + 1]
            mu = monthly_up(monthly_closes(pre))
            ci = homily_circle(sym, weekly_closes(pre)).circle
            m, w = month_of[i], week_of[i]
            sessions_in = sessions_in + 1 if i and month_of[i - 1] == m else 1
            tot += 1
            md, wd = mu != mu_final[m], ci != ci_final[w]
            mdiv += md
            wdiv += wd
            early_m += md and sessions_in <= 10
            sdiv += state_class(mu, ci) != state_class(mu_final[m], ci_final[w])
        print(f"  {sym:<6} done", flush=True)
    return dict(label=label, tot=tot, mdiv=mdiv, wdiv=wdiv, sdiv=sdiv,
                early_m=early_m, dead=dead)


def report(r):
    t = r["tot"] or 1
    print(f"\n{r['label']}  ({r['tot']} day-name obs"
          + (f"; unfetchable/short: {', '.join(r['dead'])}" if r["dead"] else "")
          + ")")
    print(f"  monthly_up differs from settled month : {100*r['mdiv']/t:5.2f}%"
          f"  (of which in first 10 sessions: {100*r['early_m']/max(r['mdiv'],1):.0f}%)")
    print(f"  weekly circle differs from settled wk : {100*r['wdiv']/t:5.2f}%")
    print(f"  digest STATE class would differ       : {100*r['sdiv']/t:5.2f}%")


if __name__ == "__main__":
    ra = scan(UNIV_A, "A current univ (HINDSIGHT BIAS)")
    rb = scan([s for s in UNIV_B if s not in UNIV_A], "B hype-2021 control")
    comb = {k: (ra[k] + rb[k] if isinstance(ra[k], int) else None)
            for k in ("tot", "mdiv", "wdiv", "sdiv", "early_m")}
    comb.update(label="COMBINED", dead=ra["dead"] + rb["dead"])
    for r in (ra, rb, comb):
        report(r)
    pct = 100 * comb["sdiv"] / (comb["tot"] or 1)
    print(f"\nPre-committed rule: mark ships only if state-class divergence "
          f">= 2% combined -> {pct:.2f}% -> "
          f"{'MATERIAL — build the mark' if pct >= 2 else 'NEGLIGIBLE — record + close'}")
