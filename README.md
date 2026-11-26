# homily-bot → crash meter

Since 2026-11-26 this repo runs one simple rule for new money:

1. Buy only two index funds: **CSPX** (S&P 500) and **XNAS** (Nasdaq-100).
   Both are Ireland-domiciled, so you pay less dividend tax and avoid US estate tax.
2. Monthly money **waits in interest-bearing cash**.
3. When an index closes **10%+ below its all-time high**, its **buy zone
   opens**. That leg's whole cash pile goes in, and every monthly amount after
   that is invested on arrival until the index makes a new all-time high.
4. **Never with borrowed money.**

Every weekday at 09:00 SGT, `crash_bot.py` sends one Telegram message:

- 🎯 **deal meter**: how far each index is from its peak, and whether its zone is open
- 💰 **cash pile**: what should be waiting, per index, if you followed every sheet
- 🧾 **debt countdown**: what's left to repay before 31 Dec 2026
- 🛒 **today's orders**: on the first weekday of the month, and for a week after a zone opens

## Your settings: `crash_plan.json`

| field | meaning |
|---|---|
| `monthly_usd` | new money per month once the debt is gone (total for both indices) |
| `start` | first month the rule runs (default 2027-01-01) |
| `split` | S&P vs Nasdaq share (default 50/50) |
| `debt.balance_sgd` / `as_of` | what's left to repay; update it when you pay some off |

## Honesty

`crash_backtest.py` tested this exact rule against plain monthly buying, on
1999→2026 data with dividends included and the rules written down before the run.
**Plain monthly buying won in most ten-year periods.** The gap was small:

- **S&P, full history:** $5.73 vs $5.79 per $1.
- **S&P, worst decade (2012–2022):** about 7% behind.
- **Nasdaq, full history:** about 0.3% behind.

So the rule is not an edge. It's a cheap way to stay disciplined and out of stock-picking, and stock-picking cost about 34% in 2026.

## Files

| file | job |
|---|---|
| `crash_bot.py` | the bot (stdlib only, no state; everything recomputed each run) |
| `crash_validate.py` | offline self-test; a red test means no message goes out |
| `crash_backtest.py` | the test above, reproducible: `python3 crash_backtest.py` |
| `.github/workflows/crash-daily.yml` | the weekday schedule |
| `archive/` | the old stock-picking system, frozen but still runnable: `cd archive && python3 homily_validate.py` |

Run it locally: `python3 crash_bot.py` (it prints instead of sending when no Telegram env is set).
