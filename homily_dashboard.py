#!/usr/bin/env python3
"""
Nightly dashboard (backlog #36) — one self-contained HTML file, zero JS.
========================================================================

`docs/dashboard.html`, rendered from `docs/snapshot.json` + the #13 ledger
+ the refine log, committed by the workflow and sent via sendDocument:
private in the chat, one tap to open, works offline, renders identically
in Telegram's in-app browser and in five years (D-36: server-side static
SVG, no client JS, no external assets — a strict self-containment test in
validate keeps it that way).

Sections: regime + coverage header · per-holding <details> cards (levels,
chip peaks, ledger-close sparkline) · discovery table · ledger state
heatmap (every name × every day, the live record at a glance) · alerts
timeline (#15's alert wording REUSED via homily_alerts.diff_alerts over
consecutive ledger dates — every alert ever, reconstructed and auditable,
owner request 2026-07-10; regime flips aren't in ledger rows, so the
timeline reconstructs state/whale/gate transitions only) · refine-log
OOS chart. #14's scorecard tables join once the ledger is 3 months old.

The render is a pure function of its three inputs — deterministic, which
is what check [33] pins. Engines frozen (§0): reads committed artifacts
only. Sparklines use ledger closes (raw, R1) and honestly say how young
the ledger is rather than fetching history that predates the record.
"""
import os
import json
import html

import homily_ledger
import homily_alerts

HERE = os.path.dirname(os.path.abspath(__file__))
DASHBOARD = os.path.join(HERE, "docs", "dashboard.html")
REFINE_LOG = os.path.join(HERE, "homily_refine_log.csv")

ICON = {"ACCUMULATE": "⭐", "HOLD": "🟢", "PULLBACK": "🟡",
        "BOTTOMING": "🔵", "CAUTION": "⚪"}
COLOR = {"ACCUMULATE": "#2e7d32", "HOLD": "#8bc34a", "PULLBACK": "#f9a825",
         "BOTTOMING": "#1565c0", "CAUTION": "#b0b0b0"}
E = lambda x: html.escape(str(x), quote=True)


# --- tiny SVG helpers (strings in, strings out, nothing clever) -------------
def _svg(w, h, body, title=None):
    t = f"<title>{E(title)}</title>" if title else ""
    return (f'<svg width="{w}" height="{h}" viewBox="0 0 {w} {h}" '
            f'xmlns="http://www.w3.org/2000/svg">{t}{body}</svg>')


def _card_svg(s, closes):
    """One holding's picture: zone band + POC/res lines + chip peaks on the
    right + the ledger-close sparkline (however young)."""
    w, h, pad = 640, 150, 8
    marks = [s["close"], s["poc"]] + [c for _, c in closes]
    if s.get("zone_lo") is not None:
        marks += [s["zone_lo"], s["zone_hi"]]
    peaks = (s.get("support") or []) + (s.get("resistance") or [])
    marks += [p for p, _ in peaks]
    lo, hi = min(marks), max(marks)
    span = (hi - lo) or lo * 0.01
    lo, hi = lo - span * 0.07, hi + span * 0.07
    y = lambda p: h - pad - (p - lo) / (hi - lo) * (h - 2 * pad)
    plot_r = w - 150
    parts = [f'<rect width="{w}" height="{h}" fill="#fafafa"/>']
    if s.get("zone_lo") is not None:
        parts.append(f'<rect x="{pad}" y="{y(s["zone_hi"]):.1f}" '
                     f'width="{plot_r - pad}" '
                     f'height="{y(s["zone_lo"]) - y(s["zone_hi"]):.1f}" '
                     f'fill="#c8e6c9"><title>add zone {s["zone_lo"]}–'
                     f'{s["zone_hi"]}</title></rect>')
    parts.append(f'<line x1="{pad}" x2="{plot_r}" y1="{y(s["poc"]):.1f}" '
                 f'y2="{y(s["poc"]):.1f}" stroke="#ef6c00">'
                 f'<title>POC {s["poc"]}</title></line>')
    for p, wt in peaks:
        col = "#81c784" if p <= s["close"] else "#e57373"
        parts.append(f'<rect x="{plot_r + 6}" y="{y(p) - 2:.1f}" '
                     f'width="{6 + wt * 120:.1f}" height="4" fill="{col}">'
                     f'<title>chip peak {p} (rel {wt})</title></rect>')
    if len(closes) >= 2:
        step = (plot_r - 2 * pad) / (len(closes) - 1)
        pts = " ".join(f"{pad + i * step:.1f},{y(c):.1f}"
                       for i, (_d, c) in enumerate(closes))
        parts.append(f'<polyline points="{pts}" fill="none" '
                     f'stroke="#1a3f8f" stroke-width="2">'
                     f'<title>ledger closes {closes[0][0]} → '
                     f'{closes[-1][0]}</title></polyline>')
    else:
        parts.append(f'<text x="{pad}" y="{h // 2}" font-size="11" '
                     f'fill="#888">ledger too young for a sparkline — '
                     f'the record starts 2026-07-08, honestly</text>')
    parts.append(f'<circle cx="{plot_r - pad}" cy="{y(s["close"]):.1f}" '
                 f'r="3" fill="#1a3f8f"><title>close {s["close"]}</title>'
                 '</circle>')
    return _svg(w, h, "".join(parts), f'{s["ticker"]} levels')


def _facts(s):
    bits = [f'{ICON.get(s["state"], "")} <b>{E(s["state"])}</b>',
            f'close {E(s["close"])}']
    if s.get("zone_lo") is not None:
        bits.append(f'add {E(s["zone_lo"])}–{E(s["zone_hi"])}')
    bits += [f'POC {E(s["poc"])}', f'{E(s["pct_in_profit"])}% in profit',
             f'wk {E(s["wk_circle"])}/{E(s["wk_score"])} '
             f'({E(s["wk_weeks"])}w)',
             f'conv {E(s["conv_score"])} ({E(s["conv_tier"])})',
             f'RS12 {E(s.get("rs12", "—"))}', E(s.get("ftag") or "F:—")]
    if s.get("book_pct") is not None:
        bits.append(f'{E(s["book_pct"])}% of book')
    if s.get("cap_note"):
        bits.append(f'⚠️ {E(s["cap_note"])}')
    if s.get("whale"):
        bits.append("🐳 whale footprint")
    return " · ".join(bits)


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
                         f'fill="#666">{E(d[5:])}</text>')
    for i, tk in enumerate(tickers):
        yy = 18 + i * ch
        parts.append(f'<text x="0" y="{yy + 10}" font-size="10" '
                     f'font-family="monospace">{E(tk)}</text>')
        for j, d in enumerate(dates):
            st = state.get((d, tk))
            if st is None:
                continue
            parts.append(f'<rect x="{lx + j * cw}" y="{yy}" '
                         f'width="{cw - 2}" height="{ch - 2}" '
                         f'fill="{COLOR.get(st, "#eee")}">'
                         f'<title>{E(d)} {E(tk)} {E(st)}</title></rect>')
    return _svg(w, h, "".join(parts), "ledger state history")


def _timeline(rows):
    """Every #15-style alert ever, reconstructed: homily_alerts.diff_alerts
    REUSED verbatim over consecutive ledger dates (regime flips aren't in
    ledger rows — noted in the section header)."""
    dates = sorted({r["date"] for r in rows})
    by_date = {d: [r for r in rows if r["date"] == d] for d in dates}
    out = []
    for prev_d, cur_d in zip(dates, dates[1:]):
        lines = homily_alerts.diff_alerts(by_date[cur_d], None,
                                          by_date[prev_d], None)
        for ln in lines:
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
        f'cy="{y(float(r["champ_oos"])):.1f}" r="4" fill="#ef6c00">'
        f'<title>{E(r["date"])} ADOPTED {E(r["champion"])}</title></circle>'
        for i, r in enumerate(rows) if r.get("adopted") == "True")
    return _svg(w, h, line("champ_oos", "#1a3f8f")
                + line("challenger_oos", "#9e9e9e") + dots,
                "champion vs challenger OOS Calmar") \
        + ("<p><small>blue champion · grey challenger · orange dot = "
           "challenger adopted (OOS-gated)</small></p>")


def render(snap, rows, refine_rows):
    """Pure, deterministic: snapshot dict + ledger rows + refine rows -> the
    full HTML document string."""
    reg = snap.get("regime") or {}
    ricon = {"BULL": "🐂", "BEAR": "🐻", "MIXED": "⚖️"}.get(reg.get("label"), "⚖️")
    cov = snap.get("coverage") or {}
    closes_by = {}
    for r in rows:
        if r.get("close"):
            closes_by.setdefault(r["ticker"], []).append(
                (r["date"], float(r["close"])))
    for v in closes_by.values():
        v.sort()
    cards = "".join(
        f'<details{" open" if s["state"] == "ACCUMULATE" else ""}>'
        f'<summary>{ICON.get(s["state"], "")} <b>{E(s["ticker"])}</b> '
        f'{E(s["close"])} — {E(s["state"])}</summary>'
        f'<p>{_facts(s)}</p>{_card_svg(s, closes_by.get(s["ticker"], []))}'
        '</details>'
        for s in snap.get("holdings", []))
    disco = "".join(
        f'<tr><td>{ICON.get(s["state"], "")} {E(s["ticker"])}</td>'
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
    return f"""<!DOCTYPE html>
<html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>homily dashboard {E(snap.get("date", ""))}</title>
<style>
body{{font:14px/1.45 -apple-system,system-ui,sans-serif;margin:16px;
     max-width:720px}}
details{{border:1px solid #ddd;border-radius:6px;padding:6px 10px;
        margin:6px 0}}
summary{{cursor:pointer}}
table{{border-collapse:collapse}} td{{padding:2px 8px;
     border-bottom:1px solid #eee}}
h2{{margin:18px 0 6px;font-size:16px}}
.wrap{{overflow-x:auto}}
</style></head><body>
<h1>Homily × Danny — {E(snap.get("date", ""))}</h1>
<p>{ricon} <b>{E(reg.get("label", "regime unavailable"))}</b>
 <i>{E(reg.get("action", ""))}</i></p>
<p><small>ledger coverage: {E(cov.get("have", "—"))}/{E(cov.get("expected",
"—"))} weekday runs ({E(cov.get("pct", "—"))}%)
{("· holes: " + E(", ".join(cov["missing"]))) if cov.get("missing") else ""}
</small></p>
{buyday}
<h2>holdings</h2>{cards}
<h2>🔎 discovery (⭐/🔵 only)</h2>
<div class="wrap"><table><tr><th></th><th>state</th><th>close</th>
<th>RS12</th><th>F</th></tr>{disco or '<tr><td colspan="5">none today</td></tr>'}
</table></div>
<h2>ledger state history</h2><div class="wrap">{_heatmap(rows)}</div>
<h2>alerts timeline (reconstructed from ledger diffs; regime flips not
recorded per-row)</h2>{_timeline(rows)}
<h2>auto-refine, out-of-sample</h2>{_refine_chart(refine_rows)}
<p><small>generated {E(snap.get("generated_utc", ""))} · self-contained,
no external assets, no scripts · approximation of Danny/Homily behaviour,
not their formulas — levels are context, not advice.</small></p>
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


def write_dashboard(path=DASHBOARD, *, snapshot=None, ledger=None):
    """IO shell: committed artifacts in, docs/dashboard.html out."""
    snap_path = snapshot or homily_ledger.SNAPSHOT
    if not os.path.exists(snap_path):
        return None
    with open(snap_path) as f:
        snap = json.load(f)
    rows = homily_ledger._read_rows(ledger or homily_ledger.LEDGER)
    doc = render(snap, rows, _read_refine())
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w") as f:
        f.write(doc)
    return path


if __name__ == "__main__":
    p = write_dashboard()
    print(f"wrote {p} ({os.path.getsize(p):,} bytes)" if p
          else "no snapshot yet — run daily_run first")
