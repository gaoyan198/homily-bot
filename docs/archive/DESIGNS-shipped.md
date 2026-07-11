# Archive — DESIGNS Part I designs whose items shipped

Moved verbatim from `DESIGNS.md` on 2026-07-11 (#76 planning-doc pruning).

<a id="d-24"></a>

### D-24 · ⭐ overflow ranking (#24)

Monthly replay over months with >5 ⭐ candidates on buy day. Compare:
(a) RS12 top-5 · (b) equal-split all · (c) random-5 — 1000 draws, giving a
*distribution*, not a strawman · (d) alphabetical top-5 — the accidental
current behaviour, which any change must also beat. Metrics: 12m forward
return and avg-cost (the system never sells; cost matters). **Adopt (a)
only if it beats random-5's median in ≥60% of draws AND beats (d).**
Expect a null result — momentum-ranking momentum-gated names is nearly
circular; the honest test is cheap and settles it.

**RUN 2026-07-10 — the null did NOT materialise** (PRD §5j, BACKTEST_RESULTS
§4, `homily_selection_backtest.py`: portfolio-MOIC variant, 200 draws,
rule pre-registered): `rs12-top3` passed every check on the honest
control's read windows, above random's p90 in all three. Promotion
candidate declared (top-3, not top-5); waits for 2026-Q4 (R10) + the #13
ledger forward-check. Conviction-score ranking added nothing over raw RS.

<a id="d-29"></a>

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

<a id="d-31"></a>

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

<a id="d-34-35-36"></a>

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

<a id="d-63"></a>

### D-63 · Bear-regime rethink — decompose the 🐻 sell step (#63)

**Owner-requested 2026-07-08; may jump the session queue.**

**Why (evidence as of 2026-07-08).** Two independent backtests agree the
bear overlay destroys value in the tested windows: the repo's own THE-test
rows (5y 16.7% → 6.4% CAGR, 10y 19.2% → 9.4% — BACKTEST_RESULTS.md) and
the owner's independent Opus replay (selling satellites at 🐻 lost to plain
holding). Worse, the overlay barely improved drawdown (−26→−28% at 5y,
−66→−64% at 10y) — in-window it fails at its *own* goal. But the overlay
that was tested is NOT PLAYBOOK §4: it sells *everything* (no bucket
distinction), parks proceeds AND new contributions in cash (§4 step 6 says
keep buying the index through the bear), and lump re-enters (§4 step 7 says
thirds over 3 months). The measured ~−10 pts/yr conflates three separate
decisions that have never been isolated. Meanwhile the 30y INDEX-level
record (`homily_regime_backtest.py`, re-run 2026-07-08) shows what the 10m
SMA actually is: roughly CAGR-neutral insurance that halves MaxDD *on the
index itself* — SPY timed 7.9%/−24% vs held 8.9%/−52%; QQQ timed 7.4%/−37%
vs held 7.4%/−81%. It pays enormously in grinding bears (dot-com QQQ −13%
timed vs −80% held), loses every V-recovery (COVID −10.5% vs −10.4%, then
re-buys higher; 2023-25 bull lag 88% vs 131%).

**The structural hypothesis to test.** The 10m SMA is an index-vol signal
applied to satellite-vol positions. By the time BOTH indices close a month
below their SMA (2022: fired ~Feb–Apr), 60–90%-vol satellites had already
taken −40…−60% of their drawdown; by the time both reclaimed (Jan–Feb
2023), the survivors had already bounced hard off the Oct–Dec lows.
Sell-low / re-buy-high is a structural lag mismatch, not one window's bad
luck — and IF this holds, no re-entry tweak rescues the sell step for
satellites; only dropping it does. The index core was never the question
(Bucket A is never sold; the 30y numbers above are why that rule stays).

**Step 1 — decomposition matrix.** New `homily_bear_backtest.py` (reuse
`run_strategy` machinery from `homily_strategy_backtest.py`; add a
`bear_mode` switch). Point-in-time, both universes (current + hype-2021
control), 5y AND 10y windows, 10 bps:
  (a) **hold-through** — idx-fallback, no regime (the current champion);
  (b) **sell-all + cash** — the existing overlay, reproduced (regression
      row: must match the committed BACKTEST_RESULTS numbers);
  (c) **freeze-only** — hold everything; while 🐻 no satellite buys,
      contributions → index core;
  (d) **faithful §4** — sell satellites once at 🐻 onset → dry powder
      (cash, 0%); contributions → index while 🐻; on 🐂 redeploy the dry
      powder into ⭐ picks in thirds over 3 months;
  (e) **sell-into-index** — sell satellites at onset, proceeds straight
      into the index core, never re-timed (kills the re-entry leg).
Report MOIC / TWR CAGR / MaxDD per mode, plus the 2022 episode in
isolation. Mandatory header caveat: these windows contain ONE bear episode
and it was V-shaped — this is a decomposition, not a proof.

**Step 2 — grinding-bear test (the design case).** The sell step was never
for 2022; §4 says its value is "avoiding the −40…−80% middle" — that means
2000-02 and 2008. Run modes (a)–(e) with `rng="max"` on high-beta names
alive through both bears (AMZN NVDA AAPL MSFT ADBE INTC CSCO QCOM ORCL
EBAY). Survivor-biased — label it — but the failure mode under test is
holding *through* −80%, which survivors still exhibited (AMZN −94%;
CSCO/INTC never reclaimed their 2000 highs). If the satellite sell step
doesn't pay HERE, it pays nowhere and the case is closed.

**Step 3 — the vol-matched alternative.** If the index gate is too slow
for satellites, the per-name tool already exists: PLAYBOOK §5.2 (⚪ 12w +
F:0–1 → sell half). Mode (f): no 🐻 selling at all; §5.2 as the only
satellite exit. Prior warning: per-stock trend-cutting failed our backtests
twice (`homily_regime.py` header) — expect a null; run it anyway so the
claim "per-name beats index-gate for satellites" finally has a number.
(Ties into idea #51, the ⚪ time-stop calibration.)

**Decision rule (pre-committed, so the result can't be argued with).**
- (c) ≥ (a) − 0.5 pt CAGR AND (c) ≥ (b), (d), (e) in both windows AND the
  sell step also fails Step 2 → **PLAYBOOK §4 drops the mechanical sell**:
  🐻 becomes freeze-satellite-adds + all contributions → index +
  margin-zero enforcement; §5.2 stays the only satellite sell; the banner
  keeps its behavioural role (pre-commitment against panic).
- (d) materially beats (b) → §4 stands as written; BACKTEST_RESULTS gets a
  correction note (the overlay it maligned was never the playbook).
- Step 2 shows the sell step pays big in 2000-02-style bears → keep it,
  reframed explicitly as tail insurance, with the measured in-window
  premium (the V-recovery cost) quoted right in §4 — the "false alarms are
  the premium" paragraph already half-says this; give it the number.
- Whatever wins, the SAME commit syncs: PLAYBOOK §4, HOW_IT_WORKS.md,
  BACKTEST_RESULTS.md (new table replaces the two overlay rows), and the
  BEAR action string in `homily_regime.py` ("DECISIVE SELL: … exit
  satellite/🚀 names" must say what the book says — no drift).

**Pitfalls.** Thirds re-entry must key off completed-month 🐂 only (reuse
`regime_series`); mode (d) sells once at onset, not every bear month; dry
powder earns 0% and MUST be marked in `val` each month or MaxDD is fake;
buckets aren't modelled in the backtest (every position is a satellite) —
acceptable, note it, and optionally add a Bucket-B proxy (grown-to->10%
positions exempt from the 🐻 sell) as a sensitivity row, not a headline.
Part III rule 6 is sacred here: if the numbers contradict this design's
hypothesis, ship them and stop.

File: `homily_bear_backtest.py` · Effort M · validate: mode (b) reproduces
the committed overlay rows (regression); golden numbers in the docstring.

**RESOLVED 2026-07-10 (PRD §5i, BACKTEST_RESULTS.md §2).** Step 2 finally
ran on true daily bars (the `range=max` fetch had been silently returning
monthly bars — fixed + guarded in `homily_data.py`, validate [22]) and the
structural hypothesis above was REFUTED in grinders: faithful §4 kept
20.4%/yr vs hold's 21.3% while cutting −76% → −29% MaxDD. Outcome = branch
3 (+ branch 2's correction note): §4 kept as priced tail insurance,
premium quoted in PLAYBOOK; freeze-only dominated (worst of both worlds);
sell-into-index catastrophic in grinders; per-name §5.2 the only
return-ADDING arm on the honest control (+3.4 pts/yr at 10y, no crash
protection). Banner/PLAYBOOK/HOW_IT_WORKS/BACKTEST_RESULTS synced in the
same commit per the rule. Rule 6 note: the numbers contradicted this
design's hypothesis and shipped anyway.

<a id="idea-49"></a>

49. **Golden-file digest tests** (S) — fixture bars → exact expected digest
    text committed; validate diffs it every run. Refactors can no longer
    silently change a row. **Gate:** none (test infra). *Build this FIRST
    on execution days — it is the executing model's safety net.*
