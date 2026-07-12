# GAMBIT AMENDMENT A4 — S1-pure promoted to paper (owner reopen, 2026-07-11)

**Two-artifact governance record** (same pattern as LIVE_ENABLE.md): this
file plus the dated owner line below authorize a change that pre-registration
law (EXECUTION §0.3) otherwise forbids. It reopens Phase 1 through the lever
KILL_MEMO §4 / LEVERAGE_MEMO §2.4 named explicitly — reconsidering the §4
stop directive, not re-shopping a dead arm.

## What changes

* **PRD §4 stop directive is RESCINDED for S1-pure only.** The clause "only
  the stopped version is promotable (the directive binds even if the pure arm
  backtests better)" no longer blocks S1-pure. S1-stopped / S2 / S3 remain
  FAILed by the gate and unchanged.
* **S1-pure is promoted to P2 paper.** It mechanically cleared the
  pre-registered Phase-1 gate on 2 of 3 qualifying windows (2020→2025,
  2021→2026: MOIC+0.10 ✓, MAR ✓, > random p90 ✓, 0.35% stress ✓ — see
  BACKTEST_RESULTS.md §Gate). Its only blocker was the §4 directive, now
  lifted. This is the **one** promotion consistent with the gate as scored.

## What the owner accepts, in writing (the cost of this lever)

* **S1-pure carries NO stops, NO take-profit, NO time stop.** Its only exits
  are 4-weekly rank rotation and the 🐻 regime kill-switch. The owner accepts
  the **−40% to −46% drawdowns** this arm required across the backtest windows
  (BACKTEST_RESULTS: MaxDD −40.2%/−45.5%/−45.6% on recent windows). KILL_MEMO
  §4 and LEVERAGE_MEMO §2.4 both flagged accepting these drawdowns as "not
  recommended"; the owner overrides that counsel deliberately and on the
  record.

## What does NOT change (the guardrails hold)

* **Paper only.** `LIVE_ORDERS` stays `off`; P3/live remains deferred sine die
  (PRD §3.4). This promotion advances to P2 paper, nothing further.
* **No margin, ever (G7).** The paper simulator refuses any entry that takes
  cash below zero — unchanged, and S1-pure is unlevered.
* **P2's own gate (PRD §5.2) inherits NO credit from the backtest.** The paper
  ledger is the real test: ≥26 weeks AND ≥20 closed trades AND expectancy > 0
  AND green vs the §1 QQQ bar before P2 advances. The kill conditions K1–K6
  (PRD §5.3) watch S1-pure from journal row 1.
* **The random-referee standard is not waived.** S1-pure sat *below* random
  p90 on one qualifying window (2019→2024) and only cleared 2/3 — it is a
  marginal promotion, and the paper phase exists precisely to see whether the
  backtest's survivorship-flattered edge survives out of sample. It may not.

## Consequence for the queue

EXECUTION G-S5 (paper loop + journal) is unblocked and built this session
against S1-pure. G-S6 (schedule/report) and G-S7 (dark orders) follow as
their own sessions. KILL_MEMO stands as the record of *why* the other three
arms died; this amendment records the single narrow reopening.

---

**Owner line (dated signature, per the two-artifact rule):**

> 2026-07-11 — I authorize promoting S1-pure to the paper phase, accepting its
> stop-free −40…−46% drawdown profile in full and against the memos' "not
> recommended" counsel. Paper only; no leverage; P2 gate applies with no
> backtest credit. — owner (gaoyan)
