#!/usr/bin/env python3
"""
Realized-cost reconcile (#100 / D-100).
=======================================

Every levered comparison in this repo runs on TWO modeled costs: financing
at IBKR BM+1.5% (≈5.8%/yr, `gambit_live.FIN`) booked weekly on negative
cash, and fills at Monday's open / the trigger price. Reality drifts. This
module reconciles the model against an actual IBKR statement, monthly:

  * **Financing** — modeled interest vs the statement's actual interest on
    the loan → the TRUE effective rate. That rate is what LEVERAGE.md §5's
    yearly re-run should use, not the 5.8% assumption; a materially higher
    real rate shrinks the ladder faster.
  * **Fill slippage** — each journalled fill (the modeled price) matched to
    the statement's actual fill → adverse slippage per side. If the measured
    round-trip cost climbs past the 0.35% STRESS arm (the backtests' worst
    cost cell), the swing report prints it RED — the edge was priced to
    clear 0.35%, so exceeding it live is a real alarm.

Read-only + stdlib: it parses a committed statement file (populated by hand
today, by a Flex cash/trades query once #32's secrets are set) and the live
journal. No statement → the block is silent (non-fatal, never blocks the
send). This module writes nothing.
"""
import csv
import json
from pathlib import Path

_HERE = Path(__file__).resolve().parent
STATEMENT = _HERE / "ibkr_statement.json"
LIVE_JOURNAL = _HERE / "gambit_live_journal.csv"

MODELED_FIN = 0.058           # gambit_live.FIN — IBKR BM+1.5%
MODELED_SIDE = 0.00125        # gambit_live.COST — modeled cost per side
STRESS_RT = 0.0035            # gambit PRD §4 — the 0.35% round-trip stress arm


def load_statement(path=STATEMENT):
    """The committed IBKR statement (or None). Shape:
    {"period":{"from","to","days"},
     "financing":{"interest_usd","avg_loan_usd"},
     "trades":[{"date","sym","side","price"}...]}"""
    p = Path(path)
    if not p.exists():
        return None
    try:
        return json.loads(p.read_text())
    except Exception:
        return None


def read_journal(path=LIVE_JOURNAL):
    p = Path(path)
    if not p.exists():
        return []
    try:
        with p.open(newline="") as f:
            return list(csv.DictReader(f))
    except Exception:
        return []


def effective_rate(fin):
    """Statement financing block -> the actual annualized effective rate, or
    None when the loan/period is missing (can't annualize nothing)."""
    if not fin:
        return None
    loan = float(fin.get("avg_loan_usd") or 0.0)
    days = float((fin.get("days")) or 0.0)
    interest = float(fin.get("interest_usd") or 0.0)
    if loan <= 0 or days <= 0:
        return None
    return interest / loan * 365.0 / days


def _fills_from_journal(rows):
    """{(date, sym, side): modeled_price} from the live journal's fills."""
    out = {}
    for r in rows:
        side = (r.get("side") or "").strip()
        px = r.get("price")
        if side not in ("BUY", "SELL") or not px:
            continue
        try:
            out[(r.get("date", ""), (r.get("symbol") or "").strip(),
                 side)] = float(px)
        except ValueError:
            continue
    return out


def slippage(journal_rows, trades):
    """Match statement trades to journalled fills and measure ADVERSE
    slippage per side (a BUY filled higher, or a SELL filled lower, than
    modeled — both cost money). -> {"n","mean_side","p90_side","over_stress",
    "unmatched"}. Empty stats when nothing matches."""
    modeled = _fills_from_journal(journal_rows)
    adverse, unmatched = [], 0
    for t in trades or []:
        key = (str(t.get("date", "")), str(t.get("sym", "")).strip(),
               str(t.get("side", "")).strip())
        m = modeled.get(key)
        actual = t.get("price")
        if m is None or actual is None or m <= 0:
            unmatched += 1
            continue
        actual = float(actual)
        # adverse = you paid more (BUY) / received less (SELL) than modeled
        s = (actual - m) / m if key[2] == "BUY" else (m - actual) / m
        adverse.append(s)
    if not adverse:
        return {"n": 0, "mean_side": None, "p90_side": None,
                "over_stress": False, "unmatched": unmatched}
    adverse.sort()
    mean_side = sum(adverse) / len(adverse)
    p90 = adverse[min(len(adverse) - 1, int(round(0.9 * (len(adverse) - 1))))]
    # implied round-trip cost = modeled side cost + measured per-side adverse,
    # doubled; RED when it clears the 0.35% stress arm
    implied_rt = 2.0 * (MODELED_SIDE + max(0.0, mean_side))
    return {"n": len(adverse), "mean_side": mean_side, "p90_side": p90,
            "over_stress": implied_rt > STRESS_RT, "implied_rt": implied_rt,
            "unmatched": unmatched}


def reconcile(journal_rows, statement, modeled_fin=MODELED_FIN):
    """-> the reconcile dict, or None when there is no statement to read."""
    if not statement:
        return None
    fin = dict(statement.get("financing") or {},
               days=(statement.get("period") or {}).get("days"))
    rate = effective_rate(fin)
    return {"period": statement.get("period") or {},
            "fin_actual": rate, "fin_modeled": modeled_fin,
            "fin_delta": (rate - modeled_fin) if rate is not None else None,
            "slippage": slippage(journal_rows, statement.get("trades"))}


def reconcile_block(statement_path=STATEMENT, journal_path=LIVE_JOURNAL,
                    esc=lambda x: x):
    """The monthly reconcile section for the swing report, or "" when there
    is no statement yet. Deterministic function of the two files."""
    stmt = load_statement(statement_path)
    rec = reconcile(read_journal(journal_path), stmt)
    if not rec:
        return ""
    per = rec["period"]
    lines = ["♟️ <b>SWING cost reconcile (#100)</b> — model vs the IBKR "
             f"statement {esc(str(per.get('from', '')))}→"
             f"{esc(str(per.get('to', '')))}"]
    if rec["fin_actual"] is not None:
        d = rec["fin_delta"]
        lines.append(
            f"　financing: modeled {rec['fin_modeled']:.2%} vs actual "
            f"{rec['fin_actual']:.2%} ({d:+.2%}) — the actual rate feeds "
            "LEVERAGE.md §5's yearly re-run"
            + ("" if abs(d) < 0.005 else
               " ⚠️ material gap; a higher real rate shrinks the ladder faster"))
    else:
        lines.append("　financing: no loan/interest on the statement this "
                     "period")
    sl = rec["slippage"]
    if sl["n"]:
        red = " 🔴 OVER the 0.35% stress arm" if sl["over_stress"] else ""
        lines.append(
            f"　fills: {sl['n']} matched · adverse slippage mean "
            f"{sl['mean_side']:+.2%}/side (p90 {sl['p90_side']:+.2%}) · "
            f"implied {sl['implied_rt']:.2%} round trip{red}"
            + (f" · {sl['unmatched']} unmatched" if sl["unmatched"] else ""))
    else:
        lines.append("　fills: none matched to journalled orders yet")
    lines.append("<i>fills modeled at Monday opens / trigger prices — this is "
                 "the honest drift; populate ibkr_statement.json by hand or "
                 "via the #32 Flex query</i>")
    return "\n".join(lines)


if __name__ == "__main__":       # pragma: no cover — manual read
    print(reconcile_block() or "no ibkr_statement.json yet")
