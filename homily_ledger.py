#!/usr/bin/env python3
"""
Signals ledger (backlog #13) — the live track record starts here.
=================================================================

Every daily run appends ONE row per screened name to `homily_signals_log.csv`
(what the digest actually printed that day) and rewrites `docs/snapshot.json`
(the full structured state, the single data contract for the dashboard track F
and for Claude sessions to answer questions without refetching). Everything in
phases C–F consumes this; #14's live scorecard is these rows read forward.

Three invariants make it a *credible* record rather than a fake one:

  * R3 — history is append-only. Same-day re-runs overwrite today's rows
    (idempotent per date+ticker), but a date already written is NEVER changed
    or backfilled. Backfilled rows would run today's code on yesterday's dates
    and manufacture a track record — the exact thing this file exists to
    prevent. Enforced mechanically by the hash checkpoint below (guard #62).
  * R7 — the run date is pinned to SGT (UTC+8), not the runner's clock. The
    cron fires 01:00 UTC = 09:00 SGT; a bare date.today() is UTC in Actions
    and SGT locally, so the same bar could key to two different dates and
    break idempotency. run_date() computes a fixed-offset SGT date instead
    (Singapore has no DST, so +8 is exact year-round).
  * R8 — the ledger, snapshot and hash checkpoint are committed by the
    workflow; they are added to its `git add` list in the same PR.

The engine files stay frozen (EXECUTION.md §0): this module only READS the
DannySignal / Conviction outputs the digest already computed.
"""
import os
import csv
import json
import hashlib
import datetime

from homily_fund import fund_tag

HERE = os.path.dirname(os.path.abspath(__file__))
LEDGER = os.path.join(HERE, "homily_signals_log.csv")
SNAPSHOT = os.path.join(HERE, "docs", "snapshot.json")
HASHFILE = os.path.join(HERE, "homily_ledger_hash.json")

# Flat CSV schema (spec, PRD #13). Order is the file's column order and the
# hash serialisation order — append columns at the END only, never reorder.
COLUMNS = [
    "date", "ticker", "held", "close", "state", "zone_lo", "zone_hi", "poc",
    "pct_in_profit", "wk_circle", "wk_score", "wk_weeks", "monthly_up",
    "vh_status", "whale", "absorption", "divergence", "shelf_stable",
    "conv_score", "conv_tier", "gates_ok", "gates_failed", "ftag",
    "rs12_rank",
    "origin",
    "whale_rank",
    "candle",
]


def run_date():
    """Pinned SGT (UTC+8) run date — deterministic on any runner (R7)."""
    return (datetime.datetime.now(datetime.timezone.utc)
            + datetime.timedelta(hours=8)).date()


# --- per-name state (one source of truth: snapshot uses it whole, the CSV
#     row is its flattened projection) -----------------------------------------
def state_of(sig, conv, held, *, fund=fund_tag, pos_view=None, origin=None):
    """DannySignal + Conviction -> a JSON-native dict of everything the digest
    knew about one name today. Pure read of frozen-engine outputs.
    `pos_view` (#27, homily_positions.position_view()) is snapshot-only,
    optional data for #28-30 to consume — None for anything not a tracked
    USD position (not held, Bucket A, non-USD, or an unsynced holdings.json).
    `origin` (#64) records HOW the name entered the universe so #14 can split
    the scorecard by it: "owner-request" (the whole pre-#65 hand-picked
    list — the honest default, PRD §5c/§5f), "holding" (in the book), or
    "screen" (reserved for #65's mechanical arrivals)."""
    s, c, ch = sig, conv, sig.chips
    zlo, zhi = (s.add_zone if s.add_zone else (None, None))
    try:
        ft = fund(s.ticker)
    except Exception:
        ft = ""
    return {
        "ticker": s.ticker,
        "held": bool(held),
        "close": round(ch.last, 4),
        "state": s.state,
        "zone_lo": (round(zlo, 4) if zlo is not None else None),
        "zone_hi": (round(zhi, 4) if zhi is not None else None),
        "poc": round(ch.poc, 4),
        "pct_in_profit": round(ch.pct_in_profit, 2),
        "wk_circle": s.weekly.circle,
        "wk_score": s.weekly.score,
        "wk_weeks": s.weekly.weeks_in_regime,
        "monthly_up": bool(s.monthly_up),
        # #101: the DAILY candle (RED/YELLOW/NEUTRAL) the digest already renders
        # (dY + the #78 pullback clock) but never persisted — wk_circle above is
        # the WEEKLY circle, a different signal. END-appended CSV column; forward
        # rows only, so a daily-candle event study can replay from the log.
        "candle": s.candle,
        "vh_status": (s.vol_hole.status if s.vol_hole else None),
        "whale": bool(s.whale.whale),
        "absorption": bool(s.whale.absorption),
        "divergence": bool(s.whale.divergence),
        "shelf_stable": bool(s.whale.shelf_stable),
        "conv_score": c.score,
        "conv_tier": c.tier,
        "gates_ok": bool(c.gates_ok),
        "gates_failed": list(c.gates_failed),
        "ftag": ft,
        "origin": origin or "owner-request",
        # snapshot-only extras (dashboard / Claude sessions); not in the CSV
        "support": [[round(p, 4), round(w, 4)] for p, w in ch.support],
        "resistance": [[round(p, 4), round(w, 4)] for p, w in ch.resistance],
        "rs12": round(c.rs12, 2),
        "dvol": round(c.dvol, 2),
        "conv_parts": dict(c.parts),
        "bucket": (pos_view["bucket"] if pos_view else None),
        "book_pct": (round(pos_view["pct"], 2)
                     if pos_view and pos_view["pct"] is not None else None),
        "cap_note": (pos_view["cap_note"] if pos_view else None),
    }


def rs12_ranks(states):
    """Cross-sectional RS12 rank among today's buy-day candidates, mirroring
    `homily_selection_backtest._screen`: ACCUMULATE (⭐) names if any screened
    today, else BOTTOMING (🔵) as fallback — same precedence #24's backtest
    ranks over. Ships now (no behaviour change) so the promotion's ledger
    forward-check (PRD §5j) has rank data accruing from day one; digest
    ordering and money allocation are untouched until/unless #24 is
    promoted. Non-candidates get no rank (None -> blank CSV cell)."""
    accum = [s for s in states if s["state"] == "ACCUMULATE"]
    cands = accum or [s for s in states if s["state"] == "BOTTOMING"]
    ranked = sorted(cands, key=lambda s: -s["rs12"])
    ranks = {s["ticker"]: i + 1 for i, s in enumerate(ranked)}
    return {st["ticker"]: ranks.get(st["ticker"]) for st in states}


def whale_ranks(states):
    """#80 (PRD §5k, MARA-vs-WULF): cross-sectional whale-accumulation
    intensity rank over the SAME candidate set as rs12_ranks (⭐ else 🔵) —
    Danny picks *between* similar names by main-force intensity, so the
    challenger for the 2026-10-01 #24 read needs this frozen at print time.
    Intensity = footprint events printing today (absorption + divergence +
    shelf_stable, 0–3); ties break by RS12 desc then ticker so the rank is
    deterministic. Pure measurement — nothing consumes it live; the whale
    booleans stay in the CSV too, so the study can re-derive its own
    reading, but the rank the digest COULD have acted on is pinned here."""
    accum = [s for s in states if s["state"] == "ACCUMULATE"]
    cands = accum or [s for s in states if s["state"] == "BOTTOMING"]
    ranked = sorted(cands,
                    key=lambda s: (-(int(s["absorption"]) + int(s["divergence"])
                                     + int(s["shelf_stable"])),
                                   -s["rs12"], s["ticker"]))
    ranks = {s["ticker"]: i + 1 for i, s in enumerate(ranked)}
    return {st["ticker"]: ranks.get(st["ticker"]) for st in states}


def _csv_cell(v):
    if v is None:
        return ""
    if isinstance(v, bool):
        return "1" if v else "0"
    if isinstance(v, list):
        return ";".join(str(x) for x in v)
    if isinstance(v, float):
        return f"{v:g}"
    return str(v)


def csv_row(state, day):
    """Flatten a state_of() dict to the exact COLUMNS the CSV commits."""
    row = {"date": day.isoformat()}
    for col in COLUMNS:
        if col == "date":
            continue
        row[col] = _csv_cell(state.get(col))
    return row


# --- append-only ledger + hash checkpoint (R3 / guard #62) -------------------
def _read_rows(path=LEDGER):
    if not os.path.exists(path):
        return []
    with open(path, newline="") as f:
        return list(csv.DictReader(f))


def _write_rows(rows, path=LEDGER):
    with open(path, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=COLUMNS)
        w.writeheader()
        for r in rows:
            w.writerow({c: r.get(c, "") for c in COLUMNS})


def _rows_hash(rows):
    """Order-independent SHA-256 of a set of ledger rows (rows are sorted by
    their serialised form, so a re-sort of the file can't change the hash)."""
    lines = sorted("\x1f".join(r.get(c, "") for c in COLUMNS) for r in rows)
    h = hashlib.sha256()
    for ln in lines:
        h.update(ln.encode())
        h.update(b"\n")
    return h.hexdigest()


def _load_checkpoint(path=HASHFILE):
    if not os.path.exists(path):
        return None
    with open(path) as f:
        return json.load(f)


def _verify_checkpoint(rows, path=HASHFILE):
    """Raise if committed history (rows dated <= checkpoint.through) no longer
    hashes to the committed value — i.e. a past row was edited or deleted."""
    cp = _load_checkpoint(path)
    if not cp or not cp.get("through"):
        return
    frozen = [r for r in rows if r["date"] <= cp["through"]]
    if _rows_hash(frozen) != cp["sha256"]:
        raise AssertionError(
            "ledger history diverged from committed checkpoint "
            f"({os.path.basename(path)} through {cp['through']}): a past row "
            "was edited, deleted or backfilled. The ledger is append-only "
            "(EXECUTION.md R3) — restore history or, only if the change was "
            "genuinely intended, regenerate the checkpoint deliberately.")


def _advance_checkpoint(rows, day, path=HASHFILE):
    """Freeze everything strictly BEFORE today's run date; today's rows stay
    mutable (same-day idempotent overwrite is allowed, R3)."""
    today = day.isoformat()
    frozen_dates = sorted({r["date"] for r in rows if r["date"] < today})
    through = frozen_dates[-1] if frozen_dates else None
    frozen = [r for r in rows if through and r["date"] <= through]
    cp = {"through": through, "rows": len(frozen), "sha256": _rows_hash(frozen)}
    with open(path, "w") as f:
        json.dump(cp, f, indent=2)
        f.write("\n")


def append_rows(new_rows, day, *, ledger=LEDGER, hashfile=HASHFILE):
    """Idempotent per (date, ticker): overwrite today's rows, never touch a
    past date. Verifies frozen history hasn't drifted before writing."""
    today = day.isoformat()
    existing = _read_rows(ledger)
    _verify_checkpoint(existing, hashfile)          # loud on any retro-edit
    kept = [r for r in existing if r["date"] != today]
    rows = kept + [{c: r.get(c, "") for c in COLUMNS} for r in new_rows]
    rows.sort(key=lambda r: (r["date"], r["ticker"]))
    _write_rows(rows, ledger)
    _advance_checkpoint(rows, day, hashfile)
    return rows


def coverage_of(rows, today):
    """#70 missed-run detector: which weekday run-dates since the ledger
    began have NO rows at all. #16 catches a run that fails; this catches a
    run that never STARTS — a track record with silent holes is biased
    toward the days the infra was healthy (R3's mirror image). Expected =
    every Mon–Fri from the first row's date through the last weekday BEFORE
    `today` (today's rows may not exist yet while the digest builds; the
    cron fires Mon–Fri regardless of market holidays, so a weekday without
    rows IS a miss — including a run halted by a red validate gate, which
    should be loud here too). -> {"expected","have","missing","pct"}."""
    dates = sorted({r["date"] for r in rows})
    if not dates:
        return {"expected": 0, "have": 0, "missing": [], "pct": 100.0}
    d = datetime.date.fromisoformat(dates[0])
    have = set(dates)
    expected, missing = 0, []
    while d < today:
        if d.weekday() < 5:
            expected += 1
            if d.isoformat() not in have:
                missing.append(d.isoformat())
        d += datetime.timedelta(days=1)
    pct = 100.0 * (expected - len(missing)) / expected if expected else 100.0
    return {"expected": expected, "have": expected - len(missing),
            "missing": missing, "pct": round(pct, 2)}


SNAPSHOT_V = 1     # #75: consumers (dashboard, Claude, the future T3 order
                   # routine) refuse a version they don't know — a silently
                   # renamed field must never cost money


def verify_snapshot(snap):
    """#75 schema contract, enforced in CI (check [33]). Pins the fields the
    dashboard and T3 read; extending the snapshot is fine, renaming or
    retyping these is a version bump."""
    assert snap.get("_v") == SNAPSHOT_V, f"unknown snapshot _v: {snap.get('_v')}"
    for k in ("date", "generated_utc", "regime", "coverage", "holdings",
              "discovery"):
        assert k in snap, f"snapshot missing {k}"
    for s in snap["holdings"] + snap["discovery"]:
        for k in ("ticker", "state", "close", "origin"):
            assert k in s, f"snapshot row {s.get('ticker')}: missing {k}"
    b = snap.get("buyday")
    if b is not None:
        for k in ("orders", "budget", "spent", "leftover", "mode"):
            assert k in b, f"snapshot buyday missing {k}"
        for o in b["orders"]:
            tk, n, px, note = o           # exactly (ticker, shares, px, note)
            assert isinstance(tk, str) and isinstance(n, int) \
                and isinstance(px, (int, float)) and isinstance(note, str), \
                f"buyday order malformed: {o}"


def write_snapshot(day, regime, holdings, discovery, path=SNAPSHOT,
                   coverage=None, buyday=None):
    """Full structured state -> docs/snapshot.json (data contract for F / Claude)."""
    reg = None
    if regime is not None:
        reg = {"label": regime.label, "action": regime.action,
               "detail": {sym: list(v) for sym, v in regime.detail.items()}}
    snap = {
        "_v": SNAPSHOT_V,
        "date": day.isoformat(),
        "generated_utc": datetime.datetime.now(datetime.timezone.utc)
                         .replace(microsecond=0).isoformat(),
        "regime": reg,
        # #70: ledger coverage — #14 must report this next to its returns
        "coverage": coverage,
        # #75/T3: the buy-day plan (None off buy days) — the machine-readable
        # twin of the digest's 🛒 block, schema pinned by verify_snapshot()
        "buyday": buyday,
        "holdings": holdings,
        "discovery": discovery,
    }
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w") as f:
        json.dump(snap, f, indent=2)
        f.write("\n")
    return snap


def record(sigs, disco, regime, day, holdings_set, *, fund=fund_tag,
           origins=None, buyday=None, shadow=None, ledger=LEDGER,
           snapshot=SNAPSHOT, hashfile=HASHFILE):
    """Orchestrator called by daily_run after the digest is built. `sigs` is
    the held+watch group, `disco` the not-held discovery group; `holdings_set`
    is the set of actually-held tickers (WATCH names screen in `sigs` but are
    not held). `origins` (#64) maps ticker -> provenance; anything unmapped
    falls back to "holding" if held else "owner-request" (conservative —
    never lets a name masquerade as mechanically screened).
    `shadow` (#65): (sig, conv) pairs from the mechanical screen's D-65
    shadow quarter — logged as rows with origin "shadow-screen" so the
    adoption gate can be measured, but OUTSIDE the rank cross-sections
    (rs12/whale ranks stay what the digest could have acted on), outside
    the snapshot, and with no digest surface."""
    org = origins or {}

    def _origin(tk):
        return org.get(tk) or ("holding" if tk in holdings_set
                               else "owner-request")

    held_states = [state_of(s, c, s.ticker in holdings_set, fund=fund,
                            origin=_origin(s.ticker))
                   for s, c, _ in sigs]
    disco_states = [state_of(s, c, False, fund=fund,
                             origin=_origin(s.ticker)) for s, c, _ in disco]
    all_states = held_states + disco_states
    ranks = rs12_ranks(all_states)
    wranks = whale_ranks(all_states)
    for st in all_states:
        st["rs12_rank"] = ranks[st["ticker"]]
        st["whale_rank"] = wranks[st["ticker"]]
    shadow_states = [state_of(s, c, False, fund=fund, origin="shadow-screen")
                     for s, c in (shadow or [])]
    rows = [csv_row(st, day) for st in all_states + shadow_states]
    all_rows = append_rows(rows, day, ledger=ledger, hashfile=hashfile)
    write_snapshot(day, regime, held_states, disco_states, path=snapshot,
                   coverage=coverage_of(all_rows, day), buyday=buyday)


def verify_history(ledger=LEDGER, hashfile=HASHFILE):
    """Read-only CI guard (#62 / R3): committed history must still match the
    committed hash checkpoint. Called from homily_validate.py."""
    _verify_checkpoint(_read_rows(ledger), hashfile)


if __name__ == "__main__":
    cp = _load_checkpoint()
    rows = _read_rows()
    print(f"ledger: {len(rows)} rows, "
          f"{len({r['date'] for r in rows})} dates; "
          f"checkpoint through {cp['through'] if cp else '—'}")
    verify_history()
    print("history OK (append-only checkpoint verified)")
