#!/usr/bin/env python3
"""
Daily entrypoint: fetch -> Danny-style composite signal -> auto-refine ->
Telegram digest. Pure stdlib (urllib). GitHub Actions cron (9am SGT = 01:00
UTC); champion state is committed back by the workflow.

Signal semantics follow @dannycheng2022's use of Homily charts (see PRD.md):
accumulate-on-dip guidance anchored on chip support — there is no SELL state.

Env: TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID (if unset -> prints digest, no send).
"""
import os, re, html, datetime, urllib.request, urllib.parse, urllib.error
from concurrent.futures import ThreadPoolExecutor
import homily_data
from homily_data import fetch_series
from homily_danny import danny_signal
from homily_conviction import conviction
from homily_fund import fund_tag
from homily_regime import market_regime
from homily_refine import daily_refine
from homily_corp import corp_action_bar, suspended_note
from homily_ribbon_backtest import RED_MEDIAN_RUN_W
from homily_ipo_backtest import REFS as IPO_REFS
from homily_pullback_backtest import dip_age, DIP_MEDIAN_D, DIP_P90_D
import homily_ledger
import homily_alerts
import homily_positions
import homily_buyday
import homily_promotions
import homily_bearready
import homily_png
import homily_dashboard
import homily_clusters
import homily_flex
import homily_provisional
import homily_breakout
import homily_quality
import homily_universe
import homily_swing
import homily_leverage
import homily_household
import homily_ops
import homily_bearish

# IBKR holding -> Yahoo symbol: lives in holdings.json (schema _v:2, #27) so
# book changes are a one-line edit (last synced from live IBKR positions
# 2026-07-10). POSITIONS carries the shares/cost/bucket #27 needs; HOLDINGS
# stays the flat ticker->yahoo map every screen()/membership check expects.
POSITIONS = homily_positions.load_positions()
HOLDINGS = {k: v["yahoo"] for k, v in POSITIONS.items()}
# Owner-requested names not (yet) held — charted anyway, week after week
WATCH = {"ASML":"ASML","ICE":"ICE","CDE":"CDE","QQQ":"QQQ"}

# Too-new listings whose real signal lives in their constituents: screen the
# members and print a proxy line under the holding's row (DRAM = Roundhill
# Memory ETF: the DRAM-cycle basket per its top weights).
PROXY_CONSTITUENTS = {
    "DRAM": {"MU": "MU", "HYNIX": "000660.KS", "SMSNG": "005930.KS",
             "SNDK": "SNDK", "WDC": "WDC", "STX": "STX"},
}

# Discovery universe: liquid names NOT held, screened for new-money setups.
# Only ⭐/🔵 states surface in the digest. Deliberately excluded: leveraged
# ETFs (SOXL, MSTR-style proxies) — out of scope per PRD; and anything
# already in HOLDINGS/WATCH. Crypto-beta spot ETFs (IBIT, ETHA) added
# 2026-07-09 — see PRD §5c.
UNIVERSE = {
    # megacap tech
    "MSFT":"MSFT","AMZN":"AMZN","META":"META","NFLX":"NFLX","ORCL":"ORCL",
    # semis / AI hardware
    "QCOM":"QCOM","ARM":"ARM","ANET":"ANET","VRT":"VRT",
    "LRCX":"LRCX","AMAT":"AMAT","KLAC":"KLAC","INTC":"INTC","MRVL":"MRVL",
    # software / growth
    "CRM":"CRM","ADBE":"ADBE","CRWD":"CRWD","PANW":"PANW","NET":"NET",
    "DDOG":"DDOG","SNOW":"SNOW","ZS":"ZS","APP":"APP","SHOP":"SHOP",
    "UBER":"UBER","HOOD":"HOOD","MDB":"MDB",
    # quality diversifiers
    "LLY":"LLY","NVO":"NVO","V":"V","MA":"MA","COST":"COST","JPM":"JPM",
    # HK/China liquid names beyond BABA
    "0700":"0700.HK","3690":"3690.HK","1810":"1810.HK",
    # SG liquid names
    "D05":"D05.SI",
    # crypto-beta spot ETFs
    "IBIT":"IBIT","ETHA":"ETHA",
    # growth mid-caps — the multi-bagger hunting ground
    "RKLB":"RKLB","ASTS":"ASTS","SOFI":"SOFI","HIMS":"HIMS","DUOL":"DUOL",
    "AXON":"AXON","TOST":"TOST","RBLX":"RBLX","IOT":"IOT","CRDO":"CRDO",
    "TMDX":"TMDX","CAVA":"CAVA","ONON":"ONON","SE":"SE","GRAB":"GRAB",
    "NBIS":"NBIS","ALAB":"ALAB",
}

# #64 universe-entry provenance: how each name got into the screen, logged
# per ledger row so #14's scorecard can split by it (the referee must not
# inherit the selection bias it exists to detect). The whole hand-picked
# WATCH/UNIVERSE list is honestly "owner-request" (PRD §5c/§5f); "screen"
# is reserved for #65's mechanical arrivals.
ORIGINS = {**{tk: "owner-request" for tk in {**WATCH, **UNIVERSE}},
           **{tk: "holding" for tk in HOLDINGS}}

ICON = {"ACCUMULATE":"⭐","HOLD":"🟢","PULLBACK":"🟡","BOTTOMING":"🔵",
        "CAUTION":"⚪"}
ORDER = {"ACCUMULATE":0,"HOLD":1,"PULLBACK":2,"BOTTOMING":3,"CAUTION":4}
VH_ARROW = {"BREAKOUT":"↑","BREAKDOWN":"↓","INSIDE":"◻"}


def digest_sort_key(sig, conv):
    """State groups in ORDER; ⭐ rows by RS12 descending inside their group
    (#24 promoted 2026-07-12 — the top-3 the buy-day splits across), every
    other state alphabetical as before."""
    rs = -conv.rs12 if sig.state == "ACCUMULATE" else 0.0
    return (ORDER[sig.state], rs, sig.ticker)


def g(x):
    return f"{round(x, 2):g}"


# --- #34 F0: Telegram HTML output. Every dynamic string that could carry a
# ticker/name/note is escaped (& < > -> entities) so the parse never breaks;
# the static <b>/<i>/<code> structural tags are the only real markup. send()
# keeps a plain-text fallback (strip_html) so a bad entity degrades, never
# drops the digest (R4).
def esc(x):
    return html.escape(str(x), quote=False)


def strip_html(s):
    """Tags out, entities back to text — the plain-text fallback body."""
    return html.unescape(re.sub(r"<[^>]+>", "", s))


def whale_dip(s):
    """The promoted 🐳 tier: ⚪ at the chip shelf WITH the whale footprint.
    Gate backtest (homily_whale_backtest.py, 58 names incl. 2021 wrecks,
    point-in-time): fwd60 +10.9% vs +9.5% DCA baseline / +9.7% plain ⚪ dip
    — the one case a ⚪ name may be added."""
    return (s.state == "CAUTION" and s.whale.whale and s.add_zone
            and s.chips.last <= s.add_zone[1])


def fmt_row(s, watch=False, young=False, corp=None, pos=None, dip=0,
            rsrank=None, prov="", brk=False, ipo=False):
    c = s.chips
    tag = "†" if watch else ""  # NB: not "*" — unpaired * breaks TG Markdown
    h = s.vol_hole
    vh = (f" · VH {g(h.lower)}-{g(h.upper)}{VH_ARROW[h.status]}" if h else "")
    yg = " · ⚠️too-new, engines not warmed" if young else ""
    # #27: position-aware digest — % of the (Bucket-C) stock book + a 10%-cap
    # note, only for tracked USD positions (homily_positions.position_view).
    bk = ""
    if pos and pos["pct"] is not None:
        bk = f" · {pos['pct']:.1f}% of book"
        if pos["cap_note"]:
            bk += f" · ⚠️ {esc(pos['cap_note'])}"
    if corp:
        # #19: a split gap in the window poisons the whole chip histogram —
        # every price derived from it (zone, POC, resistance, the VH band, and
        # the 🎯/🐳 tags that compare price to a shelf) never traded. Print the
        # state, suppress the numbers.
        levels, at, wh, vh = esc(suspended_note(corp)), "", "", ""
    else:
        zone = f"{g(s.add_zone[0])}-{g(s.add_zone[1])}" if s.add_zone else "n/a"
        res = g(c.resistance[0][0]) if c.resistance else "ATH air"
        levels = (f"add {zone} · POC {g(c.poc)} · res {res} · "
                  f"{c.pct_in_profit:.0f}% in profit")
        # the Danny move: a non-⭐ name whose price has actually reached the
        # chip-support shelf (⭐ names are at support by definition — no tag)
        at = (" · 🎯AT SUPPORT" if s.state != "ACCUMULATE" and s.add_zone
              and c.last <= s.add_zone[1] else "")
        wh = ""
        if s.whale.whale and s.state != "ACCUMULATE":
            ev = "+".join(e for e, on in (("absorb", s.whale.absorption),
                                          ("flow", s.whale.divergence),
                                          ("shelf", s.whale.shelf_stable)) if on)
            wh = (f" · 🐳{ev}" + (" ≤2% WHALE-DIP add" if whale_dip(s) else ""))
        # #105 (§23): today is the first close above the nearest major
        # overhead shelf with 🐳 in the last 10 sessions — the tested
        # 60d-edge event, fires on the event day only. Info-only.
        if brk:
            wh += " · ⤴break+🐳"
        # #111 (§26): discovery-sourcing context — priced below the
        # first-sale reference (ipo_ref.json). The survivorship caveat
        # lives with the study; info-only, read next to F:n/3.
        if ipo:
            wh += " · IPO↓"
    # #82: RED rows carry the historical base rate (median completed RED run,
    # 1,439 spells, both universes — homily_ribbon_backtest.py) so "8w" reads
    # against how much accumulate-window typically remains. Info-only.
    wk_age = (f"{s.weekly.weeks_in_regime}w · med run {RED_MEDIAN_RUN_W}w"
              if s.weekly.circle == "RED" else f"{s.weekly.weeks_in_regime}w")
    # #78 pullback clock: a non-RED daily-candle run inside an intact weekly
    # RED = a dip in progress; print its age against the measured base rate
    # (1,594 resolved dips, both universes — homily_pullback_backtest.py).
    # Deliberately NOT a warning at p90: the study showed failures resolve
    # faster, not slower, so age alone never escalates. Info-only.
    dp = (f" · dip d{dip} (med {DIP_MEDIAN_D}d · p90 {DIP_P90_D}d)"
          if dip and s.weekly.circle == "RED" else "")
    # #24 promoted (2026-07-12): mark the top-3 ⭐ rows by cross-sectional
    # RS12 rank — the same homily_ledger.rs12_ranks the forward check reads,
    # and the names the buy-day splits across. Suppressed on a corp-suspect
    # row: RS12 is computed from the same tape whose adjustment is in doubt.
    rk = (f" · RS#{rsrank}" if rsrank and rsrank <= 3 and not corp
          and s.state == "ACCUMULATE" else "")
    # #106: a `…` on the wk/monthly tokens = that engine's deciding bar is
    # still forming (Danny's "to be finalized"). Display-only; measured
    # flip-rates in HOW_TO_READ. Off (prov="") in goldens by default.
    mp = "…" if "m" in prov else ""
    wp = "…" if "w" in prov else ""
    return (f"{ICON[s.state]} <code>{esc(f'{s.ticker:<5}')}</code>{tag} "
            f"{g(c.last)} — {levels} · wk {s.weekly.circle}{wp}/{s.weekly.score} "
            f"({wk_age}) · {'mUP' if s.monthly_up else 'mDN'}{mp} · "
            f"d{s.candle[0]}{rk}{dp}{vh}{at}{wh}{yg}{bk}")


MIN_HISTORY = 250   # daily bars below this -> engines aren't warmed up

CRASH_5D = -0.07    # #59: SPY 5-session return at/below this = flash-crash


def crash_line(spy_closes):
    """#59 pre-script, or "". Written on a calm day for a crashed one: the
    only sell authority is the month-end regime banner; a -7% week is not
    it. Pure function of the closes the run already fetched."""
    if len(spy_closes) < 6:
        return ""
    r5 = spy_closes[-1] / spy_closes[-6] - 1
    if r5 > CRASH_5D:
        return ""
    return (f"🧯 <b>FLASH-CRASH PRE-SCRIPT</b> — SPY {r5 * 100:+.1f}% in 5 "
            "sessions. You wrote this on a calm day: the ONLY sell signal "
            "is the month-end regime banner above — a fast week is not it "
            "(2020: −30% and back inside a quarter). DCA continues on "
            "schedule; no margin adds (LEVERAGE.md §2); no averaging down "
            "outside the printed ⭐ zones; reread PLAYBOOK §4, then close "
            "the app. Info only — this line gates nothing.")


MAX_WORKERS = 4     # #17 / R11: bounded fan-out — a rate-limit ban on the
                    # runner IP would kill EVERY digest, worse than slow.


def _screen_one(item, spy, spy_adj):
    """(tk, result, corp, bars) for one name; result is None on any
    fetch/engine failure, corp is the suspect corporate-action bar date or
    None (#19); bars ride along so the #35 chart cards can draw without a
    second fetch. Referenced via the module global fetch_series so tests can
    monkeypatch it."""
    tk, sym = item
    try:
        bars, adj = fetch_series(sym, rng="5y")
        sig = danny_signal(tk, bars)
        c = conviction(sig, bars, spy, adj=adj, spy_adj=spy_adj)
        return (tk, (sig, c, len(bars) < MIN_HISTORY),
                corp_action_bar(bars), bars)
    except Exception:
        return tk, None, None, None


def screen(book, errs, spy, spy_adj=None, suspect=None, bars_out=None):
    """-> list of (DannySignal, Conviction, young), digest-sorted. Fetches fan
    out across a bounded thread pool (network-bound); output is sorted so it is
    identical regardless of completion order. Falls back to a sequential pass
    if the pool itself misbehaves (R11 keeps the sequential path alive).
    `errs`, `suspect` and `bars_out` are filled in place: failed tickers;
    per #19, ticker -> date of the corp-action bar that suspends its levels;
    and, for #35's charts, ticker -> the raw bars already fetched."""
    items = list(book.items())
    try:
        with ThreadPoolExecutor(max_workers=MAX_WORKERS) as ex:
            results = list(ex.map(lambda it: _screen_one(it, spy, spy_adj),
                                  items))
    except Exception:
        results = [_screen_one(it, spy, spy_adj) for it in items]
    out = []
    for tk, res, corp, bars in results:
        if res is None:
            errs.append(tk)
            continue
        out.append(res)
        if corp and suspect is not None:
            suspect[tk] = corp
        if bars_out is not None:
            bars_out[tk] = bars
    out.sort(key=lambda x: digest_sort_key(x[0], x[1]))
    return out


def breadth(screened, all_bars):
    """#26 breadth canary: % of everything screened above its 200d SMA + %
    weekly RED. Info-only forever until a year of ledger data argues
    otherwise (PRD #26). -> {"above200","red","n"} or None."""
    above = red = n = 0
    for s, _c, _y in screened:
        bars = all_bars.get(s.ticker)
        if not bars or len(bars) < 200:
            continue
        closes = [b[4] for b in bars]
        n += 1
        above += closes[-1] > sum(closes[-200:]) / 200
        red += s.weekly.circle == "RED"
    if not n:
        return None
    return {"above200": 100.0 * above / n, "red": 100.0 * red / n, "n": n}


def select_charts(screened, suspect=None):
    """#35: the top-3 actionable names (⭐/🔵, or any name whose dip reached
    its add zone — the 🎯 set), ordered by state precedence then conviction
    score. Corp-suspect names are excluded: their levels are exactly what's
    in doubt (#19), and levels are most of what the chart draws."""
    sus = suspect or {}
    pool = [(s, c) for s, c, _ in screened if s.ticker not in sus
            and (s.state in ("ACCUMULATE", "BOTTOMING")
                 or (s.add_zone and s.chips.last <= s.add_zone[1]))]
    pool.sort(key=lambda x: (ORDER[x[0].state], -x[1].score, x[0].ticker))
    return pool[:3]


def fmt_rocket(s, c, held, *, fund=fund_tag, corp=None, qual=None):
    tag = "" if held else "†"
    top = sorted(c.parts.items(), key=lambda kv: -kv[1])[:2]
    why = ", ".join(f"{k} {v}" for k, v in top)
    size = "≤5% CONVICTION" if c.tier == "CONVICTION" else "≤2% STARTER"
    if corp:
        zone = f" · {esc(suspended_note(corp))}"
    else:
        zone = (f" · add {g(s.add_zone[0])}-{g(s.add_zone[1])}"
                if s.add_zone else "")
    # #66: the sticky quality tier next to F: — info-only label (D-66's
    # cheap forward step; 💎/veto stay dead until their own gates pass)
    q = f" · {esc(qual(s.ticker))}" if qual else ""
    return (f"🚀 <code>{esc(f'{s.ticker:<5}')}</code>{tag} score {c.score} → "
            f"{size} · RS12 {c.rs12:+.0f}pts · ${c.dvol/1e9:.1f}B/d{zone} · "
            f"{esc(why)} · {esc(fund(s.ticker))}{q}")


def render_digest(sigs, disco, proxy, regime, refine, errs, today,
                  *, fund=fund_tag, suspect=None, positions=None, buyday="",
                  bearready="", gaps=None, breadth_read=None, conc=None,
                  flex_notes=None, dips=None, qual=None, promos="", swing="",
                  lev="", household="", cross_book=None, ops="", bear="",
                  turnover="", crash="", dataqa=None, prov=None, brkmap=None):
    """Pure digest assembly — no network, no clock, no state mutation. All
    the varying inputs are passed in so the exact printed text is a
    deterministic function of them; that is what makes the golden-file test
    (homily_golden.py) possible. build_digest() is the thin IO shell that
    gathers these inputs and calls this. Keep the two behaviourally in
    lock-step: any change to a printed row belongs here.

    `positions` (#27) is the holdings.json _v:2 dict (ticker -> {shares,
    cost, bucket?, currency?}) or None/{} on an unsynced book — every price
    for the book-value denominator comes from `sigs` itself (the same
    close the row already prints), so this stays a pure function of its
    arguments, no extra fetching."""
    sus = suspect or {}
    pos = positions or {}
    dip = dips or {}
    prices = {s.ticker: s.chips.last for s, _, _ in sigs if s.ticker in pos}
    book_value = homily_positions.stock_book_value(pos, prices)
    lines = [f"<b>Homily × Danny digest — {esc(today)}</b>"]
    if regime is not None:
        r = regime
        icon = {"BULL": "🐂", "BEAR": "🐻", "MIXED": "⚖️"}[r.label]
        gap = " / ".join(f"{sym} {pct:+.1f}%"
                         for sym, (_, _, pct, _) in r.detail.items())
        lines.append(f"{icon} <b>REGIME: {esc(r.label)}</b> — {esc(gap)} "
                     "vs 10m SMA")
        lines.append(f"<i>{esc(r.action)}</i>")
        if r.label == "BEAR":
            lines.append("🚨 <b>THE DECISIVE SELL SIGNAL IS ON</b> — see"
                         " protocol above; this fires a handful of times a"
                         " decade.")
        if lev:
            # #91 (LEVERAGE.md): the ladder line rides directly under the
            # regime banner it is gated by
            lines.append(lev)
    else:
        lines.append("⚖️ regime check unavailable today")
    # #99 ops-readiness: the owner's own unset switches, one standing line
    if ops:
        lines.append(ops)
    # #59: the flash-crash pre-script — pre-written so the crash-day self
    # reads the calm-day self's instructions, not the tape. Info-only; the
    # regime banner above stays the only sell authority. Counts in #73's
    # header budget (fires a few weeks a decade).
    if crash:
        lines.append(crash)
    # #26 breadth canary: one line, only on a hostile tape, info-only
    if breadth_read and breadth_read["above200"] < 30:
        lines.append(f"⚠️ breadth: only {breadth_read['above200']:.0f}% of "
                     f"the {breadth_read['n']}-name screen above its 200d "
                     f"SMA ({breadth_read['red']:.0f}% weekly RED) — hostile "
                     "tape, historically a poor month for new adds "
                     "(info only, gates nothing)")
    # #29 concentration lens: the book's real diversification, one line
    if conc:
        stars = [s.ticker for s, _c, _y in sigs
                 if s.state == "ACCUMULATE" and s.ticker in pos]
        lines += [ln for ln in homily_clusters.render(conc, stars, esc)]
        # #97: the cross-book view (swing + ESPP), only when it says something
        if cross_book:
            lines += list(cross_book)

    if buyday:
        # #31: on the first trading day of the month the copilot's 🛒 order
        # block leads the digest, right under the regime banner it obeys
        lines += ["", buyday]
    if bearready:
        # #30: first Monday of the month — the §4 rehearsal block
        lines += ["", bearready]
    if household:
        # #94: first Monday of the month — the whole-portfolio scorecard,
        # right after the bear rehearsal it shares a cadence with
        lines += ["", household]
    if promos:
        # #69/#24: month-start promotions check — the frozen rs12-top3
        # window read (published through 2026-10 by promise) + the rolling
        # demotion check every promoted entry must keep passing
        lines += ["", promos]

    # #24 promoted: cross-sectional RS12 rank over today's ⭐ candidates,
    # computed by the same homily_ledger.rs12_ranks the ledger pins for the
    # forward check — the digest mark can never disagree with the CSV column
    rsr = homily_ledger.rs12_ranks(
        [{"ticker": s.ticker, "state": s.state, "rs12": c.rs12}
         for s, c, _ in sigs + disco])

    lines.append("")
    cur = None
    for s, c, young in sigs:
        if s.state != cur:
            cur = s.state
            lines.append(f"<b>{ICON[cur]} {esc(cur)}</b>")
        pv = homily_positions.position_view(s.ticker, pos, prices, book_value)
        lines.append(fmt_row(s, s.ticker in WATCH, young, sus.get(s.ticker),
                             pv, dip.get(s.ticker, 0),
                             rsrank=rsr.get(s.ticker),
                             prov=(prov or {}).get(s.ticker, ""),
                             brk=(brkmap or {}).get(s.ticker, False)))
        # #28: PLAYBOOK §5 trim rules as flags on held rows — info only
        if s.ticker in pos:
            for fl in homily_positions.trim_flags(
                    pv, s.state, s.weekly.weeks_in_regime, fund(s.ticker)):
                lines.append(f"　⚠️ <b>{esc(fl)}</b>")
        if s.ticker in proxy:
            lines.append(proxy[s.ticker])

    # #102: the consolidated bearish tells over held names — preformatted by
    # homily_bearish.block(), printed right under the rows it summarises.
    # Info-only by design AND by evidence (the nulls are in the block text);
    # nothing downstream reads it.
    if bear:
        lines += ["", bear]

    # multi-bagger watch: stringent 5-gate screen across EVERYTHING
    rockets = sorted([(s, c) for s, c, _ in sigs + disco if c.gates_ok],
                     key=lambda x: -x[1].score)
    lines += ["", "<b>🚀 MULTI-BAGGER WATCH (5 hard gates: size, trend, "
              "leader-RS, basis, data)</b>"]
    if rockets:
        lines += [fmt_rocket(s, c, s.ticker in HOLDINGS, fund=fund,
                             corp=sus.get(s.ticker), qual=qual)
                  for s, c in rockets[:5]]
        lines.append("<i>sizing guide: CONVICTION ≤5% of account · STARTER "
                     "≤2% · add-cap 25%/name incl. existing (#92, demotion "
                     "watch armed) · add at ⭐ zones only</i>")
    else:
        lines.append("no name passes all 5 gates today — that's the point")

    # discovery: new-money setups among names not held (⭐/🔵, plus the
    # promoted 🐳 whale-dip tier — a ⚪ shelf dip being absorbed)
    # a suspect name never earns the 🐳 promotion: that tier is defined by its
    # distance to a chip shelf, and the shelf is exactly what's in doubt (#19)
    hits = [(s, y) for s, c, y in disco
            if s.state in ("ACCUMULATE", "BOTTOMING")
            or (whale_dip(s) and s.ticker not in sus)]
    lines += ["", f"<b>🔎 DISCOVERY — new-money setups ({len(disco)} names "
              "screened, not held)</b>"]
    if hits:
        lines += [fmt_row(s, True, y, sus.get(s.ticker),
                          rsrank=rsr.get(s.ticker),
                          prov=(prov or {}).get(s.ticker, ""),
                          brk=(brkmap or {}).get(s.ticker, False),
                          ipo=(s.ticker in IPO_REFS
                               and s.chips.last < IPO_REFS[s.ticker]["ref"]))
                  + f" · {esc(fund(s.ticker))}"
                  + (f" · {esc(qual(s.ticker))}" if qual else "")
                  for s, y in hits]
    else:
        lines.append("no ⭐/🔵/🐳-dip setups in the universe today")
    # #32: the Flex sync's one-line diffs (or its failure warning) — book
    # changes and sync problems both belong where the owner will read them
    for note in (flex_notes or []):
        lines.append(f"📒 book sync: {esc(note)}")
    if errs:
        lines.append(f"⚠️ fetch failed: {esc(', '.join(errs))}")
    # #60: data-QA notes (stale tape / source disagreement) — housekeeping
    # zone with the other infra warnings; warning only, never a halt (R4)
    for note in (dataqa or []):
        lines.append(f"⚠️ data-QA: {esc(note)}")
    if gaps:
        # #70: a weekday with no ledger rows = the runner never started —
        # say so, or the live record grows silent holes
        lines.append(f"⚠️ no ledger rows for {esc(', '.join(gaps))} — runner "
                     "missed, live record has a hole")
    if swing:
        # #90 (D-90): the merged gambit sleeve's paper state — fenced,
        # counters only; the weekly ♟️ digest carries the priced book
        lines += ["", swing]

    # #34 F0: legend + algo-health fold into ONE expandable blockquote so the
    # actionable digest above stays short; details are one tap away.
    champ, chal, oos_chal, oos_def, champ_oos, adopted = refine
    footer = ["<i>add = chip-support accumulate zone · POC = cost point of"
              " control · res = nearest chip resistance · VH = volatility"
              " hole zone (↑ broke above = bottoming confirm, ↓ broke below"
              " = topping risk, ◻ inside) · 🎯 = non-⭐ name at its"
              " chip-support shelf: on 🟡 the stalked dip has arrived"
              " (Danny-style discretionary add, not the backtested routine);"
              " on ⚪ info only — UNLESS 🐳 joins it · 🐳 = whale-accumulation"
              " footprint in a dip (absorb = heavy-volume floor-probe closing"
              " off its lows · flow = OBV/A-D holding vs falling price ·"
              " shelf = chip shelf replenished while price sits on it);"
              " ⚪ + 🎯 + 🐳 = WHALE-DIP tier, the one case a ⚪ name may be"
              " added — discretionary, ≤2% of account, same monthly budget,"
              " 25%/name add-cap (gate backtest: fwd60 +10.9% vs +9.5% DCA,"
              " 58 names incl. 2021 wrecks) · ⚠️ levels suspended = a >45%"
              " one-day move on abnormal volume sits in the chip window, so a"
              " split/spin-off may be mis-adjusted: the state row still"
              " prints, the levels would not be prices you could trade"
              " · F:n/m = EDGAR fundamentals"
              " checks passed (growth/profit/dilution; info only, never a"
              " timing input) · Q1/Q2/Q3 = sticky quality tier (quarterly"
              " EDGAR read + 3y RS, frozen between refreshes — business"
              " quality that does not move with the tape; info only)"
              " · RS#n = today's ⭐ RS12 rank; the buy-day splits across the"
              " top-3 (#24 promoted 2026-07-12 by owner override AHEAD of"
              " its live forward-check — the check keeps publishing at each"
              " month-start through 2026-10, demotion mandatory on FAIL)"
              " · † = not held</i>",
              "", "<b>Algo health (auto-refine, OOS-gated):</b>",
              f"champion <code>{esc(champ['params'])}</code> since "
              f"{esc(champ['since'])}",
              f"OOS Calmar champ {champ_oos:.2f} / challenger {oos_chal:.2f}"
              f"{'  → ADOPTED' if adopted else ''}",
              # #88: the buy-day set's within-month stability — info only
              *([f"<i>{esc(turnover)}</i>"] if turnover else []),
              "📖 <i>2-min guide + bear playbook: PLAYBOOK.md in the repo</i>",
              "<i>Reminder: approximation of Danny/Homily behaviour, not their"
              " proprietary formulas. 5y backtest: waiting for ⭐ zones got a "
              "WORSE avg cost than immediate DCA on every name tested — treat "
              "levels as context, not a reason to sit in cash. CAUTION = "
              "pause adds, never a mechanical sell.</i>"]
    lines += ["", "<blockquote expandable>" + "\n".join(footer)
              + "</blockquote>"]
    return "\n".join(lines)


def build_digest(flex_notes=None):
    """IO shell: fetch everything the digest needs, then hand it to the pure
    render_digest(). The network/clock/state-mutating calls live ONLY here."""
    errs, suspect, all_bars = [], {}, {}
    spy_bars, spy_adj = fetch_series("SPY", rng="5y")
    spy = [b[4] for b in spy_bars]
    sigs = screen({**HOLDINGS, **WATCH}, errs, spy, spy_adj, suspect,
                  bars_out=all_bars)
    disco = screen({k: v for k, v in UNIVERSE.items() if k not in HOLDINGS},
                   errs, spy, spy_adj, suspect, bars_out=all_bars)
    try:
        regime = market_regime()
    except Exception:
        regime = None
    # constituent proxy reads for too-new holdings (e.g. DRAM basket)
    proxy = {}
    for tk, members in PROXY_CONSTITUENTS.items():
        if tk in HOLDINGS:
            ps = screen(members, errs, spy, spy_adj)
            reads = " · ".join(f"{esc(p.ticker)} {ICON[p.state]}"
                               for p, _, _ in ps)
            proxy[tk] = f"　↳ <i>constituents proxy:</i> {reads}"
    # Pinned SGT run date (R7) — the ledger idempotency key and the digest
    # date must be the same value on every runner; homily_ledger owns it.
    today = homily_ledger.run_date()
    # one state_of() pass feeds both the buy-day copilot (#31) and the
    # state-change alerts (#15)
    states = []
    try:
        states = ([homily_ledger.state_of(s, c, s.ticker in HOLDINGS)
                   for s, c, _ in sigs]
                  + [homily_ledger.state_of(s, c, False) for s, c, _ in disco])
    except Exception as e:
        print(f"[states] skipped: {e}")
    # #31 buy-day copilot: on the month's first run (per the ledger, D-31),
    # resolve BUY_BUDGET_USD into printed orders + the T2 basket CSV.
    # Non-fatal to the send, like everything downstream of the digest.
    buyday, buyplan = "", None
    try:
        if states:
            buyday, buyplan = homily_buyday.buyday_block(
                states, POSITIONS, regime, today,
                yahoo={**HOLDINGS, **WATCH, **UNIVERSE})
    except Exception as e:
        print(f"[buyday] skipped: {e}")
    # #30 bear-readiness rehearsal, first Monday of the month. Non-fatal.
    bearready = ""
    try:
        if states:
            bearready = homily_bearready.bearready_block(states, POSITIONS,
                                                         today)
    except Exception as e:
        print(f"[bearready] skipped: {e}")
    # #99 ops-readiness: the owner's unset switches, one standing line (env
    # only, no fetch). Non-fatal, info-only.
    ops = ""
    try:
        ops = homily_ops.ops_line(os.environ, esc=esc)
    except Exception as e:
        print(f"[ops] skipped: {e}")
    # #94 household scorecard, first Monday of the month. Reads the same held
    # prices the digest already shows; fetches only QQQ (counterfactual) +
    # SGD=X (FX) inside its own shell. Non-fatal, info-only.
    household = ""
    try:
        prices_all = {s.ticker: s.chips.last for s, _c, _y in sigs}
        household = homily_household.household_block(
            POSITIONS, prices_all, today,
            regime_label=(regime.label if regime is not None else ""),
            esc=esc)
    except Exception as e:
        print(f"[household] skipped: {e}")
    # #69/#24: month-start promotions block — the frozen rs12-top3 window
    # read (promised through the 2026-10-01 read) + the rolling demotion
    # check for promoted entries. Same first-run-of-month test as the
    # copilot, but independent of BUY_BUDGET_USD. Non-fatal.
    promos = ""
    try:
        lrows = homily_ledger._read_rows()
        if homily_buyday.is_buy_day(today, lrows):
            promos = homily_promotions.month_start_block(lrows, today, esc=esc)
    except Exception as e:
        print(f"[promotions] skipped: {e}")
    # #92: the promoted add-cap's demotion watch — EVERY run, not just
    # month-start (a halving must surface the day it prints). Highs are the
    # max close since the promotion date, from bars already fetched.
    try:
        _cd = datetime.date.fromisoformat(homily_positions.CAP_PROMOTED)
        highs = {tk: max((b[4] for b in bs if b[0] >= _cd), default=None)
                 for tk, bs in all_bars.items()}
        prices_now = {s.ticker: s.chips.last for s, _c, _y in sigs}
        capdem = homily_positions.cap_demotion_line(POSITIONS, prices_now,
                                                    highs)
        if capdem:
            promos = f"{promos}\n\n{capdem}" if promos else capdem
    except Exception as e:
        print(f"[cap-demotion] skipped: {e}")
    # #70: surface recent runner misses (last ~2 weeks; the snapshot keeps
    # the full history so an old hole doesn't nag forever). Non-fatal.
    gaps = []
    try:
        cov = homily_ledger.coverage_of(homily_ledger._read_rows(), today)
        cutoff = (today - datetime.timedelta(days=14)).isoformat()
        gaps = [d for d in cov["missing"] if d >= cutoff]
    except Exception as e:
        print(f"[coverage] skipped: {e}")
    # #90/#93: SWING sleeve state — paper block + LIVE status (A5) + the
    # month-start realized report. Pure reads of committed gambit state;
    # non-fatal, never fetches, never writes sleeve state (R3).
    swing = ""
    try:
        swing = homily_swing.swing_block(homily_swing.load_state(), today,
                                         esc=esc)
        live = homily_swing.load_live()
        lb = homily_swing.live_block(live, esc=esc)
        if lb:
            swing = f"{swing}\n{lb}" if swing else lb
        if homily_buyday.is_buy_day(today, homily_ledger._read_rows()):
            mb = homily_swing.monthly_block(live, today, esc=esc)
            if mb:
                swing = f"{swing}\n\n{mb}" if swing else mb
    except Exception as e:
        print(f"[swing] skipped: {e}")
    # #91: the leverage-ladder line (LEVERAGE.md §5) — pure render from the
    # regime label + the #30 MARGIN_ZERO flag; non-fatal.
    lev = ""
    try:
        if regime is not None:
            mz = os.getenv("MARGIN_ZERO", "").lower() in (
                "1", "true", "yes", "on")
            lev = homily_leverage.leverage_line(regime.label, mz, esc=esc)
    except Exception as e:
        print(f"[leverage] skipped: {e}")
    # #26 breadth + #29 concentration: both pure reads of already-fetched
    # bars; both non-fatal, both info-only.
    br, conc, cross_book = None, None, None
    try:
        br = breadth(sigs + disco, all_bars)
        prices_held = {s.ticker: s.chips.last for s, _c, _y in sigs}
        conc = homily_clusters.concentration(all_bars, POSITIONS, prices_held)
        # #97 (G5): fold the swing sleeve's open positions + external ESPP
        # into the lens — exposures holdings.json can't see. Value = deployed
        # basis (swing) / external balance (ESPP); sector from holdings where
        # the name overlaps, else "other". Correlation math untouched.
        extra = []
        live = homily_swing.load_live()
        for sym, p in ((live or {}).get("positions") or {}).items():
            extra.append({"ticker": sym, "book": "swing",
                          "value": float(p.get("basis") or 0.0),
                          "sector": POSITIONS.get(sym, {}).get("sector",
                                                               "other")})
        try:
            _cb = homily_household.load_contributions().get("balances", {})
            espp = float(_cb.get("espp_external_usd") or 0.0)
        except Exception:
            espp = 0.0
        if espp > 0:
            extra.append({"ticker": "V", "book": "espp", "value": espp,
                          "sector": POSITIONS.get("V", {}).get("sector",
                                                               "payments")})
        if conc and extra:
            cross_book = homily_clusters.combined_render(
                homily_clusters.combined_view(conc, extra), esc)
    except Exception as e:
        print(f"[lens] skipped: {e}")
    # #78: dip-day counter for held/watch rows in an intact weekly RED.
    # Pure read of already-fetched bars; non-fatal, info-only.
    dips = {}
    try:
        dips = {s.ticker: dip_age([b[4] for b in all_bars[s.ticker]])
                for s, _c, _y in sigs
                if s.weekly.circle == "RED" and s.ticker in all_bars}
    except Exception as e:
        print(f"[dips] skipped: {e}")
    # #60: data-QA on the benchmark tape everything keys off — freshness of
    # the SPY series this very run fetched + a Stooq second opinion on the
    # last common close. Non-fatal end to end; a dead Stooq costs nothing.
    dataqa = []
    try:
        fn = homily_data.freshness_note(spy_bars, today)
        if fn:
            dataqa.append(fn)
        try:
            an = homily_data.agreement_note(spy_bars,
                                            homily_data.stooq_daily("SPY"))
            if an:
                dataqa.append(an)
        except Exception:
            pass                      # second source is strictly optional
    except Exception as e:
        print(f"[data-qa] skipped: {e}")
    # #88: top-3 turnover — how fragile the buy-day's point-in-time ⭐ set is
    # within the month. One footer line, needs ≥2 ledger runs; info-only.
    turnover = ""
    try:
        t88 = homily_ledger.top3_turnover(homily_ledger._read_rows(), today)
        if t88 and t88["days"] >= 2:
            turnover = (f"top-3 ⭐ set stable {t88['stable']}/{t88['days']} "
                        f"runs this month vs the buy-day set "
                        f"({' · '.join(t88['ref'])}) — high churn = fragile "
                        "snapshot, #87's question (info only, gates nothing)")
    except Exception as e:
        print(f"[turnover] skipped: {e}")
    # #102: short-term bearish tells on held names — pure read of the sigs +
    # bars this run already fetched; prints only on >=2 concurrent tells.
    # Non-fatal, info-only, feeds nothing downstream.
    bear = ""
    try:
        bear = homily_bearish.block(sigs, all_bars, set(HOLDINGS), esc=esc)
    except Exception as e:
        print(f"[bearish] skipped: {e}")
    # #106: which rows' trend engines read an unfinished bar today — per
    # name because HK/US session calendars differ. Display-only.
    prov = {}
    try:
        prov = {tk: homily_provisional.marks(bs)
                for tk, bs in all_bars.items()}
    except Exception as e:
        print(f"[provisional] skipped: {e}")
    # #105 (§23): whale-confirmed shelf-break event day — the tested
    # 60d-edge entry, tagged ⤴ on the row. Corp-suspect names skip (their
    # chip histogram, hence the shelf reference, is poisoned — same rule
    # as the levels themselves). Info-only.
    brkmap = {}
    try:
        brkmap = {tk: homily_breakout.breakout_today(bs)
                  for tk, bs in all_bars.items() if tk not in suspect}
    except Exception as e:
        print(f"[breakout] skipped: {e}")
    # #66: sticky quality tier, quarterly-cached EDGAR read + 3y RS from the
    # bars already fetched. Info-only label; quality_tag never raises.
    spy_cl = [b[4] for b in spy_bars]
    def qual(tk):
        bars = all_bars.get(tk)
        return homily_quality.quality_tag(
            tk, [b[4] for b in bars] if bars else None, spy_cl)
    digest = render_digest(sigs, disco, proxy, regime,
                           daily_refine(bars_map=all_bars), errs,
                           today, suspect=suspect, positions=POSITIONS,
                           buyday=buyday, bearready=bearready, gaps=gaps,
                           breadth_read=br, conc=conc, cross_book=cross_book,
                           flex_notes=flex_notes,
                           dips=dips, qual=qual, promos=promos, swing=swing,
                           lev=lev, household=household, ops=ops, bear=bear,
                           turnover=turnover, crash=crash_line(spy),
                           dataqa=dataqa, prov=prov, brkmap=brkmap)
    # #15 state-change alerts: diff today's states against yesterday's ledger
    # BEFORE record() overwrites it, so a quiet day sends no second message.
    alert = ""
    try:
        if states:
            alert = homily_alerts.format_alerts(
                homily_alerts.build_alerts(states, regime, today), today)
    except Exception as e:
        print(f"[alerts] skipped: {e}")
    # #65 shadow quarter: screen the mechanical universe.json names the hand
    # list does NOT already cover; their rows land in the ledger tagged
    # origin "shadow-screen" (no digest surface, no rank participation).
    # The D-65 adoption gate reads one quarter of these rows (~2026-10):
    # keep ≥90% of what the hand list surfaced AND find ≥1 setup it missed.
    # Non-fatal, like everything downstream of the digest.
    shadow = []
    try:
        mech = homily_universe.load_names()
        extra = {tk: tk for tk in mech
                 if tk not in HOLDINGS and tk not in WATCH
                 and tk not in UNIVERSE}
        shadow = [(s, c) for s, c, _ in
                  screen(extra, [], spy, spy_adj)]
    except Exception as e:
        print(f"[shadow] skipped: {e}")
    # #13 signals ledger + snapshot: record what the digest printed today.
    # Non-fatal to the send (the user always gets their digest); any history
    # corruption is caught hard by the validate gate (check [17]) that #16
    # runs BEFORE this step in CI.
    try:
        homily_ledger.record(sigs, disco, regime, today, set(HOLDINGS),
                             origins=ORIGINS, buyday=buyplan, shadow=shadow)
    except Exception as e:
        print(f"[ledger] skipped: {e}")
    # #36/#83 nightly boards from the just-written snapshot + ledger + this
    # run's bars: the SMALL board (docs/dashboard.html — committed by the
    # workflow, R8) and the FULL searchable board (temp path, sent below,
    # NEVER committed — D-83 §search). Stale temp unlinked first so a failed
    # render can never send yesterday's board. Non-fatal.
    try:
        if os.path.exists(homily_dashboard.BOARD_FULL):
            os.unlink(homily_dashboard.BOARD_FULL)
        homily_dashboard.write_dashboard(bars_map=all_bars)
        homily_dashboard.write_dashboard(homily_dashboard.BOARD_FULL,
                                         bars_map=all_bars, full=True)
    except Exception as e:
        print(f"[dashboard] skipped: {e}")
    # #35 chart cards: top-3 actionable names rendered from the bars the
    # screen already fetched. Per-name try — one bad render never costs the
    # others, and never the digest.
    charts = []
    for s, c in select_charts(sigs + disco, suspect):
        try:
            caption = strip_html(fmt_row(s, s.ticker in WATCH))
            charts.append((s.ticker,
                           homily_png.chart_png(s.ticker,
                                                all_bars[s.ticker], s),
                           caption))
        except Exception as e:
            print(f"[chart {s.ticker}] skipped: {e}")
    return digest, alert, charts


def chunks(text, limit=4000):
    """Split on line boundaries under Telegram's 4096-char message cap."""
    out, cur = [], ""
    for line in text.split("\n"):
        if cur and len(cur) + len(line) + 1 > limit:
            out.append(cur); cur = line
        else:
            cur = f"{cur}\n{line}" if cur else line
    if cur:
        out.append(cur)
    return out


def send(text):
    tok, chat = os.getenv("TELEGRAM_BOT_TOKEN"), os.getenv("TELEGRAM_CHAT_ID")
    if not (tok and chat):
        print(text); print("\n[no TELEGRAM_* env — printed only]"); return
    url = f"https://api.telegram.org/bot{tok}/sendMessage"

    def post(params):
        body = urllib.parse.urlencode(params).encode()
        urllib.request.urlopen(urllib.request.Request(url, data=body),
                               timeout=20)
    parts = chunks(text)
    n = len(parts)
    for i, part in enumerate(parts, 1):
        # digest exceeds Telegram's single-message cap -> split across
        # messages; label them so the reader knows more is coming
        page = f"<i>(part {i}/{n})</i>\n\n" if n > 1 else ""
        try:
            post({"chat_id": chat, "text": page + part, "parse_mode": "HTML"})
            print("[sent to Telegram]")
        except urllib.error.HTTPError as e:
            # HTML entity-parse failures return 400 — deliver tag-stripped
            # plain text rather than dropping the digest (#34 R4)
            print(f"[HTML send failed: {e.code} "
                  f"{e.read().decode(errors='replace')[:200]}]")
            post({"chat_id": chat, "text": strip_html(page + part)})
            print("[sent to Telegram — plain-text fallback]")


def send_photo(png, caption):
    """#35: sendPhoto via hand-rolled multipart/form-data (stdlib only).
    Caption is plain text (≤1024 per Telegram); a failed photo is logged and
    dropped — the text digest already carried the information."""
    tok, chat = os.getenv("TELEGRAM_BOT_TOKEN"), os.getenv("TELEGRAM_CHAT_ID")
    if not (tok and chat):
        print(f"[chart rendered, {len(png)} bytes — no TELEGRAM_* env, "
              "not sent]")
        return
    boundary = "homilyF1boundary"
    enc = lambda s: str(s).encode()
    body = b"".join([
        enc(f"--{boundary}\r\nContent-Disposition: form-data; "
            f"name=\"chat_id\"\r\n\r\n{chat}\r\n"),
        enc(f"--{boundary}\r\nContent-Disposition: form-data; "
            f"name=\"caption\"\r\n\r\n{caption[:1024]}\r\n"),
        enc(f"--{boundary}\r\nContent-Disposition: form-data; "
            f"name=\"photo\"; filename=\"chart.png\"\r\n"
            "Content-Type: image/png\r\n\r\n"),
        png, enc(f"\r\n--{boundary}--\r\n")])
    req = urllib.request.Request(
        f"https://api.telegram.org/bot{tok}/sendPhoto", data=body,
        headers={"Content-Type": f"multipart/form-data; boundary={boundary}"})
    try:
        urllib.request.urlopen(req, timeout=30)
        print("[chart sent to Telegram]")
    except Exception as e:
        print(f"[chart send failed, dropped: {e}]")


def send_document(path, caption):
    """#36: sendDocument (same multipart pattern as send_photo); the
    dashboard file lands in the chat, one tap to open, works offline."""
    tok, chat = os.getenv("TELEGRAM_BOT_TOKEN"), os.getenv("TELEGRAM_CHAT_ID")
    if not (tok and chat):
        print(f"[document {os.path.basename(path)} ready — no TELEGRAM_* "
              "env, not sent]")
        return
    with open(path, "rb") as f:
        blob = f.read()
    boundary = "homilyF2boundary"
    enc = lambda s: str(s).encode()
    body = b"".join([
        enc(f"--{boundary}\r\nContent-Disposition: form-data; "
            f"name=\"chat_id\"\r\n\r\n{chat}\r\n"),
        enc(f"--{boundary}\r\nContent-Disposition: form-data; "
            f"name=\"caption\"\r\n\r\n{caption[:1024]}\r\n"),
        enc(f"--{boundary}\r\nContent-Disposition: form-data; "
            f"name=\"document\"; "
            f"filename=\"{os.path.basename(path)}\"\r\n"
            "Content-Type: text/html\r\n\r\n"),
        blob, enc(f"\r\n--{boundary}--\r\n")])
    req = urllib.request.Request(
        f"https://api.telegram.org/bot{tok}/sendDocument", data=body,
        headers={"Content-Type": f"multipart/form-data; boundary={boundary}"})
    try:
        urllib.request.urlopen(req, timeout=30)
        print("[dashboard sent to Telegram]")
    except Exception as e:
        print(f"[dashboard send failed, dropped: {e}]")


def sunday_deepdive():
    """#33: the Sunday run is fetch-free — the week's ledger rows + Friday's
    snapshot make the summary; the dashboard is regenerated from the same
    committed artifacts and sent as the deep dive. No engine call, no
    ledger write on a non-trading day (R3)."""
    import json
    import homily_weekly
    today = homily_ledger.run_date()
    rows = homily_ledger._read_rows()
    snap = {}
    if os.path.exists(homily_ledger.SNAPSHOT):
        snap = json.load(open(homily_ledger.SNAPSHOT))
    summary = homily_weekly.weekly_summary(rows, snap, today)
    if not summary:
        print("[weekly] no rows this week — nothing to send")
        return
    # #54: the week-over-week diff rides the same message — pure ledger
    # read, '' on bootstrap/holiday weeks, never blocks the summary
    try:
        diff = homily_weekly.week_diff(rows, today)
        if diff:
            summary = f"{summary}\n\n{diff}"
    except Exception as e:
        print(f"[week-diff] skipped: {e}")
    # #83: the committed board already carries Friday's candle charts (built
    # WITH bars by Friday's run); regenerating here without bars would strip
    # them. Only build a fresh one if the file is missing entirely.
    if not os.path.exists(homily_dashboard.DASHBOARD):
        try:
            homily_dashboard.write_dashboard()
        except Exception as e:
            print(f"[dashboard] skipped: {e}")
    send(summary)
    if os.path.exists(homily_dashboard.DASHBOARD):
        send_document(homily_dashboard.DASHBOARD,
                      "📒 weekly deep dive — the full picture, offline")


if __name__ == "__main__":
    if homily_ledger.run_date().weekday() == 6:      # Sunday SGT → #33
        sunday_deepdive()
        raise SystemExit(0)
    # #32: sync the book from IBKR Flex BEFORE anything reads it. Env-gated
    # (unset secrets = no-op), never fatal; on any change the module-level
    # book views are rebuilt so this run screens the synced book.
    flex_notes = homily_flex.auto_sync()
    if flex_notes:
        for _d in flex_notes:
            print(f"[flex] {_d}")
        POSITIONS = homily_positions.load_positions()
        HOLDINGS = {k: v["yahoo"] for k, v in POSITIONS.items()}
        ORIGINS = {**{tk: "owner-request" for tk in {**WATCH, **UNIVERSE}},
                   **{tk: "holding" for tk in HOLDINGS}}
    digest, alert, charts = build_digest(flex_notes)
    send(digest)
    for _tk, png, caption in charts:    # #35: top-3 actionable chart cards
        send_photo(png, caption)
    if os.path.exists(homily_dashboard.DASHBOARD):   # #36: nightly dashboard
        send_document(homily_dashboard.DASHBOARD,
                      "📊 dashboard — tap to open (works offline)")
    if os.path.exists(homily_dashboard.BOARD_FULL):  # #83: sent, not committed
        send_document(homily_dashboard.BOARD_FULL,
                      "🔎 full board — every screened name, searchable")
    if alert:                       # #15: only on a state change, never quiet
        send(alert)
