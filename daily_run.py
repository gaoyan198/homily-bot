#!/usr/bin/env python3
"""
Daily entrypoint: fetch -> Danny-style composite signal -> auto-refine ->
Telegram digest. Pure stdlib (urllib). GitHub Actions cron (9am SGT = 01:00
UTC); champion state is committed back by the workflow.

Signal semantics follow @dannycheng2022's use of Homily charts (see PRD.md):
accumulate-on-dip guidance anchored on chip support — there is no SELL state.

Env: TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID (if unset -> prints digest, no send).
"""
import os, re, html, urllib.request, urllib.parse, urllib.error
from concurrent.futures import ThreadPoolExecutor
from homily_data import fetch_series
from homily_danny import danny_signal
from homily_conviction import conviction
from homily_fund import fund_tag
from homily_regime import market_regime
from homily_refine import daily_refine
from homily_corp import corp_action_bar, suspended_note
import homily_ledger
import homily_alerts
import homily_positions
import homily_buyday
import homily_png

# IBKR holding -> Yahoo symbol: lives in holdings.json (schema _v:2, #27) so
# book changes are a one-line edit (last synced from live IBKR positions
# 2026-07-10). POSITIONS carries the shares/cost/bucket #27 needs; HOLDINGS
# stays the flat ticker->yahoo map every screen()/membership check expects.
POSITIONS = homily_positions.load_positions()
HOLDINGS = {k: v["yahoo"] for k, v in POSITIONS.items()}
# Danny-core names not (yet) held — charted anyway, week after week
WATCH = {"ASML":"ASML"}

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


def fmt_row(s, watch=False, young=False, corp=None, pos=None):
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
    return (f"{ICON[s.state]} <code>{esc(f'{s.ticker:<5}')}</code>{tag} "
            f"{g(c.last)} — {levels} · wk {s.weekly.circle}/{s.weekly.score} "
            f"({s.weekly.weeks_in_regime}w) · {'mUP' if s.monthly_up else 'mDN'} · "
            f"d{s.candle[0]}{vh}{at}{wh}{yg}{bk}")


MIN_HISTORY = 250   # daily bars below this -> engines aren't warmed up


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
    out.sort(key=lambda x: (ORDER[x[0].state], x[0].ticker))
    return out


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


def fmt_rocket(s, c, held, *, fund=fund_tag, corp=None):
    tag = "" if held else "†"
    top = sorted(c.parts.items(), key=lambda kv: -kv[1])[:2]
    why = ", ".join(f"{k} {v}" for k, v in top)
    size = "≤5% CONVICTION" if c.tier == "CONVICTION" else "≤2% STARTER"
    if corp:
        zone = f" · {esc(suspended_note(corp))}"
    else:
        zone = (f" · add {g(s.add_zone[0])}-{g(s.add_zone[1])}"
                if s.add_zone else "")
    return (f"🚀 <code>{esc(f'{s.ticker:<5}')}</code>{tag} score {c.score} → "
            f"{size} · RS12 {c.rs12:+.0f}pts · ${c.dvol/1e9:.1f}B/d{zone} · "
            f"{esc(why)} · {esc(fund(s.ticker))}")


def render_digest(sigs, disco, proxy, regime, refine, errs, today,
                  *, fund=fund_tag, suspect=None, positions=None, buyday=""):
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
    else:
        lines.append("⚖️ regime check unavailable today")

    if buyday:
        # #31: on the first trading day of the month the copilot's 🛒 order
        # block leads the digest, right under the regime banner it obeys
        lines += ["", buyday]

    lines.append("")
    cur = None
    for s, c, young in sigs:
        if s.state != cur:
            cur = s.state
            lines.append(f"<b>{ICON[cur]} {esc(cur)}</b>")
        pv = homily_positions.position_view(s.ticker, pos, prices, book_value)
        lines.append(fmt_row(s, s.ticker in WATCH, young, sus.get(s.ticker), pv))
        if s.ticker in proxy:
            lines.append(proxy[s.ticker])

    # multi-bagger watch: stringent 5-gate screen across EVERYTHING
    rockets = sorted([(s, c) for s, c, _ in sigs + disco if c.gates_ok],
                     key=lambda x: -x[1].score)
    lines += ["", "<b>🚀 MULTI-BAGGER WATCH (5 hard gates: size, trend, "
              "leader-RS, basis, data)</b>"]
    if rockets:
        lines += [fmt_rocket(s, c, s.ticker in HOLDINGS, fund=fund,
                             corp=sus.get(s.ticker))
                  for s, c in rockets[:5]]
        lines.append("<i>sizing guide: CONVICTION ≤5% of account · STARTER "
                     "≤2% · hard cap 10%/name incl. existing · add at ⭐ "
                     "zones only</i>")
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
        lines += [fmt_row(s, True, y, sus.get(s.ticker))
                  + f" · {esc(fund(s.ticker))}" for s, y in hits]
    else:
        lines.append("no ⭐/🔵/🐳-dip setups in the universe today")
    if errs:
        lines.append(f"⚠️ fetch failed: {esc(', '.join(errs))}")

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
              " 10%/name hard cap (gate backtest: fwd60 +10.9% vs +9.5% DCA,"
              " 58 names incl. 2021 wrecks) · ⚠️ levels suspended = a >45%"
              " one-day move on abnormal volume sits in the chip window, so a"
              " split/spin-off may be mis-adjusted: the state row still"
              " prints, the levels would not be prices you could trade"
              " · F:n/m = EDGAR fundamentals"
              " checks passed (growth/profit/dilution; info only, never a"
              " timing input) · † = not held</i>",
              "", "<b>Algo health (auto-refine, OOS-gated):</b>",
              f"champion <code>{esc(champ['params'])}</code> since "
              f"{esc(champ['since'])}",
              f"OOS Calmar champ {champ_oos:.2f} / challenger {oos_chal:.2f}"
              f"{'  → ADOPTED' if adopted else ''}",
              "📖 <i>2-min guide + bear playbook: PLAYBOOK.md in the repo</i>",
              "<i>Reminder: approximation of Danny/Homily behaviour, not their"
              " proprietary formulas. 5y backtest: waiting for ⭐ zones got a "
              "WORSE avg cost than immediate DCA on every name tested — treat "
              "levels as context, not a reason to sit in cash. CAUTION = "
              "pause adds, never a mechanical sell.</i>"]
    lines += ["", "<blockquote expandable>" + "\n".join(footer)
              + "</blockquote>"]
    return "\n".join(lines)


def build_digest():
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
    buyday = ""
    try:
        if states:
            buyday = homily_buyday.buyday_block(
                states, POSITIONS, regime, today,
                yahoo={**HOLDINGS, **WATCH, **UNIVERSE})
    except Exception as e:
        print(f"[buyday] skipped: {e}")
    digest = render_digest(sigs, disco, proxy, regime, daily_refine(), errs,
                           today, suspect=suspect, positions=POSITIONS,
                           buyday=buyday)
    # #15 state-change alerts: diff today's states against yesterday's ledger
    # BEFORE record() overwrites it, so a quiet day sends no second message.
    alert = ""
    try:
        if states:
            alert = homily_alerts.format_alerts(
                homily_alerts.build_alerts(states, regime, today), today)
    except Exception as e:
        print(f"[alerts] skipped: {e}")
    # #13 signals ledger + snapshot: record what the digest printed today.
    # Non-fatal to the send (the user always gets their digest); any history
    # corruption is caught hard by the validate gate (check [17]) that #16
    # runs BEFORE this step in CI.
    try:
        homily_ledger.record(sigs, disco, regime, today, set(HOLDINGS),
                             origins=ORIGINS)
    except Exception as e:
        print(f"[ledger] skipped: {e}")
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


if __name__ == "__main__":
    digest, alert, charts = build_digest()
    send(digest)
    for _tk, png, caption in charts:    # #35: top-3 actionable chart cards
        send_photo(png, caption)
    if alert:                       # #15: only on a state change, never quiet
        send(alert)
