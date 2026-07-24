#!/usr/bin/env python3
"""
Household book — the whole-portfolio north-star scorecard (#94 / D-94).
======================================================================

§9.0's success metric — live excess vs a same-cash-flows QQQ DCA — is
measured only on the CASH sleeve (#14), because that is where signal skill
is isolatable. But the machine now runs four money surfaces: the core cash
sleeve, SRS (the index leg), ESPP (V at a 15% discount, partly off-IBKR),
and the levered swing sleeve. No artifact answers the OWNER's actual
question: is the whole thing compounding faster than the same dollars DCA'd
into QQQ — and, now that borrowed dollars are live, what is combined gross
exposure across books?

This module is that scorecard: a monthly (first-Monday, beside the #30
bear-readiness block) digest block. It is INFO-ONLY forever — it never
gates money, never places an order, and is not a replacement for #14
(which isolates signal skill). Where #14 asks "does the SIGNAL beat the
index", this asks "does the whole HOUSEHOLD beat the index on the same
cash flows".

The honest counterfactual (§9.0, at household scale): every net dollar the
owner contributed, DCA'd into QQQ at that month's ADJUSTED close instead
(dividends reinvested — #18/R1: raw bars price levels, adjusted closes
price returns), valued at the latest adjusted close. Compared against the
whole book's current value. Monthly granularity, stated on the page —
precision theater is worse than an honest coarse number, and rolling
trailing-window splits need a book-NAV history this repo does not yet
commit (recorded: they accrue from a later NAV series; this session ships
the since-inception money-weighted comparison, which is the right
money-weighted number anyway).

The flows no API can see — SRS balance, external ESPP shares, the margin
loan, and the monthly contribution amounts themselves — live in a
committed, owner-maintained `contributions.json`. A month with no row
prints a NAG, never a guessed flow (R3 spirit: never manufacture history).

Engines frozen (§0): this reads holdings.json, the committed swing live
book, and contributions.json; the only prices it needs are QQQ adjusted
closes for the counterfactual and one FX series (SGD=X) for the SGD view —
both fetched by the IO shell, never inside the pure render.
"""
import datetime
import html
import json
import os
from pathlib import Path

import homily_positions

HERE = Path(__file__).resolve().parent
CONTRIB_FILE = HERE / "contributions.json"
LIVE_BOOK = HERE / "gambit" / "gambit_live_book.json"

# LEVERAGE.md §1 ladder caps, by regime label — the household leverage line
# reports combined gross vs the cap the account is currently allowed.
LADDER_CAP = {"BULL": 1.30, "MIXED": 1.15, "BEAR": 1.00}


def first_monday(day):
    """Same cadence as the #30 bear-readiness block (calendar, not ledger:
    a missed monthly scorecard costs nothing, so R7-grade robustness isn't
    warranted, and run_date() is TZ-pinned anyway)."""
    return day.weekday() == 0 and day.day <= 7


def load_contributions(path=None):
    """contributions.json -> dict, or {} when absent/corrupt (the block then
    prints a one-line 'unmaintained' nag rather than a scorecard). `path`
    resolves at call time so CONTRIB_FILE stays overridable in tests."""
    try:
        raw = json.loads(Path(path or CONTRIB_FILE).read_text())
    except Exception:
        return {}
    return raw if raw.get("_v") == 1 else {}


def months_between(start, end):
    """Inclusive list of 'YYYY-MM' strings from start to end (both 'YYYY-MM').
    Used to find which months the flow log is MISSING (the nag)."""
    y, m = (int(x) for x in start.split("-"))
    ey, em = (int(x) for x in end.split("-"))
    out = []
    while (y, m) <= (ey, em):
        out.append(f"{y:04d}-{m:02d}")
        m += 1
        if m > 12:
            y, m = y + 1, 1
    return out


def monthly_adj(bars, adj):
    """(raw bars, adjusted closes) -> {'YYYY-MM': last adjusted close that
    month}. The counterfactual buys at each flow month's adjusted close, so
    dividends are reinvested exactly as a QQQ DCA would (#18)."""
    out = {}
    for (d, *_), a in zip(bars, adj):
        if a is None:
            continue
        out[d.strftime("%Y-%m")] = float(a)   # last obs of the month wins
    return out


def counterfactual(flows, qqq_by_month):
    """Same net contributions, DCA'd into QQQ at each month's adjusted close.

    -> {"value": today's worth of those QQQ shares, "shares", "deployed":
    net USD that found a QQQ price, "uncovered": [months with a flow but no
    price in range]}. A flow month older than the fetched QQQ range can't be
    priced — it is reported, never silently dropped (that would flatter the
    counterfactual by pretending money arrived later)."""
    if not qqq_by_month:
        return None
    latest = qqq_by_month[max(qqq_by_month)]
    shares = 0.0
    deployed = 0.0
    uncovered = []
    for f in flows:
        usd = float(f.get("usd", 0.0))
        if not usd:
            continue
        px = qqq_by_month.get(str(f.get("month", "")))
        if px is None:
            uncovered.append(str(f.get("month", "")))
            continue
        shares += usd / px
        deployed += usd
    return {"value": shares * latest, "shares": shares,
            "deployed": deployed, "uncovered": uncovered}


def book_value(positions, prices, live_book, balances):
    """Assemble the whole-household composition (all USD).

    Returns per-sleeve values + the combined-leverage inputs. The core stock
    book and index sleeve are priced from `prices` (the same raw closes the
    digest already shows, R1); the swing sleeve from its committed live book;
    SRS / external-ESPP / margin from owner-maintained `balances`.

      core_gross  — IBKR long market value (buckets A+B+C, USD only, R12)
      core_index  — the Bucket-A index sleeve within it (SRS's IBKR twin)
      srs         — SRS balance (owner field; ≈ index beta, its own account)
      espp        — external ESPP shares value (off-IBKR, owner field)
      swing_mv    — swing positions' market value (equity − cash)
      swing_eq    — swing equity (the live book's mark)
      swing_loan  — swing borrowed (−cash when cash < 0)
      margin      — core margin loan (owner field)
      net         — whole-book net worth = every asset − every loan
    """
    core_gross = 0.0
    core_index = 0.0
    for tk, p in (positions or {}).items():
        if p.get("currency", "USD") != "USD":
            continue                       # R12: no cross-currency in the sum
        px = prices.get(tk)
        if px is None:
            continue
        v = p["shares"] * px
        core_gross += v
        if p.get("bucket") == "A":
            core_index += v
    lb = live_book or {}
    swing_eq = float(lb.get("equity") or 0.0) if lb.get("armed") else 0.0
    swing_cash = float(lb.get("cash") or 0.0) if lb.get("armed") else 0.0
    swing_mv = max(0.0, swing_eq - swing_cash)      # cash<0 ⇒ borrowed
    swing_loan = max(0.0, -swing_cash)
    bal = balances or {}
    srs = float(bal.get("srs_usd") or 0.0)
    espp = float(bal.get("espp_external_usd") or 0.0)
    margin = float(bal.get("margin_loan_usd") or 0.0)
    assets = core_gross + srs + espp + swing_mv
    loans = margin + swing_loan
    return {"core_gross": core_gross, "core_index": core_index,
            "srs": srs, "espp": espp, "swing_mv": swing_mv,
            "swing_eq": swing_eq, "swing_loan": swing_loan,
            "margin": margin, "net": assets - loans,
            "ibkr_gross": core_gross + swing_mv, "ibkr_loan": loans}


def combined_leverage(comp):
    """LEVERAGE.md's account-gross number, for real, across both books:
    gross long market value / net liquidation value at IBKR (SRS/ESPP are
    separate accounts, excluded — the ladder governs IBKR gross). -> gross L
    (1.0 = unlevered) or None when there is no book yet."""
    gross = comp["ibkr_gross"]
    net = gross - comp["ibkr_loan"]
    if net <= 0:
        return None
    return gross / net


# --- #124 · PLAYBOOK §8.1 owner target line -------------------------------
# S$2M household net worth before the owner turns 40 in 2032, set
# 2026-07-24 and assigned BY THE OWNER to the savings lever ("it's a
# savings problem not a investing problem"). This line is progress
# instrumentation only — §8.1 is explicit that the target changes no
# investing rule, ever, and nothing here feeds sizing, budget or signals.
TARGET_SGD = 2_000_000.0
TARGET_MONTH = "2032-07"      # refine to the exact birthday month if stated
TARGET_REF_RATES = (0.08, 0.12)   # sober reference CAGRs, monthly compounding


def required_monthly(target, book, months, annual_rate):
    """Closed-form level monthly contribution that grows `book` to `target`
    over `months` at `annual_rate` (monthly compounding). 0.0 when the book
    alone compounds past the target; None when months <= 0. Pure math —
    the reference rate is an assumption and is printed as one, never a
    promise (PLAYBOOK §8 stands)."""
    if months <= 0:
        return None
    if annual_rate == 0.0:
        return max(0.0, (target - book) / months)
    i = annual_rate / 12.0
    growth = (1.0 + i) ** months
    gap = target - book * growth
    if gap <= 0:
        return 0.0
    return gap * i / (growth - 1.0)


def target_line(net_usd, usdsgd, today, flows=None):
    """§8.1 target progress + needed-DCA line (#124), in SGD (the target's
    own currency). '' when FX is unavailable (a USD approximation would
    misstate an SGD promise) or once the target month has passed (the §8.1
    retrospective is an owner conversation, not a digest line). The
    "vs logged" tail compares against the trailing average of the last ≤6
    logged flow months — the owner's actual savings rate, the one variable
    the target is assigned to."""
    if not usdsgd:
        return ""
    months = len(months_between(today.strftime("%Y-%m"), TARGET_MONTH)) - 1
    if months <= 0:
        return ""
    book = net_usd * usdsgd
    needs = []
    for r in TARGET_REF_RATES:
        c = required_monthly(TARGET_SGD, book, months, r)
        needs.append("on track" if c == 0.0
                     else f"S${c:,.0f}/mo @{r:.0%}")
    now = ""
    logged = [float(f.get("usd", 0.0)) for f in (flows or [])
              if f.get("month")]
    if logged:
        avg = sum(logged[-6:]) / len(logged[-6:]) * usdsgd
        if avg > 0:
            now = f" (vs ~S${avg:,.0f}/mo logged)"
    return (f"🎯 §8.1 target S$2.0M by {TARGET_MONTH}: book "
            f"S${book:,.0f} ({book / TARGET_SGD:.1%}) · needed DCA ≈ "
            + " · ".join(needs) + now
            + " — savings lever; changes no investing rule")


def render(comp, cf, contributed, lev, cap_label, usdsgd, nag, esc=None,
           target=""):
    """Pure assembly of the household block (Telegram-HTML safe, #34 R4).

    Every varying input is passed in, so the printed text is a deterministic
    function of its arguments — that is what makes the fixture check pin it.
    `cf` may be None (no QQQ prices this run); `nag` is the list of flow
    months missing from contributions.json (empty = fully maintained)."""
    e = esc or (lambda x: html.escape(str(x), quote=False))
    sgd = usdsgd or 0.0

    def money(u):
        s = f"US${u:,.0f}"
        return f"{s} (S${u * sgd:,.0f})" if sgd else s

    lines = ["🏦 <b>HOUSEHOLD BOOK</b> — whole-portfolio scorecard "
             "(monthly, info only; #14 stays the signal-skill referee)",
             f"net worth {money(comp['net'])} across "
             f"index+core {money(comp['core_gross'])} · SRS {money(comp['srs'])}"
             f" · ESPP {money(comp['espp'])} · swing {money(comp['swing_eq'])}"
             f" − margin {money(comp['margin'] + comp['swing_loan'])}"]

    if cf is not None and contributed:
        book_now = comp["net"]
        qqq_now = cf["value"]
        delta = book_now - qqq_now
        verdict = "ahead of" if delta >= 0 else "behind"
        lines.append(
            f"vs QQQ on the same US${contributed:,.0f} invested (opening "
            "balance + net flows since inception, both DCA'd into QQQ): "
            f"book {money(book_now)} · QQQ counterfactual "
            f"{money(qqq_now)} → <b>{verdict} by US${abs(delta):,.0f}</b> "
            f"({(book_now / qqq_now - 1.0) if qqq_now else 0.0:+.0%}), "
            "money-weighted")
        if cf["uncovered"]:
            lines.append("　<i>note: "
                         + e(", ".join(sorted(set(cf["uncovered"]))))
                         + " predate the fetched QQQ range — excluded from "
                         "the counterfactual (coarse by design)</i>")
    else:
        lines.append("<i>counterfactual unavailable — no contribution flows "
                     "logged yet (see contributions.json)</i>")

    if target:
        lines.append(target)          # #124 — pre-assembled, info-only

    if lev is not None:
        cap = LADDER_CAP.get(cap_label)
        over = cap is not None and lev > cap + 1e-9
        tail = (f" — ladder cap {cap:.2f}× ({e(cap_label)})"
                if cap is not None else "")
        flag = " ⚠️ OVER LADDER CAP" if over else ""
        lines.append(f"combined IBKR gross {lev:.2f}×{tail}{flag} "
                     "(core + swing; SRS/ESPP are separate accounts)")

    if nag:
        lines.append("⏳ <b>contributions.json missing "
                     f"{len(nag)} month(s)</b>: " + e(", ".join(nag[:6]))
                     + (" …" if len(nag) > 6 else "")
                     + " — add the net flow (0 is a valid month) so the "
                     "counterfactual stays honest; a guessed flow is worse "
                     "than a gap")
    return "\n".join(lines)


def _fetch_month_map(symbol, fetch_series):
    try:
        bars, adj = fetch_series(symbol, rng="5y")
        return monthly_adj(bars, adj)
    except Exception:
        return {}


def household_block(positions, prices, today, *, regime_label="",
                    fetch_series=None, esc=None):
    """IO shell for daily_run: first-Monday check, load the owner's flows,
    fetch the QQQ counterfactual + FX, render. Empty string on any other day
    or an unmaintained book. Non-fatal by construction (the caller wraps it,
    like every block downstream of the digest).

    `regime_label` (BULL/MIXED/BEAR) picks which LEVERAGE.md ladder cap the
    combined-gross line is measured against — passed in from the regime the
    digest already computed, never re-derived here."""
    if not first_monday(today):
        return ""
    contrib = load_contributions()
    if not contrib:
        return ("🏦 <i>HOUSEHOLD BOOK — contributions.json not maintained "
                "yet; add the monthly net flows to unlock the whole-book vs "
                "QQQ-DCA scorecard (#94)</i>")
    if fetch_series is None:
        import homily_data
        fetch_series = homily_data.fetch_series
    flows = contrib.get("flows") or []
    balances = contrib.get("balances") or {}
    live = None
    try:
        live = json.loads(LIVE_BOOK.read_text())
    except Exception:
        pass
    comp = book_value(positions, prices, live, balances)
    qqq = _fetch_month_map("QQQ", fetch_series)
    # The book already held money at `inception` that the monthly flow log
    # does NOT capture. A money-weighted comparison must seed that OPENING
    # balance into the QQQ counterfactual too — at the inception month's
    # price — or the headline flatters the book by every pre-existing dollar
    # (comparing a full net worth against only the new flows). Opening is
    # just a flow dated at inception; contributed basis = opening + Σflows.
    inception = str(contrib.get("inception") or "")
    opening = float(contrib.get("opening_usd") or 0.0)
    cf_flows = list(flows)
    if opening and inception:
        cf_flows = [{"month": inception, "usd": opening}] + cf_flows
    cf = counterfactual(cf_flows, qqq)
    contributed = opening + sum(float(f.get("usd", 0.0)) for f in flows)
    # FX: the "one FX series" (SGD=X ≈ USD/SGD); fall back to the owner field
    fx = _fetch_month_map("SGD=X", fetch_series)
    usdsgd = fx[max(fx)] if fx else float(contrib.get("usdsgd") or 0.0)
    # the nag: which months since inception have no flow row at all
    logged = {str(f.get("month", "")) for f in flows}
    nag = []
    if inception:
        nag = [m for m in months_between(inception, today.strftime("%Y-%m"))
               if m not in logged]
    lev = combined_leverage(comp)
    tgt = target_line(comp["net"], usdsgd, today, flows)
    return render(comp, cf, contributed, lev, regime_label, usdsgd, nag,
                  esc=esc, target=tgt)
