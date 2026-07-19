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

**Ship status: NOTHING changed today** (Part III rule 5). PLAYBOOK
§5.2's "12+ weeks" edit is a registry promotion with a demotion rule,
QUEUED behind R10 with #79/#67-whale-cap/#20 — next free slot 2027-Q2,
order per SPECS §1. The digest keeps printing the current rule until
then.

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
