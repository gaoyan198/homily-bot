#!/usr/bin/env python3
"""
#171 the live scorecard — BOT vs OWNER vs QQQ on the same dated dollars
=======================================================================

PRD §9.0 makes live excess return vs QQQ-DCA the system's single success
metric; #14 (the scorecard that measures it) was due ~2026-10 and never
built (§5r Finding F). This is that referee, cut at BOOK level because the
§5r question is two questions, and they need different books:

  * does the SYSTEM have alpha?     BOT  − QQQ
  * is the BEHAVIOUR gap + or −?    OWNER − BOT

Books, all since INCEPTION (2026-07-10, the bot's first live ledger day),
all marked at the latest close, all USD:

  BOT      every buy-day sheet as printed (docs/orders_YYYY-MM.csv), filled
           at the OPEN of the first US session on/after that month's first
           ledger run (the buy day, D-31).
  OWNER    the actual IBKR fills (owner_fills.csv). Buys are deposits; sells
           are withdrawals to cash at 0%. A sell of shares bought BEFORE
           inception still counts — it is measured as a decision (proceeds
           vs keeping the shares to today), never as a P&L on an unknown
           basis.
  NO-SELL  (#176) the OWNER's buys only, every one held to today. OWNER −
           NO-SELL is the measured price (or prize) of trading in and out.
  QQQ      for each book, the same dollars on the same dates through QQQ
           (adjclose, #18), with sells mirrored as QQQ sells.

#180 labels every OWNER buy: ON-SHEET (named on that month's sheet),
OFF-SHEET, or NO-SHEET (no sheet was printed that month — never a breach); FENCED (in daily_run.OBSERVE on a date after the fence began,
2026-08-17); PAUSED (the #13 ledger, on or before the fill date, read the
name as monthly-not-up or ⚪ CAUTION). Leverage-at-fill is NOT
reconstructable before #169 (no dated loan history) and is reported as
such, not guessed.

Honesty (frozen, travels with every quote):
  (a) n is one crash quarter. The first read is DESCRIPTIVE — nothing is
      promoted or demoted on it (#71's band governs reads from ~2027-01).
  (b) Stocks are marked on raw closes (no dividends), QQQ on adjclose:
      the comparison is tilted slightly AGAINST the books.
  (c) Non-USD fills (HKD 9992) are excluded and counted, never converted
      at a guessed rate.
  (d) This is book-level. #14's original row-level spec (#71 noise band,
      #85 epoch split, #64 origin split over ledger rows) is a later read
      on the same ledger; it is not claimed here.
"""
import csv
import datetime
import glob
import os

HERE = os.path.dirname(os.path.abspath(__file__))
FILLS = os.path.join(HERE, "owner_fills.csv")
ORDERS_GLOB = os.path.join(HERE, "docs", "orders_*.csv")
LEDGER = os.path.join(HERE, "homily_signals_log.csv")
INCEPTION = datetime.date(2026, 7, 10)
FENCE_START = datetime.date(2026, 8, 17)


def _d(s):
    return datetime.date.fromisoformat(str(s)[:10])


# --- inputs ----------------------------------------------------------------

def load_fills(path=FILLS):
    with open(path) as fh:
        return [dict(r, date=_d(r["date"]), qty=float(r["qty"]),
                     price=float(r["price"])) for r in csv.DictReader(fh)]


def load_orders(pattern=ORDERS_GLOB):
    """-> {"YYYY-MM": [(symbol, qty)]} from the committed basket CSVs."""
    out = {}
    for path in sorted(glob.glob(pattern)):
        month = os.path.basename(path)[len("orders_"):-len(".csv")]
        with open(path) as fh:
            out[month] = [(r["Symbol"], float(r["Quantity"]))
                          for r in csv.DictReader(fh)
                          if r.get("Action", "").upper() == "BUY"]
    return out


def ledger_index(path=LEDGER):
    """-> ({month: first run date}, {ticker: [(date, monthly_up, state)]})."""
    first, rows = {}, {}
    with open(path) as fh:
        for r in csv.DictReader(fh):
            d = _d(r["date"])
            m = d.strftime("%Y-%m")
            first[m] = min(first.get(m, d), d)
            rows.setdefault(r["ticker"], []).append(
                (d, r.get("monthly_up") == "1", r.get("state", "")))
    for v in rows.values():
        v.sort()
    return first, rows


# --- pure core ---------------------------------------------------------------

def _on_or_after(bars, d):
    """bars: sorted [(date, open, close)] -> first bar dated >= d."""
    return next((b for b in bars if b[0] >= d), None)


def _close_at(bars, d):
    last = None
    for b in bars:
        if b[0] > d:
            break
        last = b[2]
    return last


def bot_events(orders, first_run, bars):
    """BOT fills: qty at the open of the first session >= the buy day."""
    ev = []
    for month, lines in sorted(orders.items()):
        day = first_run.get(month)
        if day is None:
            continue
        for sym, qty in lines:
            b = _on_or_after(bars.get(sym) or [], day)
            if b is not None:
                ev.append((b[0], sym, qty, b[1]))
    return ev


def owner_events(fills, *, buys_only=False):
    """-> ([(date, sym, signed qty, price)], excluded non-USD count)."""
    ev, skipped = [], 0
    for f in fills:
        if f["date"] < INCEPTION:
            continue
        if f.get("currency", "USD") != "USD":
            skipped += 1
            continue
        side = f["side"].upper()
        if buys_only and side != "BUY":
            continue
        q = f["qty"] if side == "BUY" else -f["qty"]
        ev.append((f["date"], f["symbol"], q, f["price"]))
    return ev, skipped


def book_path(events, bars, qqq, days):
    """Mark a book and its QQQ twin on `days`. Buys = deposits, sells =
    withdrawals to 0% cash, mirrored as QQQ sells of the same dollars.
    -> [(day, V, Q, deployed)]."""
    events = sorted(events)
    out, i = [], 0
    pos, cash, qunits, qcash, dep = {}, 0.0, 0.0, 0.0, 0.0
    for day in days:
        while i < len(events) and events[i][0] <= day:
            d, sym, q, px = events[i]
            qpx = _close_at(qqq, d)
            dollars = q * px
            pos[sym] = pos.get(sym, 0.0) + q
            if q > 0:
                dep += dollars
            else:
                cash += -dollars
                qcash += -dollars
            if qpx:
                qunits += dollars / qpx
            i += 1
        v = cash + sum(n * (_close_at(bars.get(s) or [], day) or 0.0)
                       for s, n in pos.items())
        qq = qcash + qunits * (_close_at(qqq, day) or 0.0)
        out.append((day, v, qq, dep))
    return out


def summarize(path):
    """-> {"deployed","value","qqq","gap","gap_pct","worst_rel"} at the end;
    worst_rel = worst drawdown of V/Q from its running peak."""
    if not path:
        return None
    _, v, q, dep = path[-1]
    peak, worst = None, 0.0
    for _, vv, qq, _ in path:
        if qq <= 0:
            continue
        r = vv / qq
        peak = r if peak is None else max(peak, r)
        worst = min(worst, r / peak - 1.0)
    return {"deployed": dep, "value": v, "qqq": q, "gap": v - q,
            "gap_pct": (v / q - 1.0) if q else 0.0, "worst_rel": worst}


def label_buys(fills, orders, ledger_rows, fenced):
    """#180: -> [(fill, {"on_sheet","fenced","paused"})] for USD buys."""
    sheet = {m: {s for s, _ in v} for m, v in orders.items()}
    out = []
    for f in fills:
        if f["side"].upper() != "BUY" or f["date"] < INCEPTION or \
                f.get("currency", "USD") != "USD":
            continue
        sym, d = f["symbol"], f["date"]
        prior = [r for r in ledger_rows.get(sym, []) if r[0] <= d]
        last = prior[-1] if prior else None
        month = d.strftime("%Y-%m")
        out.append((f, {
            # None = no sheet was printed that month (pre-copilot July):
            # neither on- nor off-sheet, and never counted as a breach
            "on_sheet": (sym in sheet[month]) if month in sheet else None,
            "fenced": sym in fenced and d >= FENCE_START,
            "paused": bool(last) and (not last[1] or last[2] == "CAUTION"),
        }))
    return out


def label_pnl(labelled, bars, qqq, today):
    """Group labelled buys: flagged (any rule) vs clean -> {grp: (n, $in,
    value now, QQQ same $)}."""
    out = {"flagged": [0, 0.0, 0.0, 0.0], "clean": [0, 0.0, 0.0, 0.0]}
    for f, lab in labelled:
        g = "flagged" if (lab["fenced"] or lab["paused"]
                          or lab["on_sheet"] is False) else "clean"
        px_now = _close_at(bars.get(f["symbol"]) or [], today)
        q0, q1 = _close_at(qqq, f["date"]), _close_at(qqq, today)
        if px_now is None or not q0:
            continue
        cost = f["qty"] * f["price"]
        o = out[g]
        o[0] += 1
        o[1] += cost
        o[2] += f["qty"] * px_now
        o[3] += cost * q1 / q0
    return out


# --- render -------------------------------------------------------------------

def _k(x):
    return f"US${x / 1000:,.1f}k"


def render(books, labels, skipped, labelled, today, esc=lambda x: x):
    lines = [f"📒 <b>SCORECARD since {INCEPTION} (#171)</b> — same dated "
             "dollars, marked "
             f"{today}; first read is descriptive, nothing moves on it"]
    names = {"BOT": "BOT sheets", "OWNER": "OWNER actual",
             "NO-SELL": "NO-SELL (#176)"}
    for key in ("BOT", "OWNER", "NO-SELL"):
        s = books.get(key)
        if not s or s["deployed"] <= 0:
            lines.append(f"{names[key]}: no fills")
            continue
        sign = "ahead of" if s["gap"] >= 0 else "behind"
        lines.append(
            f"{names[key]}: {_k(s['deployed'])} in → {_k(s['value'])} vs "
            f"QQQ {_k(s['qqq'])} → <b>{sign} QQQ by {_k(abs(s['gap']))}</b> "
            f"({s['gap_pct']:+.1%}) · worst slide vs QQQ "
            f"{s['worst_rel']:.0%}")
    o, n = books.get("OWNER"), books.get("NO-SELL")
    if o and n:
        diff = o["value"] - n["value"]
        lines.append(f"selling decisions {'ADDED' if diff >= 0 else 'COST'} "
                     f"{_k(abs(diff))} vs never selling (OWNER − NO-SELL)")
    fl, cl = labels["flagged"], labels["clean"]
    tot = len(labelled)
    on = sum(1 for _, lab in labelled if lab["on_sheet"] is True)
    off = sum(1 for _, lab in labelled if lab["on_sheet"] is False)
    fen = sum(1 for _, lab in labelled if lab["fenced"])
    pau = sum(1 for _, lab in labelled if lab["paused"])
    lines.append(f"rule check (#180): {tot} buys — {on} on-sheet · "
                 f"{off} off-sheet · {tot - on - off} in no-sheet months · "
                 f"{fen} 👁-fenced · {pau} paused")
    for g, v in (("flagged", fl), ("clean", cl)):
        if v[0]:
            lines.append(f"　{g} buys: {v[0]} · {_k(v[1])} in → "
                         f"{_k(v[2])} vs QQQ {_k(v[3])} "
                         f"({v[2] - v[3]:+,.0f} US$)")
    lines.append("　<i>leverage-at-fill not reconstructable before #169; "
                 f"{skipped} non-USD fill(s) excluded; stocks on raw closes, "
                 "QQQ on adjclose (tilts against the books)</i>")
    return "\n".join(lines)


# --- IO shell -------------------------------------------------------------------

def _bars(sym, yahoo, fetch_series, adj=False):
    b, a = fetch_series(yahoo.get(sym, sym), rng="2y")
    if adj:
        return [(x[0], x[1], c) for x, c in zip(b, a)]
    return [(x[0], x[1], x[4]) for x in b]


def build(yahoo, fenced, *, fetch_series=None, today=None):
    """-> (books, labels, skipped, labelled, today). Fetches each symbol
    once; a symbol that will not fetch is simply unmarked (value 0) and
    named in the CLI output."""
    if fetch_series is None:
        import homily_data
        fetch_series = homily_data.fetch_series
    fills = load_fills()
    orders = load_orders()
    first_run, lrows = ledger_index()
    syms = ({f["symbol"] for f in fills if f.get("currency", "USD") == "USD"}
            | {s for v in orders.values() for s, _ in v})
    bars, missing = {}, []
    for s in sorted(syms):
        try:
            bars[s] = _bars(s, yahoo, fetch_series)
        except Exception:                               # noqa: BLE001
            missing.append(s)
    qqq = _bars("QQQ", {}, fetch_series, adj=True)
    today = today or qqq[-1][0]
    days = [b[0] for b in qqq if b[0] >= INCEPTION and b[0] <= today]
    ev_o, skipped = owner_events(fills)
    ev_n, _ = owner_events(fills, buys_only=True)
    books = {"BOT": summarize(book_path(bot_events(orders, first_run, bars),
                                        bars, qqq, days)),
             "OWNER": summarize(book_path(ev_o, bars, qqq, days)),
             "NO-SELL": summarize(book_path(ev_n, bars, qqq, days))}
    labelled = label_buys(fills, orders, lrows, fenced)
    labels = label_pnl(labelled, bars, qqq, today)
    build.missing = missing
    build.fills_through = max((f["date"] for f in fills), default=None)
    return books, labels, skipped, labelled, today


def block(yahoo, fenced, today, *, esc=lambda x: x, fetch_series=None):
    """daily_run's monthly entry (first Monday): rendered block or ""."""
    books, labels, skipped, labelled, asof = build(
        yahoo, fenced, fetch_series=fetch_series)
    out = render(books, labels, skipped, labelled, asof, esc=esc)
    ft = getattr(build, "fills_through", None)
    if ft and (asof - ft).days > 7:
        # owner_fills.csv has no automatic source yet (the Flex query has no
        # Trades section) — a stale file must say so, not look current
        out += (f"\n　⚠️ <i>owner fills only through {ft} — re-export "
                "them, or add a Trades section to the Flex query</i>")
    return out


if __name__ == "__main__":
    import daily_run
    y = {**daily_run.HOLDINGS, **daily_run.WATCH, **daily_run.UNIVERSE}
    books, labels, skipped, labelled, asof = build(y, daily_run.OBSERVE)
    print(render(books, labels, skipped, labelled, asof))
    if build.missing:
        print(f"[unmarked — no bars] {', '.join(build.missing)}")
