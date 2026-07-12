# GAMBIT AMENDMENT A5 — swing sleeve LIVE-armed by owner override (#93, 2026-07-12)

**Two-artifact governance record** (the A4 / LIVE_ENABLE / LEVERAGE.md
pattern): this file plus the dated owner line below authorize going live
ahead of the P2 paper gate that D-93 pre-registered. It is the largest
override in this repo's history and is recorded as such.

## What changes

* **The LIVE overlay starts** (`gambit_live.py` + `live_run.py`, weekly CI
  after the paper step): real owner money, mirroring the paper book's
  S1 decisions (same names, same Fridays, same Monday-open fills), sized
  under the LEVERAGE.md ladder (BULL 1.30× / MIXED 1.15× / BEAR flat &
  margin-zero), with **mandatory stops (−20%), TPs (+40% half, once) and a
  12-week time stop** on every position.
* **Bankroll: US$3,000 contributed** (≈9% of net liq; top-ups recorded,
  total ≤10% of net liq). Proceeds sweep to BUY_BUDGET (listed monthly);
  losses are the recorded cost of business.
* **Kill rules, pre-registered:** KILL-A equity ≤ **70% of contributed**
  (US$900 loss on the initial funding) → liquidate, experiment DEAD,
  failure memo owed. KILL-B expectancy ≤ 0 over the trailing 20 closed
  trades → same. No restart without a new gated design + signed amendment.
* **Arming condition:** the first order sheet prints only after the owner
  clears the legacy margin loan and sets `MARGIN_ZERO` (the clean-slate
  directive, owner's own words: "i wil try to clear my leverage now and
  start from a clean slate asap").
* **Execution stays human.** `LIVE_ORDERS` remains `off`; the G-S7 MCP
  order rail is NOT built. The bot prints a Monday order sheet; the owner
  places every order at IBKR (bot proposes, owner disposes — homily §9.2
  posture). The two-artifact LIVE_ENABLE gate governed *automated* orders
  and is therefore untouched; this amendment is the analogous record for
  the *manual* live book.

## What the owner accepts, in writing (the cost of this lever)

* **The P2 paper gate (≥26 weeks · ≥20 closed trades · expectancy > 0 ·
  green vs QQQ) is OVERRIDDEN, not passed** — the live book starts on two
  days of paper history. The paper gate keeps running and publishing; it
  just no longer blocks the money it was designed to protect.
* **The stops this book must carry FAILED the Phase-1 backtest**
  (KILL_MEMO: S1-stopped 0/3 windows — smoothness bought by cutting
  winners). They are mandated as a bounded-loss control, not an edge. The
  paper S1-pure book continues UNCHANGED as the no-stops counterfactual,
  so the cost of the stops is measured, monthly, in public.
* **Leverage amplifies whatever this arm turns out to be.** LEVERAGE_MEMO
  §2's arithmetic is not repealed; the ladder referee (regime-gated 1.30×
  QQQ, BACKTEST_RESULTS §15) is the bar this experiment must beat to be
  called anything but expensive tuition.
* **Modeled fills.** The journal assumes Monday opens and trigger prices;
  real fills drift. The monthly report carries the disclaimer; the owner
  reconciles against IBKR statements.

## Reporting (all mechanical, all committed)

Weekly: order sheet + Friday mark (equity, kill-line distance, gross vs
ladder cap) in the ♟️ digest. Daily: SWING LIVE status line in the homily
digest (validate [51]). Monthly (first run of the month): realized P&L per
closed trade with reason codes, cumulative, sweepable-to-DCA amount.
Journal: `gambit_live_journal.csv`, hash-chained from row 1 (K4 verified
before every append). Registry note: like LEVERAGE.md, this lives outside
promotions.json (the rank schema doesn't fit); THIS FILE is the registry
entry, and the kill rules above are its demotion rule.

---

**Owner line (dated signature, per the two-artifact rule):**

> 2026-07-12 — Owner directive, recorded verbatim by the executing
> session: *"Promote #93 as well … Clear tp and stop losses is a must …
> if there are any proceeds from this experiment they will all go towards
> funding the monthly dca. if there are losses, it's cost of doing
> business. If the losses are too huge … we should stop this experiment
> immediately and declare it a failure."* The −30%-of-contributed kill
> number and the US$3,000 bankroll were set by the executing session per
> the directive's "determine a number or percentage" instruction. I
> accept going live ahead of the P2 gate, the stops' measured backtest
> cost, and the kill rules as written. — owner (gaoyan), via directive;
> amend this line directly if the wording should differ.
