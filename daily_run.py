#!/usr/bin/env python3
"""
Daily entrypoint: fetch -> Danny-style composite signal -> auto-refine ->
Telegram digest. Pure stdlib (urllib). GitHub Actions cron (9am SGT = 01:00
UTC); champion state is committed back by the workflow.

Signal semantics follow @dannycheng2022's use of Homily charts (see PRD.md):
accumulate-on-dip guidance anchored on chip support — there is no SELL state.

Env: TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID (if unset -> prints digest, no send).
"""
import os, datetime, urllib.request, urllib.parse, urllib.error
from homily_data import fetch_daily
from homily_danny import danny_signal
from homily_refine import daily_refine

# IBKR holding -> Yahoo symbol
HOLDINGS = {
    "AAPL":"AAPL","AMD":"AMD","AVGO":"AVGO","BABA":"BABA","CSPX":"CSPX.L",
    "GOOG":"GOOG","NOW":"NOW","NVDA":"NVDA","PLTR":"PLTR","RDDT":"RDDT",
    "TSLA":"TSLA","TSM":"TSM","VST":"VST","ZETA":"ZETA","9992":"9992.HK",
}
# Danny-core names not (yet) held — charted anyway, week after week
WATCH = {"ASML":"ASML"}

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
}

ICON = {"ACCUMULATE":"⭐","HOLD":"🟢","PULLBACK":"🟡","BOTTOMING":"🔵",
        "CAUTION":"⚪"}
ORDER = {"ACCUMULATE":0,"HOLD":1,"PULLBACK":2,"BOTTOMING":3,"CAUTION":4}
VH_ARROW = {"BREAKOUT":"↑","BREAKDOWN":"↓","INSIDE":"◻"}


def g(x):
    return f"{round(x, 2):g}"


def fmt_row(s, watch=False):
    c = s.chips
    zone = f"{g(s.add_zone[0])}-{g(s.add_zone[1])}" if s.add_zone else "n/a"
    res = g(c.resistance[0][0]) if c.resistance else "ATH air"
    tag = "†" if watch else ""  # NB: not "*" — unpaired * breaks TG Markdown
    h = s.vol_hole
    vh = (f" · VH {g(h.lower)}-{g(h.upper)}{VH_ARROW[h.status]}" if h else "")
    return (f"{ICON[s.state]} `{s.ticker:<5}`{tag} {g(c.last)} — "
            f"add {zone} · POC {g(c.poc)} · res {res} · "
            f"{c.pct_in_profit:.0f}% in profit · wk {s.weekly.circle}/{s.weekly.score} "
            f"({s.weekly.weeks_in_regime}w) · {'mUP' if s.monthly_up else 'mDN'} · "
            f"d{s.candle[0]}{vh}")


def screen(book, errs):
    sigs = []
    for tk, sym in book.items():
        try:
            sigs.append(danny_signal(tk, fetch_daily(sym, rng="5y")))
        except Exception:
            errs.append(tk)
    sigs.sort(key=lambda s: (ORDER[s.state], s.ticker))
    return sigs


def build_digest():
    errs = []
    sigs = screen({**HOLDINGS, **WATCH}, errs)
    disco = screen(UNIVERSE, errs)

    lines = [f"*Homily × Danny digest — {datetime.date.today()}*", ""]
    cur = None
    for s in sigs:
        if s.state != cur:
            cur = s.state
            lines.append(f"*{ICON[cur]} {cur}*")
        lines.append(fmt_row(s, s.ticker in WATCH))

    # discovery: new-money setups among names not held (⭐/🔵 only)
    hits = [s for s in disco if s.state in ("ACCUMULATE", "BOTTOMING")]
    lines += ["", f"*🔎 DISCOVERY — new-money setups ({len(UNIVERSE)} names "
              "screened, not held)*"]
    if hits:
        lines += [fmt_row(s, watch=True) for s in hits[:8]]
        if len(hits) > 8:
            more = ", ".join(s.ticker for s in hits[8:])
            lines.append(f"…and {len(hits) - 8} more: {more}")
    else:
        lines.append("no ⭐/🔵 setups in the universe today")
    if errs:
        lines.append(f"⚠️ fetch failed: {', '.join(errs)}")

    champ, chal, oos_chal, oos_def, champ_oos, adopted = daily_refine()
    lines += ["", "_add = chip-support accumulate zone · POC = cost point of"
              " control · res = nearest chip resistance · VH = volatility"
              " hole zone (↑ broke above = bottoming confirm, ↓ broke below"
              " = topping risk, ◻ inside) · † = not held_",
              "", "*Algo health (auto-refine, OOS-gated):*",
              f"champion `{champ['params']}` since {champ['since']}",
              f"OOS Calmar champ {champ_oos:.2f} / challenger {oos_chal:.2f}"
              f"{'  → ADOPTED' if adopted else ''}",
              "_Reminder: approximation of Danny/Homily behaviour, not their "
              "proprietary formulas. 5y backtest: waiting for ⭐ zones got a "
              "WORSE avg cost than immediate DCA on every name tested — treat "
              "levels as context, not a reason to sit in cash. CAUTION = "
              "pause adds, never a mechanical sell._"]
    return "\n".join(lines)


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
            post({"chat_id": chat, "text": part, "parse_mode": "Markdown"})
            print("[sent to Telegram]")
        except urllib.error.HTTPError as e:
            # Markdown entity-parse failures return 400 — deliver plain
            # rather than dropping the digest
            print(f"[Markdown send failed: {e.code} "
                  f"{e.read().decode(errors='replace')[:200]}]")
            post({"chat_id": chat, "text": part})
            print("[sent to Telegram — plain-text fallback]")


if __name__ == "__main__":
    send(build_digest())
