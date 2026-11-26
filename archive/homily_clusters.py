#!/usr/bin/env python3
"""
Concentration / correlation lens (backlog #29, design D-29).
============================================================

The highest-expected-value risk feature in the plan: the current book is
largely one trade wearing many tickers, and nothing in the digest said so.
90 trading days of daily log returns per held USD name → threshold graph
at ρ ≥ 0.60 → connected components (plain BFS; a component is explainable
in one digest line, which is the actual requirement — D-29 rejected
hierarchical linkage for exactly that reason). Pairs need ≥ 60 overlapping
days (HK holidays) or the pair contributes no edge. Weights are position
VALUE (#27's book math). Labels come from the owner-maintained "sector"
field in holdings.json.

Output: one digest line ("book clusters: AI/semis 68% (NVDA AMD …) ·
other 18%") plus a nudge when a ⭐ add would deepen a >60% cluster.
Info-only forever unless a future gated study promotes it (D-29).
Engines frozen (§0): consumes bars the screen already fetched.
"""
import math

import homily_positions

RHO = 0.60           # D-29: edge threshold on 90d daily-log-return corr
MIN_OVERLAP = 60     # D-29: pairs need ≥60 overlapping days (HK holidays)
WINDOW = 90
WARN_PCT = 60.0      # PRD #29: warn when a ⭐ add deepens a >60% cluster


def log_returns(bars, n=WINDOW):
    """-> {date: daily log return} over the last n returns."""
    out, prev = {}, None
    for b in bars[-(n + 1):]:
        d, c = b[0], b[4]
        if prev and prev > 0 and c > 0:
            out[d] = math.log(c / prev)
        prev = c
    return out


def corr(ra, rb, min_overlap=MIN_OVERLAP):
    """Pearson on the overlapping dates; None below the overlap floor."""
    ks = sorted(set(ra) & set(rb))
    if len(ks) < min_overlap:
        return None
    xs, ys = [ra[k] for k in ks], [rb[k] for k in ks]
    n = len(ks)
    mx, my = sum(xs) / n, sum(ys) / n
    sx = sum((x - mx) ** 2 for x in xs)
    sy = sum((y - my) ** 2 for y in ys)
    if sx <= 0 or sy <= 0:
        return None
    cov = sum((x - mx) * (y - my) for x, y in zip(xs, ys))
    return cov / math.sqrt(sx * sy)


def components(rets, rho=RHO):
    """Threshold graph -> connected components (BFS), singletons included."""
    tks = sorted(rets)
    adj = {t: set() for t in tks}
    for i, a in enumerate(tks):
        for b in tks[i + 1:]:
            r = corr(rets[a], rets[b])
            if r is not None and r >= rho:
                adj[a].add(b)
                adj[b].add(a)
    seen, comps = set(), []
    for t in tks:
        if t in seen:
            continue
        stack, comp = [t], []
        while stack:
            u = stack.pop()
            if u in seen:
                continue
            seen.add(u)
            comp.append(u)
            stack.extend(adj[u] - seen)
        comps.append(sorted(comp))
    return comps


def concentration(all_bars, positions, prices):
    """Held, priced, USD, non-index names -> value-weighted clusters.
    -> {"clusters": [{"label","pct","tickers"}...] desc by pct, "book"} or
    None when there's nothing meaningful to cluster."""
    book = homily_positions.stock_book_value(positions, prices)
    if book <= 0:
        return None
    rets, val, sect = {}, {}, {}
    for tk, p in positions.items():
        if p.get("bucket") == "A" or p.get("currency", "USD") != "USD":
            continue
        bars, px = all_bars.get(tk), prices.get(tk)
        if not bars or px is None:
            continue
        rets[tk] = log_returns(bars)
        val[tk] = p["shares"] * px
        sect[tk] = p.get("sector", "other")
    if len(rets) < 2:
        return None
    out = []
    for comp in components(rets):
        v = sum(val[t] for t in comp)
        labels = [sect[t] for t in comp]
        label = max(sorted(set(labels)), key=labels.count)
        out.append({"label": label, "pct": 100.0 * v / book,
                    "tickers": sorted(comp, key=lambda t: -val[t])})
    out.sort(key=lambda c: (-c["pct"], c["label"]))
    return {"clusters": out, "book": book}


def combined_view(conc, extra):
    """#97 / D-97 — the cross-book view (G5's named risk instrumented).

    `conc` is the CORE concentration() output; `extra` is a list of
    {"ticker","sector","value","book"} for the swing sleeve's open positions
    and the external ESPP shares — the exposures #29's holdings-only lens
    cannot see. The correlation math (`corr`/`components`) is UNTOUCHED: the
    extras join by ticker membership or by their declared sector label (they
    usually lack 90d bars in a homily run), never by a new correlation. This
    is input assembly, not a new signal.

    -> {"rows":[{label, core_pct, comb_pct, tickers, added, overlap}...] desc
    by combined %, "combined_book", "overlap_names"} or None when there is
    nothing extra to fold in."""
    if not conc or not extra:
        return None
    core_book = conc["book"]
    extra_val = sum(e["value"] for e in extra if e.get("value"))
    if core_book <= 0 or extra_val <= 0:
        return None
    combined_book = core_book + extra_val
    clusters = [dict(c, cval=c["pct"] / 100.0 * core_book)
                for c in conc["clusters"]]
    added = [0.0] * len(clusters)
    overlap = [[] for _ in clusters]
    for e in extra:
        v = e.get("value") or 0.0
        for i, c in enumerate(clusters):
            if e["ticker"] in c["tickers"] or e.get("sector") == c["label"]:
                added[i] += v
                if e["ticker"] in c["tickers"]:
                    overlap[i].append(e["ticker"])
                break
    rows = []
    for i, c in enumerate(clusters):
        rows.append({
            "label": c["label"],
            "core_pct": 100.0 * c["cval"] / core_book,
            "comb_pct": 100.0 * (c["cval"] + added[i]) / combined_book,
            "tickers": c["tickers"], "added": added[i],
            "overlap": overlap[i]})
    rows.sort(key=lambda r: (-r["comb_pct"], r["label"]))
    return {"rows": rows, "combined_book": combined_book,
            "overlap_names": sorted({t for o in overlap for t in o})}


def combined_render(cv, esc):
    """-> digest lines for the cross-book view, or [] when the swing sleeve
    and ESPP don't change the core picture (silent by default — a line only
    when it says something new). Info-only."""
    if not cv or not cv["rows"]:
        return []
    top = cv["rows"][0]
    # speak only when swing/ESPP actually DEEPENED the dominant cluster — a
    # disjoint add that merely dilutes the denominator is not news (the core
    # lens already reported it). `added <= 0` → silent.
    if top["added"] <= 0 or (top["comb_pct"] - top["core_pct"] < 1.0
                             and top["comb_pct"] <= WARN_PCT):
        return []
    lines = [f"🔗 across both books: {esc(top['label'])} "
             f"{top['core_pct']:.0f}% core → {top['comb_pct']:.0f}% with "
             f"swing+ESPP (of ${cv['combined_book']:,.0f})"]
    if top["comb_pct"] > WARN_PCT and len(top["tickers"]) > 1:
        lines.append(f"⚠️ combined {esc(top['label'])} exposure "
                     f"{top['comb_pct']:.0f}% > {WARN_PCT:.0f}% across both "
                     "books (G5) — a swing entry here doubles the core bet; "
                     "info only, the rotation is unchanged")
    if cv["overlap_names"]:
        lines.append(f"　same name in both books: "
                     f"{esc(' '.join(cv['overlap_names']))} (G5 max-2 watch)")
    return lines


def render(conc, stars, esc):
    """-> list of digest lines: the cluster line + (maybe) the ⭐ nudge.
    `stars` = today's ⭐ tickers among held names."""
    multi = [c for c in conc["clusters"] if len(c["tickers"]) > 1]
    single_pct = sum(c["pct"] for c in conc["clusters"]
                     if len(c["tickers"]) == 1)
    bits = [f'{esc(c["label"])} {c["pct"]:.0f}% '
            f'({esc(" ".join(c["tickers"]))})' for c in multi]
    if single_pct > 0.5 or not multi:
        bits.append(f"other {single_pct:.0f}%")
    lines = ["🧲 book clusters (90d corr ≥ 0.6, % of stock book): "
             + " · ".join(bits)]
    top = conc["clusters"][0] if conc["clusters"] else None
    if top and top["pct"] > WARN_PCT and len(top["tickers"]) > 1:
        deepen = [t for t in stars if t in top["tickers"]]
        for t in deepen:
            lines.append(f'⚠️ ⭐ {esc(t)} deepens the {top["pct"]:.0f}% '
                         f'{esc(top["label"])} cluster — non-cluster ⭐ '
                         'first per PLAYBOOK §3')
    return lines
