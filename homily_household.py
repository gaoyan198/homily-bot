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
import math
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


#: off-IBKR sleeves that may be held as a QUANTITY and marked live.
#: key -> the symbol its price comes from. Adding a sleeve (ETHA, SOL-USD…)
#: is a one-line entry here plus the `<key>_qty` field in contributions.json
#: — deliberately data, not another branch in book_value (#128c: btc and
#: ibit had already grown one copy-pasted block each).
MARKED_SLEEVES = {"btc": "BTC-USD", "ibit": "IBIT"}


def _marked_value(bal, prices, key, symbol):
    """One off-IBKR sleeve -> (usd, live, qty, px).

    A configured `<key>_qty` priced from `symbol` wins; otherwise the typed
    `<key>_usd` is used. `live` is False for a typed value AND for a
    quantity whose price never arrived — the caller distinguishes those two
    (a dead feed deserves an alarm, a typed value only a note)."""
    qty = float(bal.get(f"{key}_qty") or 0.0)
    px = (prices or {}).get(symbol)
    if qty and px:
        return qty * px, True, qty, px
    return float(bal.get(f"{key}_usd") or 0.0), False, qty, 0.0


def book_value(positions, prices, live_book, balances, fx=None):
    """Assemble the whole-household composition (all USD).

    `fx` (#127, 2026-07-26): {currency: USD per 1 unit} for the non-USD
    holdings. Before this the sum skipped every non-USD position (R12) while
    `margin_loan_usd` stayed ONE lump covering non-USD borrowing too — so a
    book holding 9992.HK on HKD margin lost the asset and kept the loan, and
    the printed net worth ran ~US$10.3k light on the owner's real book. R12
    still governs the STOCK-BOOK PERCENTAGE (`core_gross` feeds no cap math
    here; homily_positions owns that and is untouched) — this fixes only the
    household NET-WORTH sum, which was never meant to be USD-only.
    A non-USD holding with no rate in `fx` is still skipped, but its ticker
    is returned in `unpriced` so the caller can say so out loud rather than
    silently under-reporting again.

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
    unpriced = []
    rates = fx or {}
    for tk, p in (positions or {}).items():
        cur = p.get("currency", "USD")
        rate = 1.0 if cur == "USD" else rates.get(cur)
        if rate is None:                   # no FX for it -> reported, not hidden
            unpriced.append(tk)
            continue
        px = prices.get(tk)
        if px is None:
            continue
        v = p["shares"] * px * rate
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
    # #128: off-IBKR crypto — like SRS and ESPP, outside the ladder. Broken
    # out in the FILE (different risk animals; it is the split the owner
    # tracks), summed for the printed line. Never enters ibkr_gross /
    # ibkr_loan: the LEVERAGE.md ladder governs the IBKR account and crypto
    # is not collateral there.
    #   btc_qty  — coins, MARKED LIVE from `prices["BTC-USD"]` when the
    #              caller supplies it (#128b). A quantity beats a typed
    #              value: it cannot go stale, which matters when this sleeve
    #              is ~half the book. Falls back to btc_usd when no price
    #              arrived (fetch failure), so a dead feed never silently
    #              zeroes half the net worth.
    #   ibit_usd — spot-BTC ETF held away from IBKR; typed value. Send
    #              ibit_qty instead and it can be marked live the same way.
    #   alt_usd  — the alt basket; typed, unpriceable without the coin list.
    sleeves, stale = {}, []
    for key, sym in MARKED_SLEEVES.items():
        usd, live, qty, px = _marked_value(bal, prices, key, sym)
        sleeves[key] = {"usd": usd, "live": live, "qty": qty, "px": px}
        # stale = a quantity WAS configured but no price arrived (fetch
        # died). A plain typed value is not stale, merely manual — different
        # conditions, and only the first deserves an alarm.
        if qty and not live:
            stale.append(key)
    alt = float(bal.get("alt_usd") or 0.0)
    crypto = sum(s["usd"] for s in sleeves.values()) + alt
    assets = core_gross + srs + espp + swing_mv + crypto
    loans = margin + swing_loan
    return {"core_gross": core_gross, "core_index": core_index,
            "srs": srs, "espp": espp, "swing_mv": swing_mv,
            "swing_eq": swing_eq, "swing_loan": swing_loan,
            "sleeves": sleeves, "alt": alt, "crypto": crypto,
            "crypto_stale": stale,
            # everything NOT marked from a live price — i.e. the part of the
            # book that goes wrong on its own if the owner forgets to update
            "crypto_manual": alt + sum(s["usd"] for s in sleeves.values()
                                       if not s["live"]),
            "margin": margin, "net": assets - loans,
            "ibkr_gross": core_gross + swing_mv, "ibkr_loan": loans,
            "unpriced": unpriced}


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


# --- #124 · PLAYBOOK §8.1 owner target line (re-cut 2026-07-24) ------------
# S$2M household by ~47, S$600k checkpoint at the 40th birthday (2032-07).
# History, kept so the re-cut is remembered as honesty and not drift: the
# target was first set as S$2M-by-2032, whose needed-DCA read S$18–21k/mo —
# beyond top-10% SG income, and the owner rightly called the monthly print
# demoralizing. A line that demands the impossible corrodes the routine
# (R0 damage), so the deadline became the OUTPUT: the line projects when
# S$2M arrives at the owner's ACTUAL logged pace, and the only demanded
# number is the checkpoint's — which is reachable. §8.1 is explicit that
# the target changes no investing rule, ever; nothing here feeds sizing.
TARGET_SGD = 2_000_000.0
CHECKPOINT_SGD = 600_000.0
CHECKPOINT_MONTH = "2032-07"       # the 40th birthday; refine if stated
TARGET_REF_RATES = (0.08, 0.12)    # sober reference CAGRs, monthly compounding


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


def months_to_target(target, book, monthly, annual_rate):
    """Closed-form months until `book` + level `monthly` contributions
    reach `target` at `annual_rate` (monthly compounding): the deadline as
    the OUTPUT. 0 when already there; None when the inputs can never
    arrive (no contributions and no growth, or nothing positive at all).
    Derivation: FV = (B + C/i)(1+i)^n − C/i  →  n = ln((T+C/i)/(B+C/i)) /
    ln(1+i); zero-rate degenerates to (T−B)/C."""
    if book >= target:
        return 0
    if annual_rate == 0.0:
        if monthly <= 0:
            return None
        return math.ceil((target - book) / monthly)
    i = annual_rate / 12.0
    base = book + monthly / i
    if base <= 0:
        return None
    ratio = (target + monthly / i) / base
    if ratio <= 1.0:
        return 0
    return math.ceil(math.log(ratio) / math.log(1.0 + i))


def _add_months(day, n):
    y, m = day.year, day.month + n
    return y + (m - 1) // 12


def target_line(net_usd, usdsgd, today, flows=None):
    """§8.1 target line (#124, re-cut): arrival-date projection at the
    owner's actual logged savings pace + the CHECKPOINT's needed DCA (the
    reachable number — the S$2M needed-DCA that read S$18–21k/mo is
    deliberately never printed again). SGD only ('' without FX — an SGD
    promise is never approximated in USD). With no logged pace the line
    still prints progress and asks for the flows instead of guessing."""
    if not usdsgd:
        return ""
    book = net_usd * usdsgd
    head = f"🎯 §8.1 S$2.0M by ~47: book S${book:,.0f} ({book / TARGET_SGD:.1%})"
    if book >= TARGET_SGD:
        return head + " — target reached; §8.1 retrospective is due"
    # Sum WITHIN each month before averaging. contributions.json documents a
    # per-sleeve `sleeve` tag, so one month legitimately carries several rows
    # (espp + core + srs); averaging rows instead of months divided the
    # owner's real rate by the number of sleeves he logged — S$4,250/mo read
    # as S$2,125 the first time this ran with tagged rows (#129).
    by_month = {}
    for f in (flows or []):
        m = f.get("month")
        if m:
            by_month[m] = by_month.get(m, 0.0) + float(f.get("usd", 0.0))
    logged = [by_month[m] for m in sorted(by_month)]
    avg = (sum(logged[-6:]) / len(logged[-6:]) * usdsgd) if logged else 0.0
    parts = [head]
    if avg > 0:
        arr = []
        for r in TARGET_REF_RATES:
            n = months_to_target(TARGET_SGD, book, avg, r)
            if n is not None:
                arr.append(f"{_add_months(today, n)} @{r:.0%}")
        pull = months_to_target(TARGET_SGD, book, avg + 1000.0,
                                TARGET_REF_RATES[0])
        base_n = months_to_target(TARGET_SGD, book, avg, TARGET_REF_RATES[0])
        parts.append(f"at ~S${avg:,.0f}/mo → S$2M ≈ "
                     + " / ".join(arr))
        if pull is not None and base_n is not None and base_n > pull:
            yrs = (base_n - pull) / 12.0
            parts.append(f"+S$1k/mo pulls it ≈ {yrs:.1f}y closer")
    else:
        parts.append("log your monthly flows (contributions.json) to "
                     "project the arrival date")
    # the checkpoint: the one number the line ASKS for, because it is real
    ck_months = len(months_between(today.strftime("%Y-%m"),
                                   CHECKPOINT_MONTH)) - 1
    if ck_months > 0:
        need = required_monthly(CHECKPOINT_SGD, book, ck_months,
                                TARGET_REF_RATES[0])
        if need == 0.0:
            parts.append("40-checkpoint S$600k: on pace")
        elif need is not None:
            parts.append(f"40-checkpoint S$600k (2032-07) needs ≈ "
                         f"S${need:,.0f}/mo @{TARGET_REF_RATES[0]:.0%}")
    return " · ".join(parts) + " — savings lever; changes no investing rule"


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
             + (f" · crypto {money(comp.get('crypto', 0.0))}"
                if comp.get("crypto") else "")
             + f" − margin {money(comp['margin'] + comp['swing_loan'])}"]
    # #128: a stale SRS balance drifts slowly; a stale crypto balance does
    # not. #128b: only the HAND-TYPED part can go stale — a live-marked
    # btc_qty must not be nagged about, or the warning trains you to ignore
    # it. Composition always prints when there is a sleeve.
    if comp.get("crypto"):
        bits = []
        for key, s in sorted((comp.get("sleeves") or {}).items()):
            if not s["usd"]:
                continue
            nm = key.upper()
            # .8g, not g: plain %g defaults to 6 significant digits and
            # would print 0.08558995 BTC as 0.0855899 — a WRONG quantity on
            # screen. .8g keeps satoshi-level holdings exact and still
            # renders a share count as "663", not "663.00000".
            bits.append(f"{nm} {s['qty']:.8g} @ {money(s['px'])} = "
                        f"{money(s['usd'])}" if s["live"]
                        else f"{nm} {money(s['usd'])} typed")
        if comp.get("alt"):
            bits.append(f"alt {money(comp['alt'])} typed")
        lines.append("　<i>crypto: " + " · ".join(bits) + "</i>")
        manual = comp.get("crypto_manual", comp["crypto"])
        if comp["net"] > 0 and manual / comp["net"] >= 0.20:
            lines.append(
                f"　<i>⚠ {manual / comp['net']:.0%} of net worth is "
                "hand-typed crypto — re-enter it with each month's flows, "
                "or send quantities and it gets marked live instead</i>")
        for key in comp.get("crypto_stale") or []:
            lines.append(f"　<i>⚠ {key.upper()} price fetch failed — using "
                         f"the typed {key}_usd; the figure may be well "
                         "off</i>")
    if comp.get("unpriced"):
        # #127: never under-report in silence — an unpriceable holding is
        # missing from `net` above while its borrowing is still subtracted.
        lines.append("　<i>⚠ no FX for "
                     + e(", ".join(sorted(comp["unpriced"])))
                     + " — excluded from net worth above, but any loan "
                     "against them IS subtracted: the figure is LOW</i>")

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
    # #127: every currency the book actually holds needs a USD rate, or the
    # net-worth sum silently drops the asset while keeping its loan. Yahoo
    # quotes "<CUR>=X" as CUR per USD, so the USD-per-unit rate is 1/that.
    need = {p.get("currency", "USD") for p in (positions or {}).values()}
    fxr = {"USD": 1.0}
    for cur in sorted(need - {"USD"}):
        m = _fetch_month_map(f"{cur}=X", fetch_series)
        if m:
            per_usd = m[max(m)]
            if per_usd:
                fxr[cur] = 1.0 / per_usd
    # #128b: mark btc_qty live. Merged into a COPY of prices so the caller's
    # dict (the digest's own closes) is never mutated.
    prices = dict(prices or {})
    for _k, _sym in MARKED_SLEEVES.items():
        if (balances or {}).get(f"{_k}_qty") and _sym not in prices:
            _m = _fetch_month_map(_sym, fetch_series)
            if _m:
                prices[_sym] = _m[max(_m)]
    comp = book_value(positions, prices, live, balances, fx=fxr)
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
