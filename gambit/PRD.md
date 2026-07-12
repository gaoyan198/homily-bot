# GAMBIT — the 4–8 week swing sleeve (PRD v0.2, 2026-07-10)

> A "gambit" is a chess opening where you give up a pawn for position —
> fitting for a game we intend to win against the suits.
> **Name confirmed by owner (D-G5 resolved).**

**Status: P2 PAPER (S1-pure), entered 2026-07-11 by Amendment A4.**
Phase 1 (G-S1…G-S4) built the harness and scored the §4 gate: no arm was
promotable under the original stop directive (KILL_MEMO.md). The owner
then reconsidered that directive for S1-pure — which mechanically cleared
the gate on 2/3 windows — accepting its stop-free −40…−46% drawdowns in
writing (AMENDMENT_A4.md), promoting it to the paper phase. G-S5 (paper
loop + journal) is built; S1-stopped/S2/S3 remain FAILed and unpromoted.
**Paper only: `LIVE_ORDERS` stays `off`, P3/live deferred sine die, no
margin (G7).** P2's gate (§5.2) inherits no credit from the backtest; the
ledger is the real test. DESIGNS.md + EXECUTION.md carry the specs.

---

## 0. Feasibility verdict, up front

**Feasible — with conditions, and with the income goal restated
honestly.** The three claims in the mission, graded against the evidence
we already own from homily-bot:

| Claim | Verdict | Why |
|---|---|---|
| A 4–8 week swing system, low owner load | **Feasible** | 5–8 positions at 4–8wk holds ≈ 1–3 approvals/week + one 30-min weekend session. This is homily's cadence discipline applied faster, not day trading. |
| Outperform buy-and-hold index | **Unproven — the hard part** | Our own honest multi-window verdict (homily BACKTEST_RESULTS §3): the monthly engine beats SPY mostly, does **not** reliably beat QQQ, at 2–3× index drawdown. One gate has passed toward the bar (rs12-top3, +modest MOIC on honest windows). Shortening to 4–8 weeks makes it *harder*, not easier — costs and whipsaw scale with turnover. This PRD's Phase 1 exists to prove or kill it. |
| **Stable** $1k/month income | **Not as stated — restated in §3** | Directional trading produces lumpy expectancy, not salary. "Stable monthly income" from swings is the claim every prop-shop marketing page makes and no honest backtest supports. What IS achievable: a mechanical quarterly skim above high-water mark, smoothed by a reserve, that *averages* $1k/mo once capital reaches ~US$80k **and** the edge is real. |

The structural advantages we genuinely hold (the reason to play at all):

1. **Singapore: no capital-gains tax.** A 4–8wk system turns the book
   ~6–10×/yr; a US trader loses 20–37% of every gain to short-term tax,
   we lose 0%. This is a real, durable edge over most of the "suits".
2. **A validated methodology.** Pre-registered decision rules, honest
   construction-date windows, luck benchmarks (200 random draws),
   append-only hash-guarded ledgers, validate-gates-the-send CI. This is
   rarer than alpha and we already built it.
3. **One passed gate pointing the right way.** #24 proved RS-momentum
   *concentration* (top-3 by 12m relative strength) beat equal-weight,
   random-p90, and crossed QQQ on the fully honest window. Momentum
   selection is the seed hypothesis for GAMBIT.
4. **IBKR MCP order rail with human approval** — bot proposes, owner
   disposes. Matches the risk posture homily's §7/§9 arrived at.

The honest handicaps:

1. Our best honest evidence is **~1–2 pts/yr of alpha over QQQ, on 3
   windows, in trending tapes** — modest, narrow, and it *underperformed*
   in reversal windows (concentrated momentum whipsaws).
2. Academic and practitioner evidence says momentum lives at **3–12
   month** horizons; **under ~1 month is reversal territory**. 4–8 weeks
   sits in the contested middle. The design answer: *select* on 3–12mo
   strength (proven), *hold* 4–8 weeks with re-ranking (to be proven in
   Phase 1) — we are shortening the rebalance, not the signal.
3. The account is already fully deployed at 1.23× leverage
   (S$42.9k net liq, −S$9.8k cash as of 2026-07-10). GAMBIT capital must
   be funded deliberately (§3.4), not conjured.

---

## 1. Mission and the bar

**Mission:** run a 4–8 week swing-trading sleeve as a business whose
product is *withdrawable cash* that funds the long-term DCA engine —
while beating what the same dollars would have done parked in the index.

**The bar (pre-committed, same spirit as homily's):** over every rolling
12-month live window, GAMBIT must beat **QQQ buy-and-hold total return on
the same capital** after costs, and its MaxDD must stay under **1.5× 
QQQ's** in the same window. Miss the bar two consecutive review quarters
→ the pre-committed consequence in §5 fires (de-risk or kill). The
referee is the live ledger, not backtests.

**Non-goals:** day trading; options *strategies* in the MVP (see §8
D-G4); touching homily-bot's BUY_BUDGET, SRS, or ESPP sleeves; any
unattended order placement.

---

## 2. What we import from homily-bot (the learnings)

### 2.1 Evidence (what the backtests actually said)

| Finding | Source | GAMBIT consequence |
|---|---|---|
| RS12 top-3 concentration beat equal/random/QQQ on honest windows; conviction score added nothing over raw RS | BACKTEST_RESULTS §4 (#24, gate PASSED) | Seed hypothesis S1. Rank by relative strength, concentrate, skip composite scores. |
| Time-boxed per-name exit (§5.2) was the **only arm that added return** (+3.4 pts/yr) on the honest control | BACKTEST_RESULTS §2 | Every GAMBIT position carries a hard **time stop** (exit at 8 weeks unless re-qualified) — the "trash-taker". |
| 🐻 regime sell = priced tail insurance (~1pt/yr cost, −29% vs −76% MaxDD in grinders); **freeze-only half-measures are dominated** | D-63 / PRD §5i | GAMBIT carries a regime kill-switch: BEAR flip → close all swings, sit in cash, no half-measures. Insurance is priced in the Phase-1 backtests, not bolted on. |
| Straddling-window losses came from momentum-buying ZM/PTON-class names into a bubble; nothing dodges regime-scale overvaluation | BACKTEST_RESULTS §3 | Accept: GAMBIT will not dodge bubbles either; the regime switch + time stops bound the damage. Don't pretend otherwise in any doc. |
| A curated universe is only out-of-sample AFTER its construction date | standing rule, PRD §5i | GAMBIT's universe is **mechanical from day 1** (D-65 pattern: liquidity gates → top-N cut), construction date stamped, only post-construction windows count as evidence. |
| Yahoo `range=max` silently returns monthly bars; QQQ pre-1999 crash | validate [22] | Port `homily_data.py` fetch (epoch params, non-1d refusal, host rotation, backoff) as GAMBIT's first module — **copy, don't import**, so the two repos stay decoupled. |

### 2.2 Methodology (worth more than the signals)

* **Pre-registration:** every backtest writes its decision rule in the
  file docstring *before the first run*. No best-of-N shopping.
* **Luck benchmark:** every selection claim is tested against ~200
  seeded random draws; a rule must clear the p90 band, not just the mean.
* **Honest windows:** multi-window harness (port of
  `homily_multiwindow_backtest.py`), ≥5y where data allows, MOIC
  money-weighted, construction-date honesty.
* **Append-only ledger:** every signal and fill logged same-day,
  SHA-256 checkpoint over prior rows, retro-edits fail CI. The track
  record IS the product; it starts un-fakeable.
* **Validate gates the send:** self-tests run before any digest/order
  proposal goes out; golden-file tests pin the rendering.
* **Engine freeze + one promoted change per quarter (R10):** once live,
  signal code is frozen outside gated sessions.
* **Fable plans, Opus executes:** this PRD and its DESIGNS/SPECS are
  Fable output; build sessions follow the homily EXECUTION.md handoff
  protocol (restate the gate before coding, validate green before
  commit, never promote a signal the session it ships).

---

## 3. The money math — what $1k/month actually requires

### 3.1 Two honest framings

**Framing A — "total-return income" (the lenient one).** You skim the
sleeve's whole return. $12k/yr at a sustained net CAGR of:

| Net CAGR | Capital needed | Realism check |
|---:|---:|---|
| 10% | $120k | ≈ index; you'd be skimming beta, see Framing B |
| 15% | $80k | ≈ our honest rs12-top3 evidence on a good tape |
| 20% | $60k | above anything we've proven on honest windows |
| 30% | $40k | marketing-page territory; not a planning number |

**Framing B — "alpha income" (the strict one).** If the skim should be
money you *wouldn't have had* holding QQQ (otherwise the honest move is:
hold QQQ and sell $1k of it monthly), then at our evidenced 1–2 pts/yr of
alpha, $12k/yr needs **$600k–1.2M**. At an optimistic-but-defensible 5
pts of alpha: **$240k**.

**Planning position (recommended):** use Framing A for the cash-flow
goal and Framing B for the scoreboard. Target **US$80k sleeve capital at
15% net** as the "$1k/mo average" milestone — while §1's bar keeps us
honest that the skim only *means* something if we're beating QQQ on the
same dollars.

### 3.2 "Stable" — the smoothing mechanism

Swing returns arrive lumpy (our honest windows include −59…−76% strategy
drawdowns; GAMBIT's tighter stops should cut that, but quarters WILL
print red). The income rule is therefore mechanical:

* **Skim rule:** at each quarter-end, if sleeve equity > high-water
  mark, withdraw **50% of the excess** to the DCA account; the rest
  compounds. Below HWM: withdraw nothing.
* **Reserve:** the first US$3k of skims seed a smoothing reserve; the
  "monthly $1k" is paid from the reserve, so a red quarter doesn't stop
  the DCA transfer. Reserve empty → transfers pause (no borrowing to
  fake stability).
* Never withdraw principal; never skim while below the bar (§1).

### 3.3 The realistic glidepath

| Stage | Capital | Expected skim (at ~15%) | Note |
|---|---:|---:|---|
| P3 pilot | US$15–20k | ~$200–250/mo avg | proves live edge; income is a rounding error, ignore it |
| P4 scale-1 | US$40k | ~$500/mo avg | fund from P3 profits + new cash only if bar is green |
| P4 scale-2 | US$80k | **~$1k/mo avg** | the milestone; 12–24 months away *if* every gate passes |

**$1k/month is a milestone reached by compounding a proven edge, not a
setting we can configure on day 1.** Anyone who tells you otherwise is
selling a course.

### 3.4 Where the capital comes from — RESOLVED (D-G1, 2026-07-10)

As of 2026-07-10 the IBKR account holds S$42.9k net liq, fully invested,
1.23× leverage (cash −S$9.8k). **Owner decision: no funds in the
immediate future.** Consequences:

* GAMBIT runs **paper-only** on a notional **US$20k** book until the
  owner explicitly funds it. P3 (live pilot) is **deferred sine die**;
  its gate in §5.2 still applies whenever funding arrives — the paper
  ledger must have earned it first.
* **Monthly results report to the owner** is a hard product requirement
  of the paper phase (spec in DESIGNS D-G6): closed trades with
  R-multiples, expectancy, equity vs QQQ/SPY on the same dollars, MaxDD,
  and a kill-condition dashboard. Delivered via the digest channel and
  committed to `PAPER_RESULTS.md`.
* **IBKR MCP integration is BUILT but SWITCHED OFF** (owner directive):
  the order-proposal module is developed and tested against the paper
  book from day 1, gated by a `LIVE_ORDERS` flag that is `off` in code,
  config, and CI; a validate check fails the build if it is ever `on`
  without an owner-signed enable file. Flipping it is a P3 gate action,
  not a config edit.
* **Margin remains rejected** (risk G7) — applies to the paper book too:
  the simulator refuses entries that would take sleeve cash below zero.

---

## 4. Strategy hypothesis space (to be settled by Phase-1 backtests)

All candidates pre-registered here; the Phase-1 harness runs all of
them + benchmark arms with identical accounting. Costs modeled at
**0.25% round trip** (IBKR tiered commission + spread + slippage) —
at ~8 turns/yr that's ~2 pts/yr of drag the edge must clear *first*.

* **S1 — RS rotation (seed, descends from #24-PASSED):** rank the
  mechanical universe by blended 3m/6m/12m relative strength (skip the
  most recent 2 weeks — classic reversal guard); hold the **top 3–5**;
  re-rank every **4 weeks**; a name exits when it leaves the top decile
  or hits its time stop. This is rs12-top3 with the rebalance shortened
  from "monthly buys, never sell" to full rotation — the delta that must
  prove itself.
* **S2 — Leader pullback:** universe filtered to RS top decile + price
  above rising 20-week trend; enter on a 3–8% pullback toward the 20-day
  mean with a reclaim bar; exit at +2R trail, −1R stop, or the 8-week
  time stop, whichever first.
* **S3 — Volatility-hole breakout (redefined 2026-07-10, owner
  directive + homily §5b evidence):** entry requires the sequence
  *contraction → resolution*: a vol-hole cluster (new 60-day low in
  ATR5/close — port of `homily_vol.py`, already event-studied) forming a
  zone, followed by a close **above** the zone's upper bound with volume
  expansion, in an RS-top-decile name. The prior plain "new-high
  breakout" arm is retired — homily's event study showed the contraction
  precondition is what carried the edge at exactly this horizon (+11.5%
  vs +8.5% baseline fwd 60d). Regime filter ON; same exit stack as S2.
  **Breakdown side (close below the zone): journal-only warning, never
  an entry or exit signal** — the same event study showed breakdowns did
  NOT predict weakness (+15.7% fwd 60d, above baseline). GAMBIT's P1
  harness re-tests this on the mechanical universe; the breakdown rule
  flips only if that re-test overturns homily's verdict.
* **Benchmark arms (mandatory):** QQQ buy-and-hold · SPY buy-and-hold ·
  equal-weight universe rebalanced monthly · 200 seeded random-N draws
  (the luck band). A candidate that can't clear the random p90 is noise,
  full stop — that filter already killed the conviction score once.
* **Overlays priced into every arm:** 🐻 regime kill-switch (all-out,
  no half-measures), 8-week time stop, max 40% of sleeve per position,
  max 2 positions per cluster (G5).
* **Owner directive (2026-07-10): every position carries an explicit
  stop AND take-profit, defined at entry and written to the journal
  before the fill.** The pre-registered exit stack (full spec DESIGNS
  D-G3): initial hard stop at 2×ATR(14) below entry; take profit half at
  +2R; trail the rest at the higher of the initial stop and the 20-day
  low; 8-week time stop; regime kill-switch overrides all. S1's natural
  exit is rank-rotation — it is tested both pure and with this stop
  stack, and **only the stopped version is promotable** (the directive
  binds even if the pure arm backtests better). **[RESCINDED for S1-pure
  by Amendment A4, 2026-07-11: owner reconsidered this directive, accepted
  S1-pure's stop-free −40…−46% drawdowns in writing, and promoted it to
  P2 paper — the one promotion consistent with the gate as scored. The
  directive still binds S1-stopped/S2/S3, which the gate FAILed. See
  AMENDMENT_A4.md.]**

### 4.1 Signal parsimony (owner directive 2026-07-10 — "clean signals, don't pollute the algorithm")

Adopted as a standing constitutional rule, not a preference:

* **Signal budget: each arm uses at most 3 orthogonal inputs** — one
  trend/RS measure, one setup trigger (pullback or vol-hole
  resolution), one regime overlay. No composite scores: homily #24
  proved the 6-component conviction score added *nothing* over raw
  relative strength. Fewer inputs = fewer ways to overfit = a journal
  the owner can actually read.
* **One in, one out.** A proposed new signal must beat the arm
  *without* it on the pre-registered harness AND displace an existing
  input, or it is rejected. The signal count never grows past the
  budget.
* **Silence is a valid output.** The weekly scan proposes at most 2 new
  entries (PRD §5.1) and is expected to propose **zero** in most weeks —
  a quiet week is the system working, not failing. No filler signals,
  no "interesting but not actionable" rows in the digest; those go to
  the journal only.
* **Every signal earns its place with an event study** (homily 5b
  pattern: baseline vs signal forward returns, no look-ahead) before it
  may appear in an arm. Directional support isn't enough; it must
  survive the random-draw band in portfolio context too.

**Pre-registered Phase-1 gate:** promote a candidate only if it beats
QQQ B&H on **MOIC AND MAR (CAGR/MaxDD)** on **≥2 of 3
construction-honest windows**, clears the random-draw p90 on all read
windows, and survives costs at 0.35% RT (stress). No candidate passes →
**the project stops at Phase 1** and we write the kill memo. That
outcome is cheap (a few sessions) and would itself be worth knowing.

---

## 5. Operating loop and phases

### 5.1 The weekly loop (steady state, owner load ≤ 30 min + approvals)

1. **Sat/Sun — scan (bot):** fetch bars, rank universe, mark regime,
   produce the weekly digest: current book, candidates entering/exiting,
   proposed orders with sizes and limit prices, ledger + bar scorecard.
2. **Sun — review (owner):** read digest, veto anything. Silence ≠
   consent: unapproved proposals expire. *(Amendment A2, 2026-07-10,
   owner decision: during the PAPER phase proposals auto-fill at
   Monday's open — a veto reply before Monday cancels, otherwise the
   simulator proceeds, so the ledger measures the system rather than
   approval latency. Explicit per-order approval returns at P3/live,
   where this clause applies as written.)*
3. **Mon — execute:** *paper phase:* the simulator fills approved
   proposals at Monday's open (+ modeled costs) and journals them; the
   MCP order path formats the identical `create_order_instruction`
   payload and logs it WITHOUT sending (`LIVE_ORDERS=off`). *Live phase
   (P3+, deferred):* the same payload is actually placed (LIMIT,
   day-only, size-capped) and **owner confirms each in IBKR**.
4. **Daily (bot, zero owner load):** ledger row appended, stop/time-stop
   breaches flagged by alert (state-change-only, the #15 pattern).
5. **Quarter-end:** scorecard vs the bar; skim rule executes; one gated
   engine change allowed (R10).

### 5.2 Phases and gates (each gate pre-committed, kill criteria included)

| Phase | Content | Gate to advance | Kill/park criterion |
|---|---|---|---|
| **P0** (this) | PRD, owner sign-off on §8 decisions | owner approves | owner declines |
| **P1** | Port data layer + multiwindow harness; mechanical universe (D-65 pattern) with stamped construction date; run §4 candidates | §4's pre-registered gate | no candidate passes → kill memo, stop |
| **P2** | **Paper phase (the current destination, open-ended per D-G1):** notional US$20k, full weekly loop, daily stop/TP monitoring, journal + append-only hash-guarded ledger from row 1, **monthly report to owner**, MCP order module built dark (`LIVE_ORDERS=off`) | ≥26 weeks AND ≥20 closed trades AND expectancy > 0 AND green vs §1 bar AND owner funds the sleeve | see §5.3 kill conditions |
| **P3** | Live pilot US$15–20k (only after owner funds it), `LIVE_ORDERS` flipped by owner-signed enable file, MCP orders + manual approval, monthly scorecard | 2 consecutive quarters green vs §1 bar | 2 consecutive red quarters → back to paper; drawdown > 20% → hard stop, post-mortem |
| **P4** | Scale to US$40k → US$80k; skim rule live; optional D-G4 study | bar stays green at each step | same as P3, evaluated at every scale step |

**No stage skips. Scaling is earned by the ledger, not the backtest.**

> **P1 outcome (2026-07-11): the kill/park criterion fired.** No §4
> candidate passed the pre-registered gate (BACKTEST_RESULTS.md);
> S1-pure cleared 2/3 windows but is non-promotable by the §4 stop
> directive, and S1-stopped / S2 / S3 each cleared 0/3. The project is
> parked at Phase 1 (KILL_MEMO.md). P2 was never entered; P3 remains
> deferred sine die as in §3.4. Re-entry is a new-hypothesis action per
> KILL_MEMO §8, not a continuation.

### 5.3 Kill conditions (owner-requested, pre-registered — evaluated in every monthly report)

The monthly report shows each of these as 🟢/🟡/🔴; two 🔴 months on the
same condition triggers the stated consequence automatically. Overriding
a trigger requires the owner to write the reason into the journal.

| # | Condition (paper or live) | Trigger | Consequence |
|---|---|---|---|
| K1 | Expectancy | ≤ 0R over the trailing 20 closed trades (evaluated once ≥15 trades exist) | halt new entries; recycle to next §4 candidate or write the kill memo |
| K2 | Drawdown | sleeve equity −20% from its high-water mark | immediate full stop, post-mortem before any restart |
| K3 | The bar | behind same-dollar QQQ B&H by >10 pts over any trailing 26 weeks | halt new entries, Fable-session review; second occurrence → kill memo |
| K4 | Discipline | any fill without a pre-written stop+TP in the journal, or any retro-edited ledger row | that alone is a red flag on the system's integrity — fix the process before the next trade |
| K5 | Owner load | loop demands >30 min/week for 4 consecutive weeks | simplify or park — overload is the failure mode this project was designed against |
| K6 | Safety | `LIVE_ORDERS=on` without the owner-signed enable file (validate check) | CI fails; nothing runs until restored |

---

## 6. Risk register (GAMBIT-specific; homily R1–R12 patterns inherited)

| # | Risk | Mitigation |
|---|---|---|
| G1 | Data bugs → invalid backtests (the Yahoo monthly-bar class) | port fetch guards + validate [22] equivalent before ANY backtest is trusted; bars-contract test first module |
| G2 | Overfitting / best-of-N shopping at higher trade frequency | pre-registration in-file; luck benchmark; §4 gate fixed before first run (it is, as of this commit) |
| G3 | Construction-date bias in the universe | mechanical universe, stamped date, post-construction windows only |
| G4 | Cost/slippage underestimation (turnover ~8×/yr) | 0.25% RT modeled, 0.35% stress arm; P2 measures real proposed-vs-fillable gap before a dollar moves |
| G5 | Correlation with the homily book (one AI/semi cluster) → same drawdown twice | cluster caps; GAMBIT digest shows combined-account exposure; max 2 names overlapping homily holdings |
| G6 | Owner overload (the day-trading failure mode arriving by the back door) | weekly cadence hard-coded; alerts are state-change-only; if P2 shows >30 min/wk, that alone fails the gate |
| G7 | Margin creep (account already 1.23×) | GAMBIT unlevered, ever; sleeve cash ≥ 0 is a validate check |
| G8 | Income pressure distorts trading ("need $1k this month" → forced trades) | skim rule is mechanical and quarterly; reserve decouples monthly transfer from monthly P&L; red quarters pay $0 and that is correct behavior |
| G9 | Sleeve bleed (GAMBIT dips into BUY_BUDGET/SRS/ESPP or vice versa) | separate ledger, separate funding (D-G1), homily PRD §9.4 sleeves untouchable by GAMBIT code |
| G10 | Automation accident (order without approval) | MCP order instructions require manual owner confirmation; buy AND sell proposals expire unapproved; AUTOTRADE-style kill switch from day 1; no resting orders in MVP |
| G11 | Regime-scale overvaluation (the ZM/PTON lesson) | not solved — bounded by regime switch + time stops; stated honestly everywhere; do not claim otherwise |

---

## 7. Repo and infra decision

**Separate repo (this one). Not mixed into homily-bot.** Reasons:

1. homily-bot's contracts forbid what GAMBIT must do: its engine is
   frozen (EXECUTION §0), its §7/§9 posture is monthly-buys-only and
   *sells are never automated even as proposals on a schedule*. A swing
   system proposes sells weekly by design. Mixing repos means mixing
   safety contracts — the exact failure R5 warned about.
2. Different heartbeat (weekly loop vs daily digest), different risk
   register, different ledger, different bar. Separate CI, separate
   validate.
3. Cross-pollination happens by **copying** proven modules (data fetch,
   harness patterns, ledger+hash, golden/validate discipline) with their
   tests — not by shared imports that couple two live trading systems.

Planned skeleton (build order = P1): `gambit_data.py` (ported fetch +
bars-contract tests) → `gambit_universe.py` (mechanical, stamped) →
`gambit_backtest.py` (multiwindow harness + §4 arms) → then and only
then the P2 loop (`weekly_run.py`, `gambit_ledger.py`,
`gambit_validate.py`). DESIGNS/SPECS/EXECUTION docs follow the homily
handoff protocol: Fable writes specs, Opus builds one item per session.

---

## 8. Owner decisions — RESOLVED 2026-07-10 (P1 unblocked)

* **D-G1 — Funding. RESOLVED: no funds for now; paper-first.** Notional
  US$20k paper book; monthly results report mandatory; IBKR MCP
  integration built from day 1 but hard-gated OFF (`LIVE_ORDERS` flag +
  owner-signed enable file + validate check K6). Full spec §3.4 and
  DESIGNS D-G1.
* **D-G2 — Universe. RESOLVED: US-only**, mechanical liquidity-gated
  list (DESIGNS D-G2). Owner attached three product requirements, all
  adopted as hard rules: **explicit stop and take-profit on every
  position** (§4 exit stack, DESIGNS D-G3), **a trading journal** (the
  ledger grows journal columns: entry/exit reason codes, R-multiple,
  MFE/MAE — DESIGNS D-G6), and **explicit kill conditions** (§5.3).
* **D-G3 — Stop handling. RESOLVED by implication of paper-first:** the
  paper simulator monitors stops/TP daily (bot-only, no owner load) and
  logs the paper fill honestly (next-day-open modeling, gaps included —
  no "I would have gotten out at the stop" fiction). The resting-GTC
  question returns as a P3 design item when live money exists.
* **D-G4 — Options sleeve. RESOLVED: parked, owner interested but has
  zero options knowledge.** Consequence: stays out of scope for P1–P2;
  Fable owes the owner a plain-language options primer
  (`docs/OPTIONS_101.md`, covered calls / cash-secured puts only, no
  code) at some point during the paper phase, so a P4-era decision can
  be an informed one. No strategy work until then.
* **D-G5 — Name. RESOLVED: GAMBIT stays.**

---

## 9. Docs map (contract, homily §9.3 style)

* `PRD.md` (this) — mission, bar, evidence, phases, risks. The constitution.
* `DESIGNS.md` (next Fable session) — D-G* deep designs after owner answers §8.
* `EXECUTION.md` — session queue + engine freeze + risk register for the executing model. Written before the first build session.
* `BACKTEST_RESULTS.md` — the only place the P1 bar is scored. Created by P1, rewritten never, appended quarterly.
* `PAPER_RESULTS.md` — the monthly report archive (P2): one section per month, appended by the first weekly run of each month, mirrored to the owner via the digest channel.
* Ledger CSV (= the trading journal) + snapshot JSON — the track record, append-only, hash-guarded from row 1; journal columns per DESIGNS D-G6.
* `docs/OPTIONS_101.md` — owed to the owner during P2 (D-G4): plain-language primer, no code.
