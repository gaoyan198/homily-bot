#!/usr/bin/env python3
"""
GAMBIT G-S5 — the paper simulator for the promoted arm S1-pure (Amendment A4).

Runs the SAME S1-pure semantics as the frozen backtest engine (gambit_arms,
mode='s1_pure'): rank the point-in-time-eligible universe by blended RS, hold
the top 5 equal-weight, re-rank every 4th Friday, rotate out names that leave
the top decile, and obey the D-63 regime kill-switch. S1-pure carries NO stop /
TP / time-stop (Amendment A4) — its only exits are ROTATE and REGIME.

The difference from the backtest is temporal, not logical: the backtest sweeps a
whole window at once; the paper loop advances a PERSISTED book one weekly
invocation at a time. Decisions are taken on the latest completed Friday; the
resulting proposals fill at the NEXT session's open (T+1, Amendment A2 auto-fill)
on the *following* invocation — so a fill is always modelled at a real open that
has printed, never at a price we wish we'd gotten (D-G3 honesty). Cash is clipped
to ≥ 0 (G7). Given the same bars and the same run dates, the sequence of journal
rows is bit-for-bit reproducible.
"""
import datetime

import gambit_arms as ga
import gambit_backtest as bt

N = ga.S1_N                       # hold the top 5 (matches the RANDOM-5 band)
COST = bt.COST_SIDE


# ------------------------------------------------------------- market views --

def rank(series, inds, d):
    """Point-in-time RS ranking at decision date d (mirrors gambit_arms.ranked):
    eligible + rankable names, sorted by −RS then symbol (deterministic ties)."""
    rows = []
    for sym, ser in series.items():
        if not ser.eligible_at(d):
            continue
        i = ser.idx_at(d)
        r = inds[sym].rs(i) if i is not None else None
        if r is not None:
            rows.append((sym, r))
    rows.sort(key=lambda x: (-x[1], x[0]))
    return rows


def decile_and_top(rows, n=N):
    decile = {s for s, _ in rows[:max(1, -(-len(rows) // 10))]}
    return decile, [s for s, _ in rows[:n]]


def _fridays_upto(cal, as_of):
    return ga.fridays([d for d in cal if d <= as_of])


def _open_on(ser, d):
    i = ser.idx_at(d)
    return ser.bars[i][1] if i is not None and ser.dates[i] == d else None


def _prev_session(cal, d):
    prev = None
    for x in cal:
        if x >= d:
            break
        prev = x
    return prev


def _iso(d):
    return d.isoformat() if isinstance(d, datetime.date) else d


def _date(s):
    return datetime.date.fromisoformat(s) if isinstance(s, str) else s


# ----------------------------------------------------------------- the step --

def weekly_step(state, series, inds, qqq, as_of):
    """Advance the persisted paper book by one weekly invocation.

    Returns (journal_rows, digest) and mutates `state` in place. Idempotent
    within a week: a second call at the same as_of settles nothing new and
    re-decides nothing (decision keyed to the Friday date)."""
    cal = qqq.dates
    regime = ga.Regime(qqq)
    frs = _fridays_upto(cal, as_of)
    rows = []
    if not frs:
        return rows, _digest(state, series, qqq, as_of, [], "NONE")
    decision = frs[-1]
    last_dec = _date(state.get("last_decision"))
    positions = state["positions"]

    # 1. settle last week's proposals at the fill session's open (T+1) --------
    if state["pending"] and last_dec is not None:
        fill_date = None
        for x in cal:
            if x > last_dec:
                fill_date = x
                break
        if fill_date is not None and fill_date <= as_of:
            rows += _settle(state, series, regime, fill_date, cal)
            state["pending"] = []

    # 2. decide on the latest Friday (once per Friday) ------------------------
    if decision != last_dec:
        bear, cap = regime.at(decision)
        ranked = rank(series, inds, decision)
        rs_of = dict(ranked)
        rank_of = {s: k + 1 for k, (s, _) in enumerate(ranked)}
        reg = "BEAR" if bear else "BULL"
        note = (f"top5={','.join(t for _, t in zip(range(N), (s for s, _ in ranked)))}"
                if ranked else "no eligible names")
        rows.append(_row("SCAN", regime=reg, notes=note,
                         equity_after=_equity(state, series, as_of), date=decision))

        pending = []
        if not ranked:
            rows.append(_row("SKIP", reason_code="NO_UNIVERSE", regime=reg,
                             date=decision))
        elif bear:
            for sym in list(positions):
                pending.append({"side": "SELL", "sym": sym, "reason": "REGIME"})
                rows.append(_row("PROPOSE", symbol=sym, side="SELL",
                                 reason_code="REGIME", regime=reg, date=decision,
                                 notes="regime kill-switch: liquidate at next open"))
            if not pending:
                rows.append(_row("SKIP", reason_code="REGIME_FLAT", regime=reg,
                                 date=decision, notes="bear regime, book already flat"))
        else:
            if state["rotation_anchor"] is None:
                state["rotation_anchor"] = _iso(decision)
            anchor = _date(state["rotation_anchor"])
            rotate = _is_rotation_friday(frs, anchor, decision) or (
                cap < 1.0 and len(positions) < N)          # ramp re-entry
            if rotate:
                decile, top = decile_and_top(ranked)
                for sym in list(positions):
                    if sym not in decile:
                        pending.append({"side": "SELL", "sym": sym,
                                        "reason": "ROTATE"})
                        rows.append(_row("PROPOSE", symbol=sym, side="SELL",
                                         reason_code="ROTATE", regime=reg,
                                         rank_rs=_fmt(rs_of.get(sym)), date=decision,
                                         notes=f"left top decile (rank "
                                               f"{rank_of.get(sym, '—')})"))
                staying = sum(1 for s in positions if s in decile)
                slots = N - staying
                for sym in top:
                    if slots <= 0:
                        break
                    if sym in positions:
                        continue
                    pending.append({"side": "BUY", "sym": sym, "reason": "ROTATE"})
                    rows.append(_row("PROPOSE", symbol=sym, side="BUY",
                                     reason_code="ROTATE", regime=reg,
                                     rank_rs=_fmt(rs_of.get(sym)), date=decision,
                                     notes=f"enter top-{N} (rank {rank_of.get(sym)})"
                                           + (f", regime cap {cap:.2f}" if cap < 1
                                              else "")))
                    slots -= 1
                if not pending:
                    rows.append(_row("SKIP", reason_code="NO_CHANGE", regime=reg,
                                     date=decision, notes="top-5 unchanged"))
            else:
                rows.append(_row("SKIP", reason_code="NO_ROTATION", regime=reg,
                                 date=decision,
                                 notes="not a rotation week — a quiet week is the "
                                       "system working (PRD §4.1)"))
        state["pending"] = pending
        state["last_decision"] = _iso(decision)

    # 3. mark to market + QQQ bar --------------------------------------------
    if state["qqq_shares"] is None:
        q = qqq.close_at(as_of)
        if q:
            state["qqq_shares"] = state["capital"] * (1 - COST) / q
    eq = _equity(state, series, as_of)
    state["hwm"] = max(state["hwm"], eq)
    state["as_of"] = _iso(as_of)
    return rows, _digest(state, series, qqq, as_of, rows,
                         "BEAR" if regime.at(decision)[0] else "BULL")


def _settle(state, series, regime, fill_date, cal):
    rows = []
    positions = state["positions"]
    prev = _prev_session(cal, fill_date)
    # sells first (free cash), then buys sized on prior-close equity
    for prop in [p for p in state["pending"] if p["side"] == "SELL"]:
        sym = prop["sym"]
        if sym not in positions:
            continue
        px = _open_on(series[sym], fill_date)
        if px is None:
            continue
        qty = positions[sym]["qty"]
        state["cash"] += qty * px * (1 - COST)
        state["closed_trades"] += 1
        positions.pop(sym)
        rows.append(_row("FILL", symbol=sym, side="SELL", qty=_fmt(qty),
                         price=_fmt(px), reason_code=prop["reason"],
                         equity_after=_equity(state, series, fill_date),
                         date=fill_date))
    bear, cap = regime.at(fill_date)
    eq_prev = _equity(state, series, prev) if prev else state["capital"]
    invested = eq_prev - state["cash"]
    target = eq_prev / N
    for prop in [p for p in state["pending"] if p["side"] == "BUY"]:
        sym = prop["sym"]
        if sym in positions or bear:
            continue
        px = _open_on(series[sym], fill_date)
        if px is None or px <= 0:
            continue
        dollars = min(target, state["cash"], max(0.0, cap * eq_prev - invested))
        if dollars <= 1.0:
            rows.append(_row("SKIP", symbol=sym, side="BUY", reason_code="CAP",
                             date=fill_date, notes="regime/cash cap left no room"))
            continue
        qty = dollars * (1 - COST) / px
        state["cash"] -= dollars
        invested += dollars
        positions[sym] = {"qty": qty, "entry": px, "entry_date": _iso(fill_date)}
        rows.append(_row("FILL", symbol=sym, side="BUY", qty=_fmt(qty),
                         price=_fmt(px), reason_code=prop["reason"],
                         equity_after=_equity(state, series, fill_date),
                         date=fill_date))
    return rows


def _is_rotation_friday(frs, anchor, decision):
    if anchor not in frs or decision not in frs:
        return decision == anchor
    return (frs.index(decision) - frs.index(anchor)) % 4 == 0


# --------------------------------------------------------------- accounting --

def _equity(state, series, d):
    eq = state["cash"]
    for sym, p in state["positions"].items():
        px = series[sym].close_at(d) if sym in series else None
        eq += p["qty"] * (px if px else p["entry"])
    return round(eq, 2)


def _qqq_value(state, qqq, d):
    if state["qqq_shares"] is None:
        return state["capital"]
    return round(state["qqq_shares"] * (qqq.close_at(d) or 0.0), 2)


# ----------------------------------------------------------------- row build --

def _fmt(x):
    return "" if x is None else f"{x:.8g}"


def _row(event, *, date, symbol="", side="", qty="", price="", stop="", tp="",
         r_distance="", reason_code="", rank_rs="", regime="", equity_after="",
         notes=""):
    return {"date": _iso(date), "event": event, "symbol": symbol, "side": side,
            "qty": qty, "price": price, "stop": stop, "tp": tp,
            "r_distance": r_distance, "reason_code": reason_code,
            "rank_rs": rank_rs, "regime": regime,
            "equity_after": _fmt(equity_after) if isinstance(equity_after, float)
            else equity_after, "notes": notes}


def _digest(state, series, qqq, as_of, rows, regime):
    eq = _equity(state, series, as_of)
    qv = _qqq_value(state, qqq, as_of)
    return {"as_of": _iso(as_of), "regime": regime, "equity": eq,
            "qqq_value": qv, "cash": round(state["cash"], 2),
            "hwm": round(state["hwm"], 2),
            "positions": dict(state["positions"]),
            "pending": list(state["pending"]), "events": rows}
