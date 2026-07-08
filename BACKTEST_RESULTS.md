# Backtest results — strategy vs S&P 500 / Nasdaq-100 (5y **and** 10y)

**Windows:** 5y = 2021-07-08 → 2026-07-07 · 10y = 2016-07-08 → 2026-07-07 ·
**$1/month contributions** · **10 bps per trade** · **point-in-time** (signals
computed only from bars up to each decision day — no look-ahead).

Regenerate any time: `python homily_strategy_backtest.py` (5y). The 10y run uses
the same `run_strategy`/`run_dca` functions with `rng="10y"`. Every number below
is raw output — nothing is hand-entered.

> **TL;DR — does the method work?** Over **5 years**, yes: the honest control
> beat both indices (22.7% vs 11.3%/14.7% CAGR). Over **10 years**, no clean win:
> it beat the S&P but **lost to a plain QQQ index fund**, added almost nothing in
> real dollars over the extra 5 years (because most of the watchlist didn't exist
> before ~2020, so it sat in cash), and carried a **−75% drawdown**. The 10-year
> test is the more sobering one — read the "10-year extension" section.

---

## The honest headline

Over this 5-year window the strategy **did** beat both indices — *on the honest
control universe, without the bear-market selling overlay.* Read that whole
sentence; all three qualifiers matter.

| Scenario | CAGR (time-weighted) | Growth of $10,000 | Worst drawdown |
|---|---:|---:|---:|
| DCA into **S&P 500** (SPY) | 11.3% | **$17,080** | −23% |
| DCA into **Nasdaq-100** (QQQ) | 14.7% | **$19,853** | −34% |
| **Our strategy — honest control** (Univ B, no regime sell) | **22.7%** | **$27,811** | −30% |

The honest-control strategy roughly **doubled the S&P's dollar outcome**
($27.8k vs $17.1k) and beat the Nasdaq-100 too — at a similar drawdown to QQQ.

> **How "Growth of $10,000" is computed.** The backtest contributes $1/month
> (dollar-cost-averaging), so its headline metric is MOIC (final value per dollar
> paid in) and a **time-weighted CAGR** that strips out contribution timing. The
> $10k column applies that time-weighted CAGR as a 5-year lump-sum compounding —
> `$10,000 × (1 + CAGR)⁵` — exactly the "growth of $10,000" convention on an index
> fund fact sheet. It answers *"if $10k had been invested and compounded at the
> strategy's realized time-weighted rate."*

---

## Full results table (all six scenarios)

| Scenario | MOIC | CAGR | Growth of $10k | MaxDD |
|---|---:|---:|---:|---:|
| DCA S&P 500 (SPY) | 1.50 | 11.3% | $17,080 | −23% |
| DCA Nasdaq-100 (QQQ) | 1.73 | 14.7% | $19,853 | −34% |
| **Honest control** (Univ B) — no regime sell | 2.14 | 22.7% | **$27,811** | −30% |
| Honest control (Univ B) — + bear-sell overlay | 1.11 | 3.3% | $11,763 | −31% |
| Hindsight univ (Univ A) — no regime sell | 3.67 | 43.3% | $60,427 | −18% |
| Hindsight univ (Univ A) — + bear-sell overlay | 1.66 | 17.6% | $22,492 | −19% |

*MOIC = final value per $1 contributed (DCA basis). CAGR = time-weighted NAV
return. MaxDD = worst peak-to-trough on the NAV.*

---

## Read this before you trust the headline

**1. It is ONE window.** 2021-07 → 2026-07 contained a sharp 2022 drawdown and a
strong recovery. A single 5-year path is *suggestive, not proof.* Different start
dates would give different numbers.

**2. Which universe you feed it decides the result — so read Universe B, not A.**
- **Universe A ("current")** is today's bot watchlist — i.e. **hindsight-picked
  2026 winners** (NVDA, PLTR, AVGO…). Its 43.3% / $60k is *upward-biased by
  construction* and should be **ignored** as a performance claim. It's shown only
  for contrast.
- **Universe B ("hype-2021")** is the honest control: what a growth investor
  *plausibly* held in mid-2021 — winners **and** still-listed wrecks (PTON, ZM,
  DOCU, ROKU, LCID, TDOC, AFRM…). The real question is whether the signals dodge
  losers *they haven't yet seen die*. That's the row the headline uses.
  *(Caveat: fully delisted names can't be fetched key-free, so a little
  survivorship bias remains even in B.)*

**3. The bear-market selling overlay HURT in this window.** Adding "liquidate
everything when both SPY and QQQ close below their 10-month SMA" cut the honest
control from **22.7% → 3.3% CAGR** ($27.8k → $11.8k) — *below both indices.* 2022
was a V-shaped recovery, and mechanical bear-selling got whipsawed out and bought
back higher. This is exactly why the operating protocol is: **BEAR de-risks
satellites and pauses adds — the index core is never sold.** (The 33-year regime
backtest shows the overlay pays only in *grinding* bears, not V-recoveries.)

**4. The ⭐-timing itself has a documented weakness.** A separate test
(`homily_danny_backtest.py`) found that *waiting* for the ⭐ ACCUMULATE zone got a
**worse** average cost than plain monthly DCA on every name tested. The edge in
the table above comes from *stock selection* (accumulating trending leaders), not
from the entry-timing levels — treat the ⭐ zone as context, not a market-timing
signal.

---

---

## 10-year extension (2016-07 → 2026-07) — the sobering result

We extended the exact same engine to a full decade. It does **not** confirm the
5-year win — and *why* it doesn't is the most useful thing in this document.

| Scenario | MOIC | CAGR | Growth of $10k | MaxDD |
|---|---:|---:|---:|---:|
| DCA S&P 500 (SPY) | 2.08 | 13.1% | $34,359 | −24% |
| DCA Nasdaq-100 (QQQ) | **2.86** | **20.1%** | **$62,554** | −34% |
| Honest control (Univ B) — no regime sell | 2.08 | 16.8% | $47,161 | **−75%** |
| Honest control (Univ B) — + bear-sell overlay | 1.18 | 7.9% | $21,352 | −72% |
| Hindsight univ (Univ A) — no regime sell | 6.67 | 31.3% | $152,361 | −48% |
| Hindsight univ (Univ A) — + bear-sell overlay | 2.14 | 14.6% | $39,147 | −44% |

**Three findings, all against the strategy as a 10-year claim:**

**1. Over 10 years it LOST to a plain QQQ index fund.** Honest control 16.8% CAGR
/ MOIC 2.08 vs QQQ 20.1% / 2.86 ($47k vs $63k on $10k). It beat the S&P, but a
one-line "buy QQQ and never look at it" beat *us*. The 5-year outperformance did
not survive the longer window.

**2. The extra 5 years added almost nothing in real dollars — because the
watchlist didn't exist yet.** The honest control's MOIC is **2.08 over 10y vs
2.14 over 5y** — essentially identical. Doubling the horizon barely changed the
dollar outcome. Reason: Universes A and B are *post-2020 growth names* (PLTR '20,
RKLB/APP/HIMS/DUOL/SOFI/COIN/AFRM/UPST '21…). In 2016–2020 most of them didn't
trade, so the strategy sat in **cash**, contributing but not investing. The
"10-year backtest" is really *~5 years parked in cash, then the 5-year strategy.*
The time-weighted CAGR (16.8%) flatters it by scoring those cash years as flat;
the MOIC (2.08) tells the honest dollar truth. **You cannot backtest a strategy
on stocks that hadn't listed yet** — that's the real lesson of this row.

**3. The drawdown is unholdable: −75%.** The 5-year window (MaxDD −30%) hid the
full 2021→2022 growth-stock collapse from its own peak. Over 10 years the
concentrated leader basket fell **−75%** — and the bear-sell overlay barely
helped (−72%). Danny's edge *is* the willingness to endure drops like this; the
backtest confirms the drops are real, and most people would not hold through a
three-quarters loss.

> **Is the 10-year test even fair to the strategy?** Partly not — the DCA SPY/QQQ
> benchmarks are valid across the full decade, but the strategy's *universe* isn't
> (it mostly post-dates 2020). So the cleanest apples-to-apples comparison remains
> the **5-year** window. The honest takeaway from going to 10 years is not "the
> method is 16.8% CAGR" — it's "we can't yet test this method over a decade,
> because the names are too young, and where we *can* test it the tail risk is
> brutal."

---

## Bottom line — does our method work?

**Over 5 years: a real, honest win.** Buying and holding trending leaders on the
control universe returned **22.7% CAGR vs 11.3% (S&P) / 14.7% (Nasdaq-100)**,
$10k → **$27.8k vs $17.0k / $19.9k**, driven by *never selling winning leaders* —
Danny's core idea, and it beat the index.

**Over 10 years: not proven, and arguably not yet testable.** It beat the S&P but
**lost to a plain QQQ index fund** (16.8% vs 20.1%), added nothing in real dollars
over the extra five years (the names didn't exist to buy), and exposed a **−75%
drawdown**. The mechanical bear-selling overlay hurt in *both* windows.

**Honest verdict:** the method's *idea* — concentrate in trending leaders, hold
them, never per-name sell — has one promising 5-year window behind it and a strong
theoretical basis, but it is **not** validated over a full cycle, it does **not**
reliably beat QQQ over 10 years, and its real cost is **tail risk you must be able
to stomach (−75%)**. It is a conviction-and-risk-tolerance strategy, not a proven
index-beater. Treat every number here as *suggestive evidence, not a guarantee.*
