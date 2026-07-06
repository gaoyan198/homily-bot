#!/usr/bin/env python3
"""
Daily entrypoint: fetch -> Danny-style composite signal -> auto-refine ->
Telegram digest. Pure stdlib (urllib). GitHub Actions cron (9am SGT = 01:00
UTC); champion state is committed back by the workflow.

Signal semantics follow @dannycheng2022's use of Homily charts (see PRD.md):
accumulate-on-dip guidance anchored on chip support — there is no SELL state.

Env: TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID (if unset -> prints digest, no send).
"""
import os, datetime, urllib.request, urllib.parse
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

ICON = {"ACCUMULATE":"⭐","HOLD":"🟢","PULLBACK":"🟡","CAUTION":"⚪"}
ORDER = {"ACCUMULATE":0,"HOLD":1,"PULLBACK":2,"CAUTION":3}


def g(x):
    return f"{round(x, 2):g}"


def fmt_row(s, watch=False):
    c = s.chips
    zone = f"{g(s.add_zone[0])}-{g(s.add_zone[1])}" if s.add_zone else "n/a"
    res = g(c.resistance[0][0]) if c.resistance else "ATH air"
    tag = "*" if watch else ""
    return (f"{ICON[s.state]} `{s.ticker:<5}`{tag} {g(c.last)} — "
            f"add {zone} · POC {g(c.poc)} · res {res} · "
            f"{c.pct_in_profit:.0f}% in profit · wk {s.weekly.circle}/{s.weekly.score} "
            f"({s.weekly.weeks_in_regime}w) · {'mUP' if s.monthly_up else 'mDN'} · "
            f"d{s.candle[0]}")


def build_digest():
    sigs, errs = [], []
    for tk, sym in {**HOLDINGS, **WATCH}.items():
        try:
            sigs.append((danny_signal(tk, fetch_daily(sym, rng="5y")),
                         tk in WATCH))
        except Exception:
            errs.append(tk)
    sigs.sort(key=lambda x: (ORDER[x[0].state], x[0].ticker))

    lines = [f"*Homily × Danny digest — {datetime.date.today()}*", ""]
    cur = None
    for s, watch in sigs:
        if s.state != cur:
            cur = s.state
            lines.append(f"*{ICON[cur]} {cur}*")
        lines.append(fmt_row(s, watch))
    if errs:
        lines.append(f"⚠️ fetch failed: {', '.join(errs)}")

    champ, chal, oos_chal, oos_def, champ_oos, adopted = daily_refine()
    lines += ["", "_add = chip-support accumulate zone · POC = cost point of"
              " control · res = nearest chip resistance · * = watch-only_",
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
