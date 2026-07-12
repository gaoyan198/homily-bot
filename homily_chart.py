#!/usr/bin/env python3
"""
Any-ticker chart CLI (#84) — the Homily card for symbols on demand.
====================================================================

    python3 homily_chart.py NVDA COIN 0700.HK

Fetches 2y+ of bars, runs the FROZEN engines read-only (the exact live
call pattern of daily_run._screen_one — R6: never a reimplementation),
and renders #83's card for any Yahoo-resolvable symbol into one
self-contained zero-JS HTML in the working directory; the path is
printed. Display keys the daily run knows ("0700", "9992") resolve to
their Yahoo symbols; anything else is passed to Yahoo as typed.

R3, deliberately: NOTHING here writes to the ledger or the snapshot — a
chart on demand is context, not a tracked call, and the card wears an
"ad-hoc" banner saying so (validate [47] pins the banner AND greps this
file for ledger writes). Corp-action suspects (#19) keep their banner
too: an ad-hoc chart must not print levels the daily digest would have
suppressed.
"""
import os
import sys

import homily_ledger
from homily_corp import corp_action_bar
from homily_dashboard import CSS, LEGEND, _card_html, E


def chart_page(cards, date):
    """Pure, deterministic: [(state_dict, bars, banner)] + date string ->
    one self-contained HTML document reusing #83's card renderer and CSS
    verbatim. No search script — one to three cards need no filter, and
    the page stays zero-JS (D-36 proper, no relaxation needed here)."""
    body = "".join(_card_html(s, bars, banner=banner)
                   for s, bars, banner in cards)
    return f"""<!DOCTYPE html>
<html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>homily chart — {E(", ".join(s["ticker"] for s, _b, _n in cards))}</title>
<style>{CSS}</style></head><body>
<div class="wrap">
<h1>HOMILY × DANNY <small>— ad-hoc chart · {E(date)}</small></h1>
<p class="legend">{LEGEND}</p>
{body}
<footer>ad-hoc chart — not screened, no ledger history; nothing was
recorded (R3). Danny/Homily colour language on purpose: red = bullish,
yellow = bearish. Approximation of documented behaviour, not their
formulas — levels are context, not advice.</footer>
</div>
</body></html>"""


def _build_one(arg, sym_map, holdings, spy, spy_adj, fetch, danny, conv):
    """One symbol -> (state_dict, bars, banner); the engine calls mirror
    daily_run._screen_one exactly (R6)."""
    tk = arg.upper()
    sym = sym_map.get(tk, tk)
    bars, adj = fetch(sym, rng="5y")
    sig = danny(tk, bars)
    c = conv(sig, bars, spy, adj=adj, spy_adj=spy_adj)
    state = homily_ledger.state_of(sig, c, tk in holdings)
    banner = "ad-hoc — not screened, no ledger history"
    corp = corp_action_bar(bars)
    if corp:
        banner += (f" · ⚠ corp-action suspect bar {corp} — chip levels "
                   "suspect, the daily digest would suppress them (#19)")
    return state, bars, banner


def main(argv):
    if not argv:
        print("usage: python3 homily_chart.py TICKER [TICKER…]")
        return 1
    # IO shell only below: symbol maps + live engines resolved here so the
    # pure chart_page stays fixture-testable without any of them.
    import daily_run
    from homily_data import fetch_series
    from homily_danny import danny_signal
    from homily_conviction import conviction
    sym_map = {**daily_run.WATCH, **daily_run.UNIVERSE, **daily_run.HOLDINGS}
    spy_bars, spy_adj = fetch_series("SPY", rng="5y")
    spy = [b[4] for b in spy_bars]
    cards = []
    for arg in argv:
        try:
            cards.append(_build_one(arg, sym_map, set(daily_run.HOLDINGS),
                                    spy, spy_adj, fetch_series,
                                    danny_signal, conviction))
        except Exception as e:
            print(f"[{arg}] no chart: {e}")
    if not cards:
        return 1
    date = homily_ledger.run_date().isoformat()
    name = "chart_" + "_".join(
        "".join(ch for ch in s["ticker"] if ch.isalnum())
        for s, _b, _n in cards)[:40] + ".html"
    path = os.path.join(os.getcwd(), name)
    with open(path, "w") as f:
        f.write(chart_page(cards, date))
    print(f"wrote {path} ({os.path.getsize(path):,} bytes)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
