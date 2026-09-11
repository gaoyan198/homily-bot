#!/usr/bin/env python3
"""
Bars vault (#113, ROADMAP §5) — data durability for the one dependency the
system cannot replace on the day it dies: Yahoo's chart API.

Every engine, every backtest and the live ledger all key off bars that exist
ONLY on Yahoo's servers. A dead endpoint (or a silent history rewrite) could
therefore orphan the ledger — rows nobody can re-derive — and un-reproduce
every published BACKTEST_RESULTS section at once. This module keeps a
committed copy of the tape so neither can happen:

  vault/base-YYYY.json.gz    full listing history of every symbol the daily
                             run touches, written ONCE per year and never
                             rewritten (the "one frozen per year" copy)
  vault/delta-YYYY-MM.json.gz everything since that base, written on the
                             first run of each month; self-contained (each
                             delta carries all bars after the base, not
                             just the month's), so only the newest one is
                             needed to restore and the last 4 are kept
  vault/manifest.json        what is in the vault, what was missing, and
                             which names had their history REWRITTEN since
                             the base (splits re-adjust raw closes;
                             dividends rescale adjusted closes) — the
                             silent-rewrite detector's record

Sizing decided the base+delta shape, not the ROADMAP row's wording
("monthly compressed snapshot"): a full snapshot is ~19 MB, and git keeps
every deleted file forever, so twelve full snapshots a year would grow the
clone by ~230 MB/yr and break the cold-start #115 depends on. One base per
year + a ~1 MB delta per month costs ~20 MB/yr. Recorded in PRD §8.5.

Fidelity: every price Yahoo serves is an exact float32, so prices are stored
with 9 significant digits and cast back through float32 on read — RAW bars
restore BIT-EXACT to what a live fetch returns. Adjusted closes restore
exactly too UNLESS a dividend landed after the base was written: then the
base's adj series is rescaled by the measured factor (float64 multiply,
~1e-7 relative), which no printed figure resolves. A raw-close rewrite in
the base window (a split, a data correction) makes that name's delta carry
its FULL fresh history instead, so a restore never splices old and new
adjustments together.

Restore: `HOMILY_BARS_SOURCE=vault` makes `homily_data.fetch_series` read
from here instead of the network — the same (bars, adj) contract, the same
`rng` windows cut relative to the vault's as-of date. Nothing else changes;
the switch is the whole restore procedure. `python homily_vault.py --drill`
proves it: a throwaway copy of the repo runs the daily digest and one
committed backtest with sockets disabled.

Pure stdlib. Idempotent: the CI step runs daily and writes only when the
year's base or the month's delta is missing, so a failed snapshot day simply
retries tomorrow. Never fatal to the digest (R4) — the workflow step is
continue-on-error and this module raises nothing out of `snapshot()`.
"""
import os, io, re, sys, json, gzip, struct, datetime, shutil, subprocess
from concurrent.futures import ThreadPoolExecutor

HERE = os.path.dirname(os.path.abspath(__file__))
VAULT_DIR = os.path.join(HERE, "vault")
MANIFEST = "manifest.json"
KEEP_DELTAS = 4          # ROADMAP #113: last 4 snapshots (+ one frozen/yr)
OVERLAP = 20             # base bars re-checked for a silent rewrite
MIN_COVERAGE = 0.95      # fewer symbols than this = don't write, retry
MAX_WORKERS = 4          # same bounded fan-out as daily_run (R11)
ENV_SOURCE = "HOMILY_BARS_SOURCE"
ALWAYS = ("SPY", "QQQ", "BTC-USD", "IBIT")   # benchmarks + crypto marks
# The committed backtests' universes — (module, constant). The first drill
# (2026-09-11) FAILED without these: core4's engine-picked arms drew from
# UNIV_B names the daily run never touches (SNAP, U, BYND, DKNG …), so a
# vault of "what the digest fetches" could not reproduce a published table.
# Nearly every harness imports UNIV_A/UNIV_B; the rest keep small lists of
# their own. Validate [80] pins that every module-level ticker list in a
# harness is registered here.
BACKTEST_UNIVERSES = (
    ("homily_strategy_backtest", ("UNIV_A", "UNIV_B")),
    ("homily_bear_backtest", ("GRIND_UNIV",)),
    ("homily_quality_backtest", ("WRECKS", "GREATS")),
    ("homily_danny_backtest", ("TICKERS",)),
    ("homily_vol_backtest", ("TICKERS",)),
    ("homily_core4_backtest", ("DANNY4",)),
)


def _f32(x):
    """Yahoo prices are exact float32; the codec round-trips through it."""
    return struct.unpack("f", struct.pack("f", x))[0]


def _sig9(x):
    return float(f"{x:.9g}")


# --- codec -----------------------------------------------------------------
def encode(bars, adj):
    """(bars, adj) -> compact columnar dict. Prices at 9 significant digits
    (float32-exact on decode), dates ISO, volumes as-is."""
    return {"d": [b[0].isoformat() for b in bars],
            "o": [_sig9(b[1]) for b in bars], "h": [_sig9(b[2]) for b in bars],
            "l": [_sig9(b[3]) for b in bars], "c": [_sig9(b[4]) for b in bars],
            "v": [int(b[5]) for b in bars], "a": [_sig9(x) for x in adj]}


def decode(cols, adj_scale=1.0):
    """columnar dict -> (bars, adj) in the homily_data contract."""
    bars = [(datetime.date.fromisoformat(d), _f32(o), _f32(h), _f32(l),
             _f32(c), v)
            for d, o, h, l, c, v in zip(cols["d"], cols["o"], cols["h"],
                                        cols["l"], cols["c"], cols["v"])]
    if adj_scale == 1.0:
        adj = [_f32(a) for a in cols["a"]]
    else:
        adj = [_f32(a) * adj_scale for a in cols["a"]]
    return bars, adj


def _dump(obj, path):
    raw = json.dumps(obj, separators=(",", ":")).encode()
    with gzip.open(path, "wb", compresslevel=9) as f:
        f.write(raw)
    return os.path.getsize(path)


def _load(path):
    with gzip.open(path, "rb") as f:
        return json.load(f)


# --- what goes in ----------------------------------------------------------
def symbols():
    """Every Yahoo symbol the daily run can touch: held + watch + hand
    universe + proxy constituents + the mechanical universe.json screen +
    benchmarks/crypto marks. Read from the live modules so a book change is
    vaulted the next month without anyone remembering to."""
    import daily_run, homily_universe, homily_cryptocycle   # lazy: heavy
    out = set(ALWAYS) | {homily_cryptocycle.HYPE_SYM}
    out |= set(daily_run.HOLDINGS.values()) | set(daily_run.WATCH.values())
    out |= set(daily_run.UNIVERSE.values())
    for members in daily_run.PROXY_CONSTITUENTS.values():
        out |= set(members.values())
    out |= set(homily_universe.load_names())
    out |= backtest_symbols()
    return sorted(s for s in out if s)


def backtest_symbols():
    import importlib
    out = set()
    for mod, attrs in BACKTEST_UNIVERSES:
        m = importlib.import_module(mod)
        for a in attrs:
            out |= set(getattr(m, a))
    return out


def _fetch_all(syms, today, fetch):
    """symbol -> (bars, adj) for every symbol that fetched; bars dated on or
    after `today` are dropped so the vault holds only SETTLED sessions (an
    Asian name fetched at 09:00 SGT has a live partial bar)."""
    def one(s):
        try:
            bars, adj = fetch(s, rng="max")
            keep = [i for i, b in enumerate(bars) if b[0] < today]
            return s, ([bars[i] for i in keep], [adj[i] for i in keep])
        except Exception:                                # noqa: BLE001
            return s, None
    try:
        with ThreadPoolExecutor(max_workers=MAX_WORKERS) as ex:
            res = list(ex.map(one, syms))
    except Exception:                                    # noqa: BLE001
        res = [one(s) for s in syms]
    return {s: v for s, v in res if v and v[0]}


# --- rewrite detection -----------------------------------------------------
def compare(base_cols, bars, adj, overlap=OVERLAP, tol=1e-5):
    """Has this name's history been rewritten since the base was written?
    Checks the base's last `overlap` dates against the fresh tape:
      -> ("same", 1.0)        raw and adjusted closes identical
      -> ("dividend", k)      raw identical, adjusted rescaled by constant k
      -> ("rewrite", None)    raw closes differ / dates missing / adj
                              inconsistent — the delta must carry full
                              history for this name"""
    fresh = {b[0].isoformat(): (b[4], a) for b, a in zip(bars, adj)}
    dates = base_cols["d"][-overlap:]
    bc = base_cols["c"][-overlap:]
    ba = base_cols["a"][-overlap:]
    ratios = []
    for d, c, a in zip(dates, bc, ba):
        if d not in fresh:
            return "rewrite", None
        fc, fa = fresh[d]
        if abs(fc - _f32(c)) > tol * abs(fc):
            return "rewrite", None
        if _f32(a) == 0:
            return "rewrite", None
        ratios.append(fa / _f32(a))
    if not ratios:
        return "rewrite", None
    k = sorted(ratios)[len(ratios) // 2]
    if any(abs(r - k) > tol * k for r in ratios):
        return "rewrite", None
    return ("same", 1.0) if abs(k - 1.0) <= tol else ("dividend", k)


# --- write -----------------------------------------------------------------
def _manifest(vault):
    p = os.path.join(vault, MANIFEST)
    if os.path.exists(p):
        with open(p) as f:
            return json.load(f)
    return {"_v": 1, "files": {}}


def _save_manifest(m, vault, today):
    m["updated"] = today.isoformat()
    with open(os.path.join(vault, MANIFEST), "w") as f:
        json.dump(m, f, indent=1, sort_keys=True)
        f.write("\n")


def write_base(fetched, today, vault=None):
    """The year's frozen copy. Refuses to overwrite — a base is immutable."""
    vault = vault or VAULT_DIR
    name = f"base-{today.year}.json.gz"
    path = os.path.join(vault, name)
    if os.path.exists(path):
        return None
    doc = {"_v": 1, "kind": "base", "asof": today.isoformat(),
           "symbols": {s: encode(*fetched[s]) for s in sorted(fetched)}}
    size = _dump(doc, path)
    return name, {"kind": "base", "asof": today.isoformat(),
                  "symbols": len(fetched), "bytes": size}


def write_delta(fetched, today, base_name, vault=None):
    """Everything since the base, for every symbol — plus the rewrite
    verdicts. Names whose base history was rewritten (or that are new since
    the base) carry FULL history here (`full` list in the manifest)."""
    vault = vault or VAULT_DIR
    name = f"delta-{today.year}-{today.month:02d}.json.gz"
    path = os.path.join(vault, name)
    base = _load(os.path.join(vault, base_name))["symbols"]
    syms, full, rewrites, dividends = {}, [], [], []
    for s in sorted(fetched):
        bars, adj = fetched[s]
        if s not in base:
            full.append(s)
            syms[s] = {"full": True, **encode(bars, adj)}
            continue
        verdict, k = compare(base[s], bars, adj)
        if verdict == "rewrite":
            full.append(s)
            rewrites.append(s)
            syms[s] = {"full": True, **encode(bars, adj)}
            continue
        if verdict == "dividend":
            dividends.append(s)
        last = datetime.date.fromisoformat(base[s]["d"][-1])
        keep = [i for i, b in enumerate(bars) if b[0] > last]
        syms[s] = {"full": False, "adj_scale": k,
                   **encode([bars[i] for i in keep], [adj[i] for i in keep])}
    doc = {"_v": 1, "kind": "delta", "asof": today.isoformat(),
           "base": base_name, "symbols": syms}
    size = _dump(doc, path)
    return name, {"kind": "delta", "asof": today.isoformat(),
                  "base": base_name, "symbols": len(syms), "bytes": size,
                  "full": full, "rewrites": rewrites,
                  "dividends": len(dividends)}


def prune(vault=None, keep=KEEP_DELTAS):
    """Keep the newest `keep` deltas; bases are never pruned."""
    vault = vault or VAULT_DIR
    m = _manifest(vault)
    deltas = sorted(n for n in m["files"] if n.startswith("delta-"))
    gone = deltas[:-keep] if len(deltas) > keep else []
    for n in gone:
        p = os.path.join(vault, n)
        if os.path.exists(p):
            os.remove(p)
        m["files"].pop(n, None)
    return m, gone


def snapshot(today=None, fetch=None, vault=None, syms=None):
    """The idempotent monthly job. -> list of human lines (for the CI log
    and, on a rewrite, the digest's data-QA footer). Never raises."""
    vault = vault or VAULT_DIR
    notes = []
    try:
        today = today or datetime.datetime.now(datetime.timezone.utc).date()
        if fetch is None:
            from homily_data import fetch_series as fetch
        os.makedirs(vault, exist_ok=True)
        m = _manifest(vault)
        base_name = f"base-{today.year}.json.gz"
        delta_name = f"delta-{today.year}-{today.month:02d}.json.gz"
        need_base = base_name not in m["files"]
        need_delta = delta_name not in m["files"]
        if not (need_base or need_delta):
            return [f"vault: {delta_name} present, nothing to do"]
        syms = syms or symbols()
        fetched = _fetch_all(syms, today, fetch)
        missing = sorted(set(syms) - set(fetched))
        cov = len(fetched) / max(1, len(syms))
        if cov < MIN_COVERAGE:
            return [f"vault: only {len(fetched)}/{len(syms)} symbols fetched "
                    f"({cov:.0%}) — not written, retrying tomorrow; missing "
                    f"{', '.join(missing[:8])}{'…' if len(missing) > 8 else ''}"]
        if need_base:
            w = write_base(fetched, today, vault)
            if w:
                w[1]["missing"] = missing
                m["files"][w[0]] = w[1]
                notes.append(f"vault: wrote {w[0]} — {w[1]['symbols']} "
                             f"symbols, {w[1]['bytes'] / 1e6:.1f} MB")
        if need_delta:
            bases = sorted(n for n in m["files"] if n.startswith("base-"))
            if not bases:
                return notes + ["vault: no base to delta against"]
            w = write_delta(fetched, today, bases[-1], vault)
            w[1]["missing"] = missing
            m["files"][w[0]] = w[1]
            notes.append(f"vault: wrote {w[0]} vs {bases[-1]} — "
                         f"{w[1]['symbols']} symbols, {w[1]['bytes'] / 1e3:.0f} KB, "
                         f"{len(w[1]['rewrites'])} rewritten, "
                         f"{w[1]['dividends']} dividend-rescaled, "
                         f"{len(missing)} missing")
            if w[1]["rewrites"]:
                notes.append(rewrite_line(w[1]))
        _save_manifest(m, vault, today)
        m, gone = prune(vault)
        if gone:
            _save_manifest(m, vault, today)
            notes.append(f"vault: pruned {', '.join(gone)}")
    except Exception as e:                               # noqa: BLE001
        notes.append(f"vault: skipped — {type(e).__name__}: {e}")
    return notes


def rewrite_line(entry):
    r = entry["rewrites"]
    return (f"vault: Yahoo REWROTE history since {entry['base']} on "
            f"{len(r)} name{'s' if len(r) != 1 else ''} "
            f"({', '.join(r[:6])}{'…' if len(r) > 6 else ''}) — raw closes "
            "in the base window changed (split or data correction); full "
            "history re-vaulted, levels on those names are on the new tape")


def note(today=None, vault=None):
    """Digest data-QA line: only on the day a delta with rewrites was
    written, so the warning prints once, not all month. -> str or ''."""
    vault = vault or VAULT_DIR
    try:
        today = today or datetime.datetime.now(datetime.timezone.utc).date()
        m = _manifest(vault)
        name = f"delta-{today.year}-{today.month:02d}.json.gz"
        e = m["files"].get(name)
        if e and e.get("asof") == today.isoformat() and e.get("rewrites"):
            return rewrite_line(e)
    except Exception:                                    # noqa: BLE001
        pass
    return ""


# --- read ------------------------------------------------------------------
def active():
    return os.getenv(ENV_SOURCE, "").lower() == "vault"


def _cut(bars, adj, rng, asof):
    """Yahoo's range tokens, relative to the vault's as-of date."""
    if rng == "max" or not bars:
        return bars, adj
    m = re.fullmatch(r"(\d+)(y|mo|d)", rng)
    if not m:
        return bars, adj
    n, unit = int(m.group(1)), m.group(2)
    if unit == "d":                              # 5d = last 5 sessions
        return bars[-n:], adj[-n:]
    if unit == "y":
        y, mo = asof.year - n, asof.month
    else:
        q, r = divmod(asof.month - 1 - n, 12)
        y, mo = asof.year + q, r + 1
    # clamp the day (Feb 29 / 31st) instead of raising
    for day in (asof.day, 30, 29, 28):
        try:
            cutoff = datetime.date(y, mo, day)
            break
        except ValueError:
            continue
    keep = [i for i, b in enumerate(bars) if b[0] >= cutoff]
    return [bars[i] for i in keep], [adj[i] for i in keep]


def _latest(vault):
    m = _manifest(vault)
    deltas = sorted(n for n in m["files"] if n.startswith("delta-"))
    bases = sorted(n for n in m["files"] if n.startswith("base-"))
    if deltas:
        d = m["files"][deltas[-1]]
        return deltas[-1], d["base"], datetime.date.fromisoformat(d["asof"])
    if bases:
        b = m["files"][bases[-1]]
        return None, bases[-1], datetime.date.fromisoformat(b["asof"])
    raise FileNotFoundError(f"vault: nothing in {vault}")


_CACHE = {}


def _doc(vault, name):
    key = (vault, name)
    if key not in _CACHE:
        _CACHE[key] = _load(os.path.join(vault, name))
    return _CACHE[key]


def read_series(symbol, rng="2y", vault=None):
    """The restore path: (bars, adj) exactly as fetch_series would return
    them, from the newest delta + its base. Raises for a symbol the vault
    never held — the same failure a dead fetch produces."""
    vault = vault or VAULT_DIR
    delta_name, base_name, asof = _latest(vault)
    base = _doc(vault, base_name)["symbols"]
    d = _doc(vault, delta_name)["symbols"] if delta_name else {}
    if symbol in d and d[symbol].get("full"):
        bars, adj = decode(d[symbol])
    elif symbol in base:
        bars, adj = decode(base[symbol], (d.get(symbol) or {}).get(
            "adj_scale", 1.0))
        if symbol in d:
            b2, a2 = decode(d[symbol])
            bars, adj = bars + b2, adj + a2
    else:
        raise KeyError(f"{symbol}: not in the bars vault")
    return _cut(bars, adj, rng, asof)


def check(vault=None):
    """Integrity: every symbol in the newest delta+base decodes, dates are
    strictly increasing, bars and adj align. -> (n_ok, problems)."""
    vault = vault or VAULT_DIR
    delta_name, base_name, _ = _latest(vault)
    syms = set(_doc(vault, base_name)["symbols"])
    if delta_name:
        syms |= set(_doc(vault, delta_name)["symbols"])
    ok, bad = 0, []
    for s in sorted(syms):
        try:
            bars, adj = read_series(s, "max", vault)
            if len(bars) != len(adj) or not bars:
                raise ValueError("misaligned/empty")
            if any(bars[i][0] >= bars[i + 1][0] for i in range(len(bars) - 1)):
                raise ValueError("dates not increasing")
            ok += 1
        except Exception as e:                           # noqa: BLE001
            bad.append(f"{s}: {e}")
    return ok, bad


# --- the restore drill (ROADMAP #113 gate) ---------------------------------
_NET_OFF = r"""
import socket
def _dead(*a, **k): raise OSError("network disabled by the vault drill")
socket.create_connection = _dead
socket.socket.connect = _dead
"""

def drill(target=None):
    """Prove the gate: in a throwaway copy of the repo, with sockets
    disabled and HOMILY_BARS_SOURCE=vault, (1) the daily digest builds and
    (2) one committed backtest runs — and its output matches the same
    backtest run against the live network. -> (ok, report_lines)."""
    target = target or "homily_core4_backtest.py"
    tmp = os.path.join(os.getenv("TMPDIR", "/tmp"), "homily_vault_drill")
    shutil.rmtree(tmp, ignore_errors=True)
    shutil.copytree(HERE, tmp, ignore=shutil.ignore_patterns(
        ".git", "__pycache__", "*.pyc"))
    env_v = {**os.environ, ENV_SOURCE: "vault"}
    for k in ("TELEGRAM_BOT_TOKEN", "TELEGRAM_CHAT_ID", "IBKR_FLEX_TOKEN"):
        env_v.pop(k, None)
    lines, ok = [], True
    # (1) full daily run, network off, vault on
    code = (_NET_OFF + "\nimport daily_run\n"
            "d, a, c = daily_run.build_digest()\n"
            "print('DIGEST_CHARS', len(d), 'CHARTS', len(c))\n")
    r = subprocess.run([sys.executable, "-c", code], cwd=tmp, env=env_v,
                       capture_output=True, text=True, timeout=900)
    tail = [ln for ln in r.stdout.splitlines() if ln.startswith("DIGEST_CHARS")]
    if r.returncode == 0 and tail:
        lines.append(f"daily run from vault, network off: OK ({tail[-1]})")
    else:
        ok = False
        lines.append("daily run from vault, network off: FAILED\n"
                     + (r.stderr or r.stdout)[-1500:])
    # (2) one committed backtest: vault/no-network vs live network
    r_v = subprocess.run([sys.executable, "-c", _NET_OFF + f"\nimport runpy\n"
                          f"runpy.run_path('{target}', run_name='__main__')"],
                         cwd=tmp, env=env_v, capture_output=True, text=True,
                         timeout=1800)
    r_n = subprocess.run([sys.executable, target], cwd=tmp,
                         env={k: v for k, v in env_v.items() if k != ENV_SOURCE},
                         capture_output=True, text=True, timeout=1800)
    if r_v.returncode != 0:
        ok = False
        lines.append(f"{target} from vault: FAILED\n{r_v.stderr[-1500:]}")
    elif r_n.returncode != 0:
        ok = False
        lines.append(f"{target} live: FAILED\n{r_n.stderr[-1500:]}")
    elif r_v.stdout == r_n.stdout:
        lines.append(f"{target}: vault output == live output "
                     f"({len(r_v.stdout.splitlines())} lines, byte-identical)")
    else:
        ok = False
        import difflib
        diff = list(difflib.unified_diff(r_n.stdout.splitlines(),
                                         r_v.stdout.splitlines(),
                                         "live", "vault", lineterm="", n=0))
        lines.append(f"{target}: vault output DIFFERS from live "
                     f"({len(diff)} diff lines)\n" + "\n".join(diff[:40]))
    shutil.rmtree(tmp, ignore_errors=True)
    return ok, lines


if __name__ == "__main__":
    if "--drill" in sys.argv:
        tgt = [a for a in sys.argv[1:] if a.endswith(".py")]
        ok, lines = drill(tgt[0] if tgt else None)
        print("\n".join(lines))
        print("DRILL", "PASS" if ok else "FAIL")
        sys.exit(0 if ok else 1)
    if "--check" in sys.argv:
        n, bad = check()
        print(f"vault check: {n} symbols OK, {len(bad)} problems")
        for b in bad:
            print("  ", b)
        sys.exit(1 if bad else 0)
    for ln in snapshot():
        print(ln)
