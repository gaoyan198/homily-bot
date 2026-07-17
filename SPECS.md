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
| #24 rs12-top3 — PROMOTED EARLY 2026-07-12, owner override (§2·24) | 2026-07-10 / 12 | backtest PASSED; forward-check publishes at month-starts through 2026-10-01; demotion rule armed (promotions.json) |
| #27 position-aware book math | 2026-07-10 | validate [26] |
| #31 buy-day copilot + T2 basket CSV | 2026-07-10 | validate [27] |
| #35 chart cards (stdlib PNG) | 2026-07-11 | validate [28] pixel-hash |
| #64 provenance column | 2026-07-11 | validate [29] |
| #30 bear-readiness line | 2026-07-11 | validate [30] |
| #69 promotion registry + #80 whale_rank column | 2026-07-11 | validate [31] |
| #70 missed-run detector | 2026-07-11 | validate [32] |
| #61 engine-freeze manifest guard | 2026-07-11 | validate [39] (negative case proven) |
| #76 planning-doc pruning | 2026-07-11 | docs-only — validate green, goldens untouched, archive pointers verified |
| #14a flip scorecard rider | 2026-07-11 | validate [40]; first matured read ~2026-08 |
| #39 bootstrap CIs | 2026-07-11 | validate [41]; CI table = BACKTEST_RESULTS §6 |
| #82 ribbon run-length + digest suffix | 2026-07-11 | study ran (§7); conditioning null per its own rule |
| #78 pullback clock + dip counter | 2026-07-11 | stability rule PASSED (§8), validate [42]; p90-warning refuted, never ships |
| #77 multi-timeframe VH | 2026-07-11 | NULL, closed (§9); consumed Q3's timing-modifier slot |
| #79 whale-distribution study | 2026-07-11 | gate PASSED (§10); ship queued behind R10 (+mLHLL variant preferred) |
| #20 conviction-score backtest | 2026-07-11 | ran (§11), validate [43]; score ranks OOS, tier cuts null, no relabel |
| #67 hard-rule audit | 2026-07-11 | pre-committed rules applied (§12); cap stays + premium quoted in PLAYBOOK §3.4 |
| #21 diagnostic + parallel J log | 2026-07-11 | validate [44]; switch read ≥2026-08-22 (§13) |
| #66 Q-tier gate + label | 2026-07-11 | wreck-separation FAILED (§14), validate [45]; label-only ships, 💎/veto dead |
| #65 universe.json + shadow quarter | 2026-07-11 | validate [46]; adoption read ~2026-10 |
| #83 Danny chart board (searchable, dual boards) | 2026-07-12 | validate [33] extended; §8.5 size-split note; goldens untouched |
| #84 any-ticker chart CLI | 2026-07-12 | validate [47]; R3 pinned mechanically |
| #90 GAMBIT merge — self-contained `gambit/`, weekly CI, ♟️ SWING block | 2026-07-12 | all four D-90 gates: both validates green (gambit 70 tests from new location, homily [48], zero golden re-pins) · journal chain verifies · same-bars replay byte-identical through both trees · tombstone in the old repo. Deviations in PRD §8.5 |
| #91 leverage ladder — backtest PASSED at 1.30×, LEVERAGE.md signed, ⚖️ digest line | 2026-07-12 | pre-registered readout (BACKTEST_RESULTS §15) + validate [49]; rule-5 override recorded in §8.5; yearly re-run + shrink rule = LEVERAGE.md §5 |
| #92 add-cap 10%→25% — PROMOTED (owner override; promotions.json "add-cap-25") | 2026-07-12 | D-67 prongs + demotion watch live every run (validate [50]); goldens re-pinned deliberately; next free R10 slot 2027-Q2 |
| #93 swing sleeve LIVE-ARMED (Amendment A5, owner override of the P2 gate) | 2026-07-12 | A5 two-artifact; kill rules pre-registered (KILL-A −30% contributed / KILL-B 20-trade expectancy); arms on MARGIN_ZERO; validate [51] + 10 pytest cases; paper book = counterfactual |
| #94 household scorecard (`homily_household.py` + `contributions.json`) | 2026-07-12 | validate [52]; first-Monday whole-book vs QQQ-DCA money-weighted (opening balance seeded, §8.5), USD+SGD, combined gross-L vs cap, missing-month nag; info-only, goldens untouched |
| #95 flywheel skim (`gambit_live.maybe_skim` + homily buyday/swing wiring) | 2026-07-12 | gambit pytest (6 new live cases, 86 total green) + homily validate [51]; quarter-end skim, kill-safe (contributed/realized untouched), baseline=contributed (§8.5), PLAYBOOK §7/§9 + A5 amended; goldens untouched |
| #96 A5 A/B reader (`gambit/gambit_ab.py`, wired into `homily_swing.monthly_block`) | 2026-07-12 | gambit pytest `test_gambit_ab.py` (9 cases) + homily validate [51]; read-only stop-cost attribution vs the paper leg, verdict gated 26wk/20-closed, report-only; goldens untouched |
| #98 swing scale ladder (`gambit_live.SCALE_STEPS`/`scale_check` + `gambit_validate.check_scale`) | 2026-07-12 | gambit pytest 4 cases + `gambit_validate` [SCALE]; K6-pattern CI guard — off-ladder or unsigned-step fails; `--scale-check` advisor; policy in gambit PRD §3.5; pure constraint, no R10 slot |
| #97 cross-book lens (`homily_clusters.combined_view` + `gambit_live.overlap_warning`) | 2026-07-12 | homily validate [36] + gambit pytest 2 cases; swing+ESPP folded into #29 (correlation math untouched), combined line only when it deepens the top cluster; sheet warning on >2 shared names; info-only, goldens untouched |
| #99 ops-readiness (`homily_ops.py` + `gambit_live.kill_watch`) | 2026-07-12 | homily validate [53] + gambit pytest 2 cases; standing ⏳ SETUP blockers line (MARGIN_ZERO/Flex/BUY_BUDGET + margin progress), one-shot KILL-A proximity warning; info-only, goldens untouched; #73 interlock still unbuilt (§8.5) |
| #100 realized-cost reconcile (`gambit/gambit_reconcile.py`, wired into `homily_swing.monthly_block`) | 2026-07-12 | gambit pytest `test_gambit_reconcile.py` (7 cases) + homily validate [51]; financing effective rate vs modeled 5.8% (feeds LEVERAGE.md §5) + fill slippage vs 0.35% stress arm; read-only, silent without a statement; dark until #32 secrets |

## 1 · Remaining queue (updated 2026-07-12)

**Shelf sweep 2026-07-17** (owner: "execute the rest of the pipeline") —
one branch per item, gates restated first, validate [56]–[61] added:
~~#89 column~~ (Phase-C, rs6 exposed + `rs6_rank`, forward rows from
07-20) · ~~#88~~ (turnover footer; July already churns daily) · ~~#73~~
(header zone CI-capped at 12) · ~~#51~~ (**PASSED** — w=2/8wk beats the
declared 12w on both honest windows; §5.2 edit QUEUED behind R10,
BACKTEST_RESULTS §16) · ~~#86~~ (**NULL**, closed — every cell loses to
immediate deployment; dips are never scarce in a 30-name screen, §17) ·
~~#87~~ (**NULL**, closed — sign-flip real but the fallback untradable,
§18) · ~~#59~~ (flash-crash pre-script) · ~~#60~~ (data-QA warnings) ·
~~#54~~ (Sunday what-changed diff). Earlier same day: ~~#102~~ (bearish
tells, validate [55]).
**Still on the shelf, each its own session:** #57 中文 toggle (S in
name, but it touches every digest string → golden regen; do it alone) ·
#58 behaviour-gap tracker (M — needs a persisted shadow book design) ·
#47/#48/#50/#52 studies · #53 absorbed by #94. Studies remain buildable
anytime; only *shipping* a money-touching result queues behind R10
(queue now: #79 tag · whale-cap 1.6% · #20 weights · #51's 8wk edit —
next slot 2027-Q2).

**Integration-era shelf (#94–100, added 2026-07-12 late; designs
D-94…D-98).** The leverage era armed four money surfaces (core cash,
SRS, ESPP, levered swing + paper counterfactual) with no instrument
that reads them together. None consumes an R10 slot — measure/integrate/
harden, not new signals. Buildable now, ordered by what the calendar
forces:
* **#95 flywheel skim (M, D-95) — build before 2026-10-01**, the first
  quarter-end the live book could clear its HWM; mechanizes the A5
  "proceeds fund the DCA" line with a pre-registered skim rule + a
  measured flywheel table. Kill math stays byte-identical (skims never
  soften KILL-A).
* **#99 ops-readiness block (S) — rides #73's line-budget session**;
  keeps the owner's own blockers (MARGIN_ZERO, Flex secrets,
  BUY_BUDGET restore) and the KILL-A distance visible; one-shot 80%-of-
  contributed alert (#15 pattern).
* **#98 scale ladder (S, D-98) — pure-constraint CI guard, land before
  the first top-up temptation**; US$3k→6k→12k earned by the live
  journal, K6-pattern validate check.
* **#94 household scorecard (M, D-94) + #97 cross-book lens (S–M, D-97)
  — build alongside the ~2026-10 #14 session** (shared adjclose /
  counterfactual / monthly-block machinery; #97 extends #29's lens
  inputs, math untouched).
* **#96 A5 A/B reader (S–M, D-96) — buildable now, verdict row
  date-gated** (26 live weeks / 20 closed); read-only over both
  journals.
* **#100 realized-cost reconcile (S) — waits on #32 Flex secrets** like
  every reconcile; feeds LEVERAGE.md §5's yearly re-run the true
  financing rate + fill slippage.

~~**Next build sessions (owner-requested 2026-07-12):** #83 + #84~~ —
**both shipped 2026-07-12** (gates [33]/[47]; the committed-board size
contradiction is recorded in PRD §8.5). The mockup file is deleted as
spec'd; `HOW_TO_READ.md` is the manual.

~~**Next build session (owner-requested 2026-07-12): #90 GAMBIT merge**~~ —
**shipped 2026-07-12** (all four D-90 gates PASSED; §0 row; the paper
book's first journal rows accrued 2026-07-10-decision during the gate
run — the sleeve's 26-week #93 clock is live). Then **#91's
`homily_leverage_backtest.py`** (M, D-91 — must run and pass its
pre-registered readout BEFORE the LEVERAGE.md policy signs; no levered
order exists before the owner signature).

Everything else remaining is DATE- or OWNER-gated:

1. **~2026-08-11** · #14a first matured read (info-only; just run
   `python3 homily_flipscore.py`).
2. **≥2026-08-22** · #21 switch decision — 30 rows of `homily_refine_j.csv`,
   own session, same +10% OOS margin; §13's λ caveat applies.
3. **~2026-10** · #14 live scorecard (+#71 noise band, build together;
   +#85 promotion-epoch split — Q3 carries TWO live changes, 🐳 07-06
   and rs12-top3 07-12, so every read splits by epoch from
   promotions.json or attributes nothing) — 3 ledger months; also the
   #65 shadow-quarter adoption read (D-65 rule) and the first
   #64-split scorecard.
4. **2026-10-01** · #24 forward-check READ (no longer a promotion
   decision — promoted early 2026-07-12 by owner override, Q4's R10 slot
   SPENT; the month-start digest block publishes the frozen-window read
   and runs the mandatory demotion check). Same read hosts the selection
   harness: #80 whale-top3 + #89 rs6/blend arms (each vs the live
   rs12-top3, gates in their rows). QUEUED (each its own gated
   session, R10-spaced, next slot 2027-Q2):
   #79 distribution-tag ship (+mLHLL variant, scope guard verbatim) ·
   #67's whale-cap tightening to 1.6% (+ #31 copilot constant sync) ·
   any #20 weight change · #25 real market cap (engine edit, §8.5) ·
   ~~#92 add-cap 10%→25%~~ — **PROMOTED early 2026-07-12** (owner
   override; §0 row; demotion watch live, validate [50]).
4b. ~~≥2027-01-09 · #93 swing live-arming read~~ — **LIVE-ARMED EARLY
   2026-07-12 by owner override (Amendment A5; P2 gate overridden, not
   passed)**. Standing reads instead: the P2 paper gate keeps publishing
   (♟️ block) as the counterfactual; the A5 kill rules are the live
   book's only exit; **owner to-do: clear legacy margin, then set
   MARGIN_ZERO — nothing trades until then.**
5. **Quarterly** · #65 universe refresh (`--shard k/N` over CI nights) +
   #44 hygiene issue; #74/#81 timing-modifier studies — ONE per quarter.
6. **Owner-gated** · T3 (two clean T2 months + cloud repo access; PRD §9.2
   verbatim) · IBKR_FLEX_TOKEN/QUERY secrets (#32) · MARGIN_ZERO ·
   BUY_BUDGET_USD back to 1550 · F3 only if two weeks of F2 shows
   file-open friction.

Guards #61 (engine-freeze SHA manifest) and #62 (ledger hash) — #62
shipped with #13; #61 shipped 2026-07-11 (`engine_freeze.json`, validate
[39]). Both guards are now live.

~~**#76 planning-doc pruning**~~ — shipped 2026-07-11: resolved PRD
addenda (§5c–5j), shipped §8 item texts, and shipped Part-I designs live
verbatim in `docs/archive/` with pointers at every original location.

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

### #24 · rs12-top3 promotion decision (design D-24 + PRD §5j)
**RESOLVED EARLY 2026-07-12 — OWNER OVERRIDE.** Promoted with NEITHER
pre-registered condition met: (a) the ledger forward-check had not
matured, (b) the 2026-10-01 date had not arrived. The owner directed it
and accepted the risk (verbatim basis in promotions.json). Shipped
exactly the pre-specified surface: daily_run ⭐ ordering (RS12 desc,
top-3 marked `RS#n`) + `homily_buyday.MAX_STARS=3`/ordering + PLAYBOOK
§3.4 — one session, one commit. NOT waived: the frozen Jul–Sep window
read publishes at every month-start digest (new #69 block, wired this
session) through the 2026-10-01 read, and the rolling demotion check is
armed — a FAIL demotes to equal-split-max-5 mechanically. R10: Q4's slot
is spent; next promotion slot 2027-Q1.

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

### #83 · Danny-style chart board — dashboard v2, searchable (M–L; design D-83)
**Goal:** replace the unreadable levels-band cards with per-name
candlestick cards in the Homily/Danny chart language (owner-requested
2026-07-12), searchable over every screened name. The full design — card
anatomy, geometry, normative palette, size budget, label-rail collision
rule, search + distribution split — is **D-83**; the owner-approved
rendering is `docs/mockup-83.html` (three cards + working search bar,
live engine data); the human manual is `HOW_TO_READ.md` (update it if
the build diverges).
**Files:** `homily_dashboard.py` (rewrite of the card section; heatmap /
timeline / refine sections stay; new `--full` mode), `daily_run.py`
(pass `bars_map` to `write_dashboard`; sendDocument the full board),
`homily_validate.py` (extend [33] with fixture bars + size-budget +
inline-script-only asserts). Delete `docs/mockup-83.html` in the same
commit.
**Build:** per D-83 — engines frozen, presentation only; reuse
`homily_png._display_bins` / `_ribbon_circles` (homily_png is not
frozen; share, don't duplicate); candles grouped per colour (one wick
path + one body group), never per-bar elements; snapshot.json schema
unchanged (#75). Search: ticker-chip anchor index (zero-JS baseline) +
sticky filter input (≤20 lines inline JS, enhancement-only — D-36
relaxation recorded in D-83). Committed `docs/dashboard.html` = small
board (held + actionable, ≤300 KB); FULL board sent nightly via
sendDocument, NEVER committed (git-history discipline; regenerate with
`--full`).
**Gate:** deterministic fixture render + self-containment +
inline-script-only + ≤300 KB asserts green; digest goldens untouched
(dashboard-only change).
**Risks:** R8 (committed artifacts unchanged — the full board is
sent-not-committed by design, do NOT add it to git-add); R9 (no "little
fixes" to engine files while in there); the red=bullish legend must ship
— an unlabeled inverse colour convention is a misread waiting to happen.

### #84 · Any-ticker chart CLI (S–M; rides #83's renderer, own session)
**Goal:** `python3 homily_chart.py TICKER [TICKER…]` — the owner can pull
the Homily card for ANY Yahoo-resolvable symbol (incl. `.HK`/`.SI`) on
demand, not just screened names.
**Files:** new `homily_chart.py` (thin CLI: fetch 2y bars →
`danny_signal`/`conviction` read-only → #83's card renderer → one
self-contained HTML in the working dir, path printed); `homily_validate.py`
(one fixture check reusing #83's fixtures).
**Build:** import the card renderer from `homily_dashboard` — zero
duplicated geometry. The card carries an **`ad-hoc — not screened, no
ledger history`** banner; NOTHING is written to the ledger or snapshot
(R3: a chart on demand is context, not a tracked call). Non-fatal on
fetch failure (print the error, render nothing).
**Gate:** fixture render determinism; engines untouched; no ledger/
snapshot writes (assert in the fixture test).
**Risks:** scope — resist making the CLI log "calls"; the ledger records
only what the daily digest printed (R3), and an ad-hoc chart is neither.

### T3 · MCP order routine (own session; PRD §9.2)
Only after: two T2 months executed verbatim + cloud GitHub access fixed.
Guardrails are IN the PRD (§9.2) and non-negotiable: AUTOTRADE variable,
whitelist = that day's ⭐ + index ETF, buy-only LIMIT ≤ close×1.01 day
orders, per-order/monthly caps, no margin, HK excluded, one attempt then
report; first month report-only diffed against T2's basket.

### #94–100 · Integration era (build per DESIGNS D-94…D-98 — spec-grade)
Same pattern as #65/#66/#67: the DESIGNS sections are already build
specs. Each is its own session, engines frozen (these are all read-side
/ gambit-side / info-only), every gate restated before coding. Sharp
edges to honour verbatim:
* **#94 (D-94):** adjclose (#18) for ALL return math; `contributions.json`
  is owner-maintained — a missing month prints the nag, never a guessed
  flow (R3 spirit: don't manufacture history). Info-only forever.
* **#95 (D-95):** the KILL-A check must stay byte-identical before and
  after SKIM rows (assert it in the pytest) — skims leave the casino,
  they never soften a pre-registered kill. HWM ratchets so a profit
  can't be skimmed twice. Amend PLAYBOOK §7/§9 + the A5 reporting
  section in the SAME commit.
* **#96 (D-96):** read-only over both journals — the fixture asserts
  ZERO writes; separate the sizing effect (ladder × US$3k vs paper's
  US$20k notional) from the exit effect so leverage and stops aren't
  blamed for each other; verdict row is REPORT-ONLY (cannot change live
  rules).
* **#97 (D-97):** `homily_clusters.concentration`'s correlation math is
  UNTOUCHED (frozen-spirit) — this is input assembly only (add swing +
  external-ESPP positions); a sheet warning is not a signal input (§4.1
  budget stands).
* **#98 (D-98):** constrains only; the validate check fails a CAPITAL
  top-up row lacking its committed `--scale-check` record + A5 owner
  line (K6 pattern — loud, not debated). No R10 slot.
* **#99:** rides #73's line-budget session and must keep #73's
  golden-file line count green (the block displaces, never adds).
* **#100:** needs #32 Flex secrets; non-fatal on fetch failure (report
  the gap, never block the send).

## 3 · In-flight work — RESOLVED 2026-07-11

The concurrent planning session committed (#68–75 slotting, §5k → #77–82,
#76 pruning spec) and this section's reconcile is done: #70 shipped (gate
[32]), the #69 forward-checker + #80 whale_rank column shipped together
as flagged (gate [31]), #14's spec addition and #14a live in §2, the PRD
§8.5 session-0 note is written. Still open from that pass: **#71
scorecard power line** (rides #14, build them together) and the #77–82
gated research queue (slotting in PRD §8.1); #75 shipped with #36 (gate
[33]) and #76 shipped 2026-07-11.

*Written 2026-07-11 by the executing model (session 0, late). If reality
contradicts a spec, record it in PRD §8.5 and stop — don't improvise.*
