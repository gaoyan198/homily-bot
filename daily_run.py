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
from homily_data import fetch_daily
from homily_danny import danny_signal
from homily_conviction import conviction
from homily_fund import fund_tag
from homily_regime import market_regime
from homily_refine import daily_refine
import homily_ledger
import homily_alerts

# IBKR holding -> Yahoo symbol: lives in holdings.json so book changes are a
# one-line edit (last synced from live IBKR positions 2026-07-06).
import json as _json
_HERE = os.path.dirname(os.path.abspath(__file__))
HOLDINGS = {k: v for k, v in
            _json.load(open(os.path.join(_HERE, "holdings.json"))).items()
            if not k.startswith("_")}
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
# ETFs (SOXL, MSTR-style proxies) and crypto-beta names (COIN) — out of
# scope per PRD; and anything already in HOLDINGS/WATCH.
UNIVERSE = {
    # megacap tech
    "MSFT":"MSFT","AMZN":"AMZN","META":"META","NFLX":"NFLX","ORCL":"ORCL",
    # semis / AI hardware
    "MU":"MU","QCOM":"QCOM","ARM":"ARM","ANET":"ANET","VRT":"VRT",
    "LRCX":"LRCX","AMAT":"AMAT","KLAC":"KLAC","INTC":"INTC","MRVL":"MRVL",
    # software / growth
    "CRM":"CRM","ADBE":"ADBE","CRWD":"CRWD","PANW":"PANW","NET":"NET",
    "DDOG":"DDOG","SNOW":"SNOW","ZS":"ZS","APP":"APP","SHOP":"SHOP",
    "UBER":"UBER","HOOD":"HOOD","MDB":"MDB",
    # quality diversifiers
    "LLY":"LLY","NVO":"NVO","V":"V","MA":"MA","COST":"COST","JPM":"JPM",
    # HK/China liquid names beyond BABA
    "0700":"0700.HK","3690":"3690.HK","1810":"1810.HK",
    # growth mid-caps — the multi-bagger hunting ground
    "RKLB":"RKLB","ASTS":"ASTS","SOFI":"SOFI","HIMS":"HIMS","DUOL":"DUOL",
    "AXON":"AXON","TOST":"TOST","RBLX":"RBLX","IOT":"IOT","CRDO":"CRDO",
    "TMDX":"TMDX","CAVA":"CAVA","ONON":"ONON","SE":"SE","GRAB":"GRAB",
    "NBIS":"NBIS","ALAB":"ALAB",
}

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


def fmt_row(s, watch=False, young=False):
    c = s.chips
    zone = f"{g(s.add_zone[0])}-{g(s.add_zone[1])}" if s.add_zone else "n/a"
    res = g(c.resistance[0][0]) if c.resistance else "ATH air"
    tag = "†" if watch else ""  # NB: not "*" — unpaired * breaks TG Markdown
    h = s.vol_hole
    vh = (f" · VH {g(h.lower)}-{g(h.upper)}{VH_ARROW[h.status]}" if h else "")
    yg = " · ⚠️too-new, engines not warmed" if young else ""
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
            f"{g(c.last)} — "
            f"add {zone} · POC {g(c.poc)} · res {res} · "
            f"{c.pct_in_profit:.0f}% in profit · wk {s.weekly.circle}/{s.weekly.score} "
            f"({s.weekly.weeks_in_regime}w) · {'mUP' if s.monthly_up else 'mDN'} · "
            f"d{s.candle[0]}{vh}{at}{wh}{yg}")


MIN_HISTORY = 250   # daily bars below this -> engines aren't warmed up


MAX_WORKERS = 4     # #17 / R11: bounded fan-out — a rate-limit ban on the
                    # runner IP would kill EVERY digest, worse than slow.


def _screen_one(item, spy):
    """(tk, result) for one name; result is None on any fetch/engine failure.
    Referenced via the module global fetch_daily so tests can monkeypatch it."""
    tk, sym = item
    try:
        bars = fetch_daily(sym, rng="5y")
        sig = danny_signal(tk, bars)
        return tk, (sig, conviction(sig, bars, spy), len(bars) < MIN_HISTORY)
    except Exception:
        return tk, None


def screen(book, errs, spy):
    """-> list of (DannySignal, Conviction, young), digest-sorted. Fetches fan
    out across a bounded thread pool (network-bound); output is sorted so it is
    identical regardless of completion order. Falls back to a sequential pass
    if the pool itself misbehaves (R11 keeps the sequential path alive)."""
    items = list(book.items())
    try:
        with ThreadPoolExecutor(max_workers=MAX_WORKERS) as ex:
            results = list(ex.map(lambda it: _screen_one(it, spy), items))
    except Exception:
        results = [_screen_one(it, spy) for it in items]
    out = []
    for tk, res in results:
        (out if res is not None else errs).append(res if res is not None else tk)
    out.sort(key=lambda x: (ORDER[x[0].state], x[0].ticker))
    return out


def fmt_rocket(s, c, held, *, fund=fund_tag):
    tag = "" if held else "†"
    top = sorted(c.parts.items(), key=lambda kv: -kv[1])[:2]
    why = ", ".join(f"{k} {v}" for k, v in top)
    size = "≤5% CONVICTION" if c.tier == "CONVICTION" else "≤2% STARTER"
    zone = (f" · add {g(s.add_zone[0])}-{g(s.add_zone[1])}"
            if s.add_zone else "")
    return (f"🚀 <code>{esc(f'{s.ticker:<5}')}</code>{tag} score {c.score} → "
            f"{size} · RS12 {c.rs12:+.0f}pts · ${c.dvol/1e9:.1f}B/d{zone} · "
            f"{esc(why)} · {esc(fund(s.ticker))}")


def render_digest(sigs, disco, proxy, regime, refine, errs, today,
                  *, fund=fund_tag):
    """Pure digest assembly — no network, no clock, no state mutation. All
    the varying inputs are passed in so the exact printed text is a
    deterministic function of them; that is what makes the golden-file test
    (homily_golden.py) possible. build_digest() is the thin IO shell that
    gathers these inputs and calls this. Keep the two behaviourally in
    lock-step: any change to a printed row belongs here."""
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

    lines.append("")
    cur = None
    for s, c, young in sigs:
        if s.state != cur:
            cur = s.state
            lines.append(f"<b>{ICON[cur]} {esc(cur)}</b>")
        lines.append(fmt_row(s, s.ticker in WATCH, young))
        if s.ticker in proxy:
            lines.append(proxy[s.ticker])

    # multi-bagger watch: stringent 5-gate screen across EVERYTHING
    rockets = sorted([(s, c) for s, c, _ in sigs + disco if c.gates_ok],
                     key=lambda x: -x[1].score)
    lines += ["", "<b>🚀 MULTI-BAGGER WATCH (5 hard gates: size, trend, "
              "leader-RS, basis, data)</b>"]
    if rockets:
        lines += [fmt_rocket(s, c, s.ticker in HOLDINGS, fund=fund)
                  for s, c in rockets[:5]]
        lines.append("<i>sizing guide: CONVICTION ≤5% of account · STARTER "
                     "≤2% · hard cap 10%/name incl. existing · add at ⭐ "
                     "zones only</i>")
    else:
        lines.append("no name passes all 5 gates today — that's the point")

    # discovery: new-money setups among names not held (⭐/🔵, plus the
    # promoted 🐳 whale-dip tier — a ⚪ shelf dip being absorbed)
    hits = [(s, y) for s, c, y in disco
            if s.state in ("ACCUMULATE", "BOTTOMING") or whale_dip(s)]
    lines += ["", f"<b>🔎 DISCOVERY — new-money setups ({len(disco)} names "
              "screened, not held)</b>"]
    if hits:
        lines += [fmt_row(s, watch=True, young=y) + f" · {esc(fund(s.ticker))}"
                  for s, y in hits[:8]]
        if len(hits) > 8:
            more = ", ".join(s.ticker for s, _ in hits[8:])
            lines.append(f"…and {len(hits) - 8} more: {esc(more)}")
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
              " 58 names incl. 2021 wrecks) · F:n/m = EDGAR fundamentals"
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
    errs = []
    spy = [b[4] for b in fetch_daily("SPY", rng="5y")]
    sigs = screen({**HOLDINGS, **WATCH}, errs, spy)
    disco = screen({k: v for k, v in UNIVERSE.items() if k not in HOLDINGS},
                   errs, spy)
    try:
        regime = market_regime()
    except Exception:
        regime = None
    # constituent proxy reads for too-new holdings (e.g. DRAM basket)
    proxy = {}
    for tk, members in PROXY_CONSTITUENTS.items():
        if tk in HOLDINGS:
            ps = screen(members, errs, spy)
            reads = " · ".join(f"{esc(p.ticker)} {ICON[p.state]}"
                               for p, _, _ in ps)
            proxy[tk] = f"　↳ <i>constituents proxy:</i> {reads}"
    # Pinned SGT run date (R7) — the ledger idempotency key and the digest
    # date must be the same value on every runner; homily_ledger owns it.
    today = homily_ledger.run_date()
    digest = render_digest(sigs, disco, proxy, regime, daily_refine(), errs,
                           today)
    # #15 state-change alerts: diff today's states against yesterday's ledger
    # BEFORE record() overwrites it, so a quiet day sends no second message.
    alert = ""
    try:
        states = ([homily_ledger.state_of(s, c, s.ticker in HOLDINGS)
                   for s, c, _ in sigs]
                  + [homily_ledger.state_of(s, c, False) for s, c, _ in disco])
        alert = homily_alerts.format_alerts(
            homily_alerts.build_alerts(states, regime, today), today)
    except Exception as e:
        print(f"[alerts] skipped: {e}")
    # #13 signals ledger + snapshot: record what the digest printed today.
    # Non-fatal to the send (the user always gets their digest); any history
    # corruption is caught hard by the validate gate (check [17]) that #16
    # runs BEFORE this step in CI.
    try:
        homily_ledger.record(sigs, disco, regime, today, set(HOLDINGS))
    except Exception as e:
        print(f"[ledger] skipped: {e}")
    return digest, alert


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
    for part in chunks(text):
        try:
            post({"chat_id": chat, "text": part, "parse_mode": "HTML"})
            print("[sent to Telegram]")
        except urllib.error.HTTPError as e:
            # HTML entity-parse failures return 400 — deliver tag-stripped
            # plain text rather than dropping the digest (#34 R4)
            print(f"[HTML send failed: {e.code} "
                  f"{e.read().decode(errors='replace')[:200]}]")
            post({"chat_id": chat, "text": strip_html(part)})
            print("[sent to Telegram — plain-text fallback]")


if __name__ == "__main__":
    digest, alert = build_digest()
    send(digest)
    if alert:                       # #15: only on a state change, never quiet
        send(alert)
