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
too. `UNIVERSE` in `daily_run.py` (~37 liquid names: megacap tech, semis/AI
hardware, growth software, quality diversifiers, HK liquid names) runs
through the same composite engine; only ⭐ ACCUMULATE / 🔵 BOTTOMING setups
surface (max 8 rows + overflow tickers). Exclusions stand: no leveraged
ETFs, no crypto-beta names. Telegram sends now split at 4000 chars.

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
15. **State-change alerts** (#3) (S; needs 13) — diff today's ledger vs
    yesterday's; send a second, tiny Telegram message ONLY on transitions
    (⭐ appears/lapses, 🔵 fires, 🐳 appears, 🐂/🐻 flips, 🚀 enters/exits).
    Quiet day = no second message; the signal stops drowning in the wall.
    **Gate:** none (delivery only).

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
24. **⭐ overflow ranking** (M) — when >5 ⭐ names compete for the monthly
    buy, today's pick is effectively alphabetical. Test RS12-ranked top-5
    vs equal-weight-all vs random-5 (the honesty benchmark), point-in-time.
    Adopt ranking only if it beats *random-5* OOS — guards against
    momentum overfit. **Gate:** the three-way test.
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
    scorecard tables (14), conviction drift, refine log chart. Committed by
    the workflow AND sent via `sendDocument` — private in the chat, one tap
    to open, works offline, repo stays private, nothing hosted. **Gate:**
    HTML self-containment test (no external URLs) in validate.
37. **F3 — Telegram Mini App** (L; *deliberate no-server relaxation*; only
    if 2 weeks of F2 shows file-open friction) — host the same dashboard
    behind Telegram WebApp auth: Cloudflare Pages + a tiny Worker verifying
    `initData` HMAC against the bot token, allowlisted to your chat_id;
    the digest gains a persistent "📊 Open dashboard" inline button.
    Costs: CF account, one secret, a deploy step. Revisit §7 wording first.
38. **F4 — interactive commands** (parked) — `/why NVDA`, `/size 2500`
    answered by the same Worker reading `docs/snapshot.json` via the GitHub
    API. Parked until F3 proves its keep; explicitly NOT a trading surface.

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
    drops (liquidity lost), instead of relying on memory.
45. **Delisted-inclusive control** (#10b) (L, blocked on finding a free
    point-in-time constituent source) — the last big survivorship hole.

### 8.1 Suggested execution order (for the execution days)

| When | Items | Why this order |
|---|---|---|
| **Week 1** (one sitting each) | 16 · 13 · 15 · 34 | send-safety first; ledger starts accruing (every week of delay = a week less live evidence); alerts + readable digest are free wins on top |
| **Month 1** | 17 · 18 · 19 · 31 · 35 | pipeline hardened, return math honest, buy-day copilot live for the next monthly buy, first chart cards |
| **Quarter** | 20 · 21 · 22 · 25 · 27 · 28 · 29 · 36 | scores validated, refine loop re-pointed, portfolio lens on, dashboard shipping nightly |
| **Gated / ongoing** | 14 (first read at 3mo) · 23 · 24 · 26 · 30 · 32 · 33 · 37 · 38 · 39–45 | each unlocks as its dependency (ledger months, position data, F2 usage) matures |

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
(unvetted; every one gated; new proposals start #61):

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
| T1 | **IBKR native recurring investment** for the index half (Bucket A, monthly, fractional) | zero — set up once in Client Portal | **none. Do this now — no code, automates 50% of the routine today** |
| T2 | copilot also emits an IBKR-importable **basket CSV**, committed as `docs/orders_YYYY-MM.csv` | import + transmit (~1 min/mo) | none |
| T3 | monthly scheduled Claude routine with the IBKR MCP connector reads the buy-day block in `docs/snapshot.json` and places the star-half as **LIMIT day orders**; Telegram report of intents/fills | review the report | cloud repo access fixed + MCP attach (routines already support both) |
| T4 | headless API/gateway trading | — | **stays out of scope** — gateway/2FA infra and its failure modes outweigh saving 1 min/month |

**T3 hard guardrails** (in the routine prompt AND cross-checked against
snapshot.json): `AUTOTRADE` repo variable must read `on` (kill switch) ·
whitelist = that day's ⭐ set + index ETF · buy-only · LIMIT ≤ last close
×1.01, day-expiry · per-order cap BUY_BUDGET/5, monthly cap BUY_BUDGET ·
skip any name >10% of book post-buy · no margin · HK excluded (R12) · one
attempt then report, never retry into a moving market. **First T3 month =
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
