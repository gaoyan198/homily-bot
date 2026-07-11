# EXECUTION — start here (entry point for the executing model)

**Read order:** this file → PRD §8 → DESIGNS.md → SPECS.md (if it exists;
writing it is session 0 below). One item per session. The algorithm works
today; the point of this file is that it still works after every session.

## 0. Engine freeze (the prime directive)

These files ARE the algorithm and are **frozen** during phases A, B, D, E, F:

    homily_chips.py  homily_clone.py  homily_danny.py  homily_vol.py
    homily_whale.py  homily_conviction.py  homily_regime.py  homily_fund.py

Phases A/B/D/E/F only *read their outputs*. Never refactor, "clean up",
re-tune, or change a default constant in a frozen file while building a
digest/ledger/frontend feature — no matter how small the improvement looks.
Only Phase C items may touch engine behaviour, one item at a time, each
behind its own backtest gate, in its own session. `homily_data.py` is
semi-frozen: the bars contract (see R1) may never change; fetch plumbing
around it may (#17).

## 1. Session queue (do them in this order)

| Session | Task | Notes |
|---|---|---|
| 0 | ~~Write `SPECS.md`~~ (done 2026-07-11, late — specs now cover the REMAINING backlog; #22 was already reconciled in place; the PRD §8.5 entry is DEFERRED — a concurrent planning session was actively editing PRD.md at write time, adding #68–75; add the §8.5 session-0 note and reconcile SPECS §1 with those items once that session commits) | **queue continues in SPECS.md §1** — 2026-07-11 batch all done: #64 [29] · #30 [30] · #69+#80 [31] · #70 [32] · #36+#75 [33]; also ~~#26+#28+#29~~ [34]-[36] · ~~#33~~ [37] · ~~#32~~ [38]. **Non-gated queue EMPTY as of 2026-07-11.** Remaining items are gated by design: #14+#71 (~3 ledger months, first read ~2026-10) · #24 promotion decision (2026-10-01, run `python3 homily_promotions.py`) · Phase-C studies #20 #21 #65 #66 #67 #39 + research #77-82 (one per session, own backtest gates, R10 budget) · #25 (needs a gated conviction-input change) · #76 doc pruning (docs-only, any time) · T3 (owner: two clean T2 months + cloud repo access). Owner to-dos: set IBKR_FLEX_TOKEN/QUERY secrets to light up #32; MARGIN_ZERO var when the loan clears; BUY_BUDGET_USD back to 1550 after the margin paydown |
| 1 | #49 golden-file digest tests | the safety net — before ANY digest-touching change |
| 2 | #16 validate-gates-the-send | see R5 before touching the workflow |
| 3 | #13 signals ledger + snapshot.json | see R3, R7 — the track record starts here |
| 4 | #15 state-change alerts | ledger diff only |
| 5 | #34 digest typography (HTML mode) | see R4; golden files updated deliberately |
| 6 | #17 fetch hardening | see R11 |
| 7 | #18 adjclose returns | see R1 — the highest-risk item in the plan |
| 8 | ~~#19 corp-action guard~~ (done 2026-07-10, `homily_corp.py`, gate [24]) · ~~#31 buy-day copilot + T2 basket CSV~~ (done 2026-07-10, `homily_buyday.py`, gate [27]; R12 followed — HK prints "manual:", D-31's board-lot sketch superseded) · ~~#35 chart cards~~ (done 2026-07-11, `homily_png.py`, gate [28] pixel-hash) · then Phase C per §8.1; SPECS.md (session 0) still TODO | |

Definition of done, every session: spec's acceptance criteria met ·
`python homily_validate.py` green · golden files pass (or were changed
*deliberately*, stated in the commit message) · diff touches ONLY files the
spec lists · README honesty line if the digest changed · gate status in the
commit message.

## 2. Risk register — how execution could corrupt the algorithm

**R1 · The bars contract.** Everything assumes bars are 6-tuples
`(date,o,h,l,c,v)` with raw (split-adjusted, non-dividend) prices — chips,
whale, vol, backtests. #18 must NOT swap `close` for adjclose inside
`fetch_daily()`: chip shelves, POC, zones would silently shift. Ship
adjclose as a *parallel* series (e.g. `fetch_daily_adj()` or a separate
accessor); return math migrates to it; levels keep raw. Golden files catch
a violation — which is why #49 precedes #18.

**R2 · Champion-state continuity (#21).** Never rewrite
`homily_refine_log.csv` history or reinterpret old rows. The new objective
logs to NEW columns/fields during the 30-day parallel run;
`homily_champion.json` gains an explicit `"objective"` field so a reader
can tell which regime a champion was selected under.

**R3 · Ledger honesty (#13).** The ledger records what the digest PRINTED
that day. **Never backfill history** — backfilled rows would run today's
code on yesterday's dates and manufacture a fake live track record, the
exact thing the ledger exists to prevent. Same-day idempotent overwrite
only; past rows are immutable.

**R4 · Silent send failure (#34).** HTML parse mode adds an escaping bug
class ( & < > in names/notes). Keep the existing plain-text fallback path
in `send()`; add the escaping test; the digest must degrade, never vanish.

**R5 · Workflow reorder trap (#16).** `daily_refine()` runs inside
`build_digest()` and MUTATES state (champion json + log append). Reorder
so validate runs first, and on failure suppress BOTH the send and the
state commit — half-committed state after a red test run is drift.
Cleanest: validate step → digest step → commit step, each gated on the
previous.

**R6 · Backtests must call live functions.** Every new backtest (#20, #22
extensions, #24) replays by calling `danny_signal()` / `conviction()` on
truncated bars — never a reimplementation "for speed". A reimplementation
validates a different algorithm; divergence is invisible until it costs
money.

**R7 · Date/timezone drift.** `fetch_daily()` builds dates via
`datetime.date.fromtimestamp()` — that's the RUNNER's timezone: UTC in
Actions, SGT locally. The same bar can be dated differently local vs CI,
which breaks ledger idempotency keys and buy-day detection. #13 must pin
this (use a fixed TZ conversion or the exchange date) BEFORE rows accrue.

**R8 · State-file commits.** New committed artifacts (ledger, snapshot,
dashboard) must be added to the workflow's `git add` list in the same PR
that creates them, or CI silently discards data daily. Local runs already
duplicate log rows (see homily_refine_log.csv, 12× on 2026-07-06) —
idempotency keys, not append-blind writes.

**R9 · Scope creep.** The diff of each session touches only the files its
spec lists. An "obvious little fix" in a frozen engine file = stop, note it
in PRD §8.5, finish the session's item. Improvements to the algorithm go
through Phase C gates, never ride along.

**R10 · Degrees-of-freedom budget.** Max ONE promoted signal-behaviour
change per quarter (PRD §8.0). If two gates pass in the same quarter, the
second waits. An algorithm that changes weekly has no track record.

**R11 · Rate-limit bans (#17).** Threaded fetch: cap concurrency ~4, add
jitter, keep the sequential path as fallback. A 429-banned runner IP kills
every digest until the ban lifts — worse than slow.

**R12 · Currency/lots (#31).** 9992.HK is HKD-quoted with board-lot
trading. Copilot v1 EXCLUDES non-USD names from order lines (prints
"manual: 9992.HK" instead) rather than mixing currencies in budget math.
USD-only until an FX line ships (#53).

## 3. Mechanical guards (new backlog items — build in session 1–2)

61. ~~**Engine-freeze CI guard**~~ (S) — **done 2026-07-11** (validate
    [39]): `homily_validate.py` asserts the SHA-256 of each frozen engine
    file against `engine_freeze.json`; an engine change fails CI unless
    the manifest is updated in the same commit — every engine edit is
    loud, deliberate, and reviewable. Update the manifest ONLY in Phase-C
    sessions whose backtest gate passed.
62. **Ledger append-only guard** (S; with #13) — validate recomputes a
    running hash of all ledger rows older than today and compares to a
    committed checkpoint; any retro-edit of history fails CI. Enforces R3
    mechanically. **Gate:** none (guard infra).

## 4. Trade-automation track (PRD §9 — owner-approved scope change)

North star (PRD §9.0): live excess vs SPY/QQQ DCA, and an unexecuted
signal has zero alpha — so routine BUYS get automated in stages T0→T3
(§9.2), sells never. Queue impact: T2 (basket CSV `docs/orders_YYYY-MM.csv`)
ships inside the #31 session; T3 (MCP order routine, report-only first
month, `AUTOTRADE` kill switch + caps per §9.2) is its OWN session, only
after two clean T2 months, and only after the owner fixes cloud repo
access. Session 0 also adds the §9.3 docs-map to README. Owner's two
manual to-dos, no code: (1) confirm SRS cash is actually deployed into
index, not idle — SRS is the index leg, no IBKR recurring investment
needed (PRD §9.4); (2) grant the cloud environment GitHub access to this
repo (unblocks routines + T3). Funding accounting per §9.4: BUY_BUDGET =
pure cash (SRS and ESPP excluded); ESPP shares live in holdings v2 as
source:"espp" — counted for caps/clusters, never added to.

*Written 2026-07-07 by the planning model. If reality contradicts this
file, record it in PRD §8.5 and stop — don't improvise around it.*
