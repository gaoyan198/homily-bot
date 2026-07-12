# GAMBIT KILL_MEMO — Phase 1 stops; no candidate promotable (2026-07-11)

> **Superseded in part, same day, by Amendment A4.** After this memo, the
> owner took the reopen lever §4 / LEVERAGE_MEMO §2.4 named — reconsidering
> the stop directive — and promoted **S1-pure** (which cleared the gate on
> 2/3 windows) to paper, accepting its −40…−46% drawdowns in writing
> (AMENDMENT_A4.md). This memo stands unchanged as the record of *why*
> S1-stopped / S2 / S3 died; only the S1-pure directive-block was lifted.
> The reopening was via the directive lever, against this memo's "not
> recommended" counsel — deliberately and on the record.

**Status: the pre-committed Phase-1 outcome has fired.** PRD §5.2 (P1
kill criterion: *"no candidate passes → kill memo, stop"*) and §4.1
(*"No candidate passes → the project stops at Phase 1 and we write the
kill memo"*) both name this document as the required deliverable. It is
now written. The project halts at Phase 1. The paper loop is **not**
built: EXECUTION queue items G-S5, G-S6, G-S7 are each gated on
"only if G-S4 passed a candidate," and G-S4 passed none. G7 (unlevered,
ever) and the `LIVE_ORDERS=off` prime directive stand. This memo
discharges the debt LEVERAGE_MEMO §6 flagged as "still owed."

**This is not a failure of the build. It is the build working.** PRD
§4.1 pre-committed that a clean kill is "cheap (a few sessions) and
would itself be worth knowing." Phase 1 cost four build sessions
(G-S1…G-S4) and bought a real answer: the registered arms do not beat
their own universe drawn at random. Knowing that before a dollar — or a
paper dollar — moved is the entire point of the pre-registration
discipline.

---

## 1. Verdict up front

**No candidate cleared the pre-registered Phase-1 gate. The margins are
not close, and they run the wrong way against the one referee that
cannot be gamed.**

| candidate | qualifying windows cleared | disposition |
|---|---|---|
| S1-pure (rotation, no stops) | 2 of 3 | **NOT PROMOTABLE** — owner stop directive (PRD §4), not the gate |
| S1-stopped (the only promotable S1) | 0 of 3 | **FAIL** |
| S2 leader-pullback | 0 of 3 | **FAIL** |
| S3 vol-hole breakout | 0 of 3 | **FAIL** |

The gate (DESIGNS Part II, restated): a candidate is promotable iff on
≥2 of the 3 most-recent 5y windows (2019→2024, 2020→2025, 2021→2026) it
(a) beats QQQ B&H MOIC by ≥ +0.10, (b) beats QQQ on MAR, (c) sits above
the 200-draw random-5 p90, and (d) still clears (a)–(c) at 0.35% RT
stress. Full cell-by-cell scoring: BACKTEST_RESULTS.md §Gate.

## 2. What was on trial (pre-registered, never edited mid-run)

Registered in DESIGNS Part II *before any harness code existed*, amended
once (A1, before G-S3 began) and with implementation choices logged (A3)
before G-S4 ran — no arm, window, cost, or threshold moved after a
number was seen. Arms: S1-pure · S1-stopped · S2 · S3 vol-hole · QQQ B&H
· SPY B&H · equal-weight-universe monthly · **200 seeded random-5 draws
(the referee)**. Windows: rolling 5y from 2015 plus two 10y. Costs
0.25% RT base, 0.35% RT stress. Fills T+1 open, gaps taken in full.
Universe: mechanical, 120 names, `constructed: 2026-07-10`, point-in-time
eligibility at each window open.

## 3. The one finding that decides it: the referee won every qualifying window

The random benchmark exists for exactly this moment. Homily #24 used it
to kill a 6-component conviction score that looked good until it was made
to beat luck. The same filter now kills the entire Phase-1 arm set:

**On all three qualifying windows, every promotable strategy arm sits
below the random-5 p90 — usually below p50.** A rule that cannot beat
five names drawn at random from its own universe is selecting noise, by
this repo's own pre-registered definition (PRD §4).

| window | QQQ MOIC | random p90 | best *promotable* arm (MOIC) |
|---|---:|---:|---|
| 2019→2024 | 2.80 | 3.25 | S1-stopped 1.50 |
| 2020→2025 | 2.46 | 3.69 | S1-stopped 1.60 |
| 2021→2026 | 2.01 | 4.15 | S1-stopped 1.17 |

The gap to the referee is measured in whole MOIC points (1.7–3.0), not
rounding. No cost assumption, window choice, or exit-tuning inside the
registered protocol closes it.

## 4. Arm by arm (honest reading)

* **S1-stopped — the designated promotable arm — FAIL (0/3).** It did
  the one thing it was built to do: cut drawdown. Its MAR beat QQQ in
  2019→2024 (0.71 vs 0.65) and 2020→2025 (0.82 vs 0.56) on MaxDD near
  −12% against QQQ's −35%. But it never cleared (a) or (c) in any
  qualifying window: MOIC 1.50 / 1.60 / 1.17 against a QQQ+0.10 bar of
  2.90 / 2.56 / 2.11 and a p90 of 3.25 / 3.69 / 4.15. **A low-drawdown
  arm that compounds to ~1.2–1.6× while the index does ~2–2.8× is a
  worse cash-equivalent, not an edge.** Tighter stops bought smoothness
  by cutting winners as readily as losers (win rate ~48–51%, but the
  rank-rotation churn — 200+ fills/window — capped the upside).

* **S1-pure — cleared 2/3 but NOT PROMOTABLE by owner directive.** Its
  headline MOIC (4.75, 5.49 on the two recent windows) comes entirely
  from never selling into −45% drawdowns and riding the survivors. PRD
  §4 pre-registered that only the stopped variant is promotable, *"even
  if the pure arm backtests better"* — because the −40…−46% drawdown
  paths it requires are the exact D-63 evidence the stop directive
  descends from. Leverage does not rescue it either (LEVERAGE_MEMO §2.4).
  The honest reopen lever here is the *directive itself* (accepting
  stop-free −45% drawdowns in writing), not the gate — and that is not
  recommended.

* **S2 leader-pullback — FAIL (0/3).** Flat. MOIC ~0.98–1.02 on the
  qualifying windows — it barely returned capital while the index
  doubled. The pullback-reclaim trigger fired rarely (~50 fills/window)
  and carried no aggregate edge (ΣR positive but tiny; expectancy did not
  survive costs into a portfolio result above the index).

* **S3 vol-hole breakout — FAIL (0/3).** The Amendment-A1 hypothesis —
  homily §5b's contraction→resolution event-study edge (+11.5% vs +8.5%
  baseline fwd 60d) — **did not replicate on the mechanical universe in
  portfolio context.** MOIC 1.02 / 1.11 / 1.09 on the qualifying windows;
  negative CAGR on several earlier windows. A directional event-study
  signal did not survive the random-draw band once turned into a sized,
  cost-bearing arm — which is precisely the test PRD §4.1 requires of any
  signal ("directional support isn't enough; it must survive the
  random-draw band in portfolio context too"). The pre-registered
  breakdown-side re-test logged its VOLHOLE_BREAKDOWN events journal-only
  (351–801 per window) and produced no signal-flip; homily's verdict
  stands — breakdowns remain a journal-only warning, never a trade.

## 5. Why the kill is the honest call, not a data artifact

**Every number scored was a survivorship-flattered upper bound**
(BACKTEST_RESULTS.md preamble; DESIGNS Part II): the 2026 universe cannot
see pre-2026 delistings, so surviving names are over-represented. Crucially
the random band is drawn from the *same* flattered universe, so the
strategy-vs-referee comparison is apples-to-apples — and the strategy arms
lost it. The flattery inflates the arms too; the real, out-of-sample result
can only be **worse**, never better. An arm that cannot clear the bar on
the friendly version of the data will not clear it on the honest one. There
is no window, cost, or tuning left to try inside the registered protocol.

## 6. The leverage question — already answered, same verdict

The owner's 2026-07-11 question ("would 10–20% leverage flip the
verdict?") was answered in LEVERAGE_MEMO.md without a re-run. Gate
condition (c) is invariant under like-for-like leverage (x→x^L is
monotone, applied to candidate and random band alike), so no leverage
level reorders the p90 column that every arm already failed; the
frictionless ×1.2 MOIC bound also misses condition (a) by 0.8–1.9 MOIC
per cell. **Leverage amplifies the sign of an edge; it cannot create the
sign.** This kill memo and that leverage memo agree: G7 stands.

## 7. What this does NOT kill — the asset that keeps

The hypothesis set died; the machine that killed it did not.

* **The methodology is the product** (PRD §0.2): pre-registered decision
  rules, construction-honest windows, the 200-draw luck band,
  append-only hash-guarded discipline, validate-gates-the-send CI. That
  apparatus just did its job in four sessions and cost almost nothing. It
  is reusable verbatim for the next hypothesis.
* **`gambit_data.py` / `gambit_universe.py` / `gambit_backtest.py` and
  their 53 green tests keep.** A future arm plugs into the same harness;
  the benchmark referee and cost model are already built and pinned.
* **The mechanical universe (`universe.json`, stamped) keeps** — its
  construction date only becomes *more* valid as out-of-sample time
  accrues past it.

## 8. Reopen conditions (pre-registered, so this is a gate, not a door slammed)

Phase 1 may be re-opened iff **all** hold — the same standard that
killed it:

* **R1 — a NEW setup hypothesis**, registered as a DESIGNS Part-II
  amendment *before* any run. Re-shopping the four dead arms, re-tuning
  their exits, or trying new windows on them is best-of-N shopping (G2)
  and is forbidden. New arms, not new knobs on old ones.
* **R2 — an event study first** (homily 5b pattern: baseline vs signal
  forward returns, no look-ahead), passing before the arm is admitted to
  the harness — and directional support alone is explicitly insufficient
  (PRD §4.1). S3 is the cautionary case: it had the event study and still
  died in portfolio context.
* **R3 — the same unchanged gate**: ≥2/3 qualifying windows on
  MOIC+0.10 AND MAR AND random-p90 AND 0.35% stress. The referee does not
  get easier because the first hypothesis lost.
* **R4 — owner registers the amendment in writing** before the run
  (the pre-registration-is-law directive; homily two-artifact pattern).

Leverage's own reopen conditions (L1–L4) are a strict subset of these
and remain in LEVERAGE_MEMO §4: leverage may only ever scale an arm that
has *already* passed R1–R3 unlevered.

## 9. State after this memo

* **Phase 1: STOPPED.** Verdict recorded in BACKTEST_RESULTS.md, scored
  mechanically, zero editorializing. This memo is its close-out.
* **No paper loop.** G-S5/G-S6/G-S7 do not trigger (no candidate passed).
  No `weekly_run.py`, no journal, no schedule, no Telegram bot needed —
  those were all downstream of a promotion that did not happen.
* **Engine freeze not armed.** It triggers on the first journal row
  (EXECUTION §0.6); no row ever accrued, so there is nothing to freeze.
  The harness stays editable for the next hypothesis.
* **`LIVE_ORDERS=off` permanently** until a reopen under §8 earns a paper
  ledger and P2 clears its own gate. Nothing about this outcome moves
  that flag.
* **The May→July levered side experiment** has its sanctioned, ring-fenced
  home in LEVERAGE_MEMO §5 (the SIDECAR, US$2k house money, scored
  against QQQ at 12 months) — it is not GAMBIT and never enters these
  books.

## 10. One line for the owner

We built the honest machine, ran the four registered bets through it, and
it told us the truth: none of them beat picking five names from the same
list at random. That answer cost four sessions and is worth having. The
machine, the universe, and the discipline all keep — pointed at the next
real hypothesis, whenever there is one. Nothing goes live; nothing is
levered; the door is a gate, not a wall.
