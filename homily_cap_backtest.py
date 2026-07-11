#!/usr/bin/env python3
"""
Hard-rule audit — price the declared constants (#67, design D-67).
==================================================================

The 10%/name add-cap (PLAYBOOK §3.4) was never backtested, and the adopted
emergent arm (§5g) never enforces it. A declared rule is insurance; this
prices it: PREMIUM = what the cap costs on realized paths, PAYOUT = what
it saves when the biggest name gaps down and never comes back.

  Step 1  cap sweep: emergent equal-weight adds + add_cap ∈
          {5,10,15,20,25,∞}% × skipped-cash ∈ {redistribute to remaining
          picks, send to index core}. Multiwindow protocol (max-range
          fetch, full prefixes, §3.5 month calendar), universes A and B,
          MOIC/CAGR/MaxDD/final+peak concentration + CAP-BINDING months.
          Weight checked on add day only — the cap gates adds, never
          forces sells (§5.1's earned-pass survives by construction).
  Step 2a natural wreck pricing: per cap, the worst single-name damage
          (invested − final value, % of paid) — if wrecks lose ⭐ long
          before they reach 10%, the cap binds only on winners, and THAT
          is the finding.
  Step 2b synthetic shock: at the book's peak-top1 date, gap the top name
          −50/−80/−95% overnight, no recovery; rerun per cap. The payout
          table — what 10% vs ∞ buys when the top name is the next LCID.
  Step 5  max-⭐-names sweep {3,5,8,∞} (picks kept by 12m RS, the live
          ordering's spirit) + the 30/50/70 stock-half blend frontier
          (info-only forever — §7 defines the split behaviourally).

(Step 3, Bucket-B threshold sensitivity, runs in homily_bear_backtest.py
via --bucketb; step 4, the whale cap derivation, in
homily_whale_backtest.py --dispersion.)

Fidelity guard (D-67's regression, printed first): on a 5y fetch of
universe B, the uncapped/redistribute arm must reproduce
homily_emergent_backtest.run_emergent's EQ numbers to 1e-9 — same
arithmetic, provably, before any sweep number is read.

Decision rule (pre-committed in D-67, restated before the run): the cap
moves ONLY if, on universe B, an alternative ties-or-beats the 10% arm's
MOIC in a majority of windows AND its synthetic-shock MaxDD stays within
5 pts of the 10% arm. May move UP, never OFF. Whatever wins, PLAYBOOK
§3.4 gains one sentence quoting the measured premium.
"""
import bisect
import datetime

from homily_data import fetch_daily
from homily_danny import danny_signal
from homily_strategy_backtest import COST, UNIV_A, UNIV_B, month_first_idx, \
    close_on
from homily_emergent_backtest import run_emergent
from homily_multiwindow_backtest import WINDOWS

CAPS = (0.05, 0.10, 0.15, 0.20, 0.25, None)          # None = uncapped
MIN_BARS = 260


class SigCache:
    """state ('ACC'/'BOT'/None) + raw 12m RS per (name, month) — one live
    danny_signal pass reused by every sweep arm. Per-name invalidation so
    the synthetic shock recomputes only the shocked name."""

    def __init__(self, data, spy):
        self.data = data
        self.spy_dates = [b[0] for b in spy]
        self.spy_closes = [b[4] for b in spy]
        self.cache = {}

    def invalidate(self, name):
        for k in [k for k in self.cache if k[0] == name]:
            del self.cache[k]

    def get(self, n, d):
        k = (n, d)
        if k in self.cache:
            return self.cache[k]
        bars = [b for b in self.data[n] if b[0] <= d]
        st, rs = None, 0.0
        if len(bars) >= MIN_BARS:
            try:
                s = danny_signal(n, bars).state
                st = {"ACCUMULATE": "ACC", "BOTTOMING": "BOT"}.get(s)
            except Exception:
                st = None
            closes = [b[4] for b in bars]
            si = bisect.bisect_right(self.spy_dates, d) - 1
            look = min(252, len(closes) - 1, si)
            if look > 0:
                rs = ((closes[-1] / closes[-1 - look])
                      - (self.spy_closes[si] / self.spy_closes[si - look]))
        self.cache[k] = (st, rs)
        return self.cache[k]


def run_capped(names, sc, spy, cap, skip_mode="redistribute", win=None,
               max_names=None):
    """Emergent equal-weight adds under an add-day weight cap. Returns a
    dict of everything D-67's tables read. Mirrors run_emergent's loop
    exactly (regression-proven) when cap=None, redistribute, no max."""
    months = [spy[i][0] for i in month_first_idx(spy)][1:]
    if win:
        months = [m for m in months if win[0] <= m <= win[1]]
    data = sc.data
    hold, cash, core = {}, 0.0, 0.0
    invested = {}
    nav, units, unit_val = [], 0.0, 1.0
    top4_peak, top1_peak, top1_info = 0.0, 0.0, None
    binding = add_months = 0

    for d in months:
        ipx = close_on(spy, d) or 0
        val = cash + core * ipx + sum(sh * (close_on(data[n], d) or 0)
                                      for n, sh in hold.items())
        if units > 0:
            unit_val = val / units
        nav.append(unit_val)
        cash += 1.0
        units += 1.0 / unit_val

        cands, backs = [], []
        for n in names:
            st, rs = sc.get(n, d)
            if st == "ACC":
                cands.append((n, rs))
            elif st == "BOT":
                backs.append((n, rs))
        picks = [n for n, _ in (cands or backs)]
        if max_names and picks:
            ranked = sorted((cands or backs), key=lambda t: -t[1])
            picks = [n for n, _ in ranked[:max_names]]

        if picks and cash > 0:
            add_months += 1
            tot = val + 1.0                     # book incl. this month's $1
            skipped = []
            if cap is not None:
                pxs = {n: close_on(data[n], d) for n in picks}
                w = {n: (hold.get(n, 0) * (pxs[n] or 0)) / tot for n in picks}
                skipped = [n for n in picks if w[n] >= cap]
            allowed = [n for n in picks if n not in skipped]
            if skipped:
                binding += 1
            if skip_mode == "redistribute":
                spend = cash if allowed else 0.0
                per = {n: spend * (1 - COST) / len(allowed) for n in allowed}
            else:                               # skipped share -> index core
                per_slice = cash * (1 - COST) / len(picks)
                per = {n: per_slice for n in allowed}
                if skipped and ipx > 0:
                    core += per_slice * len(skipped) / ipx
                    cash -= cash * len(skipped) / len(picks)
            for n in allowed:
                px = close_on(data[n], d)
                if px:
                    hold[n] = hold.get(n, 0) + per[n] / px
                    invested[n] = invested.get(n, 0.0) + per[n]
            if allowed:
                cash = 0.0

        vals = sorted(((sh * (close_on(data[n], d) or 0), n)
                       for n, sh in hold.items()), reverse=True)
        tot_v = sum(v for v, _ in vals) + cash + core * ipx
        if tot_v > 12 and vals:
            top4_peak = max(top4_peak, sum(v for v, _ in vals[:4]) / tot_v)
            if vals[0][0] / tot_v > top1_peak:
                top1_peak = vals[0][0] / tot_v
                top1_info = (d, vals[0][1])

    d_end = months[-1] if win else spy[-1][0]
    eipx = close_on(spy, d_end) or 0
    final_by = {n: sh * (close_on(data[n], d_end) or 0)
                for n, sh in hold.items()}
    final = cash + core * eipx + sum(final_by.values())
    paid = float(len(months))
    nav.append(final / units)
    yrs = paid / 12
    cagr = (nav[-1] / nav[0]) ** (1 / yrs) - 1
    mdd = min(nav[j] / max(nav[:j + 1]) - 1 for j in range(1, len(nav)))
    ranked = sorted(final_by.items(), key=lambda kv: -kv[1])
    worst = min(((final_by.get(n, 0) - inv, n) for n, inv in invested.items()),
                default=(0.0, "—"))
    return {"moic": final / paid, "cagr": cagr, "mdd": mdd,
            "top1_peak": top1_peak, "top1_info": top1_info,
            "top4_peak": top4_peak,
            "top4_final": (sum(v for _, v in ranked[:4]) / final
                           if final else 0.0),
            "binding": binding, "add_months": add_months,
            "worst_dmg": worst[0] / paid, "worst_name": worst[1]}


def shocked_data(data, name, when, factor):
    out = dict(data)
    out[name] = [(d, o * factor, h * factor, l * factor, c * factor, v)
                 if d > when else (d, o, h, l, c, v)
                 for d, o, h, l, c, v in data[name]]
    return out


def cap_label(c):
    return "uncapped" if c is None else f"{int(c * 100)}%"


def regression(spy5, univ):
    """Uncapped/redistribute must equal run_emergent EQ to 1e-9."""
    data, _ = fetch_all(univ, "5y")
    live = [n for n in univ if n in data]
    ref = run_emergent(live, data, spy5, weighted=False)
    sc = SigCache(data, spy5)
    got = run_capped(live, sc, spy5, cap=None)
    drift = max(abs(ref[0] - got["moic"]), abs(ref[1] - got["cagr"]),
                abs(ref[2] - got["mdd"]))
    print(f"[regression vs run_emergent EQ] MOIC {ref[0]:.4f}/{got['moic']:.4f}"
          f" drift={drift:.2e} {'OK' if drift < 1e-9 else 'DRIFT — VOID'}")
    return drift < 1e-9


def fetch_all(names, rng):
    data, dead = {}, []
    for n in names:
        try:
            data[n] = fetch_daily(n, rng=rng)
        except Exception:
            dead.append(n)
    return data, dead


if __name__ == "__main__":
    spy5 = fetch_daily("SPY", rng="5y")
    if not regression(spy5, UNIV_B):
        raise SystemExit("regression failed — sweep numbers would be void")

    spy = fetch_daily("SPY", rng="max")
    for tag, univ in (("B hype-2021 control (JUDGE ON THIS)", UNIV_B),
                      ("A current univ (HINDSIGHT, upper bound)", UNIV_A)):
        data, dead = fetch_all(univ, "max")
        live = [n for n in univ if n in data]
        sc = SigCache(data, spy)
        print(f"\n{'#' * 74}\n# {tag} — {len(live)} names"
              + (f" (dead: {', '.join(dead)})" if dead else "")
              + f"\n{'#' * 74}")

        # Step 1 + 2a — the sweep, every window
        beats = {}
        for w0, w1, wl in WINDOWS:
            print(f"\n── {w0} → {w1} ({wl}) ──")
            print(f"  {'cap':<10}{'skip→':<7}{'MOIC':>6}{'CAGR':>8}"
                  f"{'MaxDD':>7}{'pk1':>6}{'pk4':>6}{'bind':>7}"
                  f"{'worst-name dmg':>16}")
            for cap in CAPS:
                for sk in ("redistribute", "index"):
                    r = run_capped(live, sc, spy, cap, sk, win=(w0, w1))
                    print(f"  {cap_label(cap):<10}{sk[:5]:<7}"
                          f"{r['moic']:>6.2f}{r['cagr'] * 100:>7.1f}%"
                          f"{r['mdd'] * 100:>6.0f}%{r['top1_peak'] * 100:>5.0f}%"
                          f"{r['top4_peak'] * 100:>5.0f}%"
                          f"{r['binding']:>4}/{r['add_months']:<3}"
                          f"{r['worst_dmg'] * 100:>+9.1f}% {r['worst_name']}")
                    # key carries wl too — two windows share a start date
                    beats.setdefault(("_moic", w0, wl, sk),
                                     {})[cap_label(cap)] = r["moic"]
            # majority-of-windows bookkeeping vs the 10% arm
        wins = {}
        for (k0, w0, wl, sk), moics in [(k, v) for k, v in beats.items()
                                        if k[0] == "_moic"]:
            for cl, m in moics.items():
                if cl == "10%":
                    continue
                wins.setdefault((cl, sk), [0, 0])
                wins[(cl, sk)][1] += 1
                if m >= moics["10%"] - 1e-12:
                    wins[(cl, sk)][0] += 1
        print(f"\n  windows where an arm ties-or-beats the 10% arm's MOIC "
              f"(decision input #1):")
        for (cl, sk), (w, n) in sorted(wins.items()):
            print(f"    {cl:<9} {sk:<12} {w}/{n}")

        # Step 2b — synthetic shock, honest universe only, two key windows
        if tag.startswith("B"):
            for w0, w1, wl in ((datetime.date(2021, 7, 1),
                                datetime.date(2026, 7, 1), "5y honest"),
                               (datetime.date(2016, 7, 1),
                                datetime.date(2026, 7, 1), "10y")):
                print(f"\n── STEP 2b synthetic shock — {wl} window ──")
                base = run_capped(live, sc, spy, None, win=(w0, w1))
                when, who = base["top1_info"] or (None, None)
                if not when:
                    print("  (book never concentrated — no shock target)")
                    continue
                print(f"  shock target: {who} gapped at {when} "
                      f"(uncapped book's peak-top1 date)")
                print(f"  {'cap':<10}" + "".join(f"{'MOIC@' + f:>9}{'DD@' + f:>8}"
                                                 for f in ("-50%", "-80%", "-95%")))
                for cap in CAPS:
                    row = f"  {cap_label(cap):<10}"
                    for factor in (0.5, 0.2, 0.05):
                        sd = shocked_data(data, who, when, factor)
                        ssc = SigCache(sd, spy)
                        # reuse every cached signal except the shocked name
                        ssc.cache = {k: v for k, v in sc.cache.items()
                                     if k[0] != who}
                        r = run_capped(live, ssc, spy, cap, win=(w0, w1))
                        row += f"{r['moic']:>9.2f}{r['mdd'] * 100:>7.0f}%"
                    print(row, flush=True)

        # Step 5 — max-⭐ sweep + the blend frontier (info-only)
        w0, w1 = datetime.date(2021, 7, 1), datetime.date(2026, 7, 1)
        print(f"\n── STEP 5 max-⭐-names sweep (10% cap, redistribute, "
              f"2021-07→2026-07) ──")
        moics = {}
        for mx in (3, 5, 8, None):
            r = run_capped(live, sc, spy, 0.10, win=(w0, w1), max_names=mx)
            moics[mx] = r["moic"]
            print(f"  max {mx or '∞':<4} MOIC {r['moic']:>5.2f}  "
                  f"CAGR {r['cagr'] * 100:>6.1f}%  MaxDD {r['mdd'] * 100:>4.0f}%")
        from homily_strategy_backtest import run_dca
        dm, _, _ = run_dca(spy, spy, win=(w0, w1))
        print(f"\n  50/50 frontier (blend of DCA-SPY MOIC {dm:.2f} and the "
              f"max-∞ arm; §7 split is behavioural, info-only):")
        for wgt in (0.3, 0.5, 0.7):
            print(f"    stock-half {int(wgt * 100)}%: blended MOIC "
                  f"{wgt * moics[None] + (1 - wgt) * dm:.2f}")
