#!/usr/bin/env python3
"""
Bear-readiness line (backlog #30) — the §4 rehearsal, monthly.
==============================================================

On the first Monday of each month the digest carries a 🐻-READINESS block:
core% vs satellites%, margin-zero confirmation, the SRS-index check (PRD
§9.4 says this line should nag if the index leg isn't confirmed), and the
pre-computed sell list in EXACTLY PLAYBOOK §4 step-3 order — "if 🐻 fired
tomorrow you would sell: …". The bear playbook stays rehearsed instead of
theoretical; on the real 🐻 day nothing here is new.

§4 step 3, verbatim structure (R9 — no improvised variants):
  a. everything in ⚪ CAUTION with weak fundamentals (F:0–1) — all of it;
  b. everything else in ⚪ CAUTION — until satellites total ≤10% of book;
  c. keep any satellite still ⭐/🟢 (rare in a real bear) if you wish.
§4 never sells Bucket A or B. Step (b) doesn't fix an order, so this
module sells largest-first (fewest orders to reach the threshold) and the
book shrinks as positions leave it — both choices are presentation, the
rule itself is §4's.

Detection is plain calendar math (weekday 0, day ≤ 7 in SGT run-date
terms), unlike buy day's ledger-based rule: a missed reminder costs
nothing, so R7-grade robustness isn't warranted — and run_date() is
already TZ-pinned anyway.

Non-USD positions (9992.HK) can't join the USD % math (R12) but DO appear
in the sell list by state — the §4 rule is state-shaped, not
valuation-shaped. Info-only: this prints a rehearsal, it never sells.
Engines frozen (§0): reads state_of() dicts + holdings.json only.
"""
import os
import html

import homily_positions


def first_monday(day):
    return day.weekday() == 0 and day.day <= 7


def _fweak(ftag):
    """PLAYBOOK §4.3a 'weak fundamentals (F:0–1)'. F:— (no EDGAR data) is
    NOT weak — an unknown business isn't a failed check, and selling HK
    names first on missing US-filings data would be an improvised rule."""
    return ftag and ftag[:2] == "F:" and ftag[2] in "01"


def readiness(states, positions, prices=None):
    """Pure math: held-name state dicts + holdings -> the rehearsal plan.
    -> {"core_pct","sat_pct","idx_pct", "sell_all":[t...], "sell_until":[t...],
        "keep":[t...], "offbook":[t...], "book"} or None on an unsynced book."""
    if not positions:
        return None
    st = {s["ticker"]: s for s in states}
    prices = prices or {t: s["close"] for t, s in st.items()
                        if s.get("close") is not None}
    # USD stock book (B + C, per #27); Bucket A valued separately for core%
    book = homily_positions.stock_book_value(positions, prices)
    if book <= 0:
        return None
    val = {}
    idx_val = 0.0
    for tk, p in positions.items():
        px = prices.get(tk)
        if px is None or p.get("currency", "USD") != "USD":
            continue
        if p.get("bucket") == "A":
            idx_val += p["shares"] * px
        else:
            val[tk] = p["shares"] * px
    sats = {tk: v for tk, v in val.items()
            if positions[tk].get("bucket", "C") == "C"}
    sat_v = sum(sats.values())
    total = book + idx_val
    plan = {"book": book,
            "sat_pct": 100.0 * sat_v / book,
            "core_pct": 100.0 * (total - sat_v) / total,
            "idx_pct": 100.0 * idx_val / total,
            "sell_all": [], "sell_until": [], "keep": [], "offbook": []}

    caution = []
    for tk in sorted(sats, key=lambda t: -sats[t]):
        s = st.get(tk)
        if s is None:
            continue
        if s["state"] == "CAUTION":
            (plan["sell_all"] if _fweak(s.get("ftag"))
             else caution).append(tk)
        elif s["state"] in ("ACCUMULATE", "HOLD"):
            plan["keep"].append(tk)                 # §4.3c: may keep ⭐/🟢
    # §4.3b: remaining ⚪, largest first, until satellites ≤10% of the
    # (shrinking) stock book — proceeds leave the book at 🐻
    remaining_sat = sat_v - sum(sats[t] for t in plan["sell_all"])
    remaining_book = book - sum(sats[t] for t in plan["sell_all"])
    for tk in caution:
        if remaining_sat <= 0.10 * remaining_book:
            break
        plan["sell_until"].append(tk)
        remaining_sat -= sats[tk]
        remaining_book -= sats[tk]
    # non-USD satellites: in the list by state, outside the % math (R12)
    for tk, p in positions.items():
        s = st.get(tk)
        if (p.get("currency", "USD") != "USD" and s
                and p.get("bucket", "C") == "C" and s["state"] == "CAUTION"):
            plan["offbook"].append(
                tk + (" (F:0-1 -> a)" if _fweak(s.get("ftag")) else " (b)"))
    return plan


def render(plan, *, margin_zero, srs_covers):
    """Plan -> the digest block (Telegram-HTML safe, #34 R4)."""
    e = lambda x: html.escape(str(x), quote=False)
    j = lambda ts: ", ".join(e(t) for t in ts)
    b_pct = max(0.0, plan["core_pct"] - plan["idx_pct"])   # earned core (B)
    lines = ["🛡 <b>BEAR READINESS</b> — monthly §4 rehearsal (info only)",
             f"book: index sleeve {plan['idx_pct']:.0f}% · earned core (B) "
             f"{b_pct:.0f}% · satellites (C) {100 - plan['core_pct']:.0f}% "
             f"(= {plan['sat_pct']:.0f}% of the stock book §4 measures)"]
    if margin_zero:
        lines.append("margin: zero, confirmed (§6)")
    else:
        lines.append("⚠️ <b>margin loan outstanding</b> — §4 step 2 / §6: "
                     "clear it to ZERO before anything else; nothing in the "
                     "playbook works with a margin call in it")
    lines.append("index leg: SRS confirmed deployed"
                 if srs_covers else
                 "⚠️ index leg unconfirmed — check SRS cash is invested, "
                 "not idle (§9.4), then set SRS_COVERS_INDEX")
    steps = []
    if plan["sell_all"]:
        steps.append(f"a. ALL of {j(plan['sell_all'])} (⚪ + F:0-1)")
    if plan["sell_until"]:
        steps.append(f"b. then {j(plan['sell_until'])} until satellites "
                     "≤10% of book")
    if plan["keep"]:
        steps.append(f"c. {j(plan['keep'])} still ⭐/🟢 — keep if you wish")
    if plan["offbook"]:
        steps.append("non-USD, by state: " + j(plan["offbook"]))
    lines.append("if 🐻 fired tomorrow, in §4 order: "
                 + ("; ".join(steps) if steps
                    else "nothing to sell — no ⚪ satellites today")
                 + ". Bucket A/B never sold.")
    return "\n".join(lines)


def bearready_block(states, positions, day):
    """IO shell for daily_run: calendar check + env in, rendered block out
    (empty string on any other day or an unsynced book)."""
    if not first_monday(day):
        return ""
    held = [s for s in states if s.get("held")]
    plan = readiness(held, positions)
    if plan is None:
        return ""
    flag = lambda v: os.getenv(v, "").lower() in ("1", "true", "yes", "on")
    return render(plan, margin_zero=flag("MARGIN_ZERO"),
                  srs_covers=flag("SRS_COVERS_INDEX"))
