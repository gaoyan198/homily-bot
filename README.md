# homily-bot

A **Homily-Chart-style screen for a personal IBKR equity book**, upgraded to
mimic how [@dannycheng2022](https://x.com/dannycheng2022) uses Homily charts:
long-term **accumulate-on-dip guidance** anchored on chip (cost-distribution)
support/resistance — plus the original red/white-circle weekly regime engine
and its daily out-of-sample-gated auto-refine loop. Telegram digest via GitHub
Actions cron — no server, no paid data, pure stdlib. See `PRD.md` for the full
spec and the honesty constraints. **Start with [PLAYBOOK.md](PLAYBOOK.md)** —
the plain-English operating manual (bear-market steps, core vs satellite,
trim rules, how to read the digest in 2 minutes) — and
**[HOW_TO_READ.md](HOW_TO_READ.md)**, the chart-card manual for the #83
board (red-candle-is-BULLISH colour language, chip histogram, VH zones).

> ⚠️ **Two honest backtest results are baked into the digest on purpose:**
> 1. Mechanically holding 🔴 and cutting ⚪ trails buy-and-hold on return
>    (`homily_backtest.py`) — so there is **no sell state**; CAUTION only
>    pauses adds.
> 2. Waiting for the ⭐ ACCUMULATE zone got a **worse** average cost than
>    immediate monthly DCA on every name tested over 5y
>    (`homily_danny_backtest.py`, −1% to −13%) — the levels are context for
>    discretionary adds, not a reason to sit in cash.
> 3. The volatility hole's **bullish** side has a real but modest edge
>    (`homily_vol_backtest.py` event study: breakouts +4.4%/20d vs +2.8%
>    baseline), but its **bearish** side does not — breakdowns were followed
>    by *above*-baseline returns in these names, so a breakdown is flagged
>    as a ⚠ note, never a sell/no-add veto.
> 4. The whale-accumulation gate **passed** (`homily_whale_backtest.py`,
>    58 names incl. 2021 wrecks, point-in-time): ⚪-state shelf dips WITH
>    the 🐳 footprint returned +10.9% fwd-60d vs +9.5% DCA baseline and
>    +9.7% plain ⚪ dips — so ⚪+🎯+🐳 is the **one** permitted ⚪ add
>    (WHALE-DIP tier, discretionary, ≤2%). Flip side: the shelf alone
>    (🎯 without 🐳) *lost* to plain dips — the footprint, not the level,
>    carries the edge.
>
> This is **not** a clone of Homily's or Danny's proprietary formulas (both
> undisclosed; Danny says his chip system "can never be duplicated"). It is a
> transparent approximation of their publicly documented behaviour. Danny's
> posted results also use leverage — deliberately not copied here.

## Signal states (Danny semantics — adds only, never sells)
| State | Meaning |
|---|---|
| ⭐ ACCUMULATE | monthly trend UP + weekly RED circle + price at a major chip-support peak |
| 🟢 HOLD | trend intact but extended above support — wait for a pullback |
| 🟡 PULLBACK | weekly AMBER while monthly UP — dip forming, stalk the zone |
| 🔵 BOTTOMING | trend still broken BUT price broke **above** a volatility hole formed in the decline — Danny's early bottoming signal |
| ⚪ CAUTION | weekly WHITE or monthly trend down — pause adds (thesis review, not a sell call) |

Each digest row carries the chip levels: `add` zone (top support peak), `POC`
(decayed volume-at-price point of control), nearest `res`istance shelf, % of
chips in profit — and `VH`, the **volatility hole** ("the most crucial part"
of Danny's analysis): a new-60d-low volatility cluster printed as a zone;
↑ close above it = bottoming confirmation, ↓ below = topping-process warning
(note only, see honesty point 3), ◻ = still inside, unresolved.

⭐ rows are ordered by 12-month relative strength and the top-3 carry an
`RS#n` mark — the names the buy-day copilot splits the stock half across
(#24, promoted **2026-07-12 by owner override, ahead of its live
forward-check**; honesty: the measured lift was modest and one-window
— BACKTEST_RESULTS §4 — so the pre-registered Jul–Sep check still
publishes at every month-start through 2026-10-01, and a FAIL demotes
back to equal-split-max-5 mechanically per `promotions.json`).

Weekly-RED rows also print the historical base rate next to the run's age —
`wk RED/4 (8w · med run 8w)` — the median completed weekly-RED spell across
1,439 spells in both backtest universes (`homily_ribbon_backtest.py`, #82).
It is context for how much accumulate-window typically remains, not a
prediction: the distribution is wide (p25 2w, p75 23w), entry-candle size
added no stable conditioning, and the number gates nothing.

When a weekly-RED row's daily candle has gone non-RED, the row counts the
dip — `dip d3 (med 4d · p90 22d)` — against the measured base rate of 1,594
resolved pullbacks (`homily_pullback_backtest.py`, #78; stable across both
universes and OOS halves, which was the pre-committed ship condition).
Danny's "3–7 trading days" matches the median (4d) but not the spread
(p25–p75 = 1–14d). Deliberately absent: any warning when a dip outlasts
p90 — the same study showed trend failures resolve *faster* than healthy
pullbacks, so dip age alone never escalates anything.

Rocket and discovery rows also carry `Q1/Q2/Q3` — a sticky quality tier
(quarterly EDGAR read + 3y RS, frozen between refreshes,
`homily_quality.py`, #66). It is a LABEL and nothing more: its gate
backtest failed honestly — computed from as-of filings, Q could not
separate the 2021 wrecks (ZM/DOCU/ROKU scored Q1 on then-stellar
fundamentals; that class was a valuation collapse, not broken businesses)
— so no buy state, no veto, and no sizing reads it
(BACKTEST_RESULTS §14). Non-US names print `Q:—`.

If a name's recent tape holds a **>45% one-day move on abnormal volume** — the
signature of a split or spin-off the data feed never adjusted — every one of
those levels is built on prices that never traded. The row then prints
`⚠️ levels suspended — corporate action?` instead of the numbers: the state
still shows, the levels don't, and the name cannot be promoted into the 🐳
add tier that day.

**🐳 whale-accumulation tag** (the PLTR June-2026 lesson): a dip (≥5% below
the 60d closing high) showing ≥2 of 3 big-buyer footprints — an
**absorption print** (heavy-volume day probing the dip floor yet closing in
the top half of its range), **flow divergence** (OBV/A-D holding vs falling
price), **shelf stability** (the chip shelf's decayed weight fully
replenished while price sits on it). A ⚪ row with **🎯 + 🐳** is the
promoted **WHALE-DIP tier** — the only ⚪ add the playbook permits:
discretionary, ≤2% of account, same monthly budget, 10%/name hard cap
(honesty point 4).

## Files
| File | Role |
|---|---|
| `homily_data.py` | Daily OHLCV fetch (Yahoo v8, key-free) + weekly/monthly resample |
| `homily_chips.py` | Chip/cost-distribution engine: decayed volume-at-price → POC, support/resistance peaks |
| `homily_danny.py` | Composite state machine: monthly trend × weekly circle × daily candle × chip context × volatility hole |
| `homily_vol.py` | Volatility-hole detector: vol-collapse cluster → zone, breakout/breakdown/inside |
| `homily_corp.py` | Corporate-action sanity check: a mis-adjusted split in the chip window suspends that name's levels |
| `homily_whale.py` | Whale-accumulation footprint: absorption print + OBV/A-D divergence + shelf stability → 🐳 |
| `homily_whale_backtest.py` | The 🐳 gate: conditioned ⚪ shelf-dip buys vs plain ⚪ dips vs DCA (PASSED → WHALE-DIP tier) |
| `homily_conviction.py` | Multi-bagger gates + 0–100 conviction score + sizing tiers |
| `homily_fund.py` | EDGAR fundamentals flag (F:n/m — growth/profit/dilution), info-only, 7-day cache |
| `homily_regime.py` + `homily_regime_backtest.py` | Month-end 10m-SMA regime on SPY+QQQ (🐂/⚖️/🐻 banner) + 33y timing backtest |
| `homily_strategy_backtest.py` | THE test: full ⭐-dip strategy vs SPY/QQQ DCA, hindsight + 2021-control universes |
| `homily_core4_backtest.py` | Danny-style 90%-in-top-4 concentration vs index: hindsight, pick-once, annual re-pick |
| `homily_emergent_backtest.py` | Danny's real mechanic: never-sell dip-buying → concentration emerges (top-4 62%) |
| `docs/index.html` | Full methodology page (engines, gates, rubric, honest backtests, limits) |
| `homily_vol_backtest.py` | Event study of hole resolutions vs unconditional baseline |
| `homily_clone.py` | Original red/white-circle weekly engine (EMA ribbon + MACD + trend slope) |
| `homily_validate.py` | Self-tests: EMA/MACD math, no look-ahead, chip POC/decay, composite states |
| `homily_backtest.py` + `bt_data.py` | 5y weekly hold-🔴/cut-⚪ vs buy-and-hold (it loses) |
| `homily_danny_backtest.py` | 5y daily ⭐-gated accumulation vs monthly DCA (it loses too) |
| `homily_refine.py` | Daily auto-refine: walk-forward, champion replaced only if it wins **out-of-sample** |
| `homily_png.py` | Chart cards (#35): pure-stdlib PNG (price + add-zone/POC/res + chip histogram + weekly ribbon); top-3 actionable names sent as photos after the digest |
| `homily_dashboard.py` | Danny chart board (#83, supersedes #36): searchable dark board of candle cards (engine-coloured candles, chip histogram + POC, VH zone, add-zone band, 52w ribbon) + ledger heatmap/alerts timeline/refine chart. Small board committed (`docs/dashboard.html`, held charts + actionable facts cards); FULL board (every screened name) sent nightly, never committed. One inline filter script — the recorded D-36 relaxation. Manual: `HOW_TO_READ.md` |
| `homily_chart.py` | Any-ticker chart CLI (#84): `python3 homily_chart.py TICKER…` renders the same card for any Yahoo symbol — ad-hoc banner, nothing written to the ledger (R3) |
| `homily_promotions.py` + `promotions.json` | Promotion lifecycle registry (#69): pre-registered gates, forward-checker, and mandatory demotion rules. rs12-top3 was promoted EARLY 2026-07-12 by owner override (ahead of its live forward-check — basis recorded verbatim in the registry); the month-start digest block publishes the frozen Jul–Sep check through the 2026-10-01 read and enforces the rolling demotion rule |
| `homily_weekly.py` | Sunday deep-dive (#33): fetch-free weekly summary from the week's ledger rows + the dashboard file |
| `homily_flex.py` | IBKR Flex auto-sync (#32): shares/cost from a Flex query at run start; owner fields survive; never adds/deletes; unset secrets = manual fallback |
| `homily_clusters.py` | Concentration lens (#29): 90d-correlation clusters of the book, one digest line + a ⭐-deepens-cluster nudge; info-only |
| `homily_bearready.py` | Bear-readiness rehearsal (#30): first-Monday digest block — bucket split, margin/SRS confirmations, the pre-computed PLAYBOOK §4 sell list; info-only |
| `homily_buyday.py` | Buy-day copilot (#31): first run of the month resolves `BUY_BUDGET_USD` into printed IBKR-ready orders + a basket CSV (`docs/orders_YYYY-MM.csv`) — **info-only, never places an order** |
| `homily_swing.py` | SWING (paper) digest block (#90): P2-gate counters from the merged sleeve's committed snapshot — read-only, fetch-free, never a trade signal. Monthly report carries the #95 flywheel line (cumulative banked skims + sleeve score); the skim itself is mechanized in `gambit/gambit_live.py` (`maybe_skim`) and routed into the 🛒 BUY DAY block — quarter-end profit funds the DCA, kill-safe (skims never touch `contributed`/`realized`) |
| `homily_household.py` + `contributions.json` | Household scorecard (#94): first-Monday whole-portfolio block — every sleeve (core + SRS + ESPP + swing − margin) vs the same net contributions DCA'd into QQQ (money-weighted, adjusted closes, monthly granularity), USD + SGD, combined gross leverage vs the ladder cap. **Info-only; not the #14 signal referee** — it measures the whole household, not signal skill, and its QQQ comparison is coarse-by-design. Flows the broker can't see are owner-maintained in `contributions.json` (a missing month nags, never guesses) |
| `gambit/` | The merged 4–12wk swing sleeve (#90/D-90): its own engine, harness, 70-test validate, governance docs (KILL_MEMO, AMENDMENT_A4, LEVERAGE_MEMO) and hash-chained paper journal — self-contained, byte-identical to the retired standalone repo. **PAPER ONLY** (`LIVE_ORDERS=off`); weekly loop via `.github/workflows/gambit-weekly.yml` |
| `daily_run.py` | Entrypoint: fetch → composite signals → refine → Telegram |
| `PRD.md` | Danny-methodology spec + scope limits |
| `docs/archive/` | Verbatim planning history moved out of the live docs (#76): resolved PRD addenda §5c–5j, shipped §8 item texts, shipped designs |
| `homily_champion.json`, `homily_refine_log.csv` | Persisted state (committed daily by the workflow) |

## Watchlist
All IBKR holdings + Danny-core **ASML** (marked `†` = not held). SOXL is
excluded (3x leveraged ETF — levered ETFs stay out of scope).

## Leverage (#91 — policy: [LEVERAGE.md](LEVERAGE.md))
The digest prints a ⚖️ ladder line under the regime banner: **BULL ≤1.30× /
MIXED ≤1.15× (no new margin) / BEAR = margin zero at onset**. Honesty note:
the ladder was adopted because regime-gated 1.30× **QQQ** passed a
pre-registered survival + edge readout (BACKTEST_RESULTS §15) — it is the
equity risk premium financed below its return, NOT stock-picking alpha, and
it does not protect from bears (BEAR=1.00× stays invested; protection is
the 🐻 protocol). Borrowed dollars may fund only gate-passed swing entries
(paper until #93); **the core monthly book never carries margin** — its own
measured −59…−76% paths sit inside the margin-call boundary at any constant
≥1.25×.

## When to sell — market regime 🐂/🐻 (priced tail insurance)
Per-stock trend-selling loses (see backtests); the month-end 10m-SMA rule on
SPY **and** QQQ (both below = 🐻 BEAR, both above = 🐂 BULL) survives — as
**insurance, not a return enhancer**. The D-63 decomposition
(`homily_bear_backtest.py`, 2026-07-10, 1993→2026 incl. dot-com + 2008):
following PLAYBOOK §4 (sell weak satellites *once* at onset → dry powder,
keep buying the index all bear, re-enter stars in thirds on 🐂) returned
20.4%/yr vs 21.3%/yr for never-selling while cutting worst drawdown from
**−76% to −29%**; in the V-shaped 2022 bear it cost ~7 pts/yr of its 5y
window. "Pause adds but don't sell" tested worst of both worlds; the index
core never sells either way. Banner tops every digest and words it this way.

**The bar re-test** (`homily_multiwindow_backtest.py`, 2026-07-10, every
≥5y window since 2015, honest-control universe): the engine **beats SPY
more often than not, does NOT reliably beat QQQ**, at 2–3× the index
drawdown — the earlier "5y QQQ win" was partly an eligibility artifact.
The one arm that *added* return on the wreck-salted control was the
per-name PLAYBOOK §5.2 exit (+3.4 pts/yr at 10y). Full tables + verdict:
[BACKTEST_RESULTS.md](BACKTEST_RESULTS.md).

## Multi-bagger conviction screen 🚀
Every name (held or not) runs through 5 hard gates — size (<$5B/day dollar
volume), trend (monthly UP + weekly RED), leader RS (12m ≥ SPY+20pts), basis
(price > POC), data (≥200 bars) — then a transparent 0–100 score sets the
sizing tier: **≥75 CONVICTION ≤5% of account · 60–74 STARTER ≤2% · hard cap
10%/name incl. existing**. Max 5 rows daily; most days most names fail — by
design. Full rubric: [docs/index.html](docs/index.html) (open locally; repo
is private so GitHub Pages would make it public — enable deliberately if
wanted). NOTE: the score itself is not yet backtested (PRD backlog #1).

## Discovery screen
A ~37-name universe of liquid names **not held** (megacap tech, semis/AI
hardware, growth software, quality diversifiers, HK liquid names) is screened
with the same composite engine every run; only actionable ⭐ ACCUMULATE and
🔵 BOTTOMING setups surface in the digest (max 8 rows + overflow tickers).
Leveraged ETFs and crypto-beta names are deliberately excluded from the
universe. Edit `UNIVERSE` in `daily_run.py` to change coverage.

## Schedule
`.github/workflows/homily-daily.yml` runs **09:00 SGT Mon–Fri** (`0 1 * * 1-5`
UTC) and on manual dispatch: digest → self-tests → commit refined
champion/log back to the repo.

`.github/workflows/gambit-weekly.yml` (#90/#93) advances the swing
sleeve every **Saturday 02:00 UTC**: homily + gambit validates →
`gambit/weekly_run.py` (paper) → `gambit/live_run.py` (LIVE overlay) →
commit journals/books → weekly ♟️ digest + ORDER SHEET to Telegram.
Honesty note: the LIVE book (Amendment A5, 2026-07-12) was armed by owner
override of the P2 paper gate — it runs on days, not 26 weeks, of paper
history; its mandatory stops FAILED the Phase-1 backtest (S1-stopped 0/3)
and are a bounded-loss control, not an edge; the paper S1-pure book runs
beside it as the no-stops counterfactual. The bot places NO orders — the
owner executes the printed sheet (LIVE_ORDERS stays off). Kill rules are
mechanical: equity ≤70% of contributed, or expectancy ≤0 over 20 closed
trades → liquidate, failure memo, done. Nothing trades until the legacy
margin clears and `MARGIN_ZERO` is set.

## Setup (one-time)
```
gh secret set TELEGRAM_BOT_TOKEN -b'<token>'
gh secret set TELEGRAM_CHAT_ID  -b'<chat id>'
gh variable set BUY_BUDGET_USD    -b'<monthly cash budget>'   # optional: buy-day copilot
gh variable set SRS_COVERS_INDEX  -b'true'                    # optional: SRS is the index leg (PRD §9.4)
```
Without secrets the job still runs and prints the digest (no send). Without
`BUY_BUDGET_USD` the buy-day copilot stays dark. Honesty note: the copilot
*prints* orders and writes an importable basket CSV — it never places an
order (PRD §7); allocation follows PLAYBOOK §3 (half index / the stock
half split across the top-3 ⭐ by RS12 since #24's 2026-07-12 promotion,
10% cap, non-USD names excluded from order lines per R12).

## Run locally
```
python daily_run.py             # prints digest (sends if TELEGRAM_* env set)
python homily_validate.py       # self-tests
python homily_danny_backtest.py # ⭐-gating vs DCA, the honest comparison
python homily_backtest.py       # hold-🔴/cut-⚪ vs buy-and-hold
```
Pure standard library — no `pip install`.
