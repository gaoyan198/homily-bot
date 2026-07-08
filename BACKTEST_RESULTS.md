# Backtest results — strategy vs S&P 500 / Nasdaq-100 (5y and 10y)

**Windows:** 5y = 2021-07-08 → 2026-07-07 · 10y = 2016-07-08 → 2026-07-07 ·
**$1/month contributions** · **10 bps per trade** · **point-in-time** (signals
computed only from bars up to each decision day — no look-ahead).

Reproduce: `python homily_strategy_backtest.py` (5y, prints both variants below).
The 10y figures use the same functions with `rng="10y"`. Every number is raw
output — nothing is hand-entered.

> ### ⚠ Correction (this file was revised)
> An earlier version of this file said the strategy "sat in cash 2016–2020" and
> used that to explain the weak 10-year result. **That was a bug in the backtest,
> not the strategy.** [PLAYBOOK.md §3.5](PLAYBOOK.md#L57) says *"if there are no
> ⭐ names, buy the index with the full amount"* — but the old code let cash sit
> idle instead. The backtest now implements the index fallback (`index_bars=`
> param). Fixing it **lowered the 5-year number** (the idle cash had been
> lump-concentrating into winners, flattering the result) and **barely changed
> the 10-year one**. The corrected numbers are below.

---

## The faithful strategy (PLAYBOOK §3.5): no ⭐ → buy the index

This is what the operating manual actually prescribes, and what the numbers below
labelled **"idx-fallback"** now test: every month, split the contribution across
the ⭐ ACCUMULATE names; **if there are none, buy the index core** (never sold).
The old **"cash-wait"** rows are kept only to show the size of that earlier bug.

### 5-year window (2021-07 → 2026-07)

| Scenario | MOIC | CAGR | Growth of $10k | MaxDD |
|---|---:|---:|---:|---:|
| DCA S&P 500 (SPY) | 1.50 | 11.3% | $17,036 | −23% |
| DCA Nasdaq-100 (QQQ) | 1.73 | 14.7% | $19,880 | −34% |
| **Strategy — honest control, idx-fallback** | **1.77** | **16.7%** | **$21,675** | −26% |
| Strategy — honest control, + bear-sell overlay | 1.25 | 6.4% | $13,637 | −28% |
| *(old buggy cash-wait variant, for reference)* | *2.14* | *22.7%* | *$27,794* | *−30%* |
| Hindsight univ (discount entirely), idx-fallback | 2.59 | 29.2% | $35,964 | −23% |

**Read:** over 5 years the faithful strategy beat both indices — **16.7% vs 11.3%
(S&P) / 14.7% (QQQ)**, $10k → $21.7k vs $17.0k / $19.9k. A real but *modest* edge,
about **+2 points/yr over QQQ** — not the +8 the buggy version implied.

### 10-year window (2016-07 → 2026-07)

The fallback index matters a lot here (most early months have no ⭐, so they buy
the index). PLAYBOOK Bucket A is an SPY+QQQ blend, so both ends are shown:

| Scenario | MOIC | CAGR | Growth of $10k | MaxDD |
|---|---:|---:|---:|---:|
| DCA S&P 500 (SPY) | 2.08 | 13.1% | $34,359 | −24% |
| **DCA Nasdaq-100 (QQQ)** | **2.86** | **20.1%** | **$62,554** | −34% |
| Strategy — honest control, idx-fallback = **SPY** | 2.05 | 16.3% | $45,298 | −67% |
| Strategy — honest control, idx-fallback = **QQQ** | 2.31 | 19.2% | $57,925 | −66% |
| Strategy — honest control, + bear-sell overlay | 1.33 | 9.4% | $24,513 | −64% |

**Read:** over 10 years the faithful strategy **beats the S&P but loses to a plain
QQQ index fund** — *regardless of the fallback index.* Best case (QQQ fallback)
19.2% vs QQQ 20.1%; MOIC 2.31 vs 2.86. And it does so with a **−66% drawdown vs
QQQ's −34%.** You take roughly double the risk to slightly underperform "buy QQQ,
never look."

---

## What actually drives the result

- **Over 5y the edge is real but small.** The concentrated-leaders tilt added
  ~2 pts/yr over QQQ. The earlier "+8 pts" was an artifact of idle cash being
  lump-deployed into winners at favourable later dates — not a repeatable edge.
- **Over 10y the tilt does not beat QQQ.** Because ~half the decade had no ⭐
  candidates (the growth names hadn't listed), the strategy was mostly *just the
  index* plus a growth kicker — and after the 2022 collapse the kicker didn't net
  enough alpha to beat holding QQQ outright.
- **The bear-selling overlay hurt in BOTH windows** (6.4% at 5y, 9.4% at 10y) —
  a V-recovery whipsaw. This is why the protocol de-risks *satellites* only and
  never sells the index core.
- **Tail risk is the real cost.** −66% to −75% peak-to-trough on the concentrated
  book. Danny's whole edge is the conviction to hold through that; the backtest
  confirms the drop is real and most people would capitulate.
- **The ⭐ entry timing has no edge of its own** (`homily_danny_backtest.py`):
  waiting for the ⭐ zone got a *worse* average cost than plain DCA. The (modest)
  outperformance comes from *which* names are held, not *when* they're bought.

---

## Bottom line — does our method work?

**Over 5 years: a modest, honest win.** Holding trending leaders (with the index
as the no-⭐ fallback) returned **16.7% CAGR vs 11.3% (S&P) / 14.7% (QQQ)**, $10k →
**$21.7k vs $17.0k / $19.9k**. About +2 pts/yr over the Nasdaq — real, but small,
and from one window.

**Over 10 years: it does not beat a plain QQQ index fund.** 16–19% CAGR vs QQQ's
20.1%, at roughly *double* the drawdown (−66% vs −34%). It beats the S&P; it does
not beat the Nasdaq-100.

**Honest verdict:** the core idea — concentrate in trending leaders and never
per-name-sell — is defensible and edged the S&P in both windows and QQQ over the
recent 5y. But it is **not** a proven QQQ-beater over a full decade, its real
price of admission is a **~two-thirds drawdown**, and the mechanical
market-timing overlay actively hurt. For most people, *"DCA into QQQ and hold"*
was as good or better with far less pain. This method is a **conviction-and-
risk-tolerance** play, not a demonstrated index-beater — treat every figure here
as suggestive evidence, not a promise.
