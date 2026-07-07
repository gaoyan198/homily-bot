# DESIGNS — deep designs + extended idea bank

**Written 2026-07-06 (late) by the planning model, for the executing model.**
PRD §8 is the index; `SPECS.md` (overnight run) covers Week-1/Month-1 build
specs; this file covers (I) design decisions for the *hard* roadmap items,
(II) the extended idea bank #46–60, and (III) the execution handoff
protocol. Nothing here is implemented. Every item keeps the house rule:
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

Monthly replay over months with >5 ⭐ candidates on buy day. Compare:
(a) RS12 top-5 · (b) equal-split all · (c) random-5 — 1000 draws, giving a
*distribution*, not a strawman · (d) alphabetical top-5 — the accidental
current behaviour, which any change must also beat. Metrics: 12m forward
return and avg-cost (the system never sells; cost matters). **Adopt (a)
only if it beats random-5's median in ≥60% of draws AND beats (d).**
Expect a null result — momentum-ranking momentum-gated names is nearly
circular; the honest test is cheap and settles it.

### D-29 · Correlation / concentration lens (#29)

**Data.** 90 trading days of daily log returns per held name; pairs need
≥60 overlapping days (HK holidays) else the pair is excluded and the name
falls to "other".

**Clustering.** Threshold graph at ρ ≥ 0.60 → connected components (stdlib
BFS). Not hierarchical linkage — a component is explainable in one digest
line, which is the actual requirement.

**Labels.** Static `SECTOR` map committed next to holdings (12 lines of
maintenance, no API).

**Weights.** By position value once #27 lands; until then equal-weight
proxy with an explicit "assuming equal weights" caveat in the line.

**Triggers.** Top cluster >60% → one line. A ⭐ add inside the top cluster
→ one nudge line ("⭐ MU deepens the 68% semi cluster — non-cluster ⭐
first per PLAYBOOK §3"). Info-only forever unless a future gated study
promotes it. Validate: fixture returns with two planted blocks → exact
cluster recovery.

### D-31 · Buy-day copilot allocation algorithm (#31)

**Inputs.** `BUY_BUDGET_USD` (Actions repo *variable*), holdings v2
(shares + cost, via #27), today's ⭐ set (holdings + discovery), regime,
`SRS_COVERS_INDEX` config (PLAYBOOK §3.3: if SRS is funded and invested,
the cash DCA may go fully to stars).

**Algorithm.** budget → index leg (50%, or 0% if SRS_COVERS_INDEX) → star
leg equal-split (max 5 names; order: F:2+ first per PLAYBOOK §3.4, then
RS12 until #24 settles ranking) → per name: post-buy weight ≤10% of book
else cap and redistribute overflow to remaining stars → round DOWN to whole
shares; **HK names round to board lots** (static `LOTS` map committed —
board-lot sizes aren't key-free; 9992.HK lot size must be verified before
first use) → leftover cash printed. 🐻 regime: entire stock leg → index
per PLAYBOOK §4.6. ⚖️: normal buy day.

**Buy-day detection.** Not calendar math (US holidays, SGT offset): buy day
= first run of the month with no prior ledger rows that month — needs #13,
robust by construction, no holiday table.

**Output.** A `<pre>` block of order lines ("BUY 3 TSM @ mkt (~$1,302)"),
total deployed, leftover. Footer: *printed, never placed* — §7 stands.

### D-34/35/36 · Frontend architecture decisions

**F0 (#34).** `parse_mode=HTML`; escape `& < >` on every interpolated
string; legend + algo-health footer inside `<blockquote expandable>`;
keep the existing plain-text fallback path in `send()` (strip tags on 400).

**F1 (#35).** Minimal PNG writer: 8-byte signature + IHDR + IDAT (zlib,
filter 0 per scanline) + IEND; 24-bit RGB, no alpha (blend band colours
directly). Drawing primitives: hline/vline/rect/Bresenham line + a 5×7
bitmap font for digits and ~15 letters (~60 lines of data). Layout 900×500:
price panel (1y closes, add-zone band, POC/res lines) · right 200px
horizontal chip histogram · bottom 20px weekly-circle ribbon. Deterministic
output → pixel-hash test in validate. `sendPhoto` via hand-rolled
multipart/form-data (boundary + one file field; caption ≤1024 chars).

**F2 (#36).** Decision: **server-side static SVG, zero JavaScript.** One
self-contained `docs/dashboard.html` from a template string; per-holding
`<details>` cards; native SVG `<title>` tooltips. No client JS = renders
identically in Telegram's in-app browser, offline, and in 5 years.
`docs/snapshot.json` (#13) is the single data contract. Committed by the
workflow + sent via `sendDocument`.

### D-39 · Bootstrap CIs on THE test (#39)

Monthly return series (~60 obs) for strategy and DCA from
`homily_strategy_backtest.py`; circular block bootstrap, block length 6
(≈ regime half-year), 10,000 resamples; report MOIC 5/25/50/75/95th
percentiles for each arm plus P(strategy > QQQ DCA). Printed caveat, always:
*bootstrap cannot manufacture unseen regimes — these are within-window
uncertainty bands, not forecasts.*

---

## Part II — extended idea bank (#46–60)

Unvetted. Each carries its gate; none touches money before its gate passes.
Numbering continues PRD §8 (new proposals from later sessions start #61).

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
49. **Golden-file digest tests** (S) — fixture bars → exact expected digest
    text committed; validate diffs it every run. Refactors can no longer
    silently change a row. **Gate:** none (test infra). *Build this FIRST
    on execution days — it is the executing model's safety net.*
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
