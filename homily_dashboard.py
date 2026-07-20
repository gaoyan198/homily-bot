#!/usr/bin/env python3
"""
Danny-style chart board (#83; supersedes the #36 levels-band cards)
====================================================================

One self-contained HTML file per board, dark, searchable. Two boards from
one renderer (D-83 §search):

* the SMALL board — `docs/dashboard.html`, held + actionable names only,
  committed by the workflow (R8) and sent via sendDocument; ≤300 KB so the
  nightly diff stays reviewable;
* the FULL board — every screened name, written to a temp path and SENT
  each night, never committed (~1.4 MB/day would put ~350 MB/yr into git
  history; the Telegram chat is its archive).

Each card speaks the Homily/Danny chart language the methodology is stated
in (HOW_TO_READ.md is the manual): daily candles coloured by the frozen
engine's own `daily_candle()` on close prefixes — RED = BULLISH, yellow =
bearish, the Chinese convention, legend pinned on the page for exactly
that reason — plus the chip histogram split at the last close (POC bin
emphasized), the volatility-hole zone from `find_hole()`, the add-zone
band, POC/support/resistance on a collision-resolved label rail, and the
52-week circle ribbon. Engines frozen (§0): every mark is an engine
output; the histogram backdrop and ribbon REUSE homily_png's helpers
(share, don't duplicate).

Search: a ticker-chip anchor index works with zero JS in any renderer;
the sticky filter input is a ~20-line inline-vanilla-JS enhancement — the
one deliberate, recorded relaxation of D-36's zero-JS rule (self-contained
/ no external assets / offline all still hold; validate [33] now asserts
scripts are inline-only). Palette hexes are D-83-normative (validated
against the dark surface).

The render stays a pure function — (snapshot, ledger rows, refine rows,
bars_map) → HTML — which is what check [33] pins. bars arrive in-memory
from daily_run's screen (snapshot.json does NOT grow a bars section; #75
schema unchanged). No bars for a name → the card degrades to its facts
row, never crashes. Sections below the cards are unchanged from #36:
ledger state heatmap, alerts timeline (homily_alerts.diff_alerts reused
verbatim), refine OOS chart.
"""
import os
import json
import html
import tempfile

import homily_ledger
import homily_alerts
from homily_danny import daily_candle
from homily_vol import find_hole
from homily_png import _display_bins, _ribbon_circles
import homily_fandist
from homily_pullback_backtest import dip_age, DIP_MEDIAN_D, DIP_P90_D
from homily_ribbon_backtest import RED_MEDIAN_RUN_W

HERE = os.path.dirname(os.path.abspath(__file__))
DASHBOARD = os.path.join(HERE, "docs", "dashboard.html")
BOARD_FULL = os.path.join(tempfile.gettempdir(), "homily_board_full.html")
REFINE_LOG = os.path.join(HERE, "homily_refine_log.csv")

# D-83 normative palette (validated on the dark surface 2026-07-12).
BULL = "#e5484d"      # red candle = BULLISH — Danny/Homily colour language
BEAR = "#b8890d"      # yellow candle = bearish
NEUT = "#4a5264"
PROFIT = "#25a897"    # chips in profit / support / add zone
TRAPPED = "#6d83d1"   # trapped chips / resistance
POC = "#d47114"
VH = "#8b7ff5"
INK, MUTED, GRID = "#dde3ee", "#7e8798", "#1c2333"
SURFACE, PANEL, EDGE = "#0c1017", "#111722", "#212a3a"
RIB = {"RED": BULL, "AMBER": BEAR, "WHITE": "#aeb6c4"}
STATE = {"ACCUMULATE": (PROFIT, "⭐ ACCUMULATE"),
         "HOLD": ("#7ba05b", "🟢 HOLD"),
         "PULLBACK": (BEAR, "🟡 PULLBACK"),
         "BOTTOMING": (VH, "🔵 BOTTOMING"),
         "CAUTION": ("#8b93a3", "⚪ CAUTION")}
ORDER = {"ACCUMULATE": 0, "BOTTOMING": 1, "PULLBACK": 2, "HOLD": 3,
         "CAUTION": 4}

VIEW = 120            # ~6 months of daily candles per card
MIN_BARS = 30         # fewer -> facts row only, no chart
W, PH, H = 780, 286, 352
PL, PR = 8, 556       # price panel x-range
HX0, HX1 = 560, 688   # chip-histogram panel
AX = 694              # right label rail
RIBY0, RIBY1 = 322, 338
E = lambda x: html.escape(str(x), quote=True)


# --- card geometry helpers ---------------------------------------------------
def _yscale(view, levels):
    lo = min(b[3] for b in view)
    hi = max(b[2] for b in view)
    for p in levels:
        if p and lo * 0.85 < p < hi * 1.15:
            lo, hi = min(lo, p), max(hi, p)
    span = (hi - lo) or lo * 0.01 or 1.0
    lo, hi = lo - span * 0.05, hi + span * 0.05
    return (lambda p: 10 + (hi - p) / (hi - lo) * (PH - 20)), lo, hi


def _ticks(lo, hi, n=4):
    raw = (hi - lo) / n
    mag = 10 ** len(str(int(raw))) / 10
    step = max(1, round(raw / mag)) * mag
    t, out = (int(lo / step) + 1) * step, []
    while t < hi:
        out.append(t)
        t += step
    return out


def _fmt(v):
    return f"{v:.0f}" if v >= 500 else f"{v:.1f}"


def _card_svg(s, bars):
    """The Danny card picture. Every mark is a frozen-engine output; the
    right-hand label rail is collision-resolved (labels nudged ≥13px apart,
    grid ticks yield) — hand-placed labels were the #36 board's defect."""
    view = bars[-VIEW:]
    n = len(view)
    colors = [daily_candle([b[4] for b in bars[:len(bars) - n + i + 1]])
              for i in range(n)]
    y, lo, hi = _yscale(view, [s.get("zone_lo"), s.get("zone_hi"), s["poc"]])
    step = (PR - PL) / n
    x = lambda i: PL + i * step + step / 2
    close = s["close"]
    p = [f'<rect width="{W}" height="{H}" fill="{PANEL}" rx="6"/>']
    axis = []                                      # (y, text, colour)

    ticks = _ticks(lo, hi)
    for t in ticks:
        p.append(f'<line x1="{PL}" x2="{HX1}" y1="{y(t):.1f}" '
                 f'y2="{y(t):.1f}" stroke="{GRID}"/>')
    last_m = view[0][0].month
    for i, b in enumerate(view):
        if b[0].month != last_m:
            last_m = b[0].month
            p.append(f'<text x="{x(i):.0f}" y="310" font-size="9" '
                     f'fill="{MUTED}" text-anchor="middle">'
                     f'{b[0].strftime("%b")}</text>')

    hole = find_hole(bars)
    if hole:
        x0 = max(PL, x(n - min(hole.age, n)) - step / 2)
        yu, yl = y(hole.upper), y(hole.lower)
        p.append(f'<rect x="{x0:.1f}" y="{yu:.1f}" width="{PR - x0:.1f}" '
                 f'height="{yl - yu:.1f}" fill="{VH}" fill-opacity="0.12"/>')
        for yy in (yu, yl):
            p.append(f'<line x1="{x0:.1f}" x2="{PR}" y1="{yy:.1f}" '
                     f'y2="{yy:.1f}" stroke="{VH}" stroke-width="1" '
                     'stroke-dasharray="2 3"/>')
        lbl = {"BREAKOUT": "vh breakout ↑", "BREAKDOWN": "vh breakdown ↓",
               "INSIDE": "vh zone"}[hole.status]
        p.append(f'<text x="{x0 + 4:.1f}" y="{yu - 4:.1f}" font-size="10" '
                 f'fill="{VH}">{lbl}</text>')

    # levels can sit off-scale when a card is rebuilt from a stale snapshot
    # against fresh bars (local __main__ path) — skip, never draw garbage
    if s.get("zone_lo") is not None and s["zone_hi"] > lo and s["zone_lo"] < hi:
        zl = min(y(max(s["zone_lo"], lo)), PH - 10.0)
        zh = max(y(min(s["zone_hi"], hi)), 10.0)
        p.append(f'<rect x="{PL}" y="{zh:.1f}" width="{PR - PL}" '
                 f'height="{max(zl - zh, 1.0):.1f}" fill="{PROFIT}" '
                 'fill-opacity="0.13"/>')
        zf = lambda v: f"{v:.0f}" if v >= 100 else f"{v:.1f}"
        axis.append(((zl + zh) / 2,
                     f'add {zf(s["zone_lo"])}–{zf(s["zone_hi"])}', PROFIT))

    blo, bwidth, weights = _display_bins(bars)
    mx = max(weights) or 1
    poc_bin = weights.index(mx)
    bin_h = max(1.6, (PH - 20) / ((hi - lo) / bwidth) - 0.6)
    for j, wt in enumerate(weights):
        pr = blo + (j + 0.5) * bwidth
        # sub-0.5%-of-max bins are invisible ink — skipping them is ~30% of
        # the card's bytes (size budget, D-83)
        if not lo < pr < hi or wt / mx < 0.005:
            continue
        col, op = ((POC, 1.0) if j == poc_bin else
                   (PROFIT, 0.55) if pr <= close else (TRAPPED, 0.55))
        p.append(f'<rect x="{HX0}" y="{y(pr) - bin_h / 2:.1f}" '
                 f'width="{(wt / mx) * (HX1 - HX0):.1f}" '
                 f'height="{bin_h:.1f}" fill="{col}" fill-opacity="{op}"/>')

    if lo < s["poc"] < hi:
        p.append(f'<line x1="{PL}" x2="{HX1}" y1="{y(s["poc"]):.1f}" '
                 f'y2="{y(s["poc"]):.1f}" stroke="{POC}" stroke-width="1.2" '
                 'stroke-dasharray="5 3"/>')
        axis.append((y(s["poc"]), f'POC {_fmt(s["poc"])}', POC))
    for peaks, col, tag in ((s.get("support") or [], PROFIT, "sup"),
                            (s.get("resistance") or [], TRAPPED, "res")):
        for pr, _wt in peaks[:1]:
            if not lo < pr < hi or abs(pr - s["poc"]) / pr < 0.015:
                continue
            p.append(f'<line x1="{PL}" x2="{HX1}" y1="{y(pr):.1f}" '
                     f'y2="{y(pr):.1f}" stroke="{col}" stroke-width="1" '
                     'stroke-dasharray="3 4"/>')
            axis.append((y(pr), f'{tag} {_fmt(pr)}', col))

    axis.sort()
    placed = []
    for yy, txt, col in axis:
        if placed and yy - placed[-1][0] < 13:
            yy = placed[-1][0] + 13
        placed.append((min(max(yy, 14.0), PH - 4), txt, col))
    for yy, txt, col in placed:
        p.append(f'<text x="{AX}" y="{yy + 3:.1f}" font-size="10" '
                 f'fill="{col}">{txt}</text>')
    for t in ticks:
        if all(abs(y(t) - yy) >= 12 for yy, _t, _c in placed):
            p.append(f'<text x="{AX}" y="{y(t) + 3:.1f}" font-size="10" '
                     f'fill="{MUTED}">{t:g}</text>')

    for col, key in ((BULL, "RED"), (BEAR, "YELLOW"), (NEUT, "NEUTRAL")):
        wick, bodies = [], []
        bw = step * 0.62
        for i, b in enumerate(view):
            if colors[i] != key:
                continue
            _d, o, hh, ll, c, _v = b
            wick.append(f'M{x(i):.1f} {y(hh):.1f}V{y(ll):.1f}')
            top, bot = max(o, c), min(o, c)
            bodies.append(f'<rect x="{x(i) - bw / 2:.1f}" y="{y(top):.1f}" '
                          f'width="{bw:.1f}" '
                          f'height="{max(1.0, y(bot) - y(top)):.1f}"/>')
        if wick:
            p.append(f'<path d="{"".join(wick)}" stroke="{col}" '
                     'stroke-width="1" fill="none" stroke-opacity="0.75"/>')
            p.append(f'<g fill="{col}">{"".join(bodies)}</g>')

    if s.get("whale"):
        p.append(f'<text x="{x(n - 3):.0f}" '
                 f'y="{y(min(b[3] for b in view[-10:])) + 16:.1f}" '
                 'font-size="13" text-anchor="middle">🐳</text>')

    circles = _ribbon_circles(s["ticker"], bars)
    if circles:
        rw = (PR - PL) / len(circles)
        for i, c in enumerate(circles):
            p.append(f'<rect x="{PL + i * rw:.1f}" y="{RIBY0}" '
                     f'width="{max(rw - 1.2, 2):.1f}" '
                     f'height="{RIBY1 - RIBY0}" fill="{RIB.get(c, GRID)}"'
                     + (' fill-opacity="0.45"' if c == "WHITE" else "")
                     + "/>")
    p.append(f'<text x="{HX0}" y="{RIBY1 - 4}" font-size="10" '
             f'fill="{MUTED}">wk circle · {E(s["wk_circle"])} '
             f'{E(s["wk_weeks"])}w · med run {RED_MEDIAN_RUN_W}w</text>')
    return (f'<svg width="{W}" height="{H}" viewBox="0 0 {W} {H}" '
            f'xmlns="http://www.w3.org/2000/svg" role="img" '
            f'aria-label="{E(s["ticker"])} daily chart">{"".join(p)}</svg>')


# --- facts row + card shell --------------------------------------------------
def _chip(txt, col=None):
    st = f' style="color:{col};border-color:{col}55"' if col else ""
    return f'<span class="chip"{st}>{txt}</span>'


def _card_html(s, bars, banner=None, charted=True):
    col, label = STATE.get(s["state"], ("#8b93a3", s["state"]))
    chips = [_chip(f'close <b>{E(s["close"])}</b>')]
    if s.get("zone_lo") is not None:
        chips.append(_chip(f'add {E(s["zone_lo"])}–{E(s["zone_hi"])}',
                           PROFIT))
    chips.append(_chip(f'POC {_fmt(s["poc"])}', POC))
    chips.append(_chip(f'{E(s["pct_in_profit"])}% chips in profit'))
    if bars and len(bars) >= MIN_BARS and s["wk_circle"] == "RED":
        dip = dip_age([b[4] for b in bars])
        if dip:
            chips.append(_chip(f'dip d{dip} (med {DIP_MEDIAN_D}d · '
                               f'p90 {DIP_P90_D}d)', BEAR))
    if s.get("vh_status"):
        chips.append(_chip(f'VH {E(s["vh_status"])}', VH))
    if s.get("whale"):
        chips.append(_chip("🐳 whale footprint", TRAPPED))
    chips += [_chip(f'RS12 {E(s.get("rs12", "—"))}'),
              _chip(f'conv {E(s["conv_score"])}'),
              _chip(E(s.get("ftag") or "F:—"))]
    if s.get("book_pct") is not None:
        chips.append(_chip(f'{E(s["book_pct"])}% of book'))
    if s.get("cap_note"):
        chips.append(_chip(f'⚠️ {E(s["cap_note"])}', BEAR))
    # #103: the measured forward FAN for this exact confluence — median
    # with p25/p75 and p10 side by side, n always shown, min-n floor and
    # construction-date caveat inside homily_fandist. Never a target.
    chips += [_chip(E(t)) for t in
              homily_fandist.fan_chips(homily_fandist.row_key(s))]
    note = ("held" if s.get("held") else "🔎 discovery")
    if not charted:
        # committed-board size budget (D-83 / PRD §8.5 2026-07-12): the
        # small board charts held names only; everyone else keeps a
        # searchable facts card and their chart lives on the full board
        chart = ('<p class="nochart">chart on the nightly full board — '
                 'the committed board keeps charts to held names</p>')
    elif bars and len(bars) >= MIN_BARS:
        chart = _card_svg(s, bars)
    else:
        chart = ('<p class="nochart">chart unavailable — no bars in this '
                 'run (levels above are from the morning snapshot)</p>')
    ban = f'<p class="banner">{E(banner)}</p>' if banner else ""
    return (f'<section class="card" id="{E(s["ticker"])}" '
            f'data-tk="{E(s["ticker"])}">'
            f'<header><span class="tk">{E(s["ticker"])}</span>'
            f'<span class="pill" style="color:{col};border-color:{col}">'
            f'{label}</span><span class="note">{note}</span></header>{ban}'
            f'<div class="chips">{"".join(chips)}</div>'
            f'<div class="chartwrap">{chart}</div></section>')


def _actionable(s):
    """Small-board card set: mirrors select_charts' rule — ⭐/🔵, or a dip
    that reached its add zone (the 🎯 set)."""
    return (s["state"] in ("ACCUMULATE", "BOTTOMING")
            or (s.get("zone_lo") is not None
                and s["close"] <= s["zone_hi"]))


def _cards_and_index(snap, bars_map, full):
    rows = list(snap.get("holdings", [])) + [
        s for s in snap.get("discovery", [])
        if full or _actionable(s)]
    rows.sort(key=lambda s: (not s.get("held"),
                             ORDER.get(s["state"], 9), s["ticker"]))
    bm = bars_map or {}
    cards = "".join(_card_html(s, bm.get(s["ticker"]),
                               charted=full or bool(s.get("held")))
                    for s in rows)
    icon = {k: v[1].split()[0] for k, v in STATE.items()}
    idx = "".join(
        f'<a class="idx" href="#{E(s["ticker"])}" data-tk="{E(s["ticker"])}" '
        f'style="border-color:{STATE.get(s["state"], ("#8b93a3",))[0]}55">'
        f'{icon.get(s["state"], "")} {E(s["ticker"])}</a>'
        for s in rows)
    return cards, idx, len(rows)


_SEARCH_JS = """<script>
(function () {
  var q = document.getElementById("q"), nohit = document.getElementById("nohit");
  if (!q) return;
  var items = [].slice.call(document.querySelectorAll("[data-tk]"));
  q.addEventListener("input", function () {
    var s = q.value.trim().toUpperCase(), hits = 0;
    items.forEach(function (el) {
      var hit = !s || el.getAttribute("data-tk").indexOf(s) === 0;
      el.style.display = hit ? "" : "none";
      if (hit && el.tagName === "SECTION") hits++;
    });
    nohit.style.display = s && !hits ? "block" : "none";
  });
})();
</script>"""


# --- sections carried over from the #36 board (ledger memory) ----------------
HEAT = {"ACCUMULATE": PROFIT, "HOLD": "#7ba05b", "PULLBACK": BEAR,
        "BOTTOMING": VH, "CAUTION": NEUT}


def _heatmap(rows):
    dates = sorted({r["date"] for r in rows})
    tickers = sorted({r["ticker"] for r in rows})
    state = {(r["date"], r["ticker"]): r["state"] for r in rows}
    cw, ch, lx = 16, 14, 52
    w = lx + len(dates) * cw + 8
    h = 18 + len(tickers) * ch
    parts = []
    for j, d in enumerate(dates):
        if j == 0 or d[8:] == "01" or j % 5 == 0:
            parts.append(f'<text x="{lx + j * cw}" y="12" font-size="9" '
                         f'fill="{MUTED}">{E(d[5:])}</text>')
    for i, tk in enumerate(tickers):
        yy = 18 + i * ch
        parts.append(f'<text x="0" y="{yy + 10}" font-size="10" '
                     f'fill="{INK}" font-family="monospace">{E(tk)}</text>')
        for j, d in enumerate(dates):
            st = state.get((d, tk))
            if st is None:
                continue
            parts.append(f'<rect x="{lx + j * cw}" y="{yy}" '
                         f'width="{cw - 2}" height="{ch - 2}" '
                         f'fill="{HEAT.get(st, EDGE)}">'
                         f'<title>{E(d)} {E(tk)} {E(st)}</title></rect>')
    return (f'<svg width="{w}" height="{h}" viewBox="0 0 {w} {h}" '
            f'xmlns="http://www.w3.org/2000/svg">'
            f'<title>ledger state history</title>{"".join(parts)}</svg>')


def _timeline(rows):
    """Every #15-style alert ever, reconstructed: homily_alerts.diff_alerts
    REUSED verbatim over consecutive ledger dates (regime flips aren't in
    ledger rows — noted in the section header)."""
    dates = sorted({r["date"] for r in rows})
    by_date = {d: [r for r in rows if r["date"] == d] for d in dates}
    out = []
    for prev_d, cur_d in zip(dates, dates[1:]):
        for ln in homily_alerts.diff_alerts(by_date[cur_d], None,
                                            by_date[prev_d], None):
            out.append((cur_d, ln))
    out.reverse()                                        # newest first
    if not out:
        return "<p>no transitions in the ledger yet — quiet tape.</p>"
    return ("<ul>" + "".join(f"<li><code>{E(d)}</code> {E(ln)}</li>"
                             for d, ln in out) + "</ul>")


def _refine_chart(refine_rows):
    rows = [r for r in refine_rows if r.get("champ_oos")]
    if len(rows) < 2:
        return "<p>refine log too short for a chart.</p>"
    w, h, pad = 640, 120, 10
    vals = [float(r["champ_oos"]) for r in rows] \
        + [float(r["challenger_oos"]) for r in rows]
    lo, hi = min(vals), max(vals)
    span = (hi - lo) or 1.0
    y = lambda v: h - pad - (v - lo) / span * (h - 2 * pad)
    step = (w - 2 * pad) / (len(rows) - 1)
    line = lambda k, col: (f'<polyline fill="none" stroke="{col}" '
                           'stroke-width="2" points="'
                           + " ".join(f"{pad + i * step:.1f},"
                                      f"{y(float(r[k])):.1f}"
                                      for i, r in enumerate(rows))
                           + f'"><title>{k}</title></polyline>')
    dots = "".join(
        f'<circle cx="{pad + i * step:.1f}" '
        f'cy="{y(float(r["champ_oos"])):.1f}" r="4" fill="{POC}">'
        f'<title>{E(r["date"])} ADOPTED {E(r["champion"])}</title></circle>'
        for i, r in enumerate(rows) if r.get("adopted") == "True")
    return (f'<svg width="{w}" height="{h}" viewBox="0 0 {w} {h}" '
            f'xmlns="http://www.w3.org/2000/svg">'
            f'<title>champion vs challenger OOS Calmar</title>'
            + line("champ_oos", TRAPPED) + line("challenger_oos", MUTED)
            + dots + "</svg>"
            + "<p><small>blue champion · grey challenger · orange dot = "
              "challenger adopted (OOS-gated)</small></p>")


# --- the page ----------------------------------------------------------------
# Legend + CSS are module constants so #84's single-card CLI page reuses
# them verbatim — one visual language, zero duplicated styling.
LEGEND = (f'<span class="sw" style="background:{BULL}"></span> red candle '
          f'= <b>bullish</b> &nbsp;<span class="sw" style="background:'
          f'{BEAR}"></span> yellow = bearish &nbsp;<span class="sw" '
          f'style="background:{NEUT}"></span> neutral &nbsp;·&nbsp; '
          f'chips: <span class="sw" style="background:{PROFIT}"></span> '
          f'in profit <span class="sw" style="background:{TRAPPED}">'
          f'</span> trapped <span class="sw" style="background:{POC}">'
          f'</span> POC &nbsp;·&nbsp; <span class="sw" style="background:'
          f'{VH}"></span> volatility-hole zone &nbsp;·&nbsp; '
          'manual: HOW_TO_READ.md')


CSS = f"""body{{background:{SURFACE};color:{INK};margin:0;
  font:14px/1.5 ui-monospace,"SF Mono",Menlo,Consolas,monospace}}
.wrap{{max-width:880px;margin:0 auto;padding:16px 12px 40px}}
h1{{font-size:17px;letter-spacing:.1em;margin:0}}
h1 small{{color:{MUTED};font-weight:400;letter-spacing:0}}
h2{{margin:22px 0 6px;font-size:15px}}
.sub{{color:{MUTED};font-size:12px;margin:6px 0 2px}}
.legend{{font-size:12px;color:{MUTED};margin:10px 0 0;line-height:1.9}}
.sw{{display:inline-block;width:10px;height:10px;border-radius:2px;
  vertical-align:-1px}}
.searchbar{{position:sticky;top:0;z-index:5;background:{SURFACE}ee;
  padding:10px 0 8px;border-bottom:1px solid {EDGE};margin:8px 0 14px}}
.searchbar input{{width:100%;box-sizing:border-box;background:{PANEL};
  border:1px solid {EDGE};border-radius:6px;color:{INK};padding:8px 12px;
  font:14px ui-monospace,"SF Mono",Menlo,monospace;letter-spacing:.06em}}
.searchbar input::placeholder{{color:{MUTED}}}
.searchbar input:focus{{outline:2px solid {PROFIT}66;border-color:{PROFIT}}}
.idxrow{{display:flex;flex-wrap:wrap;gap:6px;margin-top:8px}}
.idx{{border:1px solid;border-radius:999px;padding:1px 10px;font-size:12px;
  color:{INK};text-decoration:none}}
@media (max-width:640px){{
.idxrow{{flex-wrap:nowrap;overflow-x:auto;-webkit-overflow-scrolling:touch;
  scrollbar-width:none;padding-bottom:2px}}
.idxrow::-webkit-scrollbar{{display:none}}
.idx{{flex:0 0 auto}}
}}
.nohit{{display:none;color:{MUTED};font-size:13px;padding:14px 0}}
.card{{background:{PANEL};border:1px solid {EDGE};border-radius:8px;
  padding:12px 12px 6px;margin:0 0 16px}}
.card header{{display:flex;align-items:baseline;gap:12px;flex-wrap:wrap}}
.tk{{font-size:22px;font-weight:700;letter-spacing:.06em}}
.pill{{border:1px solid;border-radius:999px;padding:1px 10px;font-size:12px}}
.note{{color:{MUTED};font-size:12px;margin-left:auto}}
.banner{{color:{BEAR};font-size:12px;margin:6px 0 0}}
.chips{{display:flex;flex-wrap:wrap;gap:6px;margin:8px 0 10px}}
.chip{{border:1px solid {EDGE};border-radius:4px;padding:1px 7px;
  font-size:11.5px;color:{MUTED};font-variant-numeric:tabular-nums}}
.chip b{{color:{INK}}}
.chartwrap{{overflow-x:auto}}
.chartwrap svg{{max-width:100%;height:auto}}
.nochart{{color:{MUTED};font-size:12px}}
.wrapx{{overflow-x:auto}}
table{{border-collapse:collapse}} td,th{{padding:2px 8px;text-align:left;
  border-bottom:1px solid {EDGE}}}
code{{color:{INK}}}
footer{{color:{MUTED};font-size:11.5px;border-top:1px solid {EDGE};
  padding-top:12px;margin-top:18px;line-height:1.7}}
ul{{padding-left:18px}}
a{{color:{TRAPPED}}}
"""


def render(snap, rows, refine_rows, bars_map=None, full=False):
    """Pure, deterministic: snapshot dict + ledger rows + refine rows (+
    in-memory bars) -> the full HTML document string."""
    reg = snap.get("regime") or {}
    ricon = {"BULL": "🐂", "BEAR": "🐻",
             "MIXED": "⚖️"}.get(reg.get("label"), "⚖️")
    cov = snap.get("coverage") or {}
    cards, idx, ncards = _cards_and_index(snap, bars_map, full)
    disco = "".join(
        f'<tr><td>{STATE.get(s["state"], ("", ""))[1].split()[0]} '
        f'{E(s["ticker"])}</td>'
        f'<td>{E(s["state"])}</td><td>{E(s["close"])}</td>'
        f'<td>{E(s.get("rs12", ""))}</td><td>{E(s.get("ftag") or "")}</td></tr>'
        for s in snap.get("discovery", [])
        if s["state"] in ("ACCUMULATE", "BOTTOMING"))
    buyday = ""
    if snap.get("buyday"):
        b = snap["buyday"]
        orders = "".join(f"<li><code>BUY {E(n)} {E(tk)}</code> "
                         f"(~${n * px:,.0f}) {E(note)}</li>"
                         for tk, n, px, note in b.get("orders", []))
        buyday = (f'<h2>🛒 buy day ({E(b.get("mode"))})</h2><ul>{orders}</ul>'
                  f'<p>budget ${b.get("budget", 0):,.0f} · leftover '
                  f'${b.get("leftover", 0):,.0f} · '
                  '<i>printed, never placed — §7 stands</i></p>')
    scope = ("every screened name" if full
             else "held + actionable — the full board arrives nightly by "
                  "document; any other symbol: python3 homily_chart.py TICKER")
    legend = LEGEND
    return f"""<!DOCTYPE html>
<html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>homily board {E(snap.get("date", ""))}</title>
<style>
{CSS}
</style></head><body>
<div class="wrap">
<h1>HOMILY × DANNY <small>— board · {E(snap.get("date", ""))}</small></h1>
<p class="sub">{ricon} <b>{E(reg.get("label", "regime unavailable"))}</b>
 <i>{E(reg.get("action", ""))}</i></p>
<p class="sub">ledger coverage: {E(cov.get("have", "—"))}/{E(cov.get(
    "expected", "—"))} weekday runs ({E(cov.get("pct", "—"))}%)
{("· holes: " + E(", ".join(cov["missing"]))) if cov.get("missing") else ""}
 · {ncards} cards ({E(scope)})</p>
<p class="legend">{legend}</p>
<div class="searchbar">
<input id="q" type="search" placeholder="search ticker — e.g. NVDA"
 aria-label="search ticker">
<div class="idxrow" id="idx">{idx}</div>
</div>
<p class="nohit" id="nohit">no card for that ticker on this board —
any name on demand: <code>python3 homily_chart.py TICKER</code>, or add it
to WATCH and it appears tomorrow.</p>
{buyday}
{cards}
<h2>🔎 discovery (⭐/🔵 only)</h2>
<div class="wrapx"><table><tr><th></th><th>state</th><th>close</th>
<th>RS12</th><th>F</th></tr>{disco or
    '<tr><td colspan="5">none today</td></tr>'}
</table></div>
<h2>ledger state history</h2><div class="wrapx">{_heatmap(rows)}</div>
<h2>alerts timeline (reconstructed from ledger diffs; regime flips not
recorded per-row)</h2>{_timeline(rows)}
<h2>auto-refine, out-of-sample</h2>{_refine_chart(refine_rows)}
<footer>Danny/Homily colour language on purpose: red = bullish, yellow =
bearish (inverse of Western charts). generated {E(snap.get("generated_utc",
""))} · self-contained, no external assets, inline script only ·
approximation of Danny/Homily behaviour, not their formulas — levels are
context, not advice.</footer>
</div>
{_SEARCH_JS}
</body></html>"""


def _read_refine(path=REFINE_LOG):
    """The refine log's champion column is an unquoted dict with commas in
    it, so csv splitting is positional from both ends: date first, then the
    four trailing fields; everything between is the champion string."""
    if not os.path.exists(path):
        return []
    out = []
    with open(path) as f:
        for ln in f.read().splitlines()[1:]:
            parts = ln.split(",")
            if len(parts) < 6:
                continue
            out.append({"date": parts[0],
                        "champion": ",".join(parts[1:-4]),
                        "champ_oos": parts[-4], "challenger_oos": parts[-3],
                        "default_oos": parts[-2], "adopted": parts[-1]})
    return out


def write_dashboard(path=DASHBOARD, *, snapshot=None, ledger=None,
                    bars_map=None, full=False):
    """IO shell: committed artifacts (+ this run's bars) in, one board out."""
    snap_path = snapshot or homily_ledger.SNAPSHOT
    if not os.path.exists(snap_path):
        return None
    with open(snap_path) as f:
        snap = json.load(f)
    rows = homily_ledger._read_rows(ledger or homily_ledger.LEDGER)
    doc = render(snap, rows, _read_refine(), bars_map=bars_map, full=full)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w") as f:
        f.write(doc)
    return path


if __name__ == "__main__":
    # Local regenerate: fetch bars for the card set (R11: modest fan-out),
    # --full = every screened name -> temp path, else the small board in
    # docs/. The CI path never runs this — daily_run passes bars in-memory.
    import sys
    from concurrent.futures import ThreadPoolExecutor
    import homily_data
    full = "--full" in sys.argv
    snap = json.load(open(homily_ledger.SNAPSHOT))
    import daily_run                       # symbol map only (IO shell)
    sym = {**daily_run.WATCH, **daily_run.UNIVERSE, **daily_run.HOLDINGS}
    names = [s["ticker"] for s in
             snap.get("holdings", []) + [d for d in snap.get("discovery", [])
                                         if full or _actionable(d)]]
    bars_map = {}
    def _one(tk):
        try:
            bars_map[tk] = homily_data.fetch_daily(sym.get(tk, tk), rng="2y")
        except Exception as e:
            print(f"[{tk}] no bars: {e}")
    with ThreadPoolExecutor(max_workers=4) as ex:
        list(ex.map(_one, names))
    out = write_dashboard(BOARD_FULL if full else DASHBOARD,
                          bars_map=bars_map, full=full)
    print(f"wrote {out} ({os.path.getsize(out):,} bytes)" if out
          else "no snapshot yet — run daily_run first")
