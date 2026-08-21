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

**Outcomes (all three executed 2026-07-19, plus the two earned ships):**
`⤴` breakout tag SHIPPED (#105's pass, validate [63]) · #109 NULL — flow
proxies cannot reach his stock-scale 50/75 marks (§24) · #110 NULL — the
retail-heat conjunction is a near-empty set, 33 tags in ~12k rally cuts
(§25) · #111 gate **PASSED** incl. the control side; `IPO↓` discovery
tag SHIPPED (validate [64], §26) with the survivorship caveat attached.
Zero engine edits, zero golden re-pins, zero R10 slots consumed.

## 5n. Addendum 2026-08-13 — third sweep of Danny's posts (window: §5k's 2026-07-11 → today) → new plans #131–132

Owner request: search his newest posts since the last review and plan
from them. Collection honesty unchanged (§5k/§5l/§5m): search snippets
only — X still 402s status URLs, nitter is dead, the Threads mirror is
still frozen at Apr 2025 — so coverage of the Jul 11 → Aug 13 window is
**incomplete by construction**; only posts that surfaced in snippets are
listed. What's genuinely new vs everything already covered, measured, or
nulled:

| Post (date · ticker) | Claim | Disposition |
|---|---|---|
| [Jul 1, 2026 · INTC monthly](https://x.com/dannycheng2022/status/2072145068908302445) (published pre-§5k but never mined — §5k's table stops at Jun 26) | "**Dual volatility holes**" marked the major long-term bottom at $25–27; once price closed above the upper boundary the long-term uptrend resumed; he "started daily charting below $40" | The boundary semantics are already ours (`homily_vol` BREAKOUT = close above upper) and the monthly-TF alone ran NULL (#77). The **two-holes-at-one-base shape** — a second hole forming while the first is unresolved — is invisible to `find_hole` by construction (it keeps only the most recent cluster) and has never been cut → **#131** |
| [Jul 16, 2026 · HOOD daily](https://x.com/dannycheng2022/status/2077587630720737549) | ">10 bullish signals in my daily MUST-READ posts" over a few months on ONE name; shared his own buy orders "more than six times… when whales offered big discounts"; "spent millions accumulating" | Campaign *duration* is #107's prior; hold-cash-for-dips is 4×-nulled (#50 last). The NEW measurable is signal **density**: how often buy-class prints recur on the same name in a trailing window, as a cross-sectional selection input (R2 lever) → **#132** |
| Aug 4, 2026 · IWM/OUST/SLNH daily charts | "If you sold at the April, June, and July bottoms, just quit the stock market and never come back" | Philosophy restatement — already the design core (no-sell states, fan-not-path). No action |
| Aug 4, 2026 · SLNH daily+monthly | "Dare to place the bet?" — speculative small-cap flow | No method content reachable in snippets; universe stays rule-governed (#65). No action |
| [Mar 11, 2026 · RKLB](https://x.com/dannycheng2022/status/2031749746789069080) (pre-§5k post, detail unmined by §5m's "no action" row) | during every sharp pullback "whale accumulation has never dipped below **60%**" — an absolute-level HOLD-through floor | #109 already ran NULL on exactly this axis (§24: our flow proxies cannot read his stock-scale absolute marks) — the same nullification applies. Recorded, no action |

**Considered and rejected:** the charting-frequency escalation ("started
daily charting below $40") — behavioural cadence, nothing testable; his
2026 winner-lap posts (HOOD/IWM signal-count brags) as *evidence* —
selection-biased by construction, only the method shape is usable.

*Slotting:* both items are STUDIES on existing harness patterns (#77's
event study, #120's bake-off), consume no R10 slot, touch no money flow;
house rules apply — point-in-time, hype-2021 control, verdict
pre-registered before the run, NULL → closed honestly.

**Outcomes (both executed 2026-08-13, owner-directed "build them"):**
**#131 NULL** (§34 — dual bottoming breakouts n=18 < 20 AND weaker than
single on both horizons) · **#132 NULL** (§35 — dens-top3 0/3 read
windows vs rs12-top3; fifth dip-affinity-loses-to-strength result).
Zero engine edits, zero golden re-pins, zero R10 slots consumed — the
sweep's whole yield was two honest closes.
## 5o. Addendum 2026-08-14 — "Volatility Hole + descending blue ribbon" post → plans #142–144

Owner supplied Danny's post of 2026-08-14 in full (bottom-timing method:
weekly VH + a descending blue ribbon; **1 hole for strong stocks, 2–3
for weak ones**; then DCA "gradually and aggressively"; "6 weeks to 6
months to fully play out"), with four dated examples: RBRK wk 2026-04-24
$49–50 · HOOD wk 2026-04-10 $66–77 · GOOGL wk 2025-05-23 $166–174 ·
MSFT wk 2026-03-20 $367–400. **A replication probe was run BEFORE any
planning** and it reframes the work:

| his example | our weekly VH at that week | ribbon read |
|---|---|---|
| RBRK $49–50 | zone **63.20–67.37** BREAKDOWN — far above | BLUE + descending |
| HOOD $66–77 | zone **104.45–120.88** BREAKDOWN — far above | BLUE + descending |
| GOOGL $166–174 | zone **161.01–165.82** BREAKOUT — adjacent, closest hit | BLUE + descending |
| MSFT $367–400 | zone **456.89–483.46** BREAKDOWN — far above | BLUE + descending |

**Finding A — the ribbon half replicates 4/4 and it means almost
nothing.** `EMA10<EMA30` with `EMA30` falling was true in every case —
but across 58 names × 5y (13,028 weekly observations) that condition is
true **45.0% of the time** (blue alone 48.6%). A filter on nearly half
of all weeks cannot be the discriminating part of a bottom call; 4/4 is
what a coin-flip-ish filter produces on four self-selected tries. Same
trap README honesty item 3 records for his SPY-monthly "perfect record".

**Finding B — the VH half does NOT replicate, and that is the
foundational problem.** Three of four of our zones sit far above his;
only GOOGL is adjacent. HOW_IT_WORKS already says our detector is "an
approximation… not a clone", but **nobody has measured how big the gap
is** — so #77 (multi-TF VH, NULL), #131 (dual VH, NULL) and the
committed daily event study all tested OUR construct and may say
nothing about HIS → **#142**, a prerequisite, not a parallel task.

**Finding C — #131's null is CONSISTENT with his claim, not a
refutation.** #131 found dual bottoming breakouts weaker than single
(+1.7% vs +6.2% fwd60) and I wrote it up as "the dual shape marks a
weaker base". Danny says precisely that and treats it as the design:
hole COUNT is a proxy for weakness, so a weak name needs 2–3 before its
bottom is in. #131 pooled strong and weak names and asked "is dual
better than single" — the wrong question for this hypothesis. The right
one is conditional → **#144**.

**Not re-opened:** "DCA gradually and aggressively" is #50, which ran
NULL on 0/9 windows (§30) and is the 4th of five dip-affinity nulls
(§37 lists them). It stays closed unless #143/#144 both PASS, in which
case a tranche test conditioned on THIS setup is a new pre-registered
item — never a revival of #50 by assertion.


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
    queue behind R10 — and still do after the 2026-07-22 re-cut: a weight
    change is a SELECTION promotion, which keeps the one-per-quarter
    budget. Only survival/exit recalibrations were freed (EXECUTION.md
    R10 carries the split and the reasoning).
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
armed, designs D-94…D-98, rows below, new proposals start #101; **#113–123 are claimed
by `ROADMAP.md` §5** (long-horizon items #113–119 + alpha-program items
#120–123, added 2026-07-24; #124 = §8.1 target line, row below) — next
free number #125):

| # | Idea | Effort | Gate |
|---|---|---|---|
| 46 | Turnover-adaptive chip decay | M | must beat fixed half-life on #47's hold-rate metric OOS |
| 47 | Shelf hold-rate statistic ("held 7/9 touches") | M | is itself an event study; ≥8 touches; info-only |
| 48 | Ancient-shelf overlay (240d half-life profile) | S–M | bounce event-study vs recent shelves |
| 49 | Golden-file digest tests — **build first on execution days** | S | none (test infra) |
| 50 | ~~Staged-add tranches (shelf / −7% / −14%)~~ — **RAN 2026-07-25, NULL, item CLOSED** (`homily_tranche_backtest.py`, rule frozen in docstring before the run; BACKTEST_RESULTS §30): all three pre-registered prongs fail — MOIC-vs-SINGLE 0/9 windows on universe A, avg-cost-vs-SINGLE 1/9 on A, MOIC-vs-DCA 1/7 on B; 3m/12m sensitivity non-promotable by pre-commitment and changes nothing. Finding: staging helps ONLY where the name keeps falling (wins 4/7 on the hype-2021 control) and there the index beat both arms anyway — insurance against bad selection, not return. Could not have shipped regardless: D-66 §(c) gated tranche automation on the thesis-break veto, which is dead (#66 FAILED, §14). Owner's dip instinct keeps its one measured outlet — 🐳 WHALE-DIP at ≤2% (§12) | M | NULL — nothing shipped, no R10 slot consumed |
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
| 103 | **Conditional forward-distribution card** — **SHIPPED 2026-07-19** (`homily_fandist.py` + `fandist.json` + board wiring, validate [65], BACKTEST_RESULTS §27): 48 confluence cells (31 with n≥30), one shared key function for study+card, p10 beside the median, min-n floor, construction-date caveat; no byte-pinned board golden existed (recorded). *(original spec:)* **Conditional forward-distribution card** (owner-requested 2026-07-17: "tell stories from charts about the most likely path" — the honest version is a FAN, not a path). For a name's current state-confluence, print the measured point-in-time forward distribution — fwd 20/60/120d median, p25/p75, p10, with n — from our own committed event studies, on the #83 chart card facts row (+ full board). The confluence KEY is pre-registered here to kill combinatorial cherry-picking: exactly (state, 🐳 bool, 🎯 bool, VH status) with no other dimensions, computed by ONE shared function the study index and the live card both call (R6 pattern — no reimplementation); distributions pooled over BOTH universes on prefix bars, n shown, cells with n<30 print "insufficient history" instead of a number; construction-date caveat printed on the card. HARD LINE (HOW_TO_READ §7 stays law): no price targets, no measured moves, no single-path arrows — the p10 prints NEXT TO the median so the downside is never below the fold; the DRAM add is the card's design case. Info-only, gates nothing, changes no engine | S–M | validate case: card never contains a target/arrow string, min-n floor enforced, distributions byte-reproducible from the committed study harness on fixture bars; board hash re-pinned deliberately; info-only — no promotion |
| 104 | ~~**POC-cross event study**~~ — **NULL, closed 2026-07-18** (`homily_poc_backtest.py`, BACKTEST_RESULTS §19): our decayed POC is crossed ~8×/yr/name and neither direction separates from baseline (down-cross +3.2%/20d vs +3.3%; universes disagree on the uptrend cut) — POC↓ never joins #102, POC↑ earns no note; the POC stays a printed context level. Caveat recorded: the null is about our fixed-half-life approximation, not Danny's own tool. *(original scope:)* (from §5l, JD Feb 2026 + POC-definition posts: close above POC bullish / close below = pullback-or-downtrend-start warning; his level hierarchy puts POC above candle colour). We compute the chip POC every run and print it — with no event semantics attached. Point-in-time event study on prefix bars, both universes incl. the 2021 control: daily close crossing the *prior day's* POC (both directions, computed off `build_profile` on bars[:i] — no same-day profile look-ahead), fwd 20/60d vs each name's unconditional baseline; also cut by state (⭐/🟢 vs ⚪) since a POC down-cross inside an uptrend is Danny's "pullback" read. If the down-cross separates: it joins #102's tell list as a dated `POC↓` line (info-only, held names, ≥2-tells rule unchanged). If the up-cross separates: a row note only. Null → closed honestly, nothing ships | S | study reproducible from committed harness; any tell ships only via #102's validate case (byte-identical buy-day/copilot with tells on/off); info-only — no promotion |
| 105 | **Breakout-add anatomy** — **gate PASSED 2026-07-18** (`homily_breakout_backtest.py`, BACKTEST_RESULTS §23): beats DCA at 60d on BOTH universes (A +14.6% vs +13.4%; B +5.6% vs +4.1%) with control median DD shallower than the ⭐-dip's (−20.4% vs −22.7%); in the wreck universe the whale-confirmed breakout beat the dip entry by ~5pt/60d. Limits recorded: no 20d edge in the control, no 120d edge in A, 🐳-within-10 required (shelf-break alone untested). **`⤴` info-tag SHIPPED 2026-07-19** (`homily_breakout.py` + defaulting-kwarg wiring, validate [63], goldens byte-identical; HOW_TO_READ row carries the measured limits; corp-suspect names skip). Any money-flow change still needs an R10 slot. *(original scope:)* (from §5l, NVDA Jun 2025 buy-signal post: close above the longest momentum bars, valid only with an updated whale-accumulation read). Our engine owns exactly one entry class — dip at chip support (⭐/WHALE-DIP); Danny's other entry is the opposite motion: a close **above** the strongest *overhead* shelf (our `resistance[0]`, his "longest momentum bar") **with 🐳 active** = momentum add. Point-in-time backtest, both universes incl. 2021 control (the control is where breakout-buying should die if it's hype-chasing): event = first daily close above the top overhead shelf with 🐳 within 10 sessions, vs (a) DCA baseline, (b) the ⭐-dip add on the same name, fwd 20/60/120d. 2021-control MaxDD reported next to every return cell. If it passes both universes: a discretionary info-tag only (`⤴` row suffix), same ≤2% framing as WHALE-DIP, **budget/copilot untouched without its own R10 slot**. Fails either universe → closed, logged in BACKTEST_RESULTS | M | pre-registered here: pass = beats DCA baseline on fwd-60d in BOTH universes with control MaxDD ≤ dip-add's; tag ships info-only via golden-additive render; no engine edit — reads frozen outputs |
| 106 | ~~**Provisional-bar honesty check**~~ — **MATERIAL, mark shipped 2026-07-18** (`homily_provisional_backtest.py` + `homily_provisional.py`, BACKTEST_RESULTS §20, validate [62]): 9.9% of days read `monthly_up` against the settled month (⅔ inside the first 10 sessions), 7.5% printed a contradicted state class — past the pre-committed 2% bar, so the `…` mark ships on the `mUP`/`wk` tokens (m: first 10 sessions by the name's own calendar; w: Mon–Thu prints), defaulting-kwarg wired, goldens byte-identical, R1 untouched. *(original scope:)* (from §5l, TSM Dec 2025 "monthly chart, to be finalized"). `monthly_closes`/`weekly_closes` include the in-progress bar, so `monthly_up` and the weekly circle are computed on a bar Danny would call unfinished. Measure it before styling it: replay 5y, both universes — how often does `monthly_up` (and the weekly circle colour) read differently mid-period vs on the completed bar, and how many of those flips changed a digest state? If flip-rate is negligible, record the number in HOW_IT_WORKS and close. If material: ship a provisionality mark only (`m…`/`w…` suffix when the deciding bar is unfinished, e.g. first ~10 sessions of a month) — **display-level, zero engine change**, R1 untouched (the signal itself keeps using all bars; we just stop presenting a provisional read as settled) | S | replay reproducible; if the mark ships: goldens additive-only, state machine byte-identical, validate case asserts the suffix appears only when the period is genuinely incomplete |
| 107 | ~~**Accumulation-window duration check**~~ — **ran 2026-07-18, closed** (`homily_accum_backtest.py`, BACKTEST_RESULTS §21): ⭐ median 2w / p90 5w (1,295 spells) and 🐳 median 1w vs Danny's 13–52w — his "accumulation period" is a campaign of repeated zone-visits, ours is the visit; the monthly routine already builds the campaign, and #50's within-window tranche clock has no measured room (the window closes first). PLAYBOOK §3 patience paragraph added; gates nothing. *(original scope:)* (from §5l, Jul 2024: "my accumulation period usually lasts 3 months to 1 year"). One-off stat over the committed ledger + 5y replay: distribution of our ⭐-window and 🐳-cluster durations per name (p25/median/p75) vs his 3mo–1yr prior. Pure measurement — calibrates #50's tranche pacing (if our windows run far shorter than his campaigns, the tranche clock, not the signal, is the binding constraint) and earns at most one PLAYBOOK §3 sentence. Gates nothing | S | none beyond reproducibility — measurement only; any PLAYBOOK edit cites the table |
| 108 | ~~**Triple-red continuation stat**~~ — **NULL, closed 2026-07-18** (`homily_triplered_backtest.py`, BACKTEST_RESULTS §22): 2,852 events sit BELOW baseline at all of 5/10/20d on both universes (B: −1.27% vs −0.10% at 5d) — the third straight red close is a slightly worse-than-average add day; `3R` never ships. Consistent with #82's conditioning null. *(original scope:)* (from §5l, IBRX Feb 2026 "Triple Red candles remain in force"). Rides #82's existing run-length harness: condition = 3 consecutive daily RED closes (`daily_candle()` recomputed on prefixes, same method as #101/#102 dating); measure continuation vs baseline fwd 5/10/20d, both universes. #82's own precedent is the null path (ribbon conditioning ran null and shipped nothing) — same rule here: null → closed, nothing ships; separation → a one-word row suffix at most, info-only | S | harness reuse (no new engine code); pre-registered: any suffix ships golden-additive, gates nothing |
| 109 | ~~**Whale-level thresholds study**~~ — **NULL, closed 2026-07-19** (`homily_whalelevel_backtest.py`, BACKTEST_RESULTS §24): the pre-registered flow proxy tops out at 55 — his 50/75 marks live on a *stock* scale (share of chips held) unreachable from OHLCV day-counts; the tradable Q5>Q1 cut holds at 60d in A but flips in the control. No `wh:n%`; #80's rank stays the only whale-comparison surface. *(original scope:)* (from §5m, MARA/WULF · FICO · AMD: Panel-3 whale accumulation as an absolute 0–100% level; "50% to run, 75% to surge"). Build an absolute whale-level proxy from the frozen footprint pieces (e.g. footprint-day share over a rolling window + OBV/A-D share — study-local, engine untouched) and test the threshold *shape*: do names above a high level outperform names below at 60/120d, and is there any kink near the claimed 50/75 marks, point-in-time, both universes? Distinct from #80 (rank) — this is *level* semantics, closer to how he actually quotes it. Null → closed; separation → the level joins the `whale_rank` column as `wh:n%`, info-only, own gate | M | study first (no ship path without it); pre-registered: any digest surface is display-only, golden-additive; his exact % is proprietary — we test our proxy's shape, never claim his numbers |
| 110 | ~~**Retail-crowding warning study**~~ — **NULL, closed 2026-07-19** (`homily_retail_backtest.py`, BACKTEST_RESULTS §25): the pre-registered conjunction fires 33× in ~12,000 rally cuts — a near-empty set (some whale footprint is almost always present on liquid names); returns at n=33 are noise and the #79-verbatim rule fails. No #102 tell; not re-tuned post-hoc. His bearish anatomy stays covered by #79+mLHLL (passed, queued). *(original scope:)* (from §5m, CELH Aug 2024: heavy retail accumulation + NO whale bar = bearish tell). Rides #79's harness: event = rally/elevated-volume window where ALL THREE whale footprints are absent while volume runs hot (the crowd is the only bid) — the mirror of 🐳-present. Fwd 60/120d vs baseline and vs untagged rally days, both universes. If it separates it becomes a #102 tell candidate (own session, dated, info-only); if #79's mLHLL ship happens first they share the surface. Null → closed | M | #79 harness reuse; pre-registered verdict rule copied from #79 (both baselines, both horizons, combined universe); scope guard: held satellites/🚀 candidacy only, never core/index |
| 111 | **Below-IPO quality tag study** — **gate PASSED 2026-07-19** (`homily_ipo_backtest.py` + `ipo_ref.json`, BACKTEST_RESULTS §26): below-IPO obs beat baseline at both horizons combined AND on the control side alone (B 12m +41.9% vs +31.7%, 59% win). Survivorship caveat recorded loudly — the strategy's losers delist out of any still-listed universe. `IPO↓` discovery tag ships info-only (own branch, validate [64]); never an auto-add. *(original scope:)* (from §5m, Apr 2025 Threads thread; OSCR — on that list — became his 2026 winner). New static `ipo_ref.json` (offer price + first-close per screened recent-IPO name, hand-collected once, committed — point-in-time by construction); study = forward 6m/12m of "below IPO reference AND F:≥2/3" names vs the screened-universe baseline, monthly grid, max history available. Sourcing axis only: a pass ships an `IPO↓` discovery-row tag (info-only, golden-additive); the universe stays rule-governed (#65) — this never auto-adds a name | M | needs the one data file + study; pre-registered: tag is discovery-surface only, no universe mutation, no money flow; null → closed and the file stays for future studies |
| 124 | ~~**§8.1 target / needed-DCA line**~~ — **shipped 2026-07-24** (gate: validate [67]; goldens untouched — `render` gains a defaulting `target` kwarg, [52] fixtures pin the without-kwarg path byte-identical): the #94 household block gains one SGD line — `🎯 §8.1 target S$2.0M by 2032-07: book S$X (n%) · needed DCA ≈ S$X/mo @8% · S$X/mo @12% (vs ~S$X/mo logged) — savings lever; changes no investing rule`. Closed-form `required_monthly()` (monthly compounding, round-trip pinned to the cent), trailing-≤6-month logged-flow average as the comparison, '' without FX (an SGD target is never approximated in USD) and after 2032-07. Info-only FOREVER, enforced mechanically: validate greps buyday/positions/daily_run for the target constants — the §8.1 target must never gate money. First read with real numbers: ~S$54k book needs ~S$18–21k/mo at 8–12%, vs ~S$4.5k/mo logged — the gap IS the §8.1 message, printed monthly. **RE-CUT same day (owner: "18-20k is too demoralizing")**: an impossible monthly demand is R0 damage — the line now projects the S$2M ARRIVAL date at the logged pace (`months_to_target` closed form, tightness-pinned), prints the +S$1k/mo pull, and only ever ASKS for the reachable 40-checkpoint number (S$600k by 2032-07 ≈ S$5.6k/mo); validate [67] re-pinned with a <S$10k/mo cap on every printed ask | S | PASSED — [67]: zero-rate degenerate case, past-target 0.0, round-trip to the cent, no-FX/past-date '', additive-only render, 15–25k/mo magnitude band, money-module leak grep |
| 125 | ~~**Buy-day eligibility — CONVICTION ⭐\|🟢 replaces ⭐-only**~~ — **PROMOTED 2026-07-25, owner-directed** (gate artifact `homily_holdadds_backtest.py` + BACKTEST_RESULTS §29; promotions.json `hold-adds`): `homily_buyday.star_candidates` eligibility `state==ACCUMULATE` → `conv_tier==CONVICTION and state in (ACCUMULATE, HOLD)`; #24's RS12 top-3 ranking + #92's 25% cap unchanged; PLAYBOOK §3.4/§3.5 + validate [27] fixtures moved in the same commit. Evidence: 3y walk-forward replay through the LIVE engines (105k signals; replay 99.5% state-matched to the live log), within-CONVICTION HOLD-day entries beat ⭐-day entries at every horizon (60d excess +15.54% vs +5.63%, clustered t 15.8/10.2); DCA-mechanics gate NEW>OLD on both honest windows (2.758/1.243 vs 2.322/1.156 per $). Frozen caveats: survivorship inflates ABSOLUTE returns (§16b stands for do-we-beat-QQQ); NEW MaxDD deeper (−36.4% vs −28.9%), accepted. Demotion armed: `hold_adds_check` executes INSIDE month_start_block monthly; rolling-6m FAIL restores ⭐-only mechanically. R10: 2027-Q2 slot SPENT (ledger now 🐳 Q3 · rs12-top3 Q4 · add-cap 2027-Q1 · hold-adds 2027-Q2 — next free 2027-Q3; FOUR promotion epochs for #14/#14a/#85) | S–M | PASSED its gate — but **ON PROBATION since 2026-07-26**: the owner-requested honest re-test (BACKTEST_RESULTS §31, `homily_holdadds_honest.py`) finds the #125 rule LOSES to pre-#125 star-only on the hype-2021 control at 5y (1.51 vs 1.74) and ties at 10y (2.50 vs 2.52), with both losing to DCA QQQ at 10y (2.86 at −79% dd). The 'too strict on a small universe' excuse fails — median 4 eligible names/month for BOTH arms. §29's edge now reads as a survivorship artifact; do NOT quote §29 without §31. Not demoted: post-hoc tests never reverse a promotion here, only the monthly live-ledger `hold_adds_check` can. [27] re-pinned; registry verify [31] covers the entry |
| 126 | **§4 + §5.2 interaction — ⚠ PARTLY RETRACTED by #130 the same day (STUDY RAN 2026-07-26, nothing shipped)** — `homily_discipline_backtest.py`, rule frozen in docstring before the run, regression-locked to `run_mode('faithful')` at drift 0.00e+00. D-63 kept both disciplines on the reasoning "different jobs, both kept"; run_mode's elif chain meant the PAIR was never measured. Result (BACKTEST_RESULTS §32): **the live combination is worse than its own better half in BOTH bear types** — grinders 33y 39.79 vs §4-alone 49.14 (−19% wealth) at a WORSE −37% vs −29% drawdown; honest 10y 1.98 vs §5.2-alone 3.19 (−38% wealth) for 3pt of drawdown. Mechanism: §4 liquidates satellites at onset so §5.2 has no trash to take, then thirds re-entry rebuys the same names for §5.2 to half-sell again. Pre-committed verdict: prong (b) FAILS decisively; prong (a) criterion had a signed-comparison bug caught with numbers visible — both readings published, deviation disclosed. **RETRACTED 2026-07-26 by #130 (BACKTEST_RESULTS §33)**: this row measured the UNGATED §5.2, which fires ~6.7× more often than the live rule (the F:0–1 condition blocks 85% of ⚪ rows). With the real gate the live combination is **byte-identical to §4 alone in grinders** (49.14 / −29%, ZERO §5.2 sells) — the "19% surrendered at a worse drawdown" finding is an artefact and the "two disciplines cannibalise each other" framing is WITHDRAWN. The proposed bear-aware §5.2 was separately found to be a **no-op** (the bear branch `continue`s before the per-name leg). What survives: on the honest universe the combination returns less than §5.2 alone (1.93 vs 2.77), which is §4's already-priced insurance premium, not a defect. | M | STUDY ONLY — Part III rule 5; any §4/§5.2 edit is a survival/exit recalibration (R10 unthrottled) needing its own gate + registry entry + demotion checker |
| 127 | ~~**Household net worth drops non-USD sleeves while counting their loans (R12 asymmetry)**~~ — **SHIPPED 2026-07-26** (validate [52] extended). `homily_household.book_value` skips `currency != USD` positions (R12, correct for the stock-book %) but `balances.margin_loan_usd` is ONE lump for all borrowing, so a book holding 9992.HK on HKD margin either loses the asset (enter the total loan → net understated by US$12,279) or loses nothing but still omits the HK equity (enter the USD-side loan → understated by US$10,175, the choice taken 2026-07-26 because it is at least internally consistent). Found while switching contributions.json on. **The #94 net-worth headline — and therefore the §8.1 target line that reads it — is low by ~US$10.2k today.** Fix: price non-USD holdings through the FX the block already fetches (it pulls SGD=X; HKD needs one more) and split the loan field per currency, OR state the scope in the printed line. Must not silently change the stock-book %% denominator (R12 stands for the cap math). | S–M | GATE PASSED — `book_value` gains an `fx` map (IO shell fetches `<CUR>=X` per held currency, 1/rate = USD per unit); an unpriceable holding is now RETURNED in `unpriced` and printed as a loud ⚠ line instead of silently shrinking net worth; R12's cap denominator (`homily_positions.stock_book_value`) asserted UNMOVED. Live reconciliation: net US$51,164.18 vs broker US$51,253.91 — residual US$89.73 is IBKR disagreeing with itself (balances `stock_market_value` 29,518.04 vs sum of its own returned USD positions 29,428.92 = 89.12), so 99.1% of the US$10,398 gap closed and the remainder is upstream. Independent check: the combined-gross line now prints 1.34×, byte-matching IBKR's own `leverage` field (it read 1.56× before). Goldens untouched — the household block is first-Monday-only and absent from both fixtures |
| 128 | ~~**Crypto sleeve in the household scorecard, live-marked**~~ — **SHIPPED 2026-07-26, revised same day (#128b)** (validate [52] extended; owner: "bitcoin - 31k sgd, and another 18k usd in altcoins"): `balances.btc_usd` + `alt_usd` (split in the FILE because they are different risk animals and it is what the owner tracks; SUMMED for the printed line). Off-IBKR like SRS/ESPP — asserted NOT to move `ibkr_gross`/`ibkr_loan` or the printed LEVERAGE.md ladder reading. `opening_usd` raised 51253.91 -> 93274.28 in the same commit: balances and opening MUST move together or the scorecard books an instant fake gain of the whole sleeve. Crypto is **45% of household net worth** and is hand-typed, so the block prints a ⚠ staleness line whenever crypto >= 20% of net worth (both branches pinned). **#128b same day**: owner broke the sleeve down — the 'S$31k bitcoin' was IBIT (spot-BTC ETF held away from IBKR), plus 0.08558995 self-custodied BTC, alts revised 18000→16600. `btc_qty` is now MARKED LIVE from BTC-USD each run (US$5,509 @ 64,369.71 on 2026-07-26); `btc_usd` survives only as a fetch-failure fallback so a dead feed can never silently zero the sleeve, and that fallback prints its own ⚠. New `crypto_manual` separates hand-typed from live-marked, and the staleness warning fires on the MANUAL share only — nagging about a live-marked holding trains the owner to ignore the warning. Bug caught in review: `crypto_manual` first counted BTC as manual only when a qty was set but pricing failed, missing the plain-typed-`btc_usd` case entirely; fixed and pinned. Household net worth moves between runs BY DESIGN now — `opening_usd` is the inception-dated basis and must never be re-derived from a later net worth. **#128c**: owner supplied 663 IBIT shares, so marking was GENERALISED rather than copy-pasted a third time — `MARKED_SLEEVES` maps key→symbol and `_marked_value` resolves `<key>_qty` (live) else `<key>_usd` (typed); a future sleeve (ETHA, SOL-USD) is one dict entry plus one field, not another branch. IBIT 663 @ 36.35 = US$24,100.05 (the typed S$31,000-derived figure was US$79.68 light). Hand-typed exposure falls 42% → 17% of net worth, so the nag correctly goes quiet. Format fixed in review: `%g` defaults to 6 significant digits and printed 0.08558995 BTC as `0.0855899` — a WRONG quantity on screen; `.8g` pinned. Additive-only: absent/zero crypto leaves the line byte-identical. | S | GATE PASSED — crypto adds to `net` exactly once · ladder reading identical with/without · 8% quiet vs 42% loud · stock-book denominator (R12) unmoved. NOTE for #14/#94 readers: the household-vs-QQQ verdict now carries a large non-equity bet; #14 stays the signal-skill referee and a crypto-driven result is NOT evidence about the stock engine |
| 129 | ~~**Monthly flows logged + per-sleeve averaging bug**~~ — **SHIPPED 2026-07-26** (validate [67] extended): owner's standing plan logged — S$1,250/mo ESPP + S$3,000/mo IBKR core + S$0 SRS = **S$4,250/mo (US$3,293.11)**, split into per-sleeve rows as contributions.json's schema intends. `BUY_BUDGET_USD` raised 1550 → **2325** (`gh variable set`) so the buy-day copilot deploys what is actually contributed. Owner's +S$1,250/mo SRS from ~2026-10 recorded in a NEW `_standing_plan` block, deliberately NOT logged as a flow: only real months enter `flows[]`, because the counterfactual buys QQQ at each month's actual price and inventing future rows would fabricate the record R-2029 reads. **BUG FOUND AND FIXED**: `target_line` averaged the trailing six *rows*, not months — with sleeve-tagged rows (which the schema documents) it divided the real pace by the sleeve count and printed S$4,250/mo as **S$2,125/mo**, pushing the projected S$2M arrival from 2042 to 2047. Latent for anyone using the documented tag; exposed the first time flows were logged properly. | S | GATE PASSED — split-by-sleeve now reads identically to one combined row, and a two-month fixture asserts the mean is over MONTHS not rows; nag/`contributed` basis unaffected (both already month-set / full-sum) |
| 130 | **§5.2 with its F-gate — the repo's best-measured arm, tested as it actually runs (STUDY RAN 2026-07-26, nothing shipped)** — `homily_fgate_backtest.py`, rule frozen before the run; F rebuilt point-in-time from EDGAR (`filed` <= month) and scored with the LIVE `checks_from` (R6). Verdict (a): §5.2 STILL ADDS (gated 2.77 vs hold 2.51, honest 10y) but at **half** the published magnitude and it **does NOT beat QQQ** (2.86) although the ungated version did. Grinders: the live rule fires **once in 33 years** (563 blocked), giving 76.61 vs the ungated 47.39 — §5.2 never wrecked grinders, the proxy did. Forces the §32/#126 retraction above. PROPOSED TO OWNER, not executed: correct §3's headline, §16b's league table and #51's promotion basis, all of which quote ungated numbers. | M | STUDY ONLY — Part III rule 5. Known issue recorded not fixed: `trim_flags` tests the F NUMERATOR so F:1/1 fires while F:2/2 does not (24 live rows) — own item |
| 131 | ~~**Dual volatility-hole bottom marker**~~ — **RAN 2026-08-13, NULL, CLOSED** (BACKTEST_RESULTS §34, `homily_dualvh_backtest.py`, rule frozen in docstring first): dual bottoming breakouts are rare (n=18 < the pre-registered 20) and LOSE to the single-hole baseline on both horizons (fwd60 +1.7% vs +6.2%; fwd120 +13.1% vs +20.6%); underpowered-n caveat and the monthly-TF #77 null both recorded. `find_hole` stays one-cluster; no ×2 surface. Original: (from §5n, INTC Jul 2026) — his INTC long-term bottom call rests on TWO holes stacked at one base, and `homily_vol.find_hole` returns only the most recent cluster, so a second hole is structurally invisible today. Study: point-in-time detector for a second hole forming within N bars while the first is still INSIDE/unresolved; event study fwd 60/120d vs the single-hole 🔵 baseline, both universes, hype-2021 control, N and the verdict frozen in the docstring before the run | S–M study | tie-or-beat single-hole 🔵 event returns on ≥20 dual events or NULL → closed honestly (#77 precedent — the monthly-TF half of this claim already nulled). Any digest surface (a `×2` mark on the existing 🔵 row) ships display-only with its own validate case + goldens untouched |
| 132 | ~~**Buy-signal density as a selection challenger**~~ — **RAN 2026-08-13, NULL, CLOSED** (BACKTEST_RESULTS §35, `homily_sigdensity_backtest.py`, rule frozen in docstring first; #24 harness unchanged, equal-all regression OK every window): dens-top3 loses to rs12-top3 on ALL THREE universe-B read windows (1.76/1.89 · 1.73/1.82 · 2.74/2.84) — the FIFTH dip-affinity-loses-to-strength result; high signal count marks names that keep returning to support. rs12-top3 stands. Shallower-MaxDD side-observation recorded UNREGISTERED in §35. Original: (from §5n, HOOD campaign) — his conviction expresses as REPEATED prints on one name over months (>10 flags, 6+ posted buy orders); we rank names by rs12 and whale_rank but have never ranked by trailing signal COUNT. Study: 13-week trailing count of buy-class prints (⭐/🔵/🐳/⤴) per name as a cross-sectional ranking, entered in the #120 bake-off harness vs rs12-top3 and whale-top3 on all three honest windows + 2021 control; count window frozen before the run | M study | tie-or-beat rs12-top3 on all three honest windows incl. hype-2021; else closed. The study is free; a promotion (if ever) pays the normal R10 selection price — next free slot 2027-Q3 |
| 133 | ~~**Bear-regime census — audit the book's only working exit**~~ — **RAN 2026-08-13 (diagnostic, no gate), findings in BACKTEST_RESULTS §36** (`homily_regimecensus_backtest.py`): every signal the live dual-index 10m-SMA rule ever gave, 1999-12→2026-07. 21 BEAR spells (≈1/15mo, ~4× PLAYBOOK §4's "handful per decade"), premium re-entries 17/21, payouts exactly where they matter (2000/2002/2008/2022); COVID fired at the bottom month-end. Plus ONE LIVE DEFECT (→#134) and the measured-vs-playbook re-entry divergence (→#135) | S study | DIAGNOSTIC — census only; each finding ships through its own item below |
| 134 | ~~**Regime partial-month defect + robustness**~~ — **SHIPPED 2026-08-13** (Phase-C, engine_freeze.json re-pinned same commit; gate validate [69] + [12] re-expressed on the injectable clock): `completed_months()` month-key filter (a month is complete because the calendar left it, never by array position — Yahoo 1mo shows the running month once, twice, or not at all), `fetch_monthly` 3-attempt retry, `monthly_from_daily` fallback (independent endpoint, same rule), snapshot `regime_last_good` carried through failed days ("regime" stays None — consumers must see unavailability), digest dark-spell aging + 🚨 at ≥3 days (`regime_stale` kwarg, default  keeps goldens byte-identical). Live smoke: month-end judgement now reads July 747.03/687.99 (+6.0%/+5.9%), BULL. Original:  Yahoo 1mo double-reports the current month (period row + live row), `sma10_state`'s single `[:-1]` keeps one partial row, so the live banner judges a MID-MONTH close as the completed month-end (proven live 2026-08-13: QQQ 718.45 partial-Aug read as "completed" vs July's true 687.99; banner margins +8.0/+9.0 vs true +6.0/+5.9). Fix = month-key filter (drop every row of the last row's month), same fix in `homily_regime_backtest.run`; validate fixture pins the double-row case WITHOUT network; fold in regime ops-hardening: retry + fetch_daily-resample fallback, and a loud staleness line when the regime has been unavailable ≥N runs (buy-day's treat-None-as-normal stands, but the silence must not be free). Gate: fixture-pinned boundary cases + engine_freeze.json manifest update + goldens byte-identical on non-boundary days | S–M | NOT RUN — needs its own session; regime label changes on boundary days are the POINT, so the gate pins fixtures, not history |
| 135 | ~~**Re-entry rule: BOTH-above vs EITHER-above**~~ — **RAN 2026-08-13, verdict: EITHER (BACKTEST_RESULTS §38, `homily_reentry_backtest.py`)**: run_mode gained `reentry=` (default kwarg-inert, drift 0.00e+00 every window). Pre-registered: BOTH keeps §4.7 only if ≥ EITHER on both honest windows at not-worse MaxDD — 5y holds (1.34/−38 vs 1.32/−42) but 10y FAILS (1.56 vs 1.69); grinders context 38.87 vs 49.14 at equal −29%. §4.7 re-worded to either-above via #137. Original:  D-63's run_mode re-enters on either-above (that produced §4's −1pt/yr headline); PLAYBOOK §4.7 prescribes both-above (🐂). Census: divergence up to 16pt (2000) / 35pt (2008 bull-trap skip) / 19pt (2022). Study = run_mode variant `reentry="both"`, all committed windows + episode isolations, both universes; whichever wins on the honest windows becomes BOTH the code's and §4.7's rule, and §4's cost headline gets re-published from the winning arm | M study | pre-register: adopt BOTH only if ≥ EITHER on both honest windows at ≤ equal MaxDD; else PLAYBOOK §4.7 is re-worded to the measured either-above rule. Docs+study; any run_mode edit is harness-only (not frozen) but regression-locked to the committed tables |
| 136 | ~~**trim_flags F ratio fix**~~ — **SHIPPED 2026-08-13** (gate validate [70]; BACKTEST_RESULTS §37): "failing" = fewer than half the applicable checks pass (`homily_positions.f_failing`, one definition; timestop_watch pairing + PLAYBOOK §4.3a/§5.2 moved same commit). Candidate "thin" rule (ratio OR m==1) measured under a selection rule frozen BEFORE it ran — FAILED both prongs (10y 2.65 < 2.775; 5y 1.74 vs 1.78) → pure ratio shipped. Honest admission in §37: correctly-gated §5.2 ≈ hold on the honest 10y (2.52 vs 2.51, 14 sells) and fires 0× in 33y grinders — the numerator bug was carrying most of the arm's remaining measured value via mislabeled thin-coverage sells. Original:  `re.match(r"F:(\d)")` reads the numerator, so F:1/1 fires §5.2's sell-half flag while F:2/2 does not (24 live rows F:1/1 today) — and §4 step 3a uses the same F:0–1 notion to pick what gets sold FIRST at a 🐻 onset. Design decision needed (ratio ≤50%? require m≥2? F:0/1 vs F:1/1?), then: fix + [55]-style validate cases both sides of every boundary + PLAYBOOK §4.3a/§5.2 wording aligned in the same commit | S | NOT RUN — flag/info code (homily_positions is not frozen) but it steers owner sells; gate = pinned fixtures for 0/1, 1/1, 1/2, 2/2, 2/4 + goldens re-pinned deliberately if any live row's flag text moves |
| 137 | ~~**PLAYBOOK §4 expectations rewrite**~~ — **SHIPPED 2026-08-13**: §4 trigger/frequency paragraphs re-written from §36 (≈1 signal/15 months, 21 in 1999–2026, premium re-entry 17/21, "first live 🐻 will most likely be a false alarm — following it anyway is the deal"; the "handful of times per decade" claim retired as ~4× wrong), COVID + 2025-03/2026-03 named; §4.7 re-entry re-worded to the MEASURED either-above rule per #135/§38 and the 🐻 banner action text in homily_regime moved in lock-step (one string; engine_freeze re-pinned; goldens use a BULL fixture, untouched). All numbers quoted from §36/§38 only. Original:  replace "a handful of times per decade" with the census reality — ≈1 spell/15 months, median 1–2 months, 17/21 re-entered higher, first live 🐻 will MOST LIKELY be a false alarm and following it anyway is the deal; add the census episode table + the COVID limitation verbatim; cost stays D-63's −1pt/yr (unchanged, it already includes whipsaws) | S | docs gate: numbers quoted only from §36; no rule changes ride along |
| 138 | ~~**Leverage drift — the ladder was certified on a policy we do not run**~~ — **RAN 2026-08-13, verdict: 1.30× HOLDS (BACKTEST_RESULTS §39, `homily_levdrift_backtest.py` + the policy axis in `homily_leverage_backtest.py`)**: the live `ratchet` policy passes everywhere `rebal` passes — QQQ worst equity/position 0.66 vs §15's 0.68, core book 0.62 — so per the frozen verdict the ladder does NOT shrink and LEVERAGE.md keeps 1.30/1.15/1.00 with a footnote. **This contradicts the expectation the session opened with** (softer ladder, §5 shrink, #91 retraction); shipped as measured, rule 6. Drift measured: 1.30× peaks **1.52× on QQQ, 1.62× on the core book** — the owner's "40%" was right and slightly conservative, and it is not the risk (0.62 is 2.5× clear of the 0.25 boundary). **The load-bearing control is the 🐻 margin-to-zero rule, not the cap:** the ONLY breaches in the study are the `fixed` arm that ignores the regime signal — 1.30× called on QQQ 2008-11-19, 1.50× on the core book 2022-07-01 at base AND stress. That re-prices #134 — a regime-print defect is a fault in the only control keeping levered books solvent. §15 regression-locked and reproduced exactly (2.57/2.29/9.43). Recorded not shipped: §2's core-ban REASONING assumes a constant-L book, which `ratchet` is not — a real gap in the argument, but NOT grounds to lift the ban on monthly-resolution, post-2016, survivor-biased evidence (own item, rule 5). Original:  **owner-requested 2026-08-13** ("how do we fix the issue of leverage growing when stocks are suffering drawdowns? If we say 30% leverage is safe, then when drawdown comes our leverage becomes 40% right even without borrowing more"). Owner is arithmetically right: debt is fixed in dollars, equity absorbs the whole loss, so constant-debt 1.30× reads 1.41× after −20% and 1.86× after −50%. But the drifted ratio is a SYMPTOM — the call point was fixed at entry (uniform d\*(1.30) = −69.2%), so the reading moving does not move the risk. The real finding is a test-vs-live gap of the #130 class: `homily_leverage_backtest.run_arm` resets `pos, debt = tgt*eq, (tgt−1)*eq` on the first session of EVERY month, which in a decline **sells and pays down debt** — verified empirically 2026-08-13, not read off the docstring (synthetic −0.3%/day path, 4/4 month boundaries SELLS+PAYS DOWN). LEVERAGE.md §1's "worst measured path reached equity/position 0.68" is therefore the CONSTANT-LEVERAGE number. The live account is constant-debt (§4 grandfathered shrink-only, §5 never-sell) against a CONCENTRATED CORE book — and §2 already states in arithmetic that the core book's −59…−76% measured paths sit INSIDE the call boundary at any constant L ≥ 1.25. Neither the live policy nor the live asset was ever the thing that passed. Study: two new policy arms + a core-book series | M study | **PRE-REGISTERED 2026-08-13 BEFORE THE RUN.** Arms × {`rebal` = existing monthly reset, regression-locked to §15 · `ratchet` = LEVERAGE.md as written (lever UP to cap in 🐂, NEVER sell to delever, debt→0 at 🐻 onset) · `fixed` = borrow once, never adjust, ignore the 🐻 signal} × L ∈ {1.15, 1.30, 1.50} × asset ∈ {QQQ daily (continuity with §15), core-book NAV from `run_emergent`} × financing {5.8% base, 7.8% stress}. **(a) SURVIVAL (primary):** breach ⇔ `equity/position < 0.25` on any observation; a cell PASSES iff zero breaches in every window. Both sides positive, lower is worse — no sign trap (worked: 0.24 < 0.25 → BREACH; 0.68 → safe). **(b) DRIFT (descriptive, no pass/fail):** max L reached per window by the never-delever arms — the owner's "1.30 became X" number. **(c) COST OF DELEVERING:** written sign-safe against the #126 trap — MaxDD are NEGATIVE fractions, so the test is `maxdd_ratchet >= maxdd_rebal − 0.05` (worked: rebal −0.29, ratchet −0.37 → −0.37 >= −0.34 is FALSE → ratchet worse by more than tolerance). **Pre-committed verdict:** if `ratchet`@1.30 breaches anywhere `rebal`@1.30 does not, LEVERAGE.md §1's 1.30 is certified for the rebalanced policy ONLY, and §5's mechanical shrink applies (1.30→1.15) — a delever-band alternative is a NEW rule needing its own item, never shipped in the same session (Part III rule 5). If `ratchet`@1.30 survives everywhere, the drift is cosmetic and LEVERAGE.md gains that footnote. Publish the core-book cells either way (rule 6). **Declared limitation, flattering direction:** the core NAV from `run_emergent` is MONTHLY, so intramonth lows are invisible and core-arm survival is FLATTERED — same direction as §1's maintenance caveat, stated not corrected. `run_emergent` gains an optional `nav_out=None` sink ONLY (return shape and all committed numbers unchanged) |
| 140 | **PROPOSED — universe capacity cut: a dollar-volume BAND, not a top-N ceiling.** D-65's L2 keeps the top ~120 L1 survivors ranked by 60d dollar volume — a pure POPULARITY rank — while 🚀's G1 rejects anything ≥$5B/day. Measured on the committed list 2026-08-14: **18 of 124 names (15%) sit above G1's ceiling** (MU $44B/d, NVDA $32B/d, SNDK $20B/d, TSLA, SPCX, AMD, INTC, AAPL …) and can therefore NEVER carry the tier the discovery layer exists to feed, while the small end is thin (smallest ZETA $165M/d, only a handful under $1B). The two rules pull opposite ways: names enter for being heavily traded and are disqualified from 🚀 for the same reason. Proposal: replace the flat top-N with a BANDED allocation — reserve a declared share of slots for the G1-eligible range ($50M–$5B/d) so the range the conviction tier can actually operate in is populated by construction, not by leftovers. Holdings + 🚀-stickiness carve-outs unchanged | M | **Retrospective backtest is NOT available and the item may not pretend otherwise**: universe.json is a 2026 artifact and no point-in-time constituent/volume source exists here (same limitation §5c named for market cap; #113's vault would be the enabler). Gate is therefore FORWARD, mirroring D-65's own shadow method — build the banded list, run it in parallel as a second shadow tag for one quarter, and adopt only if it (a) retains ≥90% of the ⭐/🔵 setups the incumbent cut surfaced, (b) surfaces ≥3 G1-ELIGIBLE setups the incumbent cut structurally could not, and (c) those extra setups clear the same F/quality checks as incumbent rows. Adoption is a SELECTION change → pays the normal R10 slot (next free 2027-Q3); the study and the shadow run are free |
| 141 | **PROPOSED — discovery blind-spot audit + a COVERAGE prong for the #65 adoption read.** #65's pre-committed gate asks two CONTINUITY questions (keeps ≥90% of hand-list names · finds ≥1 setup it missed). Neither asks the question that decides alpha: *what can the pipeline structurally never see?* Danny's own entries were small and unloved AT ENTRY (RKLB ~$5.5, PLTR ~$8.8, NBIS pre-run, OSCR/IBRX/CLSK) — exactly the profile a top-N-by-volume cut reaches only AFTER the move, by which time G1 locks them out. Study: for a declared list of large winners, reconstruct each name's price/volume/bar-count at successive points BEFORE its run and report, per name, the first date it would have (i) cleared L1's hard gates, (ii) made the top-120 cut, (iii) still been G1-eligible — i.e. the window, if any, in which our pipeline could have surfaced it at a size that still had room to multiply. Output = a coverage rate + the median lateness, and it feeds #140's band width | M study | **Declared BEFORE the ~2026-10 #65 read so it is not post-hoc**, and it ADDS a third prong to that read rather than loosening the two pre-registered ones (a gate may be made stricter before the read, never looser after it). **Frozen honesty clause: the winner list is chosen with hindsight, so this measures REACHABILITY ONLY — it is never evidence the engine would have BOUGHT them, and any write-up quoting it as skill is wrong on its face.** Winner list + the pre-run cut-off dates frozen in the study docstring before the first fetch; a null (pipeline reaches them only after the move) is the expected result and closes honestly |
| 142 | **PROPOSED (PREREQUISITE for all VH work) — volatility-hole fidelity audit: does our detector find HIS holes?** §5o's probe put 3 of 4 published zones far from ours (RBRK ours 63.20–67.37 vs his 49–50; HOOD 104.45–120.88 vs 66–77; MSFT 456.89–483.46 vs 367–400; GOOGL 161.01–165.82 vs 166–174 = the only near-miss). Our VH is a documented approximation whose ERROR has never been measured, so #77's and #131's nulls, and the committed daily event study, may all be statements about our construct alone. Build a committed `danny_vh_claims.json` from every DATED, PRICED VH claim in §5k/§5l/§5m/§5o (~10–14 cases, transcribed verbatim with URL + date + stated zone, owner-checkable), then score our detector: does a hole exist within ±N weeks whose zone OVERLAPS his? Report hit rate, median zone offset, and the SIGNED direction of the error. Then a report-only sensitivity sweep of `REF_WIN`/`MAX_GAP`/`VOL_WIN` and daily-vs-weekly bars | M study | **Diagnostic first, tuning second, never confused.** Prong 1 ships nothing. Prong 2 may only REPORT a better setting: adopting it rewrites every downstream VH result, so it is a Phase-C engine edit with its own session, gate, `engine_freeze.json` re-pin and a mandatory re-run of §7/§34 publishing the deltas. Frozen honesty clause: a low hit rate does NOT mean his method is wrong or ours is — it means they are different objects, and every past VH conclusion must then be re-labelled as being about ours |
| 143 | **PROPOSED — the descending-blue-ribbon primitive + the conjunction, measured against its base rate.** We compute `EMA10>EMA30` on weekly closes ONLY as check 2 of the 0–4 circle score; it is never exposed, and no slope exists anywhere in the repo, so "descending blue ribbon" is currently uncomputable. Add a read-only `ribbon_state(weekly_closes) -> (blue, descending, slope)` (derived helper — `homily_clone` is FROZEN and untouched, same pattern as #82), publish the base rates §5o measured (blue 48.6%, blue+descending 45.0%), then run the conjunction event study at HIS horizons — 6 weeks / 3 months / 6 months — with four arms: VH-only · ribbon-only · **VH + descending blue** · neither; both universes + hype-2021 control | M study | **The base rate IS the gate.** A 45%-prevalence filter must beat the unconditional forward return by a margin that survives its own frequency: PASS requires the conjunction arm to beat BOTH single-condition arms AND the unconditional baseline at 6wk and 6mo on the honest universe, n≥30 conjunction events. Anything less = NULL and the ribbon stays a score component. Prior worth stating: ribbon-derived conditioning has already run null twice (#82 run-length conditioning, #108 triple-red). No digest surface ships from the study session (Part III rule 5) |
| 144 | **PROPOSED — hole COUNT as a weakness proxy: the #131 re-cut this post actually implies.** His rule is conditional ("1 hole for strong, 2–3 for weak"), so hole count should predict WHICH bottom is real *given* the name's strength — not that more holes are better, which is what #131 tested and correctly rejected. Re-cut: classify each name point-in-time by RS12 tertile (live `homily_conviction._ret` deltas vs SPY, R6), then measure forward 6wk/3mo/6mo returns from the Nth hole resolution for N=1,2,3, **split by tertile**. His claim predicts an interaction: STRONG names — hole 1 already works, 2–3 add nothing; WEAK names — hole 1 underperforms and 2–3 is where the bottom lands. #131's detector (`homily_dualvh_backtest.events`) is reused unchanged, so this is a conditioning layer, not new detection | M study | Pre-register the INTERACTION, not a main effect: PASS only if (a) weak tertile — hole 2/3 beats hole 1 at 6wk AND 6mo, and (b) strong tertile — hole 1 ≥ hole 2/3; n≥20 per reported cell, honest universe. A main effect with no interaction is a NULL for this hypothesis and is reported as one (#131 already supplies the pooled main effect, so re-finding it proves nothing). Gated behind #142: if our detector does not find his holes, this measures the ordinal count of OUR holes and the headline must say exactly that |
| 145 | **PROPOSED (Phase C, gated behind #142) — VH detector refinement: adopt only what survives the OLD studies.** #142's diagnostic (D-142, 2026-08-14) named three hypotheses for why our zones miss his: **H1** age expiry (his zone "remains valid until invalidated by either side"; ours dies on `MAX_AGE`), **H2** latest-cluster-only (`find_hole` discards history — MSFT's matching zone was a Dec-2023 cluster at 362.90–377.64 vs his 367–400), **H3** the volatility definition itself (at all four of his bottoms our relvol sat 1.4–2.6× ABOVE its 60-period minimum, so no age or lookback setting can put a hole there). A 30-cell sweep reaches 3/4 overlap at `ref_win`≈10–15 with no expiry — **explicitly logged as a possible overfit, not a result** (4 self-selected cases, 2 swept parameters). This item implements whichever of H1/H2 survive the full ~14-case audit, as a Phase-C engine edit to `homily_vol.py` | M | **Adoption is gated on RETURNS, not on match rate.** Required in one commit: engine edit + `engine_freeze.json` re-pin + validate case pinning the new semantics on fixtures + **a re-run of §7 (#77 multi-TF) and §34 (#131 dual-VH) with the deltas published in BACKTEST_RESULTS either way**. Adopt only if those re-runs are NO WORSE than the committed numbers; a change that lifts fidelity and lowers returns is REJECTED and the finding recorded. H3 is explicitly OUT of scope here — a different volatility construct is a new indicator needing its own gate, not a refinement of this one |
| 147 | ~~**Crypto cycle sleeve — leverage sizing + DCA schedule for a 4-year-cycle BTC accumulation mandate**~~ — **RAN 2026-08-20, leverage FAILED its pre-registered gate, sleeve policy SHIPPED UNLEVERED** (BACKTEST_RESULTS §41, `homily_cryptocycle_backtest.py`, seven rules frozen in the docstring before the first fetch; policy artifact `CRYPTO_SLEEVE.md`). Owner asked to size 3x (then 2x) leverage on IBIT/ETHA, mid-session moved the venue to **Hyperliquid perps** and the objective to **BTC UNITS** (holds zero BTC after the 2026-08 reset, commit 5256145). Three findings. **(a) Funding is charged on NOTIONAL, not on borrowings** — the cost object §15/§39 never modelled, because both assume a broker margin loan: BTC mean 11.61%/yr = 34.8% of equity at 3x, and 44.7% annualised through 2020-10→2021-04. The sharpest number is unlevered — a **1x perp returned 0.21x where spot DCA returned 0.90x** over 2020-01→2022-12, funding taking $49,703 on $72,000 contributed. A perp is not a holding instrument and the 4-year cycle is a holding thesis. **(b) R7 (levered beats spot on UNITS in BOTH accumulation analogs) returned 1/2 on every setting** — 2x/3x, const/entry; the failing analog is −98% of units, because a liquidation is permanent when the metric is coins. **(c) The cycle thesis is itself the argument against leverage**: out-of-sample trough projection is good (errors −47d/−10d → this cycle 2026-10-24, window 2026-08-25…12-23), but completed peak→trough drawdowns (−83.1%, −75.7%) imply a trough at $30,315–$21,083, **below the liquidation price of a position opened today at 3x ($48,437), 2x ($36,328) and 1.5x**. What PASSED: **cycle-weighted unlevered DCA** (2.5× inside the trough window) beat flat in both analogs (+22.2%, +14.4% in units) — the opposite of the equity book, where hold-cash-for-dips has failed five times, because here the dip date carries a measured ±47d error rather than being unknown. Also recorded: the original IBKR route dies on arithmetic alone (Reg T caps 2x; US$4k/mo = 120% of savings; account already 1.216× vs the 1.30 cap). ETH banned from leverage (every setting >1.5x has a negative median; 3x const 0.30x with 100% of windows liquidated) | M study | **Sleeve-local: touches no signal, no selection rule, no part of the stock engine**; §9.0's beat-QQQ bar unaffected, and per #128 a crypto result is not evidence about the stock engine in either direction. Caveats pinned in §41.7 and repeated in any quote: **n=2 completed accumulation analogs**, funding unmeasured before 2019-09 (baseline-modelled, so pre-2019 is optimistic), the 2013 peak predates the Yahoo series, and the cycle estimator has three observations. `CRYPTO_SLEEVE.md` ships PROPOSED with an unsigned owner line — it is a refusal plus the four conditions (§3) under which leverage may be reconsidered, not a promotion |
| 148 | ~~**Crypto-cycle leverage-ON signal — tested, revised, and wired into the digest**~~ — **RAN + SHIPPED 2026-08-21** (BACKTEST_RESULTS §42; `homily_cryptocycle.py`, validate [72]; CRYPTO_SLEEVE.md §3 amended). #147 gated sleeve leverage behind a markup confirmation quoted as +40%/8wk and flagged in §41 as *fitted to 2 firings*; owner asked *"what is the signal to go on leverage?"* so it was measured. Scored across three completed cycles on false positives (fires, then price makes a NEW low), lateness, and upside remaining. **The HOLD is the rule, not the threshold**: every 4wk/6wk variant produced a false positive (canonical failure 2018-03-08 — fired at $9,395, BTC then fell to $3,191, −66% AFTER the go signal and 282d before the real trough = a wipeout at 3x), every 8wk variant produced none, 3/3. Constant revised **0.40 → 0.30** (geo-mean upside 14.0× vs 13.5×, fires ~42d earlier, identical FP behaviour) — but that ranking is carried by the 2015 cycle alone, so the doc now says explicitly that the hold is defensible at n=3 and the threshold is not. A 200d-SMA conjunction was tested and REJECTED (11.6×, delays the 2015 entry to 328d) and is recorded as a rejected complication, not a knob. Cost of the rule stated plainly: fires 86–167d after the trough at +38…+176% above the low — the first leg is given up by construction and is bought by §41.6's unlevered cycle-weighting instead. Digest line runs the IDENTICAL loop as the study so the two cannot drift; renders 🟠 OFF / 🟡 ARMING / 🟢 CONFIRMED under the leverage ladder. **Live: the signal ARMED 2026-08-21** (low $57,748, trigger $75,072, BTC $75,360), recorded before the fact | S | **Additive-only** — `crypto=""` is byte-identical to omitting it, golden [16] unmoved, a failed BTC fetch is non-fatal. The line is a **watch, not an authorisation**: it reports CRYPTO_SLEEVE §3's timing condition ONLY; conditions 1/3/4 (trough window closed, BTC-only, sanctioned size) still bind and the owner line on that policy remains UNSIGNED. Caveats travel: three cycles, 2015 dominates every geometric mean, and 'lateness' is only definable after the fact · **Extended 2026-08-21 (§42.1/§42.2)** after the owner asked how confident the constant is: the 8wk hold re-tested on **25 bear-phase episodes** (not 3 cycles) — median duration 2d, longest 46d, and 0/25 survive 56d (4wk 2/25, 6wk 1/25). The mechanism is real but the **margin is 10 days** over the worst observed rally; 12wk is also 0/25 and is the fallback if a breach ever occurs. Also recorded BEFORE it resolves: the signal armed at −42.7% from peak vs prior confirmations at −54…−80%, on a −53.7% drawdown vs completed cycles' −75.7%/−83.1% — either the cycle is milder or this is the first false positive in 25, and §42.2 takes no side. `CRYPTO_PLAYBOOK.md` ships as the operating manual (phases, monthly routine, digest-state table, never-bend rules, per-claim confidence, falsifiers) |
| 149 | ~~**Harvest-to-spot: the levered structure that PASSES its gate**~~ — **RAN 2026-08-20, WRITTEN UP 2026-08-21** (BACKTEST_RESULTS §43). Owner proposed a structure §41 never tested: *"monthly rebalancing close out positions that are in profit and move them to spot, and dca only leveraged positions."* Not §41's failed arm with a friendlier constant — a different mechanism, so it got its OWN pre-registered gate (G1 beat spot in both analogs · G2 beat plain levered perp · G3 retain ≥50% in the losing analog · G4 harvested spot never zero). **G1 PASS at 3× (FAIL at 2×), G3 PASS, G2 FAIL everywhere** — harvest loses to unharvested leverage in the winning analog (+53.7% vs +102.5%); G2 was arguably mis-specified (it benchmarks an arm with a 0.07× worst case) but it was pre-registered and failed, and is recorded as such rather than re-specified. The finding is the TAIL: on 45 rolling 3y windows the worst case moves **0.07× → 0.96× while the median RISES 1.18× → 1.39×** (93% beat spot) — a Pareto improvement, and the reason 3× is defensible here when §41.4 found held leverage indefensible at 2× and 3× alike. Engine still liquidated in 69% of windows; it no longer matters because gains were swept out first. Withdrawal feasibility audited against HL's rule (withdrawable = AV − initial margin): zero blocked sweeps. **ETH still fails** (median 0.98×, 100% liquidated) — §4 ban unchanged. **Where it does NOT work:** a monotonic glide to the cycle trough banks $0 and returns 0.29×/0.20× vs spot's 0.64×/0.54% — every flattering window contained a rally, so the structure stays gated behind §42's confirmation | M study | **Process failure recorded:** §43 was run 2026-08-20 but written up only after `CRYPTO_PLAYBOOK.md` shipped citing 3× against a CRYPTO_SLEEVE §3 that still capped at ≤2.0× — the two docs contradicted each other for one day. Fixed by making the cap STRUCTURE-DEPENDENT (≤3× inside the sweep, ≤2× without) in both files, with the amendment noted in-place rather than silently corrected. Also pinned: there is no state in which this sleeve is 'leverage only' — the W cap self-limits, and contributions arriving at a full engine sweep straight to spot the same month |
| 150 | ~~**Crypto-cycle watch read the UNSETTLED bar — the clock could start on a wick**~~ — **FIXED 2026-08-21 same day as #148 shipped** (`homily_cryptocycle.py`, validate [72] extended). Crypto trades 24/7, so a live Yahoo fetch always returns a provisional last bar whose 'close' is just the current quote. On ship day that provisional print crossed the trigger intraday ($75,360 vs a $75,072 trigger) and **fell back below it the same session** — and the session reported to the owner as 'the signal ARMED today' had in fact not armed on any settled close (2026-08-19 settled at $69,266, 8.4% below the trigger). Reading the unfinished bar would have started a 56-day irreversible clock on a wick, which is **not the rule §42 measured** — that backtest evaluated settled daily closes throughout, so live and backtest had silently diverged on day one. Fix: `cycle_state` drops any bar dated >= asof before arming/disarming; the provisional price is still carried as `live_price` and printed so the digest shows where the tape is, flagged 'unsettled — the clock reads the <date> close, not the tape'. Contrast **#106**, which MARKS provisional bars rather than dropping them: that is display-only, this one gates an irreversible action, so it drops | S | validate [72] pins it with a wick fixture (an unsettled 2x spike must NOT arm) plus the report-but-do-not-act assertions. **Correction recorded in-place rather than quietly amended**: the #148 row and BACKTEST_RESULTS §42's live-status paragraph both claimed an arming that a settled close never supported |
| 151 | ~~**BTC bull/bear regime + cycle phase + a single leverage verdict in the digest**~~ — **SHIPPED 2026-08-21** (BACKTEST_RESULTS §44; `homily_cryptocycle.py`, validate [73]). Owner asked the digest to say plainly whether BTC is bull or bear, to reuse the SPY/QQQ regime method, and to be unambiguous about when leverage is allowed. **The stock book's 10m-SMA rule transfers on its own evidence**: over 134 BTC months, BULL averages +8.61% forward vs BEAR +0.96%, and long-only-in-BULL returns 395.5× vs buy-and-hold 284.2× at 60.0% max drawdown vs 75.6%. **But it is not a safe ENTRY gate, and the first test said otherwise because the window was wrong** — measured from 10 months post-peak regime-only looked best (+74.6%/+96.3%), which silently excludes its worst behaviour: the SMA mislabels **9/35 markdown months as BULL (26%)**, clustered right after the peak (2017-12 and 2018-01 read BULL while BTC fell $19k→$10k). Re-run PEAK-TO-PEAK: regime-only earns the best return with **5 liquidations** vs the combined gate's **1** — and under CRYPTO_SLEEVE §6 one realised liquidation bans sleeve leverage permanently, so that arm never reaches the return it is credited with. **Rule adopted: §42's signal guards the ENTRY, the regime guards the EXIT** — the signal cannot fire in a markdown but never turns off; the regime turns off but fires early in a markdown; each covers the other's hole | S | Two lines above the timing detail: regime + 4-year-cycle phase, then a single ✅ PERMITTED / ❌ NO LEVERAGE verdict that names EVERY open gate, not the first. Running month never votes (#134 invariant, pinned in [73]). Additive-only. **Live: 🐻 BEAR** (month-end $62,814 vs 10m SMA $77,257), phase MARKDOWN, verdict ❌ on all three counts. Caveats: ~3 cycles of months; whipsaw is 1 flip/10.1mo with 7/14 runs under 3mo, so the exit gate will sometimes delever into a recovery — the real price of 5→1 liquidations · **§44.1 added 2026-08-21** after the owner asked whether the 8wk hold is still necessary now that the regime gates: swept peak-to-peak with the regime EXIT in series, **4wk and 6wk BEAT 8wk in both windows at identical liquidation counts** (16.6552/4.3868 vs 16.0561/4.0419). The 4wk arm confirms 2018-03-08 INSIDE the markdown and is NOT liquidated there — the regime flipped BEAR in 2018-04 and unwound it first; both arms liquidate on the same date 2021-05-19. An earlier draft asserted the 4wk arm blew up in 2018; the trace disproves it and the correction is in-place. **8wk RETAINED as a robustness choice, not a measured one**, and logged as such: of 25 bear episodes, 2 survive 4wk / 1 survives 6wk / 0 survive 8wk, and the one that matters (2018-02-08, 46d) had the regime reading BULL throughout — so at 4wk/6wk only the regime exit stands between the engine and a markdown, a second-order dependency on a gate flipping every 10.1mo. Cost of the choice is measured at −3.7%/−8.5% of ending units. `CRYPTO_PLAYBOOK.md` rewritten as a step-by-step (Part A do-this-month · B the four gates · C phases · D never-bend rules · E confidence + falsifiers) |

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

**2026-07-25 (planning era, execution) · #118(c) shipped and it BREAKS #118's
own "no standing infra, no new secrets kept live" clause — deliberately,
scoped, recorded here rather than reinterpreted quietly.** The owner asked
whether GitHub's 60-day inactivity disable threatens a repo entering a
long-term planning phase. It does, and worse than the docs suggest: the repo
is **public**, only commits reset the clock (issues/PRs/tags do not), and the
disable takes the whole workflow file down including `workflow_dispatch`, so
the manual re-run button dies with the schedule. Today the repo is safe by
accident — `daily refine` pushes real state nearly every weekday — but that
is exactly the signal a broken run removes, so "CI silently died" and "GitHub
disabled CI" are one 60-day fuse, lit at the moment nobody is watching.

The fix could not be a GitHub-hosted checker: it would be disabled by the
same event it exists to report. So the liveness signal leaves GitHub, and an
external monitor alerts on its absence — which requires exactly the standing
infra and live secret #118's gate forbids. Rather than pretend a watchdog can
be a drill, the clause is **amended for prong (c) alone**; (a)/(b) keep the
original no-standing-infra bar. The alternative reading — file it as #125 —
was rejected because this is the observability half of (b)'s scheduling
death, not a new capability.

Two things were deliberately NOT built. **No keepalive commit:** GitHub took
down the popular keepalive action as a ToS violation for circumventing the
inactivity policy, and validate [68] now fails if a manufactured liveness
commit ever appears in either workflow. **No shared monitor URL** between the
two books — one healthy book would mask the other's death, so [68] pins one
check per book. Honest limit on the whole item: whether a commit pushed by the
workflow's own `GITHUB_TOKEN` resets the inactivity clock is **not
authoritatively documented** and community reports conflict; the watchdog is
built to not depend on that answer, since it fires on missing pings either
way. Owner half is unshipped by construction (the two checks + secrets) —
until it is done, both workflows log `watchdog skipped` and nothing changes.

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

**2026-07-25 (execution, latest) · #125 promoted; the R10 ledger now reads
four-spent.** Buy-day eligibility ⭐-only → CONVICTION ⭐|🟢, owner-directed
same-session as the study (Part-III rule-5 override recorded in
promotions.json "hold-adds", like #91's). Accounting: 🐳 (Q3) · rs12-top3
(Q4, early) · add-cap-25 (2027-Q1, early) · hold-adds (2027-Q2, early) —
**next free promotion slot 2027-Q3**; #14/#14a/#85 reads split FOUR
promotion epochs. Demotion is the first custom checker that executes
INSIDE month_start_block rather than reminding (`checker_fn` field).

**2026-07-12 (execution) · #92 promoted; the R10 ledger then read
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
| `ROADMAP.md` | the multi-year arc — verdict calendar (R-2027 / R-2029 / R-2036), the §2 alpha program (shot budget + #120 bake-off), survival workstreams, items #113–123; re-read every July — added 2026-07-24 |
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

## 10. Long-horizon roadmap — 2027 / 2031 / 2036 (added 2026-07-24)

Full text: **`ROADMAP.md`** (standing doc, re-read every July with the
#40 re-test). This PRD keeps the near-term backlog; ROADMAP.md owns the
multi-year arc. The shape, in one paragraph:

**Horizon 1 (→2027)** is already scheduled by dated reads — the job is
hitting them: #14 scorecard + October reads (2026-10), swing 26-week
verdict (~2027-01), 2027-Q2 R10 selection slot, first live-vs-sim
reconcile (2027-07), then the pre-registered **R-2027** year-one read.
**Horizon 2 (2028–2031)** centres on **R-2029**, the three-fork rule
frozen now: live edge above the #71 band → scale · inside → hold &
cheapen · below → **demote to discipline mode** (signals stop gating
money; DCA + risk lens + copilot + honest ledger survive) — the price
of calling §9.0 a north star. Plus the era's survival workstreams:
data durability (#113–114), the first live bear, model succession
(#115), complexity pruning (#116). **Horizon 3 (→2036)** is the
endowment test: **R-2036** is binding and benchmark-final; platform
deaths are pre-planned as ops (#118); the glide-path trigger is SET
(2026-07-24, PLAYBOOK §8.1: S$2M household by ~47 + S$600k checkpoint
at 40 — re-dated same day when the before-40 demand priced at an
unreachable S$18–21k/mo — assigned to the savings lever) while #119's
study waits on its pre-registered proximity condition (≥S$1M or
2030-07); the durable assets are
the ledger, the scorecard, and docs a stranger could operate from.
New items #113–123 live in ROADMAP.md §5 under the same gate law as
§8.3: #113–119 are infrastructure (no R10 slots); **#120–123 are the
ROADMAP §2 alpha program** — the algorithm-improvement pipeline stated
as a shot budget (~4 selection promotions/yr under R10-as-re-cut, ≈20
by 2029, ≈40 by 2036; survival/exit lane unthrottled): the annual #120
selection bake-off every ranking idea must win, the #121
drawdown-repair series aimed at §16b's −62%-vs-−34% gap, #122 universe
capacity behind #65's adoption, and #123 ledger-fitted selection once
≥3y of live rows exist (~2029; weights must stay digest-printable,
§8.2 stands). Studies are free; promotions pay the normal R10 price.
