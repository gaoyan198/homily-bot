# GAMBIT LEVERAGE_MEMO — can 10–20% leverage flip the Phase-1 verdict? (2026-07-11)

**Status: Fable analysis memo answering an owner question logged
2026-07-11. No protocol change. G7 (unlevered, ever) and EXECUTION
prime directive 2 (no margin, even simulated) stand unless every reopen
condition in §4 is met and signed.**

**The question (owner, 2026-07-11):** Phase 1 passed no promotable
candidate (BACKTEST_RESULTS.md, 2026-07-10). Separately, a May→July
real-money side experiment — following @theaiportfolios calls (NOW,
AVGO, RDDT, VST, ZETA, ~US$1k per position, levered) — closed
+US$2k. Would re-running Phase 1 with 10–20% leverage clear the gate?

---

## 1. Answer up front

**No — and not because the rulebook forbids it. Because of arithmetic.**
The gate's random-p90 condition is blind to leverage: applying a common
leverage factor L to a candidate and to the 200-draw luck band is the
monotone transform x → x^L — it lifts every number and reorders none of
them. Every failed candidate failed the p90 condition on **all three**
qualifying windows, so no leverage level — 1.1×, 2×, 5× — changes that
column. Leverage amplifies whatever sign the edge has; it cannot create
the sign. This memo shows the bound cell by cell so the question never
needs a build session.

| gate condition | responds to leverage? |
|---|---|
| (a) MOIC ≥ QQQ + 0.10 | yes, weakly — but even a *frictionless* 2× misses every failed cell (§2.1) |
| (b) MAR > QQQ | no — leverage-invariant to first order, strictly worse after financing (§2.2) |
| (c) MOIC > random p90 | **never** — invariant under like-for-like leverage (§2.3) |
| (d) repeat at 0.35% RT | inherits (a)–(c); levered notional also pays more absolute cost |

## 2. The arithmetic, condition by condition

### 2.1 Condition (a) — the frictionless upper bound

Under continuously rebalanced leverage L with **zero** financing cost
and **zero** volatility drag, levered MOIC ≤ MOIC^L. Reality is worse:
IBKR USD margin runs ~BM+1.5% (≈6%/yr on the borrowed slice — at
L=1.2 that alone is ~0.6–1.2 pts/yr of drag, ~3–6 MOIC points over
5y), and vol drag compounds on top. The generous bound, at the owner's
proposed L = 1.2:

| candidate | window | MOIC | ×1.2 bound | needed (QQQ+0.10) | clears? |
|---|---|---:|---:|---:|---|
| S1-stopped | 2019→2024 | 1.50 | 1.63 | 2.90 | ✗ (gap 1.27) |
| S1-stopped | 2020→2025 | 1.60 | 1.76 | 2.56 | ✗ (gap 0.80) |
| S1-stopped | 2021→2026 | 1.17 | 1.21 | 2.11 | ✗ (gap 0.90) |
| S2 pullback | 2019→2024 | 1.02 | 1.02 | 2.90 | ✗ |
| S2 pullback | 2020→2025 | 0.98 | 0.98 | 2.56 | ✗ |
| S2 pullback | 2021→2026 | 0.98 | 0.98 | 2.11 | ✗ |
| S3 vol-hole | 2019→2024 | 1.02 | 1.02 | 2.90 | ✗ |
| S3 vol-hole | 2020→2025 | 1.11 | 1.13 | 2.56 | ✗ |
| S3 vol-hole | 2021→2026 | 1.09 | 1.11 | 2.11 | ✗ |

Even frictionless **2×** (not "some leverage" — doubling) reads 2.25 /
2.56 / 1.37 for S1-stopped against 2.90 / 2.56 / 2.11: one tie, zero
clears. Concretely: at 1.2× the extra return is ≈ 0.2 × (arm CAGR −
financing rate); for S1-stopped at 8.5% CAGR that is ~+0.5 pt/yr —
MOIC 1.50 → ~1.54 after costs. The gaps are measured in whole MOIC
points; the lever moves hundredths.

### 2.2 Condition (b) — MAR

CAGR and MaxDD scale together under leverage, so MAR is invariant to
first order — then strictly degraded, because financing subtracts from
CAGR while drawdowns scale slightly *super*-linearly (gaps are taken in
full on levered notional). S1-stopped's two (b) checkmarks survive
leverage; its (a) and (c) failures don't move. Nothing is gained.

### 2.3 Condition (c) — the referee is leverage-blind

Scored honestly, the random band must carry the same leverage as the
candidate (anything else compares a levered book to an unlevered
benchmark — the exact self-deception the band exists to prevent). Under
common L, ordering is preserved exactly. The distances are not close:
S1-stopped sits at 1.50 vs p90 3.25, 1.60 vs 3.69, 1.17 vs 4.15.
**These arms underperform random selection from their own universe.**
Leverage applied to a below-random arm is leverage applied to negative
relative edge — it grows the shortfall in dollars.

### 2.4 S1-pure — the one arm leverage doesn't even apply to

S1-pure cleared 2/3 windows unlevered. Its blocker is not the gate but
the owner's own directive (PRD §4: every position carries a stop; only
the stopped variant is promotable, *"even if the pure arm backtests
better"*). Leverage doesn't address that blocker — it aggravates the
reason for it: S1-pure's −40…−46% drawdowns become roughly −48…−55%
at 1.2×. If anything were to reopen, the honest lever is that directive
(consciously accepting stop-free −45% drawdowns), not margin — and this
memo recommends against that too; the directive descends from homily's
D-63 evidence for exactly these drawdown paths.

## 3. What the May experiment measured (and didn't)

Logged because it motivated the question, with its limits stated:

* **One ~2-month window in an up-tape.** Leverage samples the right
  tail in bulls by construction; the rule it challenges was written for
  the left tail, which a single bull window cannot price.
* **The counterfactual is not $0.** Unlevered, the same follows earned
  a large fraction of the move. Leverage contributed amplification, not
  selection — and amplification is symmetric.
* **n = a handful of correlated momentum names.** This repo's own
  referee (the 200-draw band) would place one +$2k outcome well inside
  luck. We killed the conviction score on that filter; the same
  standard applies to our own wins.
* **Copy-following is not a registered arm and can never be one:** no
  point-in-time record of the calls exists, so it cannot be backtested
  — only measured live. That is what §5 is for.

## 4. Reopen conditions (pre-registered, so this is a gate, not a slammed door)

Leverage may be revisited iff **all four** hold:

* **L1** — a candidate has passed the Phase-1 gate (or the P2 paper
  bar) fully unlevered. Leverage scales a proven edge; it never
  substitutes for one.
* **L2** — the candidate's unlevered MAR exceeds QQQ's with enough
  headroom that MAR stays above QQQ after ×L drawdown scaling and
  financing at IBKR's then-current rate.
* **L3** — the levered variant is pre-registered as a Part-II protocol
  amendment: financing modeled at BM+1.5%, the random band levered
  identically, a stress cell at rate+2%, and K2's −20% hard stop
  unchanged (leverage tightens effective room; it never loosens a kill
  condition).
* **L4** — owner signs the amendment in writing (two-artifact pattern,
  as with LIVE_ENABLE.md).

Until then: G7 stands, the paper simulator keeps cash ≥ 0, and the
Phase-1 verdict is unchanged by this question.

## 5. The sidecar — if the May-style experiment continues, measure it honestly

The itch is legitimate; the answer is to ring-fence and score it, not
to fold it into GAMBIT's books. Pre-registered rules (defaults are
owner-editable **before** the first trade, frozen after):

1. **Bankroll:** fixed **US$2,000** — the May profit, house money. It
   can go to zero without touching BUY_BUDGET / SRS / ESPP / the GAMBIT
   paper book. No top-ups before the 12-month score; wins may compound
   inside.
2. **Account reality (read twice):** IBKR margin is **account-level**.
   The account already runs 1.23× (PRD §0). A sidecar margin call can
   force liquidation of long-term holdings — the exact unrecoverable
   error homily PLAYBOOK §6 exists to prevent. Therefore: total sidecar
   notional ≤ US$5k, ≤ US$1k margin per position, ≤ 3 concurrent
   positions — sized so a −50% overnight gap on every sidecar name
   cannot breach account maintenance margin. Defined-risk structures or
   a separate account dominate all of this if available.
3. **Every position carries a stop written before entry** and an 8-week
   time stop (D-G3 spirit — no open-ended holds).
4. **Ledger:** `SIDECAR.csv`, append-only: date · ticker · source call
   · margin used · leverage · entry/exit · P&L · **unlevered
   counterfactual P&L** (the honesty column — what the same follow
   earned without margin) · same-dollar QQQ P&L over the holding
   period.
5. **Kill criteria:** bankroll −50% from start → stop, post-mortem
   before any restart. Expectancy ≤ 0 over the trailing 20 closed
   trades → stop.
6. **Score at 12 months (2027-07):** vs same-dollar QQQ buy-and-hold.
   Beat it with ≥20 closed trades and the *counterfactual column*
   showing the leverage (not just the picks) carried the excess → it
   has earned a conversation about formalization under §4. Anything
   less → it was tuition, and cheap at the size.

## 6. Verdict

* Phase-1 verdict **unchanged**; the kill memo owed under PRD §5.2 is
  now written (**KILL_MEMO.md**, 2026-07-11) — this leverage memo never
  substituted for it and does not now.
* **G7 stands.** No levered re-run will be built — §2 shows the result
  without spending a session.
* The real reopening levers for GAMBIT, in honesty order: a **new
  setup hypothesis** registered by amendment (new arms, not leverage on
  dead ones) · a re-examination of the S1-pure stop directive with the
  −45%+ drawdowns accepted in writing (not recommended) · time — the
  paper-phase methodology is the asset, and it keeps.
* The sidecar (§5) is the sanctioned home for the levered follows:
  small, stopped, scored against QQQ, with the counterfactual column
  keeping the wins honest.
