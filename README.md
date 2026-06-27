# homily-bot

A **Homily-Chart-style "Red/White Circle" trend-regime screen** for a personal
IBKR equity book, with a daily **out-of-sample-gated auto-refine** loop and a
Telegram digest. Runs on GitHub Actions cron — no server, no paid data.

> ⚠️ **This is a trend-following risk flag, not a trading system.** A 5-year
> backtest (`homily_backtest.py`) shows that mechanically holding 🔴 and cutting
> ⚪ **underperforms buy-and-hold on return** in every name tested and is
> actively bad on whippy names (TSLA). Its only reliable benefit is smaller
> drawdowns. The digest carries this reminder every day on purpose.
>
> It is **not** a clone of Homily's proprietary algorithm (undisclosed). It is a
> transparent approximation, and the daily refine optimises *its own* backtest —
> it does **not** converge toward Homily.

## Files
| File | Role |
|---|---|
| `homily_clone.py` | Red/white-circle signal engine (EMA ribbon + MACD + trend slope) |
| `homily_validate.py` | Self-tests: EMA correctness, no look-ahead, synthetic up→RED/down→WHITE |
| `homily_backtest.py` + `bt_data.py` | 5y weekly backtest vs buy-and-hold |
| `homily_refine.py` | Daily auto-refine: walk-forward, champion only replaced if it wins **out-of-sample** |
| `daily_run.py` | Entrypoint: Yahoo fetch → signals → refine → Telegram |
| `homily_champion.json`, `homily_refine_log.csv` | Persisted state (committed daily by the workflow) |

## Schedule
`.github/workflows/homily-daily.yml` runs **09:00 SGT Mon–Fri** (`0 1 * * 1-5` UTC)
and on manual dispatch. It runs the digest, runs the self-tests, then commits any
refined champion/log back to the repo so refinement accumulates over time.

## Setup (one-time)
Add two repo secrets, then enable Actions:
```
gh secret set TELEGRAM_BOT_TOKEN -b'<token>'   # e.g. @GyIbkrBot's token
gh secret set TELEGRAM_CHAT_ID  -b'<chat id>'
```
Without secrets the job still runs and prints the digest (no send), so scheduling
is safe before secrets are set.

## Run locally
```
python daily_run.py        # prints digest (sends if TELEGRAM_* env set)
python homily_backtest.py  # the honest buy-and-hold comparison
python homily_refine.py    # one refine step
```
Pure standard library — no `pip install`.
