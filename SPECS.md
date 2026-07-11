# SPECS — build specs for the remaining backlog

The "how" file per PRD §9.3 (PRD = what/why · DESIGNS = deep design
decisions · EXECUTION = session order, freeze rule, risk register · this
file = per-item build specs). Written 2026-07-11 — later than planned
(session 0 was queued first but the Week-1/Month-1 items shipped without
it); it therefore specs only what REMAINS. One item per session, engines
frozen (EXECUTION §0), every gate restated before coding.

## 0 · Status ledger (what already shipped, with its gate)

| Item | Shipped | Gate |
|---|---|---|
| #49 golden digest tests | 2026-07-07 | validate [16] |
| #16 validate-gates-the-send | 2026-07-07 | workflow halt simulation |
| #13 ledger + snapshot.json | 2026-07-08 | validate [17][18], guard #62 |
| #15 state-change alerts | 2026-07-08 | validate [19] |
| #34 F0 HTML digest | 2026-07-08 | validate [20], goldens re-pinned |
| #17 fetch hardening | 2026-07-08 | validate [21] |
| #18 adjclose returns (parallel series, R1 kept) | 2026-07-10 | validate [23] |
| #19 corp-action guard | 2026-07-10 | validate [24] + golden `corp` |
| #12/#22 whale gate → WHALE-DIP tier | 2026-07-06 | homily_whale_backtest PASSED |
| #63 bear decomposition → §4 kept as priced insurance | 2026-07-10 | D-63 pre-committed rule, branch 3 |
| #24 rs12-top3 experiment (NOT promoted; see §2·24) | 2026-07-10 | selection backtest PASSED; promotion gated |
| #27 position-aware book math | 2026-07-10 | validate [26] |
| #31 buy-day copilot + T2 basket CSV | 2026-07-10 | validate [27] |
| #35 chart cards (stdlib PNG) | 2026-07-11 | validate [28] pixel-hash |
| #64 provenance column | 2026-07-11 | validate [29] |
| #30 bear-readiness line | 2026-07-11 | validate [30] |
| #69 promotion registry + #80 whale_rank column | 2026-07-11 | validate [31] |
| #70 missed-run detector | 2026-07-11 | validate [32] |
| #61 engine-freeze manifest guard | 2026-07-11 | validate [39] (negative case proven) |

## 1 · Remaining queue (recommended order)

1. ~~#64 provenance~~ · ~~#30 bear-readiness~~ · ~~#69 registry + #80
   whale_rank~~ · ~~#70 missed-run detector~~ — all shipped 2026-07-11
   (gates [29]–[32]); the time-sensitive ledger columns are accruing.
3. **#36 nightly dashboard** — the Quarter centrepiece (owner-confirmed);
   ride **#75 snapshot schema contract** (S, blocks T3) in the same
   session if scope allows.
4. **#25 real market cap** · **#26 breadth canary** · **#28 trim-rule
   flags** · **#29 concentration lens** — S/M digest features, any order.
5. **#32 Flex auto-sync** · **#33 Sunday deep-dive** — after #36.
6. **#14 live scorecard** — first read ~2026-10 (needs ~3 ledger months).
   Its **#14a flip-scorecard rider** (1/5/20-day flip returns vs QQQ) can
   read ~2026-08 and may ship earlier with any digest session.
7. **#24 promotion decision** — 2026-10-01 at the earliest, per §2·24.
8. **Phase C / studies, one per session, each behind its own gate:**
   #20 conviction backtest · #21 refine re-point · #65 mechanical
   universe · #66 right-stock discipline · #67 hard-rule audit · #39
   bootstrap CIs. R10: max ONE promoted behaviour change per quarter —
   whale holds Q3; #24 (if its forward-check passes) is the natural Q4
   slot; anything else that passes WAITS.
9. **T3 order routine** — own session; only after two clean T2 months AND
   cloud repo access works. Guardrails verbatim from PRD §9.2.

Guards #61 (engine-freeze SHA manifest) and #62 (ledger hash) — #62
shipped with #13; #61 shipped 2026-07-11 (`engine_freeze.json`, validate
[39]). Both guards are now live.

**#76 planning-doc pruning** (S, docs-only, spec in §2) — slot into any
session; the sooner it ships the less context every later session burns.

## 2 · Build specs

### #64 · Universe-entry provenance (S)
**Goal:** every ledger row carries how its name got into the universe, so
#14 can split the scorecard by `screen` vs `owner-request` (PRD #64: the
referee must not inherit the selection bias it exists to detect).
**Files:** `daily_run.py` (an `ORIGIN` map next to `UNIVERSE`/`WATCH`/
`HOLDINGS`), `homily_ledger.py` (column appended at END per the
append-only-columns rule), `homily_validate.py`.
**Build:** `origin` values: `owner-request` for the whole pre-#65
hand-picked list (honest: the curated list IS discretionary, PRD §5c/§5f),
`holding` for book names, `screen` reserved for #65 arrivals. state_of()
gains the field; csv_row/snapshot emit it.
**Gate:** validate fixture — row for a UNIVERSE name carries its origin;
unknown names get `owner-request` (the conservative default). No behaviour
change anywhere.
**Risks:** R3 — never backfill origins onto past rows; the column starts
blank for history and that blankness is honest.

### #30 · Bear-readiness line (S; needs #27 — met)
**Goal:** first-Monday digest line: satellites% vs core%, margin-zero
confirmation, and the pre-computed PLAYBOOK-§4-order sell list ("if 🐻
fired tomorrow you would sell: …"), so §4 stays rehearsed.
**Files:** `daily_run.py` (or a small `homily_bearready.py`),
`homily_validate.py`.
**Build:** pure function over positions + today's states: Bucket C value /
book, the §4.3 ordering (⚪ F:0–1 first, then ⚪ until satellites ≤10%),
margin line reads a `MARGIN_ZERO` env the owner sets (no broker API here;
#32 automates later). First-Monday = same ledger-based detection idiom as
buy day (first run of an ISO week whose weekday ≤ today's, or simply the
buy-day helper with week granularity — keep it one function).
**Gate:** fixture test — a book with known ⚪/F-tags produces exactly the
§4-ordered list. Info-only.
**Risks:** wording must match PLAYBOOK §4 verbatim (R9 — no improvised
variants of the sell order).

### #36 · Nightly dashboard (L; needs #13 — met; design D-36)
**Goal:** `docs/dashboard.html`, one self-contained file, zero JS, static
inline SVG: per-holding cards (price + levels + chip histogram),
ledger state-history heatmap, alerts timeline (every #15 alert ever,
reconstructed from ledger diffs — owner request 2026-07-10), refine-log
chart; later #14 tables. Committed by the workflow + sent via
`sendDocument`.
**Files:** new `homily_dashboard.py`, `daily_run.py` (call + send),
workflow git-add (R8), `homily_validate.py`.
**Build:** template string over `docs/snapshot.json` + the ledger CSV; SVG
primitives can reuse the geometry math of `homily_png.py` (share, don't
duplicate: extract the y-scale/bin helpers if needed — homily_png is NOT
frozen). `<details>` per holding; native `<title>` tooltips.
**Gate:** validate — self-containment (no `http`/`//` external refs in the
output), deterministic render on fixture snapshot/ledger, sendDocument
path behind the same env guard as send().
**Risks:** R8 (git-add in same PR); file size — keep SVGs plain (no
base64 PNGs) so the HTML stays reviewable.

### #25 · Real market cap (S)
Committed `market_caps.json` (~68 names, monthly manual refresh) replaces
the $-volume proxy in G1; validate spot-checks 3 known caps ±30% and warns
when the file is >45 days stale. **Gate:** the spot-check itself. Note:
this CHANGES conviction gate inputs → it is a Phase-C-adjacent edit;
`homily_conviction.py` is frozen, so implement as a data override the
conviction call already supports, or schedule as the quarter's gated
session if it needs an engine edit. Decide at build time; if engine edit,
it queues behind R10.

### #26 · Breadth canary (S, info-only)
% of universe above 200d SMA + % weekly RED, one line under the regime
banner when <30%. Pure read of already-fetched bars in build_digest.
**Gate:** info-only by design; fixture test for the threshold line.

### #28 · Trim-rule flags (S; needs #27 — met)
PLAYBOOK §5 as flags on held rows: Rule 1 (bought-not-earned >10% → "trim
to 10%"), Rule 2 (⚪ 12w + F:0–1 → "sell-half review"), Rule 3 (thesis
break — manual, no flag). Flags only, no SELL state.
**Files:** `homily_positions.py` or the row formatter; validate fixtures.
**Gate:** rules mirror §5 verbatim (assert the wording in the test).

### #29 · Concentration lens (M; design D-29)
90d daily-return correlation over held names (stdlib math on bars already
fetched), greedy clustering, one digest line + a warning when a ⭐ add
would deepen a >60% cluster. **Gate:** correlation math fixture (two
synthetic correlated pairs cluster; an anticorrelated name doesn't);
info-only.

### #32 · IBKR Flex auto-sync (M)
Flex Web Service token + queryId as repo secrets; fetch positions at run
start → rewrite holdings.json positions (shares/cost only — bucket,
currency, source tags are owner-owned fields and must survive a sync).
Fallback stays manual. **Gate:** parser fixture on a canned Flex XML;
sync is non-fatal (fetch failure → yesterday's book + a digest warning).
**Risk:** silent book drift — print a one-line diff of what changed.

### #33 · Sunday deep-dive (M; needs #13, #36)
Weekly message = #36 dashboard regenerated + one summary (per-holding 12w
state timeline, conviction drift, the week's 🐳/VH events). Mostly
composition of existing pieces; ships after #36. **Gate:** none (delivery).

### #14 · Live scorecard (M; needs ~3 ledger months → first read ~2026-10)
Forward 1/3/6-month returns of every past ⭐/🔵/🚀 row vs same-day SPY,
split by state, conviction decile, and #64 origin. Monthly digest section
+ a docs page (fold into #36). Uses adjclose (#18) for return math.
**Gate:** it IS the gate for everything else. Hard rule: rows enter the
scorecard only at their recorded ledger date (R3).

**#14a · Flip scorecard (S rider, early read).** Same referee, shorter
horizon: every state *transition* in homily_signals_log.csv (e.g.
CAUTION→BOTTOMING, HOLD→ACCUMULATE) gets forward 1/5/20-day returns vs
same-day QQQ, split by transition type. First read possible ~1 month
after log start (2026-07-09) — the early smoke test while #14 proper
waits for 3 ledger months. Same R3 rule: flips enter at their logged
date only; no retro-editing. *(Owner-requested 2026-07-11 after the
META/SHOP/NVDA flips of 07-10 all confirmed next session — one good day
is anecdote, this makes it measurement.)*

### #24 · rs12-top3 promotion decision (due 2026-10-01+, design D-24 + PRD §5j)
Pre-registered: promote ⭐ ordering/allocation to top-3-by-RS12 ONLY if
(a) the ledger forward-check passes — Jul–Sep top-3-RS12 ⭐ rows
outperform other ⭐ rows on forward returns (rs12_rank column, live since
2026-07-10), and (b) Q4's R10 slot is free. If promoted: daily_run ⭐
ordering + `homily_buyday.MAX_STARS`/ordering + PLAYBOOK §3.4 wording, one
session, one commit. If the forward-check fails: record in §8.5, close.

### #20 · Conviction-score backtest (L; design D-20)
Point-in-time daily replay, both universes, calling live `conviction()`
(R6 — never a reimplementation); forward 6m/12m by score decile + tier
hit-rates + the let-through wreck list. Decision rule pre-committed in
D-20: non-monotone deciles → 🚀 footer relabelled "shortlist, no measured
edge"; weights change only on a monotone OOS signal (and then queue behind
R10). **Gate:** the backtest itself.

### #21 · Refine-loop re-point (M; design D-21)
New objective (mean fwd-60d excess of would-be-⭐ days minus false-block
penalty) logged in PARALLEL for 30 days — new columns, old rows untouched
(R2); `homily_champion.json` gains an `"objective"` field. Switch only
after the parallel run and only via the same OOS margin. **Gate:** the
30-day parallel log comparison.

### #65 · Mechanical universe (L; design D-65) / #66 · Right-stock
discipline (M–L; D-66) / #67 · Hard-rule audit (M; D-67)
Owner-requested studies with pre-committed decision rules — build exactly
per their DESIGNS sections (they are already spec-grade). Each is its own
session; #65 needs a shadow quarter in the ledger before any swap; #66's
💎 row stays info-only until it beats DCA and unfiltered-⚪ dips OOS;
#67's cap moves only UP, never OFF, and only per its rule.

### #39 · Bootstrap CIs (M; design D-39)
Circular block bootstrap (block 6, 10k resamples) over the monthly return
series of `homily_strategy_backtest.py`; MOIC percentile bands + P(strategy
> QQQ DCA); mandatory caveat line. **Gate:** deterministic with a fixed
seed; validate asserts the caveat string is present in the output.

### #76 · Planning-doc pruning (S, docs-only — token optimization)
**Goal:** PRD + DESIGNS + SPECS + EXECUTION are ~2,000 lines combined and
every session (human or model) pays that context cost up front. Shrink the
live docs to what a future session needs to *act*, without losing history.
**How:** create `docs/archive/`; move verbatim (never rewrite, never
delete): resolved PRD addenda (§5c–5j), §8.5 execution notes older than
the current month, DESIGNS Part I designs whose items shipped, and the §0
status-ledger rows' back-story. Leave a one-line pointer at each original
location (`→ docs/archive/<file>#<anchor>`). Collapse shipped idea-bank
rows (PRD §8.3) to one-liners. Keep all item numbering intact — #14's
scorecard and the provenance audit (#67) reference these numbers.
**Gate:** docs-only — validate green, goldens untouched; spot-check that
every archived section is reachable from a pointer where it used to live.

### T3 · MCP order routine (own session; PRD §9.2)
Only after: two T2 months executed verbatim + cloud GitHub access fixed.
Guardrails are IN the PRD (§9.2) and non-negotiable: AUTOTRADE variable,
whitelist = that day's ⭐ + index ETF, buy-only LIMIT ≤ close×1.01 day
orders, per-order/monthly caps, no margin, HK excluded, one attempt then
report; first month report-only diffed against T2's basket.

## 3 · In-flight work — RESOLVED 2026-07-11

The concurrent planning session committed (#68–75 slotting, §5k → #77–82,
#76 pruning spec) and this section's reconcile is done: #70 shipped (gate
[32]), the #69 forward-checker + #80 whale_rank column shipped together
as flagged (gate [31]), #14's spec addition and #14a live in §2, the PRD
§8.5 session-0 note is written. Still open from that pass: **#71
scorecard power line** (rides #14, build them together), **#75 snapshot
schema contract** (ride #36), **#76 doc pruning** (any docs-only
session), and the #77–82 gated research queue (slotting in PRD §8.1).

*Written 2026-07-11 by the executing model (session 0, late). If reality
contradicts a spec, record it in PRD §8.5 and stop — don't improvise.*
