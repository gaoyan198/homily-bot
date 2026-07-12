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

### D-83 · Danny-style chart board — dashboard v2 (#83)

**Owner-requested 2026-07-12** ("the dashboard looks like trash and I
can't even read it properly — build a proper UI that mimics the charts
Danny always shows in his X posts"). Mockup built the same day from live
engine outputs and approved as the visual target: **`docs/mockup-83.html`**
(three cards — NVDA ⭐ / TSLA ⚪🐳 / SHOP 🔵; delete the file in the
commit that ships #83, per §9.3 "delete, don't accrete").

**Why the current dashboard fails.** `_card_svg` draws a 640×150 band of
levels plus a sparkline of LEDGER closes — and the ledger is days old, so
every card renders as an empty rectangle with an apology. No candles, no
price history, no chip histogram, no VH zone: the board speaks a
different visual language from the methodology it reports, which is
stated entirely in Danny/Homily chart terms (PRD §2, §5b).

**The card (one per name; all elements are frozen-engine outputs):**

1. **~6 months of daily candlesticks** (VIEW=120 bars), coloured by
   `homily_danny.daily_candle()` on close prefixes — **red = bullish,
   yellow = bearish, gray = neutral**. This is Danny's colour language,
   the inverse of Western charts; the page pins a legend at the top for
   exactly this reason and the footer says it again.
2. **Right-hand chip histogram** — `homily_png._display_bins()` (engine
   constants NBINS/HALF_LIFE), split at last close: in-profit teal below,
   trapped slate above, POC bin emphasized orange. POC + top-1
   support/resistance as dashed lines; labels live on a right-hand
   **collision-resolved label rail** (level labels sorted by y and nudged
   ≥13px apart; grid ticks yield to level labels within 12px — the #1
   readability defect of hand-placed labels).
3. **Volatility-hole zone** — `find_hole()`: translucent violet band from
   formation bar to the right edge, dashed boundaries, status label
   ("vh breakout ↑" / "vh breakdown ↓" / "vh zone").
4. **Add-zone band** — translucent teal across the plot with an
   `add lo–hi` rail label (whole numbers ≥100).
5. **52-week circle ribbon** along the bottom — `_ribbon_circles()`
   blocks (RED/AMBER/WHITE; WHITE at reduced opacity), captioned
   "wk circle · RED {n}w · med run 8w" (#82's stat).
6. **Facts chips row** (HTML, above the SVG): state pill · close · add
   zone · POC · % chips in profit · dip counter `dip d{n} (med 4d · p90
   22d)` (#78) · VH status · 🐳 · RS12 · conv · F-tag · book% + cap note
   (the position-aware fields stay).

**Architecture decisions.**

* **Bars arrive in-memory:** `write_dashboard(..., bars_map=…)` called
  from `daily_run` (which already fetched every name's bars).
  `docs/snapshot.json` does NOT grow a bars section — it is a committed
  artifact under the #75 schema contract and 68×500 bars would bloat it.
  `render()` stays a pure function — (snapshot, ledger rows, refine rows,
  bars_map) → HTML — so determinism check [33] extends with fixture bars.
* **Zero-JS, self-contained, dark** (D-36 stands). Native `<title>`
  tooltips only; the consumer is Telegram's in-app browser = touch, so
  nothing may depend on hover — every number a tooltip would carry is
  printed on the label rail or in the chips row. Dark-only is deliberate
  (the chart language is a dark-terminal idiom), not an omission.
* **Size budget:** cards for HELD names + today's actionable set (⭐/🔵/🎯
  in discovery) only, cap ~20 cards; discovery stays a table; the ledger
  heatmap, alerts timeline and refine chart sections remain below the
  cards. Candles are grouped per colour — one wick `<path>` + one body
  `<g>` per colour, ≈6 elements per card, never one element per candle.
  Assert total ≤300 KB in validate (the nightly commit must stay
  reviewable, R8).
* **Palette is normative** (validated against the dataviz six checks on
  the dark surface, 2026-07-12): bull `#e5484d` · bear `#b8890d` · profit
  `#25a897` · trapped `#6d83d1` · POC `#d47114` · VH `#8b7ff5` · surface
  `#0c1017` · panel `#111722` · ink `#dde3ee` · muted `#7e8798`. Reuse
  these hexes; don't re-derive.
* **Engine freeze respected:** reads `daily_candle` / `homily_circle` /
  `find_hole` outputs and homily_png's existing display helpers
  (`_display_bins`, `_ribbon_circles` — homily_png is NOT frozen; share
  the helpers, don't duplicate them). `_card_svg` and the ledger-close
  sparkline are deleted (superseded — the candles ARE the price history;
  ledger closes remain in the heatmap).

**Explicitly NOT in this item:** price targets or measured moves (PRD §5k
rejected them), client JS, external assets, new deps/secrets, any change
to what the digest prints (dashboard-only), any signal/level/state
computation change anywhere. Footer keeps the §2 honesty constraints
verbatim: approximation of documented behaviour, not Danny's or Homily's
formulas; red-bullish colour convention restated.

**Search & distribution (added 2026-07-12, owner request: "if I want to
analyse any stock I should be able to search it and get the Homily
chart").**

* **Board scope grows to ALL screened names** (~68: universe + holdings +
  watch), one card each — not just held+actionable. Search covers what the
  system screens; arbitrary out-of-universe symbols are #84's CLI job.
* **Search mechanics, progressive enhancement:** baseline = a
  state-coloured **ticker-chip index** at the top (`<a href="#NVDA">` per
  card — zero-JS, works in any renderer, plus the browser's find-in-page).
  Enhancement = a sticky filter `<input>` with **≤20 lines of inline
  vanilla JS** (prefix match on `data-tk`, hides non-matching cards and
  chips; a no-hit hint points at the #84 CLI and at adding the name to
  WATCH). This is a **deliberate, recorded relaxation of D-36's zero-JS
  rule**: the rule's actual goals — one self-contained file, no external
  assets, offline, no hosting, renders identically in five years — all
  still hold; the JS is optional sugar and the page is fully usable
  without it. The self-containment validate check gains one assert: no
  external `script src` (inline only).
* **Distribution split (the size problem, solved by not committing it):**
  ~68 cards × ~20 KB ≈ 1.4 MB — fine to *send*, wrong to *commit* (≈350
  MB/yr of git history at daily cadence). So: `docs/dashboard.html`
  (committed, workflow git-add unchanged) stays the SMALL board — held +
  actionable, ≤300 KB budget as above — while the FULL board is generated
  each night and delivered via `sendDocument` only; Telegram chat history
  is its archive, and `python3 homily_dashboard.py --full` regenerates it
  locally on demand. R8 unaffected (sent-not-committed artifacts don't
  enter the git-add list).
* **Reading manual:** `HOW_TO_READ.md` (top-level, registered in PRD §9.3)
  teaches the card element-by-element with the three mockup cards as
  worked examples; ships with the plan, updated if the build diverges.

**Gate (presentation-only):** deterministic render on fixture
bars+snapshot+ledger (extends [33]) · self-containment assert + inline-
script-only assert · committed-board ≤300 KB budget assert · digest
goldens untouched. Info-only by definition.

File: `homily_dashboard.py` rewrite + the `daily_run.py` call-site +
validate fixtures · Effort M–L (search/full-board adds breadth, not
depth — same card renderer) · one session; **#84 (any-ticker CLI) is its
own follow-up session reusing the renderer** (spec in SPECS §2).

### D-86 · Dip war-chest backtest (#86)

**Owner instinct, 2026-07-12** (verbatim intent): Danny doesn't DCA — he
holds ammunition and "FOMOs in" when whales offer a discount; monthly
DCA leaves no money for dips. Three of our own measurements point the
other way and are the NULL HYPOTHESIS this study must overturn, not
ignore: per-name ⭐-waiting lost 1–13% of avg cost to immediate DCA
(§5f); ~52–54% of ⚪-blocked days on the momentum basket ran +15% within
60d (BACKTEST_RESULTS §13 — the cost of sitting out); whale-dip episodes
carry a p5 of −31.7% (§12). The study exists to give the instinct one
honest, pre-registered shot — and to end the debate either way.

**Protocol.** Extend `homily_strategy_backtest.py`'s monthly loop with a
reserve arm: each month the stock half splits — (1−f) deploys per the
live protocol (rs12-top3 since 2026-07-12; model both pre/post rules),
f accrues to a cash reserve. The reserve deploys, whole, at the FIRST
qualifying event: a screened name's fresh ⭐ transition (not a
continuing ⭐), a 🔵 fire, a ⚪+🎯+🐳 whale-dip (≤2% cap still binds), or
🟡+🎯. Unspent reserve older than k months sweeps to the index (the §3.5
lesson as a backstop, not a veto). Grid: f ∈ {25%, 50%}, k ∈ {2, 3, 6}.
Point-in-time engines on prefixes, both universes, the §3 multiwindow
harness (all ≥5y windows since 2015), idx-fallback baseline = the
faithful committed protocol. 10 bps costs, same as THE test.

**Pre-registered decision rule (frozen here, before any run):** a (f,k)
cell is adoptable ONLY if, versus the idx-fallback baseline, it (a) wins
MOIC on ≥2 of the 3 construction-honest windows (2020→2025, 2021→2026,
2016→2026), (b) keeps MaxDD within +5 pts, and (c) is not behind BOTH
indexes in any straddle window where the baseline isn't. Best-of-grid
shopping is disallowed: if two cells pass, the SMALLER f wins; ties →
smaller k. Anything less = NULL, recorded beside §5f with the grid
table, and the war-chest idea closes (the owner reads the number, not a
softened summary). Adoption, if earned, is a 2027-Q1+ registry
promotion (R10) with a written demotion rule — it would change §3.3's
split, the copilot, and PLAYBOOK §3, one session, one commit.

**Relationship to #50:** #50 stages ONE position's add (shelf/−7%/−14%);
#86 reserves BUDGET across months. Run #50 first if convenient — its
tranche bookkeeping is reusable — but neither blocks the other.

File: `homily_warchest_backtest.py` (new; reuses bt_data + the §3
harness) · Effort M · one session, results → BACKTEST_RESULTS new §.

### D-87 · Concentration regime conditioner (#87)

**Why now:** rs12-top3 is LIVE (promoted 2026-07-12, owner override)
and its documented weak side is reversals — §4's honesty box: on
universe A's 2019→2024 window top-3 scored 2.35 vs equal-all's 2.59,
below the p10 of 200 random draws. The demotion rule catches sustained
live failure; this study asks the cheaper question first: is the
failure state PREDICTABLE, and should concentration stand down in it?

**Protocol.** Reuse `homily_selection_backtest.py`'s replay: same
monthly candidate sets, same picks, but each month is tagged with three
point-in-time conditioners — (a) regime label (BULL/MIXED/BEAR from the
frozen 10m-SMA engine), (b) breadth (% of screened names above their
200d SMA, the #26 canary), (c) trailing-3m QQQ total return sign. For
each conditioner: MOIC of rs12-top3 vs equal-all *within* each state,
both universes, all §3 windows. No new parameters are fitted — the
conditioners are pre-existing, frozen engine outputs.

**Pre-registered decision rule:** a conditioner earns a promotion
candidacy ONLY if, on BOTH universes, top-3 beats equal-all in its
favourable state AND loses in its hostile state (sign flip, not a
gradient), and the implied conditional strategy (equal-split in hostile
months, top-3 otherwise) beats always-top-3 by ≥ +0.05 MOIC on ≥2 of
the 3 construction-honest windows without losing any of them. One
conditioner passing = the candidate; two passing = the SIMPLER one
(regime label > breadth > QQQ sign, in that order). None = NULL, close,
and the live demotion rule remains the only guard. Any ship is a
2027-Q1+ registry entry (R10) with its own demotion rule.

File: extend `homily_selection_backtest.py` (flag-gated arm; committed
run's numbers stay byte-identical) · Effort M · one session.

### D-90 · GAMBIT merge — one repo, three books (#90)

**Owner directive, 2026-07-12** (verbatim intent): one repo to update;
the 4–12-week swing sleeve lives here; GAMBIT as a separate repo
retires. What merges is the MACHINE and its live paper state — not a
strategy claim: the Phase-1 kill (KILL_MEMO), the A4 reopen (S1-pure to
P2 paper, −40…−46% drawdowns accepted in writing), `LIVE_ORDERS=off`
and the P2 gate all carry over byte-for-byte. The merge changes WHERE
the sleeve runs, not WHAT it has earned.

**Layout.** `gambit/` package: engine + harness + tests keep their
filenames (`gambit/gambit_arms.py` … `gambit/weekly_run.py`,
`gambit/universe.json`, `gambit/tests/`); governance docs verbatim to
`docs/gambit/` (PRD, DESIGNS, EXECUTION, BACKTEST_RESULTS, KILL_MEMO,
LEVERAGE_MEMO, AMENDMENT_A4). `SIDECAR.csv` (if rows exist) rides to
`gambit/SIDECAR.csv` — ring-fenced ledger, never in homily books. File
CONTENTS stay byte-identical (only paths move), so the gambit engine
manifest re-pins paths with unchanged content hashes and the journal
hash chain verifies unbroken across the move.

**Integration points (all additive):** CI gains the weekly paper job
(`gambit_validate` gates it, same pattern as homily [16]); the homily
digest gains a fenced `SWING (paper)` section appended from the weekly
run — it states P2 PAPER + gate progress (`wk n/26 · trades n/20 ·
expectancy`) so nobody mistakes paper for money; homily's ledger,
snapshot and goldens are untouched (R2/R3 — swing rows never enter
`homily_signals_log.csv`).

**Gate (all four):** (1) `gambit_validate` green from the new location
AND homily validate green with zero golden re-pins; (2) journal hash
chain verifies across the move; (3) one weekly paper run from inside
homily-bot reproduces the standalone run byte-identical on the same
bars snapshot; (4) the gambit repo's final commit is a tombstone README
pointing here — archived read-only, never deleted (history is the audit
trail).

Effort M · one session · goes FIRST among #90–93: everything else in
the directive lands inside the merged repo.

### D-91 · Leverage policy — regime-gated ladder, sleeve-only (#91)

**Owner directive, 2026-07-12:** maximum-return posture; leverage is no
longer excluded (§7/§8.2 amended this date). This design gives the
directive the same treatment every other rule here gets: derive the
constants from our own measured paths, pre-register the referee, and
write the delever rule before a dollar moves. LEVERAGE_MEMO's
arithmetic is not repealed — **leverage amplifies edge, it cannot
create it** — so the policy binds leverage to the two places the
evidence permits it: the regime signal, and a gate-passed sleeve.

**The arithmetic the constants come from** (maintenance m = 0.25, gross
leverage L, uniform drop d; margin call when (1−Ld)/(L(1−d)) < m, i.e.
d\* = (1−mL)/(L(1−m)) — and concentrated books carry m > 0.25, which
only tightens every row):

| gross L | call at drop d\* | against our own measured paths |
|---|---:|---|
| 1.15× | −82.6% | — |
| 1.30× | −69.2% | regime-gated worst path −29% → −38% levered equity DD; a COVID-speed −35% shock landing before the month-end signal → −45.5%. No call. |
| 1.50× | −55.6% | the same −35% shock → −52.5% equity DD — one gap away from a call at concentrated maintenance |
| 2.00× | −33.3% | called by QQQ's own measured −34%; called by every strategy path |
| ≥1.25× constant on the core book | −73%…−33% | the core arms' multiwindow paths ran **−59…−76%** → wipeout territory. **The core monthly book never carries margin. Non-negotiable.** |

The regime signal is month-end, so the ladder must survive a crash
FASTER than the signal — hence the −35% stress row, and hence 1.30, not
1.50.

**The ladder (policy; owner signs before it is live):**

* **BULL** (SPY and QQQ both above 10m SMA): account gross ≤ **1.30×**.
* **MIXED** (one below): ≤ **1.15×** — no new margin, paydown drift.
* **BEAR** (🐻 onset): **1.00× — margin to zero at onset.** Not new
  machinery: PLAYBOOK §4's first step is already "margin first."
  Re-lever only on the §4.7 thirds re-entry schedule.
* Margin dollars fund ONLY swing-sleeve entries (4–12wk, journaled,
  stop written before entry). Per levered position: sized so a p5
  episode (−31.7%, BACKTEST_RESULTS §12) × L costs ≤0.5% of net liq —
  at 2× position leverage ≈ 1.6% notional, the same dispersion math
  that derived the whale-dip cap.
* Financing modeled at IBKR BM+1.5% in every levered comparison, with a
  stress cell at rate+2% (LEVERAGE_MEMO L3, inherited).

**The referee (pre-registered):** any levered arm is scored against
**regime-gated levered QQQ at the same L, same financing** — never
against unlevered QQQ (that comparison is the self-deception the random
band exists to prevent, in leverage form). Leverage that cannot beat
the same leverage on the index belongs on the index.
`homily_leverage_backtest.py` (new, M; reuses bt_data + the frozen
regime engine) pins the arms: QQQ B&H · regime-gated QQQ · regime-gated
QQQ at L ∈ {1.15, 1.30, 1.50} net of financing · the honest-control
strategy at the same ladder (expected: confirms the core-book ban) ·
S1-pure at sleeve scale. **Run before the policy signs.** Constants
adopt only if (a) no measured path — including the max-history grinders
— breaches d\* at its ladder step, and (b) regime-gated levered QQQ
beats unlevered QQQ net of financing on ≥2 of 3 construction-honest
windows. Results → BACKTEST_RESULTS new §; a failed readout shrinks the
ladder, it does not widen the model.

**Account reality (the transition):** the account already runs ~1.23×
(S$42.9k net liq, −S$9.8k cash, 2026-07-10) — legacy margin, spent on
the core book, which is exactly what this policy forbids going forward.
Grandfathered **shrink-only**: no new core margin ever; contributions
and the standing MARGIN_ZERO task pay it down; swing entries may use
only the headroom between current gross and the ladder cap (~S$3.1k
today, growing with every paydown month). Nothing is force-sold (§5
stands).

**What stays true under the directive:** live leverage attaches only to
a sleeve arm that has passed its unlevered gate (L1 inherited —
S1-pure's P2 paper gate reads earliest ~2027-01); until then the only
live levered dollars are the SIDECAR's, on its frozen terms (scored
2027-07). Two-artifact pattern: this design + a dated owner signature
in a new `LEVERAGE.md` before the first levered order; the daily digest
prints a leverage line (gross L vs ladder cap) from the day the policy
signs.

Effort: M (backtest) + S (policy doc + digest line) · gate: the
pre-registered readout above, then the owner signature.

### D-92 · Concentration promotion — add-cap 10% → 25% + dip-adds into winners (#92)

**Owner directive, 2026-07-12:** concentration encouraged — "allow
adds into winners on dips instead of the 10% hard rule." The evidence
already priced this exact move (D-67 / BACKTEST_RESULTS §12):
25%-redistribute ties-or-beats 10% in 7/9 windows with shock-MaxDD
within 5 pts — **formally adoptable by the letter of D-67** — and the
recorded cost is the shock table: at a −95% single-name gap, 25% keeps
1.70 vs 10%'s 1.89 MOIC (half the insurance payout surrendered). The
reason this is adoptable at all: the ⭐ gate, not the cap, contains
wrecks (step-2a, confirmed — wrecks lose ⭐ long before they accumulate).
**Uncapped stays excluded**: ruled out pre-registration (∞ excluded by
rule) and its −95% shock number (1.49) is the memo the next bubble will
wish we had kept.

**What changes when promoted:** PLAYBOOK §3.4 add-cap 10% → 25% of the
stock book (the bucket-C warning threshold in `homily_positions.py`
moves with it); dip-adds route exactly as today — ⭐-at-shelf monthly ·
🟡+🎯 aggressive add · ⚪+🎯+🐳 whale-dip ≤2% — the cap was the binding
constraint on winners and 25% unbinds it for a book whose top names sit
near 10% now. Copilot constant sync (#31), validate test, README
honesty line, all in the same commit.

**Pre-registered demotion rule (armed in the promotion commit,
promotions.json):** if any single name ≥15% of the stock book closes
−50% from its held high-water mark, the cap reverts to 10%
mechanically and the episode is scored in BACKTEST_RESULTS — that is
the exact wreck the 10% cap insured against. Names may GROW past 25% by
appreciation and are never force-trimmed (§5 stands); the cap binds
adds only.

**Timing (R10):** Q3 carries 🐳 + rs12-top3; Q4's slot was spent by the
early promotion — the clean slot is **2027-Q1**. The owner-override
lever exists (the #24 pattern: two-artifact + promotions.json entry +
the demotion rule above), at the recorded cost that October's
attribution then reads THREE 2026 epochs and #85's split becomes
mandatory. This design makes either path a one-session change; the
directive's intent is on the record now either way.

Effort S (promotion session) · gate: D-67 already ran — the gate is the
demotion rule being armed in the same commit.

### D-93 · Swing sleeve live-arming (#93)

Preconditions, all four, none waivable silently: (1) **P2 paper gate
green** — ≥26 weeks (≥2027-01-09) AND ≥20 closed trades AND expectancy
> 0 AND green vs the QQQ bar, no backtest credit (gambit PRD §5.2,
unchanged by the merge); (2) **LIVE_ENABLE two-artifact** (gambit PRD
§3.4 pattern); (3) **order rail** = the G-S7 dark-order spec on the
IBKR MCP rail, human approval per order — bot proposes, owner disposes;
(4) **leverage attaches per D-91's ladder ONLY if L2 holds on the paper
ledger's own numbers** — MAR above QQQ's with headroom surviving ×L
drawdown scaling + financing at the then-current rate. K1–K6 kill
switches carry over live from journal row 1.

Effort M · own session · earliest ~2027-01 · gate: the P2 ledger IS the
gate.

*(#93 was LIVE-ARMED early 2026-07-12 by owner override — Amendment A5;
the preconditions above were overridden, not met. See PRD §8.5.)*

### D-94 · Household book — the whole-portfolio north-star scorecard (#94)

**Planned 2026-07-12 (late), integration era.** §9.0's metric is measured
only on the cash sleeve (#14, correctly — that is where signal skill is
isolatable). But the system now runs FOUR money surfaces — core cash
sleeve, SRS (the index leg), ESPP (V at 15% discount, partly off-IBKR),
and the levered swing sleeve with its paper counterfactual — and no
artifact answers the owner's actual question: *is the whole machine
compounding faster than the same cash flows DCA'd into QQQ?* With
leverage live-armed this is also the ruin-risk readout: combined gross
exposure across books is a number nobody computes today.

**What.** `homily_household.py` — a monthly (first-Monday, beside
bear-readiness) digest block + docs section:

* whole-book value = IBKR book (holdings.json v2 incl. source tags) +
  external ESPP shares + SRS balance + swing sleeve equity
  (`gambit_live_book.json`) − margin loan; printed in USD **and SGD**
  (#53 absorbed here — the `SGD=X` FX line lives in this block).
* rolling 12m/24m/36m whole-book money-weighted return vs the
  same-cash-flows QQQ DCA counterfactual (adjclose math, #18/#68).
* one attribution row per sleeve — core edge (the #14 number once it
  matures), swing realized+MTM, ESPP discount, SRS beta — so nobody
  confuses which engine earned what.
* combined gross leverage vs the LEVERAGE.md ladder cap (core margin +
  swing margin over net liq) — the number the ⚖️ line approximates
  today from one book's view.

**Cash-flow honesty.** The counterfactual needs actual flow dates.
BUY_BUDGET deployments are in the ledger (#13); swing
contributions/skims are journal rows; SRS/ESPP are owner-scheduled — a
small committed `contributions.json` (owner-maintained; the block prints
a nag when a month has no row, never a guess) covers what no API sees.
Monthly granularity, stated on the page — precision theater is worse
than an honest coarse number.

**Explicitly not:** a replacement for #14 (which isolates signal skill);
a money gate (info-only forever); a new fetch surface beyond the one FX
series.

**Gate (info-only).** Fixture: synthetic 3-sleeve book + flow history →
deterministic table; validate asserts adjclose is used for return math
and that a missing contributions month prints the nag.

File: `homily_household.py` + digest/docs wiring + `contributions.json` ·
Effort M · buildable now (manual fields until #32 secrets, labelled).

### D-95 · Flywheel — swing-skim → DCA routing, measured (#95)

**Why.** The stated purpose of the live sleeve is income that
accelerates the DCA (A5 owner line: *"any proceeds … will all go towards
funding the monthly dca"*), and the monthly report already prints a
"sweepable-to-DCA amount" — but nothing defines WHEN a sweep happens,
HOW it enters the buy routine, or MEASURES the acceleration. An
unmechanized transfer is the behaviour gap (#58) arriving in the newest
sleeve: proceeds will sit, or move on mood.

**Skim rule (pre-registered).** At each quarter-end monthly report
(first report of Jan/Apr/Jul/Oct), if the live book is above BOTH its
high-water mark AND contributed capital:

    skim = min(free cash, equity − max(hwm, contributed))

Realized cash only — never a forced sale, never principal; the HWM
ratchets so the same profit cannot be skimmed twice; below HWM or
contributed → skim 0, and that is correct behaviour (G8: red quarters
pay nothing; no borrowing to fake stability).

**Kill-math interplay (stated, not re-derived).** Skims append SKIM
journal rows and accrue in a `skimmed` field; `contributed` is
untouched. KILL-A stays `equity ≤ 70% of contributed` — a skim moves
equity closer to the trigger in absolute dollars, which is accepted and
conservative: banked money leaves the casino and the remaining book
must survive on its own. Cumulative skims count in the experiment's
SCORING (equity + skims vs contributed, vs the LEVERAGE.md §3 referee)
and in #94's attribution — never in the kill check. Pre-registered kill
rules do not get softened by their own successes.

**Routing.** The skim prints as a `+ skim US$X (swing, Qn)` line in the
next 🛒 BUY DAY block: BUY_BUDGET + skim deploys per the unchanged §3
routine. The owner moves the cash — the same trust model as the order
sheet (bot proposes, owner disposes).

**Measurement (the point).** Monthly flywheel table: cumulative skims,
what they bought (ledger rows), and two counterfactuals — (i) left
compounding in the sleeve, (ii) same-day QQQ. That table is the honest
answer to "does the swing sleeve accelerate the DCA" — and a
null/negative answer prints too.

**R10 note (pre-empting the debate).** This is funding-flow accounting
(§9.4 territory — owner cash routing between his own sleeves), not a
signal-behaviour promotion; no R10 slot is consumed. The first real
skim is an owner action from a printed line.

**Gate.** Fixture pytest: synthetic journals → skim fires only above
hwm ∧ contributed; ratchet correct; kill check byte-identical before
and after SKIM rows; PLAYBOOK §7/§9 + the A5 reporting section amended
in the same commit.

Files: `gambit/gambit_live.py` (skim calc + SKIM rows),
`homily_buyday.py` (+skim line), PLAYBOOK, validate/pytest · Effort M ·
build before 2026-10-01 (the first quarter-end the live book could
conceivably clear its HWM).

### D-96 · A5 A/B reader — the stop-cost table (#96)

**Why.** A5's central design IS an A/B — the live overlay
(stops/TP/time-stop, ladder-sized) mirrors the paper S1-pure book (no
stops) on the same Friday decisions — and A5 promises the stops' cost
is *"measured, monthly, in public."* No pre-registered read exists yet;
without one the conclusion will be argued from vibes at exactly the
moment (a stop-out that recovered / a crash the stops dodged) when
vibes are worst.

**What.** A monthly section riding the realized report: per-episode
attribution — every live exit the paper book didn't take (STOP / TP /
TIME) is followed forward on the paper leg to the current mark; prints
the realized delta per episode + a cumulative "stops P&L" line + the
sizing effect (ladder × US$3k vs paper's notional US$20k) separated
from the exit effect, so leverage and stops don't get blamed for each
other. The modeled-fill caveat carries verbatim.

**Pre-registered read (frozen now).** At the earlier of 26 live weeks
or 20 closed live trades, the reader prints its verdict row: stops
cumulatively cost / saved US$X vs paper on the same decisions.
**REPORT-ONLY:** the A5 stops stay mandatory while the book is levered
(bounded loss is their job, not edge — KILL_MEMO stands); the read
informs the next signed amendment and cannot change live rules itself.
Both directions stated in advance: stops looking expensive in a
trending tape is EXPECTED (S1-stopped 0/3); what could justify an
amendment is the ladder/kill interplay, never one hot quarter.

**Gate.** Deterministic fixture: two synthetic journals with known
divergences → known attribution table; the module is read-only (zero
writes to either journal, asserted in the fixture).

File: `gambit/gambit_ab.py` (read-only over both journals) + report
wiring · Effort S–M · buildable now; the verdict row is date-gated.

### D-97 · Cross-book concentration lens (#97)

**Why.** G5 named this risk the day GAMBIT was designed: both books
draw from the same AI/semi cluster, so one −35% cluster gap now hits
the core book AND a levered sleeve in the same week. #29's lens sees
holdings.json only; the swing positions and the external ESPP V shares
are invisible to the one instrument built to see concentration.

**What.** Input-assembly extension only —
`homily_clusters.concentration`'s correlation math is untouched:
positions fed to the lens = holdings.json (incl. `source:"espp"`
external shares, already counted for caps) + gambit live open positions
tagged `book:"swing"`. The digest cluster line gains the combined view
when it differs from core-only ("AI/semi 58% core → 64% with swing ⚠").
Order-sheet side: the weekly sheet prints a warning when a proposed
entry would (a) breach G5's max-2-overlap with core holdings or
(b) deepen a >60% combined cluster — info-only, the owner decides; the
S1 rotation itself is untouched (the §4.1 signal budget stands — a
warning is not an input).

**Gate.** Fixtures both sides: synthetic overlapping books → warning
fires; disjoint books → silent; sheet text pinned. Info-only.

Files: `homily_clusters.py` (input assembly), `daily_run.py` (line),
`gambit/gambit_live.py` (sheet warning) · Effort S–M.

### D-98 · Swing scale ladder — the bankroll is earned (#98)

**Why.** A5 caps top-ups at ≤10% of net liq but sets no earn-condition,
and at US$3k the sleeve's income is a rounding error (~US$40/mo at
+15%/yr) — so the pressure to top up after a hot month is structural.
Impulse scaling after wins is exactly how G8's income-pressure failure
arrives by the other door. Pre-register the steps now, in the bull,
while nobody is excited.

**The ladder (policy).** Contributed capital moves only in
pre-registered steps: **US$3k → 6k → 12k**, each still ≤10% of net liq
at the step date, LEVERAGE.md account caps always binding. One step up
requires ALL of, evaluated on the live journal alone:

* ≥20 closed live trades since the previous step;
* expectancy > 0 over the trailing 20 closed;
* equity + cumulative skims ahead of the LEVERAGE.md §3 referee
  (regime-gated 1.30× QQQ, same dollars, same dates) over the trailing
  26 weeks;
* zero kill-line touches and zero margin events, ever;
* a dated owner line appended to AMENDMENT_A5 (two-artifact pattern)
  naming the step.

A kill ends the experiment regardless of ladder position (A5: no
restart without a new gated design). Steps DOWN are always free and
need no conditions.

**Gate.** Constrains only — no R10 slot. `gambit_validate` check: a
CAPITAL top-up row in the live journal without a committed
satisfied-preconditions record (`gambit_live.py --scale-check` output)
+ the A5 owner line fails CI — the K6 pattern: policy breaches are
loud, not debated.

Files: `gambit/PRD.md` §3.5 (policy text), `gambit/gambit_validate.py`,
journal CAPITAL rows (already exist per A5 "top-ups recorded") ·
Effort S.

---

## Part II — extended idea bank (#46–60)

Unvetted. Each carries its gate; none touches money before its gate passes.
Numbering continues PRD §8 (#61–84 taken — see PRD §8.3 index; #68–75
assigned 2026-07-11 in PRD §8 phases; #77–82 = Danny latest-posts review,
PRD §5k, full rows in the §8.3 table; #83 = Danny-style chart board,
D-83 above; #84 = any-ticker chart CLI; #85–89 added 2026-07-12 —
#85 epoch split (S, rides #14), #86 dip war-chest (D-86), #87
concentration conditioner (D-87), #88 top-3 turnover stat (S), #89
rs6/blend rank challenger (column time-sensitive); #90–93 added
2026-07-12 — the owner max-return directive: #90 GAMBIT merge (D-90),
#91 leverage policy (D-91), #92 add-cap promotion (D-92), #93 swing
live-arming (D-93); #94–100 added 2026-07-12 (late) — the integration
era: #94 household scorecard (D-94), #95 flywheel skim (D-95), #96 A5
A/B reader (D-96), #97 cross-book lens (D-97), #98 scale ladder (D-98),
#99 ops-readiness block, #100 realized-cost reconcile — full rows in
PRD §8.3; new proposals start #101).

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
53. ~~**SGD lens**~~ (S) — **absorbed into #94 (D-94) 2026-07-12**: the
    USD/SGD line ships inside the household block, not as its own digest
    line (delete, don't accrete). Original intent: monthly book return in
    SGD + USDSGD 12m trend (`SGD=X`); liabilities are SGD, the book USD.
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
