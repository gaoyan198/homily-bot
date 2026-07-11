# DESIGNS — deep designs + extended idea bank

**Written 2026-07-06 (late) by the planning model, for the executing model.**
PRD §8 is the index; `SPECS.md` (overnight run) covers Week-1/Month-1 build
specs; this file covers (I) design decisions for the *hard* roadmap items,
(II) the extended idea bank #46–60, and (III) the execution handoff
protocol. Shipped/resolved designs move verbatim to
`docs/archive/DESIGNS-shipped.md` (#76) — a stub with the outcome stays
here. Every item keeps the house rule:
point-in-time backtest with the hype-2021 control before anything gates
money; info-only until promoted.

---

## Part I — deep designs for the hard items

### D-20 · Conviction-score backtest (#20)

**Replay protocol.** For each Friday f in 2021-07 → 2026-07 (weekly grid
cuts compute 5×, loses nothing at 6–12m horizons), for each name in the
universe, compute gates + score with `conviction(danny_signal(tk,
bars[:i]), bars[:i], spy[:i])` — the live functions, truncated bars, zero
new code paths to trust. Two universes: today's `UNIVERSE` (hindsight-
biased, label it) and the frozen hype-2021 control from
`homily_strategy_backtest.py`.

**Outputs.** (a) Decile table: *within-day cross-sectional* score deciles →
forward 126d/252d mean & median excess vs SPY (within-day assignment
controls for regime; pooled deciles would just rediscover "2023 was good").
(b) Tier table: CONVICTION / STARTER / fails → P(≥2× in 500 bars), P(≥5×),
P(−50% first). (c) The wreck list the gates passed.

**Statistical honesty.** Overlapping forward windows inflate significance —
report point estimates plus block-bootstrap 90% bands (reuse D-39
machinery); require ≥30 observations per decile before reading a row.

**Decision rule (pre-committed, so the result can't be argued with).**
Hold out 2024-07 → 2026-07. Adopt weight changes only if the OOS decile
ranking is monotone-ish (Spearman ρ ≥ 0.5) AND top-decile excess > 0.
Otherwise the digest footer changes to "score = shortlist, no measured
edge" — and that is a fine outcome; the gates alone may be the product.

**Pitfalls.** The `age` component reads `len(bars)` — in replay young names
correctly earn age points early (matches live behaviour). G1 $-volume is
nominal; 5y inflation drift acceptable. Delisted names still missing
(#45) — say so in the output header.

File: `homily_conviction_backtest.py` · Effort M–L · validate: replay
determinism test (same inputs → same table).

### D-21 · Refine-loop re-pointing (#21)

**Why.** `homily_refine.py` optimises hold-🔴/cut-⚪ Calmar — a strategy §1
retired. The circle's live job is gating composite states. Optimising the
wrong objective daily is worse than not optimising.

**New objective.** For param set p on a segment:
`J(p) = mean over basket[ mean fwd-60d excess of ⭐(p) days ] − λ·FB(p)`
where ⭐(p) = days the composite would print ACCUMULATE with circle params
p (recompute `homily_circle` inside `danny_signal`), excess is vs
*same-name* buy-and-hold over the same window (isolates timing skill from
name selection), and FB(p) = fraction of ⚪(p) days followed by ≥+15% in
60d — the false-block penalty, i.e. the PLTR-June failure class made a
first-class citizen of the objective.

**λ discipline.** λ = 0.5; sensitivity-print 0.25/0.5/1.0 and keep λ only
if the param *ranking* is stable across all three. Never tune λ on outcome.

**Sample-size diagnostic first.** ⭐ days are sparse (support proximity
required). Before committing: print pooled ⭐-day counts per walk-forward
fold. If pooled obs < 100, the objective is unstable — fall back to scoring
RED-regime days instead of ⭐ days (more obs, same spirit). This diagnostic
run is its own deliverable; do not skip to the objective.

**Migration.** 30 days parallel: log both objectives, champion still
Calmar-selected; flip after if no adoption-flapping. `homily_champion.json`
gains `"objective"` field; log gains columns (append, never rewrite
history). Same walk-forward split, same +10% adoption margin, same tiny
grid — the anti-overfit architecture is the part that already works.

### D-24 · ⭐ overflow ranking (#24)

**RUN 2026-07-10, archived** → `docs/archive/DESIGNS-shipped.md#d-24`. rs12-top3 passed pre-registered checks; the live promotion protocol is SPECS §2·24.

### D-29 · Correlation / concentration lens (#29)

**Shipped 2026-07-11** (validate [36]), archived → `docs/archive/DESIGNS-shipped.md#d-29`.

### D-31 · Buy-day copilot allocation algorithm (#31)

**Shipped 2026-07-10** (validate [27]; EXECUTION R12 superseded the HK board-lot sketch), archived → `docs/archive/DESIGNS-shipped.md#d-31`.

### D-34/35/36 · Frontend architecture decisions

**All three shipped** (gates [20]/[28]/[33]), archived → `docs/archive/DESIGNS-shipped.md#d-34-35-36`.

### D-39 · Bootstrap CIs on THE test (#39)

Monthly return series (~60 obs) for strategy and DCA from
`homily_strategy_backtest.py`; circular block bootstrap, block length 6
(≈ regime half-year), 10,000 resamples; report MOIC 5/25/50/75/95th
percentiles for each arm plus P(strategy > QQQ DCA). Printed caveat, always:
*bootstrap cannot manufacture unseen regimes — these are within-window
uncertainty bands, not forecasts.*

### D-63 · Bear-regime rethink — decompose the 🐻 sell step (#63)

**RESOLVED 2026-07-10** (PRD §5i, BACKTEST_RESULTS §2; numbers contradicted the hypothesis and shipped anyway, rule 6), archived → `docs/archive/DESIGNS-shipped.md#d-63`.

### D-65 · Universe construction — from hand-picked list to mechanical screen (#65)

**Owner-requested 2026-07-10** ("think about how you are screening for
Universe").

**What exists today.** `UNIVERSE` in `daily_run.py` is a hand-curated
~60-name dict grown by conversation (megacaps, semis, growth software,
diversifiers, HK/SG, crypto ETFs, mid-caps). Names enter by owner/model
taste — `origin: owner-request` in #64's terms — and never mechanically
leave. Three costs: (1) the live scorecard inherits the selection bias
(#64 makes it measurable, not gone); (2) backtest UNIV_A is
hindsight-flattered and even the "honest" UNIV_B control is itself a
hand-built list; (3) selection is the biggest measured lever (R2), yet a
name we never screen can never ⭐ — the multi-bagger hunt is capped by
where we already looked.

**Design constraints.** Key-free, stdlib, CI-friendly (≤ ~100 deep fetches
per daily run), and NO free point-in-time constituent source exists (#45
stays blocked) — so survivorship-free construction is impossible; say so
rather than pretend.

**Pipeline — three mechanical layers, refreshed quarterly (rides #44):**

* **L0 base listing (free, mechanical):** the NASDAQ Trader symbol
  directory (`nasdaqlisted.txt` + `otherlisted.txt`, published daily,
  key-free) = every US-listed security (~11k rows). Drop test issues,
  warrants/units/rights/preferred, secondary share classes, and ETFs
  (except the index/crypto ETFs the owner holds — those are
  `owner-request` anyway).
* **L1 hard gates** (quarterly, from bulk EOD — Stooq bulk files or Yahoo
  batched over several CI nights): price ≥ $5 · median 60d dollar-volume
  ≥ $50M · ≥130 bars listed (younger-but-liquid tagged `young`; the 🚀
  tier's own 260-bar gate G5 is unchanged) · primary exchange
  NYSE/NASDAQ/AMEX.
* **L2 capacity cut:** rank L1 survivors by 60d dollar-volume; keep top
  ~120 + every current holding + every name that passed all 🚀 gates in
  the last two quarters (stickiness — a winner doesn't fall off the list
  the quarter it cools). This list ships as committed `universe.json`
  (`symbol, origin, since, gate values`) — provenance lives where the
  ledger (#13/#64) can log it.

**Owner adds stay possible** — tagged `origin: owner-request`, including
ALL non-US names (HK/SG/KR have no equivalent free master list;
international inclusion stays discretionary and labelled as such).

**Diff discipline.** The refresh never silently swaps the list: #44's
quarterly GitHub issue shows adds/drops WITH their gate values; a drop is
actioned only after failing L1 two consecutive quarters (whipsaw guard).

**Gate (pre-committed).** One shadow quarter: the mechanical list runs in
parallel (ledger rows tagged `shadow-screen`, no digest surface). Adopt as
the live screen universe only if it (a) retains ≥90% of the names the hand
list actually surfaced (⭐/🔵/🚀) that quarter — it must not LOSE signal —
and (b) surfaces ≥1 legitimate setup the hand list missed. Either way #14
splits the scorecard by origin from day 1; if `screen` and `owner-request`
rows diverge materially, that decides the follow-through.

**Backtest-universe honesty (feeds #40).** UNIV_B stays frozen (it is the
committed control), but the next July re-test adds a third universe:
*mechanical-2021* = top-100 by 2021-07 dollar-volume among still-fetchable
names — rule-stated instead of taste-stated. Still survivor-limited (#45),
but removes hand-picking from the control's construction.

File: `homily_universe.py` + `universe.json` · Effort L (the bulk-EOD
quarterly job is the work) · until it ships, #64 labels + #44 hygiene issue
are the cheap forward steps and are NOT blocked on this.

### D-66 · Right-stock discipline — sticky quality tier, 💎 quality dips, thesis-break veto (#66)

**Owner-requested 2026-07-10**, quoting Danny: *"Successful investing is
NEVER about multiple indicators… It's about picking the right stocks,
aggressively adding to them during pullbacks, and holding patiently."* The
owner's three challenges: (1) how do we know we're picking RIGHT stocks;
(2) sizing up the WRONG stock during a pullback is catastrophic — what
reduces that; (3) do we detect pullbacks in great stocks, given our
indicators use price as strength so a pulling-back stock drifts to ⚪.

**Honest inventory of what already exists.**

* *Right-stock side:* the 🚀 gates + 0–100 score (unvalidated until #20
  runs — the PRD itself says "shortlist, not an edge"); `homily_fund.py`
  F:n/3 (3 coarse checks, info-only, US-only); the RS12 ≥ SPY+20 gate.
  Which competing ⭐ gets the money is effectively alphabetical until #24.
  §8.0 already names selection (R2) the biggest signal-side lever.
* *Pullback-in-great-stock side:* better covered than challenge (3)
  assumes — ⭐ ACCUMULATE **is by construction a pullback state** (weekly
  dip to a chip shelf *inside* an intact monthly uptrend), plus 🟡, 🔵 and
  the gated WHALE-DIP tier. The composite never punishes a dip per se; it
  punishes a broken monthly trend.
* *The two real holes, which are the same hole:*
  1. A pullback deep enough to break monthly EMA10 parks the name in ⚪
     and pauses adds **regardless of business quality** — the PLTR-June
     false-block class (#21 attacks the tape side of this; nothing attacks
     the quality side). NVDA-2022 (−60%, business intact) and PTON-2022
     (−60%, business broken) print the *same* ⚪ row apart from a small
     F-tag.
  2. Conversely the aggressive dip-add paths (🎯-on-🟡, ⚪+🎯+🐳
     WHALE-DIP, #50 tranches if adopted) have **no fundamental veto** — a
     2021-wreck falling knife with whale footprints can still draw an add.
     Caps (2%/5%/10%) bound the damage per add; nothing stops the add.

  Both failure modes are one missing fact: **a per-name business-quality
  judgment that does not move with the tape.** Everything price-derived
  collapses in a drawdown by definition; quality must come from the slow
  layer or it is just momentum wearing a suit.

**Design — three parts, one slow input.**

* **(a) Sticky quality tier Q (quarterly).** Extend `homily_fund.py` from
  3 checks to a small scored set, EDGAR-only, key-free: revenue growth
  (level + direction), profitability (NI>0 or OCF>0, margin direction),
  FCF sign, dilution rate. Plus exactly ONE price input — 3y RS vs SPY —
  as the "market has voted for years" check, never a shorter window.
  Output: **Q1** compounder-grade · **Q2** unproven · **Q3**
  broken-or-unknown. Computed at quarterly refresh (rides #44/#65's
  cadence), committed like the fund cache, and *frozen between refreshes* —
  no tape feedback loop, that is the whole point. Non-US names print `Q:—`
  honestly (same stance as F:—).
* **(b) 💎 quality-dip row (info-only until gated).** Fires when: Q1 ·
  state ⚪ *purely from trend break* (weekly structure not WHITE-collapsed)
  · drawdown within the name's own historical recovery envelope · no fresh
  fundamental downgrade at the last refresh. Digest prints "💎 NVDA — ⚪ by
  tape, business intact (Q1, F:3/3) — quality dip, shelf 152" instead of
  silently parking it. This answers challenge (3) for the deep-pullback
  case; ⭐ already answers the shallow one.
* **(c) Thesis-break veto (the wrong-stock damage control).** The
  aggressive add paths — 🎯-on-🟡, WHALE-DIP, and #50 tranches if adopted —
  require Q ≥ Q2 AND no fresh downgrade (revenue growth flipped negative,
  dilution spike, F-score −2 vs prior quarter). A veto ONLY: it can block
  an add, never create one, so it cannot add a new way to lose. Caps
  unchanged. This answers challenge (2): the machinery that sizes up into
  weakness refuses to run on names whose business broke.

**Gate (pre-committed, the replay is the work).** Point-in-time replay on
UNIV_A + the frozen UNIV_B 2021-hype control, filings as-of date only:

1. **Wreck-separation test (must pass first):** does Q, computed from
   then-available filings, separate the 2021 wreck list (PTON ZM DOCU
   class) from the later-recovered greats (NVDA META 2022 class)? Report
   the tier × forward-24m table. If Q cannot separate them OOS, the tier
   prints as a label but **everything downstream stays dead** — close
   honestly per Part III rule 6.
2. **💎 event study:** forward 12m of quality-dip days vs (i) unfiltered ⚪
   dips and (ii) same-budget DCA. 💎 becomes a *buyable* state only if it
   beats both; otherwise it ships info-only forever (still useful: it
   changes what the human reads during the next NVDA-2022).
3. **Veto standard (weaker, because a veto only reduces action):** on the
   replay, count wreck-adds blocked vs winner-adds falsely blocked; ship if
   clearly net-positive. The PLTR-June case must NOT be blocked (Q was
   fine) — that is the regression test for over-blocking.

**Interlocks.** #20 stays the referee for the 🚀 score — this item does not
touch that rubric. #21's false-block penalty is the tape-side twin of (b).
#24's ranking test gains a fourth arm: Q-tier as ⭐ tie-break. #51's ⚪
time-stop study gets a Q split — P(recover | weeks-in-⚪, Q) is likely that
study's strongest cut, and the data answer to "hold the dip or cut it".
#50 is gated on (c) before any tranche automation. Danny's lag point from
§6.4 stands: fundamentals gate the *universe and the holding decision*,
the tape still gates *money flow* — Q never times an entry.

File: `homily_fund.py` extension + `homily_quality_backtest.py` · Effort
M–L (the point-in-time filings replay is the work; the digest wiring is
trivial) · Cheap forward step NOT blocked on the gate: print `Q:` next to
`F:` as a label from day 1 — labels are free, promotions are gated.

### D-67 · Hard-rule provenance audit — price the declared constants (#67)

**Owner-requested 2026-07-10** ("how did we determine that a stock going
to 10% means we stop adding? if it fits our screen why can't we add to
these winning stocks? any smart way to determine these hard rules instead
of gut feeling?").

**Why (audit finding).** The 10%/name add-cap (PLAYBOOK §3.4) appears
fully formed in the first PLAYBOOK commit (581e82d) with no backtest
behind it — and it *contradicts* the adopted evidence: the emergent
backtest that §5g crowned "THIS is the method the digest encodes" never
enforces any cap. Its winning 2.10× book let PLTR grow to ~30% of book
with adds continuing the whole way (top-4 62%, peak 69%). The live
routine is therefore more conservative than the tested one — plausibly
right as insurance against the gap-down no trend gate can see, but the
premium has never been priced. The same audit, applied to every hard
constant in the system, sorts them into three provenance classes:

| Constant | Where | Provenance | Owner study |
|---|---|---|---|
| 10m SMA regime, both indices, monthly close | §4 | tested (30y `homily_regime_backtest.py`; D-63 decomposition) | #63 done |
| no adds while ⚪ | §1/§2 | tested implicitly (emergent adds only on ⭐/🔵) | — |
| no ⭐ → full amount to index | §3.5 | tested (cited in §3.5) | — |
| never-sell / hold-through | §3/§5 | tested (THE test · emergent · multiwindow) | #40 yearly |
| 🐳 WHALE-DIP tier exists | §3.6b | tested + gated (§5h) | — |
| **10%/name add-cap** | §3.4 | **declared; contradicts the tested arm** | **this item** |
| **10% Bucket-B "earned" threshold** | §1 | declared (same digit reused) | this item, sensitivity |
| **≤2% whale-dip cap** | §3.6b | declared ("edge is modest" instinct) | this item |
| **max 5 ⭐ names/month** | §3.4 | declared | this item |
| 50/50 A-vs-stock split | §7 | declared, deliberately behavioural | this item, info-only |
| ⚪ 12w + F:0–1 → sell half | §5.2 | declared | #51 (queued) |
| thirds-over-3-months re-entry | §4.7 | declared | D-63 modes |
| satellites ≤10% bear trim | §4.3b | declared | D-63 |
| margin zero | §6 | ruin-avoidance — not tunable, no study moves it | excluded by design |
| F thresholds (rev >10%, dil <12%) | `homily_fund.py` | declared, info-only | #66 Q-tier absorbs |
| score <60 → no capital | HOW_IT_WORKS | declared | #20 (referee) |

**The method (the owner's "smart way").** A declared rule is insurance.
Price it like insurance: **premium** = what the rule costs on realized
paths (multiwindow, both universes); **payout** = what it saves on the
paths it exists for (wreck scenarios). A sweep that only maximises MOIC
would delete every safety rule, because in both our universes this
cycle's mega-winner won — that is the hindsight trap §8.0 warns about,
so the sweep alone is never the decision rule here.

**Step 1 — cap sweep (the premium).** `homily_cap_backtest.py`: the
emergent arm + `add_cap ∈ {5, 10, 15, 20, 25, ∞}%` × two treatments of
skipped cash {redistribute to remaining ⭐ names, send to index core}.
Weight checked on add day only — the cap gates adds, never forces sells
(§5.1's earned-pass survives). Replay over the multiwindow WINDOWS,
universes A and B. Report MOIC / TWR / MaxDD / peak-top1 / peak-top4 per
cell, plus **cap-binding frequency** (months a skip actually happened) —
without it the sweep is unreadable, since binding depends on book size
vs monthly flow. Judge on B.

**Step 2 — wreck pricing (the payout).** Two probes:
  a. *natural:* per cap level on universe B, each book's damage from its
     worst held name. Hypothesis: wrecks lose ⭐ long before they reach
     10%, so the cap binds only on eventual winners — if the replay
     shows exactly that, it IS the finding (the ⭐ gate, not the cap,
     contains wrecks).
  b. *synthetic:* at each book's peak-top1 date, gap the top name −80%
     overnight, no recovery; rerun per cap level. This is the payout
     table — what 10% vs ∞ buys when the biggest name is the next LCID
     (or a fraud print the trend gate cannot front-run).

**Step 3 — Bucket-B threshold sensitivity.** The same 10% digit defines
"earned core" (§1), which flips the 🐻 sell exemption and trim rule 1.
Reuse D-63's Bucket-B proxy row with the threshold swept {8, 10, 15}% —
a sensitivity table, never a headline.

**Step 4 — whale 2% from dispersion, not gut.** From the
`homily_whale_backtest.py` episode returns: per-episode fwd60
distribution → cap sized so a 5th-percentile episode costs ≤0.5% of
book. If the derived figure lands near 2%, the rule graduates from gut
to derived; if far, the derived number is the proposal.

**Step 5 — max-5 and the split.** Max ⭐ names swept {3, 5, 8, ∞} in the
same harness (expect ~null per §5g's sizing result; cheap to check
honestly). The 50/50 split is NOT optimised — §7 defines it as the split
you can hold through a bear — but print the 30/50/70 stock-half frontier
per universe so the owner picks with a number instead of a feeling.
Info-only forever.

**Decision rule (pre-committed).**
- The add-cap moves ONLY if, on universe B, an alternative ties-or-beats
  the 10% arm's MOIC in a majority of windows AND its synthetic-shock
  MaxDD stays within 5 pts of the 10% arm. Expected outcome: uncapped
  wins realized paths (PLTR did exactly this in-sample) but loses the
  shock table — then the cap STAYS and PLAYBOOK §3.4 gains one sentence
  quoting its measured premium ("this cap cost ~X pts/yr in the tested
  windows; it exists for the gap-down the trend gate can't see"). The
  question closes with a number either way.
- If Step 2a shows the cap binds only on eventual winners AND the shock
  payout is small, the cap may move UP (15/20%) — never OFF: ∞ is not
  adoptable from two universes that both contain this cycle's
  mega-winner.
- Whale cap: adopt the derived number iff it lands in [1%, 4%]; outside
  that band keep 2% and note the estimate's fragility.
- Any change syncs PLAYBOOK + HOW_IT_WORKS + the #31 copilot constant +
  BACKTEST_RESULTS in the same commit; §8.0's one-live-change / 90-day
  spacing stands.

**Pitfalls.** Universe A is hindsight — upper bound, never verdict. A
per-name cap is a weak proxy for cluster exposure (today's book is one
AI trade wearing 15 tickers) — #29 is the real control; note the
interplay, don't conflate them. Synthetic −80% is a modelling choice —
label it as such and show −50/−80/−95 so the conclusion isn't an
artifact of one number. Part III rule 6: if the numbers say the
insurance is free (uncapped ≈ capped), ship that null — it means the ⭐
gate was doing the work all along, which is itself the answer.

**Interlocks.** #27/#31 consume whatever cap constant wins (it must live
in one place, imported everywhere). #29 is the successor risk control if
the cap ever relaxes. #51 owns the 12w rule, D-63 the bear constants,
#20 the score-60 line — the registry above is the map of who owns what.
The registry ships as a new "rule provenance" section in
BACKTEST_RESULTS.md the day the study runs; PLAYBOOK footnotes land only
as each owner study concludes (Part III rule 5).

File: `homily_cap_backtest.py` (+ an episode-dispersion block in
`homily_whale_backtest.py`) · Effort M · validate: uncapped arm must
reproduce the committed emergent numbers (regression, same pattern as
D-63 mode (b)).

---

## Part II — extended idea bank (#46–60)

Unvetted. Each carries its gate; none touches money before its gate passes.
Numbering continues PRD §8 (#61–82 taken — see PRD §8.3 index; #68–75
assigned 2026-07-11 in PRD §8 phases; #77–82 = Danny latest-posts review,
PRD §5k, full rows in the §8.3 table; new proposals start #83).

46. **Turnover-adaptive chip decay** (M) — replace the fixed 60d half-life
    in `homily_chips.py` with decay scaled by relative volume (v / avg50v):
    heavy-volume days consume more "chip age" — closer to how real chip
    models decay by turnover against float. **Gate:** shelf hold-rate (#47
    metric) must beat fixed-HL out-of-sample; else keep fixed and close.
47. **Shelf hold-rate statistic** (M) — for each historical *touch* of a
    top-2 support shelf (first close within 2% above it after ≥10 days
    away), measure P(+5% before −5%). Print per name: "shelf held 7/9
    touches". Turns the add-zone from an assertion into a measured
    frequency. **Gate:** it is itself an event study; print only with ≥8
    touches; info-only tag.
48. **Ancient-shelf overlay** (S–M) — a second chip profile at 240d
    half-life exposes multi-year accumulation shelves the 60d profile
    forgets; print only when an ancient shelf sits ≤10% below price
    ("deep shelf 152 · 2y"). **Gate:** bounce event-study, ancient vs
    recent shelves.
49. ~~**Golden-file digest tests**~~ (S) — **shipped 2026-07-07** (the goldens themselves); full text → `docs/archive/DESIGNS-shipped.md#idea-49`
50. **Staged-add tranches** (M) — Danny adds aggressively as dips deepen.
    Backtest: split the monthly star-budget into thirds at shelf / −7% /
    −14% (unfilled tranches roll to index next month) vs single add.
    **Gate:** avg-cost + MOIC vs single-add and DCA, both universes;
    complexity adopted only on a clear win.
51. **CAUTION time-stop study** (M) — empirical distribution of ⚪ spell
    durations and outcomes: P(recover to prior high | weeks in ⚪, F-tag).
    Calibrates PLAYBOOK §5.2's 12-week rule with data instead of instinct.
    **Gate:** the study; PLAYBOOK edited only after.
52. **Inverse-vol sizing within stars** (S–M) — equal-split gives a 60%-vol
    name and a 25%-vol name equal dollars. Test 1/σ₆₀ weights vs equal.
    **Gate:** THE-test rerun; adopt only if MOIC ties-or-beats AND MaxDD
    improves. (§5g found sizing didn't matter — expect a null; it's cheap
    to check honestly.)
53. **SGD lens** (S) — monthly line: book return in SGD, USDSGD 12m trend
    (`SGD=X`). The investor's liabilities are SGD; the book is USD.
    Info-only. **Gate:** none.
54. **Weekly diff report** (S; needs #13) — "what changed this week":
    state transitions, score moves ≥10, new/lost shelves, cluster drift.
    Pure ledger diff, feeds the Sunday edition (#33).
55. **Breadth cross-check** (S) — equal-weight ETF (RSP) monthly-SMA
    agreement with the SPY/QQQ regime; disagreement prints a "narrow tape"
    note. **Gate:** 20y event check that narrow-tape months actually
    underperform; drop the idea if not.
56. **AI analyst memo** (M, meta) — a weekly scheduled cloud agent (same
    mechanism as tonight's run) reads `snapshot.json` + ledger and opens a
    10-line memo PR: anomalies, stale flags, data-QA failures, unreconciled
    PRD claims. Process QA only — it never emits signals. **Gate:** 4-week
    trial; keep only if it catches ≥1 real issue.
57. **中文 digest toggle** (S) — `DIGEST_LANG=zh` renders states and labels
    in Chinese (筹码 / 主力 / 缩量 / 星标加仓). The source methodology is
    Chinese; some terms are simply more precise in the original. **Gate:**
    none (presentation).
58. **Behaviour-gap tracker** (M; needs #13 + #27) — a shadow portfolio
    that followed PLAYBOOK perfectly from 2026-07 vs the actual IBKR book;
    the delta, printed quarterly, is the measured cost of hesitation and
    deviation. The most brutally honest metric this system could own —
    PLAYBOOK §8 says discipline dominates; this prices it. **Gate:** none
    (measurement).
59. **Flash-crash pre-script** (S) — SPY 5d return < −7% → digest prepends
    the pre-written note: the monthly signal will lag by design; sizing is
    the protection; do nothing rash (PLAYBOOK §4 "what the signal cannot
    do"). Psychology aid, info-only. **Gate:** none.
60. **Data-QA cross-check** (S; feeds #17) — daily asserts per name: last
    bar ≤3 business days old, close within 2% of Stooq's, volume > 0;
    failure → "data suspect" tag that suppresses levels (same mechanism as
    #19) but keeps the state row. **Gate:** validate tests.

---

## Part III — execution handoff protocol (for the executing model)

1. **One item per session**, in PRD §8.1 order. Read the item's `SPECS.md`
   section (if present) else its Part I design here; restate the item's
   gate in your own words *before* writing code.
2. **Build #49 (golden-file digest test) first** if the session touches
   anything the digest prints — it is the safety net for every later item.
3. Guardrails: stdlib only; no new secrets; workflow edits only where the
   item says; `python homily_validate.py` green before every commit; match
   the repo's comment/docstring voice.
4. Every commit message: what shipped + gate status (PASSED / info-only /
   n-a). If the digest changed, add the honesty line to README in the same
   commit.
5. **Never promote info-only → money-gating in the same session as the
   build.** Promotion is its own reviewed change after the gate's backtest
   is in the repo. (The #12 whale pattern: tag first, gate, then tier.)
6. If a backtest contradicts the plan's expectation, ship the honest number
   and stop — do not tune until it agrees. A null result closed cleanly is
   a successful session.
