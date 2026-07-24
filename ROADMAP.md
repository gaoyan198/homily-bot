# ROADMAP — 2027 · 2031 · 2036

**Date:** 2026-07-24 · **Owner:** gaoyan · **Status:** standing plan,
re-read every July alongside the #40 annual re-test.

PRD §8 owns the near-term backlog (items, gates, phases). This document
owns the multi-year arc: **when the live ledger becomes able to render a
verdict, what each verdict binds us to, and what has to survive long
enough to reach it.** The north star does not change at any horizon:
§9.0's live, measured excess return vs SPY/QQQ DCA on the same cash
flows. Nothing below adds a signal; signals still enter only through
PRD §8's gates and EXECUTION.md R10.

## 0. The honest starting point (read before any horizon)

As of 2026-07-22 (BACKTEST_RESULTS §16b) the engine still **loses to QQQ
on the 10-year honest control** — 2.69× vs 2.86×, carried at −62% MaxDD
vs QQQ's −34%. The backtested case for this system rests on selection +
never-sell (§5f), and that case is *promising on the honest window,
unproven live*. Therefore the long-range plan is not "scale the edge" —
it is: **keep the referee honest, keep the operation alive, and let the
pre-registered reads decide**. Every horizon below ends in a verdict
rule written now, so future-us cannot re-shop it after seeing the data.

The three ways this system wins, in priority order (from §8.0's measured
lever ranking — unchanged):

1. **R0 — the routine executes.** Savings rate + discipline dominate any
   signal change. This survives even a zero-alpha verdict.
2. **R1 — the record stays honest.** Uncorrupted bars, append-only
   ledger, pre-registered gates. Without this no verdict means anything.
3. **R2 — selection alpha, if it exists,** shows up in the #14 scorecard
   above the #71 noise band. If it never does, rule R-2029 below fires.

---

## 1. Horizon 1 — the verdict year (now → end 2027)

Nothing new to invent; the year is already scheduled by dated reads.
The job is to *hit the dates* and protect the referee.

| When | What decides | Binds |
|---|---|---|
| 2026-08-22 | #21 refine-objective switch read (30 rows of parallel J) | champion selection stays Calmar unless the parallel run separates |
| ~2026-10 | **#14 scorecard build + first read** (with #71 noise band, #85 three-epoch split, #64 origin split) | the referee exists; no promotion/demotion on a first read inside the band |
| 2026-10-01 | #24 rs12-top3 frozen Jul–Sep forward-check · #65 shadow-quarter adoption read · five-way selection harness (equal · rs12 · whale #80 · rs6 · blend #89) | FAIL on #24 demotes to equal-split-max-5 mechanically; #65 pass = rule-governed universe starts replacing the hand list |
| 2026-Q4 | survival/exit lane ships as gates pass (post-R10-re-cut): #79 whale-distribution tag (+mLHLL, scope guard verbatim) · #67 whale-cap 1.6% | each with registry entry + demotion rule, one at a time |
| ~2027-01 | **swing sleeve 26-week clock** (live-armed 2026-07-10): KILL-A/-B stand as written · #96 stop-cost A/B verdict (26 wk / 20 closed) · #98 ladder step-1 preconditions | a KILL fires = liquidate + failure memo, no renegotiation; ladder steps only with the owner-signed A5 line |
| ~2027-01 | #71's own estimate: first scorecard read where edges become *readable* | promotions may cite the scorecard from here, never before |
| 2027-Q2 | R10 **selection** slot free (first since the 2026 overrides) | at most ONE of the queued candidates ships — #20 weights · #25 real mcap · the #23/#74/#81 confluence winner — chosen by what the October reads said, not by novelty |
| 2027-07 | #40 annual re-test + **first live-vs-sim reconciliation** (a full year of ledger vs what the backtests promised) | divergence = the overfit alarm; findings go to BACKTEST_RESULTS and gate the next promotion |
| 2027-12 | **R-2027 year-one verdict** (rule below) | posture for Horizon 2 |

**R-2027 (pre-registered now):** at 2027-12-31, publish the #14
scorecard (~18 months of rows) against the frozen #71 band, split by
origin and promotion epoch. If the live edge is **above** the band:
continue, and T2→T3 automation may proceed on §9.2's own gates. If
**inside** the band: continue unchanged — 18 months was always expected
to be underpowered; no new selection machinery ships just to "find" an
edge the band can't read. If **below −band**: freeze all selection
promotions (R10 slot goes unspent) until a read returns to the band.
No other action is authorised by this read.

Owner to-dos that block the above and belong to no session:
IBKR_FLEX secrets (#32) · MARGIN_ZERO (arms #93 and retires the ⏳
SETUP line) · BUY_BUDGET_USD restored after the paydown.

---

## 2. The alpha program — where the algorithm actually improves

*(Added 2026-07-24, same day as the file, on the owner's challenge: "no
improvement in the algorithm at all?" The first draft had the referee
and the survival plan and no research program — the same gap the owner
called out on 2026-07-22 before the R10 re-cut, and it was a fair hit
both times. This section is the fix. No honesty constraint is relaxed
by it: studies are free, promotions pay the R10 selection price, nulls
close honestly.)*

**The shot budget.** Under R10-as-re-cut the pipeline's throughput is
fixed and knowable, so plan with it instead of around it: **SELECTION**
changes (which names get money; how they're ranked, ordered, weighted)
ship at most one per quarter → ~4/yr, **≈20 shots by R-2029's read,
≈40 by R-2036's**. **SURVIVAL/EXIT** recalibrations ship whenever they
pass a pre-registered gate — unthrottled. Studies are never budgeted,
only promotions are: run as many honest experiments as sessions allow.

**Where the shots aim** — by §8.0's *measured* lever ranking, not by
what is fun to build:

1. **Selection (R2) — most shots go here.** The backtested edge, where
   it exists at all, is cross-sectional (§5f). Every selection idea
   funnels through one door: the #120 bake-off.
2. **Drawdown repair (R3) — the measured failure.** §16b's gap is not
   CAGR, it is carrying −62% against QQQ's −34%. This is
   survival/exit-lane work — the lane the re-cut deliberately
   unthrottled — and the plan expects the most tractable wins here,
   because #51 already proved the pattern: the §5.2 clock is the only
   arm ever measured to ADD return.
3. **Timing (R4) — smallest measured lever.** At most one modifier per
   quarter through #23's confluence harness. Never more; every timing
   study so far that promised more (#77, #86, #104, #108, #110) died
   honestly in its control.

**The pipeline by horizon.**

* *In flight, 2026–27 (already dated in §1):* the five-way rank read
  2026-10-01 (equal · rs12 · whale #80 · rs6 · blend #89) · #20 weight
  change · #79's distribution-tag ship · #23/#74/#81 confluence
  modifiers · #25 real market cap · #21 refine re-point. A full year of
  algorithm work is already scheduled — Horizon 1 was never the gap.
* *2028–2031 (standing machinery, #120–122):* the **annual selection
  bake-off** (#120) turns #24's one-off harness into the permanent July
  fixture every new ranking idea must enter and win — an F:n/m ranker,
  the #66 Q label, whale level, whatever Danny teaches next. The
  **drawdown-repair series** (#121) works the R3 gap study by study.
  **Universe capacity** (#122) widens the pool selection picks from
  once #65 earns adoption — top-3-of-200 has more room than
  top-3-of-124, if and only if ranking quality survives, which is the
  gate. Blocked-but-standing, never dropped: #41 supervised Homily fit
  (needs owner-exported labels) and #45 delisted-inclusive data (needs
  a free source; it is the biggest single data upgrade available and
  unlocks honest live universe construction).
* *2031–2036 (#123):* **ledger-fitted selection** — by ~2031 the live
  ledger is 5+ years of point-in-time rows that cannot be
  survivorship-biased or hindsight-constructed: the one training set
  this repo can trust outright. Walk-forward fit of the ranking weights
  on our own live record, features restricted to existing ledger
  columns, fitted weights printable in one digest footer line (§8.2's
  ML exclusion stands — nothing unprintable ever gates money). It
  enters #120 like every other challenger and wins or dies there.

**What the program does not promise.** Shot quality and shot volume are
guaranteed; the edge is not. If forty honest shots and ten live years
cannot put the scorecard above the band, R-2036 reads that as the
answer — the program is how we make sure the answer, either way, was
earned rather than defaulted.

---

## 3. Horizon 2 — 2028–2031: the era of the binding read

By mid-2029 the ledger holds ~3 years of live rows and the #71 band is
narrow enough to read a realistic edge. This is the system's first
genuine, adequately-powered exam — and the fork is written **now**:

**R-2029 (pre-registered, the three-fork rule):** at the 2029-07 annual
re-test, take the #14 scorecard, cash sleeve only, since-inception,
against the frozen band method (#71's block-bootstrap, method already
frozen — any change to the method before this read voids the read):

* **(a) Edge above the band → SCALE.** T3 automation runs full (§9.2
  gates unchanged); the swing ladder may climb its owner-signed steps;
  cap/concentration re-reads use their existing demotion rules; the
  LEVERAGE.md ladder may widen only via its own §5 yearly re-run. Scaling
  means *more of the same measured thing* — not new signal families.
* **(b) Edge inside the band → HOLD & CHEAPEN.** The verdict is "not
  readable yet" — legitimate at n≈3y for a realistic edge. Keep the
  routine, spend the years' effort on ops cost (fewer sessions, more
  automation of the *measurement*, aggressive #115 pruning), not on new
  degrees of freedom. The R0 machinery already pays for itself at zero
  alpha: the behaviour gap it closes is real return.
* **(c) Edge below −band → DEMOTE TO DISCIPLINE MODE.** Signal engines
  stop gating money: the buy-day copilot routes 100% to the index leg,
  ⭐/tiers/ranks go info-only, the swing sleeve winds down at its next
  KILL/verdict boundary, R2/R4 machinery retires to the archive. What
  survives is what was measured to work: DCA + never-sell + risk lens +
  execution copilot (R0, R3) and the honest ledger. **This fork is the
  price of calling §9.0 a north star.** Writing it in 2026, before the
  data, is the only reason a 2029 read against us will be believed —
  and obeyed.

The read repeats every July after 2029 under the same rule; forks are
reversible in either direction on a later read (demotion is not
deletion — the engines keep running info-only, so re-promotion has a
live shadow record to cite, the #65 pattern).

**Survival workstreams for the era** (this is the actual 5-year risk
list — each is a numbered item in §5 with its own gate):

* **Data durability** — Yahoo is the single largest existential
  dependency. #113 bars vault + #114 fetch failover, both proven by
  restore drills, not by hope.
* **The first live bear.** Every 🐻 protocol, margin-zero rule, crash
  pre-script (#59) and bear-readiness line (#30) was shipped in a bull
  tape. The first real regime flip is a drill we don't schedule — so
  the rehearsal machinery must stay green every quarter until it fires.
  PLAYBOOK §4 stays human, forever (§9.1).
* **Model succession.** The owner's division of labour (planning model /
  executing model, DESIGNS Part III) must survive model swaps. #115's
  cold-start drill proves the docs are sufficient — yearly, with a
  model that has no memory of this repo.
* **Complexity budget.** ~50 harnesses and growing; nulls are supposed
  to be closed, not accreted. #116 makes pruning a July cadence with a
  mechanical rule.
* **Whole-book truth.** contributions.json accrues a NAV history from
  2026-07 — around 2028 the #94 rolling 12/24/36-month windows unlock,
  and the household scorecard becomes the owner's real net-worth
  referee (SRS + ESPP + core + swing vs one QQQ counterfactual).

---

## 4. Horizon 3 — 2031–2036: the endowment test

At ten years the founding question — *does selection + never-sell,
executed with discipline, beat QQQ DCA on the same cash flows?* — has a
definitive live answer with real statistical power.

**R-2036 (pre-registered):** the 10-year scorecard read is **binding
and benchmark-final**. No re-benchmarking (not to SPY-only, not to a
"risk-adjusted" reframe chosen after the fact, not to Danny's
self-reported numbers), no window-shopping the start date. The same
three forks as R-2029 apply, but at this power **fork (b) collapses
into (c)**: an edge still unreadable after ten years of rows is, for
this book's purposes, not there. The system that survives fork (c) is
still valuable — an honest, automated, risk-shaped DCA machine with a
decade of append-only records — and that outcome is a success of the
process, recorded as such.

**Assume-decay planning** (write it now, so each death is ops, not
crisis): over ten years, expect to lose *at least one of each* —
the data source (Yahoo), the delivery channel (Telegram), the scheduler
(GitHub Actions), the broker interface (IBKR Flex/MCP), and the
teacher (Danny's feed goes quiet or paywalled — after which the system
stands only on its own measured record, which is the point of the
record). The stdlib-only / no-server / flat-file constraints are the
ten-year bet that pays here: every component is replaceable behind an
interface the repo already owns. #118 drills the two most likely
deaths in advance.

**Capital lifecycle.** Somewhere in this decade the book's job may
change from accumulation to funding something (a house, a sabbatical,
retirement glide). That is an *owner life decision with a dated
trigger*, not a signal — and the trigger fired early: **2026-07-24 the
owner set — and same-day honestly re-dated — the target: S$2M by ~47
with a S$600k checkpoint at 40 (PLAYBOOK §8.1)**, self-assigned to the
savings lever after seeing the ~60%/yr arithmetic. #119's *study* still
waits on its proximity condition (≥S$1M or 2030-07), and sells remain
human forever (§9.1 is not relaxed at any horizon). What the plan owes the owner meanwhile: the
household scorecard (#94) keeps the whole-book number visible monthly,
so the day the question arrives, ten years of honest data are already
on the table.

**The docs are the asset.** By 2036 the durable value of this repo is
(1) the ledger + scorecard record and (2) the operating manual that
lets any competent operator + any competent model run it cold. Code is
the cheapest layer to regenerate; the record and the rules are not.
#115's yearly drill is the proof this stays true.

---

## 5. New numbered items #113–#123

PRD §8.3 numbering continues here (#101–#112 spent; #124 = the §8.1
target line, shipped same day, row in PRD §8.3; next free: #125). Same law as every §8.3 row: pre-registered gate,
info-only until promoted, null → closed honestly. #113–119 are
infrastructure — none is a signal, none consumes an R10 selection slot.
#120–123 are the §2 alpha program: their STUDIES are free, their
PROMOTIONS pay the normal R10 selection price like everything else.

| # | Item | Effort | Gate |
|---|---|---|---|
| 113 | **Bars vault — data durability.** Periodic (monthly, workflow-committed per R8) compressed snapshot of every universe name's raw + adjusted bars, so a Yahoo death or silent history rewrite can neither orphan the ledger nor un-reproduce a published backtest. Retention: last 4 snapshots + one frozen per year | S–M | restore drill: a full daily run + one committed backtest reproduce from the vault alone, network off |
| 114 | **Fetch failover chain.** Promote #60's Stooq cross-check from warn-only to an ordered fallback (Yahoo → alternate) used ONLY on hard fetch failure — never silent source mixing; the digest prints the source the day it isn't Yahoo, and #60's agreement check runs on every failover day | M | canned-outage test: primary dead → run completes on fallback with the source line printed; disagreement > tol still warns, never halts (R4) |
| 115 | **Cold-start runbook + yearly succession drill.** `COLD_START.md`: from a fresh clone + secrets list to a verified daily run and one monthly buy-day sheet, no memory assumed. Drilled every July by a session with no prior context of this repo (new model preferred — that's the real test) | S build · S/yr | the drill itself; every failure patches the DOCS in the same session, never the drill-runner's memory |
| 116 | **Complexity budget — the July prune.** Rides #40: every module/harness must hold one of {live consumer · dated pending read · archive}. Closed-null harnesses move to `docs/archive/` with their BACKTEST_RESULTS pointer; the #73 digest line budget stays capped; net top-level module count may not grow year-over-year without a §8.5 note saying why | S/yr | docs-only gate: validate green, goldens untouched, every archived piece reachable via pointer |
| 117 | **R-2029 verdict freeze.** Turn §3's three-fork rule into a checked artifact before it can matter: the band method pinned to the committed #71 implementation (hash), the fork thresholds and the demote-to-discipline mechanics written into a validate case that fails if the wording drifts from this file | S | validate case pins ROADMAP §3 wording + #71 method hash; any later edit to either requires a deliberate re-pin with a §8.5 note |
| 118 | **Platform-migration drills.** Prove the two most likely platform deaths are ops: (a) delivery — digest to a second channel (email or file-drop) behind the same send interface; (b) scheduling — the daily run from a plain cron/launchd on any box. One drill each, adapters kept as dormant code paths | S–M | each drill = one real end-to-end delivery/run via the alternate path, logged in §8.5; no standing infra, no new secrets kept live |
| 119 | **Glide-path study (trigger SET 2026-07-24; study still parked on proximity).** The dated trigger fired: PLAYBOOK §8.1 names **S$2M household (SGD, #94 figure) by ~47, with a S$600k checkpoint at the 40th birthday (2032-07)** — re-dated same day from the original before-40 demand after its needed-DCA priced at S$18–21k/mo (beyond any salaried path; the owner called the print demoralizing and the deadline moved, not the honesty) — owner-assigned to the SAVINGS lever (contribution growth), explicitly never to the investing rules. The de-risking study itself stays parked — at ~2.5% of target a glide-path analysis is decoration — behind a proximity condition pre-registered NOW so it can't be re-shopped: **unpark when the #94 household figure first closes ≥50% of target (S$1M) OR at 2030-07, whichever comes first**; at unpark, study contribution-redirect vs allocation-shift paths on the honest windows, same control discipline as everything else | L (later) | trigger = PLAYBOOK §8.1 (met 2026-07-24); unpark = the ≥S$1M-or-2030-07 condition above; study gate pre-registered at unpark time; sells stay human (§9.1) regardless of outcome |
| 120 | **Annual selection bake-off — the standing harness (from 2028-07).** Generalize `homily_selection_backtest.py`'s K-way comparison into a permanent July fixture: every accrued challenger rank (rs12 · rs6 · blend · whale_rank #80 · an F:n/m ranker · the #66 Q label · whatever columns exist by then) re-run on all three construction-honest windows PLUS the live ledger's accrued forward rows. Every new selection idea enters here and wins or dies here; at most ONE promotion per run (the R10 selection budget is the harness's output limit, not its input limit) | M build · S/yr | challenger must tie-or-beat the incumbent on all three honest windows incl. hype-2021 AND on the accrued live rows (#71's band arbitrates the live side); else the incumbent stands |
| 121 | **Drawdown-repair series (survival/exit lane — unthrottled).** §16b's measured failure worked as a program, one pre-registered study per session on an EXISTING exit/stop/cap/clock — candidate queue: trailing shelf-loss exit · regime-scaled CAUTION clock · bear-onset satellite tightening · staged-add shapes (#50) — target metric frozen per study: honest-window MaxDD reduced at non-inferior MOIC, both universes. #51 is the proven pattern (the §5.2 clock is the only arm measured to ADD return) | M each | per-study rule frozen before the run; PASS ships with registry entry + real demotion checker (the #51 pattern); NULL closed — no re-tuning toward the target metric |
| 122 | **Universe capacity growth (blocked on #65 adoption).** Selection alpha scales with the pool it picks from: after #65's shadow quarter earns adoption, widen the L2 cut stepwise (124 → ~200) and re-run #120 at each step — top-3-of-200 beats top-3-of-124 only if ranking quality survives the dilution, which is the gate, not the hope | S–M per step | each widening re-runs the #120 bake-off; top-3 quality on the wider pool ≥ the narrower pool's on all honest windows, else the step reverts |
| 123 | **Ledger-fitted selection (date-gated ≥2029-07).** By then the live ledger is ≥3y of point-in-time rows that cannot be survivorship-biased or hindsight-constructed — the one training set this repo can trust. Walk-forward fit of ranking weights on our own live rows ONLY; features restricted to existing ledger columns; the fitted weights must print in one digest footer line (§8.2's ML exclusion stands — nothing unprintable ever gates money). Enters #120 as a challenger; never ships directly | L | ≥3 live ledger years before the first fit; must beat the incumbent on a held-out live year AND pass #120's full bar; refit yearly, never intra-year; else closed |

---

## 6. Standing cadence — the plan is that the cadence survives

| Cadence | What |
|---|---|
| Monthly | buy-day routine + reconcile (#72) · household block (#94) |
| Quarterly | R10 selection slot (max one) · universe hygiene (#44) · swing skim (#95) · rehearsal machinery green |
| Yearly (July) | #40 re-test + live-vs-sim reconcile · **#120 selection bake-off (from 2028)** · LEVERAGE.md §5 re-run · #116 prune · #115 cold-start drill · re-read THIS file |
| 2027-12 | R-2027 read (§1) |
| 2029-07, then yearly | R-2029 three-fork read (§3) |
| 2036-07 | R-2036 binding read (§4) |

Ten years from now the deliverable is not a cleverer signal. It is an
unbroken ledger, a scorecard someone can believe, and a system a
stranger could operate. Everything above serves that.
