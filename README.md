# homily-bot

A **Homily-Chart-style screen for a personal IBKR equity book**, upgraded to
mimic how [@dannycheng2022](https://x.com/dannycheng2022) uses Homily charts:
long-term **accumulate-on-dip guidance** anchored on chip (cost-distribution)
support/resistance — plus the original red/white-circle weekly regime engine
and its daily out-of-sample-gated auto-refine loop. Telegram digest via GitHub
Actions cron — no server, no paid data, pure stdlib. See `PRD.md` for the full
spec and the honesty constraints. **Start with [PLAYBOOK.md](PLAYBOOK.md)** —
the plain-English operating manual (bear-market steps, core vs satellite,
trim rules, how to read the digest in 2 minutes).

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
| `homily_dashboard.py` | Nightly dashboard (#36): self-contained zero-JS `docs/dashboard.html` — holding cards, ledger state heatmap, reconstructed alerts timeline, refine chart; committed + sent as a document |
| `homily_promotions.py` + `promotions.json` | Promotion lifecycle registry (#69): pre-registered gates, forward-checker, and mandatory demotion rules — the Oct-2026 rs12-top3 decision is this program's output |
| `homily_weekly.py` | Sunday deep-dive (#33): fetch-free weekly summary from the week's ledger rows + the dashboard file |
| `homily_flex.py` | IBKR Flex auto-sync (#32): shares/cost from a Flex query at run start; owner fields survive; never adds/deletes; unset secrets = manual fallback |
| `homily_clusters.py` | Concentration lens (#29): 90d-correlation clusters of the book, one digest line + a ⭐-deepens-cluster nudge; info-only |
| `homily_bearready.py` | Bear-readiness rehearsal (#30): first-Monday digest block — bucket split, margin/SRS confirmations, the pre-computed PLAYBOOK §4 sell list; info-only |
| `homily_buyday.py` | Buy-day copilot (#31): first run of the month resolves `BUY_BUDGET_USD` into printed IBKR-ready orders + a basket CSV (`docs/orders_YYYY-MM.csv`) — **info-only, never places an order** |
| `daily_run.py` | Entrypoint: fetch → composite signals → refine → Telegram |
| `PRD.md` | Danny-methodology spec + scope limits |
| `homily_champion.json`, `homily_refine_log.csv` | Persisted state (committed daily by the workflow) |

## Watchlist
All IBKR holdings + Danny-core **ASML** (marked `†` = not held). SOXL is
excluded (3x leveraged ETF — leverage is out of scope by design).

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
order (PRD §7); allocation follows PLAYBOOK §3 (half index / half ⭐, 10%
cap, non-USD names excluded from order lines per R12).

## Run locally
```
python daily_run.py             # prints digest (sends if TELEGRAM_* env set)
python homily_validate.py       # self-tests
python homily_danny_backtest.py # ⭐-gating vs DCA, the honest comparison
python homily_backtest.py       # hold-🔴/cut-⚪ vs buy-and-hold
```
Pure standard library — no `pip install`.
