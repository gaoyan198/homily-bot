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
target line, shipped same day, row in PRD §8.3; #125 = the buy-day
eligibility promotion, 2026-07-25; #126 = the §4+§5.2 interaction study, 2026-07-26; #127 = the household FX asymmetry, 2026-07-26; #128 = the crypto sleeve, 2026-07-26; #129 = flows + the per-sleeve averaging fix, 2026-07-26; #130 = the F-gate study, 2026-07-26; #131–132 = the Danny sweep-3 studies (dual-VH marker · signal-density challenger), PRD §5n, 2026-08-13, both NULL same day; #133 = the bear-regime census + #134–137 the bear-audit fixes it proposed (134 partial-month defect · 135 re-entry divergence · 136 F-ratio · 137 §4 expectations), 2026-08-13; #138 = the leverage-drift / constant-debt gate re-run (owner-asked: "leverage grows when stocks drop"), 2026-08-13; #139 = the Flex LOT-detail parser fix (shares summed across tax lots; closes the SPECS §1.6 open check by removing the dependency instead of verifying it), 2026-08-13; #140–141 = the universe-coverage plans (volume band · discovery blind-spot audit), 2026-08-14; #142–144 = the 2026-08-14 Danny post (VH fidelity audit · blue-ribbon conjunction · hole-count-as-weakness re-cut), PRD §5o; #145 = the VH detector refinement session gated behind #142 (adoption on RETURNS, not match rate), 2026-08-14; #146 = the whale-precognition study (owner-asked after MRNA's +177% news gap: "can we detect whales buying before the news"), run + NULL same day 2026-08-20 — 🐳 lifts the 21d ≥10% up-gap rate only +19.7%/+7.6% (A/B) against its honest in-dip comparator, under the pre-registered +25% bar, and its direction skew beats plain dip-only at ≥5% gaps but NOT at the news-shaped ≥10%: the tag marks bounces, not news, BACKTEST_RESULTS §40; #147 = the crypto cycle sleeve (owner-asked: size 3x/2x leverage for a 4-year-cycle BTC accumulation mandate), run 2026-08-20 — leverage FAILED its pre-registered units gate 1/2 on every setting, perp funding-on-notional measured for the first time here (a 1x perp returns 0.21x where spot DCA returns 0.90x), and the cycle thesis is itself the argument against leverage since the mildest completed drawdown lands below every levered liquidation price; ships UNLEVERED as CRYPTO_SLEEVE.md (PROPOSED, owner line unsigned), BACKTEST_RESULTS §41; next free: #159). Same law as every §8.3 row: pre-registered gate,
info-only until promoted, null → closed honestly. #113–119 are
infrastructure — none is a signal, none consumes an R10 selection slot.
#120–123 are the §2 alpha program: their STUDIES are free, their
PROMOTIONS pay the normal R10 selection price like everything else.

| # | Item | Effort | Gate |
|---|---|---|---|
| 113 | ~~**Bars vault — data durability.**~~ — **SHIPPED 2026-09-11** (`homily_vault.py`, `vault/`, validate [80]; PRD §8.5 records the one deviation). Shape is **one frozen base per year + a self-contained monthly delta** (everything since the base), not twelve full snapshots: a full snapshot is ~23 MB and git never forgets a deleted file, so the row's literal wording would have grown the clone ~270 MB/yr and broken the cold start #115 depends on; base+delta costs ~23 MB/yr. Restore is the switch `HOMILY_BARS_SOURCE=vault` on `homily_data.fetch_series` — same contract, same `rng` windows, RAW bars bit-exact (every Yahoo price is an exact float32; stored at 9 significant digits, cast back on read), adjusted closes exact unless a dividend landed after the base (then rescaled by the measured factor, ~1e-7). The silent-rewrite detector compares the base's last 20 bars on every delta: a raw-close change (split, correction) re-vaults that name in full and prints ONE data-QA line in the digest that morning; a pure adj rescale is logged as a dividend, not a rewrite. First base: 199 symbols (held + watch + hand universe + proxies + universe.json + benchmarks/crypto + every committed harness's universe via `BACKTEST_UNIVERSES`), as-of 2026-09-11. The first drill FAILED honestly — a vault of "what the digest fetches" (179 names) could not reproduce `homily_core4_backtest`, whose engine-picked arms draw from UNIV_B names (SNAP, U, BYND, DKNG …) the daily run never touches; the registry + a reflective validate scan of every harness's ticker lists is the fix, and the drill was re-run from scratch. Original text: periodic (monthly, workflow-committed per R8) compressed snapshot of every universe name's raw + adjusted bars, so a Yahoo death or silent history rewrite can neither orphan the ledger nor un-reproduce a published backtest. Retention: last 4 snapshots + one frozen per year | S–M | **PASSED 2026-09-11** — `python homily_vault.py --drill`: throwaway copy of the repo, sockets disabled, `HOMILY_BARS_SOURCE=vault` → the full daily digest built and `homily_core4_backtest.py` produced output byte-identical to the same run against the live network. Re-run every July with the #115 cold-start drill |
| 114 | ~~**Fetch failover chain.**~~ — **SHIPPED 2026-09-11** (`homily_data.FALLBACKS`, validate [81]; PRD §8.5). Chain is **Yahoo → Nasdaq (api.nasdaq.com historical, US listings, ~10y, split-adjusted, no dividend adjustment) → vault (#113, any vaulted name, up to a month stale)**, consulted per symbol only after Yahoo hard-fails, first source that serves wins, source + as-of recorded per name. NOT Stooq: the row's planned alternate now answers with a JavaScript proof-of-work challenge instead of CSV, so #60's check had been silently dead — solving the challenge is anti-bot circumvention and was not built; Stooq is retired and #60's daily SPY agreement check now runs against the vault's frozen Yahoo tape instead. A breaker declares Yahoo down after 5 consecutive transport failures (never a 404) so an outage costs seconds, not 199 × 3 × 20 s. The digest prints one `📡 SOURCE` line naming counts, names, what each source means (adj = raw close on Nasdaq names; STALE as-of date on vault names) and #60's agreement tally vs the vault for every Nasdaq-served name; that day the digest sends but **no verdict-feeding state is written** — ledger, snapshot, refine-J, alerts, dashboard — because a foreign tape is not a reference row (R1). Honest limit: whether GitHub runner IPs reach api.nasdaq.com is unverified (it worked from the owner's machine); if they don't, the chain degrades to Yahoo → vault and the line says so. Original text: promote #60's Stooq cross-check from warn-only to an ordered fallback (Yahoo → alternate) used ONLY on hard fetch failure — never silent source mixing; the digest prints the source the day it isn't Yahoo, and #60's agreement check runs on every failover day | M | **PASSED 2026-09-11** — canned outage (validate [81], offline): Yahoo dead → Nasdaq/vault serve with the source line, breaker trips, 404-immune, disagreement warns never halts, no state on a foreign day. Live rehearsal in a throwaway copy with Yahoo pointed at a dead host: full digest in 25 s, 168 names via Nasdaq + 11 via vault, 102/102 Nasdaq closes agree with the vault's Yahoo tape, ledger/snapshot/dashboard/refine-J byte-unchanged, no alert |
| 115 | ~~**Cold-start runbook + yearly succession drill.**~~ — **BUILT + FIRST DRILL 2026-09-11** (`COLD_START.md`, validate [83]; PRD §8.5). Written FROM a drill, not before it: fresh clone → validate (2.9 s) → daily run with no secrets (16 s, digest printed) → buy-day sheet → gambit validate → vault restore drill (PASS from the clone). Four findings, each patched the same session: gambit's validate needs `pytest` (the one non-stdlib need, stated nowhere); a local daily run silently writes four state files an operator would commit (reset line added); no way to see a buy-day sheet except on the 1st of a month (`homily_buyday.py --rehearse` built — fetch-free, writes nothing — and its first cut skipped the 👁 fence and printed CYPH, fixed); the drill was once run against an uncommitted tree. [83] pins the doc to the tree: every workflow secret/variable is in its inventory, every script it names exists, the rehearsal flag is real, the Flex expiry matches §6, the drill log has a dated row. **Honest limit: the first runner was the author with full context, so this proves the mechanics, not the docs' sufficiency — the 2027-07 drill by a context-free session is the first real test** (protocol in COLD_START §10). Original text: from a fresh clone + secrets list to a verified daily run and one monthly buy-day sheet, no memory assumed. Drilled every July by a session with no prior context of this repo (new model preferred — that's the real test) | S build · S/yr | the drill itself; every failure patches the DOCS in the same session, never the drill-runner's memory — **first drill 2026-09-11 (author), next 2027-07 (context-free)** |
| 116 | **Complexity budget — the July prune.** — **MECHANICS BUILT 2026-09-11, first prune 2027-07** (`homily_budget.py`, `module_budget.json`, validate [85]; PRD §8.5). Live is DERIVED from the import graph (45 of 90 modules reach an entry point — including four harnesses `daily_run`/`homily_refine` import constants from, which therefore can never be archived); the other 45 are registered: 5 tools · 23 gates of record (re-run each July) · 3 pending dated reads (#24 2026-10-01; #79 + #105 ship-or-close by 2026-12-31) · **13 closed nulls, `archive_by 2027-07-31`** — [85] fails the build once one outlives that date, a pending read rots at 90 days past, or the count exceeds the cap (90, set 2026-09-11; raising it = edit + same-day §8.5 note naming #116). `python homily_budget.py` prints the census the July session prunes from. `gate` is a fourth status the row did not name (a PASSED harness is the artifact #40 reproduces from; archiving it would break the July re-run). Original text: rides #40: every module/harness must hold one of {live consumer · dated pending read · archive}. Closed-null harnesses move to `docs/archive/` with their BACKTEST_RESULTS pointer; the #73 digest line budget stays capped; net top-level module count may not grow year-over-year without a §8.5 note saying why | S/yr | docs-only gate: validate green, goldens untouched, every archived piece reachable via pointer — **first prune due 2027-07-31 (13 files); [85] enforces the date** |
| 117 | ~~**R-2029 verdict freeze.**~~ — **SHIPPED 2026-09-11** (`homily_verdict.py`, `verdict_freeze.json`, validate [82]; PRD §8.5). Pinned: sha256 of §3's R-2029 rule text (rule line through "demotion is not deletion"), of §4's R-2036 rule text (pinned with it — the 2036 collapse-and-no-re-benchmarking clause is the same rule and would otherwise be its one editable half), and of the SOURCE of the band method — #71 is not built yet but its method is committed as D-39's block bootstrap (`homily_bootstrap`: resample_indices · moic_of · block_moics · percentiles · paired_beats, BLOCK 6 · 10,000 · seed 39 · 5/25/50/75/95), so the pin is on those definitions, stricter than a file hash. Twelve fork clauses are stored verbatim and must stand in the file. Negative-tested in [82]: a one-word edit to the rule, a dropped clause and a moved band constant each fail; an edit outside the rule does not. Original text: turn §3's three-fork rule into a checked artifact before it can matter: the band method pinned to the committed #71 implementation (hash), the fork thresholds and the demote-to-discipline mechanics written into a validate case that fails if the wording drifts from this file | S | **PASSED 2026-09-11** — [82] fails the build on any drift; a deliberate change is `python homily_verdict.py --repin` AND a PRD §8.5 note dated the same day naming #117, both checked |
| 118 | **Platform-migration drills + the liveness watchdog.** — **(a)+(b) DRILLED 2026-09-11 in one real run** (`homily_deliver.py`, validate [84]; recipes in COLD_START §7; PRD §8.5): a macOS launchd agent (not GitHub) fired the daily job at its scheduled minute in a fresh clone, validate green, and the digest + 3 chart cards + 2 documents + the state-change alert were delivered through `HOMILY_DELIVERY=file:<dir>` — Telegram never touched — as one self-contained HTML bundle (`digest_2026-09-11.html`, 57 KB, charts inline as data-URI PNGs); the agent was then unloaded and its plist deleted, nothing left standing. The adapter sits behind the same three `send*` functions (dormant when the variable is unset; the workflow passes it as a repo variable). Email was NOT built: it needs a credential kept live, which this row's own gate forbids, and a synced folder already reaches a phone. Gambit's weekly send is an inline script in its workflow and is NOT behind this adapter (noted, not done). Original text: prove the two most likely platform deaths are ops: (a) delivery — digest to a second channel (email or file-drop) behind the same send interface; (b) scheduling — the daily run from a plain cron/launchd on any box. One drill each, adapters kept as dormant code paths. **(c) SHIPPED 2026-07-25 — out-of-GitHub liveness watchdog** (`HEALTHCHECK_URL_DAILY` / `HEALTHCHECK_URL_GAMBIT`, validate [68]): both CI jobs ping an external monitor after their commit/push step, plus an explicit `/fail` ping on a red run; the monitor alerts on the ping's ABSENCE. This closes the era's real ops risk — a **public** repo's scheduled workflows are auto-disabled after 60 days with no commits, that disable also kills `workflow_dispatch`, and a silently broken run is precisely what stops the daily push that resets the clock. So the two failure modes share one 60-day fuse, and the planning phase is when nobody is watching it burn. Explicitly NOT a keepalive commit: manufacturing activity to dodge the policy is a GitHub ToS violation (the popular keepalive action was taken down for it), and this repo's daily push is real state anyway | S–M | (a)/(b): each drill = one real end-to-end delivery/run via the alternate path, logged in §8.5; no standing infra, no new secrets kept live. **(c) amends that clause for itself and only itself** (§8.5, 2026-07-25): a watchdog that is not standing is not a watchdog, so (c) keeps one live secret per book and one external check. Its gate: validate [68] pins the wiring in both workflows (present · post-push · own URL per book · dark-if-unset · dispatch trigger intact · no manufactured commit), and each of those six pins was negative-tested at ship. Owner half, ONCE: create the two checks with cron+grace matching each job's cadence (daily is Mon–Fri — a 24h period false-alarms every weekend), set the secrets, and confirm the alert channel is not the same Telegram bot this repo owns |
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
| **2027-06-26** | **IBKR Flex token EXPIRES** (#32, set 2026-07-25 with ~1y max expiry). Rotate BEFORE this date: Performance & Reports → Flex Queries → Flex Web Service Configuration → Generate New Token (longest expiry, IP field blank — runners rotate IPs), then re-set `IBKR_FLEX_TOKEN`. Generating invalidates the old token, so secret and token must move together. **Why this earns a calendar row:** expiry is caught at `homily_flex.auto_sync`'s except and is deliberately non-fatal — CI stays GREEN, the #118(c) watchdog pings healthy, and the only signal is one `📒 book sync` line in Telegram. Nothing red ever appears while the book silently stops tracking reality |
| 2027-12 | R-2027 read (§1) |
| 2029-07, then yearly | R-2029 three-fork read (§3) |
| 2036-07 | R-2036 binding read (§4) |

Ten years from now the deliverable is not a cleverer signal. It is an
unbroken ledger, a scorecard someone can believe, and a system a
stranger could operate. Everything above serves that.
