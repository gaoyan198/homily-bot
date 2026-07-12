#!/usr/bin/env python3
"""
GAMBIT G-S5 — the weekly digest (owner-facing, ♟️ prefix per DESIGNS D-G7).

Pure rendering from a paper-simulator digest dict — no I/O, no clock, no
network — so a golden-file test can pin it byte-for-byte (homily #49: build the
golden before the first send). validate gates the send on that golden; a
changed render fails CI until the golden is regenerated deliberately.

This is the PAPER digest: it reports the notional US$20k book, proposals that
will auto-fill Monday's open unless vetoed (Amendment A2), and the book vs
same-dollar QQQ (the PRD §1 bar). It never renders or implies a live order.
"""

PREFIX = "♟️ GAMBIT"          # ♟️ GAMBIT


def _pct(a, b):
    return "n/a" if not b else f"{(a / b - 1) * 100:+.1f}%"


def render(digest, *, arm="S1-pure (paper, Amendment A4)"):
    d = digest
    L = []
    L.append(f"{PREFIX} — weekly paper digest — {d['as_of']}")
    L.append(f"arm: {arm} · regime: {d['regime']} · LIVE_ORDERS=off (paper)")
    L.append("")
    eq, qv = d["equity"], d["qqq_value"]
    L.append(f"book equity   ${eq:,.2f}   (cash ${d['cash']:,.2f})")
    L.append(f"vs same-$ QQQ  ${qv:,.2f}   book {_pct(eq, qv)} vs QQQ B&H")
    L.append(f"high-water     ${d['hwm']:,.2f}   drawdown {_pct(eq, d['hwm'])}")
    L.append("")

    pos = d["positions"]
    if pos:
        L.append(f"open book ({len(pos)}/5):")
        for sym in sorted(pos):
            p = pos[sym]
            L.append(f"  {sym:<6} qty {float(p['qty']):>10.4f} "
                     f"@ {float(p['entry']):>9.2f}  since {p['entry_date']}")
    else:
        L.append("open book: flat (no positions)")
    L.append("")

    pend = d["pending"]
    if pend:
        L.append("proposals — auto-fill Monday open unless vetoed (A2):")
        for p in pend:
            L.append(f"  {p['side']:<4} {p['sym']:<6} [{p['reason']}]")
    else:
        L.append("proposals: none — a quiet week is the system working (§4.1)")
    L.append("")

    ev = [e for e in d["events"] if e["event"] in ("FILL", "REGIME")]
    if ev:
        L.append("this week's fills:")
        for e in ev:
            L.append(f"  {e['event']} {e['side']} {e['symbol']} "
                     f"qty {e['qty']} @ {e['price']} [{e['reason_code']}]")
        L.append("")
    L.append("— paper only; no real order was placed. Ledger: gambit_journal.csv")
    return "\n".join(L)
