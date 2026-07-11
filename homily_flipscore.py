#!/usr/bin/env python3
"""
Flip scorecard (#14a) — the early-read referee for state transitions.
=====================================================================

#14 proper needs ~3 ledger months before its first read; this rider reads
the same ledger sooner at a shorter horizon: every state TRANSITION in
homily_signals_log.csv (e.g. CAUTION→BOTTOMING, HOLD→ACCUMULATE) gets
forward 1/5/20-trading-day returns vs same-day QQQ, split by transition
type. Owner-requested 2026-07-11 after the META/SHOP/NVDA flips of 07-10
all confirmed next session — one good day is anecdote, this makes it
measurement.

The R3 rule is structural here, not a convention: a flip exists ONLY where
two consecutive ledger rows for the same ticker disagree on state. Nothing
is ever recomputed from bars for a past date, so the flip list can never
contain a transition the digest didn't actually print. Forward PRICES are
market data fetched at read time (that is not backfilling — the events are
pinned; only their outcomes mature), using the dividend-adjusted series
(#18) for the return math.

First read possible ~1 month after log start (2026-07-09). Until horizons
mature the table prints honest zero-count rows rather than nothing.
"""
import datetime

import homily_ledger

HORIZONS = (1, 5, 20)          # trading days forward, vs same-day QQQ
BENCH = "QQQ"


def flips(rows):
    """Ledger rows -> [{date, ticker, prev, new, prev_date}], one per state
    transition between a ticker's consecutive ledger appearances. Pure read
    of what the digest printed (R3): no bars, no recomputation."""
    by_tk = {}
    for r in rows:
        if r.get("ticker") and r.get("date") and r.get("state"):
            by_tk.setdefault(r["ticker"], []).append(r)
    out = []
    for tk, rs in sorted(by_tk.items()):
        rs.sort(key=lambda r: r["date"])
        for prev, cur in zip(rs, rs[1:]):
            if cur["state"] != prev["state"]:
                out.append({"date": cur["date"], "ticker": tk,
                            "prev": prev["state"], "new": cur["state"],
                            "prev_date": prev["date"]})
    out.sort(key=lambda f: (f["date"], f["ticker"]))
    return out


def _fwd(dates, adj, day, n):
    """n-trading-day forward return from `day` in an aligned (dates, adj)
    series, or None while the horizon hasn't matured / the date is absent."""
    try:
        i = dates.index(day)
    except ValueError:
        return None
    if i + n >= len(adj) or not adj[i]:
        return None
    return adj[i + n] / adj[i] - 1


def flip_excess(fl, series):
    """One flip -> {horizon: excess-vs-QQQ or None}. `series` maps ticker ->
    (dates, adj) with QQQ under BENCH; a missing series yields all-None."""
    day = datetime.date.fromisoformat(fl["date"])
    name = series.get(fl["ticker"])
    bench = series.get(BENCH)
    out = {}
    for n in HORIZONS:
        r = _fwd(name[0], name[1], day, n) if name else None
        b = _fwd(bench[0], bench[1], day, n) if bench else None
        out[n] = (r - b) if r is not None and b is not None else None
    return out


def scorecard(rows, series):
    """-> (table, n_flips): table maps 'PREV→NEW' -> {horizon: {n, mean,
    median, win}} over the flips whose horizon has matured."""
    fls = flips(rows)
    table = {}
    for fl in fls:
        key = f"{fl['prev']}→{fl['new']}"
        ex = flip_excess(fl, series)
        slot = table.setdefault(key, {n: [] for n in HORIZONS})
        for n in HORIZONS:
            if ex[n] is not None:
                slot[n].append(ex[n])
    out = {}
    for key, slot in table.items():
        out[key] = {}
        for n in HORIZONS:
            xs = sorted(slot[n])
            if xs:
                mid = xs[len(xs) // 2] if len(xs) % 2 else \
                    (xs[len(xs) // 2 - 1] + xs[len(xs) // 2]) / 2
                out[key][n] = {"n": len(xs),
                               "mean": sum(xs) / len(xs),
                               "median": mid,
                               "win": sum(x > 0 for x in xs) / len(xs)}
            else:
                out[key][n] = {"n": 0, "mean": None, "median": None,
                               "win": None}
    return out, len(fls)


def render(table, n_flips, ledger_dates):
    lines = [f"Flip scorecard (#14a) — {n_flips} transitions over "
             f"{len(ledger_dates)} ledger dates "
             f"({min(ledger_dates)} → {max(ledger_dates)}); "
             f"excess vs same-day {BENCH}, dividend-adjusted"]
    lines.append(f"{'transition':<24}" + "".join(
        f"{'n':>4}{f'+{n}d mean':>10}{'win%':>6}" for n in HORIZONS))
    for key in sorted(table):
        row = f"{key:<24}"
        for n in HORIZONS:
            c = table[key][n]
            if c["n"]:
                row += (f"{c['n']:>4}{c['mean'] * 100:>+9.1f}%"
                        f"{c['win'] * 100:>5.0f}%")
            else:
                row += f"{0:>4}{'—':>10}{'—':>6}"
        lines.append(row)
    if not table:
        lines.append("(no transitions logged yet)")
    lines.append("flips enter at their recorded ledger date only (R3); a "
                 "horizon column stays — until enough forward days exist.")
    return "\n".join(lines)


if __name__ == "__main__":
    from homily_data import fetch_series
    rows = homily_ledger._read_rows()
    fls = flips(rows)
    need = sorted({f["ticker"] for f in fls}) + [BENCH]
    # ticker -> yahoo symbol via the same maps the digest screens
    import daily_run
    yahoo = {**daily_run.HOLDINGS, **daily_run.WATCH, **daily_run.UNIVERSE}
    series = {}
    for tk in need:
        sym = yahoo.get(tk, tk)
        try:
            bars, adj = fetch_series(sym, rng="1y")
            series[tk] = ([b[0] for b in bars], adj)
        except Exception:
            pass
    table, n = scorecard(rows, series)
    dates = sorted({r["date"] for r in rows}) or ["—"]
    print(render(table, n, dates))
