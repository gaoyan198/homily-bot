#!/usr/bin/env python3
"""
Buy-day copilot (backlog #31) + T2 basket CSV (PRD §9.2).
=========================================================

On the first trading day each month the digest LEADS with a 🛒 BUY DAY
section: today's ⭐ list resolved into exact IBKR-ready order lines from
`BUY_BUDGET_USD` (an Actions repo *variable*, not a secret — it is a
number, not a credential). Info-only: it prints orders, never places
them; PRD §7 stands. T2 rides along in the same session (EXECUTION.md
§4): the identical orders are also written as an IBKR-importable basket
CSV, `docs/orders_YYYY-MM.csv`, committed by the workflow (R8).

Allocation (D-31, PLAYBOOK §3):
  budget → index leg (50%; 0% if `SRS_COVERS_INDEX` — PRD §9.4: the
  owner's SRS contributions ARE the index half; 100% on 🐻 per §4.6 or
  when there is no ⭐ per §3.5) → star leg split across the TOP-3 ⭐
  names by RS12 (holdings + discovery — #24 promoted 2026-07-12, owner
  override, promotions.json carries the basis + demotion rule; the
  F:2+-first tie-break retired with equal-split-max-5) → per name the
  post-buy value is capped at 10% of the post-deploy stock book (#27's
  CAP_PCT), overflow redistributed to the remaining stars → round DOWN
  to whole shares → leftover printed, rolls to next month.

R12: non-USD names never get an order line — no cross-currency budget
math until an FX line ships (#53). A non-USD ⭐ prints "manual: 9992.HK"
instead. (D-31 sketched HK board-lot rounding; EXECUTION.md R12 is the
later, stricter rule and wins.)

Buy-day detection is NOT calendar math (US holidays, SGT offset make
that fragile): buy day = first run of the month with **no prior ledger
rows that month** (D-31) — robust by construction and idempotent on
same-day re-runs, since today's own rows don't count as "prior". Needs
#13's ledger; an empty/missing ledger is conservatively NOT a buy day
(mirrors #15's first-ever-run silence).

Engines stay frozen (EXECUTION.md §0): this module only reads the
state_of() dicts the digest already computed, plus holdings.json prices.
"""
import os
import csv
import html
import datetime

import homily_ledger
import homily_positions

HERE = os.path.dirname(os.path.abspath(__file__))
DOCS = os.path.join(HERE, "docs")

INDEX_TICKER = "CSPX"        # the Bucket A sleeve (PLAYBOOK §1)
MAX_STARS = 3                # #24 promoted 2026-07-12: top-3 by RS12
                             # (was 5, equal-split; a FAIL on the registry's
                             # rolling demotion check restores max-5)
INDEX_FRAC = 0.5             # PLAYBOOK §3.3: half to index, half to stars
CAP_FRAC = homily_positions.CAP_PCT / 100.0   # one cap constant (D-27 interlock)


def is_buy_day(day, ledger_rows):
    """First run of the month = no ledger row this month dated BEFORE today.
    Today's own rows (a same-day re-run) don't count, so the answer is stable
    all day. Empty ledger -> False (conservative; the record accrues first)."""
    iso = day.isoformat()
    if not ledger_rows:
        return False
    return not any(r["date"][:7] == iso[:7] and r["date"] < iso
                   for r in ledger_rows)


def star_candidates(states, positions, yahoo):
    """Today's ⭐ set split into (usd, manual). `manual` = non-USD names the
    orders must exclude (R12): held names by their holdings.json currency,
    unheld discovery names by a suffixed Yahoo symbol (0700.HK, D05.SI —
    every USD name in the universe maps to a bare symbol). Sort order per
    PLAYBOOK §3.4 as promoted (#24, 2026-07-12): RS12 descending, ticker
    tie-break — the same ranking homily_ledger.rs12_ranks pins for the
    forward check."""
    usd, manual = [], []
    for s in states:
        if s["state"] != "ACCUMULATE":
            continue
        p = positions.get(s["ticker"])
        if p is not None:
            foreign = p.get("currency", "USD") != "USD"
        else:
            foreign = "." in yahoo.get(s["ticker"], s["ticker"])
        (manual if foreign else usd).append(s)
    usd.sort(key=lambda s: (-s.get("rs12", 0.0), s["ticker"]))
    return usd, manual


def _cap_split(pool, picks, prices, positions, book_value):
    """Equal-split `pool` dollars across picks, capping each name so its
    post-buy value stays ≤ CAP_FRAC of the post-deploy book (current stock
    book + the star leg being put to work), redistributing a capped name's
    overflow to the uncapped rest. -> {ticker: dollars} (0 = fully capped)."""
    denom = book_value + pool
    cap = {}
    for s in picks:
        held = positions.get(s["ticker"])
        cur = held["shares"] * prices[s["ticker"]] if held else 0.0
        cap[s["ticker"]] = max(0.0, CAP_FRAC * denom - cur)
    alloc, active, remaining = {}, [s["ticker"] for s in picks], pool
    while active:
        share = remaining / len(active)
        binding = [t for t in active if cap[t] < share]
        if not binding:
            for t in active:
                alloc[t] = share
            break
        for t in binding:
            alloc[t] = cap[t]
            remaining -= cap[t]
            active.remove(t)
    return alloc


def plan(budget, states, positions, regime_label, *, srs_covers_index=False,
         yahoo=None):
    """Pure allocation: budget + today's screened states -> the order plan.
    No env, no clock, no files — that's what check [27] fixtures exercise.
    -> {"orders": [(ticker, shares, price, note)], "manual": [...],
        "skipped": [...], "index_amt", "spent", "leftover", "mode"}"""
    yahoo = yahoo or {}
    prices = {s["ticker"]: s["close"] for s in states
              if s.get("close") is not None}
    book = homily_positions.stock_book_value(positions, prices)
    usd_stars, manual = star_candidates(states, positions, yahoo)
    picks = usd_stars[:MAX_STARS]

    if regime_label == "BEAR":
        mode, index_amt = "bear", budget          # PLAYBOOK §4.6
    elif not picks:
        mode, index_amt = "nostars", budget       # PLAYBOOK §3.5
    else:
        mode = "normal"
        index_amt = 0.0 if srs_covers_index else budget * INDEX_FRAC
    star_pool = budget - index_amt

    orders, skipped, spent = [], [], 0.0
    ipx = prices.get(INDEX_TICKER)
    if index_amt > 0:
        if ipx:
            n = int(index_amt // ipx)
            if n:
                orders.append((INDEX_TICKER, n, ipx, "Bucket A index leg"))
                spent += n * ipx
            else:
                skipped.append(f"{INDEX_TICKER}: index leg "
                               f"${index_amt:,.0f} < 1 share (~${ipx:,.0f})")
        else:
            skipped.append(f"{INDEX_TICKER}: no price today — put the "
                           f"${index_amt:,.0f} index leg in manually")

    alloc = (_cap_split(star_pool, picks, prices, positions, book)
             if star_pool > 0 and picks else {})
    for s in picks:
        tk, px = s["ticker"], prices[s["ticker"]]
        n = int(alloc.get(tk, 0.0) // px)
        if n:
            orders.append((tk, n, px, ""))
            spent += n * px
        elif alloc.get(tk, 0.0) <= 1e-9 and star_pool > 0:
            skipped.append(f"{tk}: at the 10% cap — no add")
        elif star_pool > 0:
            skipped.append(f"{tk}: allocation ${alloc[tk]:,.0f} "
                           f"< 1 share (~${px:,.0f})")
    return {"orders": orders, "manual": [s["ticker"] for s in manual],
            "skipped": skipped, "index_amt": index_amt, "budget": budget,
            "spent": spent, "leftover": budget - spent, "mode": mode,
            "srs_covers_index": srs_covers_index}


def render(p, day):
    """Plan -> the 🛒 HTML block the digest leads with. Telegram-HTML safe:
    every interpolated name is escaped (#34 R4)."""
    e = lambda x: html.escape(str(x), quote=False)
    month = day.strftime("%B %Y")
    lines = [f"🛒 <b>BUY DAY — {e(month)}</b> · budget ${p['budget']:,.0f}"]
    if p["mode"] == "bear":
        lines.append("<i>🐻 regime: entire budget → Bucket A "
                     "(PLAYBOOK §4.6 — buy the index through the bear)</i>")
    elif p["mode"] == "nostars":
        lines.append("<i>no ⭐ today → full amount to Bucket A (§3.5: cash "
                     "waiting for stars costs more than it saves)</i>")
    elif p["srs_covers_index"]:
        lines.append("<i>SRS covers the index leg (§9.4) — cash 100% to ⭐</i>")
    if p["orders"]:
        rows = [f"BUY {n:>3} {e(tk):<5} @ mkt (~${n * px:,.0f})"
                + (f"   ← {e(note)}" if note else "")
                for tk, n, px, note in p["orders"]]
        lines.append("<pre>" + "\n".join(rows) + "</pre>")
    for tk in p["manual"]:
        lines.append(f"manual: {e(tk)} (non-USD — orders stay USD-only, R12)")
    for s in p["skipped"]:
        lines.append(f"· {e(s)}")
    lines.append(f"deployed ~${p['spent']:,.0f} · leftover "
                 f"${p['leftover']:,.0f} rolls to next month")
    lines.append("<i>printed, never placed — §7 stands (PRD §9.2 T0/T2)</i>")
    return "\n".join(lines)


def write_basket(p, day, docs=DOCS):
    """T2: the same orders as an IBKR BasketTrader-importable CSV,
    docs/orders_YYYY-MM.csv. Idempotent (whole-file rewrite, one file per
    month); written only when there are order lines. USD only by
    construction (R12). -> path or None."""
    if not p["orders"]:
        return None
    path = os.path.join(docs, f"orders_{day.strftime('%Y-%m')}.csv")
    os.makedirs(docs, exist_ok=True)
    with open(path, "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["Action", "Quantity", "Symbol", "SecType", "Exchange",
                    "Currency", "TimeInForce", "OrderType"])
        for tk, n, _px, _note in p["orders"]:
            w.writerow(["BUY", n, tk, "STK", "SMART", "USD", "DAY", "MKT"])
    return path


def buyday_block(states, positions, regime, day, *, yahoo=None,
                 ledger=homily_ledger.LEDGER, docs=DOCS):
    """IO shell daily_run calls: env + ledger in -> (rendered block, plan).
    ("", None) on a non-buy-day or with no budget configured. The plan dict
    also lands in docs/snapshot.json (#75) — the machine-readable twin the
    T3 order routine will read. A regime of None (check unavailable) is
    treated as a normal buy day — §3 only reroutes on an explicit 🐻."""
    try:
        budget = float(os.getenv("BUY_BUDGET_USD", "") or 0)
    except ValueError:
        budget = 0.0
    if budget <= 0:
        return "", None
    if not is_buy_day(day, homily_ledger._read_rows(ledger)):
        return "", None
    srs = os.getenv("SRS_COVERS_INDEX", "").lower() in ("1", "true", "yes", "on")
    p = plan(budget, states, positions,
             regime.label if regime is not None else "MIXED",
             srs_covers_index=srs, yahoo=yahoo)
    write_basket(p, day, docs=docs)
    return render(p, day), p


if __name__ == "__main__":
    rows = homily_ledger._read_rows()
    today = homily_ledger.run_date()
    print(f"today {today} · buy day: {is_buy_day(today, rows)} · "
          f"BUY_BUDGET_USD={os.getenv('BUY_BUDGET_USD', '(unset)')} · "
          f"SRS_COVERS_INDEX={os.getenv('SRS_COVERS_INDEX', '(unset)')}")
