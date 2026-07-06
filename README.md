# homily-bot

A **Homily-Chart-style screen for a personal IBKR equity book**, upgraded to
mimic how [@dannycheng2022](https://x.com/dannycheng2022) uses Homily charts:
long-term **accumulate-on-dip guidance** anchored on chip (cost-distribution)
support/resistance — plus the original red/white-circle weekly regime engine
and its daily out-of-sample-gated auto-refine loop. Telegram digest via GitHub
Actions cron — no server, no paid data, pure stdlib. See `PRD.md` for the full
spec and the honesty constraints.

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

## Files
| File | Role |
|---|---|
| `homily_data.py` | Daily OHLCV fetch (Yahoo v8, key-free) + weekly/monthly resample |
| `homily_chips.py` | Chip/cost-distribution engine: decayed volume-at-price → POC, support/resistance peaks |
| `homily_danny.py` | Composite state machine: monthly trend × weekly circle × daily candle × chip context × volatility hole |
| `homily_vol.py` | Volatility-hole detector: vol-collapse cluster → zone, breakout/breakdown/inside |
| `homily_vol_backtest.py` | Event study of hole resolutions vs unconditional baseline |
| `homily_clone.py` | Original red/white-circle weekly engine (EMA ribbon + MACD + trend slope) |
| `homily_validate.py` | Self-tests: EMA/MACD math, no look-ahead, chip POC/decay, composite states |
| `homily_backtest.py` + `bt_data.py` | 5y weekly hold-🔴/cut-⚪ vs buy-and-hold (it loses) |
| `homily_danny_backtest.py` | 5y daily ⭐-gated accumulation vs monthly DCA (it loses too) |
| `homily_refine.py` | Daily auto-refine: walk-forward, champion replaced only if it wins **out-of-sample** |
| `daily_run.py` | Entrypoint: fetch → composite signals → refine → Telegram |
| `PRD.md` | Danny-methodology spec + scope limits |
| `homily_champion.json`, `homily_refine_log.csv` | Persisted state (committed daily by the workflow) |

## Watchlist
All IBKR holdings + Danny-core **ASML** (watch-only, marked `*`). SOXL is
excluded (3x leveraged ETF — leverage is out of scope by design).

## Schedule
`.github/workflows/homily-daily.yml` runs **09:00 SGT Mon–Fri** (`0 1 * * 1-5`
UTC) and on manual dispatch: digest → self-tests → commit refined
champion/log back to the repo.

## Setup (one-time)
```
gh secret set TELEGRAM_BOT_TOKEN -b'<token>'
gh secret set TELEGRAM_CHAT_ID  -b'<chat id>'
```
Without secrets the job still runs and prints the digest (no send).

## Run locally
```
python daily_run.py             # prints digest (sends if TELEGRAM_* env set)
python homily_validate.py       # self-tests
python homily_danny_backtest.py # ⭐-gating vs DCA, the honest comparison
python homily_backtest.py       # hold-🔴/cut-⚪ vs buy-and-hold
```
Pure standard library — no `pip install`.
