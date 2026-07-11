# PRD — Danny-Cheng-style signal upgrade for homily-bot

**Date:** 2026-07-06 · **Owner:** gaoyan · **Status:** implementing

## 1. Goal

Upgrade homily-bot so its daily Telegram digest gives the *kind* of calls
[@dannycheng2022](https://x.com/dannycheng2022) posts: long-term
accumulate-on-dip guidance anchored on chip (cost-distribution) support and
resistance levels, on a fixed watchlist of conviction names — instead of the
current "RED=hold / WHITE=cut" regime flag that our own backtest shows
underperforms buy-and-hold.

## 2. Danny's methodology (from his public X posts)

| Pillar | What he does | Our approximation |
|---|---|---|
| Never trade | Long-term accumulate; signals time **adds**, never exits of core names | Signal states are ACCUMULATE / HOLD / CAUTION — no "sell" state |
| Fixed watchlist | NVDA TSM AVGO AMD ASML SOXL TSLA PLTR, charted weekly/monthly forever | IBKR holdings + ASML watch. SOXL excluded (3x leveraged) |
| "Chip system" (筹码) | Proprietary cost-distribution → support/resistance/reversal prices, dynamic POC updated daily+weekly | Volume-at-price histogram with exponential time decay (`homily_chips.py`) |
| Momentum bars | Longest horizontal bars in Panel 1 = accumulation shelves; close above them = momentum buy | Same histogram: top chip peaks below/above price |
| Colored candles | Red candle = short-term bullish, yellow = bearish | Daily EMA10 + MACD-hist state |
| Multi-timeframe | Monthly trend → weekly structure → daily entry | Monthly EMA10 trend + existing weekly circle + daily pullback test |
| Leverage | Margin amplification (his $800k→$3.6M claim) | **Deliberately NOT copied** |

Honesty constraints (non-negotiable, carried in digest):
- His exact indicators are proprietary ("can never be duplicated" — his words).
  This is an approximation of documented behaviour, not a clone.
- His returns are self-reported, unaudited, levered, and from one bull cycle.
  The bot never implies expected returns.

## 3. Signal spec

Per ticker, computed from ~2y daily OHLCV (Yahoo, key-free) resampled to
weekly/monthly:

1. **Monthly trend**: close > EMA10(monthly) and EMA10 rising → UP.
2. **Weekly circle**: existing `homily_circle` 4-factor engine (unchanged).
3. **Daily candle colour**: RED if close > EMA10(daily) and MACD hist > 0,
   YELLOW if both negative, else NEUTRAL.
4. **Chip context** (`homily_chips.py`):
   - histogram: each day's volume spread triangularly over its H–L range,
     weight decayed with 60-trading-day half-life (recent volume dominates);
   - **POC** = heaviest bin; **support** = top chip peaks below price;
     **resistance** = top peaks above; **% chips in profit**.

Composite state:

| State | Condition |
|---|---|
| ⭐ **ACCUMULATE** | monthly UP + weekly RED + price within 3% above (or at/below) a major chip-support peak |
| 🟢 **HOLD** | monthly UP + weekly RED, but extended above support (wait for pullback) |
| 🟡 **PULLBACK WATCH** | weekly AMBER while monthly UP — dip forming, watch chip support |
| ⚪ **CAUTION** | weekly WHITE or monthly trend down — pause adds (never "sell") |

Digest line (Danny voice):
`⭐ NVDA — accumulate zone 185–190 (chip peak), POC 172, resistance 211, 78% chips in profit, weekly RED 8w, daily red candle`

## 4. Deliverables

| File | Change |
|---|---|
| `homily_data.py` | NEW — daily OHLCV fetch (Yahoo v8, 2y/1d), weekly/monthly resample, stdlib only |
| `homily_chips.py` | NEW — decayed volume-at-price engine: POC, peaks, % in profit |
| `homily_danny.py` | NEW — composite state machine per §3 |
| `daily_run.py` | Digest rewritten per §3; ASML added as watch-only |
| `homily_danny_backtest.py` | NEW — accumulate-on-dip vs plain DCA avg-cost comparison (5y daily) |
| `homily_validate.py` | + chip-engine self-tests (POC correctness, no look-ahead) |
| `README.md` | Updated |

Unchanged: `homily_clone.py` weekly engine, `homily_refine.py` OOS-gated
refine loop, GitHub Actions schedule (09:00 SGT Mon–Fri).

## 5. Acceptance criteria

1. `python homily_validate.py` passes all tests including new chip tests.
2. `python daily_run.py` prints a digest with chip levels for every holding
   (Pop Mart 9992.HK included via Yahoo) and sends to Telegram when env set.
3. `python homily_danny_backtest.py` prints an honest avg-cost comparison of
   ACCUMULATE-gated buying vs same-budget DCA over 5y.
4. No new dependencies (stdlib only), no new secrets, workflow untouched.
5. Digest retains the standing disclaimer that signals are guidance, not a
   promise of Danny's returns.

## 5b. Addendum 2026-07-06 — volatility hole

Added on request: Danny calls the volatility hole "the most crucial and
important part of my technical analysis" for temporary topping/bottoming.
From his posts: a volatility-collapse spot printed as a zone with upper and
lower boundaries, valid until invalidated by either side; a close above the
upper boundary has preceded strong rallies (his SPY monthly study).

Implementation: `homily_vol.py` — a hole day is a new 60-day low in relative
volatility (ATR5/close); consecutive hole days form a cluster; the zone is
the cluster's high/low; status = BREAKOUT / BREAKDOWN / INSIDE from the
latest close. Composite gains a 🔵 BOTTOMING state (broken trend + upside
hole breakout) and a ⚠ topping note (uptrend + downside breakdown).

Event-study verdict (`homily_vol_backtest.py`, 8 names × 5y, no look-ahead):
breakouts beat baseline modestly (+4.4% vs +2.8% fwd 20d; +11.5% vs +8.5%
fwd 60d) — directionally supports Danny's claim. Breakdowns did NOT predict
weakness (+15.7% fwd 60d, above baseline) — so breakdowns are a warning
note only and never veto adds.

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

## 5k. Addendum 2026-07-11 — review of Danny's latest X posts → new plans #77–82

Owner request: mine Danny's recent posts for method details the bot doesn't
capture yet. Sweep covered June 2025 → June 2026 (X blocks direct fetch;
collected via search snippets, so quotes are post *openers* — full threads
unverified). What's genuinely new vs. what §2/§5b/§5h already cover:

| Post (date · ticker) | Claim | Disposition |
|---|---|---|
| [Apr 11, 2026 · SPY monthly](https://x.com/dannycheng2022/status/2042989378042236997) | "every volatility hole, once surpassed, has triggered a strong subsequent rally" — on the *monthly* chart, Dec 2013→now | Our VH engine is **daily-only** → **#77**, incl. a direct replication of this claim |
| [Feb 28, 2026 · COIN](https://x.com/dannycheng2022/status/2027685494122025180) | daily VH fired Feb 12 as early bottom signal, *then* the weekly confirmed | Same gap: multi-timeframe VH sequence → **#77** |
| [Jun 26, 2026 · KOSPI](https://x.com/dannycheng2022/status/2070229289417507220) | yellow candle ≠ bearish while the red ribbon unfolds; "the pullback usually takes 3 to 7 trading days before the next strong bullish candle" | A **testable duration claim** we've never measured → **#78** |
| [Sep 6, 2025 · LULU](https://x.com/dannycheng2022/status/1964177009854337528) | his actual **sell** anatomy: monthly lower-highs/lower-lows + *declining* whale accumulation + momentum bars breached below ($329/$313) | We model whale *accumulation* only (§5h); no distribution tell exists → **#79** |
| [Jun 26, 2024 · MARA vs WULF](https://x.com/dannycheng2022/status/1805828960787513768) | between two similar names, the whale-accumulation gap (94% vs low) decided the winner | Cross-sectional selection — the **R2 lever** → **#80** |
| [Jun 18, 2024 · PLTR](https://x.com/dannycheng2022/status/1802940053582463114) | "whales on the daily chart have been playing tricks… I track them on the weekly" (his 2026 charts are overwhelmingly weekly/monthly) | Our 🐳 footprints are daily → **#81** |
| [Mar 20, 2026 · PLTR](https://x.com/dannycheng2022/status/2034813250815304023) | "Never simply follow red or yellow candles" — VH outranks candle colour | Already our hierarchy (§5b: 🔵 overrides broken trend); no action |
| Red/blue **ribbon** posts (PLTR weekly; [NIO Jul 2024](https://x.com/dannycheng2022/status/1810141974454014139)) | big red candles open bullish runs "lasting weeks to months"; blue ribbon = protracted downtrend | Run-length is measurable and would calibrate how long an ⭐ window typically stays open → **#82** |
| [Apr 2026 · no-FOMO](https://x.com/dannycheng2022/status/2046270349265011162) | "not feeling FOMO on this recent high… next time whales offer a bigger discount, that's when I'll FOMO in" | Already the HOLD state + #50 tranches; no action |

**Considered and rejected** (logged so nobody re-derives them): measured-move
price targets ([AMZN inverse-H&S → $300, May 15 2026](https://x.com/dannycheng2022/status/2055204797138284708)) — subjective pattern
anchoring; he himself mocked pattern-callers three weeks earlier
([SPX Apr 16](https://x.com/dannycheng2022/status/2044598238964269146): "nobody owns a crystal ball"), and printing price targets breaks
the §2 honesty constraints. Leverage-on-discount posts — §7 stands. His
speculative small-caps (ONDS IBRX CLSK) — universe stays rule-governed per
#65; G1 liquidity gates exist precisely to not chase these.

## 6. Improvement backlog (queued for next runs)

Ranked; each item should ship with its own honest validation before the
digest starts trusting it. *(2026-07-06: #1–12 are absorbed into the §8
roadmap phases — kept here for numbering continuity, referenced as #n.)*

1. **Backtest the conviction score** — replay 5y point-in-time (gates +
   score each day, no look-ahead), report forward 6m/12m returns by score
   decile and tier. Until then the 🚀 tier is a shortlist, not an edge.
2. **Real market cap** — replace the dollar-volume proxy in G1 (Yahoo crumb
   auth, or a monthly-refreshed static map committed to the repo).
3. **State-change alerts** — a second, tiny Telegram message only when a
   name CHANGES state (⭐ appears, 🔵 fires, hole resolves) so the signal
   isn't buried in the daily wall.
4. ~~**Fundamental overlay for 🚀**~~ — **DONE 2026-07-06** (`homily_fund.py`):
   EDGAR companyconcept, 3 checks (revenue growth >10% / NI>0 or OCF>0 /
   dilution <12%), `F:n/m` tag on 🚀 + discovery rows, info-only by design
   (fundamentals gate the universe & the hold-through-CAUTION decision, the
   tape gates money flow — Danny's lag point respected). 7-day cache
   committed by workflow; non-US names print `F:—`.
5. **Supervised Homily fit** — if the user exports real red/white-circle
   readings from a Homily terminal, fit the clone against actual labels
   (the only path that truly converges to Homily).
6. **Universe hygiene** — quarterly review: drop names that lost liquidity,
   auto-flag new liquid IPOs passing G5 for manual inclusion.
7. **Earnings awareness** — flag rows with earnings inside 7 days (dates via
   free sources are flaky — validate coverage first).
8. **HK depth** — 9992.HK chip profile is HKD-denominated and thinner;
   consider SEHK-specific volume normalisation before trusting HK zones.
9. **Weekly deep-dive** — Sunday digest: full chip histogram sparklines per
   holding, conviction score drift over the week, refine-log summary.
10. **Annual strategy re-test** — re-run `homily_strategy_backtest.py` each
    July as new out-of-sample data accrues; also add a delisted-inclusive
    universe if a free point-in-time constituent source is found.
11. **Auto-sync holdings from IBKR** — holdings live in `holdings.json`
    (manual edit / synced via IBKR MCP in Claude sessions; last sync
    2026-07-06 — dropped BABA, added DRAM 87sh + MU). The Actions bot
    cannot use MCP (chat-only connector); true automation = IBKR **Flex
    Web Service** (user enables a Flex Query for positions in Client
    Portal → token + queryId as repo secrets → fetch at run start).
    Until then: tell Claude after trades, or edit holdings.json.
12. ~~**Whale-accumulation pattern**~~ — **DONE 2026-07-06**
    (`homily_whale.py` + gate `homily_whale_backtest.py`, addendum §5h):
    🐳 = dip + ≥2 of 3 footprints (absorption print / OBV-A/D divergence /
    shelf replenished). Gate PASSED on the combined 58-name universe incl.
    2021 wrecks → ⚪+🎯+🐳 promoted to the WHALE-DIP discretionary tier
    (≤2% of account, same budget, 10% hard cap). The PLTR June case
    reproduces point-in-time (🐳 fires Jun 26-30 at the 113-119 shelf).
    Closes roadmap item 22 (⚪ arm; the 🟡 variant untested — 🎯 on 🟡
    keeps its existing discretionary framing).

## 7. Out of scope

Leverage/margin signals; options; SOXL; auto-trading via IBKR; copying his
paid Patreon content; any claim of replicating Homily's or Danny's
proprietary formulas.

## 8. Roadmap 2026H2 — the full plan (added 2026-07-06, execution deferred)

Everything queued, organised into phases by *which lever it actually pulls*.
Items #1–12 from §6 are absorbed into these phases (referenced as #n). This
section is the spec; nothing here is built yet.

### 8.0 What actually moves returns here (read before picking an item)

Our own backtests already rank the levers — the plan honours that ranking
instead of chasing more indicators:

| Lever | Evidence | Phase |
|---|---|---|
| **R0 Executing the monthly routine at all** | PLAYBOOK §8: savings rate + discipline dominate any indicator change we will ever ship | E |
| **R1 Not corrupting the signal we already have** | one bad Yahoo fetch, an unnoticed split, or a bug shipped before self-tests poisons every level the digest prints | B |
| **R2 Cross-sectional selection** (which names get the ⭐ money) | THE test (§5f): the edge came from selection + never-sell (2.10× on the control), NOT entry timing — per-name ⭐-waiting *lost* to DCA on every name | C |
| **R3 Portfolio shape** (concentration, caps, buckets) | §5g: emergent concentration beat the engineered core-4 by −30% vs −68% MaxDD; today's book is essentially one correlated AI/semi trade and nothing measures it | D |
| **R4 Entry-timing refinements** | smallest measured lever; VH bullish edge is modest, whale tag gated + promoted 2026-07-06 (§5h) | C (gated) |

Implication adopted: execution (E) and integrity (B) outrank another timing
signal every time. "Maximise returns" = maximise *executed, risk-shaped
exposure to the validated edge* — not more signals.

Standing rules for every item below:

* point-in-time backtest with the hype-2021 control before anything gates
  money; ships info-only until promoted (the #12 pattern);
* **one live-behaviour change at a time**, 90 ledger-days between promotions
  of anything that redirects money;
* stdlib-only / no-server / no-secrets constraints stand, except items 37–38
  which relax them *deliberately and reversibly*;
* every shipped item adds a `homily_validate.py` test + an honesty line in
  README if it touches the digest.

Effort tags: S = one sitting · M = 1–2 days · L = multi-day.

### Phase A — measure first: the live track record (keystone)

The bot has honest *backtests* but no *live* record of its own calls. Fix
that before improving anything, or improvements are unmeasurable.

13. **Signals ledger** (S) — `homily_ledger.py`: every run appends one row
    per screened name to `homily_signals_log.csv` (committed by the
    workflow like the refine log): date, ticker, held?, close, state, zone
    lo/hi, POC, %-in-profit, weekly circle/score/weeks, monthlyUP, VH
    status, 🐳 bools, conviction score + failed gates, F-tag. Idempotent per
    (date, ticker) — re-runs overwrite, no dupes (the refine log currently
    logs 12 rows on a 12-run day). Also emits `docs/snapshot.json` — full
    structured state for the dashboard track (F) and for Claude sessions to
    answer questions without refetching. Append-only history = point-in-time
    by construction, no look-ahead. Everything in phases C–F consumes this.
    **Gate:** none (pure measurement).
14. **Live out-of-sample scorecard** (M; needs 13 + ~3 months of rows) —
    monthly digest section + docs page: forward 1/3/6-month returns of every
    past ⭐/🔵/🚀 row vs same-day SPY, split by state and by conviction
    decile. Converts "promising, not proven" into an accruing live record —
    THE credibility artifact, and the referee for every later promotion.
    **Gate:** n/a — it *is* the gate for everything else.
    **Spec addition 2026-07-11:** the scorecard also carries MaxDD and
    worst-rolling-12m vs the same-cash counterfactual (§5i's verdict:
    every arm ran 2–3× index drawdown — a returns-only scorecard would
    hide exactly the failure the bar exists to catch), plus #70's
    coverage % and #71's noise band. §9.0's north-star wording is
    unchanged; this is how it gets *reported*, not a new metric.
15. **State-change alerts** (#3) (S; needs 13) — diff today's ledger vs
    yesterday's; send a second, tiny Telegram message ONLY on transitions
    (⭐ appears/lapses, 🔵 fires, 🐳 appears, 🐂/🐻 flips, 🚀 enters/exits).
    Quiet day = no second message; the signal stops drowning in the wall.
    **Gate:** none (delivery only).
64. **Universe-entry provenance** (S; ships with or right after 13) — every
    `UNIVERSE` / `WATCH` entry carries an `origin`: `screen` (arrived by a
    mechanical liquidity/G5 rule) or `owner-request` (added on request —
    today: D05.SI, IBIT, ETHA per §5c; arguably the whole pre-#44 list).
    `homily_ledger.py` logs it per row; 14 splits the scorecard by it.
    Rationale: §8.0 makes 14 the referee for every later promotion, but the
    universe is a discretionary list (§5c/§5f — the 3.69 MOIC number is
    hindsight-biased *because* of how these names were chosen). Without the
    field, an ⭐ on an owner-requested name and an ⭐ on a screened name enter
    the live record indistinguishable, and the referee inherits the
    selection bias it exists to detect. Does not make inclusion rule-based —
    that needs point-in-time constituents and stays blocked behind 45 — it
    makes the bias *visible and measurable* in the meantime, which is the
    part that isn't blocked. **Gate:** none (labelling only; no live
    behaviour changes). **Note:** if the two origins later diverge
    materially in the scorecard, that is evidence *for* prioritising 44/45,
    not a reason to drop names by hand.
70. **Missed-run detector** (S; rides 13) (added 2026-07-11) — each run
    compares the ledger's last row date against the trading calendar since;
    a gap prints one digest line ("⚠️ no ledger rows for 2026-07-08 —
    runner missed, live record has a hole") and `docs/snapshot.json` gains
    a `coverage` field that 14 reports alongside its returns. Rationale:
    #16 catches a run that *fails*; nothing catches a run that never
    *starts* — and a track record with silent holes is biased toward the
    days the infra was healthy, which corrupts the referee exactly like
    backfilling would (R3's mirror image). **Gate:** none (measurement);
    validate fixture with a planted gap.
71. **Scorecard power line** (S; rides 14, reuses D-39 bootstrap
    machinery) (added 2026-07-11) — before the first #14 read, pre-register
    how many ledger-months a given size of live edge needs to be
    distinguishable from noise (block-bootstrap the null on the same-day
    SPY counterfactual rows) and print it on the scorecard itself:
    "n=214 rows over 2.5mo — noise band ±6.2 pts; edges inside the band
    are unreadable before ~2027-01". Protects the referee in BOTH
    directions: no promoting on three lucky months, no demoting on three
    unlucky ones. The band's method is frozen before the first read so it
    can never be re-fit to make a result significant. **Gate:** the
    calculation itself.

### Phase B — protect the signal (integrity before intelligence)

16. **Self-tests gate the send** (S) — the workflow currently runs
    `daily_run.py` (which sends) *then* `homily_validate.py`: a broken
    engine ships its digest, then fails CI. Reorder: validate → digest. On
    failure send one line — "⚠️ digest suppressed, self-tests failed" — so
    silence is never ambiguous. **Gate:** none.
17. **Fetch hardening** (M) — `homily_data.py` has no retry, no fallback,
    and ~75 sequential 5y fetches per run. Add: retry with backoff + jitter,
    query1/query2 host rotation, `ThreadPoolExecutor` (stdlib) fan-out,
    Stooq daily CSV as key-free fallback (rows tagged `src:stooq` when
    used), and a partial-digest banner ("screened 61/71 — fetch failed:
    …") instead of a silent short list. **Gate:** validate test with a
    mocked flaky fetch.
18. **Total-return correctness** (M) — all return math (RS12/G3, THE test,
    scorecard) uses raw closes: dividends are invisible, so payers (V MA
    COST LLY NVO, SPY itself) are systematically docked vs zero-div growth
    names. Parse `adjclose` from the same Yahoo response; use it for ALL
    return/RS computations; keep raw OHLC for chip levels (levels must be
    tradeable prices). Re-run G3 both ways and publish the delta.
    **Gate:** validate test: NVO RS12 (raw) < RS12 (adj); backtest tables
    regenerated with a footnote.
19. **Corporate-action sanity check** (S) — a mis-adjusted split poisons the
    chip histogram and every level printed for weeks. Detector: |1-day
    move| > 45% on a volume spike → suppress that name's chip levels for the
    day ("levels suspended — corporate action?"), keep the state row.
    **Gate:** validate test on a synthetic 10:1 split series.
69. **Promotion lifecycle registry + rs12 forward-checker** (S–M) (added
    2026-07-11) — the promotion machinery is currently prose scattered
    across §5h/§5j/R10; make it mechanical. Committed `promotions.json`:
    one entry per gate-passed candidate — the pre-registered rule
    verbatim, gate date + artifact (backtest file, BACKTEST_RESULTS
    section), earliest promotion date, the forward-check criteria, AND a
    **demotion rule written the same day**. Ships now with the rs12-top3
    forward-checker as executable code (reads #13 rows, computes forward
    returns of top-3-by-`rs12_rank` ⭐ names vs the other ⭐ names, prints
    PASS/FAIL against the frozen criteria) so the 2026-10-01 decision is
    a program's output, not a fresh judgment call made three months from
    now with the result already visible. Standing rule adopted with this
    item: **nothing is promoted without a pre-registered demotion rule in
    the registry** (e.g. rs12-top3, if promoted, demotes back to
    equal-split when top-3 rows underperform other-⭐ rows over a rolling
    6-month ledger window — exact figure frozen in the registry entry
    before promotion). A promoted signal that stops working leaves by
    rule, not by debate — that, not refusing new signals, is how the
    algorithm stays uncluttered. **Gate:** none (guard infra, the #61/#62
    pattern); validate asserts every entry names its gate artifact.
75. **Snapshot schema contract** (S; rides 13/36, blocks T3) (added
    2026-07-11) — `docs/snapshot.json` is read by the dashboard (36),
    Claude sessions, and eventually the T3 order routine — the first
    consumer for whom a silently renamed field costs money. Add `"_v"`
    to the snapshot, a validate check pinning the buy-day block's
    required fields and types, and one more T3 hard guardrail in §9.2:
    the routine refuses to act on a schema version it doesn't know.
    **Gate:** validate contract test.

### Phase C — make the scores mean something (selection quality, R2)

20. **Conviction-score backtest** (#1, elevated) (L) — point-in-time daily
    replay 5y, both universes (current + hype-2021 control): gates + score
    each day, no look-ahead; report forward 6m/12m by score decile, tier
    hit-rates (2×/5×/10× within 24m), and the wreck list the gates let
    through. Promote/demote score weights only if OOS deciles are
    monotone-ish; if flat, the 🚀 section gets relabelled "shortlist, no
    measured edge" in the digest footer. **Gate:** the backtest itself.
21. **Re-point the daily refine loop** (M) — quiet misalignment: the loop
    tunes circle params for hold-🔴/cut-⚪ Calmar — a strategy §1 retired.
    The circle's actual job is *gating composite states*. New objective:
    walk-forward score = mean forward-60d excess return of days the param
    set would print ⭐, minus a false-block penalty (⚪ days followed by
    ≥+15% in 60d — the PLTR June class). Same OOS-adoption margin as today.
    Run both objectives in parallel for 30 days (log-only) before switching
    the champion's meaning. **Gate:** parallel-run comparison in the log.
22. ~~**Whale gate**~~ — **DONE 2026-07-06** with #12 (§5h): the ⚪ arm was
    tested and PROMOTED (`homily_whale_backtest.py`). Residual: the 🟡+🐳
    variant is untested — fold it into the confluence studies (23).
23. **Confluence studies** (M; cheaper once 13 accrues) — three one-table
    questions: 🔵+🐳 vs 🔵 alone; ⭐+F:3/3 vs ⭐+F:0; fresh ⭐ (first week)
    vs stale ⭐. Adopt at most ONE new modifier per quarter — degrees of
    freedom are the enemy. **Gate:** each table, control included.
24. ~~**⭐ overflow ranking**~~ — **GATE PASSED 2026-07-10** (§5j,
    `homily_selection_backtest.py`, BACKTEST_RESULTS §4): `rs12-top3`
    beat equal-all, alpha-top5 AND random-5's p90 on all three honest
    control windows; crossed QQQ in the fully honest 2021→2026 window.
    Promotion deferred to ≥2026-10-01 (R10; 🐳 took Q3's slot) and gated
    on the #13 ledger forward-check. Interim ship (no behaviour change):
    RS12-rank column in the ledger so the forward-check has data.
25. **Real market cap** (#2) (S) — replace the $-volume proxy in G1 with a
    monthly-refreshed static map committed to the repo (curated from public
    sources; ~60 names is 10 minutes of maintenance) + a staleness warning
    in validate. Kills the known over-counting of hot momentum names.
    **Gate:** spot-check vs three known caps in validate.
26. **Breadth canary** (S, info-only) — % of universe above 200d SMA and %
    weekly RED, one line under the regime banner when <30% ("hostile tape —
    historically poor month for new adds"). Never gates anything until a
    year of ledger data says it should. **Gate:** info-only by design.

### Phase D — portfolio & risk lens (returns are portfolio-level, R3)

27. **Position-aware digest** (M) — extend `holdings.json` to
    `{symbol, shares, cost}` (`"_v": 2`; synced via IBKR MCP in Claude
    sessions until #11/32 automates it). Unlocks: per-name % of stock book
    printed on its row, automatic Bucket A/B/C classification per PLAYBOOK
    §1 (earned vs bought via cost basis + ledger add-history), and 10%-cap
    proximity warnings ("NVDA 9.4% — next add breaches the cap").
    **Gate:** validate test on a fixture book.
28. **Trim-rule flags** (S; needs 27) — PLAYBOOK §5 becomes executable
    flags, not prose: "⚠️ RULE 1: RDDT 12% — bought-not-earned, trim to
    10%"; "⚠️ RULE 2 REVIEW: ZETA ⚪ 13w + F:1/3 — sell-half rule". Flags
    only — there is still no SELL state; the PRD §1 principle survives.
    **Gate:** rules mirror PLAYBOOK §5 verbatim; validate fixtures.
29. **Concentration / correlation lens** (M) — 90d daily-return correlation
    across held names (stdlib), greedy clustering, one digest line: "book
    clusters: AI/semis 68% (NVDA AMD AVGO TSM MU DRAM VST) · software 14% ·
    other 18%" + a warning when a ⭐ add would deepen a >60% cluster
    ("⭐ MU deepens the 68% cluster — non-cluster ⭐ first per §3").
    Info-only, but this is the highest-expected-value risk feature in the
    plan: the current book is one trade wearing 15 tickers.
    **Gate:** correlation math test; info-only.
30. **Bear-readiness line** (S; needs 27) — first-Monday digest: satellites%
    vs core%, margin=0 confirmation, and the pre-computed 🐻 sell list in
    PLAYBOOK §4 order ("if 🐻 fired tomorrow you would sell: …"). The bear
    playbook stays rehearsed instead of theoretical. **Gate:** none.

### Phase E — execution copilot (R0 — the highest-ROI phase in the plan)

31. **Buy-day copilot** (M; needs 27) — on the first trading day each month
    (SGT), the digest leads with a 🛒 BUY DAY section: the ⭐ list resolved
    into exact orders from `BUY_BUDGET_USD` (repo *variable*, not secret):
    50% → Bucket A per §3, remainder equal-split across ⭐ (max 5),
    respecting the 10% cap (27), cluster warning (29), F-preference; prints
    IBKR-ready lines — "BUY 3 TSM @ mkt (~$1,302)". No ⭐ → "full amount →
    Bucket A" per §3.5. Turns the 10-minute routine into 2. **Gate:**
    fixture test: budget in → orders out, caps respected; info-only (it
    prints orders, never places them — §7 stands).
32. **IBKR Flex auto-sync** (#11, unchanged) (M) — Flex Web Service token +
    queryId as secrets → positions fetched at run start → feeds 27 without
    manual syncs. Fallback stays: tell Claude after trades / edit the JSON.
33. **Sunday deep-dive** (#9, now concrete) (M; needs 13, 36) — weekly
    edition = the F2 dashboard regenerated + one summary message: per-holding
    state timeline (12w), conviction drift, distance-to-zone, the week's
    🐳/VH events, scorecard refresh (14). Replaces "more text" with the
    dashboard link/file.
72. **Buy-day execution reconcile** (S–M; needs 27, sharper once 32
    lands) (added 2026-07-11) — the first run after buy day diffs
    holdings against the basket the copilot printed: "🛒 reconcile:
    executed 4/5 — TSM 3sh missing (~$1,302 undeployed)". Prints daily
    until the book reflects the basket or the month ends; each month
    closes with one executed-n-of-m row that feeds #58's behaviour-gap
    tracker. Pure R0: §9.0 says an unexecuted signal has zero alpha —
    this is the instrument that notices, and the T2→T3 promotion gate
    ("two consecutive months executed verbatim", §9.2) gets measured by
    it instead of by memory. **Gate:** fixture test (basket + holdings
    in → reconcile line out).

### Phase F — frontend: from wall-of-text to glanceable

Phased so each step is useful alone and the no-server rule is only relaxed
at the step that truly needs it.

34. **F0 — digest typography v2** (S) — switch sends to Telegram HTML parse
    mode (kills the Markdown-entity fallback class of bugs in
    `daily_run.py send()`); align rows in `<pre>` blocks; unicode chip
    sparklines per row (`▁▃█▅▂` with a price marker — the histogram in 8
    chars); fold the legend + algo-health footer into an expandable
    blockquote so the actionable digest is ~10 lines tall. **Gate:**
    validate test for HTML entity escaping.
35. **F1 — chart cards, stdlib PNG** (M) — `homily_png.py`: a pure-stdlib
    PNG writer (`zlib` + `struct`, filter-0 scanlines, ~200 lines) drawing
    1y price + zone/POC/res bands + chip-histogram side panel + state
    ribbon; `sendPhoto` (multipart via urllib) the top-3 actionable names
    (⭐/🔵/🎯) daily. The digest becomes glanceable without any dependency
    or host. **Gate:** deterministic pixel-hash test on fixture bars.
36. **F2 — daily dashboard, self-contained HTML** (L; needs 13) —
    `homily_dashboard.py` renders `docs/dashboard.html` nightly: inline-SVG
    interactive (hover = values, zero external assets): every holding's
    card (price + levels + chip histogram), ledger state-history heatmap,
    scorecard tables (14), conviction drift, refine log chart, and an
    **alerts timeline** (every #15 state-change alert ever sent, newest
    first, reconstructed from ledger diffs — so a missed Telegram ping is
    recoverable and the alert history is auditable in one place; owner
    request 2026-07-10). Committed by
    the workflow AND sent via `sendDocument` — private in the chat, one tap
    to open, works offline, repo stays private, nothing hosted. **Gate:**
    HTML self-containment test (no external URLs) in validate.
    *Owner note 2026-07-10: the charts UI (#35 chip-chart cards + this
    dashboard) is explicitly wanted — keep #35 next in the Month-1 queue
    after #18/#19, and treat #36 as the Quarter item's centrepiece.*
37. **F3 — Telegram Mini App** (L; *deliberate no-server relaxation*; only
    if 2 weeks of F2 shows file-open friction) — host the same dashboard
    behind Telegram WebApp auth: Cloudflare Pages + a tiny Worker verifying
    `initData` HMAC against the bot token, allowlisted to your chat_id;
    the digest gains a persistent "📊 Open dashboard" inline button.
    Costs: CF account, one secret, a deploy step. Revisit §7 wording first.
38. **F4 — interactive commands** (parked) — `/why NVDA`, `/size 2500`
    answered by the same Worker reading `docs/snapshot.json` via the GitHub
    API. Parked until F3 proves its keep; explicitly NOT a trading surface.
73. **Digest line budget** (S) (added 2026-07-11) — a hard cap on
    actionable digest lines (~12 above the fold; overflow prints tickers
    only), enforced by a validate check counting lines in the #49 golden
    digests. Standing rule adopted with it: a new digest feature must
    displace an existing line or live on the dashboard (36) — additive-
    only growth is how the wall-of-text happened, and a budget the CI
    enforces is worth ten style intentions. **Gate:** golden-file line
    count in validate.

### Phase G — research queue (one per quarter, July re-test cadence)

39. **Bootstrap CIs on THE test** (M) — block-bootstrap the monthly returns
    of strategy vs DCA (stdlib `random`); publish 5–95% MOIC bands. Turns
    "one window" into a distribution honestly. **Gate:** the CI table.
40. **Annual re-tests** (#10) (M, every July) — strategy/core-4/emergent
    re-runs + NEW: live-vs-sim reconciliation once 14 has a year of data
    (does the live scorecard match what the backtest promised? divergence =
    the overfit alarm).
41. **Supervised Homily fit** (#5) (L, blocked on user exporting real
    red/white labels from a Homily terminal).
42. **Earnings windows** (#7) (M) — approximate next report as last
    10-Q/10-K date + ~91d from EDGAR `submissions` (already used by
    `homily_fund.py`); tag rows "≈E-week" ±7d, US names only; validate
    coverage before trusting; never gates, informs sizing restraint.
43. **HK depth** (#8) (M) — SEHK volume normalisation before trusting
    9992.HK / 0700.HK chip zones; until then HK rows carry "levels
    lower-confidence" — plus DRAM proxy note: MU appears both as holding
    and constituent by design.
44. **Universe hygiene automation** (#6) (S) — quarterly workflow opens a
    GitHub issue with candidate adds (new liquid names passing G5) and
    drops (liquidity lost), instead of relying on memory. Note this keeps a
    human in the inclusion loop by design; names it adds are still `origin:
    owner-request` per 64 until the rule itself decides.
45. **Delisted-inclusive control** (#10b) (L, blocked on finding a free
    point-in-time constituent source) — the last big survivorship hole. The
    same missing source blocks rule-based *live* universe construction; 64
    measures the resulting bias while this stays blocked.

### 8.1 Suggested execution order (for the execution days)

| When | Items | Why this order |
|---|---|---|
| **Week 1** (one sitting each) | 16 · 13 · 64 · 15 · 34 | send-safety first; ledger starts accruing (every week of delay = a week less live evidence); 64 rides along with 13 because a row logged without `origin` can never be back-filled honestly; alerts + readable digest are free wins on top |
| **Month 1** | 17 · 18 · 19 · 31 · 35 | pipeline hardened, return math honest, buy-day copilot live for the next monthly buy, first chart cards |
| **Quarter** | 20 · 21 · 22 · 25 · 27 · 28 · 29 · 36 | scores validated, refine loop re-pointed, portfolio lens on, dashboard shipping nightly |
| **Gated / ongoing** | 14 (first read at 3mo) · 23 · 24 · 26 · 30 · 32 · 33 · 37 · 38 · 39–45 | each unlocks as its dependency (ledger months, position data, F2 usage) matures |

*Slotting for the 2026-07-11 additions (#68–75):* **69 has a deadline** —
the rs12-top3 forward-checker must be frozen well before the 2026-10-01
read, so it goes next-but-one after the current session (68 rides the same
session: the checker should be built on total-return math, which is what 68
migrates). 70 and 73 are S-effort free wins that ride the next
digest-touching session; 71 ships with 14's build; 72 after the first T2
month produces a basket; 75 with the next change that touches
snapshot.json; 74 waits in the #23 research queue under the R10 budget.

*Slotting for #77–82 (§5k, Danny latest-posts review):* only one piece is
time-sensitive — **#80's `whale_rank` ledger column** must ship before the
July–Sept rows accrue or the 2026-10-01 #24 read can't include the whale
challenger; it rides the same ledger-touching session as #69 (identical
pattern to §5j's rs12_rank column, S effort, no behaviour change). The
#80 study itself runs at the October read alongside rs12-top3. #79 is the
highest-value study of the batch (it feeds #28's trim flags and #51's
time-stop with a tape-based reason) and takes the next open research slot
after #74 in the #23 queue. #77 and #81 are R4 timing modifiers competing
for the same R10 one-per-quarter budget — run at most one per quarter,
whichever the #23 harness reaches first. #78 and #82 are S–M info-only
studies that ride any session already touching the backtest harnesses;
they change digest text only if their distributions hold up.

### 8.2 Explicitly NOT in this plan

Leverage/margin, options overlays, intraday data, auto-execution, paid data
feeds, ML black-boxes (any model whose reasoning can't be printed in a
digest footer), and any new timing signal without a control-salted
point-in-time gate. §7 stands in full.

### 8.3 Extended idea bank #46–60 + deep designs (added 2026-07-06 late)

Full text in **`DESIGNS.md`**: Part I = design decisions for the hard items
(#20 replay protocol + pre-committed decision rule · #21 new refine
objective with false-block penalty + sample-size diagnostic · #24 three-way
ranking test · #29 clustering algorithm · #31 allocation algorithm incl. HK
board lots + ledger-based buy-day detection · #34–36 frontend architecture
decisions · #39 block-bootstrap spec). Part III = the execution handoff
protocol for whichever model builds this. Part II = idea bank, indexed here
(unvetted; every one gated; #61–62 = EXECUTION.md guards, #63 = bear-regime
rethink below, #64 = universe-entry provenance (Phase A), #65 =
mechanical universe construction below, #66 = right-stock discipline
below (owner-requested 2026-07-10), #67 = hard-rule provenance audit
below (owner-requested 2026-07-10), #68 = total-return backtest migration
(§8.5; renumbered 2026-07-11 from a duplicate "64"), #69–75 = 2026-07-11
protect-the-referee / execution additions in Phases A/B/E/F plus #74
below, #76 = planning-doc pruning below, #77–82 = Danny latest-posts
review below (§5k, owner-requested 2026-07-11), new proposals start #83):

| # | Idea | Effort | Gate |
|---|---|---|---|
| 46 | Turnover-adaptive chip decay | M | must beat fixed half-life on #47's hold-rate metric OOS |
| 47 | Shelf hold-rate statistic ("held 7/9 touches") | M | is itself an event study; ≥8 touches; info-only |
| 48 | Ancient-shelf overlay (240d half-life profile) | S–M | bounce event-study vs recent shelves |
| 49 | Golden-file digest tests — **build first on execution days** | S | none (test infra) |
| 50 | Staged-add tranches (shelf / −7% / −14%) | M | avg-cost + MOIC vs single-add and DCA, both universes |
| 51 | ⚪ time-stop study (calibrate PLAYBOOK §5.2's 12w rule) | M | the study itself; PLAYBOOK edited only after |
| 52 | Inverse-vol sizing within stars | S–M | THE-test rerun; expect a null per §5g |
| 53 | SGD lens (book return in SGD, USDSGD trend) | S | info-only |
| 54 | Weekly "what changed" ledger diff | S | needs #13 |
| 55 | Breadth cross-check (RSP vs regime; "narrow tape" note) | S | 20y event check or drop |
| 56 | AI analyst memo (weekly cloud-agent process-QA PR) | M | 4-week trial; keep only if it catches a real issue |
| 57 | 中文 digest toggle (筹码/主力 native terms) | S | none (presentation) |
| 58 | Behaviour-gap tracker (perfect-PLAYBOOK shadow book vs real) | M | none (measurement) — prices the discipline gap |
| 59 | Flash-crash pre-script (SPY 5d < −7% psychology note) | S | none (info-only) |
| 60 | Data-QA cross-check (freshness/Stooq-agreement asserts) | S | validate tests; feeds #17 |
| 63 | **Bear-regime rethink** — decompose the 🐻 sell step (owner-requested 2026-07-08; full design **D-63** in DESIGNS.md Part I) | M | pre-committed decision rule in D-63; PLAYBOOK §4 edited only per that rule — **RESOLVED 2026-07-10**, see §5i |
| 65 | **Mechanical universe construction** (owner-requested 2026-07-10; full design **D-65** in DESIGNS.md Part I) — L0 NASDAQ-Trader symbol master → L1 liquidity gates ($5+, $50M/d median, 130+ bars) → L2 top-~120 capacity cut + holdings + recent-🚀 stickiness; quarterly refresh via #44's issue; committed `universe.json` with per-name `origin`; non-US stays owner-request; adds a rule-stated *mechanical-2021* control to #40 re-runs | L | one shadow quarter in the ledger: keeps ≥90% of hand-list ⭐/🔵/🚀 names AND surfaces ≥1 setup the hand list missed; #14 splits scorecard by origin either way |
| 66 | **Right-stock discipline** (owner-requested 2026-07-10, Danny's "right stocks, add aggressively on pullbacks, hold" principle; full design **D-66** in DESIGNS.md Part I) — sticky per-name quality tier Q (quarterly, fundamentals-led, no tape feedback) + 💎 quality-dip row for Q1 names parked in ⚪ by drawdown alone + thesis-break VETO on the aggressive dip-add paths (🎯-on-🟡, WHALE-DIP, #50 tranches) | M–L | wreck-list separation replay per D-66 (2021 control must separate from the recovered greats); 💎 stays info-only until it beats both DCA and unfiltered-⚪ dips OOS; the veto ships on the weaker net-block-count standard |
| 74 | **缩量 dry-up dip tag** (added 2026-07-11) — Danny's healthy-pullback tell: a dip day on *contracting* volume (20d avg vs 50d avg) is accumulation-friendly; the same dip on expanding volume is distribution. Rides #23's confluence-study harness (⭐/🎯 dips split by dry-up vs expansion); counts against the one-modifier-per-quarter budget (R10); no digest tag ships before promotion | M | event study, both universes incl. 2021 control; null → closed honestly, nothing ships |
| 76 | **Planning-doc pruning** (added 2026-07-11, token optimization) — PRD/DESIGNS/SPECS/EXECUTION have grown past ~2,000 lines combined and every session pays that context cost. Compact them: move resolved addenda (§5c–5j), shipped-item designs, and §8.5 execution notes to `docs/archive/` (archived verbatim, never deleted — provenance intact); collapse shipped idea-bank rows to one-line pointers; keep numbering continuity. Live docs keep only what a future session needs to act | S | docs-only — validate green, goldens untouched, every archived section reachable via a pointer from where it used to live |
| 77 | **Multi-timeframe volatility hole** (owner-requested 2026-07-11, from Danny's latest posts — §5k) — run `homily_vol.py` hole detection on weekly and monthly resamples; his claimed sequence is daily VH = early tell, weekly/monthly = confirmation (COIN Feb 2026), and his SPY-monthly study claims a perfect breakout record since Dec 2013. Deliverable includes a **direct replication table of that SPY claim** — if it doesn't replicate on our approximation, that's a §8.5-worthy finding on its own | M | event study of weekly-VH breakouts, both universes incl. 2021 control, vs the daily-VH baseline from `homily_vol_backtest.py`; info-only until promoted; R4 timing → counts against the R10 one-modifier-per-quarter budget |
| 78 | **Pullback clock** (from §5k, KOSPI Jun 26 2026) — Danny: within an intact red ribbon a pullback "usually takes 3–7 trading days". Measure the actual distribution of dip durations (consecutive non-RED daily candles) inside intact weekly-RED spells, per universe; if a stable band exists OOS, 🟡 rows gain "dip day 4 (typ. 3–7)" and a dip running past ~p90 duration becomes a data-driven trend-failure early warning (feeds #51's time-stop thinking at daily scale) | M | the study itself; digest line ships only if the duration band is stable across both universes and OOS halves; info-only |
| 79 | **Whale-distribution warning** (from §5k, the LULU sell anatomy) — the inverse of #12's footprints: rallies absorbed (up-day closes weak at shelf resistance), OBV-A/D *negative* divergence, support shelf eroding instead of replenishing, plus monthly lower-highs/lower-lows. Scope guard: prints ONLY on held satellites / Bucket-B rows and as a veto input to 🚀 candidacy — core names and the index never get a sell tag (§1 principle stands). Feeds #28's trim-rule flags and #51's time-stop as an evidence line, replacing gut feel with a tape reason | M | event study incl. 2021 control: does the tag predict forward 60/120d underperformance vs sector-matched baseline? Honest precedent: VH *breakdowns* were null (§5b) — if this is null too, closed, nothing ships |
| 80 | **Whale-rank selection challenger** (from §5k, MARA-vs-WULF) — Danny picks *between* similar names by whale-accumulation intensity; that's cross-sectional selection (R2), our biggest measured lever. Ship a `whale_rank` ledger column now (S, rides the next ledger-touching session — same pattern as the rs12_rank column, §5j), then enter it as a challenger in the #24 three-way harness at the 2026-10-01 read: whale-top3 vs rs12-top3 vs equal-all | S column + M study | must tie-or-beat rs12-top3 on all three honest windows incl. hype-2021 control; else closed. Column itself is pure measurement, no gate |
| 81 | **Weekly-timeframe whale detection** (from §5k, "whales on daily play tricks") — recompute #12's three footprints on weekly bars; his own practice tracks accumulation weekly. Confluence table: daily-🐳 vs weekly-🐳 vs both firing | M | rides #23's confluence harness; counts against the R10 one-modifier-per-quarter budget; 2021 control included; only the winning variant (if any) keeps the 🐳 promotion |
| 82 | **Ribbon run-length stat** (from §5k) — his "ribbon" is a regime run; "big red candles open runs lasting weeks to months" is a run-length claim. Measure the historical distribution of weekly-RED spell lengths (optionally conditioned on entry-candle size); digest already prints "weekly RED 8w" — add the base rate: "RED 8w (median run 11w)", so the owner knows how much accumulate-window typically remains | S–M | run-length study; if entry-candle size conditioning adds nothing, print the unconditional base rate only; info-only, no gate beyond the study |
| 67 | **Hard-rule provenance audit** (owner-requested 2026-07-10, "determine these hard rules instead of gut feeling"; full design **D-67** in DESIGNS.md Part I) — audit finding: the 10%/name add-cap was never backtested and the adopted emergent arm (§5g, 2.10×) never enforces it (PLTR grew to ~30% with adds continuing). Registry of every hard constant by provenance (tested / declared / not-tunable), then price the declared ones as insurance: cap sweep on the multiwindow harness (premium) + synthetic top-name −80% shock (payout), Bucket-B threshold sensitivity, whale 2% derived from episode dispersion, max-5 sweep, 50/50 frontier printed info-only | M | pre-committed decision rule in D-67 — cap moves only if an alternative ties-or-beats 10% on universe B AND survives the shock table; may move UP, never OFF; PLAYBOOK edited only after, with the measured premium quoted |

### 8.4 Planning → execution handoff

Division of labour adopted 2026-07-06: the planning model writes §8 +
`DESIGNS.md` + `SPECS.md`; the executing model builds one item per session
following `DESIGNS.md` Part III (gate restated before coding, #49 golden
files first, validate green before commit, info-only never promoted in the
same session it ships, null results closed honestly).

**Executing model: start at `EXECUTION.md`** (added 2026-07-07) — the
session queue, the engine-freeze rule (signal engines frozen outside
gated Phase-C sessions), the execution risk register R1–R12 (bars
contract, ledger backfill ban, refine-state continuity, TZ drift, workflow
reorder trap, …), and mechanical guards #61 (engine-freeze CI hash check)
and #62 (ledger append-only hash check).

### 8.5 Execution notes — where reality contradicted the plan

`EXECUTION.md` requires that a session which finds the plan wrong records it
here rather than improvising around it. Newest first.

**2026-07-11 · session 0 ran LAST; a Week-1 item had silently slipped;
two sessions shared the repo.** `SPECS.md` was queued first and written
after every Week-1/Month-1 item had shipped without it — the PRD/DESIGNS
text plus EXECUTION.md's risk register proved sufficient spec for S/M
items. Review found: (1) **#64 provenance was in §8.1's Week-1 row ("64
rides along with 13") but never made EXECUTION.md's session queue** — the
ledger accrued origin-less rows 2026-07-08→10; those stay blank forever
(R3). Shipped same day (gate [29]), as were #30 [30], #69+#80 [31], #70
[32]. (2) The queue's "reconcile #22" task was stale — already struck
through here. (3) #31 followed EXECUTION R12 (non-USD excluded, "manual:"
line) over D-31's HK board-lot sketch — the stricter, later rule won.
(4) A planning session and this execution session ran concurrently; the
execution session kept to code files and committed only its own work, the
planning session's PRD/DESIGNS edits landed separately (6ae518c), and its
last SPECS paragraph — orphaned uncommitted when it ended — was folded in
by the reconcile commit. Worked, but two live sessions in one checkout is
luck, not process: prefer one repo-writing session at a time. (5) Ledger
column appends (#64 origin, #80 whale_rank) each require a DELIBERATE
guard-#62 checkpoint regeneration — done in the same commits, stated in
their messages; the guard held green before and after both.

**2026-07-10 · #19 shipped; "volume spike" was half the tell.** The item
specified `|1-day move| > 45%` **on a volume spike**. That catches a forward
split (10:1 leaves prices divided and volume multiplied) and misses the reverse
split, where the same mis-adjustment multiplies price and *divides* volume — a
volume **collapse**. `homily_corp.py` accepts either side of the median (spike
OR collapse); validate check [24] pins both. Also widened beyond the letter of
the spec: the suspension covers the VH band and the 🎯/🐳 tags, not just
`add`/`POC`/`res` — they are all prices read off the same poisoned histogram,
and a 🐳 promotion is by definition a claim about distance to a chip shelf.
Run over the live 67-name book on 2026-07-10: **zero names flagged** — the
guard is dormant, as a guard should be.

**2026-07-10 · #18 shipped; its stated premise was wrong.** The item claimed
raw closes "systematically dock payers (V MA COST LLY NVO, SPY itself)". The
measured delta is `name_yield − spy_yield`, not `name_yield`: crediting SPY's
own ~1.3% yield to the benchmark docks *every* name by −1.3 pts, and only
above-SPY yielders come out ahead (D05.SI +7.6, JNJ +2.8, NVO +2.1). V/MA/COST
still lose ground (−0.6…−0.8) because they yield less than SPY. Across all 68
universe names **G3 flipped for none** (full table: BACKTEST_RESULTS.md §5).
The fix is correct and now shipped, but it bought correctness, not selection
quality — logged so nobody later re-derives it as an edge.

**New backlog item, opened by the same session:**

68. **Backtests on total return** (M) *(renumbered 2026-07-11 from a
    duplicate "64" — #64 is universe-entry provenance in Phase A)* — `homily_selection_backtest.py`,
    `homily_strategy_backtest.py`, `homily_core4_backtest.py` and
    `homily_multiwindow_backtest.py` still rank/compound on raw closes, so
    live RS12 and backtested RS12 now differ by the yield spread. Migrate them
    to `homily_data.fetch_series()` (raw bars for signals/levels, adj closes
    for returns and for the SPY/QQQ DCA baselines they are measured against —
    the baselines are *understated* today, so this can only make the strategy
    look worse, which is exactly why it must be done). **Gate:** #24's
    `rs12-top3` selection result re-run on adjusted closes must still clear
    its pre-registered rule; if it doesn't, the promotion candidate deferred
    to 2026-10-01 is withdrawn, not re-shopped.

## 9. North star + trade-execution automation track (added 2026-07-07)

### 9.0 North star — the tie-breaker for every prioritisation call

The system's single success metric: **live, measured excess return vs SPY
and QQQ DCA on the same cash flows, over rolling multi-year windows** —
the #14 scorecard on the #13 ledger, reconciled yearly against the
backtests (#40). Standing implications:

1. Anything that doesn't (a) improve selection, (b) reduce risk of ruin,
   or (c) close the behaviour gap (#58) is decoration — deprioritise it.
2. **The behaviour gap is part of the edge.** An unexecuted signal has
   zero alpha. Hence §9.2: remove the human from routine execution,
   staged, with the same gate discipline as signals.

### 9.1 Scope change to §7 (owner request, 2026-07-07)

§7's "auto-trading via IBKR" exclusion is **relaxed for routine monthly
BUYS only**, staged per §9.2. Never automated, ever: sells of any kind,
the 🐻 bear protocol (PLAYBOOK §4 stays human), leverage, options, or any
order outside that day's whitelist (digest ⭐ set + the index ETF).

### 9.2 Automation stages (each runs 2 clean months before the next)

| Stage | What | Human effort | Infra |
|---|---|---|---|
| T0 | #31 copilot prints exact orders | type them in (~5 min/mo) | none — already queued |
| T1 | **SRS as the index leg** — confirm SRS cash is actually deployed into index (not idle), then `SRS_COVERS_INDEX=true`: the cash budget goes 100% to the star half | zero | none — owner decision 2026-07-07: SRS (S$15,300/yr) already covers Bucket A; IBKR recurring investment NOT needed |
| T2 | copilot also emits an IBKR-importable **basket CSV**, committed as `docs/orders_YYYY-MM.csv` | import + transmit (~1 min/mo) | none |
| T3 | monthly scheduled Claude routine with the IBKR MCP connector reads the buy-day block in `docs/snapshot.json` and places the star-half as **LIMIT day orders**; Telegram report of intents/fills | review the report | cloud repo access fixed + MCP attach (routines already support both) |
| T4 | headless API/gateway trading | — | **stays out of scope** — gateway/2FA infra and its failure modes outweigh saving 1 min/month |

**T3 hard guardrails** (in the routine prompt AND cross-checked against
snapshot.json): `AUTOTRADE` repo variable must read `on` (kill switch) ·
whitelist = that day's ⭐ set + index ETF · buy-only · LIMIT ≤ last close
×1.01, day-expiry · per-order cap BUY_BUDGET/5, monthly cap BUY_BUDGET ·
skip any name >10% of book post-buy · no margin · HK excluded (R12) · one
attempt then report, never retry into a moving market · the routine reads
`docs/snapshot.json`'s buy-day block and REFUSES to act on a snapshot
`_v` it doesn't know (#75 — a silently renamed field must never cost
money; `homily_ledger.verify_snapshot` pins the contract in CI). **First T3 month =
report-only** (order instructions created, not transmitted), diffed
against T2's basket. Promotion gates: T2→T3 needs two consecutive months
of the basket executed verbatim with zero manual corrections; T3 keeps
running only while the monthly Flex reconcile (#32: positions vs intended)
shows zero unexplained deviations.

### 9.3 Repo cleanliness contract (so the executor always knows where things live)

| File | Role, one line |
|---|---|
| `PRD.md` | what & why — spec, backlog, scope decisions |
| `SPECS.md` | how — build specs per item (session 0 writes it) |
| `DESIGNS.md` | deep design decisions — folds into SPECS.md once specs exist; delete, don't accrete |
| `EXECUTION.md` | session order, engine freeze, risk register |
| `PLAYBOOK.md` | the human manual |
| `README.md` | index + honesty notes; session 0 adds this docs-map to it |

Rules: no new top-level .md without a line here; generated artifacts live
in `docs/` or as workflow-committed state files (and MUST be added to the
workflow's `git add` list in the same PR, per R8); when a doc supersedes
another, the old content is deleted in the same commit.

### 9.4 Funding-source accounting (owner Q&A, 2026-07-07)

Three sleeves; the bot only ever deploys the first:

* **Cash sleeve = `BUY_BUDGET`.** Pure cash, monthly, set by the owner.
  It does NOT include SRS or ESPP. With `SRS_COVERS_INDEX=true` the
  copilot routes 100% of it to the ⭐ star half (PLAYBOOK §3.3 path).
* **SRS sleeve (S$15,300/yr cap).** IS Bucket A while its cash is actually
  invested in index — it satisfies the index leg by construction, so it is
  never added to `BUY_BUDGET` and earns no "edge" (it is the benchmark).
  The bear-readiness line (#30) should nag if SRS cash sits idle.
* **ESPP sleeve (corrected 2026-07-07).** 10% of salary, contributed
  monthly to employer stock (Visa, V) at a 15% discount — the owner's own
  savings, not granted shares. It therefore IS part of the PLAYBOOK §7
  monthly-investable outflow, pre-committed to one name before the bot
  sees a dollar: `BUY_BUDGET` = the cash remaining AFTER the ESPP
  deduction. The 15% discount is the comp component (one-shot per lot,
  taxed as employment income in SG; no CGT on later sale). What the plan
  must carry:
  - `holdings.json` v2 (#27): the V position tagged `source: "espp"`,
    **including shares held outside IBKR at the plan administrator** —
    Flex sync (#32) will not see those; they are a manual field, updated
    after each purchase window.
  - Risk: V exposure compounds monthly regardless of signal, and is
    employer-correlated (salary and shares from the same company). Cap
    and cluster math (#28, #29) count TOTAL V (IBKR + external). The
    copilot treats V like any other name, but its 10%-cap check must
    include the external ESPP shares — and because the ESPP inflow never
    stops, V will drift toward the cap by itself; the trim flag (#28)
    applies to it like any bought-not-earned position.
  - An explicit owner decision the digest should keep visible (flag,
    never an order): hold ESPP lots (an ever-growing active bet on V) vs
    sell-soon-after-purchase to bank the ~15% discount and redeploy into
    the routine — the standard diversification play; verify plan holding
    rules/blackout windows first.
  - Measurement: excluded from the #14 signal-edge scorecard (its return
    is discount + one stock, not skill); included in whole-book views
    (#29 clusters, #30 bear-readiness, #58 behaviour-gap).

**Measurement (#14) follows the same lines:** the live-edge scorecard
compares the cash sleeve's deployments vs a same-cash same-day index-DCA
counterfactual only. SRS is excluded (it IS the index), ESPP is tracked
separately (its return = discount + one stock, not signal skill).
