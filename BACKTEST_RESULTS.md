# Backtest results — strategy vs S&P 500 / Nasdaq-100

**Re-run in full 2026-07-10 (D-63 session).** Windows roll with the run
date, so bars shift a few days vs the 2026-07-08 figures; deltas ≤0.4 pt.
**$1/month contributions** · **10 bps per trade** · **point-in-time**
(signals computed only from bars up to each decision day — no look-ahead).

Reproduce: `python homily_strategy_backtest.py` (5y THE test) ·
`python homily_bear_backtest.py` (D-63 bear decomposition, Steps 1+2) ·
`python homily_multiwindow_backtest.py` (every ≥5y window since 2015).
Every number is raw output — nothing is hand-entered.

> ### ⚠ Data-integrity note (2026-07-10)
> Yahoo's chart API **silently returns monthly bars for `range=max`** while
> honouring daily granularity for `5y`/`10y`. Every previous "max-range"
> replay (the D-63 Step-2 grinding-bear run of 2026-07-08, which also
> crashed before printing) was computing daily signals on monthly bars —
> garbage. `homily_data.py` now requests epoch `period1/period2` for full
> history and **refuses any non-daily response** (validate test [22]).
> All 5y/10y numbers were unaffected (verified by regression); every
> max-range number below is from the fixed fetch.

> ### ⚠ Correction (kept from the 2026-07-08 revision)
> An earlier version let no-⭐ months sit in cash instead of buying the
> index per PLAYBOOK §3.5. The idx-fallback rows below are the faithful
> strategy; the old cash-wait variant flattered the 5y number.

---

## 1 · THE test (committed protocol): 5y and 10y, honest control

Universe B = "hype-2021 control": winners AND wrecks a growth investor
plausibly held in mid-2021 (PTON ZM DOCU ROKU LCID…). Names fetched at
window length, so a name needs a year of in-window bars before it can be
bought (see §3 for the cleaner full-history protocol — it lowers the 5y
result).

### 5-year window (2021-07 → 2026-07)

| Scenario | MOIC | CAGR | MaxDD |
|---|---:|---:|---:|
| DCA S&P 500 (SPY) | 1.51 | 11.3% | −23% |
| DCA Nasdaq-100 (QQQ) | 1.77 | 14.7% | −34% |
| **Strategy — honest control, idx-fallback** | **1.77** | **16.7%** | −26% |
| Strategy — honest control, + bear-sell overlay (mode b) | 1.27 | 6.8% | −28% |
| Hindsight univ (discount entirely), idx-fallback | 2.67 | 29.9% | −23% |

### 10-year window (2016-07 → 2026-07)

| Scenario | MOIC | CAGR | MaxDD |
|---|---:|---:|---:|
| DCA S&P 500 (SPY) | 2.09 | 13.1% | −24% |
| **DCA Nasdaq-100 (QQQ)** | **2.92** | **20.1%** | −34% |
| Strategy — honest control, idx-fallback = SPY | 2.07 | 16.4% | −67% |
| Strategy — honest control, + bear-sell overlay (mode b) | 1.35 | 9.5% | −64% |
| Strategy — honest control, §5.2 per-name exit (mode f) | 2.54 | 19.8% | −65% |

**Read:** 5y — beat both indexes modestly (but see §3: the cleaner
protocol erases the QQQ win). 10y — beats SPY on CAGR, **loses to QQQ**
(2.07–2.54 vs 2.92 MOIC) at roughly **double the drawdown**. The best
strategy arm over 10y is the **per-name §5.2 exit**, not any market-timing.

---

## 2 · D-63 — the 🐻 sell step decomposed (the bear-regime verdict)

The committed "bear-sell overlay" (rows above) sells *everything*, every
bear month, into cash, and lump re-enters. PLAYBOOK §4 never said that.
The decomposition isolates each decision (`homily_bear_backtest.py`;
modes: a hold-through · b the tested overlay · c freeze-only, no sells,
contributions→index · d faithful §4: sell once at onset→dry powder,
contributions→index, re-enter in thirds · e sell satellites into index at
onset · f no market selling, §5.2 per-name exit only).

### Step 1 — honest control, windows containing only the 2022 (V-shaped) bear

| mode | 5y MOIC | 5y CAGR | 5y MaxDD | 10y MOIC | 10y CAGR | 10y MaxDD |
|---|---:|---:|---:|---:|---:|---:|
| (a) hold-through | 1.77 | 16.7% | −26% | 2.07 | 16.4% | −67% |
| (b) sell-all + cash | 1.27 | 6.8% | −28% | 1.35 | 9.5% | −64% |
| (c) freeze-only | 1.69 | 15.0% | −23% | 2.05 | 16.2% | −65% |
| (d) faithful §4 | 1.37 | 9.9% | −23% | 1.60 | 11.3% | −43% |
| (e) sell-into-index | 1.70 | 15.2% | −23% | 2.27 | 16.0% | −27% |
| (f) §5.2 per-name only | 1.79 | 16.7% | −25% | 2.54 | 19.8% | −65% |

2022 episode in isolation: every de-risking mode (c/d/e) held 0.92 vs
hold-through's 0.88 — **the overlay's V-bear cost lives in the recovery
months**, when hold-through was still averaging into crushed names and the
protocol was re-entering in thirds.

### Step 2 — grinding bears (the design case): 1993→2026, dot-com + 2008 + 2022

High-beta survivors (AMZN NVDA AAPL MSFT ADBE INTC CSCO QCOM ORCL EBAY) —
**survivor-biased, which flatters hold-through**, since the names that
died in 2000–02 aren't fetchable.

| mode | MOIC | CAGR | MaxDD |
|---|---:|---:|---:|
| DCA SPY | 5.87 | 8.8% | −54% |
| DCA QQQ (from 1999-03) | 10.66 | 10.0% | −80% |
| (a) hold-through | 73.45 | 21.3% | **−76%** |
| (b) sell-all + cash | 59.13 | 21.1% | −36% |
| (c) freeze-only | 53.83 | 20.1% | −76% |
| **(d) faithful §4** | **50.00** | **20.4%** | **−29%** |
| (e) sell-into-index | 13.58 | 15.2% | −64% |
| (f) §5.2 per-name only | 47.83 | 19.5% | −79% |

### D-63 verdict (per the pre-committed decision rule)

* **The sell step is real tail insurance, priced.** Through two grinding
  bears + one V-bear, faithful §4 gave up ~**1 pt/yr** (and ~⅓ of final
  wealth) vs never-selling to cut the worst drawdown from **−76% to −29%**.
  In the V-shaped 2022 window alone the premium was ~7 pts/yr. It is kept,
  reframed as insurance — PLAYBOOK §4 now quotes these numbers.
* **The overlay the earlier tables maligned was never the playbook** —
  selling monthly into cash + lump re-entry (b) is strictly worse than
  once-at-onset + index-contributions + thirds re-entry (d) in grinders
  (−36% vs −29% MaxDD) and similar in the V-window. Correction recorded.
* **Freeze-only (c) — pause adds but don't sell — is the worst of both
  worlds:** kept the entire −76% grinder drawdown AND still lagged
  hold-through in the V-window. It is not a middle way; PLAYBOOK §4 now
  says so.
* **Sell-into-index (e) is catastrophic in grinders** (15.2% vs 20.4%):
  it locks in the satellite loss at onset and never participates in the
  recovery. Dead idea.
* **The per-name §5.2 exit (f) is the only mode that ADDED return on the
  honest control** (+3.4 pts/yr over hold at 10y) — it takes out the
  PTON/ZM class. But it provides **zero crash insurance** (−79% in
  grinders). §4 = insurance; §5.2 = trash-taker. Different jobs, both kept.
  *(Caveat: (f) was tested without its F-gate — an aggressive upper bound.)*

---

## 3 · Multi-window re-test — the owner's bar (2026-07-10)

*"If the strategy cannot clear the S&P 500 or the Nasdaq over multiple
≥5-year periods, our efforts are not worth it."*
(`homily_multiwindow_backtest.py`: 7 rolling 5y windows + 2 ten-year
windows, full-history bars — names are eligible the day a window opens,
the cleaner protocol.)

**A curated list is only out-of-sample AFTER its construction date.** The
"honest" control was assembled as *what a growth investor held in
mid-2021* — so pre-2021 windows on it are as hindsight-flattered as the
current universe is for 2026 (they print 54–84% CAGR; ignore them). The
windows that mean something:

| window (univ B) | DCA SPY | DCA QQQ | strategy (a) | per-name (f) | honest? | verdict |
|---|---:|---:|---:|---:|---|---|
| 2017→2022 | 1.20 | 1.31 | 1.04 | 1.44 | straddles 2021 | (a) loses to both |
| 2018→2023 | 1.29 | 1.49 | 0.98 | 1.21 | straddles | loses to both |
| 2019→2024 | 1.41 | 1.62 | 1.10 | 1.26 | straddles | loses to both |
| 2020→2025 | 1.40 | 1.53 | 1.71 | 1.68 | straddles | beats both |
| **2021→2026** | **1.50** | **1.78** | **1.70** | **1.69–1.78** | **fully honest** | **beats SPY, ties-to-loses QQQ** |
| 2016→2026 (10y) | 2.09 | 2.96 | 2.76 | 3.36–3.83 | straddles | (a) loses QQQ; (f) beats |

(MOIC, money-weighted — the saver's number. Strategy MaxDD in these
windows: −59…−76% vs index −23/−34%. The current universe A sweeps all 9
windows vs both indexes — that is the hindsight upper bound, not
evidence.)

**Protocol honesty:** under this cleaner eligibility protocol the
committed "5y win over QQQ" (1.77 vs 1.77 at 16.7% CAGR) **degrades to
1.70 vs 1.78 — a small loss** — because the committed run force-parked the
first year in the index while names accrued bars, accidentally dodging
part of the 2022 drawdown.

**Why the straddling windows lose:** the ⭐ gate (monthly-up + weekly-RED
+ chip support) kept qualifying ZM/PTON-class names through 2020–21 as
they became eligible — momentum entries into a bubble. The gate does not
dodge regime-scale overvaluation; nothing in the system currently does.

---

## 4 · Selection inside the ⭐ set (#24, run 2026-07-10) — the first gate to PASS toward the bar

Owner directive: north star stays *beat QQQ*; the lever is selection.
`homily_selection_backtest.py` replays the same monthly candidate sets and
varies only the pick: equal-split-all (current behaviour) · alphabetical
top-5 (what PLAYBOOK §3.4's "max 5" accidentally does) · top-5/3 by 12m
relative strength · top-5/3 by conviction score · 200 seeded random-5
draws (the luck benchmark). Decision rule pre-registered in the file
docstring before the first run.

Universe B, the three construction-honest read windows (MOIC):

| window | DCA QQQ | equal-all | random-5 p10–p90 | rs12-top3 | conv-top3 |
|---|---:|---:|---:|---:|---:|
| 2020→2025 | 1.53 | 1.71 | 1.66–1.77 | **1.89** | 1.83 |
| **2021→2026 (fully honest)** | **1.78** | 1.70 | 1.66–1.75 | **1.82 ✓** | 1.73 |
| 2016→2026 (10y straddle) | 2.96 | 2.76 | 2.73–2.78 | 2.84 | 2.87 |

**Verdict (mechanical):** `rs12-top3` passed all four pre-registered
checks (beats equal 3/3, beats random-median 3/3 — in fact above the p90
of 200 random draws in all three — drawdown held, beats alpha-top5 3/3);
`conv-top3` also passed (2/3 on alpha). **rs12-top3 is the promotion
candidate** — declared now to prevent best-of-N shopping later; the
conviction score ranked no better than raw relative strength (a partial
#20 answer: its weight is carried by the trend/RS components).

**Honesty box:** the lift is modest (+0.04…+0.18 MOIC over 5–10y); the
read sample is 3 windows; the 10y straddle still loses to QQQ (2.84 vs
2.96); and on hindsight universe A's 2017/2018/2019-start windows the same
rule *underperformed* equal-all (concentrated momentum whipsaws in
reversals — 2019→2024 A: 2.35 vs 2.59, below random's p10). This is a real
but narrow edge in trending tapes, not a solved problem. The fully-honest
window's QQQ cross (1.82 vs 1.78) is one window, ~2 points of MOIC.

**Status:** gate PASSED, promotion **deferred to ≥2026-10-01** — R10
allows one promoted signal-behaviour change per quarter and the 🐳
WHALE-DIP tier used 2026-Q3's slot (2026-07-06). Until then the live
ledger (#13) accrues fresh out-of-sample rows: before promotion, check
that ⭐ names ranked top-3-by-RS12 in the ledger actually outperformed the
rest — a free forward test the promotion must also survive.

**2026-07-12 update: PROMOTED EARLY by owner override** — ahead of both
the ledger forward-check and the 2026-10-01 date (basis recorded verbatim
in `promotions.json`; PRD §8.5). The pre-registered check was NOT waived:
the #69 month-start digest block publishes the frozen Jul–Sep window read
through the 2026-10-01 read, the rolling demotion check runs alongside
it, and a FAIL demotes to equal-split-max-5 mechanically. The honesty box
above stands unchanged — the measured lift is modest and one-window; the
live rows now referee a change that is already spending money.

---

## 5 · #18 total-return correctness — the RS12 delta (run 2026-07-10)

RS12 (and RS6) now measure **total** return — dividends reinvested, on both
the name and the SPY benchmark — instead of raw price return. Raw OHLC still
drives every chip level, POC, $-volume and the G4 basis test: a printed level
has to be a price you could have traded at (EXECUTION R1).

Reproduce: `python homily_conviction.py --rs-delta [SYM…]`.

The PRD's premise (#18: "payers V MA COST LLY NVO are systematically docked")
is **only half right**, and the direction was published before it was measured:

| effect | pts on RS12 |
|---|---|
| SPY's own 12m yield, now credited to the benchmark | **−1.3** to every name |
| the name's own 12m yield, now credited back to it | +0 … +8.9 (D05.SI) |

So the delta is `name_yield − spy_yield`, not `name_yield`. A **sub-SPY-yield**
payer still loses ground: V −0.6, MA −0.6, COST −0.8, LLY −0.2. Only real
yielders gain: **D05.SI +7.6**, JNJ +2.8, NVO +2.1, KO +2.0. Zero-dividend
growth names all sit on the −1.3 floor. `CSPX.L` (accumulating ETF — dividends
are inside the NAV, never distributed) correctly takes the full −1.3.

**Across all 68 universe names, G3 flipped for none of them.** Range −1.3 …
+7.6 pts, and the gate sits at +20. The closest call is NET (+21.9 → +20.5,
still passing). This is a **correctness fix with no measured selection effect
today** — it removes a bias that would have mattered had the universe held
high-yield names, and it is the honest denominator for every future RS number.
It is not alpha, and it does not move the bar in the bottom line below.

**Footnote for §1–§4 above:** those tables were produced with **raw-close**
RS12, and are NOT regenerated. The backtests (`homily_selection_backtest.py`,
`homily_strategy_backtest.py`, `homily_core4_backtest.py`) still rank on raw
closes, so live RS12 and backtested RS12 now differ by the yield spread above.
For the momentum-growth universe those tables screen, the spread is a near
-constant −1.3 pts across names — a rank-preserving shift, which is why the
#24 `rs12-top3` gate result stands unchanged. Migrating the backtests to
`fetch_series()` is queued as **#64** (PRD §8.5); until it lands, do not
compare a live RS12 print against a number in §1–§4 to the tenth of a point.

---

## 6 · #39 bootstrap CIs on THE test (run 2026-07-11)

Circular block bootstrap (block 6 ≈ a regime half-year, 10,000 resamples,
seed 39) over each arm's 60 monthly NAV returns from the 5y THE-test window
(2021-07 → 2026-07, idx-fallback+regime arm, the faithful strategy).
P(>QQQ DCA) uses PAIRED draws — the same blocks applied to both series —
so the arms' correlation is preserved. Reproduce: `python homily_bootstrap.py`.

| arm | realized MOIC | p5 | p25 | p50 | p75 | p95 | P(>QQQ DCA) |
|---|---|---|---|---|---|---|---|
| DCA SPY (benchmark) | 1.52 | 0.99 | 1.21 | 1.36 | 1.52 | 1.76 | — |
| DCA QQQ (benchmark) | 1.77 | 0.92 | 1.23 | 1.49 | 1.77 | 2.26 | — |
| strategy A current univ (HINDSIGHT) | 1.65 | 0.96 | 1.24 | 1.48 | 1.79 | 2.36 | 53.5% |
| strategy B hype-2021 control | 1.29 | 0.79 | 1.01 | 1.21 | 1.46 | 1.91 | **23.8%** |

Reading: the one-window numbers §1 committed are points inside WIDE bands —
QQQ DCA's own 5–95 band spans 0.92–2.26×. On the honest universe the
strategy beats QQQ DCA in only ~24% of resampled paths; even the
hindsight-picked universe is a coin flip (53.5%). This does not change the
bottom-line verdict below — it quantifies how little one 5y window can
prove in either direction, which is exactly why #14's live scorecard (and
#71's pre-registered noise band, which reuses this machinery) referees all
future promotions. CAVEAT (mandatory, D-39): bootstrap cannot manufacture
unseen regimes — these are within-window uncertainty bands, not forecasts.

---

## 7 · #82 ribbon run-length (run 2026-07-11)

How long does a weekly-RED spell last once it opens? Max-history weekly
closes, live circle engine on prefixes, both universes; completed spells
only (29 open spells excluded as right-censored). Reproduce:
`python homily_ribbon_backtest.py`.

| universe | n spells | median | p25 | p75 | p90 | mean |
|---|---|---|---|---|---|---|
| A current | 1,110 | 9w | 2w | 24w | 44w | 17.0w |
| B hype-2021 | 329 | 7w | 2w | 22w | 36w | 14.8w |
| **combined** | **1,439** | **8w** | 2w | 23w | 42w | 16.5w |

Entry-candle conditioning ("big red candles open runs lasting weeks to
months") did NOT clear its pre-committed rule (big-entry median must beat
small-entry by ≥3w on BOTH universes: A +3w, B −1w) — the unconditional
base rate ships alone. Shipped: RED rows print `med run 8w`
(`RED_MEDIAN_RUN_W`, info-only, gates nothing). Danny's qualitative claim
is directionally supported — a quarter of runs last 23w+ — but entry-candle
size is not the tell he implies, at least not at our weekly-circle
approximation.

---

## 8 · #78 pullback clock (run 2026-07-11)

Dip = maximal run of non-RED daily candles inside an intact weekly-RED
spell; resolved by a RED candle (weekly still RED), failed if the weekly
circle breaks mid-run. 5y daily, live engines on prefixes. Reproduce:
`python homily_pullback_backtest.py`.

| cut | n | median | p25 | p75 | p90 |
|---|---|---|---|---|---|
| A all / H1 / H2 | 1082 / 361 / 721 | 5d / 6d / 4d | 1d | 13–14d | 21d |
| B all / H1 / H2 | 512 / 128 / 384 | 4d / 5d / 4d | 1d | 14–16d | 21–23d |
| **combined resolved** | **1,594** | **4d** | 1d | 14d | 22d |
| failures (weekly broke mid-dip) | 483 | 3d | 1d | 10d | 17d |

STABLE per the pre-committed rule (medians within ±1d, p90 within ±2d
across A/B × H1/H2) → the info-only digest counter shipped: weekly-RED
rows with a non-RED candle print `dip d{n} (med 4d · p90 22d)`. Danny's
"3–7 trading days" holds at the median, not the spread. NOT shipped: the
past-p90 trend-failure warning the PRD floated — failures resolve FASTER
(median 3d), so the resolved:failed ratio at long ages ≈ the base rate and
dip age alone carries no escalation signal. That null is recorded here so
nobody re-derives the idea.

---

## 9 · #77 multi-timeframe volatility hole (run 2026-07-11) — NULL, closed

Weekly/monthly resamples fed to the frozen daily `find_hole` engine; event
walker identical to the committed daily study. This consumed 2026-Q3's one
timing-modifier research slot (R10 / PRD §8.1 — #74 and #81 wait for later
quarters). Reproduce: `python homily_mtf_vol_backtest.py`.

**1 · SPY-monthly replication (Danny's Apr-2026 "perfect record since Dec
2013" claim): does NOT replicate as an edge.** At ref 24mo: 5 resolved
breakouts, all positive fwd6m (+2.2…+10.2%, mean +5.1%), 4/5 positive
fwd12m (mean +7.9%). But SPY's UNCONDITIONAL forward returns over the same
period are +6.0% fwd6m (78% positive) and +12.3% fwd12m (83% positive) —
the breakouts ran at or BELOW the market's base rate. The "perfect record"
is the equity drift, not the indicator; and n=5 in 12 years could not
support a rule even if the mean were above baseline. (Engine-default
ref 60: 4 events, same picture.)

**2 · Weekly-VH event study (58 names, 5y): NULL.** A: breakout fwd4w
+5.5% vs baseline +4.2% but fwd12w 12.2% vs 13.1% (below); B: below
baseline at both horizons (+1.2% vs +2.1% / +4.7% vs +6.0%); ALL: +3.5% vs
+3.2% / 8.1% vs 9.6%. The daily study's modest breakout edge (+4.4 vs
+2.8 / +11.5 vs +8.5) does NOT survive the move to weekly bars.

**3 · Sequence claim (daily fires first, weekly confirms): directionally
present, not usable.** Weekly breakouts preceded by a daily-VH breakout
within 56 days did better than those without (fwd4w +3.6% vs +2.9%, fwd12w
+8.8% vs +5.5%) — but neither leg beats the all-weeks baseline, so there
is nothing to gate money on.

Verdict: the DAILY hole keeps its place (🔵 upgrade + score component);
weekly/monthly confirmation adds nothing measurable in our universes and
ships nowhere. Closed per Part III rule 6.

---

## 10 · #79 whale-distribution warning (run 2026-07-11) — PASSED its gate; ship queued

The inverse of the 🐳 accumulation footprints (the LULU sell anatomy):
rally context (≥5% above the 60d closing low) + ≥2 of {heavy-volume weak
closes at the 20d ceiling · OBV AND A/D both below the pre-rally trough ·
top support shelf receiving zero fresh volume}. Monthly lower-highs/
lower-lows reported as a split, not folded in. 58 names, 5y, point-in-time.
Reproduce: `python homily_dist_backtest.py`.

| arm (ALL combined) | days | fwd60 | fwd120 |
|---|---|---|---|
| baseline (all days) | 55,217 | +9.7% | +19.6% |
| rally untagged | 43,215 | +9.5% | +19.5% |
| rally TAGGED | 1,833 | **+7.8%** | **+16.7%** |
| tagged + monthly LH/LL | 178 | **+5.4%** | **−0.3%** |

Pre-committed rule (tagged < untagged AND < baseline at both horizons on
ALL): **PASSED** — unlike VH breakdowns (§5b), distribution footprints do
predict forward underperformance. Two honesty caveats before anyone ships
it: (1) the effect is carried by universe B (tagged fwd60 +1.5% vs +5.9%
base; on the hindsight-picked A universe the plain tag was NOT predictive —
+14.0% vs +13.2%), i.e. it flags the 2021-wreck top anatomy, not every
rally; (2) the sharp variant is the monthly-LH/LL confluence (n=178,
fwd120 −0.3% vs +19.6%) — the plain tag alone would nag plenty of winners.

Shipping is NOT this session (Part III rule 5): the digest surface — PRD
scope guard verbatim: held satellites / Bucket-B rows and a 🚀-candidacy
veto input only, core names and the index never get a sell tag — is its
own future gated session, preferring the +mLHLL variant, and any veto
behaviour queues behind R10 (Q4 is #24's natural slot; this waits its
turn).

---

## 11 · #20 conviction-score backtest (run 2026-07-11) — the score ranks; the tiers don't

Weekly point-in-time replay 2021-07 → 2026-07 (260 Fridays), live
`danny_signal`+`conviction` on trailing-5y windows, within-day score
deciles, block-bootstrap 90% bands, ≥30 obs per row. A = live 70-name book
(HINDSIGHT), B = frozen hype-2021 control. Reproduce:
`python homily_conviction_backtest.py`.

**Decision (pre-committed in D-20): the relabel branch does NOT trigger.**
OOS (2024-07→2026-07) decile means are monotone on BOTH universes —
A: ρ = +1.00, D0 +2.7% → D9 +30.1% fwd126 excess; B: ρ = +0.99 (computed
from the committed run's decile means), D0 −12.3% → D9 +14.6% (band on
B's top decile is wide: [−0.9, +32.0]%). Top-decile excess > 0 on both.
The 🚀 footer keeps its wording; any weight change is a Phase-C promotion
that queues behind R10 (Q4 belongs to #24 first).

**The honest second finding: the TIER CUTS add nothing.** Episode-level
outcomes within 500 bars:

| tier (universe) | episodes | P(≥2×) | P(≥5×) | P(−50% first) |
|---|---|---|---|---|
| CONVICTION (A / B) | 577 / 219 | 44% / 26% | 8% / 3% | 18% / 36% |
| STARTER (A / B) | 595 / 170 | 39% / 22% | 4% / 2% | 13% / 37% |
| fails (A / B) | 731 / 243 | 40% / 24% | 7% / 3% | 17% / 39% |

CONVICTION ≈ STARTER ≈ fails on every outcome. The score's *cross-
sectional ranking* carries information (deciles above); the 75/60
*thresholds* — which set the ≤5%/≤2% sizing tiers — separate nothing, and
the five gates passed 144 wreck-episodes on B (36% of gated CONVICTION
entries halved before doubling — full list in the run output). Danny-style
sizing by score TIER is, on this evidence, sizing by noise around the
cuts; the ranking, not the label, is where the signal lives. Full-window
A also shows a U-shape (D0/D1 fat from 2021-22 losers mean-reverting) —
another reason the within-day OOS read, not the pooled one, is the
decision input.

---

## 12 · #67 hard-rule provenance audit (run 2026-07-11) — every declared constant priced

Owner's question: "any smart way to determine these hard rules instead of
gut feeling?" Method: a declared rule is insurance — price the PREMIUM
(cost on realized paths) and the PAYOUT (what it saves in the wreck case).
Fidelity: the uncapped arm reproduces the committed emergent EQ numbers to
drift 0.00e+00 before any sweep number is read. Reproduce:
`python homily_cap_backtest.py` · `python homily_bear_backtest.py
--bucketb` · `python homily_whale_backtest.py --dispersion`.

### The rule-provenance registry (who owns each hard constant)

| Constant | Where | Provenance after this run | Owner study |
|---|---|---|---|
| 10m SMA regime, monthly close | §4 | tested (30y; D-63) | #63 done |
| no adds while ⚪ | §1/§2 | tested implicitly (emergent) | — |
| no ⭐ → full amount to index | §3.5 | tested | — |
| never-sell / hold-through | §3/§5 | tested (THE · emergent · multiwindow) | #40 yearly |
| 🐳 WHALE-DIP tier exists | §3.6b | tested + gated (§5h) | — |
| **10%/name add-cap** | §3.4 | **declared → PRICED (Step 1–2 below); stays** | this study |
| 10% Bucket-B "earned" threshold | §1 | declared → measured insensitive (Step 3) | this study |
| ≤2% whale-dip cap | §3.6b | declared → **derived 1.6%** (Step 4); adoption queued | this study |
| max 5 ⭐ names/month | §3.4 | declared → measured ≈ null (Step 5) | this study |
| 50/50 A-vs-stock split | §7 | declared, behavioural; frontier printed (Step 5) | info-only forever |
| ⚪ 12w + F:0–1 → sell half | §5.2 | declared | #51 (queued) |
| thirds re-entry / bear trim | §4.7/§4.3b | declared | D-63 modes |
| margin zero | §6 | ruin-avoidance — not tunable | excluded by design |
| F thresholds | homily_fund | declared, info-only | #66 absorbs |
| score <60 → no capital | HOW_IT_WORKS | declared → §11: tier cuts separate nothing | #20 ran |

### Step 1–2 · the add-cap, priced (universe B = the judge)

Premium (uncapped − 10%-cap MOIC, redistribute treatment, per window):
+0.63/+0.97 in the sparse 2015/2016 5y windows (3–8 eligible names — the
cap fights diversification itself there), **+0.05 in the fully honest
2021→2026 window**, ±0.03 in 2017–2020 starts, +0.51/+0.55 in the 10y
windows. On hindsight universe A the cap is free-to-beneficial (uncapped
loses 6/9 redistribute windows). Formal prong check: 25%-redistribute
ties-or-beats 10% in 7/9 windows with shock-MaxDD within 5 pts → **by the
letter of D-67 a move UP to 25% is adoptable**; uncapped also clears the
prongs but ∞ is excluded by rule.

Payout (top name gapped at the uncapped book's peak-top1 date, no
recovery, 10y window, shock target SHOP): at −80%, 10%-cap MOIC 1.96 vs
uncapped 1.70; at −95%, 1.89 vs 1.49 — and 25% gives back half the
protection (1.70 @ −95%). On the 5y wreck window (target PLTR) the cap
bought nothing (1.40 vs 1.43 @ −80%): redistribution pushed the skipped
cash into other 2021 wrecks. Step 2a natural pricing: worst-single-name
damage is ≤1.8% of paid at EVERY cap level in EVERY window — **wrecks lose
⭐ long before they accumulate; the ⭐ gate, not the cap, contains wrecks**
(the D-67 hypothesis, confirmed).

**2026-07-12 update: PROMOTED to 25% by owner override** (#92/D-92,
`promotions.json` "add-cap-25") — ahead of the clean 2027-Q1 slot, on the
letter-of-D-67 adoptability above. The recorded cost stands: 25%
surrenders half the −95% shock payout (1.70 vs 1.89). Demotion armed and
checked every run (validate [50]): a ≥15%-of-book name closing −50% from
its post-promotion high reverts the cap to 10% mechanically. R10
arithmetic: 2027-Q1's slot is spent early; next free slot 2027-Q2. The
original decision text below stands as the record of what the study
itself concluded.

**Decision (per the pre-committed rule + R10):** the cap STAYS at 10%
today — §8.0's one-live-change/90-day spacing and R10 bind any move (🐳
holds Q3), and the shock table shows 25% surrenders half the payout the
cap exists for (a dimension the prongs didn't pin, recorded here so the
Q4+ promotion session weighs it). PLAYBOOK §3.4 now quotes the measured
premium in place.

### Step 3 · Bucket-B threshold {none, 8, 10, 15}% — insensitive

Faithful-§4 arm, univ B 5y: MOIC 1.36/1.44/1.44/1.36; sell-into-index:
1.70/1.67/1.67/1.70. Spread ≤0.08 MOIC with one bear onset in the window —
a sensitivity table, never a headline. The 10% digit is not load-bearing.

### Step 4 · whale-dip cap derived from episode dispersion

680 whale-dip episodes (5y, 58 names): fwd60 p5 −31.7%, median +7.3%,
p95 +67.6%. Cap sized so a p5 episode costs ≤0.5% of book: **1.6%** —
inside the pre-committed [1%, 4%] adoption band, so the 2% rule graduates
from gut to derived. The 0.4-pt tightening (and the #31 copilot constant
sync) queues behind the same 90-day spacing as everything else.

### Step 5 · max-⭐ sweep + the 50/50 frontier (info-only)

Max ⭐ {3, 5, 8, ∞} on the honest 2021 window: B 1.74/1.74/1.70/1.70
MOIC — ≈ null, as §5g predicted (A: 3.85/3.93/3.80/3.78). Keep max-5 for
simplicity, not edge. Blend frontier (B, vs DCA-SPY 1.50): stock-half
30/50/70% → 1.56/1.60/1.64 — the split buys drawdown tolerance, not
return; §7's behavioural definition stands, info-only forever.

---

## 13 · #21 refine re-point (built 2026-07-11) — diagnostic passed, parallel run started

The Calmar objective tunes a strategy §1 retired; the circle's live job is
gating composite states. New objective (D-21): J(p) = mean fwd-60d excess
of ⭐(p) days vs same-name drift − 0.5 × FB(p), FB = fraction of ⚪(p)
days followed by ≥+15% in 60d (the PLTR-June class as a first-class term).
Reproduce: `python homily_refine_objective.py --diagnostic`.

**Diagnostic (D-21 step 1, ran before anything else):** pooled ⭐-days
per walk-forward fold = 479 / 1,012 / 736 on the 8-name basket — all ≥100,
so the ⭐ objective stands (no RED-day fallback). λ sensitivity: param
rankings IDENTICAL at λ=0.25 and 0.5, reshuffled at λ=1.0 — λ stays 0.5
(fixed a priori), and the eventual switch session must treat the ranking
as FB-sensitive at high λ. First read of J levels: J(champion) −0.276,
J(default) −0.281, with FB ≈ 52–54% — on this momentum basket half of all
blocked days were followed by +15% in 60 days, i.e. the false-block cost
the objective exists to punish is real and large in this window.

**Parallel run live:** `homily_refine_j.csv` (sibling append-only file —
the Calmar log's history stays byte-identical, R2) accrues J(champion) and
J(challenger) daily via `daily_refine(bars_map=…)`; workflow commits it
(R8). `homily_champion.json` now carries `"objective": "calmar"` so every
champion states which regime selected it. Earliest switch read:
**2026-08-22** (30 rows), its own session, same +10% OOS margin — champion
selection stays Calmar until then.

---

## 14 · #66 right-stock discipline (run 2026-07-11) — wreck-separation FAILED; label only

Sticky quality tier Q (0–7 pts: growth 10/25% · profit · margin direction
· FCF · dilution <12% · 3y RS ≥ SPY; Q1 ≥5, Q2 3–4, Q3 ≤2 — cuts committed
before the run) computed from filings FILED on/before 2021-11-01, judged
on forward 24m. 45 scoreable names, both universes. Reproduce:
`python homily_quality_backtest.py`.

| tier @2021-11 | n | mean fwd24m | median |
|---|---|---|---|
| Q1 | 32 | −24.6% | −23.1% |
| Q2 | 8 | −70.9% | −71.7% |
| Q3 | 5 | −50.2% | −43.8% |

**Pre-committed rule: FAIL.** The Q1−Q3 gap (+25.5 pts) clears its prong,
but only 4/8 canonical wrecks scored ≤Q2 (need ≥60%) — ZM, DOCU, ROKU and
W were **Q1 on their as-of filings** (ZM: profitable, revenue +300%; the
2021 class was overwhelmingly a VALUATION collapse, not broken businesses
at filing time), and the tier ordering isn't even monotone (Q2 fared
worst). Fundamentals-as-filed cannot separate that wreck class; a Q-gated
💎 buy signal or thesis-break veto built on it would be false confidence.
Per D-66's own rule: **the Q label ships info-only (it still changes what
a human reads during the next NVDA-2022) and everything downstream — 💎
buyable state, dip-add veto, #24's Q tie-break arm, #51's Q split — stays
dead.** The PLTR regression passed for the record (Q1 as-of 2026-06, the
veto would not have blocked Danny's add) but is moot. Implementation note:
Q lives in NEW `homily_quality.py` — the frozen `homily_fund.py` was not
touched, so no engine-freeze question arises either way.

---

## 15 · #91 leverage-ladder backtest (run 2026-07-12) — PASSED; LEVERAGE.md signed

The D-91 ladder (BULL ≤1.30× / MIXED ≤1.15× / BEAR = margin zero) simulated
on total-return QQQ with month-end 10m-SMA regime labels (SPY+QQQ, applied
next session — no look-ahead), monthly releverage, maintenance 0.25,
financing constant 5.8%/yr base + 7.8% stress (DELIBERATELY conservative:
the ZIRP decade's real ~2% margin would flatter every levered arm).
Decision rule frozen in the file docstring before the run. Reproduce:
`python homily_leverage_backtest.py`.

| window | QQQ B&H | timed (cash in 🐻) | ladder 1.15× | **ladder 1.30×** | 1.50× (info) |
|---|---:|---:|---:|---:|---:|
| 2020→2025 | 2.27 | 1.88 | 2.38 | **2.57** | 2.84 |
| 2021→2026 | 2.14 | 1.53 | 2.18 | **2.29** | 2.45 |
| 2016→2026 (10y) | 7.30 | 3.78 | 8.10 | **9.43** | 11.49 |
| MAX 1999→2026 | 16.86 | 19.66 | 20.55 | **25.53** | 33.44 |

**Readout (pre-registered): PASS at L=1.30.** (a) Zero margin-call breaches
in any window — every rolling 5y since 2015, both 10y, and the max-history
path through dot-com + 2008 + 2022 — at base AND stress financing; worst
equity/position ratio 0.68 (boundary 0.25). (b) Beat unlevered QQQ on 3/3
construction-honest read windows net of financing (stress cells also
clear: 2.51 / 2.24 / 8.98). LEVERAGE.md signed same day at 1.30/1.15/1.00
(owner override, §8.5 — the policy's only immediate live effects are
constraints).

**Honesty box:** (1) the ladder does NOT protect from bears — BEAR = 1.00×
stays invested, so the max-history levered drawdown is −86% vs QQQ's −83%
(protection is the CORE book's 🐻 protocol, a different product; the timed
arm shows what exiting does: −37% MaxDD but it loses every modern 5y/10y
window to buy-and-hold, 1.53–3.78 vs 2.14–7.30 — regime EXIT only pays
across giant bears, which is exactly the D-63 conclusion re-found on the
index). (2) The edge is the equity risk premium financed below its return,
gated so the margin never sees a bear — +1…+2.5 CAGR pts/yr on the read
windows; it is NOT stock-picking alpha and it does not touch the §14
bottom-line verdict on the strategy engine. (3) Intra-day gaps below the
daily close are not modeled; the 0.68 worst ratio is the measured headroom
against that risk, and concentrated maintenance >0.25 would shrink it —
both stated in LEVERAGE.md §1. (4) The CORE-BOOK BAN is arithmetic, not
simulation: d\*(L) = (1−mL)/(L(1−m)) puts every constant L ≥ 1.25 inside
the strategy book's own measured −59…−76% drawdown range. No leverage on
the core monthly book, ever.

**The new referee this creates:** any levered arm (the #93 swing sleeve
included) is now scored against regime-gated 1.30× QQQ at the same
financing — 2.57 / 2.29 / 9.43 on the read windows. Leverage that cannot
beat the same leverage on the index belongs on the index.

---

## Bottom line — measured against the owner's bar

**The strategy engine, as an index-beating machine, does not clear the
bar.** On construction-honest evidence it beats the S&P 500 more often
than not, but it does **not** reliably beat QQQ over ≥5y windows — the
fully honest window loses to QQQ slightly, the 2021-straddling windows
lose to both, and every strategy arm carries **2–3× the index drawdown**
(−59…−76% vs −34%). "DCA into QQQ and never look" remains the strongest
simple competitor, exactly as the 2026-07-08 revision concluded — and the
cleaner protocol strengthens that conclusion.

**The live path toward the bar (owner's standing directive: don't
concede):** §4's rs12-top3 concentration is the first gated, pre-registered
change that moved the honest window past QQQ (1.82 vs 1.78) — promotion
queued for 2026-Q4 behind a ledger forward-check. The remaining levers, in
expected order of impact: the universe itself (#65 — a screen can't buy a
winner it never sees), the ⚪ time-stop calibration (#51, sharpening the
one return-adding exit), and the re-pointed refine loop (#21). One gated
change at a time; the scorecard (#14) referees.

**What the system measurably IS good for:**
1. **The per-name §5.2 exit added ~3 pts/yr on the wreck-salted control**
   — the one arm with a repeatable, attributable edge (getting out of
   broken businesses). Worth calibrating properly (#51) and promoting only
   through its gate.
2. **The 🐻 protocol is honestly-priced tail insurance** — ~1 pt/yr over
   33 years to turn −76% into −29%. That is a *behavioural* product: it
   exists so the human survives the grinder without capitulating.
3. **Discipline infrastructure** — the ledger, alerts, buy-day copilot and
   honesty gates change the savings rate and the behaviour gap (#58),
   which PLAYBOOK §8 already ranks above any signal.

Anything claiming more than that is not supported by our own numbers.

**2026-07-12 addendum (§15, owner max-return directive):** the first
measured, adoptable path PAST the QQQ bar at account level now exists and
it is not stock-picking — **regime-gated 1.30× leverage on QQQ itself**
(+0.15…+2.13 MOIC over the read windows net of financing, zero margin
calls on any measured path incl. 1999→2026). LEVERAGE.md governs it. The
bar for every strategy arm accordingly RISES: beat levered QQQ at the same
L, not just QQQ. The strategy engine's verdict above is unchanged; what
changed is that "outperform QQQ" no longer requires the engine to do it.

## 16 · #51 ⚪ time-stop calibration (run 2026-07-17) — PASSED; w=2 (8 weeks) queued

`homily_timestop_backtest.py` — D-63's mode (f) with `caution_months`
parametrized (default replays the committed tables byte-identically).
$1/month, 10 bps, idx-fallback SPY, point-in-time signals on prefixes.
Same caveat as every mode-(f) number: the F:0–1 gate isn't modelled
(fundamentals not point-in-time) — cells are the aggressive bound, the
cross-w comparison is like-for-like.

| w (mo ≈ wk) | B·5y MOIC | B·10y MOIC | A·5y | A·10y | B·10y MaxDD |
|---|---|---|---|---|---|
| 1 (~4wk) | **2.15** | **3.07** | 2.62 | 3.86 | −58% |
| 2 (~8wk) | 1.99 | 2.73 | 2.36 | 4.29 | −63% |
| **3 (~12wk, incumbent)** | 1.80 | 2.55 | 2.36 | 4.22 | −65% |
| 4 (~16wk) | 1.88 | 2.25 | 2.39 | 5.09 | −68% |
| 6 (~24wk) | 1.76 | 2.20 | 2.43 | 4.79 | −68% |

Pre-registered rule (frozen in the file's docstring before the run):
challenger must win MOIC on BOTH universe-B windows, not lose both A
windows, MaxDD within +5 pts; minimal change wins among passers.
**w=1 and w=2 both pass; w=2 is the minimal-change winner.** Reading:
the declared 12 weeks is too patient — a broken name's first two ⚪
months carry most of the salvage value; cutting to 8 weeks adds ~0.2
MOIC on the wreck-salted control at slightly BETTER drawdown, and even
the hindsight universe doesn't punish it (A·10y 4.29 vs 4.22). w=1 is
stronger still on B but trades 60–90% more and loses A·10y — the rule's
minimal-change clause exists precisely to resist that reach.

~~**Ship status: NOTHING changed today** (Part III rule 5). PLAYBOOK
§5.2's "12+ weeks" edit is a registry promotion with a demotion rule,
QUEUED behind R10 with #79/#67-whale-cap/#20 — next free slot 2027-Q2,
order per SPECS §1.~~ **SHIPPED 2026-07-22** — see §16b.

## 16b · #51 re-run + the QQQ bar the first run never published (2026-07-22)

Owner directive: "ignore R10, ship everything that you think will improve
our odds, and backtest them rigorously." Before shipping, the study was
re-run on rolled data (`python3 homily_timestop_backtest.py`, windows now
2021-07-22 / 2016-07-22 → 2026-07-21) and the **DCA QQQ row — which
`grid_table` has printed on every run since 2026-07-17 and which the §16
table above silently omitted — is published here.** §16 answered "which
w wins"; it never asked whether the winner clears the north star.

| window | DCA SPY | **DCA QQQ** | w=1 (~4wk) | **w=2 (~8wk)** | w=3 incumbent | w=4 | w=6 |
|---|---|---|---|---|---|---|---|
| **B · 5y** (honest) | 1.50 | **1.73** | 2.10 | **1.95** | 1.77 | 1.83 | 1.71 |
| **B · 10y** (honest) | 2.09 | **2.86** | 3.01 | **2.69** | 2.51 | 2.22 | 2.16 |
| A · 5y (hindsight) | 1.50 | 1.73 | 2.66 | 2.36 | 2.35 | 2.36 | 2.39 |
| A · 10y (hindsight) | 2.09 | 2.86 | 4.00 | 4.34 | 4.27 | 5.16 | 4.82 |

MaxDD, B·10y: QQQ −34% · w=1 −57% · **w=2 −62%** · w=3 −64% · w=6 −68%.
MaxDD, B·5y: QQQ −34% · w=2 −25% · w=3 −24%.

**Gate: PASS, reproduced.** Passing set [1, 2]; w=2 the minimal-change
winner — identical verdict to 2026-07-17 on independently rolled data.
w=2 beats the incumbent on both honest windows (1.95 vs 1.77; 2.69 vs
2.51) at better B·10y drawdown (−62% vs −64%).

**The north-star reading, recorded because it cuts against the ship:**
on the 5y honest control the engine beats QQQ-DCA at markedly better
drawdown (1.95 vs 1.73, −25% vs −34%). **On the 10y honest control it
LOSES to QQQ at every w except w=1** — incumbent 2.51 and promoted w=2
2.69 both trail 2.86, at roughly twice the drawdown. This promotion
NARROWS a losing gap; it does not close it. PRD §5i's verdict ("beats
SPY mostly, does not reliably beat QQQ, 2–3× index drawdown") survives
this study intact and should not be quoted as overturned.

**Why w=1 was NOT taken, though it is the only setting that clears QQQ
on B·10y (3.01 vs 2.86).** It loses A·10y (4.00 vs 4.27), takes −57%
drawdown, and trades 83% more (1484 vs 812 fills). The frozen rule's
minimal-change clause selected w=2 on 2026-07-17, *before* anyone looked
at a QQQ column. Re-picking w=1 now, having seen that column, would be
choosing a parameter because it flatters the north star — the precise
post-hoc selection this file's pre-registration discipline exists to
prevent. The clause was written to resist exactly this temptation and it
was honored. Recorded so a future session does not "fix" it.

**Shipped:** `homily_positions.CAUTION_WEEKS = 8` (the live flag), PLAYBOOK
§5.2 Rule 2, `trim_flags` docstring, HOW_IT_WORKS F:n/3 row. NOT touched:
`homily_bear_backtest.CAUTION_MONTHS = 3` — that is the BACKTEST replay
constant every committed table in this file depends on, and gambit's
`TIME_STOP_DAYS = 84`, which is the swing sleeve's separate A5 rule.
Registry entry `timestop-8wk` carries a frozen demotion rule with a real
checker (`homily_promotions.timestop_watch`, paired-episode read over
committed ledger rows: mean delta > 0 across ≥8 episodes = the earlier
exit destroyed value = mandatory revert to 12). Gate: validate [35],
which now pins both sides of the 8-week boundary and the constant itself.

## 17 · #86 dip war-chest (run 2026-07-17) — NULL on both arms; the instinct closes

`homily_warchest_backtest.py` — D-86's protocol verbatim, rule frozen in
the design before any run. Fraction f of the monthly dollar accrues to a
reserve that deploys whole on the first qualifying dip event (fresh ⭐ ·
fresh 🔵 · ⚪+🎯+🐳 capped 2% · 🟡+🎯), stale tranches sweep to the index
after k months; grid f∈{25,50}% × k∈{2,3,6}, both deployment rules
(equal-all pre-rule, rs12-top3 live), fund-unit NAV, 10 bps.

Universe B (honest control), MOIC vs the f=0 baseline:

| window | arm | baseline | best war-chest cell |
|---|---|---|---|
| 2020→2025 | equal-all | 1.71 | 1.65 (all cells lose) |
| 2020→2025 | rs12-top3 | 1.89 | 1.79 (all cells lose) |
| 2021→2026 | equal-all | 1.70 | 1.65 (all cells lose) |
| 2021→2026 | rs12-top3 | 1.82 | 1.74 (all cells lose) |
| 2016→2026 | equal-all | 2.76 | 2.65 (all cells lose) |
| 2016→2026 | rs12-top3 | 10.24 (A) / — | see log; B cells lose |

**VERDICT (D-86's rule, mechanically applied): NULL on both arms — no
(f,k) cell wins ≥2 of 3 read windows.** On the honest control every
single cell LOSES to just deploying the money; bigger f loses more
(f=50% turned 2021→2026 CAGR negative). Universe A shows scattered tiny
wins (hindsight, not evidence).

**The structural finding that kills the idea more thoroughly than the
MOIC table:** k never mattered — every (f,·) column is identical. With
a ~30-name screen, a qualifying dip event fires essentially every
month, so the reserve deploys almost immediately and "ammunition" never
accumulates. The war-chest premise assumes dips are SCARCE; in this
system they are the most common event there is. This is §5f's per-name
lesson at the budget level, now measured: waiting costs, the discount
never arrives scarce enough to pay for the wait. Fourth measurement
pointing the same way; the idea closes beside §5f per the design.

## 18 · #87 concentration regime conditioner (run 2026-07-17) — NULL; demotion rule stays the only guard

`homily_selection_backtest.py --conditioner` (flag-gated; the committed
run's paths untouched). Three pre-existing conditioners, thresholds
pre-registered (regime ≠ BULL · breadth < 30 (#26's own line) · trailing
3m QQQ < 0); implied strategy = equal-split in hostile months, rs12-top3
otherwise.

Sign-flip test (full 2015→2026 span): ALL three conditioners flip on
both universes — top-3 only earns its concentration in favourable
states (B favourable: 32.8 vs 31.8 compounded; hostile: both arms ~0.2,
i.e. everything loses together). That is the descriptive confirmation
of §4's honesty box.

But the tradable version fails: the conditional arm LOSES to
always-top-3 on ALL THREE universe-B read windows for ALL three
conditioners (e.g. 2021→2026: regime 1.80 / breadth 1.80 / qqq3m 1.77
vs 1.82) — in hostile months the arms fall together, so standing down
to equal-split saves nothing and costs the re-entry. Universe A shows
±0.02–0.05 noise (hindsight). **VERDICT (D-87's rule): NULL — no
conditioner clears "≥ +0.05 MOIC on ≥2 of 3 without losing any". The
item closes; the live rs12-top3 demotion rule (promotions.json,
month-start check) remains the only guard on concentration's weak
side.** The right lever for reversal pain stays #24's October
forward-check, not a regime switch.

## 19 · #104 POC-cross event study (run 2026-07-18) — NULL both directions; POC stays a printed level

`homily_poc_backtest.py` (PRD §5l — Danny's "close above POC bullish /
close below = pullback-or-downtrend-start"). Point-in-time: day i's
reference is the PRIOR day's POC (`build_profile(bars[:i])`, no same-day
look-ahead), event = state-flip of close-vs-POC, fwd 20/60d vs the
unconditional baseline over the same eligible days, 5y daily, both
universes, down-crosses also cut by the live digest state on the event
day.

First finding, descriptive: our decayed-POC is crossed **~8×/year per
name** (2,534↓ / 2,565↑ across 64 names × 5y) — in this approximation it
sits too close to price to be a level of consequence.

Second finding, the verdict: no information either side. Combined
down-cross +3.2%/20d vs +3.3% baseline and +9.2%/60d vs +9.9%; up-cross
+3.4%/20d vs +3.3%, +9.3%/60d vs +9.9% — and no sign consistency where
it matters (universe A down-cross 20d sits AT baseline, 4.3% vs 4.3%).
Danny's "pullback" framing (POC loss inside an intact trend) fares no
better: the uptrend cut runs ABOVE baseline at 20d in universe A (+4.6%
vs +4.3%) and collapses only in universe B's 60d (+0.3% vs +4.1%) — the
two universes disagree, which is exactly what the pre-committed rule
exists to catch. **VERDICT (rule in the script header, #79 precedent):
NULL both directions — POC↓ never joins #102's tells, POC↑ earns no row
note, the item closes.** The POC remains what it always was here: a
printed context level. Honest caveat, recorded: our fixed 60d-half-life
volume-at-price POC is a transparent stand-in for Danny's undisclosed
turnover-decayed chip engine — this null is about OUR approximation, not
a disproof of his read on his own tool.

## 20 · #106 provisional-bar check (run 2026-07-18) — MATERIAL at 7.5%; the `…` mark ships

`homily_provisional_backtest.py` (PRD §5l — Danny's "to be finalized").
5y daily replay, both universes, 54,072 day-name observations, comparing
each day's LIVE read (in-progress bar included, exactly what the digest
printed) against the verdict the same period produced at its final bar.
State impact computed exactly without `danny_signal` calls: the label
changes iff class(mu, circle) changes — `near_support`/`bottoming` are
daily-frequency and identical across the counterfactual (proof in the
script docstring, mirroring the frozen branch order).

| | A current | B hype-2021 | combined |
|---|---:|---:|---:|
| `monthly_up` differs from settled month | 9.54% | 10.41% | **9.87%** |
| …of which in the month's first 10 sessions | 67% | 64% | 66% |
| weekly circle differs from settled week | 4.40% | 3.88% | 4.20% |
| digest STATE class would differ | 7.71% | 7.13% | **7.49%** |

**VERDICT (pre-committed 2% bar): MATERIAL — the display-only mark
ships** (same session): `homily_provisional.marks()` → a `…` on the
row's `mUP`/`mDN` token inside the month's first 10 sessions (counted
from the name's own bars — HK/US calendars differ) and on the `wk`
circle token for Mon–Thu prints. Wired through defaulting kwargs
(`fmt_row(prov="")`, `render_digest(prov=None)`) — goldens and the state
machine byte-identical with the mark off; validate [62] asserts the
session/weekday rule, default-off, and that stripping `…` reproduces the
unmarked digest byte-for-byte. R1 untouched: the engines keep using
every bar; only the *presentation* stops calling a provisional read
settled. Known miss, accepted: a Friday-holiday week escapes `w…`.

## 21 · #107 accumulation-window durations (run 2026-07-18) — ⭐ is a moment, not a campaign

`homily_accum_backtest.py` (PRD §5l — Danny Jul 2024: "my accumulation
period usually lasts 3 months to 1 year", i.e. 13–52 weeks). Weekly-grid
replay (D-20 precedent), live `danny_signal` on prefixes, completed
spells only (#82's right-censoring rule), 5y, both universes. The
committed ledger (live since 2026-07-08) has no completed spell yet —
replay only, noted.

| spell type | n | p25 | median | p75 | p90 |
|---|---:|---:|---:|---:|---:|
| ⭐ ACCUMULATE (A) | 977 | 1w | 2w | 3w | 6w |
| ⭐ ACCUMULATE (B) | 318 | 1w | 2w | 3w | 4w |
| ⭐ ACCUMULATE (combined) | 1,295 | 1w | **2w** | 3w | 5w |
| 🐳 footprint (combined) | 1,043 | 1w | **1w** | 2w | 3w |

**Reading (pure measurement, gates nothing):** our windows are an order
of magnitude shorter than Danny's band — his 3mo–1yr "accumulation
period" is a *campaign* assembled from many short zone-visits, ours is
the zone-visit itself. The monthly buy routine (repeated visits) is what
builds campaign-length exposure, so the #50 within-window tranche idea
has no measured room to operate: the median window closes before a
multi-tranche clock would tick twice. One patience-calibration paragraph
added to PLAYBOOK §3 (info-only). Caveat: the weekly grid quantizes —
sub-week spells register as 1w — but the gap to 13w is unambiguous.

## 22 · #108 triple-red continuation (run 2026-07-18) — NULL, and mildly the wrong sign

`homily_triplered_backtest.py` (PRD §5l — IBRX Feb 2026 "Triple Red
(Bullish) candles remain in force"). Event = a daily-RED run (live
`daily_candle` semantics, one-pass R6 prefix equality, spot-checked
against the real prefix call) first reaching 3; fwd 5/10/20d vs the
unconditional baseline; 2,852 events, both universes.

| univ | 5d ev/base | 10d ev/base | 20d ev/base |
|---|---:|---:|---:|
| A current | +0.14% / +0.67% | +0.89% / +1.33% | +2.21% / +2.65% |
| B hype-2021 | −1.27% / −0.10% | −0.38% / −0.34% | −1.15% / −0.81% |
| combined | −0.39% / +0.38% | +0.40% / +0.69% | +0.93% / +1.33% |

**VERDICT (pre-committed): NULL — the `3R` suffix never ships; closed.**
Not only does the event fail to beat baseline anywhere, it sits BELOW
baseline at every horizon on both universes: the third consecutive red
close is a slightly *worse*-than-average day to add (buying a 3-day
burst is mild chasing). Consistent with #82's ribbon-conditioning null:
run-length continuation claims keep failing to survive measurement on
our furniture. Recorded so nobody re-derives it.

## 23 · #105 breakout-add anatomy (run 2026-07-18) — PASSED; ⤴ tag queued for its own gated session

`homily_breakout_backtest.py` (PRD §5l — Danny's NVDA Jun-2025 buy-signal
post: close above the longest momentum bars, valid only with an updated
whale read). Event = first close above the prior-day profile's nearest
major overhead shelf (`resistance[0]`, top-8 strongest de-duplicated
peaks — the shelf a live rule could actually have watched) with 🐳
within 10 sessions (live `whale_read`, same-day convention). Comparators:
DCA baseline + first cut-day of each ⭐ spell (weekly grid). 1,407
breakout events, 5y, both universes.

| arm (univ) | 20d | 60d | 120d | med DD | p10 DD |
|---|---:|---:|---:|---:|---:|
| BREAKOUT+🐳 (A) | +4.0% | **+14.6%** | +27.7% | −11.5% | −33.2% |
| ⭐-dip entry (A) | +4.2% | +13.4% | +26.1% | −12.4% | −34.9% |
| DCA baseline (A) | +4.3% | +13.4% | +27.9% | — | — |
| BREAKOUT+🐳 (B) | +0.2% | **+5.6%** | +6.7% | −20.4% | −42.9% |
| ⭐-dip entry (B) | +0.1% | +0.9% | +3.7% | −22.7% | −49.7% |
| DCA baseline (B) | +1.5% | +4.1% | +6.2% | — | — |

**VERDICT (pre-committed three-leg bar): PASS** — beats DCA at 60d on
both universes and the control's median worst-forward-DD is *shallower*
than the ⭐-dip's. The finding worth keeping: in the wreck universe the
whale-confirmed breakout beat our dip entry by ~5pt/60d with less
drawdown — confirmation-on-strength filtered the 2021 wrecks better
than dip-buying did. Honest limits, attached to any future ship: no
edge at 20d in the control (−1.3pt — the entry is early by a month), at
baseline by 120d in universe A (the edge is a 60d phenomenon), and the
event needs 🐳 within 10 sessions — the shelf-break alone was NOT
tested separately here. **Ship path (pre-registered): info-only `⤴` row
tag, its own session + gate + validate case; discretionary ≤2%
WHALE-DIP framing at most; budget, copilot and engines untouched — and
any money-flow change would additionally need an R10 slot (next free
2027-Q2).** *Shipped 2026-07-19 — `homily_breakout.py`, validate [63],
HOW_TO_READ row with the limits attached.*

## 24 · #109 whale-level thresholds (run 2026-07-19) — NULL; his 0–100 scale is not reachable from OHLCV

`homily_whalelevel_backtest.py` (PRD §5m — "whales need 50% to run, 75%
to surge"; WULF 94% vs MARA 9%). Pre-registered proxy, fixed before the
run: LEVEL = 100 × (accumulation-day share + OBV-rise share)/2 over
trailing 60 sessions; 12,091 weekly-grid obs, fwd 60/120d, quintiles +
his absolute marks.

Two findings. First, the **scale never gets there**: the proxy's max is
55 across both universes and 5 years — zero observations ≥75, 66 ≥50.
Any day-share-shaped proxy is mean-reverting around ~35; Danny's 9%-vs-94%
spreads must measure a *stock* quantity (share of float/chips held by
large accounts), not a *flow* day-count — unknowable from public OHLCV.
The 50/75 kink is therefore untestable here, recorded as such (the 66
obs ≥50 ran +20.6%/60d — suggestive, far too few to lean on). Second,
the tradable cut fails the pre-committed rule: Q5>Q1 holds at 60d in
universe A (+15.0% vs +8.3%, a real gradient) but flips in the control
at 60d (+1.3% vs +2.1%) and ties at 120d in A (23.6 = 23.6).
**VERDICT: NULL — no `wh:n%` column; closed.** The rank semantics (#80's
`whale_rank`, cross-sectional, shipped) remain the only whale-comparison
surface, which the MARA/WULF post itself supports.

## 25 · #110 retail-crowding warning (run 2026-07-19) — NULL: the tag is a near-empty set

`homily_retail_backtest.py` (PRD §5m — CELH Aug 2024: heavy retail
accumulation + no whale bar = bearish). Pre-registered tag: rally (≥5%
off the 60d low) + heat (20d avg volume ≥1.3× 50d) + churn (OBV flat
over 21 sessions) + both rally-compatible whale footprints absent (the
third, flow divergence, is dip-gated and cannot fire in a rally —
recorded up front).

The result is a base-rate finding, not a return finding: **33 tagged
observations** out of ~12,000 rally cuts across 64 names × 5y — on
liquid US names, sustained heat with zero net flow and zero whale
footprints during a rally essentially does not occur; some footprint is
almost always present. At n=33 the returns are noise (60d +6.8% vs both
baselines ~+9.6% — under; 120d +20.3% vs +19.4/+19.8 — over) and the
pre-committed #79-verbatim rule fails. **VERDICT: NULL — no #102 tell,
closed.** Danny's green-bars read, whatever it measures on his terminal,
is not this conjunction; loosening the definition post-hoc would be
tuning on the outcome, so it stays closed unless a future post pins a
sharper observable. His bearish anatomy remains covered by the piece
that DID pass: #79 whale-distribution (+mLHLL), still queued behind R10.

## 26 · #111 below-IPO sourcing (run 2026-07-19) — PASSED with a loud survivorship caveat; IPO↓ tag ships

`homily_ipo_backtest.py` + `ipo_ref.json` (PRD §5m — his Apr-2025
below-IPO value thread; OSCR from that list became his 2026 winner).
Monthly grid, max history, 39 hand-collected split-adjusted refs, first
post-listing year skipped, price condition alone (no point-in-time
fundamentals — recorded).

| pool | 6m below/base | 12m below/base | n below |
|---|---:|---:|---:|
| A-side | +36.7% / +24.7% | +104.2% (81% win) / +65.0% | 274 |
| B-side (control) | +15.6% / +12.1% | +41.9% (59% win) / +31.7% | 390 |
| combined | +24.3% / +16.5% | +68.6% / +43.2% | 664 |

**VERDICT (pre-committed): PASS — beats baseline at both horizons
combined AND on the control side alone.** The win rates say it is broad,
not one lucky name (81%/59% at 12m). **The caveat that must ride every
use: survivorship is concentrated exactly here.** The universe contains
only names still listed in 2026; "buy quality names under their IPO
price" is precisely the strategy whose losers (delisted wrecks) vanish
from such a universe. The wrecks we DO hold (PTON, BYND, LCID) are in
the B-side and it still passed — but a delisted-inclusive universe
(backlog #10's standing wish) would cut these numbers materially.
Sourcing-axis semantics only: the `IPO↓` tag marks a discovery row as
"the market prices this below its first sale" — context for the owner's
judgment next to `F:n/3`, never an auto-add, never a buy signal.

## 27 · #103 fan-distribution card (built 2026-07-19) — the fan ships; 48 cells, 31 usable

`homily_fandist_backtest.py` → `fandist.json` → `homily_fandist` →
board cards (validate [65]). Weekly-grid prefix replay, both universes
pooled, keyed by the pre-registered confluence (state · 🐳 · 🎯 · VH)
through ONE shared function — 48 cells, 31 with n≥30 at 60d. Sample of
what the card now says (60d, nearest-rank percentiles):

| confluence | n | p10 | med | p75 |
|---|---:|---:|---:|---:|
| ⭐ ·|·|BREAKOUT | 1,597 | −20.6% | +6.2% | +20.5% |
| 🟢 ·|·|BREAKOUT | 1,361 | −24.6% | +5.6% | +24.6% |
| ⚪ W|T|BREAKDOWN (the WHALE-DIP shape) | 691 | −19.7% | +8.2% | +27.4% |
| 🔵 ·|T|BREAKOUT | 410 | −29.0% | +1.6% | +20.1% |

The design point the numbers make by themselves: every confluence we
print — including the best ones — carries a double-digit-negative p10
at 60d. That p10 sits NEXT TO the median on the card (HOW_TO_READ §7's
no-targets law), which is the whole answer to "tell me the most likely
path": there isn't one, there is a fan, and 1-in-10 of the names that
looked exactly like today's chart were down ~20–30% two months later.
Info-only; gates nothing; no digest change (board cards only, no
byte-pinned board golden existed so nothing was re-pinned — recorded).

## 28 · #67b whale-dip cap — can it be RAISED? (run 2026-07-22) — NULL; the cap is not a return knob

Owner-directed 2026-07-22: #67 Step 4 derived a *tightening* to 1.6%; the
owner declined that direction and asked the opposite — 🐳 WHALE-DIP is the
only entry trigger that beat DCA, so is the cap mis-set on the LOW side?
`homily_whalecap_backtest.py`, rule frozen in the docstring before the run
(largest-passer wins, deliberately the opposite tie-break to #51's).

**B · 5y, 417 episodes, 3.5%/mo allowance, 200 resamples of within-month
funding order:**

| cap | MOIC p50 | p5 | p95 | MaxDD p50 | funded | skipped |
|---|---|---|---|---|---|---|
| 1.0% | 1.052 | **1.026** | 1.083 | −5.3% | **134** | 283 |
| 1.6% | 1.053 | 1.017 | 1.089 | −6.0% | 91 | 326 |
| **2.0% (incumbent)** | 1.054 | **0.994** | 1.113 | −4.4% | **46** | 371 |
| 2.5% | 1.054 | 0.994 | 1.113 | −5.5% | 46 | 371 |
| 3.0% | 1.054 | 0.994 | 1.113 | −6.6% | 46 | 371 |
| 4.0% | — | — | — | — | **0** | infeasible |

**RULE: NULL.** No cap above 2.0% clears the clauses; the cap STAYS 2%.

**Read the identical rows — they are the finding.** 2.0 / 2.5 / 3.0% post
the SAME MOIC, p5, p95, funded and skipped counts. With a 3.5%/mo
allowance, every cap in ~[1.75%, 3.5%] funds exactly ONE leg per month, so
the cap changes only the SIZE of an identical set of bets. 4.0% exceeds the
monthly allowance outright and funds nothing. Within that band the knob
does not select differently — it just levers.

**A THIRD design flaw, recorded rather than buried** (v1 ignored the
budget; v2 was confounded by funding order; this is v3). MOIC is a RATIO —
scale-invariant — so a pure size increase cannot move it, and clause (a)
was therefore *unsatisfiable by construction* for any c in the one-leg band.
The NULL is structurally guaranteed there, not empirically earned, and must
not be quoted as "we measured that raising the cap doesn't pay." The honest
statement is narrower: **within the budget-feasible range the cap has no
measurable effect on return per dollar committed, and raising it scales
drawdown while leaving the return multiple unchanged** (MaxDD −4.4% → −5.5%
→ −6.6% across 2.0/2.5/3.0% on identical legs). A study that wanted to price
the *leverage* choice would have to measure absolute book contribution, not
MOIC, and would then be answering a risk-appetite question rather than an
empirical one.

**What the table does support, against the direction it was commissioned
in.** Finer caps deploy the allowance more completely (134 legs at 1.0% vs
46 at 2.0%) at a statistically indistinguishable median (1.052 vs 1.054,
heavily overlapping bands) and with a materially tighter downside:
**p5 1.026 at 1.0% vs 0.994 at 2.0%** — the fine-grained sleeve's bad case
is still profitable, the coarse one's is not. That is the diversification
benefit, and it points back toward #67 Step 4's 1.6%, i.e. the tightening
the owner declined. NOT shipped: the owner ruled on that direction and this
run is not a mandate to overturn it — it returns to them as a fresh
decision. Caveat on the allowance: 3.5%/mo is BUY_BUDGET_USD 1550 over the
~US$44k book of 2026-07-22, and whale-dips actually COMPETE with ⭐ adds for
that budget, so the true whale-dip allowance is smaller and every constraint
above is looser than reality.

**Nothing shipped from this study.** PLAYBOOK §3.6b keeps ≤2%.

## 29 · #125 buy-day eligibility — the ⭐ gate subtracts return (run 2026-07-25) — PASSED, promoted same day (owner-directed)

Trigger: NBIS printed ⭐ ACCUMULATE · CONVICTION 79 into BOTH of its crash
sessions (−13.9% on 07-16, −15.0% on 07-24); the owner bought off the
07-22 print and asked whether "buy day = buy ACCUMULATE" is right at all.

**Method** (`homily_holdadds_backtest.py`, rule frozen in the docstring
before the run): every log-screened ticker, full-history daily bars,
per-day truncation to the live trailing-5y window, walked forward through
the REAL `danny_signal()` + `conviction()` — 105k signals over 3 years.
Replay fidelity was proven first: 99.5% state match (1602/1610) against
the 12 live logged days; the 8 misses are HK/SG/LSE timezone closes, every
US row exact.

**Finding 1 — the tier picks names, and it works.** Excess over the
same-day universe mean, date-clustered t-stats: CONVICTION tier +3.28%
at 20d [t 14.7], +9.73% at 60d [t 17.9], monotone in the raw score
(80-89 bucket +14.6% at 60d; sub-20 buckets negative). Positive every
year 2024–2026; 2023 flat-negative.

**Finding 2 — the ⭐ at-support day is the WORSE entry on those names.**
Within CONVICTION tier, same names, only the state differs:

| entry day | n | 20d excess | 60d excess |
|---|---|---|---|
| 🟢 HOLD | 6,037 | **+4.79** [t 12.1] | **+15.54** [t 15.8] |
| ⭐ ACCUMULATE | 8,993 | +2.07 [t 8.5] | +5.63 [t 10.2] |

ACC − HOLD is negative in all 12 tier×horizon cells. Mechanism: the states
sort on prior momentum (HOLD names +11.8% prior-20d, ⭐ +5.4%, ⚪ −5.3%)
and forward returns FOLLOWED prior momentum in this universe — waiting
for the fade to the (rolling, re-anchoring) chip shelf is mean-reversion
timing that momentum beat. Also answers the crash question honestly: ⭐ is
UNDER-represented before >8% single-day drops (0.63× base rate; 🟢 is the
crash-heavy state at 1.81×) — NBIS twice in nine days was bad luck, not
the pattern.

**The gate — live buy-day mechanics** (37 monthly buy days 2023-08..
2026-07, $1k/mo star leg, top-3 by RS12, never sells, valued 2026-07-24):

| arm | per $1 | win A (23-08..25-07) | win B (25-08..26-07) | MaxDD |
|---|---|---|---|---|
| OLD — ⭐ any tier | 1.944 | 2.322 | 1.156 | −28.9% |
| **NEW — CONVICTION ⭐\|🟢** | **2.266** | **2.758** | **1.243** | −36.4% |
| SPY DCA | 1.308 | 1.419 | 1.079 | −11.5% |
| QQQ DCA | 1.395 | 1.539 | 1.095 | −14.2% |

NEW > OLD on both windows → **PASS**; promoted same day, owner-directed
(promotions.json `hold-adds`; R10: spends 2027-Q2's slot, next free
2027-Q3; demotion = `hold_adds_check` rolling-6m on the live ledger,
executed every month-start, FAIL restores ⭐-only mechanically).

**Caveats frozen with the gate.** (1) Universe as of 2026-07-11 replayed
BACKWARDS — every name survived to be picked, so absolute returns and the
margin over SPY/QQQ are inflated and must not be quoted as "the routine
beats the index 2×"; §16b's 10y honest control (engine 2.69 vs QQQ 2.86)
remains the standing answer to "do we beat the market". The OLD-vs-NEW
spread is within-universe, within-day, and is the finding. (2) NEW's
mid-path drawdowns are deeper — more end value, scarier months, accepted.
(3) 2023 is the weak year for the tier edge; the 3y average leans on
2024–26. (4) No dividends anywhere (raw closes), consistent across arms.

## 30 · #50 staged-add tranches (run 2026-07-25) — NULL on all three prongs; the dip instinct is insurance, not alpha

Trigger: the owner's challenge, verbatim — *"but doesnt danny aggressively
scale in when the price dips, seems counterintuitive to buy when the price
hasnt retraced. But i will respect the data."* PRD §8.3 row 50 had
pre-registered the shape (avg-cost + MOIC vs single-add and DCA, both
universes); the rest of the rule was frozen in
`homily_tranche_backtest.py`'s docstring before the first run — deadline
6m primary, 3m/12m sensitivity explicitly non-promotable (the #86 clause).

Arms, $1/name/month, identical cash on identical dates so only the SHAPE
differs: **SINGLE** deploys at the month's first close · **STAGED** parks
it and deploys ⅓ at the point-in-time chip shelf, ⅓ at −7%, ⅓ at −14%,
unfilled tranches forced at market on the 6-month anniversary, waiting
cash earning 0% · **DCA** the same dollars into SPY.

| universe | MOIC vs SINGLE | avg cost vs SINGLE | MOIC vs DCA |
|---|---|---|---|
| A momentum/quality (36) | **0/9 windows** | **1/9** | 9/9 |
| B hype-2021 control (29) | 4/7 | 4/7 | **1/7** |

**Pre-committed rule: NULL — all three prongs fail**, each needing BOTH
universes: (a) MOIC-vs-SINGLE dies on A (0/9), (b) avg-cost-vs-SINGLE dies
on A (1/9), (c) MOIC-vs-DCA dies on B (1/7). The sensitivity grid changes
nothing (3m: A 0/9, B 4/9 · 12m: A 0/9, B 3/9) and by pre-commitment
could not have rescued it anyway.

**The split IS the finding, and it is the honest answer to the owner.**
Staging wins only where the name keeps falling. On universe A — the good
names, the ones the buy routine actually points at — waiting for the dip
lost every single window and paid a **higher** average cost in 8 of 9:
quality names grind upward, so the discount you wait for usually arrives
above today's price. On universe B it wins on both SINGLE metrics — and
still loses to just buying SPY in 6 of 7 windows, because a basket
carrying MOIC 0.63–1.07 is not a thing to optimise the entry into. There
is no window in which staging is the right answer: where it helps you
picked wrong, and where you picked wrong the index beat you anyway. It is
insurance against bad selection, not a source of return — and #125 just
established that the CONVICTION tier is the part of this engine that
picks well.

**Recorded caveats.** Universe B's early windows are thin (n=3 in
2016-2021 and in the 2016-2026 10y — most B names listed 2019-2021), so
those two rows carry little weight; the B verdict rests on the four
2018→2026 windows where n=8–22. Cash earns 0% while parked, which is
realistic for this book but flatters SINGLE in a high-rate window. The
shelf is recomputed point-in-time per buy day from the frozen
`build_profile`, i.e. the same re-anchoring shelf §29 identified — a
tranche waiting on a rising shelf fills sooner than the −7%/−14% legs.

**Nothing shipped. #50 closes.** Independently of the numbers it could not
have shipped today: D-66 §(c) made tranche automation conditional on the
thesis-break veto ("the machinery that sizes up into weakness refuses to
run on names whose business broke"), and that veto is **dead** — #66's
wreck-separation gate FAILED (§14). Averaging down into a genuine wreck
had no guard, which is precisely the failure mode universe B is made of.
The owner's instinct is not dismissed: the one dip trigger that DID beat
DCA is 🐳 WHALE-DIP (§12 row 4, +10.9% vs +9.5% fwd-60d), which stays
live at its ≤2% cap, and the 🐻 protocol remains the real dry-powder path.

## 31 · #125 HONEST-WINDOW re-test (run 2026-07-26) — the verdict survives, and #125's edge does NOT replicate

Owner, 2026-07-26: *"the 2.69x study is already old, that's just buying
stars during buy day."* Both halves correct — §16b tested the pre-#125
selection, and #125's own gate (§29) replayed the 2026-07-11 universe
BACKWARDS, so every name in it survived to be picked. Neither answers
*"what do I get if I follow the NEW buy day for ten years?"*
`homily_holdadds_honest.py` answers it on the repo's own honest control.

Measured: the buy-day routine ALONE — $1,000/month, 100% to stocks
(SRS_COVERS_INDEX=true), equal split across top-3 by RS12, **never sold**.
No §5.2 exit, no §4 bear protocol. That is deliberately not §16b's
strategy; §16b included the exits, which are the engine's best-measured
arm. Never quote the two interchangeably.

| universe | window | arm | MOIC | MaxDD | vs QQQ |
|---|---|---|---|---|---|
| **B honest** | 5y | OLD ⭐-only | **1.74** | −40.7% | beats (1.73) |
| **B honest** | 5y | **NEW #125** | **1.51** | −41.8% | **loses** |
| **B honest** | 10y | OLD ⭐-only | 2.52 | −79.2% | **loses** |
| **B honest** | 10y | **NEW #125** | **2.50** | −79.1% | **loses** |
| B honest | 5y/10y | DCA SPY | 1.50 / 2.08 | | |
| B honest | 5y/10y | **DCA QQQ ← the bar** | **1.73 / 2.86** | −34% | |
| A hindsight | 10y | OLD / NEW | 9.44 / 9.63 | −60/−63% | both "beat" |

**Finding 1 — PRD §5i survives, on the current rule.** On the honest
universe the buy-day routine returns **2.50 over ten years against QQQ's
2.86, at −79% drawdown versus −34%.** Slightly WORSE than §16b's 2.69,
which is the expected direction: §16b's engine carried the §5.2 exit and
this arm carries none. The "does not reliably beat QQQ, 2–3× the index
drawdown" verdict is re-confirmed against the rule that is live today, not
inherited from the old one.

**Finding 2 — #125's advantage does not replicate out of survivorship.**
§29 had NEW beating OLD decisively (2.266 vs 1.944 per $, both windows).
Here NEW **loses** to OLD at 5y (1.51 vs 1.74) and ties at 10y (2.50 vs
2.52). The obvious excuse — "CONVICTION is too strict on a 29-name
universe" — was checked and **fails**: both arms see a median of 4
eligible names per month on B (zero-candidate months: OLD 15/120, NEW
20/120). NEW is not starved on B; it selects differently and worse. On the
hindsight universe A the tier filter is genuinely more selective (median 4
candidates vs OLD's 13) and there it wins — which is exactly the pattern a
survivorship artifact produces: a "quality" filter looks brilliant when
every name in the pool was chosen for having survived.

**Status of #125 — unchanged by this file, and that is deliberate.** #125
shipped on a pre-registered gate it passed; this is a different universe
and different windows, run after the fact. Post-hoc tests do not reverse
promotions in this repo — the registry's `hold_adds_check` runs monthly on
LIVE ledger rows and is the only mechanism allowed to demote it. What this
result DOES do is strip #125 of its claimed evidence: it should now be
read as **unproven, on probation**, not as a validated improvement. The
owner has been told in these words. If the live check FAILs, the ⭐-only
line returns mechanically.

**Caveats.** Universe B inherits homily_strategy_backtest's residual
survivorship — fully delisted names cannot be fetched key-free, so B's
worst outcomes are missing and every B number above is still flattering.
Most B names listed 2019–2021, so the 10y window buys SPY early (§3.5
fallback) and concentrates into the 2021 cohort later; that is honest
behaviour, not a bug, but the 10y row is not ten years of stock-picking.
No dividends anywhere. Neither arm models the exits.

## 32 · #126 — §4 + §5.2 together (run 2026-07-26) — ⚠ **PARTLY RETRACTED SAME DAY, see §33**: this section measured the UNGATED §5.2, which fires ~6.7× more often than the live rule; with the real F-gate the live combination is byte-identical to §4 alone in grinders and there is NO destructive interaction. Read §33 first.

D-63 kept both disciplines on the reasoning *"§4 = insurance; §5.2 =
trash-taker. Different jobs, both kept"* (§3). `run_mode`'s modes are an
elif chain, so that pairing was **never measured**. `homily_discipline_backtest.py`
measures it, selection held at the committed `_screen` so this is purely a
discipline question. Regression-locked: with the per-name leg off it
reproduces the frozen `run_mode("faithful")` to **drift 0.00e+00** on every
window, else the run aborts.

**Grinding bears · 33y · dot-com + 2008 + 2022 (SURVIVOR-BIASED, inherited
from D-63 Step 2 — the bias flatters hold-through):**

| arm | MOIC | CAGR | MaxDD |
|---|---:|---:|---:|
| neither (hold-through) | **74.67** | 21.3% | −76% |
| §4 only (mode d) | 49.14 | 20.3% | **−29%** |
| §5.2 only (mode f) | 47.39 | 19.4% | −79% |
| **§4 + §5.2 ← THE LIVE SYSTEM** | **39.79** | 19.3% | −37% |

**Honest control · universe B · 10y (V-bear only):**

| arm | MOIC | MaxDD |
|---|---:|---:|
| §5.2 only | **3.19** | −71% |
| neither | 2.51 | −74% |
| **§4 + §5.2 ← LIVE** | **1.98** | −48% |
| §4 only | 1.69 | −51% |

**THE FINDING, and it holds in BOTH bear types: the live combination is
worse than its own better half.** In grinders it returns 39.79 against
§4-alone's 49.14 — **19% of final wealth surrendered** — while drawdown
gets *worse*, −37% vs −29%. In the V-bear window it returns 1.98 against
§5.2-alone's 3.19, **38% surrendered**, for 3 points of drawdown. There is
no window in this repo where running both beats running the better one.

Mechanism: §4 liquidates the satellites at 🐻 onset, so §5.2 has nothing
left to identify as trash; then thirds re-entry rebuys the same names,
which §5.2 proceeds to half-sell again three months later. The exit is
paid for twice and delivers once.

**PRE-COMMITTED VERDICT — (b) FAILS decisively; (a) is disclosed twice.**
(b) trash-taker pays: **FAIL**, 39.79 < 49.14. (a) insurance survives: the
prose criterion ("no more than 5 points of protection given up") **FAILS**
— 8 points given up; the criterion as first *coded* compared signed
drawdowns the wrong way and printed PASS. That sign bug was caught while
reading the first run's output, i.e. the fix was made with numbers
visible — a genuine deviation from clean pre-registration, recorded here
rather than buried, with both readings published so no one need trust the
note. The verdict does not turn on it: (b) fails under any reading, and
(b) is the actionable prong.

Verdict per the frozen decision tree: **§5.2 costs wealth inside §4
without adding safety → propose a bear-aware §5.2** (skip the per-name leg
while the regime is 🐻, since §4 has already de-risked). NOTHING SHIPS FROM
THIS FILE — Part III rule 5. Any §4/§5.2 change is a survival/exit
recalibration (R10 unthrottled lane) needing its own pre-registered gate,
registry entry and demotion checker.

**Caveats.** GRIND_UNIV is survivor-biased by construction (D-63's own
warning, inherited): names that died in 2000–02 are unfetchable, which
flatters every never-sell arm and therefore makes the case against the
combination *conservative*, not overstated. Universe B carries the same
residual survivorship. Raw closes throughout — and note §31's measurement
that ignoring dividends understates DCA QQQ by ~7% and DCA SPY by ~17%
over 10y, so every benchmark bar in this repo is easier than reality.
Mode (f) still runs without its F:0–1 gate here (D-63's "aggressive upper
bound"), so §5.2's standalone 3.19 is an overstatement, which makes the
combination's shortfall against it a *lower* bound.

## 33 · #130 §5.2 WITH its F-gate (run 2026-07-26) — the arm was never tested as it actually runs, and §32 must be RETRACTED

D-63 (§3) concluded *"the per-name §5.2 exit (f) is the only mode that
ADDED return on the honest control (+3.4 pts/yr over hold at 10y)"*, with
its own footnote: *"(Caveat: (f) was tested without its F-gate — an
aggressive upper bound.)"* Every later use took the headline: §16b's league
table, #51's 12→8wk promotion, and §32 (#126) this same day. The live rule
(`homily_positions.trim_flags`) needs ⚪ 8+ weeks **AND** F:0–1; on the live
signals log that second condition blocks **85%** of ⚪ rows.

`homily_fgate_backtest.py` rebuilds F point-in-time from EDGAR (`filed` <=
the month, never today's cache) and scores it with the LIVE
`homily_fund.checks_from` (R6). F reconstructable for 29/29 and 10/10 names.

| honest B · 10y | MOIC | MaxDD | sells | blocked |
|---|---:|---:|---:|---:|
| hold | 2.51 | −74% | 0 | — |
| ungated (what D-63 published) | **3.19** | −71% | 214 | 0 |
| **gated (the live rule)** | **2.77** | −72% | 58 | 351 |
| DCA QQQ ← the bar | **2.86** | −34% | | |

**Pre-committed verdict: (a) — §5.2 still adds.** 2.77 > hold's 2.51, so
D-63's direction survives. Two corrections ride with it: the magnitude is
roughly HALVED (+0.26 MOIC vs the published +0.68), and **the gated arm
does NOT beat QQQ** (2.77 vs 2.86) although the ungated one did. Any
session quoting "§5.2 is the only arm that beats the index" is quoting the
ungated number — it is wrong. (5y: hold 1.75 · ungated 1.74 · gated 1.78 ·
QQQ 1.73 — gated edges the bar there, on one window.)

**The grinder result is the sharp one.** 33y, survivor-biased:

| arm | MOIC | MaxDD | sells |
|---|---:|---:|---:|
| hold | 74.67 | −76% | 0 |
| ungated | 47.39 | −79% | 259 |
| **gated** | **76.61** | −76% | **1** |

The live rule fires **once in thirty-three years** (563 blocked). It is
near-inert on quality names and slightly BETTER than never selling — which
is the rule working as designed: it sells broken businesses, and a
survivor universe contains none. §5.2 does not wreck grinders. The ungated
proxy did.

### RETRACTION of §32 (#126), written the same day it shipped

§32 measured "the live combination" with the UNGATED §5.2. Re-run with the
real gate:

| | §4 only | §4+§5.2 UNGATED (§32) | §4+§5.2 **GATED = live** | §5.2 only gated |
|---|---:|---:|---:|---:|
| grinders 33y | 49.14 / −29% | 39.79 / −37% | **49.14 / −29%** | 76.61 / −76% |
| honest 10y | 1.69 / −51% | 1.98 / −48% | **1.93 / −50%** | 2.77 / −72% |

**In grinders the real live combination is byte-identical to §4 alone
(49.14, −29%, ZERO §5.2 sells).** §32's headline — "19% of wealth
surrendered and a WORSE drawdown, −37% vs −29%" — is an artefact of a rule
firing 6.7× too often. **There is no destructive interaction.** §32's
"the two disciplines cannibalise each other" framing is WITHDRAWN, and the
"bear-aware §5.2" next step it proposed was independently found to be a
no-op (the bear branch already `continue`s before the per-name leg).

What survives of §32: on the honest universe the combination still returns
less than §5.2 alone (1.93 vs 2.77). That is **§4's insurance premium** —
30% of terminal wealth for −72%→−50% drawdown — the same priced trade-off
D-63 already recorded, not a new defect. In grinders §4 costs 76.61→49.14
for −76%→−29%.

**Net effect on this session's conclusions.** "The alpha is in the exits"
is substantially weakened: the gated §5.2 is a mild, rarely-firing positive
that loses to QQQ, and §4 is a deliberate insurance cost decided in 2026-07.
No honest configuration of this engine beats QQQ at 10y — §5i and §31 stand.

**Also on the record, not fixed:** `trim_flags` tests the F NUMERATOR, so
**F:1/1 fires while F:2/2 does not**, both being 100% pass rates (24 live
rows carry F:1/1). This study reproduces the live behaviour faithfully
rather than quietly improving it; whether that test should be a ratio is
its own item. **NOTHING SHIPPED** — Part III rule 5; the §3/§16b/#51 wording
corrections are proposed to the owner, not executed here.

## 34 · #131 dual volatility-hole bottom marker (run 2026-08-13) — NULL; the dual shape is rare and reads WEAKER than the single hole

Claim under test (PRD §5n, Danny's INTC post Jul 1 2026): "dual
volatility holes" — two holes stacked at one base — marked INTC's major
long-term bottom; the dual shape should therefore mark better bottoms
than a lone hole. Rule frozen in `homily_dualvh_backtest.py`'s docstring
before the first run: live `find_hole` point-in-time (R6), a distinct
second cluster (cluster-end jump > MAX_GAP) arming ≤ 40 bars after a
still-unresolved first = DUAL; headline scope = bottoming-process
(trend DOWN) BREAKOUT resolutions; fwd 60/120d vs the single-hole 🔵
baseline; 5y daily; universes A + B + ALL; verdict pre-registered
(n ≥ 20 AND dual ≥ single on BOTH horizons).

ALL (58 names), bottoming BREAKOUT:

| arm | n | fwd60 | win | fwd120 | win |
|---|---|---|---|---|---|
| single 🔵 breakout | 618 | +6.2% | 54% | +20.6% | 60% |
| **DUAL 🔵 breakout** | **18** | **+1.7%** | **39%** | **+13.1%** | **59%** |

All three prongs FAIL: n = 18 < 20, and the dual arm loses on both
horizons — in universe A (the better names) dual is far weaker (+3.1%
vs +10.3% fwd60). **NULL — item CLOSED.** The honest reading is the
inverse of the claim on our approximation: a second hole forming before
the first resolves marks a choppier, weaker base, not a stronger one.

Caveats, both directions, recorded: (a) n = 18 is underpowered — this is
"no evidence + point estimate against", not "proven worse"; (b) our
hole detector is an approximation of his proprietary construction, and
his INTC read was MONTHLY — the monthly-TF half of the claim already ran
NULL separately (#77, §7); (c) context rows (dual topping breakouts
+9.9%/n=28, dual bottoming breakdowns +19.9% fwd120/n=24) are small,
unregistered cuts — not evidence, not to be quoted as findings. What
stands: the single-hole 🔵 event edge (homily_vol_backtest baseline) is
untouched; `find_hole`'s one-cluster design loses nothing measurable.
**NOTHING SHIPPED** — no engine edit, no digest surface; the would-be
`×2` mark on 🔵 dies with the item.

## 35 · #132 buy-signal density as a selection challenger (run 2026-08-13) — NULL; rs12-top3 stands, strength beats dip-affinity a FIFTH time

Claim under test (PRD §5n, Danny's HOOD post Jul 16 2026): conviction
that expresses as REPEATED buy signals on one name over months should
identify the better name — so a trailing signal COUNT should rank names
at least as well as the incumbent rs12. Rule frozen in
`homily_sigdensity_backtest.py`'s docstring before the first run:
density = count of weeks (of the trailing 13) whose week-first
`danny_signal` state ∈ {ACCUMULATE, BOTTOMING}, live engine on truncated
bars (R6); dens-top3 (tie-break rs12) raced in the UNCHANGED #24 harness
(same cache, same accounting, equal-all regression drift < 1e-9 every
window — all printed OK); verdict = MOIC ≥ rs12-top3 − 0.01 on ALL THREE
universe-B read windows.

Universe B (hype-2021 control), read windows — the verdict table:

| window | dens-top3 | rs12-top3 | read |
|---|---|---|---|
| 2020→2025 | 1.76 | 1.89 | FAIL |
| 2021→2026 | 1.73 | 1.82 | FAIL |
| 2016→2026 | 2.74 | 2.84 | FAIL |

0 of 3. **NULL — item CLOSED; rs12-top3 stands.** Universe A (hindsight
upper bound, never the verdict) agrees and is starker: 10y dens 6.22 vs
rs12 10.24.

Mechanism, and why this null was predictable in hindsight: buy-class
states fire at support (⭐) or on bottoming breakouts (🔵), so a high
13-week count marks a name that keeps COMING BACK to support — a weaker
tape — while rs12 marks strength. This is the FIFTH measurement in which
some form of dip-affinity loses to strength (staged adds #50/§30,
war-chest #86, at-support ⭐-day entries §29/§31, whale-cap raise §28's
direction, now density). Danny's repeated-signal campaigns are a
POSITION-SIZING behaviour on names he already picked; as a PICKING rule
the pattern selects laggards.

Unregistered observation, recorded but NOT evidence (wrong side of the
gate, and mostly in the hindsight universe): dens-top3 rode shallower
MaxDD than rs12-top3 in every universe-A window (e.g. −43% vs −57% at
10y) — the at-support tilt buys less-extended names. If a drawdown-repair
item (#121) ever wants this, it enters as its own pre-registered study;
do not quote this paragraph as support. **NOTHING SHIPPED** — no R10
slot, no engine edit, goldens untouched.

## 36 · #133 bear-regime census (run 2026-08-13) — owner-requested audit; 4 findings, 1 live defect

Owner: "timing of the bear market is more important than ever … relook
at our bear market indicators and scrutinize them as closely as
possible." Since #130/#126 established that gated §5.2 fires ~once in
33y and the live combination equals §4 alone in grinders, **the regime
banner is effectively the book's entire bear defence** — so it got the
full treatment: code audit of the live path (`homily_regime.py`,
`daily_run` surface, `homily_buyday` reroute, `trim_flags`, `run_mode`)
plus `homily_regimecensus_backtest.py`, a point-in-time census of every
signal the live dual-index rule ever gave (1999-12 → 2026-07, 319
month-ends). Diagnostic only — no gate, nothing shipped.

**FINDING 1 — LIVE DEFECT: the regime engine reads a partial month as a
completed month-end.** Yahoo's 1mo endpoint returns the current month
TWICE (a period row stamped the 1st + a live row stamped at the last
trade: SPY 2026-08-01 770.56 AND 2026-08-13 772.49 in the same
response). `sma10_state`'s single `[:-1]` drops only the live row, so
`last_completed` today = QQQ 718.45 (mid-August) instead of July's
687.99 — the banner's margins read +8.0%/+9.0% when the true completed
reading is +6.0%/+5.9%. Both say BULL today (benign), but at a boundary
this makes the "decisive month-end" signal flip INTRA-month on a crash
or bounce — it is not the tested rule, and it can differ between two
runs on the same day. `homily_regime_backtest.run` carries the same
`[:-1]`. homily_regime.py is FROZEN (engine list) → fix is Phase-C with
its own gate: **#134**, priority 1.

**FINDING 2 — the measured re-entry rule is NOT the playbook's.** D-63's
`run_mode` (source of §4's "−1 pt/yr for −76%→−29%" headline) re-enters
on the first month-end that is not BEAR (EITHER index recovers);
PLAYBOOK §4.7 tells the owner to wait for 🐂 (BOTH above). The census
prices both on every spell — the divergence is material and cuts both
ways: dot-com re-entry SPY −20.3% (EITHER) vs −36.0% (BOTH, 13 months
later); 2008-01 spell: EITHER re-entered May-2008 INTO the bull trap
(+2.2%) and sold again at the 2008-06 re-onset, BOTH skipped the trap
(−33.1%); 2022-02 spell: EITHER whipsawed +3.4%, BOTH re-entered
2023-01 at −6.9%/−15.0%. Summary over 21 spells: EITHER avg round-trip
SPY +1.4% (premium paid 17/21), BOTH −0.7% (15/21). Neither dominates;
what is broken is that the OWNER-facing rule was never the MEASURED
rule. Resolution study = **#135**.

**FINDING 3 — the signal fires ~4× as often as the playbook says.**
PLAYBOOK §4: "a handful of times per decade." Census: **21 BEAR spells
in 26.7y** (≈ one per 15 months), median length 1–2 months; 9 spells in
the 2010s alone; two in the last 18 months (2025-03, 2026-03 — the
latter a +10.5%/+15.7% round-trip whipsaw three months before this bot
went live). 17 of 21 spells re-entered higher (EITHER). The signal
earned its keep in exactly the sequences it exists for — 2000-09
(−43% further fall avoided, re-entry 20–36% cheaper), 2002-04, 2008-06
(−42% avoided, ~28% cheaper), 2022-04 — and charged a 2–16% round-trip
premium roughly every other year in between. COVID (2020-03): fired at
the exact bottom month-end, pure +12.7–18.1% premium, as §4 already
admits. Expectations text correction = **#137**; the D-63 net cost
(−1pt/yr) already includes all whipsaws and stands.

**FINDING 4 — recap, now bear-critical: `trim_flags` F numerator.**
Known since #130: `F:(\d)` reads the count passed, not the ratio, so
F:1/1 (100% of its one applicable check) fires the §5.2 flag while
F:2/2 does not. §4 step 3a sells "everything in ⚪ CAUTION with weak
fundamentals (F:0–1)" FIRST at onset — with 24 live rows carrying
F:1/1, the onset sell list mislabels healthy names as weak. Fix =
**#136** (was "own item" in §33; now it has a bear-path reason to jump
the queue).

Also audited, no defect found: `run_mode`'s thirds re-entry state
machine (prev_bear reset correct, tranches correct); the regime-None
fallback (digest prints "unavailable", buy-day deliberately treats None
as a normal day — single-day exposure, monthly cadence; hardening
folded into **#134**); MIXED near-misses (10 spells ever, only
ladder-relevant); QQQ-veto months (11 — the AND-rule's whipsaw damping,
working as designed). Honesty: census is price-only (no dividends),
Yahoo bars as-served today (no point-in-time index vault — #113), and
the census metric itself was amended mid-session (12m-peak column
ADDED alongside the frozen all-time column after the all-time numbers
proved misleading for 2002–2011 onsets; both printed).

## 37 · #136 F "failing" is now a ratio (run + SHIPPED 2026-08-13) — and the honest §5.2 edge mostly belonged to the bug

The bug (§33 known-issue, §36 finding 4): `trim_flags` tested the F
NUMERATOR (`<= 1`), so F:1/1 — a name passing 100% of its one
measurable check — fired §5.2's sell-half flag while F:2/2 did not, and
§4 step 3a's bear-onset sell list keys off the same notion (24 live
rows carried F:1/1). The fix: **"failing" = fewer than half of the
applicable checks pass** (`homily_positions.f_failing`, the ONE
definition; `timestop_watch`'s pairing, PLAYBOOK §4.3a and §5.2 moved
in the same commit; gate validate [70] pins both sides of 12 tag
boundaries).

Measured effect (`homily_fgate_backtest.py`, now 5 arms; "gated" keeps
the pre-fix rule so §33 stays reproducible):

| honest B | hold | ungated | gated (pre-fix) | **gated_ratio (shipped)** | gated_thin |
|---|---|---|---|---|---|
| 5y MOIC | 1.75 | 1.74 | 1.79 (53 sells) | **1.78 (5)** | 1.74 (28) |
| 10y MOIC | 2.51 | 3.19 | 3.03 (70) | **2.52 (14)** | 2.65 (38) |
| GRIND 33y | 74.67 | 47.39 | 76.61 (1) | **74.67 (0)** | 76.61 (1) |

Selection was pre-registered in the study docstring BEFORE gated_thin
ran (disclosure: gated/gated_ratio HAD been seen first — the sequence
is in the docstring): ship thin (ratio OR m==1 "unverifiable") only if
10y ≥ 2.775 and 5y within 0.02 of ratio. Thin FAILED both prongs
(2.65; 1.74) → **the pure ratio ships**, value loss booked as the price
of semantic correctness.

THE BIGGER FINDING, stated plainly: with the correct gate, §5.2's
measured contribution on the honest 10y is **+0.01 MOIC over hold**
(2.52 vs 2.51) and ZERO firings in 33y of grinders. #130 halved the
published magnitude; #136 shows most of the remainder was carried by
sells the rule's own semantics call mistakes (thin-coverage 2021-era
names — good sells, wrong reason). After §31, §33 and this: **"the
alpha is in the exits" is dead on honest measurements.** §4 remains
priced tail insurance (§38 re-measures its re-entry), §5.2 remains a
semantically coherent trash-taker that almost never fires. A DELIBERATE
"unverifiable fundamentals + broken chart" tell — the pattern the bug
was accidentally trading — is available to future study, but it enters
as its own pre-registered item or not at all. Wording corrections to
§3/§16b/#51 that #130 proposed remain proposed and now carry this
section too.

## 38 · #135 bear re-entry: EITHER-above beats BOTH-above (run 2026-08-13) — PLAYBOOK §4.7 re-worded to the measured rule

§36 finding 2: the "−1 pt/yr" insurance headline was measured on
`run_mode`, which re-arms the thirds on the first month-end that is NOT
BEAR (either index recovering suffices), while PLAYBOOK §4.7 told the
owner to wait for 🐂 (both above). Rule frozen in
`homily_reentry_backtest.py`'s docstring before the run; `run_mode`
gained `reentry=` ("either" default; kwarg-inert at drift 0.00e+00 on
every window, `_assert_regression` OK — the committed tables replay
byte-identically).

| window | hold | faithful EITHER (D-63) | faithful BOTH (§4.7-literal) |
|---|---|---|---|
| B honest 5y | 1.75 / −64% | 1.32 / −42% | 1.34 / −38% |
| B honest 10y | 2.51 / −74% | **1.69 / −51%** | 1.56 / −49% |
| GRIND 33y (context) | 74.67 / −76% | **49.14 / −29%** | 38.87 / −29% |

Pre-registered verdict (BOTH keeps §4.7 only if MOIC ≥ EITHER with
MaxDD not worse on BOTH honest windows): 5y holds, **10y fails** →
**§4.7 is re-worded to the measured either-above rule** (ships via
#137, Part III rule 5 — nothing edited here). The grinders context is
decisive in the same direction: waiting for both indices cost 21% of
33y final wealth for ZERO drawdown benefit. The census's 2008
bull-trap case (§36) is real but rare; on the full record the earlier
re-entry wins. Honesty: the B-honest MOICs sit far below hold because
these windows are dominated by the 2022 V-bear + 2025/2026 whipsaws —
§4's premium windows; its payout window is the grinder column. That
trade-off is priced and signed (D-63); this study only settles WHICH
re-entry the protocol should prescribe.

---

## 39 · #138 leverage drift: the ladder was certified on a policy we do not run (run 2026-08-13) — 1.30× SURVIVES; the 🐻 rule is the load-bearing control

Owner's question: *"how do we fix the issue of leverage growing when
stocks are suffering drawdowns? If we say 30% leverage is safe, then when
drawdown comes our leverage becomes 40% right even without borrowing
more."* The arithmetic half is correct and not in dispute — debt is fixed
in dollars, equity absorbs the whole loss, so constant-debt 1.30× reads
1.41× at −20% and 1.86× at −50%. The drifted ratio is a **symptom**: the
call point was fixed at entry (d\*(1.30) = −69.2%), so the reading moving
does not move the risk.

The audit behind it is the #130 class — a headline certified on something
other than what we run. §15's arms reset position **and** debt to target on
the first session of every month, which in a decline *sells and pays debt
down*. Verified empirically before any arm was written (synthetic −0.3%/day
path: 4/4 month boundaries SELLS+PAYS DOWN), not read off the docstring.
The live account never performs that sale (§5 never-sell, §4 grandfathered
shrink-only) and is not holding QQQ. Two new policy arms and a core-book
series were pre-registered in PRD #138 **before** the run.

**Policies.** `rebal` = §15's monthly reset both ways · `ratchet` =
LEVERAGE.md as actually written (lever UP to cap on a 🐂 month, NEVER sell
to delever, debt→0 at a 🐻 onset, ⚖️ MIXED adds no new margin and drifts) ·
`fixed` = borrow once, never act on the 🐻 signal at all.

**Regression lock (printed every run):** the default policy reproduces
§15's ladder-1.30 read windows exactly — 2.57 / 2.29 / 9.43. §15's "MAX"
row is deliberately not locked; it ends at the run date and drifts by
construction. `run_mode` and `run_emergent` gained a kwarg-inert `nav_out=`
sink (#135's pattern); nothing above reads it.

### QQQ, base financing (`homily_leverage_backtest.py`)

| policy | worst equity/position (boundary 0.25) | 1.30× drifted to | verdict |
|---|---:|---:|---|
| rebal (what §15 measured) | 0.68 | 1.46× | PASS |
| **ratchet (LEVERAGE.md as written)** | **0.66** | **1.52×** | **PASS** |
| fixed (🐻 signal ignored) | 0.25 | 4.05× | **⚠ CALL 2008-11-19** |

### Core book, honest universe B (`homily_levdrift_backtest.py`)

Book NAV from the committed harness; 5y window contains the 2022 bear
(mode `hold` MaxDD −64%, `faithful` −42%).

| policy | worst equity/position | 1.30× drifted to | verdict |
|---|---:|---:|---|
| rebal | 0.73 | 1.37× | PASS |
| **ratchet** | **0.62** | **1.62×** | **PASS** |
| fixed | 0.34 | 2.93× | PASS at 1.30 · **⚠ CALL at 1.50 (2022-07-01**, base AND stress) |

**Readout (a) SURVIVAL — the pre-registered primary: `ratchet`@1.30 passes
everywhere `rebal`@1.30 passes**, on both assets. Per the verdict frozen
before the run, the ladder therefore does **NOT** shrink; LEVERAGE.md keeps
1.30/1.15/1.00 and gains a footnote instead. **This contradicts the
expectation the session started with** (a softer ladder, a §5 shrink, a #91
retraction) — shipped as measured, Part III rule 6.

**Readout (b) DRIFT — the owner's number, measured.** Under the live
policy 1.30× peaks at **1.52× on QQQ and 1.62× on the core book**. The
owner's estimate of "40%" was the right instinct and slightly conservative.
It is also not the risk: at 1.62× the worst equity/position was 0.62, still
2.5× clear of the 0.25 boundary.

**Readout (c) COST OF DELEVERING.** Written sign-safe against the #126
trap (MaxDD are negative; test is `maxdd_ratchet >= maxdd_rebal − 0.05`).
Every cell is within tolerance — and on QQQ `ratchet` both *earns more* and
draws down *less* than `rebal` (MAX 28.70 vs 25.37 at −85% vs −86%), because
the monthly reset sells low and rebuys. On the core book the sign flips
(10y/hold 19.41 vs 21.99): the same reset that hurts on an index helps on a
book whose drawdowns mean-revert harder. Not a rule change either way —
recorded, unregistered.

### What is actually load-bearing

**The 🐻 margin-to-zero rule, not the cap.** The only breaches in the whole
study are in the `fixed` arm — the one that ignores the regime signal:
1.30× margin-called on QQQ in **2008-11-19**, and 1.50× on the core book in
**2022-07-01** at base *and* stress financing. `ratchet` and `fixed` differ
in exactly one behaviour. So the answer to "how do we fix leverage growing
in a drawdown" is: **it is already fixed, by the rule that cuts margin to
zero at a 🐻 onset — provided that signal fires.** That re-prices #134 (the
partial-month regime defect, fixed the same day): a defect in the regime
print is not a reporting bug, it is a fault in the only control that keeps
levered books solvent.

**Honesty box.** (1) The core NAV is **MONTHLY**, so intramonth lows are
invisible and every core cell is FLATTERED — a core cell that breaches has
breached decisively, but a core cell that passes has not been tested
intramonth. Same direction as §15's "intra-day gaps not modeled". (2) The
honest universe reaches back only to 2016 — **the core book was never run
through dot-com or 2008**; the only asset tested across those is QQQ. The
33y GRIND rows are survivor-biased context and were excluded from the
verdict by construction. (3) `fixed` borrows once and never adjusts, so
over long windows its leverage *decays* toward 1.00× as equity compounds —
its mild 33y peaks are that decay, not safety. (4) These are lump-sum NAV
paths; contributions (the owner's actual paydown lever, S$3,000/mo since
2026-07-31) are excluded by construction, so the live book delevers
*faster* than any arm here.

**How long this dependency is acute (scoping note, so a later session does
not read it as permanent).** "The regime print is a solvency control" binds
wherever borrowed dollars sit. On the CORE book that is a dated condition,
not a standing one: the owner redirected S$3,000/mo to margin paydown from
2026-08, which on the owner's own plan reaches MARGIN_ZERO around 2026-11
(plan-derived, not measured here — check `homily_ops` against the live
balance rather than trusting this sentence). After that the core book
carries no margin and §2's ban is self-enforcing; the dependency does not
disappear, it TRANSFERS to the levered swing sleeve, which MARGIN_ZERO is
precisely the gate for (#93/A5). Read §39 as: acute on the core book for
roughly the next quarter, permanent for anything levered thereafter.

**Adjacent gap found while writing this, NOT part of #138 and not fixed
here** (own item, Part III rule 5): the money path treats an unavailable
regime as a normal buy day — `homily_buyday.buyday_block` states it
verbatim, "a regime of None (check unavailable) is treated as a normal buy
day — §3 only reroutes on an explicit 🐻". That fails OPEN: unknown ⇒
deploy as if 🐂. Two things bound it and both are real: #134 already made
the outage visible (retry, `monthly_from_daily` fallback, `regime_last_good`
carry, 🚨 at ≥3 days), and the buy-day deploys only NEW cash — it cannot
add leverage. So the failure mode is *the owner not being told to
de-lever*, not the bot levering up. Cosmetic before §39; a risk-class
question after it, because §39 is what established that the 🐻 print is the
control keeping levered books solvent.

**Not shipped, proposed (#139+):** the core-book ban in LEVERAGE.md §2 is
argued as arithmetic — constant L ≥ 1.25 sits inside the book's −59…−76%
range. That premise is a *constant-L* book, which `ratchet` is not: the 🐻
rule delevers before the boundary, and the honest core book survives 1.30×
because of it. That is a real gap in the ban's reasoning, **but it is not
grounds to lift the ban** on this evidence — monthly resolution, no
dot-com/2008 core path, survivor bias in the only long window. Lifting or
re-wording §2 is a separate item with its own gate (Part III rule 5); this
study only records that §2's stated reason no longer matches the measured
mechanism.

> **Do not cite the paragraph above in support of carrying core margin.**
> The gap is in the ARGUMENT, not the CONCLUSION. §2's ban stands
> unchanged, and it is currently being cured from a LIVE BREACH — the core
> book carried ~S$10.8k of margin at 1.34× on 2026-07-31, the third breach
> of the 1.30 cap, now being paid down at S$3,000/mo. A flaw in why a rule
> was argued is not permission to stop obeying it, and this study measured
> nothing that would make core margin safe: the core cells are monthly
> (blind to intramonth lows), reach back only to 2016, and the only path
> through dot-com and 2008 is QQQ — where the arm that stops de-levering
> was margin-called. Nothing here reduces the case for reaching
> MARGIN_ZERO on schedule.

---

## 40 · #146 does 🐳 have precognition? (run 2026-08-20) — NULL; the tag marks bounces, not news

**Origin.** Owner question after MRNA gapped +84% at the open and closed
**+177%** on 2026-08-19 on cancer-trial news: *did the bot flag whale
accumulation before the news?* Two answers, and the general one needed a
study.

**The MRNA answer is trivial and worth recording anyway.** MRNA is not in
the core universe (152 names scanned in the 4,172-row signals log, zero
MRNA rows) and gambit drops it explicitly — `"drop": "capacity-cut"`, its
$368M mdv126 missing the top-120 cut. A point-in-time replay of the
run-up (32 sessions, `danny_signal` on `bars[:i+1]`) tagged **🐳 on zero
of 32 sessions**, with `absorb_days = 0` every single day. The reason is
not a threshold that barely missed: **volume in the 20 sessions before the
news never once reached the 50-day average** (max 1.00×, against the
detector's 1.30× requirement). There was no footprint to find. And the
move was a **+84% gap** — 48% of the day's gain happened before a share
could trade, so even a perfect same-day detector captures nothing.

**The general study.** `homily_whalegap_backtest.py`, rule frozen in the
docstring before the first run. Claim under test is *not* "does 🐳 pay"
(that is #12/#67, answered) but "does the footprint carry information
about news that has not broken yet." Gaps are the right endpoint because
a gap is the part of a news move nobody can trade.

The comparator is the design decision that matters: **in-dip-but-not-🐳**,
not all-days. 🐳 requires a dip by construction, and dips are elevated-
variance states that raise gap probability on their own; scoring the tag
against all days would credit it for the dip it is standing in.

Primary endpoint, pre-registered, single (no multiplicity to shop):
P(up-gap ≥10% within 21 sessions). Gate: relative lift ≥ +25% **and**
same sign in both universes. Episode-clustered (gap > 5d), 5y, 300-bar
warmup, 65 names.

| | 🐳 | in-dip, no 🐳 | all days (context) | lift |
|---|---|---|---|---|
| **A** (bot list, hindsight-biased) | 9.09% (n=748) | 7.59% (n=1080) | 7.95% | **+19.7%** |
| **B** (hype-2021 control, wrecks) | 9.11% (n=604) | 8.46% (n=721) | 9.37% | **+7.6%** |

**VERDICT: NULL.** Gate condition (1) fails in both universes — neither
clears +25%, and the honest control retains barely a third of the
already-insufficient A figure, the familiar hindsight-decay shape. Note
also that in universe B the 🐳 rate (9.11%) sits *below* the all-days
baseline (9.37%): whatever the tag marks, it is not a richer news
environment than an average day in the control.

**The secondaries explain WHAT the tag actually is, and this is the part
worth keeping.** Direction skew (up-rate − down-rate, 21d):

| gap | A: 🐳 | A: dip-only | B: 🐳 | B: dip-only |
|---|---|---|---|---|
| ≥5% | **+8.7** | +4.4 | **+9.9** | +5.5 |
| ≥10% | +2.5 | **+2.8** | +1.2 | **+2.8** |
| ≥20% | +1.2 | +0.2 | +0.0 | +0.1 |

At **≥5%** gaps 🐳 roughly doubles the dip-only upward skew in both
universes — consistent and real. At **≥10%**, the news-shaped threshold,
the 🐳 skew is *equal or worse* than plain dip-only in both. So the tag's
information lives entirely in small gaps, which is what a bounce off
absorbed supply looks like — **the dip-buy edge #12/#67 already measured
and already ships**. It adds nothing where actual news lives.

**Interpretation.** 🐳 is a dip-absorption detector, exactly as
`homily_whale.py` documents, and it has no pre-news channel. This is the
expected result from a feed that is Yahoo daily OHLCV only: the datasets
that would carry informed positioning (unusual options volume/OI,
dark-pool prints, Form 4) are not wired in, and #109 already established
the deeper reason — Danny's whale scale measures a *stock* quantity
(share of float held by large accounts), unknowable from public bars.
Informed pre-news accumulation, where it exists at all, is not a footprint
in daily OHLCV.

**No re-cut.** The threshold, horizon, comparator and gate were fixed
before the run and stay fixed. The small positive lift in both universes
is recorded as directionally positive and insufficient — not as a
promising signal awaiting a friendlier threshold. **This item does not
touch the existing 🐳 tier**, which was promoted on dip-buy returns and
was not on trial here; §12/§28's whale-dip rules stand unchanged.

**Closed.** Harness kept for #116's archive sweep (a dated pending read:
nothing consumes it live).
