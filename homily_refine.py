#!/usr/bin/env python3
"""
Daily auto-refinement engine for the Homily-clone strategy.
===========================================================

Honours the request to "refine the algorithm every day" WITHOUT overfitting:

  * Parameters are tuned, but a challenger param-set only becomes the new
    champion if it beats the current champion OUT-OF-SAMPLE (walk-forward),
    by a margin. In-sample backtest fit is never trusted on its own.
  * Small param grid (18 combos) -> few degrees of freedom -> less curve-fit.
  * Objective = Calmar-like CAGR/|maxDD| averaged across a multi-name basket,
    measured only on the held-out (test) segment. We optimise the strategy's
    one real edge (drawdown control), and still print raw CAGR so the return
    cost vs buy-&-hold stays visible.

State persists in homily_champion.json (+ append-only homily_refine_log.csv) so
performance drift is tracked over time rather than silently re-fit each day.
"""
import json, os, datetime
from homily_clone import ema, sma, macd
from homily_backtest import max_drawdown, cagr, COST_BPS
from bt_data import BT

HERE = os.path.dirname(os.path.abspath(__file__))
CHAMPION = os.path.join(HERE, "homily_champion.json")
LOG = os.path.join(HERE, "homily_refine_log.csv")

# --- small parameter grid (deliberately tiny to limit overfitting) ---------
GRID = [{"ef": ef, "es": es, "inv": inv}
        for ef in (8, 10, 13) for es in (26, 30, 40)
        for inv in ("RED", "RED+AMBER")]
DEFAULT = {"ef": 10, "es": 30, "inv": "RED"}

def circle_series_p(closes, ef, es):
    e_f, e_s, s_s = ema(closes, ef), ema(closes, es), sma(closes, es)
    line, _, hist = macd(closes)
    out = []
    for i in range(len(closes)):
        sc = (closes[i] > e_s[i]) + (e_f[i] > e_s[i]) + \
             (hist[i] > 0 and line[i] > 0) + \
             (s_s[i] is not None and i >= 4 and s_s[i-4] is not None and s_s[i] > s_s[i-4])
        out.append("RED" if sc >= 3 else ("WHITE" if sc <= 1 else "AMBER"))
    return out

def run(closes, p):
    inv = {"RED"} if p["inv"] == "RED" else {"RED", "AMBER"}
    circ = circle_series_p(closes, p["ef"], p["es"])
    cost = COST_BPS / 10000.0
    eq, pos = [1.0], 0
    for i in range(len(closes) - 1):
        want = 1 if circ[i] in inv else 0
        if want != pos:
            eq[-1] *= (1 - cost); pos = want
        eq.append(eq[-1] * (closes[i+1]/closes[i] if pos else 1.0))
    c, dd = cagr(eq, len(closes)-1), max_drawdown(eq)
    return {"cagr": c, "mdd": dd, "calmar": c/abs(dd) if dd < 0 else c}

def basket_score(split, p, metric="calmar"):
    """Average OOS metric across the basket on the TEST segment only."""
    vals = []
    for closes in BT.values():
        cut = int(len(closes) * split)
        test = closes[cut:]
        vals.append(run(test, p)[metric])
    return sum(vals) / len(vals)

def search(train_split=0.6):
    """Pick best params on TRAIN, report their TEST (OOS) result -> honest."""
    def score_on(seg_lo, seg_hi, p):
        vals = []
        for closes in BT.values():
            n = len(closes); lo, hi = int(n*seg_lo), int(n*seg_hi)
            vals.append(run(closes[lo:hi], p)["calmar"])
        return sum(vals)/len(vals)
    best = max(GRID, key=lambda p: score_on(0.0, train_split, p))      # tuned in-sample
    oos_best = score_on(train_split, 1.0, best)                        # judged OOS
    oos_def  = score_on(train_split, 1.0, DEFAULT)
    return best, oos_best, oos_def

def load_champion():
    if os.path.exists(CHAMPION):
        return json.load(open(CHAMPION))
    return {"params": DEFAULT, "oos_calmar": basket_score(0.6, DEFAULT),
            "since": str(datetime.date.today())}

def daily_refine(margin=0.10):
    champ = load_champion()
    challenger, oos_chal, oos_def = search()
    champ_oos = basket_score(0.6, champ["params"])
    adopted = False
    # adopt challenger only if it beats the CURRENT champion OOS by a margin
    if oos_chal > champ_oos * (1 + margin) and challenger != champ["params"]:
        champ = {"params": challenger, "oos_calmar": oos_chal,
                 "since": str(datetime.date.today())}
        json.dump(champ, open(CHAMPION, "w"), indent=2)
        adopted = True
    row = f'{datetime.date.today()},{champ["params"]},{champ_oos:.3f},{oos_chal:.3f},{oos_def:.3f},{adopted}\n'
    if not os.path.exists(LOG):
        open(LOG, "w").write("date,champion,champ_oos,challenger_oos,default_oos,adopted\n")
    open(LOG, "a").write(row)
    return champ, challenger, oos_chal, oos_def, champ_oos, adopted

if __name__ == "__main__":
    champ, chal, oos_chal, oos_def, champ_oos, adopted = daily_refine()
    print("DAILY AUTO-REFINE (walk-forward, OOS-gated)\n" + "-"*50)
    print(f"Default params {DEFAULT}  -> OOS Calmar {oos_def:.2f}")
    print(f"Best-on-train  {chal}  -> OOS Calmar {oos_chal:.2f}")
    print(f"Champion       {champ['params']} (since {champ['since']}) OOS Calmar {champ_oos:.2f}")
    print(f"Adopted challenger today? {adopted}")
    print("-"*50)
    # the honest benchmark: how does the CHAMPION compare to buy & hold OOS?
    from homily_backtest import buyhold
    print("\nChampion strategy vs Buy&Hold, OUT-OF-SAMPLE (last 40% of 5y):")
    print(f"{'NAME':<6}{'StratCAGR':>11}{'StratMDD':>10}{'B&H CAGR':>10}{'B&H MDD':>9}")
    for tk, closes in BT.items():
        cut = int(len(closes)*0.6); test = closes[cut:]
        s = run(test, champ["params"]); b = buyhold(test)
        print(f"{tk:<6}{s['cagr']*100:>10.1f}%{s['mdd']*100:>9.0f}%"
              f"{b['cagr']*100:>9.1f}%{b['mdd']*100:>8.0f}%")
