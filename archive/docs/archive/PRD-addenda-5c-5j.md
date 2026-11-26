# Archive — PRD addenda §5c–§5j

Moved verbatim from `PRD.md` on 2026-07-11 (#76 planning-doc pruning).
Never edited after archiving; pointers remain at the original locations.

<a id="5c"></a>

## 5c. Addendum 2026-07-06 — discovery screen (names not held)

User request: no loyalty to current holdings — screen for money elsewhere
too. `UNIVERSE` in `daily_run.py` (~40 liquid names: megacap tech, semis/AI
hardware, growth software, quality diversifiers, HK/SG liquid names) runs
through the same composite engine; only ⭐ ACCUMULATE / 🔵 BOTTOMING setups
surface (max 8 rows + overflow tickers). Exclusion stands: no leveraged
ETFs. Telegram sends now split at 4000 chars.

**Update 2026-07-09:** added D05.SI (DBS), IBIT, ETHA to `UNIVERSE` per
owner request. The crypto-beta exclusion is lifted — IBIT/ETHA (spot
BTC/ETH ETFs) now screen through the same composite engine as everything
else, no special-casing.

<a id="5d"></a>

## 5d. Addendum 2026-07-06 — multi-bagger conviction screen + methodology page

User request: multi-bagger potentials, stringent recommendations, conviction
sizing, methodology exposed as a page.

* `homily_conviction.py` — 5 hard gates (size-by-$vol < $5B/d, monthly UP +
  weekly RED, 12m RS ≥ SPY+20pts, price > POC, ≥200 bars) then a 0–100 score
  (trend 25 · RS 25 · structure 15 · vol-hole 10 · size/room 15 · age 10).
  Tiers: ≥75 CONVICTION ≤5% of account · 60–74 STARTER ≤2% · hard cap
  10%/name incl. existing. 🚀 section in digest, max 5, held + not-held.
* Universe +17 growth mid-caps (RKLB ASTS SOFI HIMS DUOL AXON TOST RBLX IOT
  CRDO TMDX CAVA ONON SE GRAB NBIS ALAB).
* `docs/index.html` — self-contained methodology page (engines, gates,
  rubric, sizing, honest-backtest table, limitations). Repo is private, so
  enabling GitHub Pages would make the page public — kept as an in-repo file
  to open locally; enable Pages only as a deliberate decision.

<a id="5e"></a>

## 5e. Addendum 2026-07-06 — market regime / decisive sell signal

User request: a strong decisive bull-over signal to sell into, hold dry
powder, re-accumulate in bears.

* `homily_regime.py` — classic 10-month-SMA month-end rule on BOTH SPY and
  QQQ: both above = 🐂 BULL, both below = 🐻 BEAR (the decisive sell), split
  = ⚖️ MIXED (wait for month-end). Digest banner at the top every day;
  BEAR carries the protocol (halt adds, exit satellites/🚀, raise dry
  powder, index core stays, re-enter on month-end reclaim).
* `homily_regime_backtest.py` — 33y SPY / 26y QQQ, no look-ahead, 5bps per
  switch, cash at 0%: QQQ timed = same final wealth with −37% vs −81% MaxDD;
  SPY timed = 7.9% vs 8.9% CAGR with −24% vs −52% MaxDD. Great in grinding
  bears (dot-com QQQ −12.7% vs −79.6%), useless in flash crashes (COVID),
  lags strong bulls (2023-25). Full tables on docs/index.html §4.
* **Resolved 2026-07-10 (see §5i / D-63):** the sell step survives as
  *priced tail insurance* (−76%→−29% worst dd for ~1 pt/yr over 33y), the
  banner/protocol wording synced; "DECISIVE SELL" framing retired.

<a id="5f"></a>

## 5f. Addendum 2026-07-06 — full strategy vs index DCA (THE test)

User: "make sure we have a winning strategy that outperforms the index —
take the bias out, report hard numbers." `homily_strategy_backtest.py`:
point-in-time monthly replay 2021-07→2026-07, $1/month, 10bps/trade,
⭐-gated equal-weight deployment, optional 🐻 full liquidation.

Hard numbers (MOIC / TWR CAGR / MaxDD):
* DCA SPY 1.50 / 11.3% / −23% · DCA QQQ 1.74 / 14.7% / −34%
* A current universe (hindsight-biased): no-regime 3.69 / 43.5% / −18%;
  with regime-sell 1.69 / 18.0% / −19%
* B hype-2021 control (incl. wrecks): **no-regime 2.10 / 22.2% / −30% —
  beat both indexes**; with regime-sell 1.31 / 6.9% / −31% — lost to SPY.

Conclusions adopted: (1) accumulation engine = the buying discipline —
promising cross-sectional edge even on loser-salted control, one window,
residual survivorship, "promising not proven"; (2) 🐻 full liquidation was
pure cost in a V-recovery window — keep BEAR protocol scoped to satellites
+ pause-adds, index core never sells (digest already words it this way);
(3) re-run this test yearly as data accrues (added to backlog).
*(2026-07-10: (1)'s "promising" is downgraded and (2) is superseded by the
D-63 decomposition — see §5i: freeze-only is dominated, §4's once-at-onset
sell + index-contributions + thirds re-entry is the kept shape, and the
cleaner-protocol multi-window test erases the 5y QQQ win.)*

<a id="5g"></a>

## 5g. Addendum 2026-07-06 — core-4 concentration test (Danny's 85/90% method)

User: full-time job, can't execute broad dip-buying; prefers Danny's 90%-in-
top-4 concentration. `homily_core4_backtest.py` (2021-07→2026-07, $1/mo
split across core, 10bps, point-in-time):

* DCA SPY 1.50 / QQQ 1.74 MOIC.
* Danny's literal 4 (NVDA PLTR AMD HOOD) fixed: 5.56 / 46.3% CAGR / −61%
  dd — PURE HINDSIGHT upper bound (HOOD was a fresh meme-IPO in 2021).
* Engine-picked once in 2021 (NET ZS LCID CRWD), held: 1.76 / 6.4% / −72%
  — one wreck (LCID) dragged it to index-level. The cautionary tale.
* **Engine-picked, re-picked each July: 3.14 / 26.7% / −68% — beat QQQ**,
  one decision/year, executable. Picks churned through some garbage (BYND,
  CHWY 2022) but momentum re-selection recovered.

Adopted guidance: concentration cuts both ways (−61…−72% dd on 90% of
book); survivable structure = ~50% index core + ~50% annual-re-pick core-4
(~2.3×, ~−40% dd, linear approx). Published in docs/index.html §5b.

**Correction (same day, user insight):** Danny's core is EMERGENT — dips
bought while trend intact, never sold, winners grow into the core.
`homily_emergent_backtest.py` confirms: never-sell ⭐ accumulation on the
control universe → 2.10× (vs QQQ 1.74×) at −30% dd, with top-4 emerging at
62% of book (peak 69%, PLTR alone ~30%) from 27 names ever bought.
Emergent-concentration beats the engineered core-4 (−30% vs −68% dd, losers
never handed 22.5% of the book). Conviction-weighted adds vs equal adds:
no difference (2.09 vs 2.10) — the ⭐ gate does the work; skip sizing
complexity. THIS is the method the digest encodes; adopted as the standing
recommendation.

<a id="5h"></a>

## 5h. Addendum 2026-07-06 — whale-accumulation tag + WHALE-DIP tier (#12)

`homily_whale.py` approximates Homily's main-force line from public OHLCV.
🐳 = an actual dip (close ≥5% below the 60d closing high) + ≥2 of 3
footprints: **absorption** (a ≥1.3×-volume day probing within 3% of the
20d min low yet closing in the top half of its range — PLTR 2026-06-26 is
the calibration print), **flow divergence** (OBV or A/D line ≥ its
pre-dip-peak level while price is down), **shelf stability** (decayed chip
weight in the ±2% shelf band fully replenished over 10 bars while price
sits on the shelf). Point-in-time replay reproduces the motivating case:
🐳 fires on PLTR June 26-30 at the 113-119 shelf, before the July-1 rip to
125 — it cannot tag June 23-25 because the footprint only completes in the
data on the 26th; the tag follows evidence, not conviction.

Gate (`homily_whale_backtest.py`: 58 names = current univ + 2021 hype
controls, 5y daily point-in-time, $1 per qualifying day, vs the all-days
DCA baseline):

| arm (ALL combined) | days | episodes | fwd20 | fwd60 |
|---|---|---|---|---|
| DCA baseline | 53,987 | — | +3.1% | +9.5% |
| ⚪ dip unconditioned | 19,166 | 670 | +3.2% | +9.7% |
| ⚪ dip at shelf (🎯 only) | 10,714 | 1,047 | +3.0% | +9.0% |
| ⚪ dip 🎯+🐳 | 4,791 | 744 | **+3.5%** | **+10.9%** |

The conditioned arm beats baseline AND the unconditioned arm at both
horizons — including on the hype-2021 control alone (+8.1% vs +5.6% fwd60)
— so per the pre-registered rule it is **PROMOTED: ⚪+🎯+🐳 = WHALE-DIP
tier**, the one case a ⚪ name may be added. Discretionary, ≤2% of account
per name, same monthly budget (never extra money), 10%/name hard cap.
Honesty notes: the edge is modest (+1.4pts fwd60 over DCA); day-rows
cluster (~6 days/episode — judge by episodes); one 5y window; and the
shelf alone (🎯 without 🐳) actually LOST to the plain dip arm — the whale
footprint, not the level, carries the edge, which is exactly Danny's point.

<a id="5i"></a>

## 5i. Addendum 2026-07-10 — D-63 resolved + multi-window re-test (the bar)

Owner asked (2026-07-10): continue the bear/bull planning (their own
backtest agreed 🐻-selling hurt), rethink universe screening, and re-run
the backtests independently — with the bar: *beat SPY or QQQ over multiple
≥5y windows or the effort isn't worth it.* Full numbers:
BACKTEST_RESULTS.md (rewritten this session); harness:
`homily_multiwindow_backtest.py` (new, also serves #40's yearly re-test).

**Found + fixed on the way (the session's most consequential bug):**
Yahoo returns MONTHLY bars for `range=max` while honouring `interval=1d`
on shorter tokens — so D-63 Step 2 had only ever run daily signals on
monthly bars (and then crashed on QQQ's 1999 start; also fixed).
`homily_data.py` now uses epoch params for full history and refuses
non-daily responses; validate test [22] pins both. 5y/10y numbers were
unaffected (regression-verified).

**D-63 resolution (pre-committed rule, branch 3 + branch 2's correction):**
* Step 2 (1993→2026 incl. dot-com + 2008, survivor-biased): faithful §4 =
  20.4%/yr at **−29% MaxDD** vs hold-through 21.3%/yr at **−76%** — the
  sell step IS the drawdown insurance it claimed to be, priced at ~1 pt/yr
  (~⅓ of 33y final wealth), and ~7 pts/yr in a 2022-style V-window.
  **PLAYBOOK §4 stays, reframed as priced tail insurance with the numbers
  quoted in-file**; `homily_regime.py` BEAR banner now mirrors it (sell
  weak satellites ONCE → dry powder; monthly buys → index all bear;
  thirds re-entry — no drift).
* The committed overlay (sell-all monthly + cash + lump re-entry, mode b)
  was never §4 and overstated the damage — BACKTEST_RESULTS corrected.
* **Freeze-only ("pause adds, don't sell") is dominated** — kept the −76%
  grinder drawdown AND lagged in the V-window. §4 gained a "no
  half-measures" warning; the old idea that 🐻 might become freeze-only is
  dead.
* **Per-name §5.2 exit is the only arm that ADDED return on the honest
  control** (+3.4 pts/yr at 10y; best arm in most multi-window cells) —
  it exits the PTON/ZM class. Zero crash protection (−79% in grinders).
  §4 = insurance, §5.2 = trash-taker; both kept, jobs now stated. #51
  (⚪ time-stop calibration) is the follow-up that could sharpen it —
  raised in priority within Phase C.

**Multi-window verdict vs the bar (universe B control, 9 windows):** a
curated list is only out-of-sample after its construction date (mid-2021
for the control), so: pre-2021 windows = hindsight noise (54–84% CAGR,
ignored); 2021-straddling windows **lose to both indexes** (the ⭐ gate
momentum-bought ZM/PTON-class names into the bubble as they became
eligible — the gate does not dodge regime-scale overvaluation); the fully
honest 2021→2026 window **beats SPY, ties-to-loses QQQ** (1.70 vs 1.78
MOIC) — and the committed "5y QQQ win" was partly an eligibility artifact
(rng-5y fetch force-parked year 1 in the index). Every arm carries 2–3×
index drawdown. **Verdict: as an index-beating machine the engine does
not clear the owner's bar; QQQ DCA remains the strongest simple
competitor.** What survives on the numbers: §5.2 exits (small real edge on
wreck-salted books), 🐻 as priced insurance, and the discipline/execution
infrastructure (R0/R1) — plus selection work (#20/#24/#65) as the only
credible path to an actual edge, measured live by #13/#14/#64.

**Consequences adopted:** (1) BACKTEST_RESULTS.md is the single place the
bar is scored; re-run yearly via `homily_multiwindow_backtest.py` (#40).
(2) Construction-date honesty becomes a standing rule: every future
backtest names the universe's construction date and only reads
post-construction windows as evidence (applies to D-65's mechanical-2021
control too). (3) No engine changes shipped from these results — anything
that would (e.g. a valuation/breadth gate on ⭐, #26) goes through its own
Phase-C gate. (4) Owner decision recorded: the effort's justification is
now explicitly *risk-shaped disciplined exposure + live measurement*, not
a proven QQQ-beater — PLAYBOOK §8 and HOW_IT_WORKS honesty lines updated
to match.

<a id="5j"></a>

## 5j. Addendum 2026-07-10 (later) — #24 executed: ⭐ selection gate PASSED

Owner directive (same day, after §5i): the bar stays *beat QQQ*; do not
concede; improve the signals' ability to pick multibagger winners. Per
§8.0 the only lever with evidence is selection, so #24 (⭐ overflow
ranking) was executed at portfolio level — `homily_selection_backtest.py`,
decision rule pre-registered in the docstring before the first run
(equal-all vs alpha-top5 vs RS12-top5/3 vs conviction-top5/3 vs 200
random-5 draws; same candidate sets, same accounting,
regression-checked).

**Result (full tables BACKTEST_RESULTS.md §4): `rs12-top3` —
concentrate each month's stock-half into the top 3 candidates by 12m
relative strength — passed all four pre-registered checks** on universe
B's read windows, beating not just random's median but its p90 in all
three, and crossing QQQ in the fully honest 2021→2026 window (1.82 vs
1.78 MOIC). `conv-top3` also passed but no better than raw RS
(partial #20 answer: the score's weight is its trend/RS parts).
Declared now: **rs12-top3 is THE promotion candidate** (no
best-of-N shopping later). Caveats stated in the results file: modest
lift, n=3 read windows, 10y straddle still under QQQ, and it
*underperforms* equal-weight in universe A's reversal windows —
a trending-tape edge, not a solved problem.

**Promotion protocol (pre-committed):** R10 gives one signal-behaviour
promotion per quarter; 🐳 took 2026-Q3 (§5h). So: earliest 2026-10-01,
and ONLY IF the ledger forward-check passes — using #13 rows accrued
July–Sept, the ⭐ names that were top-3-by-RS12 on their day must have
outperformed the other ⭐ names over the same horizon. If promoted, the
change is: digest orders ⭐ rows by RS12 with the top-3 marked, PLAYBOOK
§3.4 becomes "split across the TOP 3 by 12-month relative strength (was:
equally across max 5)", copilot #31 allocates accordingly. Files:
daily_run.py (ordering/marking), PLAYBOOK.md, homily_ledger.py rank
column (ships NOW with no behaviour change so the forward-check has
data — S effort, next session).

**Update 2026-07-10 (rank column shipped):** `homily_ledger.py` gained
`rs12_ranks()` + a `rs12_rank` CSV column (appended at the end, per the
file's append-only-columns rule) — cross-sectional rank of a name's RS12
among that day's ⭐ ACCUMULATE candidates, falling back to 🔵 BOTTOMING on
a no-⭐ day, exactly mirroring `homily_selection_backtest._screen`'s
precedence. Non-candidates get a blank rank. Pure measurement: digest
ordering, copilot allocation and money movement are all unchanged; this
only makes sure the July–Sept ledger rows carry the rank data the
2026-10-01 forward-check needs. Gate: `homily_validate.py` check [25].
