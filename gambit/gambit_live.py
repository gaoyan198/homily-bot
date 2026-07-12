#!/usr/bin/env python3
"""
GAMBIT LIVE overlay (#93, Amendment A5 — owner override of the P2 paper gate,
2026-07-12). The paper S1-pure book stays UNTOUCHED as the no-stops
counterfactual; this module runs the owner's LIVE variant beside it:

  * same names, same Fridays, same T+1 Monday-open fills as the paper book
    (decisions are MIRRORED from the committed paper state — this module
    never ranks, so the frozen engine stays frozen);
  * sized in real dollars under the LEVERAGE.md ladder (BULL 1.30× /
    MIXED 1.15× / BEAR 1.00× — and the paper arm's regime kill-switch
    already exits in a bear, so BEAR in practice = flat);
  * every position carries a STOP (−20%) and a TP (+40%, HALF off, once) —
    the owner's mandate. Recorded honestly: the stopped variant FAILED the
    Phase-1 backtest gate (KILL_MEMO: S1-stopped 0/3), so stops here are a
    bounded-loss control the owner chose, not an edge claim; the paper book
    is the counterfactual that measures what they cost.
  * ASSUMED fills: entries/rotations at Monday open, stops/TPs at their
    trigger prices (gap-throughs at the gapped open — modeled, not wished).
    The owner's real IBKR fills may drift a little; the monthly block says
    so every time it prints.

PRE-REGISTERED (frozen here; changes = a recorded amendment, PRD §8.5):
  BANKROLL first funding US$3,000 (~9% of net liq — top-ups allowed, cap
  10% of net liq, each recorded in the book's `contributed`);
  STOP −20% from entry · TP +40% for half, once · TIME stop 12 weeks ·
  stop/TP adjustments ONLY at 4-weekly re-ranks, by the owner, on the sheet;
  same-bar stop+TP ambiguity resolves to STOP on the full remainder (worst
  case); financing 5.8%/yr booked weekly on negative cash;
  KILL-A: marked equity ≤ 70% of contributed → liquidate everything,
  experiment DEAD, failure memo owed — no restart without a new gated
  design; KILL-B: expectancy ≤ 0 over the trailing 20 closed live trades →
  same. Killed is killed: this module refuses to trade after it.
  ARMING: the first live order sheet prints only once MARGIN_ZERO is set
  (the owner's clean-slate condition) — until then the block says waiting.
  Proceeds: the flywheel skim (#95 / D-95) banks realized profit to the DCA
  each quarter — see maybe_skim(); losses are the recorded cost of business.
"""
import datetime

import gambit_journal as gj

BANKROLL = 3000.0
STOP_PCT = 0.20
TP_PCT = 0.40
TIME_STOP_DAYS = 84                  # 12 weeks
KILL_EQUITY_FRAC = 0.70
KILL_EXPECTANCY_N = 20
LADDER = {"BULL": 1.30, "MIXED": 1.15, "BEAR": 1.00}
COST = 0.00125                       # per side, = gambit_backtest.COST_SIDE
FIN = 0.058                          # LEVERAGE.md financing, on negative cash
N = 5
SKIM_MONTHS = {1, 4, 7, 10}          # D-95: quarter-ends (first run of each)
SKIM_MIN = 1.0                       # don't bother the owner with cents


def new_book(capital=BANKROLL):
    return {"armed": None, "contributed": capital, "cash": capital,
            "positions": {}, "pending": [], "realized": [],
            "hwm": capital, "equity": capital, "last_decision": None,
            "last_processed": None, "killed": None,
            # #95 flywheel: cumulative profit banked to the DCA + the record
            # of each skim (never in `realized` — a skim is not a trade).
            "skimmed": 0.0, "skims": [], "last_skim_q": None}


def _iso(d):
    return d.isoformat() if isinstance(d, datetime.date) else d


def _date(s):
    return datetime.date.fromisoformat(s) if isinstance(s, str) else s


def _equity(book, series, d):
    eq = book["cash"]
    for sym, p in book["positions"].items():
        px = series[sym].close_at(d) if sym in series else None
        eq += p["qty"] * (px if px else p["entry"])
    return round(eq, 2)


def _gross(book, series, d):
    g = 0.0
    for sym, p in book["positions"].items():
        px = series[sym].close_at(d) if sym in series else None
        g += p["qty"] * (px if px else p["entry"])
    return g


def _exit(book, sym, frac, px, when, reason, rows):
    """Sell `frac` of the position at px; realize P&L against basis."""
    p = book["positions"][sym]
    qty = p["qty"] * frac
    basis = p["basis"] * frac
    proceeds = qty * px * (1 - COST)
    pnl = round(proceeds - basis, 2)
    book["cash"] += proceeds
    book["realized"].append({"date": _iso(when), "sym": sym,
                             "reason": reason, "pnl": pnl})
    rows.append({"date": _iso(when), "event": reason, "symbol": sym,
                 "side": "SELL", "qty": f"{qty:.6g}", "price": f"{px:.6g}",
                 "reason_code": reason, "notes": f"pnl {pnl:+.2f}"})
    if frac >= 1.0 - 1e-9:
        book["positions"].pop(sym)
    else:
        p["qty"] -= qty
        p["basis"] -= basis


def reconcile(book, series, upto, rows):
    """Walk daily bars since last_processed: stops, TPs, gap-throughs.
    Same-bar stop+TP → STOP on the full remainder (pre-registered)."""
    start = _date(book.get("last_processed") or "1900-01-01")
    for sym in list(book["positions"]):
        p, ser = book["positions"][sym], series.get(sym)
        if ser is None:
            continue
        for i, d in enumerate(ser.dates):
            if d <= start or d > upto or d <= _date(p["entry_date"]):
                continue
            if sym not in book["positions"]:
                break
            o, h, l = ser.bars[i][1], ser.bars[i][2], ser.bars[i][3]
            if l <= p["stop"]:
                _exit(book, sym, 1.0, min(o, p["stop"]), d, "STOP", rows)
                continue
            if not p.get("tp_taken") and h >= p["tp"]:
                p["tp_taken"] = True
                _exit(book, sym, 0.5, max(o, p["tp"]), d, "TP", rows)
    book["last_processed"] = _iso(upto)


def settle(book, series, cal, regime_label, as_of, rows):
    """Fill pending at the first session after last_decision (T+1 opens),
    sells first, buys sized to equity × ladder / N with margin room."""
    if not book["pending"] or book["last_decision"] is None:
        return
    last_dec = _date(book["last_decision"])
    fill = next((d for d in cal if d > last_dec), None)
    if fill is None or fill > as_of:
        return                                  # Monday hasn't printed yet
    for prop in [p for p in book["pending"] if p["side"] == "SELL"]:
        sym = prop["sym"]
        if sym not in book["positions"]:
            continue
        ser = series.get(sym)
        i = ser.idx_at(fill) if ser else None
        if i is None or ser.dates[i] != fill:
            continue
        _exit(book, sym, 1.0, ser.bars[i][1], fill, prop["reason"], rows)
    L = LADDER.get(regime_label, 1.0)
    eq = _equity(book, series, fill)
    target = eq * L / N
    for prop in [p for p in book["pending"] if p["side"] == "BUY"]:
        sym = prop["sym"]
        if sym in book["positions"] or regime_label == "BEAR" or \
                book.get("killed"):
            continue
        ser = series.get(sym)
        i = ser.idx_at(fill) if ser else None
        if i is None or ser.dates[i] != fill:
            continue
        px = ser.bars[i][1]
        room = L * eq - _gross(book, series, fill)
        dollars = min(target, max(0.0, room))
        if dollars <= 1.0 or px <= 0:
            continue
        qty = dollars * (1 - COST) / px
        book["cash"] -= dollars
        book["positions"][sym] = {
            "qty": qty, "entry": px, "entry_date": _iso(fill),
            "basis": dollars, "stop": round(px * (1 - STOP_PCT), 2),
            "tp": round(px * (1 + TP_PCT), 2), "tp_taken": False}
        rows.append({"date": _iso(fill), "event": "FILL", "symbol": sym,
                     "side": "BUY", "qty": f"{qty:.6g}", "price": f"{px:.6g}",
                     "stop": f"{px * (1 - STOP_PCT):.2f}",
                     "tp": f"{px * (1 + TP_PCT):.2f}",
                     "reason_code": prop["reason"], "regime": regime_label})
    book["pending"] = []


def decide(book, paper, regime_label, as_of, rows):
    """Mirror the paper book's Friday decision + live-only TIME stops.
    Never ranks; the paper state is the single source of names."""
    decision = paper.get("last_decision")
    if decision is None or book.get("last_decision") == decision:
        return
    pend = []
    for prop in paper.get("pending", []):
        if prop["side"] == "SELL" and prop["sym"] in book["positions"]:
            pend.append(dict(prop))
        elif prop["side"] == "BUY" and prop["sym"] not in book["positions"] \
                and not book.get("killed"):
            pend.append(dict(prop))
    for sym, p in book["positions"].items():
        if (_date(decision) - _date(p["entry_date"])).days >= TIME_STOP_DAYS \
                and not any(x["sym"] == sym and x["side"] == "SELL"
                            for x in pend):
            pend.append({"side": "SELL", "sym": sym, "reason": "TIME"})
    for prop in pend:
        rows.append({"date": decision, "event": "PROPOSE",
                     "symbol": prop["sym"], "side": prop["side"],
                     "reason_code": prop["reason"], "regime": regime_label})
    book["pending"] = pend
    book["last_decision"] = decision


def check_kill(book, series, as_of, rows):
    if book.get("killed"):
        return
    eq = _equity(book, series, as_of)
    reason = None
    if eq <= KILL_EQUITY_FRAC * book["contributed"]:
        reason = (f"KILL-A: equity {eq:.2f} <= "
                  f"{KILL_EQUITY_FRAC:.0%} of contributed "
                  f"{book['contributed']:.2f}")
    elif len(book["realized"]) >= KILL_EXPECTANCY_N:
        last = book["realized"][-KILL_EXPECTANCY_N:]
        if sum(r["pnl"] for r in last) <= 0:
            reason = (f"KILL-B: expectancy <= 0 over the trailing "
                      f"{KILL_EXPECTANCY_N} closed trades")
    if reason:
        book["killed"] = {"date": _iso(as_of), "reason": reason}
        book["pending"] = [{"side": "SELL", "sym": s, "reason": "KILL"}
                           for s in book["positions"]]
        rows.append({"date": _iso(as_of), "event": "REGIME", "symbol": "",
                     "side": "", "reason_code": "KILL", "notes": reason})


def _quarter(d):
    d = _date(d)
    return f"{d.year}-Q{(d.month - 1) // 3 + 1}"


def maybe_skim(book, qqq, as_of, rows):
    """#95 / D-95 — the flywheel skim: at the first weekly run of each
    quarter (Jan/Apr/Jul/Oct), bank realized profit to the monthly DCA.

    The bar for "profit not yet banked" is `equity − contributed`, NOT the
    weekly high-water mark (`book["hwm"]` tracks equity every week, so
    `equity − hwm` ≈ 0 and the skim would never fire). Contributed is the
    right floor precisely because a skim REDUCES equity by the banked amount:
    once 600 of profit is skimmed, equity drops from 3600 to 3000, so the
    same 600 can never be skimmed again — and genuinely NEW profit earned
    afterward (3000 → 3150) is correctly bankable as its own 150. This is
    D-95's "the HWM ratchets so the same profit is never skimmed twice",
    achieved by the equity drop itself; `skimmed` is a cumulative record for
    the report, never part of the bar (adding it would double-count — bar
    raised AND cash removed). A drawdown below contributed skims 0, and that
    is correct (G8: red quarters pay nothing, no borrowing to fake
    stability).

    Skims are CONSERVATIVE with respect to the pre-registered kills: the
    banked cash leaves the book, so equity moves TOWARD KILL-A, never away;
    and a skim is never appended to `realized`, so KILL-B's expectancy over
    the trailing 20 CLOSED TRADES is untouched. Pre-registered kill rules do
    not get softened by the sleeve's own successes — the money just leaves
    the casino. Returns the skimmed amount (0.0 if none)."""
    if not book.get("armed") or book.get("killed"):
        return 0.0
    book.setdefault("skims", [])                  # forward-compat: a book
    book.setdefault("skimmed", 0.0)               # committed pre-#95 lacks these
    q = _quarter(as_of)
    if _date(as_of).month not in SKIM_MONTHS or book.get("last_skim_q") == q:
        return 0.0
    book["last_skim_q"] = q                       # once per quarter, even if 0
    skimmable = book["equity"] - book["contributed"]   # profit not yet banked
    free_cash = max(0.0, book["cash"])            # can't skim tied-up money
    s = round(min(free_cash, max(0.0, skimmable)), 2)
    if s < SKIM_MIN:
        return 0.0
    book["cash"] = round(book["cash"] - s, 2)     # equity drops by exactly s
    book["equity"] = round(book["equity"] - s, 2)
    book["skimmed"] = round(book.get("skimmed", 0.0) + s, 2)
    qpx = qqq.close_at(as_of) if qqq else None     # for D-95's later QQQ arm
    book["skims"].append({"date": _iso(as_of), "usd": s, "quarter": q,
                          "qqq": round(qpx, 4) if qpx else None})
    rows.append({"date": _iso(as_of), "event": "SKIM", "symbol": "",
                 "side": "", "reason_code": "SKIM",
                 "notes": f"skim {s:+.2f} to BUY_BUDGET (cumulative "
                          f"{book['skimmed']:.2f}); contributed and realized "
                          "untouched"})
    return s


def live_step(book, paper, series, qqq, regime_label, as_of, *,
              margin_zero=False):
    """One weekly advance. Returns (order_sheet_text, journal_rows).
    Mutates `book` in place. Idempotent per Friday like the paper step."""
    rows = []
    if book.get("killed") and not book["positions"] and not book["pending"]:
        return (f"♟️ SWING LIVE — DEAD since {book['killed']['date']} "
                f"({book['killed']['reason']}). Failure memo owed; no "
                "restart without a new gated design."), rows
    if not book.get("armed"):
        if not margin_zero:
            return ("♟️ SWING LIVE — waiting for the clean slate: set "
                    "MARGIN_ZERO once the legacy loan is cleared; the first "
                    "order sheet prints the Saturday after."), rows
        book["armed"] = _iso(as_of)
        book["last_processed"] = _iso(as_of)
        book["last_decision"] = paper.get("last_decision")
        pend = [{"side": "BUY", "sym": s, "reason": "ARM"}
                for s in paper.get("positions", {})]
        pend += [dict(p) for p in paper.get("pending", [])
                 if p["side"] == "BUY"]
        book["pending"] = pend
        for prop in pend:
            rows.append({"date": _iso(as_of), "event": "PROPOSE",
                         "symbol": prop["sym"], "side": "BUY",
                         "reason_code": prop["reason"],
                         "regime": regime_label})
        return _sheet(book, series, regime_label, as_of), rows

    # weekly financing on borrowed cash (booked before anything trades)
    days = max(0, (as_of - _date(book["last_processed"])).days)
    if book["cash"] < 0 and days:
        book["cash"] -= -book["cash"] * FIN * days / 365.0

    settle(book, series, qqq.dates, regime_label, as_of, rows)
    reconcile(book, series, as_of, rows)
    decide(book, paper, regime_label, as_of, rows)
    check_kill(book, series, as_of, rows)
    book["equity"] = _equity(book, series, as_of)
    book["hwm"] = max(book.get("hwm", 0.0), book["equity"])
    # #95: bank the quarter's profit AFTER the kill check (a skim can only
    # move equity toward KILL-A, never away — done last, on the marked book)
    maybe_skim(book, qqq, as_of, rows)
    return _sheet(book, series, regime_label, as_of), rows


def _sheet(book, series, regime_label, as_of):
    """The owner's Monday order sheet + status (the 5-minute artifact)."""
    L = LADDER.get(regime_label, 1.0)
    eq = _equity(book, series, as_of)
    kill_line = KILL_EQUITY_FRAC * book["contributed"]
    real = round(sum(r["pnl"] for r in book["realized"]), 2)
    gross = _gross(book, series, as_of)
    lines = [f"♟️ SWING LIVE — order sheet for Monday after {_iso(as_of)}"]
    if book.get("killed"):
        lines.append(f"🚨 KILLED {book['killed']['date']} — "
                     f"{book['killed']['reason']}")
        lines.append("LIQUIDATE every line below at Monday's open, repay "
                     "the margin, done. This experiment is over.")
    if book["pending"]:
        eqL = eq * L / N
        for p in book["pending"]:
            if p["side"] == "BUY":
                ser = series.get(p["sym"])
                px = ser.close_at(as_of) if ser else None
                n = int(eqL // px) if px else 0
                if px and n:
                    lines.append(
                        f"  BUY {n} {p['sym']} market · GTC STOP {n} @ "
                        f"{px * (1 - STOP_PCT):.2f} · GTC LIMIT SELL "
                        f"{max(1, n // 2)} @ {px * (1 + TP_PCT):.2f} "
                        f"[{p['reason']}] (~ref {px:.2f}; sizes re-check "
                        "at Monday's open)")
                else:
                    lines.append(f"  BUY {p['sym']} — sized at Monday open "
                                 f"(≈${eqL:,.0f}) [{p['reason']}]")
            else:
                lines.append(f"  SELL ALL {p['sym']} market + cancel its "
                             f"GTC orders [{p['reason']}]")
    else:
        lines.append("  no orders this week — a quiet week is the system "
                     "working")
    # #95: a fresh skim this week → the owner sweeps it to the DCA
    if book.get("skims") and book["skims"][-1]["date"] == _iso(as_of):
        sk = book["skims"][-1]
        lines.append(f"  💧 SKIM ${sk['usd']:,.2f} → BUY_BUDGET this quarter "
                     f"({sk['quarter']}): move that cash to the monthly DCA; "
                     f"cumulative banked ${book.get('skimmed', 0.0):,.2f}")
    lines.append(f"status: equity ${eq:,.2f} · contributed "
                 f"${book['contributed']:,.2f} · KILL line ${kill_line:,.2f}"
                 f" · realized {real:+,.2f} · skimmed "
                 f"${book.get('skimmed', 0.0):,.2f} · gross "
                 f"{(gross / eq if eq else 0):.2f}× (cap {L:.2f} "
                 f"{regime_label}) · stops move only at re-ranks")
    return "\n".join(lines)
