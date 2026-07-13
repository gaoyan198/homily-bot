#!/usr/bin/env python3
"""
A5 A/B reader — the stop-cost table (#96 / D-96).
=================================================

Amendment A5's central design IS an A/B: the LIVE overlay (stops / TP /
time-stop, ladder-sized) mirrors the PAPER S1-pure book (no stops) on the
same Friday decisions. A5 promises the stops' cost is "measured, monthly,
in public." This module is that pre-registered read, frozen now so the
verdict can never be argued from vibes at the exact moment (a stop-out that
recovered / a crash the stops dodged) when vibes are worst.

What it does — per-episode attribution of every LIVE exit the paper book
did NOT take (final reason STOP / TP / TIME), matched to the paper book's
own handling of the same entry, in RETURN terms so the exit-timing decision
is isolated from the size difference (live US$3k × ladder vs paper's
notional US$20k). Both legs read straight from the two committed journals —
this module is READ-ONLY: it opens two CSVs and writes nothing, ever.

Pre-registered verdict (frozen here): at the earlier of 26 LIVE weeks or 20
CLOSED live trades, print the verdict row — stops cumulatively COST or SAVED
US$X vs the paper leg on the same decisions. REPORT-ONLY: the A5 stops stay
mandatory while the book is levered (bounded loss is their job, not edge —
KILL_MEMO's S1-stopped 0/3 stands); this read informs the next signed
amendment and cannot change a live rule by itself. Both directions are
stated in advance — stops looking expensive in a trending tape is EXPECTED;
what could justify an amendment is the ladder/kill interplay over a full
cycle, never one hot quarter.
"""
import csv
from pathlib import Path

_HERE = Path(__file__).resolve().parent
LIVE_JOURNAL = _HERE / "gambit_live_journal.csv"
PAPER_JOURNAL = _HERE / "gambit_journal.csv"

VERDICT_WEEKS = 26          # gambit PRD §5.2 / A5 — same bar as the P2 gate
VERDICT_TRADES = 20
MATCH_WINDOW_DAYS = 14      # live mirrors paper's Monday fills → entries align
STOP_REASONS = {"STOP", "TP", "TIME"}   # the exits the paper book never takes


def read_rows(path):
    """A journal CSV -> list of row dicts (or [] when absent). Read-only."""
    p = Path(path)
    if not p.exists():
        return []
    try:
        with p.open(newline="") as f:
            return list(csv.DictReader(f))
    except Exception:
        return []


def _f(v):
    try:
        return float(v)
    except (TypeError, ValueError):
        return None


def parse_episodes(rows):
    """Journal rows -> a list of position episodes, in order. An episode is
    one BUY (side=BUY) through the SELL(s) that close it (TP takes half, a
    later STOP/ROTATE closes the rest — proceeds aggregate, value-weighted
    exit price). Works identically on both books: the live journal tags exits
    with reason_code STOP/TP/TIME/ROTATE/KILL, the paper journal with
    ROTATE/REGIME — the parser only reads `side` and `price`."""
    episodes, open_by_sym = [], {}
    for r in rows:
        sym = (r.get("symbol") or "").strip()
        side = (r.get("side") or "").strip()
        px, qty = _f(r.get("price")), _f(r.get("qty"))
        d = (r.get("date") or "").strip()
        if not sym or px is None:
            continue
        if side == "BUY":
            open_by_sym[sym] = {"sym": sym, "entry_date": d, "entry_px": px,
                                "qty": qty or 0.0, "exits": [], "closed": False}
        elif side == "SELL" and sym in open_by_sym:
            ep = open_by_sym[sym]
            ep["exits"].append({"date": d, "px": px, "qty": qty or 0.0,
                                "reason": (r.get("reason_code") or "").strip()})
            sold = sum(x["qty"] for x in ep["exits"])
            if ep["qty"] <= 0 or sold >= ep["qty"] - 1e-6:
                w = sum(x["qty"] for x in ep["exits"]) or 1.0
                ep["exit_px"] = sum(x["px"] * x["qty"] for x in ep["exits"]) / w
                ep["exit_date"] = ep["exits"][-1]["date"]
                ep["final_reason"] = ep["exits"][-1]["reason"]
                ep["ret"] = ep["exit_px"] / ep["entry_px"] - 1.0
                ep["basis"] = ep["entry_px"] * ep["qty"]
                ep["closed"] = True
                episodes.append(ep)
                del open_by_sym[sym]
    episodes.extend(open_by_sym.values())      # leftover open episodes
    return episodes


def _match_paper(live_ep, paper_eps):
    """The paper episode for the same name entered around the same rotation
    (live mirrors paper's Monday fill, so entries align within a few days)."""
    best, best_gap = None, MATCH_WINDOW_DAYS + 1
    for pe in paper_eps:
        if pe["sym"] != live_ep["sym"]:
            continue
        gap = abs(_daydiff(pe["entry_date"], live_ep["entry_date"]))
        if gap <= MATCH_WINDOW_DAYS and gap < best_gap:
            best, best_gap = pe, gap
    return best


def _daydiff(a, b):
    import datetime
    try:
        return (datetime.date.fromisoformat(a)
                - datetime.date.fromisoformat(b)).days
    except Exception:
        return 10 ** 6


def attribute(live_eps, paper_eps):
    """For every CLOSED live episode whose exit the paper book didn't take
    (STOP/TP/TIME), compute the exit delta vs the paper leg in RETURN terms:
    delta_ret = paper_ret − live_ret (positive = the stop COST return; the
    paper book, holding, did better; negative = the stop SAVED — live exited
    before a deeper drop). Priced on the live basis so the cumulative is a
    real dollar figure at live size. Paper legs still open are counted
    `pending` (no fabricated mark) and left out of the cumulative."""
    episodes, cum, matched, pending = [], 0.0, 0, 0
    live_notional = sum(e.get("basis", 0.0) for e in live_eps if e["closed"])
    paper_notional = sum(e.get("basis", 0.0) for e in paper_eps if e["closed"])
    for le in live_eps:
        if not le["closed"] or le.get("final_reason") not in STOP_REASONS:
            continue
        pe = _match_paper(le, paper_eps)
        if pe is None:
            episodes.append({**_epview(le), "paper": None, "status": "no-match"})
            continue
        if not pe["closed"]:
            pending += 1
            episodes.append({**_epview(le), "paper_ret": None,
                             "status": "paper-open"})
            continue
        delta_ret = pe["ret"] - le["ret"]
        cost = delta_ret * le.get("basis", 0.0)     # +cost / −saving, live size
        cum += cost
        matched += 1
        episodes.append({**_epview(le), "paper_ret": pe["ret"],
                         "delta_ret": delta_ret, "cost": cost,
                         "status": "closed"})
    return {"episodes": episodes, "cum_cost": round(cum, 2),
            "matched": matched, "pending": pending,
            "size_ratio": (paper_notional / live_notional
                           if live_notional else None)}


def _epview(le):
    return {"sym": le["sym"], "entry_date": le["entry_date"],
            "reason": le.get("final_reason"), "live_ret": le.get("ret")}


def _weeks_since(rows, as_of):
    import datetime
    dates = [r.get("date") for r in rows if r.get("date")]
    if not dates or as_of is None:
        return 0
    try:
        first = datetime.date.fromisoformat(min(dates))
        return max(0, (as_of - first).days // 7)
    except Exception:
        return 0


def ab_block(as_of=None, *, live_path=LIVE_JOURNAL, paper_path=PAPER_JOURNAL,
             esc=lambda x: x):
    """The monthly A/B section (rides the realized report). "" when the live
    book has no closed stop-episodes yet — the read is honest about being
    pending until the pre-registered bar. Deterministic function of the two
    journals + the date."""
    live_rows, paper_rows = read_rows(live_path), read_rows(paper_path)
    if not live_rows:
        return ""
    live_eps = parse_episodes(live_rows)
    paper_eps = parse_episodes(paper_rows)
    attr = attribute(live_eps, paper_eps)
    closed_live = sum(1 for e in live_eps if e["closed"])
    weeks = _weeks_since(live_rows, as_of)
    lines = ["♟️ <b>SWING A/B — stops vs the paper leg (#96, report-only)</b>"]
    if attr["matched"] == 0:
        lines.append(f"<i>no STOP/TP/TIME episode with a closed paper match "
                     f"yet ({attr['pending']} paper legs still open) — "
                     f"pending: wk {weeks}/{VERDICT_WEEKS} · closed live "
                     f"{closed_live}/{VERDICT_TRADES}</i>")
        return "\n".join(lines)
    verb = "COST" if attr["cum_cost"] >= 0 else "SAVED"
    for e in attr["episodes"]:
        if e["status"] != "closed":
            continue
        lines.append(
            f"　{esc(e['sym'])} [{esc(e['reason'])}] live {e['live_ret']:+.0%}"
            f" vs paper {e['paper_ret']:+.0%} → stop "
            f"{'cost' if e['cost'] >= 0 else 'saved'} ${abs(e['cost']):,.0f}")
    sr = attr["size_ratio"]
    lines.append(
        f"<i>stops {verb} ${abs(attr['cum_cost']):,.0f} cumulative over "
        f"{attr['matched']} matched episode(s), at live size"
        + (f"; paper trades ≈{sr:.1f}× the notional (size effect is separate "
           "from this exit effect)" if sr else "")
        + f" · {attr['pending']} paper legs still open</i>")
    if weeks >= VERDICT_WEEKS or closed_live >= VERDICT_TRADES:
        lines.append(
            f"🔎 <b>VERDICT (pre-registered bar reached: wk {weeks}, closed "
            f"{closed_live})</b>: the mandated stops have {verb} "
            f"${abs(attr['cum_cost']):,.0f} vs holding the paper leg. "
            "REPORT-ONLY — stops stay mandatory while levered (KILL_MEMO); "
            "this informs the next signed amendment, it changes no live rule. "
            "Fills are modeled — reconcile against IBKR.")
    else:
        lines.append(f"<i>verdict pending — fires at wk {VERDICT_WEEKS} or "
                     f"{VERDICT_TRADES} closed live trades (now wk {weeks} · "
                     f"{closed_live} closed)</i>")
    return "\n".join(lines)


if __name__ == "__main__":       # pragma: no cover — manual read
    import datetime
    print(ab_block(datetime.date.today()) or "no live journal yet")
