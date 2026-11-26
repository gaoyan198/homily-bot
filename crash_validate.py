#!/usr/bin/env python3
"""Offline self-test for crash_bot.py — runs before every send (no network)."""
import datetime
import json

import crash_bot as cb

D0 = datetime.date(2026, 1, 1)


def series(prices, start=D0):
    """Weekday-dated synthetic closes."""
    out, d = [], start
    for p in prices:
        while d.weekday() >= 5:
            d += datetime.timedelta(days=1)
        out.append((d, float(p)))
        d += datetime.timedelta(days=1)
    return out


# [1] meter: zone opens at the first close <= -10% from the peak, stays open
# through a partial rebound, closes only on a new all-time high
s = series([90, 100, 95, 91, 90, 89.9, 95])
m = cb.meter(s)
assert m["peak"] == 100 and abs(m["dd"] + 0.05) < 1e-9
assert m["on"] and m["since"] == s[4][0], m          # opened at 90 (exactly -10%)
assert not m["trigger_today"] and abs(m["deepest"] + 0.101) < 1e-9
assert cb.meter(s[:5])["trigger_today"], "zone opening on the last bar = trigger day"
assert not cb.meter(s[:6])["trigger_today"], "the day after is not a trigger day"
assert not cb.meter(series([100, 95, 90.01]))["on"], "-9.99% is not the zone"
assert cb.meter(series([100, 90]))["on"], "exactly -10% opens the zone"
m2 = cb.meter(series([100, 85, 99, 100.5, 95]))
assert not m2["on"] and m2["peak"] == 100.5, "a new high closes the zone"
print("[1] meter: -10% opens, rebound stays open, new high closes ....... PASS")

# [2] pile: off-zone months accumulate, the opening day deploys the whole
# pile, months inside the zone invest on arrival
prices = [100] * 25 + [101] * 22 + [102] * 20 + [89] * 22 + [95] * 21
s = series(prices)
z = cb.zone_by_day(s)
open_day = next(d for d, on in z.items() if on)
assert dict(s)[open_day] == 89
p = cb.pile(s, D0, 100.0)
months = len({(d.year, d.month) for d, _ in s})
assert p["contributed"] == 100.0 * months
assert p["last_deploy"][0] == open_day and p["last_deploy"][1] > 0
assert abs(p["pile"] + p["invested"] - p["contributed"]) < 1e-9, "money conserved"
assert p["pile"] == 0.0, "after the zone opened, every month is invested"
# before the start date nothing counts
assert cb.pile(s, s[-1][0] + datetime.timedelta(days=1), 100.0)["contributed"] == 0
# a quiet market only ever adds to the pile
q = cb.pile(series([100 + i * 0.1 for i in range(120)]), D0, 50.0)
assert q["invested"] == 0 and q["pile"] == q["contributed"] > 0
print("[2] pile: accrues off-zone, deploys on open, conserves money ...... PASS")

# [3] buy day = first Mon–Fri of the month (Aug 2026: 1st is a Saturday)
assert cb.first_weekday_of_month(datetime.date(2026, 8, 3))
assert not cb.first_weekday_of_month(datetime.date(2026, 8, 4))
assert cb.first_weekday_of_month(datetime.date(2026, 12, 1))
print("[3] buy day: first weekday of the month ........................... PASS")

# [4] debt countdown
t = datetime.date(2026, 11, 26)
assert "set your balance" in cb.debt_line({}, t)
assert "ZERO" in cb.debt_line({"balance_sgd": 0}, t)
l = cb.debt_line({"balance_sgd": 5000, "target": "2026-12-31"}, t)
assert "S$5,000 left" in l and "35 days" in l and "/week" in l, l
print("[4] debt countdown: unset / zero / per-week pace .................. PASS")

# [5] render: buy-day sheet follows the zone per leg; trigger instruction
# repeats for a week; honesty line always present; HTML-safe
plan = {"monthly_usd": 1000, "start": "2026-01-01",
        "split": {"SPY": 0.5, "QQQ": 0.5}, "debt": {"balance_sgd": 0}}
on = {"date": t, "dd": -0.12, "peak": 1, "peak_date": D0, "on": True,
      "since": datetime.date(2026, 11, 26), "deepest": -0.12, "trigger_today": False}
off = dict(on, dd=-0.03, on=False, since=None)
pl = {"pile": 0.0, "invested": 0, "contributed": 0,
      "last_deploy": (datetime.date(2026, 11, 26), 6000.0)}
pq = {"pile": 3000.0, "invested": 0, "contributed": 0, "last_deploy": None}
legs = [("SPY", "S&P 500", "CSPX", on, pl), ("QQQ", "Nasdaq-100", "XNAS", off, pq)]
r = cb.render(datetime.date(2026, 12, 1), legs, plan)
assert "BUY US$500 CSPX" in r and "ADD US$500 to the Nasdaq-100 cash pile" in r, r
assert "BUY US$6,000 CSPX" in r, "trigger deploy still shown within a week"
assert "S&amp;P 500" in r and "S&P 500" not in r.replace("S&amp;P", ""), "escaped"
assert "not an edge" in r and "borrowed money" in r
r2 = cb.render(datetime.date(2026, 12, 2), legs, plan)
assert "BUY US$500" not in r2, "monthly sheet only on the buy day"
r3 = cb.render(datetime.date(2026, 12, 10), legs, plan)
assert "US$6,000" not in r3, "deploy reminder expires after a week"
r4 = cb.render(t, legs, dict(plan, start="2027-01-01"))
assert "starts 2027-01-01" in r4 and "🛒" not in r4, "nothing to buy before start"
print("[5] render: per-leg sheet, week-long deploy reminder, escaped .... PASS")

# [6] satellite thesis block: every thesis + break line printed, price is
# info only (no zone, no order), a failed fetch never drops the thesis,
# short histories say "since listing", HTML-escaped
sats = {"AAA": {"name": "A & Co", "thesis": ["moat <wide>", "growth"],
                "bear_case": ["capex burn", "dilution"],
                "breaks_if": ["margins fall"]},
        "BBB": {"name": "Bee", "thesis": ["x"]}}
blk = "\n".join(cb.satellite_block(sats, {"AAA": series([100, 120, 90]),
                                          "BBB": None}))
assert "WHY YOU OWN THEM" in blk and "A &amp; Co" in blk and "moat &lt;wide&gt;" in blk
assert "✓ growth" in blk and "would break if: margins fall" in blk
assert "⚠ <i>bear case: capex burn · dilution</i>" in blk
assert blk.index("bear case") < blk.index("would break if"), "bear case before the sell rule"
assert "-25% from its peak since listing" in blk, blk
assert "Bee</b> (BBB) · price unavailable today" in blk and "✓ x" in blk
assert "BUY" not in blk and "zone" not in blk.lower(), "single stocks get no buy zone"
assert cb.satellite_block({}, {}) == []
full = cb.render(datetime.date(2026, 12, 2), legs, dict(plan, satellite=sats),
                 {"AAA": series([100, 120, 90])})
assert "WHY YOU OWN THEM" in full and full.index("WHY YOU OWN") < full.index("not an edge")
print("[6] satellite thesis: printed daily, info-only price, fail-soft ... PASS")

# [7] thesis check: the CODE computes bull/bear scores and the verdict from
# per-line judgments; --verify refuses rewritten/missing lines, bad
# statuses, no source; a met sell condition forces 🚨 SELL; stale says so
import thesis_check as tc
pl7 = {"satellite": {"AAA": {"thesis": ["t1", "t2"], "bear_case": ["r1", "r2"],
                             "breaks_if": ["b1"]}}}
def _row(line, **kw):
    return dict(line=line, evidence="e", source="https://x.test", **kw)
def _doc(t=("holding", "holding"), r=("not_happening", "partly"), trig=False):
    return {"checked": "2026-12-01", "stocks": {"AAA": {
        "thesis": [_row("t1", status=t[0]), _row("t2", status=t[1])],
        "bear": [_row("r1", status=r[0]), _row("r2", status=r[1])],
        "breaks": [_row("b1", triggered=trig)], "summary": "fine <ok>"}}}
ok7 = _doc()
assert tc.verify(ok7, pl7) == [], tc.verify(ok7, pl7)
s7 = tc.score(ok7["stocks"]["AAA"])
assert (s7["bull"], s7["bear"], s7["met"]) == (10, 2, []) and "🟢 HOLD" in s7["verdict"]
assert "WATCH" in tc.score(_doc(t=("holding", "weakening"))["stocks"]["AAA"])["verdict"]
assert "CONSIDER SELLING" in tc.score(_doc(t=("mixed", "weakening"))["stocks"]["AAA"])["verdict"], "bull 3"
assert "CONSIDER SELLING" in tc.score(_doc(r=("happening", "partly"))["stocks"]["AAA"])["verdict"], "bear 8"
assert "🚨 SELL" in tc.score(_doc(trig=True)["stocks"]["AAA"])["verdict"], \
    "a met sell condition overrides even a perfect bull score"
bad = _doc(); bad["stocks"]["AAA"]["thesis"][0]["line"] = "t1 (reworded)"
assert any("exactly" in p for p in tc.verify(bad, pl7)), "rewritten line refused"
bad = _doc(); bad["stocks"]["AAA"]["bear"] = bad["stocks"]["AAA"]["bear"][:1]
assert any("bear" in p for p in tc.verify(bad, pl7)), "every bear line judged"
bad = _doc(); bad["stocks"]["AAA"]["bear"][0]["status"] = "holding"
assert any("bear status" in p for p in tc.verify(bad, pl7))
bad = _doc(); bad["stocks"]["AAA"]["breaks"][0]["source"] = ""
assert any("source" in p for p in tc.verify(bad, pl7))
d7 = datetime.date(2026, 12, 2)
l7 = tc.line_for("AAA", ok7, d7)
assert "🟢 HOLD" in l7 and "bull 10/10 · bear 2/10" in l7 and "why: fine &lt;ok&gt;" in l7
assert "STALE" in tc.line_for("AAA", ok7, datetime.date(2027, 2, 1))
assert "sell condition met: b1" in tc.line_for("AAA", _doc(trig=True), d7)
assert tc.line_for("ZZZ", ok7, d7) is None and tc.line_for("AAA", None, d7) is None
blk7 = "\n".join(cb.satellite_block({"AAA": {"name": "A", "thesis": ["t1"]}},
                                    {}, scores=ok7, today=d7))
assert "🟢 HOLD" in blk7
print("[7] thesis check: bull+bear scored in code, verdict rules, strict verify  PASS")

print("\nAll crash_bot checks passed.")
