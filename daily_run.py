#!/usr/bin/env python3
"""
Daily entrypoint: fetch -> signal -> auto-refine -> Telegram digest.
Pure stdlib (urllib). Designed for GitHub Actions cron (9am SGT = 01:00 UTC),
the same key-free/Telegram pattern as sg-housing-bot. State (champion params)
is committed back to the repo by the workflow so refinement accumulates.

Env: TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID (if unset -> prints digest, no send).
"""
import os, json, ssl, urllib.request, urllib.parse, datetime
from homily_clone import homily_circle
from homily_refine import daily_refine

# IBKR holding -> Yahoo symbol
HOLDINGS = {
    "AAPL":"AAPL","AMD":"AMD","AVGO":"AVGO","BABA":"BABA","CSPX":"CSPX.L",
    "GOOG":"GOOG","NOW":"NOW","NVDA":"NVDA","PLTR":"PLTR","RDDT":"RDDT",
    "TSLA":"TSLA","TSM":"TSM","VST":"VST","ZETA":"ZETA","9992":"9992.HK",
}

def fetch_weekly(symbol, rng="1y"):
    url = f"https://query1.finance.yahoo.com/v8/finance/chart/{symbol}?range={rng}&interval=1wk"
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    ctx = ssl.create_default_context()
    with urllib.request.urlopen(req, timeout=20, context=ctx) as r:
        data = json.load(r)
    q = data["chart"]["result"][0]["indicators"]["quote"][0]["close"]
    return [c for c in q if c is not None]

def build_digest():
    rows = []
    for tk, sym in HOLDINGS.items():
        try:
            closes = fetch_weekly(sym)
            if len(closes) < 35:
                rows.append((tk, "n/a", 0, 0)); continue
            s = homily_circle(tk, closes)
            rows.append((tk, s.circle, s.score, s.pct_vs_ma30))
        except Exception as e:
            rows.append((tk, f"ERR", 0, 0))
    order = {"RED":0,"AMBER":1,"WHITE":2,"n/a":3,"ERR":4}
    rows.sort(key=lambda r: (order.get(r[1],9), -r[2]))
    champ, chal, oos_chal, oos_def, champ_oos, adopted = daily_refine()

    icon = {"RED":"🔴","AMBER":"🟡","WHITE":"⚪","n/a":"·","ERR":"⚠️"}
    lines = [f"*Homily digest — {datetime.date.today()}*", ""]
    for tk, c, sc, pct in rows:
        lines.append(f"{icon.get(c,'·')} `{tk:<5}` {c:<5} {sc}/4  ({pct:+.0f}% vs MA30)")
    lines += ["", "*Algo health (auto-refine, OOS-gated):*",
              f"champion `{champ['params']}` since {champ['since']}",
              f"OOS Calmar champ {champ_oos:.2f} / challenger {oos_chal:.2f}"
              f"{'  → ADOPTED' if adopted else ''}",
              "_Reminder: signal = risk flag only; backtest shows it trails buy&hold on return._"]
    return "\n".join(lines)

def send(text):
    tok, chat = os.getenv("TELEGRAM_BOT_TOKEN"), os.getenv("TELEGRAM_CHAT_ID")
    if not (tok and chat):
        print(text); print("\n[no TELEGRAM_* env — printed only]"); return
    url = f"https://api.telegram.org/bot{tok}/sendMessage"
    body = urllib.parse.urlencode({"chat_id": chat, "text": text,
                                   "parse_mode": "Markdown"}).encode()
    urllib.request.urlopen(urllib.request.Request(url, data=body), timeout=20)
    print("[sent to Telegram]")

if __name__ == "__main__":
    send(build_digest())
