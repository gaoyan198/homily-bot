# HOW IT WORKS — every signal, its exact math, and which ones actually earn their keep

This is the reference for *why* the bot says what it says. Written for an
adult who is not finance-savvy: every term is defined the first time it's
used, every signal gets its complete formula, and every claim of "this
works" carries the measured number behind it (receipts in
`BACKTEST_RESULTS.md`). Siblings: **PLAYBOOK.md** tells you what to *do*
with the signals; **HOW_TO_READ.md** explains the chart *picture*.

**The one-paragraph version.** Every weekday morning a script downloads
free daily price-and-volume data, runs it through a handful of transparent
formulas, and sends you a Telegram digest. The digest answers exactly one
question per stock: *is now a sensible time to add money to this name, and
if so how much?* It never tells you to sell an individual stock on a chart
signal — that idea was tested twice and loses (the only sells are three
written rules in PLAYBOOK §5 and the market-wide bear protocol in §4).
Everything else in this repo — the ~17 backtest files, the ledger, the
validators — exists to *check the signals against reality* and to stop us
from fooling ourselves.

---

## 0 · Why this repo looks so big now

The signal code is small (about 10 files). The repo grew because of a
house rule: **no signal gets to touch money until it passes a
pre-registered test, and every test result — including the failures — is
kept.** So for almost every signal file there is a backtest file that
judges it, plus infrastructure that referees the live results (the daily
ledger, the flip scorecard, golden-file tests, a promotion registry that
allows only ONE signal-behaviour change per quarter). Roughly:

| Group | What it is | Files |
|---|---|---|
| **Engines** (the actual signals) | the math this document explains | `homily_data/chips/clone/danny/vol/whale/corp/regime/conviction/fund/quality.py` |
| **Referees** (is it true?) | backtests + self-tests + live track record | `homily_*_backtest.py` (~17), `homily_validate.py`, `homily_golden.py`, `homily_ledger.py`, `homily_flipscore.py`, `homily_bootstrap.py`, `homily_promotions.py` |
| **Delivery** (getting it to you) | digest, charts, copilots | `daily_run.py`, `homily_alerts/png/dashboard/chart/weekly/buyday/bearready/flex/clusters/positions/universe.py` |
| **Self-improvement** | daily walk-forward parameter tuning | `homily_refine.py`, `homily_refine_objective.py`, `homily_champion.json` |
| **State** | caches and records the workflow commits back | `holdings/universe/promotions/engine_freeze/…json`, `homily_signals_log.csv` |

---

## 1 · The building blocks (all the math ingredients, defined once)

Everything below is computed from **daily bars**: for each trading day, the
open, high, low, close price and the volume (number of shares traded).
Days are grouped into weekly and monthly closes for the slower signals.

* **SMA(n) — simple moving average.** The plain average of the last *n*
  closes. A smoothed version of price; it lags but doesn't twitch.
* **EMA(n) — exponential moving average.** Like SMA but recent days count
  more. Formula: `k = 2/(n+1)`, then each day
  `ema_today = k × close + (1−k) × ema_yesterday`. An EMA10 leans on
  roughly the last two trading weeks.
* **MACD — momentum gauge.** `line = EMA12 − EMA26` (fast average minus
  slow average: positive means price has been accelerating upward),
  `signal = EMA9 of the line`, `histogram = line − signal` (is that
  acceleration itself still growing?). Histogram above zero = momentum
  building; below = fading.
* **True range / relative volatility.** A day's true range =
  `max(high, yesterday's close) − min(low, yesterday's close)` — how far
  price actually travelled. The bot's volatility measure is the 5-day
  average true range divided by the close (so a $500 stock and a $5 stock
  compare fairly).
* **Dollar volume.** `close × shares traded` — how much money changes
  hands per day. Used as a (rough) stand-in for company size.
* **Total return.** Price return *plus* dividends reinvested. Used for
  all relative-strength numbers; raw prices are kept for chart levels
  (a level must be a price you could actually have traded at).

And the measuring sticks used in the evidence sections:

* **DCA** — dollar-cost averaging: invest a fixed amount every month, no
  signals. This is the "do nothing clever" baseline every idea must beat.
* **Forward return / baseline** — "after the signal fired, what did price
  do over the next N days, versus what it did on *all* days?" If a signal's
  forward return matches the baseline, the signal predicted nothing.
* **MOIC** — money multiple: end value ÷ money paid in. **CAGR** — the
  equivalent smooth %/year. **MaxDD** — worst peak-to-trough fall along
  the way (the "how sick did it make you feel" number).
* **Point-in-time** — every backtested decision uses only data that
  existed on that day (no peeking). **Out-of-sample (OOS)** — judged on a
  period the rule was *not* fitted on.

---

## 2 · The main signal: the five-colour state

Each name gets exactly one state per day, built from five sub-engines.
Here is each sub-engine with its full math, then the decision tree.

### 2.1 Monthly trend — "is the long-term direction up?" (`homily_danny.py`)

```
monthly_up  =  (≥ 12 monthly closes exist)
           AND (latest monthly close > EMA10 of monthly closes)
           AND (that EMA10 is higher than it was last month)
```
Plain English: price is above its ~10-month average AND that average is
itself rising. This is the slowest, most important gate — with it broken,
nothing below can produce a buy state.

### 2.2 Weekly circle — "is the medium-term structure healthy?" (`homily_clone.py`)

Four independent checks on *weekly* closes, one point each:

| # | Check | Formula | Plain meaning |
|---|---|---|---|
| 1 | price above long trend | `close > EMA30(weekly)` | trading above its ~7-month average |
| 2 | ribbon bullish | `EMA10(weekly) > EMA30(weekly)` | the fast average leads the slow one |
| 3 | momentum up *and* positive | `MACD histogram > 0 AND MACD line > 0` | rising momentum, not just "falling more slowly" |
| 4 | long trend rising | `SMA30(weekly) > SMA30 four weeks ago` | the slow average points up |

Score 3–4 = **RED** (healthy — note: red is *bullish* here, the
Chinese-chart convention). Score 2 = **AMBER** (wobbling). Score 0–1 =
**WHITE** (broken). The digest also counts how many consecutive weeks the
current colour has held.

### 2.3 Daily candle — "what is the very short term doing?" (`homily_danny.daily_candle`)

```
RED     if close > EMA10(daily) AND MACD histogram > 0
YELLOW  if close < EMA10(daily) AND MACD histogram < 0
NEUTRAL otherwise
```
Entry-timing garnish only. Danny's own warning, kept on the board:
*"Never simply follow red or yellow candles."*

### 2.4 Chips (筹码分布) — "at what price does everybody else own it?" (`homily_chips.py`)

The idea: people defend the price they paid. If a lot of shares last
changed hands around $100, holders there are quick to buy more at $100
(support); holders trapped above the current price tend to sell as soon as
they break even (resistance). The bot reconstructs "where the holders
live" from volume history:

* Split the whole price range of the data into **120 bins**.
* For each past day, take its volume and spread it **triangularly** across
  the bins its high–low range covers (most weight at the day's midpoint).
* Age the weight: each day old chips lose weight by `0.5^(1/60)` — a
  **60-trading-day half-life**, so a day from 3 months ago counts half,
  6 months ago a quarter. Recent accumulation dominates ("dynamic POC").
* **POC** (point of control) = the single heaviest bin — the crowd's
  dominant cost basis.
* **% in profit** = share of total chip weight sitting at prices at or
  below today's close (holders currently in the green).
* **Peaks** = local maxima of the histogram, strongest first, de-duplicated
  within 2% of each other, keep up to 8. Peaks at or below the close (give
  or take one bin) = **support shelves**; peaks above = **resistance**.
* **Add zone** = `0.98× to 1.03×` the top support shelf. **"At support"
  (🎯)** = close at or below `shelf × 1.03`.

Honesty note: real chip systems decay by turnover against the share float;
float isn't available key-free, so the fixed half-life is the transparent
stand-in. This is an approximation of Danny's proprietary system, not a
copy.

### 2.5 Volatility hole — "has the market gone unusually quiet?" (`homily_vol.py`)

Danny calls this "the most crucial part" of his analysis. Intuition:
before a big move, trading often goes dead quiet — a coiled spring. Math:

```
relvol(day)  = average of last 5 true ranges ÷ close
hole day     = relvol ≤ the minimum relvol of the previous 60 days
                (i.e. a fresh 60-day low in volatility)
zone         = hole days ≤3 days apart cluster together;
               zone upper/lower = that cluster's highest high / lowest low
in force     = until 90 bars after the cluster ends
status       = BREAKOUT  if close > upper
               BREAKDOWN if close < lower
               INSIDE    otherwise
```
The zone is drawn on the chart (violet band). A close **above** it is the
bullish resolution — it powers the 🔵 state. A close **below** it prints
only a ⚠ warning, because the bearish side failed its test (§6).

### 2.6 The decision tree — one state per name (`homily_danny.danny_signal`)

Checked in this order, first match wins:

```
1. monthly trend DOWN or weekly WHITE?
      → 🔵 BOTTOMING  if a volatility hole is in force AND status = BREAKOUT
      → ⚪ CAUTION    otherwise
2. weekly AMBER (monthly still up)?        → 🟡 PULLBACK
3. price at support (close ≤ shelf ×1.03)? → ⭐ ACCUMULATE
4. otherwise                               → 🟢 HOLD
```

| State | Plain meaning | What you do (PLAYBOOK) |
|---|---|---|
| ⭐ ACCUMULATE | long-term up + structure healthy + price sitting on a defended shelf | candidate for the monthly buy (§3) |
| 🟢 HOLD | healthy but price is stretched above its support | nothing — wait for it to come back |
| 🟡 PULLBACK | a dip is forming inside an intact long-term uptrend | watch the shelf; get ready |
| 🔵 BOTTOMING | trend is broken, BUT price just broke *above* a quiet-market zone — the earliest legal reversal hint | small discretionary buy at most |
| ⚪ CAUTION | trend broken | pause adds. **Not a sell** — the only sells are PLAYBOOK §4/§5 |

There is deliberately **no SELL state**: mechanically holding RED and
cutting WHITE was backtested and *trails* simple buy-and-hold.

---

## 3 · The tags that ride on a row

### 🎯 "at support" — price inside the add zone
Math: close ≤ top-support-shelf × 1.03 (the zone itself is shelf × 0.98 to
× 1.03). On a non-⭐ name this is context only. **Measured:** on ⚪ names,
buying the shelf *without* the whale tag did **worse** than waiting — the
level alone carries no edge (see §6).

### 🐳 whale footprint — "someone big is buying this dip" (`homily_whale.py`)
Fires only when there IS a dip: `close ≤ 95% of the highest close of the
last 60 days`. Then it looks for at least **2 of 3** fingerprints big
buyers leave in public data:

1. **Absorption print** — within the last 15 days, at least one day with
   volume ≥ 1.3× its trailing 50-day average, whose low probed within 3%
   of the 20-day floor, yet which closed in the **top half** of its range
   (`(close − low)/(high − low) ≥ 0.5`). Sellers hammered it all day;
   someone took every share and pushed it back up.
2. **Flow divergence** — over the dip window, OBV *or* the
   accumulation/distribution line is at/above its level at the pre-dip
   peak while price is lower. (OBV: running total of volume, added on up
   days, subtracted on down days. A/D: volume credited by where the close
   lands within the day's range.) Money flowed in while price fell.
3. **Shelf stability** — price is sitting on the support shelf
   (within −10%/+3% of it) and the shelf's decayed chip weight (±2% band)
   is **no lower than 10 days ago**. Untouched, decay alone would have
   shrunk it to ~89%; holding steady means fresh volume is replenishing
   the shelf at the same prices — accumulation, not flight.

**⚪ + 🎯 + 🐳 together = WHALE-DIP**, the single permitted CAUTION-state
buy: discretionary, ≤2% of the account. This tier passed its gate (§6).

### ⚠ topping-process breakdown
If a volatility hole formed after a *rally* (`trend_before = UP`, judged
by comparing the close at cluster start vs 20 bars earlier) and price
closes **below** the zone, a warning note is appended. Note only — the
bearish side of the hole is measurably not predictive (§6).

### ⚠ levels suspended — corporate action? (`homily_corp.py`)
A >45% single-day move on abnormal volume inside the chip window is the
signature of an unadjusted stock split or spin-off: every chip level would
be built on prices that never traded. The state still prints; the levels
don't, and the name can't be promoted into the 🐳 tier that day.

---

## 4 · The context numbers on a row (they gate nothing)

| Print | Math | What it's for | Evidence status |
|---|---|---|---|
| `med run 8w` | median length of a completed weekly-RED spell, measured over 1,439 historical spells (p25 2w · p75 23w · p90 42w) | calibrates urgency: a quarter of healthy runs last 23+ weeks, so a fresh ⭐ is usually not urgent-tomorrow | info-only base rate |
| `dip d{n} (med 4d · p90 22d)` | n = trading days the current non-RED-candle pullback has run inside an intact weekly-RED; base rate from 1,594 resolved pullbacks | calibrates patience: the median healthy dip lasts 4 days | info-only. A "dip too old = trend failing" warning was tested and **refuted** — failing trends actually resolve *faster* (median 3d) |
| `% in profit` | chip weight below close ÷ total | >90% = everyone's happy (momentum-friendly but extended); <40% = heavy overhead supply | descriptive only |
| `RS12` | 12-month **total** return of the name minus SPY's (both with dividends reinvested), in points | the selection ranker — see §6 for why this humble number is the star of the show | ranking edge measured; top-3 concentration passed its gate |
| `conv NN` | conviction score 0–100 (§7 has the full point table) | compare names by the **number**; the CONVICTION/STARTER labels measurably separate nothing | ranking real (OOS decile test), tier labels null |
| `Q1/Q2/Q3` | sticky quality tier, 0–7 pts from SEC filings: rev growth ≥10% (+1) and ≥25% (+1) · profitable (+1) · margin improved (+1) · free cash flow > 0 (+1) · dilution <12%/yr (+1) · 3-year RS ≥ SPY (+1). Q1 ≥5 · Q2 3–4 · Q3 ≤2; recomputed quarterly, frozen between | a *business*-quality read that doesn't move with the tape — what you glance at during the next NVDA-2022 | gate **FAILED** (couldn't separate the 2021 wrecks — ZM/DOCU/ROKU scored Q1 on their then-filings). Label only, drives nothing |
| `F:n/3` | EDGAR checks, latest fiscal year vs prior: revenue +10%+ · net income > 0 OR operating cash flow > 0 · share dilution <12%/yr | feeds exactly one rule: PLAYBOOK §5.2 (12+ weeks in ⚪ **and** F:0–1 → sell half) — the "broken business, not just broken chart" test | info-only as a tag; the §5.2 rule it feeds is the system's best-measured arm (§6) |
| `x% of book` / ⚠ cap | position size vs the 10%-per-name cap | so an add can't quietly breach the cap | rule, priced in §12 of BACKTEST_RESULTS |

---

## 5 · The market weather banner 🐂 / ⚖️ / 🐻 (`homily_regime.py`)

The one market-wide timing rule, on purpose very slow (it fires a few
times per decade):

```
At each month end, for BOTH SPY (S&P 500) and QQQ (Nasdaq-100):
   is the completed monthly close above the average of the
   last 10 completed monthly closes (the 10-month SMA)?

both above → 🐂 BULL    both below → 🐻 BEAR    split → ⚖️ MIXED (no action)
```

🐻 triggers the PLAYBOOK §4 protocol: margin to zero, sell the weak
satellites **once**, keep buying the index all the way through the bear,
re-enter stars in thirds when 🐂 returns. The index core never sells.

**Measured honestly (33 years, dot-com + 2008 + 2022):** the protocol
gave up ~**1 point/year** versus never selling anything — and in a
V-shaped bear like 2022 about 7 points/year of that window — in exchange
for cutting the worst drawdown from **−76% to −29%**. So it is **priced
tail insurance**, not a return booster: you pay a premium so the account
(and you, psychologically) survive a 2000–02-style multi-year grinder.
Also measured: "pause adds but don't sell" is the *worst of both worlds*
(kept the −76% drawdown AND lagged in the V-bear) — that's why the banner
never suggests it.

---

## 6 · Which signal is better? — the league table

This is the question the whole referee apparatus exists to answer. First,
understand that the signals do **three different jobs**, and "better" only
makes sense within a job:

* **WHICH stock** — selection: ⭐'s gates, RS12, the conviction score.
* **WHEN to add** — timing: ⭐-at-shelf, 🔵 breakout, 🐳 whale-dip, 🎯.
* **HOW MUCH / survival** — sizing caps, 🐻 insurance, §5.2 exit.

### The league table, ranked by strength of measured evidence

| Rank | Signal | Job | The measured number | Verdict |
|---|---|---|---|---|
| 1 | **PLAYBOOK §5.2 exit** (⚪ 12w + F:0–1 → sell half) | survival | the **only arm that ADDED return** on the wreck-salted control: **+3.4 pts/yr over 10y** vs holding everything | the best thing in the system. It takes out the PTON/ZM class. Zero crash protection though (kept −79% in grinders) — it's a trash-taker, not insurance |
| 2 | **🐻 regime protocol** | survival | −1 pt/yr premium over 33y buys worst-drawdown −76% → **−29%** | honestly-priced insurance. Keep paying it |
| 3 | **RS12 ranking** (buy the top-3 by RS12 among ⭐ names) | which | only pre-registered change that pushed the honest window past QQQ (**1.82 vs 1.78 MOIC**); beat 200 random draws above their p90 in all 3 read windows | gate PASSED; **promoted 2026-07-12 by owner override**, ahead of the live forward-check — the check still publishes at every month-start through Oct 2026, and a FAIL demotes it mechanically (promotions.json) |
| 4 | **🐳 WHALE-DIP** (⚪+🎯+🐳) | when | +10.9% fwd-60d vs +9.5% DCA vs +9.7% plain ⚪ dips (58 names, point-in-time) | the only *entry trigger* that beat DCA. Shipped, but capped ≤2% because outcomes are wild (worst 5% of episodes: **−31.7%** in 60d) |
| 5 | **🔵 VH breakout** | when | +4.4% vs +2.8% baseline fwd-20d; +11.5% vs +8.5% fwd-60d (daily holes only) | real but modest. Earns the 🔵 state and 10 score points, nothing more |
| 6 | **⭐ gate** (monthly up + weekly RED + shelf) | which | as a *timing* trigger it **lost to DCA on every name tested** (average cost −1%…−13% worse). But as a *selector/container*: wrecks lose their ⭐ long before you can build size — the cap study showed the ⭐ gate, not the add-cap, is what contains wrecks (the basis on which #92 later raised the cap to 25%) | the workhorse — but for the *which* job, not the *when* job. Its levels are context for adds, never a reason to sit in cash |
| 7 | **Distribution warning** (#79, inverse-whale) | when (to worry) | tagged rally days +7.8% fwd-60 vs +9.7% baseline; with monthly lower-highs/lows: **−0.3% fwd-120 vs +19.6%** | passed its gate but NOT shipped yet — edge lives in the wreck universe, and the digest surface is its own future gated change |
| — | conv score (the number) | which | OOS decile returns rise monotonically with score on both universes | real as a *ranking*… |
| — | conv tiers (the labels) | how much | CONVICTION ≈ STARTER ≈ fails on every outcome (P(2×), P(5×), P(halve-first)) | …but the 75/60 cutoffs are noise. Read the number, ignore the word |
| — | med-run, dip-counter, % in profit, Q, F | context | base rates / labels | info-only by design or by failed gate |

### The proven-null graveyard (kept so nobody re-invents them)

* **Selling on chart states** (hold 🔴 / cut ⚪): trails buy-and-hold. Twice.
* **VH breakdown as a sell/veto**: breakdowns were followed by *above*-baseline returns.
* **Weekly & monthly volatility holes**: add nothing; Danny's SPY-monthly "perfect record" was just the market's own base rate (5 events in 12 years, at/below unconditional returns).
* **🎯 shelf alone on ⚪**: lost to plain waiting. The footprint (🐳), not the level, carries the edge.
* **Dip-age warning** ("pullback too old = failing"): refuted — failures resolve *faster*.
* **Entry-candle size predicting run length**: failed its rule on one of two universes.
* **Q as a gate/veto**: as-of-filing fundamentals could not separate the 2021 wrecks.
* **Conviction tier labels as sizing**: separate nothing at the cutoffs.

### Head-to-head: the questions you'd actually ask

**"Is ⭐ better than 🔵?"** They fire in opposite worlds, so they never
compete on the same stock on the same day: ⭐ exists only in intact
uptrends, 🔵 only in broken ones. As a pure *timing* trigger, 🔵 is
actually the better-proven of the two (+4.4% vs +2.8% baseline; ⭐'s
timing is measurably *negative*). But ⭐'s real value is the *which* job —
it keeps the monthly budget in healthy, defended names and quietly drops
wrecks before they can grow — and it operates where falling-knife risk is
lowest. So the monthly budget follows ⭐; 🔵 gets at most a small
discretionary punt. If you must rank them: **⭐ for your money, 🔵 for
your watchlist.**

**"Is whale-dip better than ⭐?"** Per trigger, yes: WHALE-DIP is the only
entry in the system that beat plain DCA in its test (+10.9% vs +9.5%
fwd-60d), while waiting for ⭐ prices *lost* to DCA. But WHALE-DIP is
rare, fires in broken trends, and has a violent downside tail (worst 5% of
episodes −31.7%) — which is why it's rationed to ≤2% of the account (the
dispersion math actually derives 1.6%) while ⭐ names may carry 5–10%.
**Better trigger, much smaller allowance.** Both together are still
smaller than the real answer, which is boring: the monthly buy-day
discipline itself.

**"Is 🟢 worse than ⭐?"** 🟢 is not a weaker buy — it's *no buy*. Same
healthy name, wrong price (stretched above its shelf). 🟡 is "the dip you
were waiting for may be forming." Neither is a sell.

**"Red candles are good?!"** Yes — in this system (Chinese chart
convention) red = bullish, yellow = bearish. The board pins a legend
because misreading this inverts every chart. And per Danny himself: never
trade candle colours alone; the hierarchy is monthly trend → weekly circle
→ chip context, with the daily candle last.

**"Q says Q1 but F says 1/3 — who wins?"** Neither gates anything. F
feeds the one written sell-rule (§5.2, with the ⚪-12-week clock); Q is a
glance-value label whose gate failed. If they disagree, believe neither —
read the filings.

**"Danny doesn't DCA — he saves up and buys big on massive discounts.
Should the monthly budget just wait for 🔵/🐳?"** Half-true about Danny,
and the tested answer for us is no. True: Danny holds cash/leverage and
buys aggressively at shelves during dips (his Apr-2026 post: *"next time
whales offer a bigger discount, that's when I'll FOMO in"*; the PLTR
June-2026 add). Two things he does that we deliberately don't copy: his
"big buys" ride **leverage** (out of scope by design), and his discounts
are pullbacks-to-shelf *inside intact uptrends* — which is exactly what ⭐
already is. The hold-cash-for-dips pattern has been measured here three
ways and lost every time: (1) waiting for the ⭐ shelf got a worse average
cost than plain monthly buying on **every** name tested (−1%…−13%) —
quality names grind upward, so the discount you wait for usually arrives
at a higher price; (2) on the momentum basket, **half of all days the ⚪
gate blocked were followed by +15% within 60 days** — the measured cost
of sitting out; (3) 🐳/🔵 events are far too rare and too tail-risky
(worst 5% of whale-dips: −31.7%) to absorb a monthly budget — that's why
the whale-dip cap *derived from its own dispersion* is ~1.6–2%, not 50%.
The playbook already routes money toward dips without the cash drag: the
monthly buy goes to ⭐ names (names AT their shelf — the disciplined
version of "buy the discount"), 🟡+🎯 allows an aggressive add, ⚪+🎯+🐳
takes its ≤2% from the same budget, and the 🐻 protocol builds real dry
powder for the only discounts that are actually massive. A staged-add
variant (park the tranche, deploy at shelf / −7% / −14%) sits in the
backlog as **#50** with a pre-registered test — if it beats single-add
and DCA on average cost, it ships; nothing before that.

---

## 7 · How much to buy — sizing (`homily_conviction.py`)

Separate question from *what* to buy. Five hard gates first — fail any
one and the name gets no 🚀 capital, period:

| Gate | Test | Why |
|---|---|---|
| G1 size | avg 20-day dollar volume < $5B/day | megacaps by traded value can't 5× quickly (NB: dollar volume is a *proxy* for size — honest limitation) |
| G2 trend | monthly UP **and** weekly RED | leaders only, no falling knives |
| G3 leader | RS12 ≥ +20 pts vs SPY (total return, both sides) | relative strength — it must already be beating the market |
| G4 basis | close > POC | the crowd's average holder is in profit and defending |
| G5 data | ≥ 200 daily bars | fresh IPOs are unratable |

Survivors get the 0–100 score:

| Component | Max | Exact points |
|---|---|---|
| trend | 25 | monthly up +10 · weekly RED +10 · RED streak ≥8w +5 |
| relative strength | 25 | RS12 ≥100 → 20, ≥50 → 15, ≥20 → 10 · RS6 ≥10 → +5 |
| structure | 15 | close > POC +5 · % in profit ≥60 +5 · state = ⭐ +5 |
| vol hole | 10 | BREAKOUT ≤30 bars old → 10 · INSIDE → 5 |
| size/room | 15 | dollar volume < $0.5B → 15 · <$1.5B → 12 · <$3B → 8 · <$5B → 4 |
| listing age | 10 | < ~4.5y of data → 10 (young, room to run) · else 5 |

Tiers: **≥75 CONVICTION** up to 5% of the account · **60–74 STARTER** up
to 2% · **<60** watch only. Hard caps regardless: **25% per name**
including what you already hold (raised from 10% by the #92 promotion,
2026-07-12 — owner override, demotion watch armed); whale-dips ≤2%.
Honesty (measured, §6): the score's *ranking* is real, the tier *labels*
are noise — compare names by number. The cap trade-off was priced before
the raise: 10% costs almost nothing in the honest window and buys real
protection in single-name blowups (10y shock test: MOIC 1.89 capped at
10% vs 1.70 at 25% vs 1.49 uncapped when the top name gaps −95%) — the
raise deliberately spends half that insurance for room to add into
winners; a ≥15%-of-book name halving from its post-promotion high
reverts it mechanically.

---

## 8 · Self-checks — why you can trust the numbers on the digest

* **`homily_validate.py`** — 47 self-tests of the math itself (EMA/MACD
  correctness, no look-ahead, chip decay, composite states, data
  integrity). Runs on every workflow run; a red test blocks the digest.
* **Golden files (`homily_golden.py`)** — fixture bars must render the
  exact expected digest, so a code change can't silently alter signals.
* **The ledger (`homily_signals_log.csv`)** — every state the digest ever
  printed, one row per name per day. Live forward results are judged from
  this file only (nothing recomputed after the fact), via the flip
  scorecard (`homily_flipscore.py`).
* **The promotion registry (`homily_promotions.py`)** — a signal-behaviour
  change ships only through a pre-registered gate, max **one per quarter**.
  2026 exception, recorded: Q3 carries both 🐳 (07-06) and rs12-top3
  (07-12, owner override — Q4's slot spent, next slot 2027-Q1); the
  month-start digest block publishes every entry's forward check.
* **The refine loop (`homily_refine.py`)** — retunes the weekly-circle
  parameters daily, walk-forward: a challenger replaces the champion only
  if it wins on data it wasn't fitted to. Its objective is itself under
  review (#21) with a parallel scoring file before any switch.

---

## 9 · The honest bottom line

Measured across every ≥5-year window since 2015 on a
construction-honest universe (i.e. including the 2021 wrecks a growth
investor really held):

* The full strategy **beats the S&P 500 more often than not**.
* It does **not reliably beat the Nasdaq-100** — the fully honest window
  loses to QQQ slightly (1.70 vs 1.78 MOIC), and a bootstrap over that
  window says the strategy beats QQQ-DCA in only ~24% of resampled paths.
* It carries **2–3× the index's drawdown** (−59…−76% vs −34%).
* "**DCA into QQQ and never look**" remains the strongest simple
  competitor. That sentence is kept at the bottom of the evidence file on
  purpose.

What the system is measurably *for*, then: (1) the §5.2 exit that removes
broken businesses (+3.4 pts/yr on the control), (2) the 🐻 insurance that
turns −76% into −29%, (3) the discipline machinery — budgets, caps,
ledger, honesty gates — that keeps a human saving and adding through
noise. The signals tell you *where* and *how much*; they are context for
discretionary adds, not a money machine. Anything claiming more than that
is not supported by this repo's own numbers.

**Has it improved since launch? Yes — but improvements ship one gate at a
time, so the curve is a staircase, not a slope.** Shipped so far: the 🐳
WHALE-DIP tier (2026-Q3's one allowed change), the priced 🐻 protocol, the
measured §5.2 exit, and the honesty/measurement layer itself. Also live:
rs12-top3 concentration — the first change that pushed the honest window
past QQQ (1.82 vs 1.78) — **promoted 2026-07-12 by owner override**,
ahead of its live forward-check; that check publishes at every
month-start through Oct 2026 and demotes it mechanically on a FAIL. In
flight: the mechanical universe (#65, first shadow read ~Oct 2026) and
the refine re-point (#21, first read Aug 2026). Most experiments fail
their gates and are recorded as nulls — that
is the design working, not stagnation: a gate that never fails is a gate
that ships noise. For calibration, the bar this repo holds itself to
(beat QQQ-DCA, ~20%/yr money-weighted over the last decade) is a bar most
professional funds miss after fees; "quant-fund returns" in the famous
sense (Medallion-class) come from leverage, shorting, intraday horizons
and capacity limits that a long-only personal account on free daily data
cannot and should not imitate.

*Not a clone of Homily's or Danny's proprietary formulas (both
undisclosed). Transparent approximation of their documented behaviour;
Danny's leverage deliberately not copied.*
