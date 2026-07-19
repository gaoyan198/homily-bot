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

**Archived verbatim → `docs/archive/PRD-addenda-5c-5j.md#5c`** (#76). Discovery screen over `UNIVERSE`; leveraged ETFs stay excluded; crypto exclusion lifted 2026-07-09 (IBIT/ETHA + D05.SI added).

## 5d. Addendum 2026-07-06 — multi-bagger conviction screen + methodology page

**Archived verbatim → `docs/archive/PRD-addenda-5c-5j.md#5d`** (#76). Conviction gates + 0–100 score, 🚀 tiers/caps, universe +17 mid-caps, `docs/index.html` methodology page (repo private — Pages stays off).

## 5e. Addendum 2026-07-06 — market regime / decisive sell signal

**Archived verbatim → `docs/archive/PRD-addenda-5c-5j.md#5e`** (#76). 10-month-SMA month-end regime on SPY+QQQ, 🐻 protocol banner; sell step later reframed as priced tail insurance (§5i / D-63).

## 5f. Addendum 2026-07-06 — full strategy vs index DCA (THE test)

**Archived verbatim → `docs/archive/PRD-addenda-5c-5j.md#5f`** (#76). THE test: the edge is selection + never-sell (control 2.10× vs QQQ 1.74×); 🐻 full liquidation was pure cost. Conclusions partly superseded by §5i.

## 5g. Addendum 2026-07-06 — core-4 concentration test (Danny's 85/90% method)

**Archived verbatim → `docs/archive/PRD-addenda-5c-5j.md#5g`** (#76). Core-4 vs emergent concentration: EMERGENT wins (−30% vs −68% MaxDD); equal adds ≈ conviction-weighted — adopted as the standing method the digest encodes.

## 5h. Addendum 2026-07-06 — whale-accumulation tag + WHALE-DIP tier (#12)

**Archived verbatim → `docs/archive/PRD-addenda-5c-5j.md#5h`** (#76). 🐳 whale tag gate PASSED → WHALE-DIP tier PROMOTED (⚪+🎯+🐳, ≤2%/name, same budget, 10% hard cap) — holds 2026-Q3's R10 slot.

## 5i. Addendum 2026-07-10 — D-63 resolved + multi-window re-test (the bar)

**Archived verbatim → `docs/archive/PRD-addenda-5c-5j.md#5i`** (#76). D-63 resolved + multiwindow re-test: the engine does NOT clear the beat-QQQ bar; §4 kept as priced tail insurance, §5.2 the only return-adding exit; construction-date honesty adopted as a standing rule; the effort's justification is risk-shaped disciplined exposure + live measurement.

## 5j. Addendum 2026-07-10 (later) — #24 executed: ⭐ selection gate PASSED

**Archived verbatim → `docs/archive/PRD-addenda-5c-5j.md#5j`** (#76). #24 executed: rs12-top3 PASSED all pre-registered checks — THE promotion candidate, earliest 2026-10-01, gated on the #13 ledger forward-check (rs12_rank column live since 2026-07-10, validate [25]). **PROMOTED EARLY 2026-07-12 by owner override — see §8.5; forward-check reads continue to 2026-10-01, demotion rule armed.**

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

## 5l. Addendum 2026-07-17 — historical Danny X-post sweep → new plans #104–108

Owner request: fetch Danny's *historical* posts (§5k covered Jun 2025 →
Jun 2026) and plan from them. Same collection honesty as §5k: X blocks
direct fetch, so everything came via search snippets — quotes are post
*openers*, threads unverified. **Coverage limit, recorded up front:** the
true 2022–2023 archive is essentially unindexed by search — the earliest
directly surfaced post is Mar 2024 (AMD); everything known about his
2022–23 period arrives second-hand through his own 2026 retrospectives
(e.g. NVDA $15.2 / PLTR $8.8 in 2023). A full-archive crawl needs X
API/login — out of scope, not attempted. What's genuinely new:

| Post (date · ticker) | Claim | Disposition |
|---|---|---|
| [Feb 26, 2026 · JD](https://x.com/dannycheng2022/status/2026877065115611444) | "Candle color doesn't matter—what counts are these 3 levels: 1. Longest Momentum bar $29.4 · 2. Upper blue-ribbon boundary $28.3 · 3. POC $27.4–27.5" — an explicit **level hierarchy above candle colour** | POC is the one level we compute (`homily_chips.poc`) but attach **zero event semantics** to → **#104** |
| POC-definition posts (surfaced via search) | "close above the POC is bullish; a close below may signal a pullback, correction, or the start of a downtrend"; his POC is *dynamic*, updates daily/weekly | Same gap → **#104** |
| [Jun 7, 2025 · NVDA](https://x.com/dannycheng2022/status/1931220827984539928) | full **buy-signal anatomy**: close above the longest momentum bars ($110.1/$115.8/$130.6/$135.3) = momentum buy, valid only when aligned with an *updated* whale-accumulation read (Panel 3) | Our only entry class is dip-at-support; a **breakout-add** (close above the strongest overhead shelf + 🐳) has never been tested → **#105** |
| [Dec 27, 2025 · TSM](https://x.com/dannycheng2022/status/2004934229403242859) | "monthly chart, **to be finalized**" — he treats in-progress higher-timeframe bars as provisional | Our `monthly_closes`/`weekly_closes` resample **includes the partial bar**, so `monthly_up` and the weekly circle can flip when the bar completes; never measured → **#106** |
| [Jul 21, 2024 · Patreon-adapted](https://x.com/dannycheng2022/status/1814950759940903243) | "My accumulation period usually lasts **3 months to 1 year**" (NVDA/PLTR campaigns) | A checkable duration prior for our ⭐/🐳 windows and #50 tranche pacing → **#107** |
| [Feb 27, 2026 · IBRX](https://x.com/dannycheng2022/status/2027253330796507317) | "**Triple Red (Bullish)** candles remain in force despite the recent retracement" — 3 consecutive red closes as a continuation marker | Run-length harness exists (#82) but daily triple-red as a *continuation* conditioner was never cut → **#108** |
| [Mar 21, 2026 · SLV](https://x.com/dannycheng2022/status/2035191322475471239) | weekly-VH breakdown = "a clear sign of weakness… more downside" | Our event study measured the opposite on our names (README honesty 3); #77 multi-TF VH ran NULL; VH↓ already ships as a dated #102 tell. No action |
| [Apr 16, 2026 · leverage史](https://x.com/dannycheng2022/status/2044688709438886203) | "I don't always use leverage — only when whales hand us massive discounts": NVDA $15.2 ×144k sh, PLTR $8.8 ×150k+ sh, 2023 | Governed: LEVERAGE.md's regime ladder is the signed policy; dip-conditioned deployment was #86 — ran **NULL** 2026-07-17. No action |
| [Jul 8, 2024 · NIO monthly](https://x.com/dannycheng2022/status/1810141974454014139) | blue ribbon = protracted downtrend (Panels 1+3 primer) | #82 ran the ribbon run-length study; conditioning null per its own rule. No action |
| [Nov–Dec 2025 philosophy](https://x.com/dannycheng2022/status/1999322103389266123) | "I've never traded — not once"; the dozen $20M+ fortunes were buy-and-hold; ["dumbest questions"](https://x.com/dannycheng2022/status/1996794808992780382) = ticker-timing asks | Already the design core: no sell state, fan-not-path (#103). No action |
| [Mar 11, 2026 · RKLB](https://x.com/dannycheng2022/status/2031749746789069080) | entry origin story: whale accumulation + long-term reversal reads at $5.5 | Selection-by-whale is #80 (`whale_rank` column, shipped). No action |

**Considered and rejected:** subscribing to / scraping his Patreon
("DannyTrades") for the pre-2024 record — §7 out-of-scope stands. An X
API/login crawl of the 2022–23 archive — cost and ToS friction for
material his 2026 retrospectives already summarise; revisit only if an
item above turns on a disputed historical claim.

*Slotting:* all five are studies/presentation — none touches money flow,
so none consumes an R10 slot unless a passed gate later ships a
money-touching change. Backlog rows #104–108 in §8.3; sequencing note in
SPECS §1.

**Outcomes (all five executed 2026-07-18, one session each, branch per
item):** #104 NULL both directions (§19) · #105 gate **PASSED**, `⤴`
info-tag ship queued for its own gated session (§23) · #106 **MATERIAL**
at 7.5%, `m…`/`w…` mark shipped (validate [62], §20) · #107 measured — ⭐
median 2w vs his 13–52w campaign prior, PLAYBOOK §3 paragraph (§21) ·
#108 NULL, below baseline everywhere (§22). Two nulls, one ship, one
measurement, one passed gate; zero engine edits, zero golden re-pins,
zero R10 slots consumed.

## 5m. Addendum 2026-07-18 — second sweep of Danny's posts → new plans #109–111

Owner request: fetch more posts and plan from them. Collection honesty
unchanged (§5k/§5l): search snippets + his stale Threads mirror
(@dannycheng2022, last mirrored Apr 2025) — X still blocks direct fetch
(402 on the status URL). What's genuinely new vs everything already
covered, measured, or nulled:

| Post (date · ticker) | Claim | Disposition |
|---|---|---|
| [Jun 26, 2024 · MARA vs WULF](https://x.com/dannycheng2022/status/1805828960787513768) + [Aug 15, 2024 · FICO](https://x.com/dannycheng2022/status/1824049895201964421) + [Mar 7, 2024 · AMD](https://x.com/dannycheng2022/status/1765589586275930236) | Panel-3 whale accumulation is an absolute **0–100% level with named thresholds**: "whales need to reach **50% for the stock to run and 75% to surge**" (WULF 94% vs MARA 9.1%; FICO 92%; AMD 93.4%) | Our 🐳 is a binary dip-context tag and #80's `whale_rank` is a *cross-sectional rank* — nobody has an absolute level or the run/surge threshold claim → **#109** |
| [Aug 7, 2024 · CELH](https://x.com/dannycheng2022/status/1821141127740952689) | His bearish checklist counts **heavy retail accumulation (green bars) + NO whale bar** as a distribution tell — the *inverse* of the whale read | We model whale presence, never whale *absence under heavy volume*; #79 (passed, ship queued) measured active selling footprints, not the retail-crowding shape → **#110** |
| Threads Apr 20, 2025 · [below-IPO thread](https://www.threads.com/@dannycheng2022) (ALAB · SNOW · OSCR · COIN) | A **valuation sourcing screen**: quality growers trading below IPO reference (ALAB 179% growth at 12.8× EV/S; SNOW NRR 126% at 10.1×) — and OSCR from that list became his big 2026 winner | Our discovery screen is tape-first + F-checks; no valuation axis exists. Static IPO-reference map is committable, point-in-time by construction → **#111** |
| Threads Apr 21, 2025 · AMZN weekly | His full bearish sequence called in real time: weekly-VH reversal Feb 2025 → bearish candles → LH/LL → *declining* whale accumulation ("avoided a 32% drawdown") | Evidence FOR the #79+mLHLL variant already gate-PASSED and queued behind R10 — raises its ship priority, no new item |
| [Mar 18, 2026 · SNDK](https://x.com/dannycheng2022/status/2034171075240857688) "Trend is your best friend"; [Mar 15, 2026 charting philosophy](https://x.com/dannycheng2022/status/2033021857553854859); [Feb 25, 2026 tops](https://x.com/dannycheng2022/status/2026629980206281102) "biggest winners top out when everyone stops doubting" | philosophy restatements | Already the design core (trend engines, no-sell, fan-not-path). No action |
| [May 4, 2026 · OSCR](https://x.com/dannycheng2022/status/2051272467218411732) and 2026 small-cap flow (IBRX/CLSK/RKLB) | live calls, no new method content surfaced | Universe stays rule-governed (#65); no action |

**Considered and rejected:** approximating his Panel-2 "green trend
line" (never defined publicly — nothing testable); the 200-EMA/4h crypto
post (out of scope); replicating his exact whale-% (proprietary — #109
tests *our* absolute proxy against his threshold *shape*, not his
numbers).

*Slotting:* #109/#110 are studies on existing harnesses (#79/#80
patterns); #111 needs one new static data file (IPO reference map) and a
study; none touches money flow without a later R10 slot. All three
follow the house rule: point-in-time, hype-2021 control, pre-registered
verdicts, null → closed honestly.

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

*(Amended 2026-07-12, owner max-return directive: leverage/margin is no
longer blanket-excluded — it is governed by D-91's regime-gated,
sleeve-only policy (§8.2, §8.5). Everything else above stands.)*

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

13. ~~**Signals ledger**~~ — **shipped 2026-07-08** (gate: validate [17][18], guard #62); full text → `docs/archive/PRD-shipped-items.md#item-13`
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
15. ~~**State-change alerts** (#3)~~ — **shipped 2026-07-08** (gate: validate [19]); full text → `docs/archive/PRD-shipped-items.md#item-15`
64. ~~**Universe-entry provenance**~~ — **shipped 2026-07-11** (gate: validate [29]); full text → `docs/archive/PRD-shipped-items.md#item-64`
70. ~~**Missed-run detector**~~ — **shipped 2026-07-11** (gate: validate [32]); full text → `docs/archive/PRD-shipped-items.md#item-70`
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

16. ~~**Self-tests gate the send**~~ — **shipped 2026-07-07** (gate: workflow halt simulation); full text → `docs/archive/PRD-shipped-items.md#item-16`
17. ~~**Fetch hardening**~~ — **shipped 2026-07-08** (gate: validate [21]); full text → `docs/archive/PRD-shipped-items.md#item-17`
18. ~~**Total-return correctness**~~ — **shipped 2026-07-10** (gate: validate [23]; adjclose ships as a parallel series, R1 kept); full text → `docs/archive/PRD-shipped-items.md#item-18`
19. ~~**Corporate-action sanity check**~~ — **shipped 2026-07-10** (gate: validate [24] + golden `corp`); full text → `docs/archive/PRD-shipped-items.md#item-19`
69. ~~**Promotion lifecycle registry + rs12 forward-checker**~~ — **shipped 2026-07-11** (gate: validate [31]; `promotions.json`); full text → `docs/archive/PRD-shipped-items.md#item-69`
75. ~~**Snapshot schema contract**~~ — **shipped 2026-07-11** (gate: validate [33]); full text → `docs/archive/PRD-shipped-items.md#item-75`

### Phase C — make the scores mean something (selection quality, R2)

20. ~~**Conviction-score backtest**~~ — **ran 2026-07-11** (BACKTEST_RESULTS
    §11, validate [43]): the SCORE ranks OOS on both universes (A ρ +1.00,
    B ρ +0.99, top decile positive) → no footer relabel; the TIER CUTS
    (75/60) separate nothing (CONVICTION ≈ STARTER ≈ fails on 2×/5×/wreck
    rates) and the gates passed 144 wreck-episodes on B. Weight changes
    queue behind R10.
21. **Re-point the daily refine loop** — **diagnostic PASSED + parallel run
    LIVE 2026-07-11** (BACKTEST_RESULTS §13, validate [44]): ⭐-day folds
    pooled 479/1012/736 (no RED fallback); λ rankings stable at 0.25/0.5,
    reshuffle at 1.0 recorded; J logs daily to `homily_refine_j.csv`
    (sibling append-only file, R2); champion.json carries `objective`.
    **Switch read: ≥2026-08-22 (30 rows), its own session** — champion
    selection stays Calmar until then. **Gate:** the parallel-run
    comparison.
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
25. **Real market cap** (#2) (S→M) — **build-time decision 2026-07-11
    (§8.5): requires an ENGINE EDIT** — `conviction()` has no market-cap
    input to override (G1 computes $-volume from bars internally), so this
    is a Phase-C change to frozen `homily_conviction.py` and QUEUES behind
    R10. **Gate:** spot-check vs three known caps in validate, plus the
    engine-freeze manifest update in the same gated session.
26. ~~**Breadth canary**~~ — **shipped 2026-07-11** (gate: validate [34]; info-only); full text → `docs/archive/PRD-shipped-items.md#item-26`

### Phase D — portfolio & risk lens (returns are portfolio-level, R3)

27. ~~**Position-aware digest**~~ — **shipped 2026-07-10** (gate: validate [26]; holdings v2); full text → `docs/archive/PRD-shipped-items.md#item-27`
28. ~~**Trim-rule flags**~~ — **shipped 2026-07-11** (gate: validate [35]); full text → `docs/archive/PRD-shipped-items.md#item-28`
29. ~~**Concentration / correlation lens**~~ — **shipped 2026-07-11** (gate: validate [36]; info-only); full text → `docs/archive/PRD-shipped-items.md#item-29`
30. ~~**Bear-readiness line**~~ — **shipped 2026-07-11** (gate: validate [30]); full text → `docs/archive/PRD-shipped-items.md#item-30`

### Phase E — execution copilot (R0 — the highest-ROI phase in the plan)

31. ~~**Buy-day copilot**~~ — **shipped 2026-07-10** (gate: validate [27]; T2 basket CSV included, R12 followed); full text → `docs/archive/PRD-shipped-items.md#item-31`
32. ~~**IBKR Flex auto-sync** (#11)~~ — **shipped 2026-07-11** (gate: validate [38]; owner secrets still to be set); full text → `docs/archive/PRD-shipped-items.md#item-32`
33. ~~**Sunday deep-dive** (#9)~~ — **shipped 2026-07-11** (gate: validate [37]); full text → `docs/archive/PRD-shipped-items.md#item-33`
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

34. ~~**F0 — digest typography v2**~~ — **shipped 2026-07-08** (gate: validate [20], goldens re-pinned); full text → `docs/archive/PRD-shipped-items.md#item-34`
35. ~~**F1 — chart cards, stdlib PNG**~~ — **shipped 2026-07-11** (gate: validate [28] pixel-hash); full text → `docs/archive/PRD-shipped-items.md#item-35`
36. ~~**F2 — daily dashboard, self-contained HTML**~~ — **shipped 2026-07-11** (gate: validate [33]); full text → `docs/archive/PRD-shipped-items.md#item-36`
37. **F3 — Telegram Mini App** (L; *deliberate no-server relaxation*; only
    if 2 weeks of F2 shows file-open friction) — host the same dashboard
    behind Telegram WebApp auth: Cloudflare Pages + a tiny Worker verifying
    `initData` HMAC against the bot token, allowlisted to your chat_id;
    the digest gains a persistent "📊 Open dashboard" inline button.
    Costs: CF account, one secret, a deploy step. Revisit §7 wording first.
38. **F4 — interactive commands** (parked) — `/why NVDA`, `/size 2500`
    answered by the same Worker reading `docs/snapshot.json` via the GitHub
    API. Parked until F3 proves its keep; explicitly NOT a trading surface.
73. ~~**Digest line budget**~~ — **shipped 2026-07-17** (gate: validate
    [58]): the standing HEADER zone (title → first state group: regime,
    ladder, ops, breadth, lens, cross-book — the lines every digest
    carries) is CI-capped at 12 non-empty lines, checked on all three
    committed goldens AND a synthetic fully-loaded header (BULL + ladder
    + #99 ops + hostile-breadth — the interlock §8.5 asked for).
    Cadenced blocks (buy-day/rehearsal/household/promotions) are exempt:
    they earn their rows a few days a month. Standing rule now
    mechanical: a new digest feature must displace a line or live on the
    dashboard (#36). Deliberately NOT built (recorded per §8.5): the
    "overflow prints tickers only" fallback — a render change with no
    live trigger while the budget holds; build it the day the check
    trips. Original text: a hard cap on actionable digest lines (~12
    above the fold), enforced by a validate check counting lines in the
    #49 golden digests. **Gate:** golden-file line count in validate —
    PASSED.

### Phase G — research queue (one per quarter, July re-test cadence)

39. ~~**Bootstrap CIs on THE test**~~ — **shipped 2026-07-11**
    (BACKTEST_RESULTS §6, validate [41]): honest universe B beats QQQ DCA
    in 23.8% of resampled paths; hindsight A is a coin flip (53.5%).
    Machinery importable (#20's bands and #71's noise band reuse it).
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

*Slotting for #90–93 (owner max-return directive, 2026-07-12):* **#90
goes first** — everything else in the directive lands inside the merged
repo. #91's backtest rides any session after #90 (it reuses bt_data +
the frozen regime engine); the LEVERAGE.md policy signs only after its
readout, and no levered order exists before the signature. #92 waits for
its R10 slot (2027-Q1) unless the owner spends the override lever — the
demotion rule is written either way, so the override is a one-session
change. #93 is date-gated by the paper ledger itself (~2027-01). None of
these touch homily goldens; the digest's SWING section and leverage line
are additive.

*Slotting for #94–100 (integration era, 2026-07-12 late):* the leverage
era ARMED four money surfaces without any single instrument that reads
them together, so this batch is measure/integrate/harden, not new
signals — none consumes an R10 slot (they add no signal behaviour;
#95/#98 are §9.4 funding-flow accounting, the rest are info-only or CI
guards). Order by what the calendar forces: **#95 (flywheel skim) and
#99 (ops-readiness) go first** — #95 must exist before 2026-10-01, the
first quarter-end the live book could clear its HWM, and #99 is an
S-effort R0 win that rides #73's line-budget session and keeps the
owner's own blockers (MARGIN_ZERO, Flex secrets) visible. #94 (household
scorecard) and #97 (cross-book lens) build naturally alongside the
~2026-10 #14 scorecard session — same adjclose/counterfactual
machinery, same monthly-block surface. #96 (A5 A/B reader) is buildable
now but its verdict row is date-gated (26 live weeks / 20 closed); #98
(scale ladder) is a pure-constraint CI guard, buildable anytime, and
wants to land before the first top-up temptation. #100 waits on the #32
Flex secrets like every reconcile. All homily-goldens-safe (info-only
digest lines / gambit-side reports); each ships behind the same #49
golden safety net.

### 8.2 Explicitly NOT in this plan

**Amended 2026-07-12 (owner max-return directive):** leverage/margin
leaves this list and is governed by **D-91's regime-gated, sleeve-only
policy** (#91) — never on the core monthly book (D-91's arithmetic: the
core arms' own −59…−76% measured paths are margin-call wipeouts at any
constant ≥1.25×), live attachment only to a gate-passed swing arm plus
the ring-fenced sidecar on its frozen terms, margin to zero at 🐻 onset.

Still excluded, unchanged: options overlays, SOXL-class levered ETFs,
intraday data, auto-execution beyond the human-approved order rail, paid
data feeds, ML black-boxes (any model whose reasoning can't be printed in
a digest footer), and any new timing signal without a control-salted
point-in-time gate. §7 stands as amended.

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
review below (§5k, owner-requested 2026-07-11), #83 = Danny-style chart
board below (owner-requested 2026-07-12; design D-83), #84 = any-ticker
chart CLI below (owner-requested 2026-07-12), #90–93 = owner max-return
directive 2026-07-12 — leverage / merge / concentration, designs
D-90…D-93 (§8.5 records the directive), #94–100 = integration era
2026-07-12 (late) — measure/integrate/harden what the leverage era
armed, designs D-94…D-98, rows below, new proposals start #101):

| # | Idea | Effort | Gate |
|---|---|---|---|
| 46 | Turnover-adaptive chip decay | M | must beat fixed half-life on #47's hold-rate metric OOS |
| 47 | Shelf hold-rate statistic ("held 7/9 touches") | M | is itself an event study; ≥8 touches; info-only |
| 48 | Ancient-shelf overlay (240d half-life profile) | S–M | bounce event-study vs recent shelves |
| 49 | Golden-file digest tests — **build first on execution days** | S | none (test infra) |
| 50 | Staged-add tranches (shelf / −7% / −14%) | M | avg-cost + MOIC vs single-add and DCA, both universes |
| 51 | ~~⚪ time-stop study~~ — **run 2026-07-17, PASSED** (BACKTEST_RESULTS §16): w=2 (~8 weeks) beats the declared 12w on both honest-control windows at no DD cost (B·5y 1.99 vs 1.80, B·10y 2.73 vs 2.55); w=1 passes too but fails minimal-change. §5.2 edit = registry promotion + demotion rule, QUEUED behind R10 (2027-Q2 queue with #79 · whale-cap 1.6% · #20). NOTHING shipped today per Part III rule 5 | M | the study itself; PLAYBOOK edited only after — study PASSED, edit queued |
| 52 | Inverse-vol sizing within stars | S–M | THE-test rerun; expect a null per §5g |
| 53 | SGD lens (book return in SGD, USDSGD trend) | S | info-only |
| 54 | ~~Weekly "what changed" ledger diff~~ — **shipped 2026-07-17** (gate: validate [61]): `homily_weekly.week_diff` — this week's closing row vs last week's per ticker (whole screen, not just held): state transitions, 🚀-gate flips, the top-3 ⭐ set move, screen arrivals/departures; appended to the Sunday message by the fetch-free deep-dive shell, '' on bootstrap/holiday/quiet weeks | S | PASSED — transitions/flips/top-3/arrivals + quiet-week silence |
| 55 | Breadth cross-check (RSP vs regime; "narrow tape" note) | S | 20y event check or drop |
| 56 | AI analyst memo (weekly cloud-agent process-QA PR) | M | 4-week trial; keep only if it catches a real issue |
| 57 | 中文 digest toggle (筹码/主力 native terms) | S | none (presentation) |
| 58 | Behaviour-gap tracker (perfect-PLAYBOOK shadow book vs real) | M | none (measurement) — prices the discipline gap |
| 59 | ~~Flash-crash pre-script~~ — **shipped 2026-07-17** (gate: validate [59]; goldens untouched — defaulting kwarg): `crash_line()` fires at SPY ≤ −7% over 5 sessions, prints the calm-day self's instructions (regime banner = only sell authority · DCA on schedule · no margin adds §2 · no off-zone averaging down) in the header zone, inside #73's budget. Info-only | S | PASSED — trigger/edge/too-short cases + additive render + budget fit |
| 60 | ~~Data-QA cross-check~~ — **shipped 2026-07-17** (gate: validate [60]; goldens untouched): `freshness_note` (last SPY bar > 3 weekdays old = stale-tape warning, weekend/holiday-safe) + `stooq_daily`/`agreement_note` (second-source close on the last common date, 1% tol) → ⚠️ data-QA lines in the housekeeping zone; warning only, never a halt (R4); Stooq strictly optional (probe from the dev box hit its anti-bot page → silently skipped there; the CI runner may fare better — freshness always runs) | S | PASSED — gap math, canned-CSV parse, tolerance, additive render |
| 63 | ~~Bear-regime rethink~~ — **RESOLVED 2026-07-10** (§5i; design → `docs/archive/DESIGNS-shipped.md#d-63`) | M | done per D-63's pre-committed rule |
| 65 | **Mechanical universe construction** — **built + shadow quarter ARMED 2026-07-11** (validate [46]): `universe.json` committed (124 names, L0→L1→L2 per D-65; bulk sources auth-gated → per-name fetches, quarterly `--shard k/N` over CI nights); daily run logs the ~80 non-hand-list names as `shadow-screen` ledger rows, fenced out of ranks/snapshot/digest. Adoption read ~2026-10 | L | one shadow quarter: keeps ≥90% of hand-list ⭐/🔵/🚀 names AND surfaces ≥1 setup the hand list missed; #14 splits scorecard by origin either way |
| 66 | **Right-stock discipline** — **gate FAILED 2026-07-11** (BACKTEST_RESULTS §14, validate [45]): as-of-filed Q could NOT separate the 2021 wrecks (ZM/DOCU/ROKU/W were Q1 on then-stellar fundamentals — that class was a valuation collapse, not broken businesses). Per D-66's own rule the Q1/Q2/Q3 label ships info-only (`homily_quality.py`, frozen homily_fund untouched); 💎 buyable state, thesis-break veto and every downstream consumer STAY DEAD | M–L | wreck-separation replay ran and failed its pre-committed rule; closed honestly per Part III rule 6 |
| 74 | **缩量 dry-up dip tag** (added 2026-07-11) — Danny's healthy-pullback tell: a dip day on *contracting* volume (20d avg vs 50d avg) is accumulation-friendly; the same dip on expanding volume is distribution. Rides #23's confluence-study harness (⭐/🎯 dips split by dry-up vs expansion); counts against the one-modifier-per-quarter budget (R10); no digest tag ships before promotion | M | event study, both universes incl. 2021 control; null → closed honestly, nothing ships |
| 76 | ~~Planning-doc pruning~~ — **done 2026-07-11**: §5c–5j addenda, shipped §8 item texts and shipped designs moved verbatim to `docs/archive/` with pointers in place; §8.5 notes stayed (all current-month); numbering intact | S | docs-only gate met — validate green, goldens untouched, every section reachable via its pointer |
| 77 | ~~Multi-timeframe volatility hole~~ — **NULL, closed 2026-07-11** (BACKTEST_RESULTS §9): the SPY-monthly "perfect record" is the market's base rate (breakouts at/below unconditional fwd returns, n=5); weekly VH null on both universes; sequence claim directionally present but never beats baseline. Daily VH keeps its place; consumed Q3's timing-modifier slot | M | event study ran; closed per Part III rule 6 |
| 78 | ~~Pullback clock~~ — **shipped 2026-07-11** (BACKTEST_RESULTS §8, validate [42]): band STABLE (median 4d, p25–p75 1–14d, p90 22d) → RED rows print `dip d{n} (med 4d · p90 22d)`. Danny's 3–7d holds at the median only. The past-p90 failure warning is REFUTED (failures resolve faster) and never ships — §8.5 | M | stability rule PASSED; info-only counter shipped |
| 79 | **Whale-distribution warning** — **gate PASSED 2026-07-11** (BACKTEST_RESULTS §10): tagged rally days underperform both controls at both horizons; the monthly-LH/LL confluence variant is the sharp one (n=178, fwd120 −0.3% vs +19.6% base); effect carried by universe B (plain tag NOT predictive on A). Ship (scope guard verbatim: held satellites/Bucket-B + 🚀-candidacy veto only) is its own gated session QUEUED behind R10 — Q4 is #24's first | M | event study PASSED its pre-committed rule; ship queued, prefer +mLHLL variant |
| 80 | **Whale-rank selection challenger** (from §5k, MARA-vs-WULF) — Danny picks *between* similar names by whale-accumulation intensity; that's cross-sectional selection (R2), our biggest measured lever. Ship a `whale_rank` ledger column now (S, rides the next ledger-touching session — same pattern as the rs12_rank column, §5j), then enter it as a challenger in the #24 three-way harness at the 2026-10-01 read: whale-top3 vs rs12-top3 vs equal-all | S column + M study | must tie-or-beat rs12-top3 on all three honest windows incl. hype-2021 control; else closed. Column itself is pure measurement, no gate |
| 81 | **Weekly-timeframe whale detection** (from §5k, "whales on daily play tricks") — recompute #12's three footprints on weekly bars; his own practice tracks accumulation weekly. Confluence table: daily-🐳 vs weekly-🐳 vs both firing | M | rides #23's confluence harness; counts against the R10 one-modifier-per-quarter budget; 2021 control included; only the winning variant (if any) keeps the 🐳 promotion |
| 82 | ~~Ribbon run-length stat~~ — **shipped 2026-07-11** (BACKTEST_RESULTS §7): 1,439 spells, combined median 8w (p25 2w / p75 23w / p90 42w) → RED rows print `med run 8w`. Entry-candle conditioning failed its pre-committed rule (A +3w, B −1w) → unconditional only, per the item's own gate | S–M | study ran; info-only suffix shipped, goldens re-pinned deliberately |
| 67 | ~~Hard-rule provenance audit~~ — **ran 2026-07-11** (BACKTEST_RESULTS §12): registry shipped; cap priced (premium +0.05 MOIC on the honest window — near free; payout +0.26/+0.40 MOIC at −80/−95% shock) and STAYS at 10% (25% clears the formal prongs but surrenders half the payout; any move queues behind R10); Bucket-B threshold insensitive; whale cap DERIVED at 1.6% (in band, tightening queued); max-5 ≈ null; PLAYBOOK §3.4 quotes the premium | M | pre-committed rules applied; step-2a hypothesis confirmed (the ⭐ gate, not the cap, contains wrecks) |
| 83 | ~~**Danny-style chart board — dashboard v2, searchable**~~ — **shipped 2026-07-12** (gate: validate [33] extended — deterministic fixture render, inline-script-only, ≤300 KB committed board; goldens untouched): candle cards in the Homily/Danny chart language (red = bullish via `daily_candle()`, chip histogram + POC, VH zone, add-zone band, 52w ribbon, collision-resolved label rail), ticker-chip index + inline-JS filter (the recorded D-36 relaxation). Committed board = held charts + actionable facts cards (262 KB); FULL board (68 charts, 1.48 MB) sent nightly, never committed — the small-board scope correction is §8.5. Manual: `HOW_TO_READ.md` | M–L | PASSED |
| 84 | ~~**Any-ticker chart CLI**~~ — **shipped 2026-07-12** (gate: validate [47]): `python3 homily_chart.py TICKER…` renders the same card for ANY Yahoo-resolvable symbol (display keys resolve; corp-suspects keep their #19 warning); `ad-hoc — not screened, no ledger history` banner; R3 pinned mechanically (the check greps the module for ledger writes). Live-tested on COIN + 0700.HK | S–M | PASSED |
| 85 | **Promotion-epoch scorecard split** (added 2026-07-12 — the attribution debt the #24 early promotion created) — 2026-Q3 now carries TWO live signal changes (🐳 2026-07-06, rs12-top3 2026-07-12), so every #14/#14a read must split ledger rows by promotion epoch (boundaries read from `promotions.json`, never recomputed) on top of the #64 origin split, or October's numbers blend regimes and attribute nothing. Pure measurement | S | none (measurement infra) — rides the #14 build session (~2026-10) |
| 86 | ~~**Dip war-chest backtest**~~ — **run 2026-07-17, NULL on both arms, CLOSED** (BACKTEST_RESULTS §17): every (f,k) cell LOSES to immediate deployment on the honest control (e.g. 2021→2026 rs12-top3: 1.74–1.65 vs 1.82; f=50% turns CAGR negative), and k never matters — with a ~30-name screen a qualifying dip fires ~every month, so ammunition never accumulates; the scarcity premise is false in this system. Fourth measurement agreeing with §5f/§13/§12. Idea closed per D-86's own frozen rule | M | D-86's pre-registered rule — NULL, closed honestly, nothing ships |
| 87 | ~~**Concentration regime conditioner**~~ — **run 2026-07-17, NULL, CLOSED** (BACKTEST_RESULTS §18): the sign-flip is REAL on both universes (top-3 earns its keep only in favourable states; hostile months everything falls together) but the tradable fallback loses all three honest read windows for all three conditioners — standing down to equal-split saves nothing and costs the re-entry. The live demotion rule stays the only guard; reversal risk is #24's October read's problem | M | D-87's pre-registered rule — NULL, closed honestly |
| 88 | ~~**Top-3 turnover stat**~~ — **shipped 2026-07-17** (gate: validate [57]; goldens untouched — defaulting kwarg): `homily_ledger.top3_turnover()` (month-scoped pure read, reference = the month's first run = the buy-day set per D-31) + one info-only footer line, printed only with ≥2 runs of data. Live July read at ship: the top-3 set changed on nearly every run this week — exactly the fragility signal that raises #87's priority. Original text: — rs12_rank prints daily but money moves monthly: measure within-month churn of the ledger's top-3 ⭐ set (column live since 2026-07-10). High churn ⇒ the buy-day's point-in-time snapshot is fragile and #87 gains priority. Ships at most an info-only footnote ("top-3 stable n/21 days") | S | none (pure ledger read); the footnote gates nothing |
| 89 | **RS-horizon challenger — rs6 / blended rank** — the conviction score already reads RS6, but nobody has tested rank-by-rs6 or 0.5·rs6+0.5·rs12 as the concentration key. Ship an `rs6_rank` ledger column NOW (S — rides the next ledger-touching session; same time-sensitive pattern as #80's whale_rank: forward rows only accrue after it ships), then enter both variants as challengers in the #24 harness (now five-way: equal · rs12 · whale · rs6 · blend) at the 2026-10-01 read. **CORRECTION 2026-07-14 (found while shipping #101):** NOT the pure ledger append this row assumed — `rs6` is a *local* inside the frozen `conviction()` engine (`homily_conviction.py:70`), never stored on `Conviction`, and the adj series isn't in scope at `record()`. Ranking by rs6 needs rs6 *exposed* = a frozen-engine edit (guard #61) + `engine_freeze.json` regen = a **Phase-C session, not S** (same shape as #25, EXECUTION §8.5). The additive fix is behavior-preserving (no signal/score/gate/digest change), so it is a small engine session — but it must wait a Phase-C slot; every day unshipped is lost forward rs6 data before the October read. **COLUMN SHIPPED 2026-07-17** (Phase-C session, gate: validate [56]): `rs6` END-appended to `Conviction` with a default (behavior-preserving — the score consumed rs6 all along; goldens byte-identical), `engine_freeze.json` + guard-#62 checkpoint regenerated deliberately, `rs6_ranks()` mirrors rs12_ranks (⭐ else 🔵, ties by ticker), forward rows accrue from 2026-07-20. The rs6/blend **study** stays queued for the 2026-10-01 #24 harness read | ~~S~~ → engine-gated M (Phase-C) — column DONE, study Oct | same bar as #80: tie-or-beat rs12-top3 on all three construction-honest windows incl. the hype-2021 control; else closed. Column is pure measurement, no gate |
| 90 | ~~**GAMBIT merge — one repo, three books**~~ — **shipped 2026-07-12** (owner directive; design D-90): self-contained `gambit/` (docs stayed in-package, NOT `docs/gambit/` — §8.5 deviation: [K6] reads PRD.md ROOT-relative), byte-identical move (hashes verified), weekly CI job (`gambit-weekly.yml`, Sat 02:00 UTC, validate→run→commit→♟️ Telegram), ♟️ SWING (paper) block in the daily digest (validate [48], goldens untouched), first paper journal rows accrued (2026-07-10 Friday decision — the #93 26-week clock is LIVE), tombstone committed in the old repo | M | PASSED all four D-90 gates incl. same-bars byte-identical replay through both trees |
| 91 | ~~**Leverage policy — regime-gated ladder, sleeve-only**~~ — **shipped 2026-07-12** (owner directive; design D-91): `homily_leverage_backtest.py` ran with its rule frozen first — readout **PASSED at L=1.30** (zero margin-call breaches on every window incl. 1999→2026 at base AND stress financing, worst equity/position 0.68 vs boundary 0.25; beat unlevered QQQ 3/3 read windows net of 5.8%: 2.57/2.29/9.43 vs 2.27/2.14/7.30 — BACKTEST_RESULTS §15). **LEVERAGE.md SIGNED same session by owner override** (§8.5 rule-5 note; the policy's immediate live effects are constraints — shrink-only legacy margin, BEAR=margin-zero, core-book ban). Digest ⚖️ ladder line live (validate [49]); referee for all levered arms = regime-gated 1.30× QQQ | M+S | PASSED its pre-registered readout; LEVERAGE.md §5 carries the yearly re-run + mechanical shrink rule |
| 92 | ~~**Concentration promotion — add-cap 10%→25% + dip-adds into winners**~~ — **PROMOTED 2026-07-12 by owner override** (design D-92; promotions.json "add-cap-25"): `CAP_PCT` 10→25 (one constant, D-27 interlock reaches the copilot), WARN 8→20, PLAYBOOK §3.4/§5.1 + digest/reader texts moved together, goldens re-pinned deliberately (text-only diff eyeballed); demotion watch LIVE and checked every run (`cap_demotion_line`, validate [50]) — a ≥15%-of-book name closing −50% from its post-promotion high reverts the cap to 10% mechanically; uncapped stays excluded (−95% shock 1.49) | S | D-67's prongs (already run) + demotion rule armed in the same commit; R10 arithmetic in §8.5 — next free slot 2027-Q2 |
| 93 | ~~**Swing sleeve live-arming**~~ — **LIVE-ARMED 2026-07-12 by owner override (Amendment A5)**, the P2 paper gate OVERRIDDEN not passed (§8.5): `gambit_live.py` overlay mirrors the paper decisions under the LEVERAGE.md ladder with mandatory stops (−20%) / TPs (+40% half) / 12wk time stop; US$3,000 ring-fenced bankroll (≤10% net liq); KILL-A equity ≤70% of contributed · KILL-B expectancy ≤0 over 20 closed — liquidate + failure memo, mandatory; arms only once MARGIN_ZERO set (clean slate); owner places every order from the printed Monday sheet (G-S7 rail NOT built, LIVE_ORDERS off); paper S1-pure continues as the no-stops counterfactual; weekly order sheet + daily status + monthly realized report (validate [51], 10 live-overlay pytest cases) | M | A5 two-artifact + kill rules = the demotion rule; the paper gate keeps publishing but no longer blocks |
| 94 | ~~**Household book — whole-portfolio scorecard**~~ — **shipped 2026-07-12 late** (design D-94; gate: validate [52]): `homily_household.py` + owner-maintained `contributions.json` — first-Monday block, every sleeve (core + SRS + ESPP + swing − margin) vs the same net contributions DCA'd into QQQ (money-weighted, adjusted closes, **opening balance seeded at inception** so pre-existing dollars never flatter the book — §8.5), USD **and SGD** (#53 absorbed, live SGD=X), combined IBKR gross-L vs the ladder cap, missing-month nag. Info-only; render pure/deterministic; goldens untouched (new `household=""` kwarg defaults empty). Rolling 12/24/36m windows deferred — need a book-NAV history the repo doesn't yet commit (§8.5); since-inception money-weighted ships now | M | PASSED — validate [52]: adjclose counterfactual, opening-honesty guard, leverage over-cap flag, missing-month nag |
| 95 | ~~**Flywheel — swing-skim → DCA routing, measured**~~ — **shipped 2026-07-12 late** (design D-95; gate: gambit pytest 6 new cases + homily validate [51]): `gambit_live.maybe_skim()` banks profit each quarter-end (first weekly run of Jan/Apr/Jul/Oct), `skimmed`/`skims` book fields + `SKIM` journal rows; the ♟️ sheet 💧 line + the homily 🛒 BUY DAY `+ swing skim` line route it (allocation math unchanged); the monthly report shows cumulative banked + the sleeve score (equity+skims vs contributed). **Kill-safe by construction:** a skim reduces equity (→ toward KILL-A, never away), never touches `contributed`, and is never appended to `realized` (KILL-B's expectancy list). Funding-flow accounting per §9.4 — no R10 slot. Baseline is `equity − contributed`, NOT D-95's literal `max(hwm, contributed)` (§8.5 — the skim's own equity drop is the ratchet; adding cumulative-skimmed would double-count). Full flywheel-vs-QQQ counterfactual table deferred (§8.5); each skim stores its QQQ price so it's computable later | M | PASSED — skim fires only above contributed · quarter-gated (no double-skim) · cash-bounded · kill check byte-identical (contributed/realized untouched) · PLAYBOOK §7/§9 + A5 amended same commit |
| 96 | ~~**A5 A/B reader — the stop-cost table**~~ — **shipped 2026-07-12 late** (design D-96; gate: gambit pytest `test_gambit_ab.py` 9 cases + homily validate [51]): `gambit/gambit_ab.py` — reads BOTH journals (read-only, stdlib), parses episodes uniformly by side+reason, attributes every live STOP/TP/TIME exit vs the paper leg in RETURN terms (exit effect isolated from the size ratio), cumulative stops-P&L, verdict row gated at 26 live weeks / 20 closed. REPORT-ONLY (KILL_MEMO stands). Wired into the monthly realized report (`homily_swing.monthly_block`, lazy import, non-fatal). Scoped to CLOSED paper legs — an open paper leg is `pending`, never a fabricated mark (§8.5) | S–M | PASSED — synthetic two-journal fixture (stop that cost / stop that saved / paper-open pending / rotate-excluded / verdict gate) + read-only asserted |
| 97 | ~~**Cross-book concentration lens**~~ — **shipped 2026-07-12 late** (design D-97; gate: homily validate [36] + gambit pytest 2 cases): `homily_clusters.combined_view`/`combined_render` fold swing open positions (value=deployed basis) + external ESPP into the #29 lens — **correlation math (`corr`/`components`) untouched**, extras join by ticker/sector label; a `🔗 across both books` line prints only when swing/ESPP DEEPEN the top cluster (disjoint dilution stays silent), with the G5 >60% warning + same-name-in-both watch. Order-sheet side: `gambit_live.overlap_warning` fires when swing (incl. pending BUYs) shares >2 names with the core book (`live_run` passes `core_tickers` from holdings.json). Info-only; S1 rotation + §4.1 budget untouched (a warning is not an input); goldens untouched (new `cross_book` kwarg defaults None) | S–M | PASSED — overlapping books fire both lines, disjoint stays silent, sheet warning pinned |
| 98 | ~~**Swing scale ladder — the bankroll is earned**~~ — **shipped 2026-07-12 late** (design D-98; gate: gambit pytest 4 cases + `gambit_validate` [SCALE]): `gambit_live.SCALE_STEPS` (3k→6k→12k) + `scale_check()` advisor (`python3 gambit_live.py --scale-check`) + `gambit_validate.check_scale` CI guard (K6 pattern) — `contributed` off the ladder, or a step reached without a dated `AMENDMENT_A5` owner line naming it, FAILS the build. Mechanical preconditions (≥20 closed, expectancy>0, never killed, on-ladder) auto-checked; the referee/26wk + ≤10%-net-liq conditions are owner-attested in the A5 line (same stance K6 takes). `gambit/PRD.md` §3.5 is the policy. Pure constraint — no R10 slot | S | PASSED — off-ladder + unsigned-step both fail CI; base + no-book pass; signed step passes |
| 99 | ~~**Ops-readiness block**~~ — **shipped 2026-07-12 late** (design D-99; gate: homily validate [53] + gambit pytest 2 cases): `homily_ops.py` — one standing `⏳ SETUP` line listing the owner's unset switches (MARGIN_ZERO / IBKR_FLEX secrets / BUY_BUDGET_USD) with margin-paydown progress from a manual `MARGIN_BALANCE` var ("S$X to clean slate"); silent when the board is clean. Plus a ONE-shot KILL-A proximity warning: `gambit_live.kill_watch` sets `warned_80` when equity first crosses below 80% of contributed (journals KILL_WARN, resets above 85%), surfaced once in the SWING LIVE block. Pure R0, info-only; new `ops=""` kwarg defaults empty → goldens untouched. #73 line-budget interlock still unbuilt — the block is one compact line (§8.5) | S | PASSED — full board lists 3 to-dos, clean board silent, one-shot fires once + resets |
| 100 | ~~**Realized-cost reconcile**~~ — **shipped 2026-07-12 late** (design D-100; gate: gambit pytest `test_gambit_reconcile.py` 7 cases + homily validate [51]): `gambit/gambit_reconcile.py` — parses a committed `ibkr_statement.json` (populated by hand today, by a #32 Flex cash/trades query once secrets exist) + the live journal; reports actual financing effective rate vs modeled 5.8% (**the true rate feeds LEVERAGE.md §5's yearly re-run**) and per-side adverse fill slippage, printing 🔴 when the implied round-trip clears the 0.35% stress arm. Read-only, stdlib; wired into the monthly swing report (`homily_swing.monthly_block`, lazy import). No statement → silent (non-fatal, never blocks the send). Dark until the owner populates a statement / sets Flex secrets | S | PASSED — canned-statement fixture: effective-rate annualization, adverse-slippage-by-side + stress flag, unmatched-safe, silent-without-statement, read-only asserted |
| 101 | ~~**Daily candle colour in the ledger**~~ — **shipped 2026-07-14** (owner-noticed 2026-07-13 via Danny's MU yellow-candle post; gate: homily validate [54]): `daily_candle()` (RED/YELLOW/NEUTRAL) is the one engine output the digest renders (`dY` + the #78 pullback clock) yet never persisted — the log's `wk_circle` is the *weekly* circle, a different signal — so a "did we flag MU yellow on 2026-07-10?" audit needed a live recompute. `homily_ledger.COLUMNS` gains a `candle` cell read off the frozen `DannySignal.candle` (no engine edit); guard-#62 checkpoint regenerated deliberately for the new serialisation, and the committed ledger is now re-verified live inside validate. Forward rows only, same time-sensitive pattern as #80's `whale_rank`. Pure measurement — gates nothing | S | PASSED — END-appended, state→CSV→append round-trip, R3 clean, goldens 16/16, freeze [39] intact |
| 102 | ~~**Short-term bearish-tells block (info-only)**~~ — **shipped 2026-07-17** (gate: homily validate [55]; goldens untouched — the scenarios pass no book, so the block never fires there): `homily_bearish.py` (pure, stdlib, no IO) reads the frozen `DannySignal` + the bars the run already fetched; three tells ship — candle YELLOW (dated by exact prefix recompute of `daily_candle()`), wk AMBER/WHITE (aged), VH↓ topping (dated to the first close below the boundary) — #79's tag joins when its own queued session lands. Live smoke at ship: MU `candle YELLOW since 7/1` (1 tell → silent, confluence by design), DRAM 1 tell, 9992 1 tell. Known limit, recorded honestly: too-new names (DRAM) can't warm the monthly/weekly engines, so their deterioration mostly reads as 1 tell — the ⚠️too-new row note remains their surface. (owner-requested 2026-07-17, after Danny's bearish MU reads into the Jul 13–16 correction — MU ~−22% off its high on CXMT-IPO / HBM-export-restriction news; his 2026-07-10 MU yellow-candle post was #101's trigger). Audit finding: every tell Danny reads before a correction is already computed here, but scattered across per-name row suffixes — daily candle YELLOW (#101, now ledgered), weekly AMBER/WHITE (state icon), ⚠ topping-VH breakdown (note-only, homily_danny.py), #78 dip age, #82 run-length — and the sharpest one, **#79's whale-distribution tag (+mLHLL variant, gate PASSED 2026-07-11), has no digest presence at all** while its ship sits QUEUED behind R10. Ship a dedicated **⚠️🐻 short-term bearish tells** digest block over HELD names only: one line per name when ≥2 tells are active, each tell dated ("MU: candle YELLOW since 7/10 · VH↓ 7/15"), read off existing frozen outputs — no engine edit, no new signal, no threshold tuning. When #79's own gated session ships, its tag joins the tell list (this block does NOT advance #79's queue slot or widen its scope guard). **Gates nothing, by design and by the evidence** (VH breakdowns ran above-baseline forward, homily_vol_backtest.py; #78's past-p90 warning REFUTED — §8.5): DCA/buy-day/copilot math untouched. The point is owner discipline at the moment of *manual* action — the 2026-07-16 DRAM/9992 core-margin adds (the LEVERAGE.md §1+§2 cap breach) were placed with none of these tells consolidated in front of the owner. HOW_TO_READ gets the honesty paragraph: tells ≠ prediction, the measured nulls stay stated next to the block | S | validate case: block renders only when ≥2 tells are active on a held name AND buy-day/copilot outputs are asserted byte-identical with the block on/off; goldens additive-only; info-only — no promotion, no registry entry |
| 103 | **Conditional forward-distribution card** (owner-requested 2026-07-17: "tell stories from charts about the most likely path" — the honest version is a FAN, not a path). For a name's current state-confluence, print the measured point-in-time forward distribution — fwd 20/60/120d median, p25/p75, p10, with n — from our own committed event studies, on the #83 chart card facts row (+ full board). The confluence KEY is pre-registered here to kill combinatorial cherry-picking: exactly (state, 🐳 bool, 🎯 bool, VH status) with no other dimensions, computed by ONE shared function the study index and the live card both call (R6 pattern — no reimplementation); distributions pooled over BOTH universes on prefix bars, n shown, cells with n<30 print "insufficient history" instead of a number; construction-date caveat printed on the card. HARD LINE (HOW_TO_READ §7 stays law): no price targets, no measured moves, no single-path arrows — the p10 prints NEXT TO the median so the downside is never below the fold; the DRAM add is the card's design case. Info-only, gates nothing, changes no engine | S–M | validate case: card never contains a target/arrow string, min-n floor enforced, distributions byte-reproducible from the committed study harness on fixture bars; board hash re-pinned deliberately; info-only — no promotion |
| 104 | ~~**POC-cross event study**~~ — **NULL, closed 2026-07-18** (`homily_poc_backtest.py`, BACKTEST_RESULTS §19): our decayed POC is crossed ~8×/yr/name and neither direction separates from baseline (down-cross +3.2%/20d vs +3.3%; universes disagree on the uptrend cut) — POC↓ never joins #102, POC↑ earns no note; the POC stays a printed context level. Caveat recorded: the null is about our fixed-half-life approximation, not Danny's own tool. *(original scope:)* (from §5l, JD Feb 2026 + POC-definition posts: close above POC bullish / close below = pullback-or-downtrend-start warning; his level hierarchy puts POC above candle colour). We compute the chip POC every run and print it — with no event semantics attached. Point-in-time event study on prefix bars, both universes incl. the 2021 control: daily close crossing the *prior day's* POC (both directions, computed off `build_profile` on bars[:i] — no same-day profile look-ahead), fwd 20/60d vs each name's unconditional baseline; also cut by state (⭐/🟢 vs ⚪) since a POC down-cross inside an uptrend is Danny's "pullback" read. If the down-cross separates: it joins #102's tell list as a dated `POC↓` line (info-only, held names, ≥2-tells rule unchanged). If the up-cross separates: a row note only. Null → closed honestly, nothing ships | S | study reproducible from committed harness; any tell ships only via #102's validate case (byte-identical buy-day/copilot with tells on/off); info-only — no promotion |
| 105 | **Breakout-add anatomy** — **gate PASSED 2026-07-18** (`homily_breakout_backtest.py`, BACKTEST_RESULTS §23): beats DCA at 60d on BOTH universes (A +14.6% vs +13.4%; B +5.6% vs +4.1%) with control median DD shallower than the ⭐-dip's (−20.4% vs −22.7%); in the wreck universe the whale-confirmed breakout beat the dip entry by ~5pt/60d. Limits recorded: no 20d edge in the control, no 120d edge in A, 🐳-within-10 required (shelf-break alone untested). **`⤴` info-tag SHIPPED 2026-07-19** (`homily_breakout.py` + defaulting-kwarg wiring, validate [63], goldens byte-identical; HOW_TO_READ row carries the measured limits; corp-suspect names skip). Any money-flow change still needs an R10 slot. *(original scope:)* (from §5l, NVDA Jun 2025 buy-signal post: close above the longest momentum bars, valid only with an updated whale-accumulation read). Our engine owns exactly one entry class — dip at chip support (⭐/WHALE-DIP); Danny's other entry is the opposite motion: a close **above** the strongest *overhead* shelf (our `resistance[0]`, his "longest momentum bar") **with 🐳 active** = momentum add. Point-in-time backtest, both universes incl. 2021 control (the control is where breakout-buying should die if it's hype-chasing): event = first daily close above the top overhead shelf with 🐳 within 10 sessions, vs (a) DCA baseline, (b) the ⭐-dip add on the same name, fwd 20/60/120d. 2021-control MaxDD reported next to every return cell. If it passes both universes: a discretionary info-tag only (`⤴` row suffix), same ≤2% framing as WHALE-DIP, **budget/copilot untouched without its own R10 slot**. Fails either universe → closed, logged in BACKTEST_RESULTS | M | pre-registered here: pass = beats DCA baseline on fwd-60d in BOTH universes with control MaxDD ≤ dip-add's; tag ships info-only via golden-additive render; no engine edit — reads frozen outputs |
| 106 | ~~**Provisional-bar honesty check**~~ — **MATERIAL, mark shipped 2026-07-18** (`homily_provisional_backtest.py` + `homily_provisional.py`, BACKTEST_RESULTS §20, validate [62]): 9.9% of days read `monthly_up` against the settled month (⅔ inside the first 10 sessions), 7.5% printed a contradicted state class — past the pre-committed 2% bar, so the `…` mark ships on the `mUP`/`wk` tokens (m: first 10 sessions by the name's own calendar; w: Mon–Thu prints), defaulting-kwarg wired, goldens byte-identical, R1 untouched. *(original scope:)* (from §5l, TSM Dec 2025 "monthly chart, to be finalized"). `monthly_closes`/`weekly_closes` include the in-progress bar, so `monthly_up` and the weekly circle are computed on a bar Danny would call unfinished. Measure it before styling it: replay 5y, both universes — how often does `monthly_up` (and the weekly circle colour) read differently mid-period vs on the completed bar, and how many of those flips changed a digest state? If flip-rate is negligible, record the number in HOW_IT_WORKS and close. If material: ship a provisionality mark only (`m…`/`w…` suffix when the deciding bar is unfinished, e.g. first ~10 sessions of a month) — **display-level, zero engine change**, R1 untouched (the signal itself keeps using all bars; we just stop presenting a provisional read as settled) | S | replay reproducible; if the mark ships: goldens additive-only, state machine byte-identical, validate case asserts the suffix appears only when the period is genuinely incomplete |
| 107 | ~~**Accumulation-window duration check**~~ — **ran 2026-07-18, closed** (`homily_accum_backtest.py`, BACKTEST_RESULTS §21): ⭐ median 2w / p90 5w (1,295 spells) and 🐳 median 1w vs Danny's 13–52w — his "accumulation period" is a campaign of repeated zone-visits, ours is the visit; the monthly routine already builds the campaign, and #50's within-window tranche clock has no measured room (the window closes first). PLAYBOOK §3 patience paragraph added; gates nothing. *(original scope:)* (from §5l, Jul 2024: "my accumulation period usually lasts 3 months to 1 year"). One-off stat over the committed ledger + 5y replay: distribution of our ⭐-window and 🐳-cluster durations per name (p25/median/p75) vs his 3mo–1yr prior. Pure measurement — calibrates #50's tranche pacing (if our windows run far shorter than his campaigns, the tranche clock, not the signal, is the binding constraint) and earns at most one PLAYBOOK §3 sentence. Gates nothing | S | none beyond reproducibility — measurement only; any PLAYBOOK edit cites the table |
| 108 | ~~**Triple-red continuation stat**~~ — **NULL, closed 2026-07-18** (`homily_triplered_backtest.py`, BACKTEST_RESULTS §22): 2,852 events sit BELOW baseline at all of 5/10/20d on both universes (B: −1.27% vs −0.10% at 5d) — the third straight red close is a slightly worse-than-average add day; `3R` never ships. Consistent with #82's conditioning null. *(original scope:)* (from §5l, IBRX Feb 2026 "Triple Red candles remain in force"). Rides #82's existing run-length harness: condition = 3 consecutive daily RED closes (`daily_candle()` recomputed on prefixes, same method as #101/#102 dating); measure continuation vs baseline fwd 5/10/20d, both universes. #82's own precedent is the null path (ribbon conditioning ran null and shipped nothing) — same rule here: null → closed, nothing ships; separation → a one-word row suffix at most, info-only | S | harness reuse (no new engine code); pre-registered: any suffix ships golden-additive, gates nothing |
| 109 | ~~**Whale-level thresholds study**~~ — **NULL, closed 2026-07-19** (`homily_whalelevel_backtest.py`, BACKTEST_RESULTS §24): the pre-registered flow proxy tops out at 55 — his 50/75 marks live on a *stock* scale (share of chips held) unreachable from OHLCV day-counts; the tradable Q5>Q1 cut holds at 60d in A but flips in the control. No `wh:n%`; #80's rank stays the only whale-comparison surface. *(original scope:)* (from §5m, MARA/WULF · FICO · AMD: Panel-3 whale accumulation as an absolute 0–100% level; "50% to run, 75% to surge"). Build an absolute whale-level proxy from the frozen footprint pieces (e.g. footprint-day share over a rolling window + OBV/A-D share — study-local, engine untouched) and test the threshold *shape*: do names above a high level outperform names below at 60/120d, and is there any kink near the claimed 50/75 marks, point-in-time, both universes? Distinct from #80 (rank) — this is *level* semantics, closer to how he actually quotes it. Null → closed; separation → the level joins the `whale_rank` column as `wh:n%`, info-only, own gate | M | study first (no ship path without it); pre-registered: any digest surface is display-only, golden-additive; his exact % is proprietary — we test our proxy's shape, never claim his numbers |
| 110 | ~~**Retail-crowding warning study**~~ — **NULL, closed 2026-07-19** (`homily_retail_backtest.py`, BACKTEST_RESULTS §25): the pre-registered conjunction fires 33× in ~12,000 rally cuts — a near-empty set (some whale footprint is almost always present on liquid names); returns at n=33 are noise and the #79-verbatim rule fails. No #102 tell; not re-tuned post-hoc. His bearish anatomy stays covered by #79+mLHLL (passed, queued). *(original scope:)* (from §5m, CELH Aug 2024: heavy retail accumulation + NO whale bar = bearish tell). Rides #79's harness: event = rally/elevated-volume window where ALL THREE whale footprints are absent while volume runs hot (the crowd is the only bid) — the mirror of 🐳-present. Fwd 60/120d vs baseline and vs untagged rally days, both universes. If it separates it becomes a #102 tell candidate (own session, dated, info-only); if #79's mLHLL ship happens first they share the surface. Null → closed | M | #79 harness reuse; pre-registered verdict rule copied from #79 (both baselines, both horizons, combined universe); scope guard: held satellites/🚀 candidacy only, never core/index |
| 111 | **Below-IPO quality tag study** (from §5m, Apr 2025 Threads thread; OSCR — on that list — became his 2026 winner). New static `ipo_ref.json` (offer price + first-close per screened recent-IPO name, hand-collected once, committed — point-in-time by construction); study = forward 6m/12m of "below IPO reference AND F:≥2/3" names vs the screened-universe baseline, monthly grid, max history available. Sourcing axis only: a pass ships an `IPO↓` discovery-row tag (info-only, golden-additive); the universe stays rule-governed (#65) — this never auto-adds a name | M | needs the one data file + study; pre-registered: tag is discovery-surface only, no universe mutation, no money flow; null → closed and the file stays for future studies |

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

**2026-07-12 (integration era, execution) · #99 shipped; the #73 line-budget
interlock it was gated on does not exist yet.** D-99's gate named "#73's
line-count check green", but #73 (the digest line budget) is still on the
nice-to-have shelf, unbuilt. Rather than expand scope, #99 ships with its
own golden-fixture gate (validate [53], goldens byte-exact via the `ops=""`
default) and a deliberately conservative footprint — ONE compact `⏳ SETUP`
line, items joined with · so it never adds rows. When #73 lands it should
count this line in its budget; recorded so the interlock isn't forgotten.

**2026-07-12 (integration era, execution) · #96 shipped; the A/B follows
CLOSED paper legs only, not "the current mark".** D-96 said the paper leg
is "followed forward … to the current mark". Marking an OPEN paper position
to today needs a live price — a fetch the fetch-free monthly report can't
make, and marking-to-model would fabricate a number the whole repo refuses
to fabricate. Resolution: an open paper leg is reported `pending` and left
out of the cumulative; only episodes where BOTH legs have closed enter the
stop-cost total. Honest and journal-only (D-96's "read-only over both
journals" was the firmer constraint). The verdict still fires at the
pre-registered bar (26 live weeks / 20 closed); by then enough episodes
have closed on both sides. Wired into `homily_swing.monthly_block` via a
lazy `gambit_ab` import (both modules read-only); with no live journal yet
the section is silent, so goldens and [51] are unchanged.

**2026-07-12 (integration era, execution) · #95 shipped; the skim baseline
is `contributed`, not D-95's `max(hwm, contributed)`.** D-95 wrote the
skim as `equity − max(hwm, contributed)`. `hwm` (the weekly equity
high-water mark) is wrong — it ratchets to equity every week, so
`equity − hwm ≈ 0` and the skim never fires. The correct bar is
`equity − contributed`: a skim REDUCES equity by exactly the banked amount
(cash leaves the book), so once 600 of profit is skimmed equity drops
3600→3000 and that 600 can never be skimmed twice — the ratchet is the
equity drop itself, no `hwm` needed. Adding cumulative `skimmed` to the
baseline (my first attempt) DOUBLE-counts (bar raised AND cash removed) and
wrongly forfeits genuinely-new post-skim profit — caught by a pytest that
skims 600, then expects a fresh 150 to bank next quarter. `skimmed` is a
report field only. Kill-safety verified: skims never touch `contributed`
or `realized`, so KILL-A/KILL-B are byte-identical (a skim only moves
equity toward KILL-A, which is the intended conservatism). The full
flywheel-vs-QQQ counterfactual TABLE is deferred (same reason as #94's
rolling windows — the fetch-free monthly report has no `qqq_now`); each
skim stores the QQQ price at skim time so the table is computable in a
follow-up. Committed `gambit_live_book.json` gained the three new fields;
`maybe_skim` also `setdefault`s them so a book saved before #95 upgrades
cleanly.

**2026-07-12 (integration era, execution) · #94 shipped; two divergences
from D-94, both found by driving the block.** (1) **The counterfactual
needed an OPENING BALANCE D-94 didn't specify.** D-94 said "same-cash-flows
QQQ DCA" using the flows in `contributions.json` — but the book already
held ~S$42.9k at the 2026-07 inception that the monthly flow log does not
capture. Comparing full net worth against only the new flows printed a
nonsense +405% edge on the first drive. Fix: `contributions.json` carries
`opening_usd` (whole-book net worth at inception), seeded into the QQQ
counterfactual at the inception month's adjusted close exactly like a flow;
the basis becomes opening + Σflows. The same synthetic book that merely
rode QQQ then reads ≈flat instead of a fake edge — pinned by the
opening-honesty guard in validate [52]. This is the money-weighted
comparison done right; recorded because a future refactor that drops the
seeding would silently restore the lie. (2) **Rolling 12/24/36m windows
deferred — the repo commits no book-NAV history.** A trailing-window
money-weighted return needs the book value at each window start; the ledger
holds per-name signal rows, not book NAV. Shipped the since-inception
money-weighted number (which is the correct money-weighted figure anyway)
and noted the windows accrue once a NAV series exists — a later follow-up,
not this session. No workflow edit: `contributions.json` is a static
owner-maintained config like `holdings.json`, not a nightly-regenerated
artifact, so R8 doesn't apply. Two fetches, not D-94's "one FX series":
QQQ (counterfactual) + SGD=X (FX), both first-Monday-only and non-fatal —
the "one new fetch" wording assumed QQQ was already exposed to the block,
which it wasn't.

**2026-07-12 (execution, final) · #93 LIVE-ARMED by the largest override
yet — recorded, not waived.** D-93's four preconditions said: paper gate
green (26 weeks) → LIVE_ENABLE → order rail → L2 on paper MAR. The owner
directed live-arming at two days of paper history; Amendment A5 (gambit/)
is the two-artifact record, with the owner's verbatim directive and what
it accepts: the stops it mandates FAILED the Phase-1 backtest
(S1-stopped 0/3 — bounded-loss control, not edge), the paper gate keeps
publishing but no longer blocks, fills are modeled. What was NOT
overridden: execution stays human (order sheet, owner places; the G-S7
rail was NOT built and LIVE_ORDERS stays off, so the automated-orders
gate is untouched); the ladder binds sizing; the kill rules are
pre-registered and mechanical (KILL-A −30% of contributed = US$900 on
the initial US$3,000; KILL-B expectancy ≤0 over 20 closed; any margin
call → LEVERAGE.md §5). Arming waits on MARGIN_ZERO — the owner's own
clean-slate condition — so the first levered dollar moves only after the
legacy loan clears. The paper S1-pure book runs on as the no-stops
counterfactual: the A5 experiment is, deliberately, a measured A/B of
the owner's variant against the gate's variant.

**2026-07-12 (execution, latest) · #92 promoted; the R10 ledger now reads
three-spent.** The add-cap raise was designed for the clean 2027-Q1 slot;
the owner's "execute them NOW" spent it early (basis verbatim in
promotions.json "add-cap-25"). Accounting: 🐳 (Q3) · rs12-top3 (Q4,
early) · add-cap-25 (2027-Q1, early) — **next free promotion slot
2027-Q2**, and every #14/#14a/#85 read of 2026 H2 rows must now split
THREE promotion epochs (2026-07-06 / -07-12a / -07-12b share a quarter;
the two same-day changes are at least cleanly co-dated). Registry schema
note: verify_registry gained a `custom` forward_check type (criterion +
checker required) because the cap's demotion watch is not a ledger-rank
check; the rank schema stands unchanged for signal entries. Golden files
re-pinned deliberately (legend/sizing text only — the diff was eyeballed:
two lines per scenario, all "10%"→"25%" wording).

**2026-07-12 (execution, later) · #91 shipped; Part-III rule-5 override
recorded.** Rule 5 says never promote in the same session as the gate's
build; LEVERAGE.md signed the same session `homily_leverage_backtest.py`
first ran — on the owner's explicit "execute them NOW, dont stop until
you're done," recorded verbatim in the LEVERAGE.md owner line (the
#24/A4 override pattern: overridden, not waived silently). Accepted
because the policy's only immediate live effects CONSTRAIN (shrink-only
legacy margin, BEAR = margin-zero, core-book ban) — no levered order can
exist before #93's gate regardless. Registry note: the policy
deliberately does NOT enter promotions.json (verify_registry's schema is
ledger-rank-specific); LEVERAGE.md §5 is its registry, with a yearly
re-run + mechanical one-step shrink rule. The #85 epoch question was
checked: the ladder changes no signal/allocation behaviour, so no new
ledger epoch opens.

**2026-07-12 (execution) · #90 shipped same day; two deviations + one
finding.** (1) D-90 said governance docs move to `docs/gambit/` — they
stayed INSIDE `gambit/` instead: gambit's [K6] safety gate reads
`PRD.md` ROOT-relative (relocating it would have silently disarmed the
P3-deferral check), and the seven docs cross-reference each other by
relative name. `gambit/` is fully self-contained; byte-identity is the
rule that mattered and it held. (2) The paper book's first journal rows
were created during the gate run (SCAN + 5 PROPOSE on the 2026-07-10
Friday decision) — G-S6 scheduling was never built in the standalone
repo, so the merge session started the clock; `gambit-weekly.yml`
closes that gap permanently. Also recorded: gambit_validate and its
tests use CWD-relative paths — every invocation must run from `gambit/`
(the workflow pins `working-directory`). (3) Finding: two LIVE fetches
minutes apart differed by 1e-7 in one name's RS (Yahoo adjclose
jitter), re-chaining every later journal hash — the D-90 gate's
"same bars snapshot" clause exists for exactly this; the replay harness
(bars captured once, played through both trees) proved byte-identical.
Do not panic at a future jitter diff; replay on captured bars before
suspecting the code.

**2026-07-12 (later still) · Owner max-return directive — leverage
sanctioned, concentration encouraged, GAMBIT merges in (#90–93,
D-90…D-93).** The owner hardened the posture: aim for Danny-class
returns, beat QQQ; "discipline repo, not an outperformance strategy" is
no longer the accepted ceiling. What changed: §7/§8.2's leverage
exclusion is amended to D-91's regime-gated sleeve-only policy; the
D-67-priced add-cap raise to 25% is designed with its demotion rule
(#92); GAMBIT retires as a repo and its paper sleeve moves here (#90).
What did NOT change — recorded so nobody reads this entry as a mood:
the falsifiable bar stays §9.0's beat-QQQ ("match Danny" is posture,
not a metric — his returns are unaudited, self-selected, and earned in
a decade when QQQ itself did 20%/yr); KILL_MEMO, LEVERAGE_MEMO and
AMENDMENT_A4 carry over in full (leverage amplifies edge, never creates
it; S1-pure sits on paper because paper is the test); the core monthly
book never carries margin (its own measured −59…−76% paths are
margin-call wipeouts at any constant ≥1.25×); and every money-touching
piece of the directive still ships through the registry with a demotion
rule. The account's legacy 1.23× margin is grandfathered shrink-only —
MARGIN_ZERO stands, now with a destination: paydown headroom becomes
swing budget, never core adds.

**2026-07-12 (later) · #24 promoted EARLY by owner override — R10 and the
forward-check condition both overridden, neither waived silently.** The
§5j/§2·24 protocol said: promote only if (a) the Jul–Sep ledger
forward-check passes and (b) Q4's R10 slot is free on 2026-10-01. The
owner directed immediate promotion (Fable handoff; risk accepted
verbatim in promotions.json) — so rs12-top3 went live 2026-07-12 with
condition (a) unmet and (b) moot. What was NOT overridden: the frozen
Jul–Sep window still gets its read — a #69 month-start digest block
(wired in the same commit) publishes it every month through 2026-10-01,
alongside the rolling demotion check, and a FAIL demotes to
equal-split-max-5 mechanically. R10 arithmetic going forward: 2026-Q3
now carries TWO live signal-behaviour changes (🐳 2026-07-06, rs12-top3
2026-07-12) — Q3/Q4 ledger attribution must read them jointly, Q4's
slot is spent, and the next promotion slot is 2027-Q1 (whale-top3's
earliest date already says so).

**2026-07-12 · #83 shipped; D-83's committed-board scope was wrong by 4×.**
D-83 said the committed small board = "held + actionable" cards under
≤300 KB. Measured: a real candle card costs ~20–30 KB and held+actionable
is ~49 names → 1.16 MB, four times the budget. Resolution (recorded, not
improvised): the committed board charts **held names only**; actionable
discovery names keep searchable *facts* cards there (state pill, levels,
chips row — ~1 KB each) with their charts on the FULL board, which is sent
nightly and never committed, exactly as D-83 §search already split it.
Also trimmed per card: per-bin histogram tooltips dropped, sub-0.5%-of-max
bins skipped (~30% of bytes, invisible ink). Result: committed board
262 KB with all 49 names still searchable, full board 1.48 MB with 68
charts. Sunday's deep-dive now sends Friday's committed board as-is
instead of regenerating bar-less (regeneration would have stripped the
charts — found while wiring `bars_map`).

**2026-07-11 (late) · the gated-research backlog executed in one sitting;
two items found the plan wrong.** Owner instruction: "execute the
remaining items to the fullest." Ran, each on its own branch with its gate
restated first, one merge per item, validate [40]–[46] added: #14a · #39 ·
#82 · #78 · #77 · #79 · #20 · #67 · #21 (diagnostic + parallel start) ·
#66 (test 1) · #65 (build + shadow start). Results live in
BACKTEST_RESULTS §6–§14. Where reality contradicted the plan:
(1) **#25's premise was wrong** — SPECS §2 says "implement as a data
override the conviction call already supports"; `conviction()` has no
market-cap input at all (G1 computes $-volume internally from bars), so
real mcap needs an engine edit to frozen `homily_conviction.py` → per the
spec's own fallback it queues as a Phase-C change behind R10. Not built;
recorded here instead of improvised. (2) **#78's "past-p90 early warning"
idea is refuted, not just unproven** — trend failures resolve FASTER than
healthy pullbacks (median 3d vs 4d); the dip counter shipped, the warning
never will (§8 of BACKTEST_RESULTS). (3) **R10 arithmetic**: the quarter's
one timing-modifier research slot went to #77 (null); #74/#81 wait.
Promotion candidates that PASSED gates but are QUEUED, not shipped: #79's
distribution tag (prefer the +mLHLL variant), #67's whale-cap tightening
to 1.6%, any #20 weight change — Q4's slot remains #24's first, then this
queue. (4) **#66's Q label ships via a NEW `homily_quality.py`** rather
than extending frozen `homily_fund.py` (D-66 suggested the extension): a
sibling module is functionally identical and leaves the engine freeze
untouched — which mattered, because the wreck-separation gate FAILED and
no engine edit was ever justified. (5) **#65's bulk-EOD sources are
auth-gated** (probed: Yahoo v7 batch 401, Stooq bulk 401) — L1 runs on
per-name chart fetches; the quarterly job shards over CI nights via
`--shard k/N` exactly as D-65 anticipated. Also: the L0 filter needed a
when-issued (5th-char V) drop that D-65 didn't list — found live when
SKHYV entered on a fake $17B/d print.

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
| `HOW_TO_READ.md` | the chart-card reading manual (#83 board / #84 CLI) — added 2026-07-12 |
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
