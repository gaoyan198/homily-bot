#!/usr/bin/env python3
"""
Crash-buying bot — the whole strategy, in one file.
===================================================

What it does (owner's rule, 2026-11-26):
  * Two index legs: S&P 500 (bought as CSPX) and Nasdaq-100 (bought as XNAS),
    split per crash_plan.json.
  * The monthly money WAITS in a cash pile (T-bill / money-market / IBKR
    interest-bearing cash — never 0%).
  * When an index closes 10%+ below its all-time high, its BUY ZONE opens:
    that leg's whole pile goes in that day, and every monthly amount is
    invested on arrival until the index closes at a new all-time high.
  * Never with borrowed money.

What it prints (one short Telegram message each weekday):
  🎯 deal meter  — how far each index is from its peak, zone ON/OFF
  💰 cash pile   — what should be waiting, per leg, if the sheet was followed
  🧾 debt        — countdown to debt-free (crash_plan.json "debt")
  🛒 buy sheet   — on the first weekday of the month, and on a trigger day

Honesty (crash_backtest.py, rules frozen before the run, 1999→2026,
dividends in): this rule is NOT an edge. Plain monthly buying beat it in
most 10-year windows (S&P 13/17, Nasdaq 14/17), but by little — S&P full
history $5.73 vs $5.79 per $1, worst decade −7% (2012–22); Nasdaq −0.3%.
The owner runs it for discipline and to stay out of stock-picking, which
cost far more. The meter uses SPY/QQQ dividend-adjusted closes (the
tested series), not the UCITS funds' own prices.

Stdlib only. No state files: everything is recomputed from price history
and crash_plan.json on every run.
"""
import datetime
import html
import json
import os
import time
import urllib.parse
import urllib.request

import thesis_check

HERE = os.path.dirname(os.path.abspath(__file__))
PLAN_FILE = os.path.join(HERE, "crash_plan.json")
ZONE = -0.10                      # buy zone opens at 10% below the peak
EPS = 1e-12                       # float slack: exactly -10.0% opens the zone
LEGS = (("SPY", "S&P 500", "CSPX"), ("QQQ", "Nasdaq-100", "XNAS"))
HOSTS = ("query1.finance.yahoo.com", "query2.finance.yahoo.com")


# ---------------------------------------------------------------- data ----
def fetch(symbol, tries=4, min_bars=500):
    """-> [(date, adj_close)] full daily history from Yahoo. Raises after
    `tries` failures (the message then says so — never a silent skip)."""
    last = None
    for attempt in range(tries):
        host = HOSTS[attempt % len(HOSTS)]
        url = (f"https://{host}/v8/finance/chart/{urllib.parse.quote(symbol)}"
               f"?period1=0&period2={int(time.time())}&interval=1d"
               "&events=div,split")
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
            with urllib.request.urlopen(req, timeout=30) as r:
                res = json.load(r)["chart"]["result"][0]
            ts = res["timestamp"]
            adj = res["indicators"]["adjclose"][0]["adjclose"]
            out = [(datetime.datetime.fromtimestamp(t, datetime.timezone.utc).date(), a)
                   for t, a in zip(ts, adj) if a is not None]
            if len(out) < min_bars:
                raise ValueError(f"{symbol}: only {len(out)} bars")
            return out
        except Exception as e:                    # noqa: BLE001 - retry
            last = e
            time.sleep(2 * (attempt + 1))
    raise RuntimeError(f"{symbol}: Yahoo failed {tries}x ({last})")


# --------------------------------------------------------------- logic ----
def meter(series, zone=ZONE):
    """Pure. -> dict for the LAST bar: dd (fraction), peak, peak_date,
    on (buy zone open), since (date the zone opened, or None), deepest dd
    of the current episode, trigger_today (zone opened on the last bar).
    Zone semantics = crash_backtest.py: opens on the first close at or
    below `zone` from the running all-time high; closes on a new high."""
    peak, peak_date = 0.0, None
    on, since, deepest = False, None, 0.0
    for d, p in series:
        if p >= peak:
            peak, peak_date = p, d
            on, since, deepest = False, None, 0.0
        dd = p / peak - 1
        deepest = min(deepest, dd)
        if not on and dd <= zone + EPS:
            on, since = True, d
    d, p = series[-1]
    return {"date": d, "price": p, "dd": p / peak - 1, "peak": peak,
            "peak_date": peak_date, "on": on, "since": since,
            "deepest": deepest, "trigger_today": on and since == d}


def zone_by_day(series, zone=ZONE):
    """Pure. -> {date: zone_open_bool} after each close (same rule as meter)."""
    peak, on, out = 0.0, False, {}
    for d, p in series:
        if p >= peak:
            peak, on = p, False
        if not on and p / peak - 1 <= zone + EPS:
            on = True
        out[d] = on
    return out


def pile(series, start, monthly_usd, zone=ZONE):
    """Pure. What one leg's cash pile SHOULD hold today if every sheet since
    `start` (a date) was followed: each first trading day of a month adds
    `monthly_usd` (invested instead while the zone is open); the day the
    zone opens, the whole pile is invested. -> {"pile", "invested",
    "contributed", "last_deploy": (date, usd) or None} in USD."""
    zones = zone_by_day(series, zone)
    cash = invested = contributed = 0.0
    last_deploy = None
    last_month, prev_on = None, None
    for d, _p in series:
        if d < start:
            prev_on = zones[d]
            continue
        on = zones[d]
        # zone state at the moment of the monthly buy = yesterday's close
        # (the bot runs before the US open on the previous close)
        ym = (d.year, d.month)
        if ym != last_month:
            last_month = ym
            contributed += monthly_usd
            if prev_on:
                invested += monthly_usd
            else:
                cash += monthly_usd
        if on and not prev_on and cash > 0:
            invested += cash
            last_deploy = (d, cash)
            cash = 0.0
        prev_on = on
    return {"pile": cash, "invested": invested, "contributed": contributed,
            "last_deploy": last_deploy}


def first_weekday_of_month(day):
    """True on the first Mon–Fri of the calendar month (the buy day)."""
    d = day.replace(day=1)
    while d.weekday() >= 5:
        d += datetime.timedelta(days=1)
    return day == d


def debt_line(debt, today):
    """-> one line for the debt countdown, from crash_plan.json "debt"."""
    target = datetime.date.fromisoformat(debt.get("target", "2026-12-31"))
    bal = debt.get("balance_sgd")
    days = (target - today).days
    if bal is None:
        return (f"🧾 <b>Debt:</b> {days} days to {target:%d %b} — set your "
                "balance in crash_plan.json to track it")
    if bal <= 0:
        return "🧾 <b>Debt: ZERO</b> 🎉 — monthly money now flows to the piles"
    weeks = max(days / 7, 1 / 7)
    asof = debt.get("as_of")
    return (f"🧾 <b>Debt:</b> S${bal:,.0f} left"
            + (f" (as of {asof})" if asof else "")
            + f" · {max(days, 0)} days to {target:%d %b} · "
            f"≈S${bal / weeks:,.0f}/week to make it")


# -------------------------------------------------------------- render ----
def render(today, legs, plan, sat_prices=None, scores=None):
    """Pure. `legs` = [(sym, name, fund, meter_dict, pile_dict|None)];
    `sat_prices` = {ticker: series|None} for the satellite thesis block."""
    e = lambda x: html.escape(str(x), quote=False)
    lines = [f"🎯 <b>CRASH METER — {today:%a %d %b %Y}</b>"]
    for sym, name, fund, m, _ in legs:
        dd = m["dd"] * 100
        bar = "🟩" if m["on"] else "⬜"
        state = (f"BUY ZONE ON since {m['since']:%d %b}"
                 if m["on"] else f"zone opens at −10% ({(m['dd'] - ZONE) * 100:.1f} pts away)")
        lines.append(f"{bar} <b>{e(name)}</b> {dd:+.1f}% from peak "
                     f"({m['peak_date']:%d %b %Y}) — {e(state)}")
    monthly = plan.get("monthly_usd")
    started = plan.get("start") and today >= datetime.date.fromisoformat(plan["start"])
    if monthly and started:
        tot = sum(p["pile"] for *_, p in legs if p)
        parts = " · ".join(f"{e(name)} ${p['pile']:,.0f}"
                           for _, name, _, _, p in legs if p)
        lines.append(f"💰 <b>Cash pile:</b> US${tot:,.0f} waiting ({parts}) "
                     "— keep it in interest-bearing cash, never 0%")
    elif monthly:
        lines.append(f"💰 <b>Cash pile:</b> starts {e(plan['start'])} "
                     f"(US${monthly:,.0f}/month)")
    else:
        lines.append("💰 <b>Cash pile:</b> set monthly_usd + start in "
                     "crash_plan.json")
    lines.append(debt_line(plan.get("debt") or {}, today))
    lines += satellite_block(plan.get("satellite") or {}, sat_prices or {},
                             scores=scores, today=today)

    # 🛒 sheet: trigger day (deploy the pile) and/or the monthly buy day
    # the deploy instruction repeats for a week after the zone opens, so one
    # missed run (or a weekend) can't swallow it
    sheet = []
    for sym, name, fund, m, p in legs:
        ld = p and p.get("last_deploy")
        if (started and m["on"] and ld and ld[0] == m["since"]
                and (today - m["since"]).days <= 7):
            sheet.append(f"🔔 {e(name)} hit −10% on {m['since']:%d %b}: BUY "
                         f"US${ld[1]:,.0f} {e(fund)} (the whole {e(name)} "
                         "pile) if you haven't yet")
    if monthly and started and first_weekday_of_month(today):
        for sym, name, fund, m, p in legs:
            amt = monthly * plan["split"][sym]
            sheet.append(f"BUY US${amt:,.0f} {e(fund)} ({e(name)} zone open)"
                         if m["on"] else
                         f"ADD US${amt:,.0f} to the {e(name)} cash pile (zone closed)")
    if sheet:
        lines += ["", "🛒 <b>TODAY</b>"] + [f"· {s}" for s in sheet]
    lines.append("<i>not an edge: tested ≈1% behind plain monthly buying "
                 "(worst decade −7%) — the price of the discipline. Never "
                 "with borrowed money.</i>")
    return "\n".join(lines)


def satellite_block(sats, prices, esc=lambda x: html.escape(str(x), quote=False),
                    scores=None, today=None):
    """Pure. The daily thesis reminder. `sats` = crash_plan.json "satellite"
    ({ticker: {name, thesis[], breaks_if[]}}); `prices` = {ticker: series or
    None}. Distance from peak is INFORMATION ONLY — no buy zone for single
    stocks: waiting for single-name dips lost to scheduled buying every time
    the old repo tested it (archive/BACKTEST_RESULTS §5f/§17/§30), and a
    single company, unlike the index, can fall and never come back."""
    if not sats:
        return []
    out = ["", "📌 <b>WHY YOU OWN THEM</b> — sell only if the thesis breaks, "
           "never because the price dropped"]
    for tk, c in sats.items():
        s = prices.get(tk)
        if s:
            peak = max(p for _, p in s)
            where = f"{(s[-1][1] / peak - 1) * 100:+.0f}% from its peak"
            if len(s) < 250:                  # under a year of history
                where += f" since listing ({s[0][0]:%d %b %Y})"
        else:
            where = "price unavailable today"
        out.append(f"<b>{esc(c.get('name', tk))}</b> ({esc(tk)}) · {esc(where)}")
        sl = thesis_check.line_for(tk, scores, today) if today else None
        if sl:
            out.append(sl)
        out += [f"  ✓ {esc(t)}" for t in c.get("thesis", [])]
        if c.get("bear_case"):
            out.append("  ⚠ <i>bear case: "
                       + esc(" · ".join(c["bear_case"])) + "</i>")
        if c.get("breaks_if"):
            out.append("  ✗ <i>would break if: "
                       + esc(" · ".join(c["breaks_if"])) + "</i>")
    return out


def load_plan(path=PLAN_FILE):
    with open(path) as f:
        return json.load(f)


def send(text):
    tok, chat = os.getenv("TELEGRAM_BOT_TOKEN"), os.getenv("TELEGRAM_CHAT_ID")
    if not (tok and chat):
        print(text)
        print("\n[no TELEGRAM_* env — printed only]")
        return
    url = f"https://api.telegram.org/bot{tok}/sendMessage"
    body = urllib.parse.urlencode({"chat_id": chat, "text": text,
                                   "parse_mode": "HTML"}).encode()
    urllib.request.urlopen(urllib.request.Request(url, data=body), timeout=20)
    print("[sent to Telegram]")


def main(today=None):
    today = today or (datetime.datetime.now(datetime.timezone.utc)
                      + datetime.timedelta(hours=8)).date()   # SGT
    plan = load_plan()
    legs, errors = [], []
    start = (datetime.date.fromisoformat(plan["start"])
             if plan.get("start") else None)
    for sym, name, fund in LEGS:
        try:
            s = fetch(sym)
        except Exception as e:                    # noqa: BLE001
            errors.append(str(e))
            continue
        p = (pile(s, start, plan["monthly_usd"] * plan["split"][sym])
             if plan.get("monthly_usd") and start else None)
        legs.append((sym, name, fund, meter(s), p))
    # satellite prices are context only: a failed fetch prints "price
    # unavailable" on that name and never blocks the message
    sat_prices = {}
    for tk, c in (plan.get("satellite") or {}).items():
        try:
            sat_prices[tk] = fetch(c.get("yahoo", tk), tries=2, min_bars=1)
        except Exception:                         # noqa: BLE001
            sat_prices[tk] = None
    if errors:
        msg = ("⚠️ <b>CRASH METER FAILED TODAY</b> — price data unavailable: "
               + html.escape("; ".join(errors), quote=False)
               + "\nCheck the S&P/Nasdaq yourself before any buy.")
        if legs:
            msg += "\n\n" + render(today, legs, plan, sat_prices,
                                     thesis_check.load_scores())
        send(msg)
        raise SystemExit(1)
    send(render(today, legs, plan, sat_prices, thesis_check.load_scores()))


if __name__ == "__main__":
    main()
