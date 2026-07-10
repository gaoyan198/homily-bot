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

## Bottom line — measured against the owner's bar

**The strategy engine, as an index-beating machine, does not clear the
bar.** On construction-honest evidence it beats the S&P 500 more often
than not, but it does **not** reliably beat QQQ over ≥5y windows — the
fully honest window loses to QQQ slightly, the 2021-straddling windows
lose to both, and every strategy arm carries **2–3× the index drawdown**
(−59…−76% vs −34%). "DCA into QQQ and never look" remains the strongest
simple competitor, exactly as the 2026-07-08 revision concluded — and the
cleaner protocol strengthens that conclusion.

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
