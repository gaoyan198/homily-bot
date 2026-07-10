# How the algorithm works — and how it decides what to accumulate

This bot is a **Homily-chart / Danny-Cheng-style accumulation screen** for a
personal IBKR equity book. It never tells you to sell an individual stock (that
loses in every backtest here — see the honesty notes below). It only answers one
question, per name, every trading day:

> *Is now a sensible time to ADD to this name, and if so, how much?*

There are two audiences below: the **pro** version (what actually runs), and the
**explain-like-I'm-5** version.

---

## Explain it like I'm a pro

### 1. The data layer (`homily_data.py`)
Key-free daily OHLCV from Yahoo v8, resampled into **weekly** and **monthly**
closes. Pure stdlib, no paid feeds, no `pip install`. Everything downstream is
derived from price and volume only — which is both the honesty constraint (no
private fundamentals driving the call) and the main limitation (dollar-volume is
a *proxy* for market cap).

### 2. Four engines feed one state machine

The daily call is a composite of four independent, transparent engines:

| Engine | File | What it measures |
|---|---|---|
| **Monthly trend** | `homily_danny.py` | `close > EMA10(monthly)` **and** EMA10 rising → the long-term uptrend is intact |
| **Weekly circle** | `homily_clone.py` | the original 4-factor red/white regime engine (EMA ribbon + MACD + slope) → RED = healthy, AMBER = wobbling, WHITE = broken |
| **Chip distribution** | `homily_chips.py` | volume-at-price (筹码分布): where holders' cost basis sits → POC, support/resistance shelves, % of holders in profit |
| **Volatility hole** | `homily_vol.py` | Danny's "most crucial part": a collapse in volatility to a 60-day extreme, printed as a zone → breakout above it = bottoming confirmation |

Plus a **whale-accumulation** footprint detector (`homily_whale.py`) that looks
for big-buyer fingerprints in a dip (absorption prints, OBV/A-D divergence, shelf
stability).

### 3. The chip engine — the heart of "where to accumulate"
Chips (`homily_chips.py`) are a **cost-distribution** model. Each day's volume is
spread triangularly across that day's high–low range, and older days are decayed
with a **60-trading-day half-life**, so recent accumulation dominates — Danny's
"dynamic POC" behaviour. The outputs:

- **POC** (point of control): the single heaviest price bin — the crowd's
  dominant cost basis.
- **Support peaks**: heavy chip shelves *below* price. Holders there are in
  profit and defend their basis → price tends to hold.
- **Resistance peaks**: heavy shelves *above* price. Trapped holders sell into
  rallies → price tends to stall.
- **% in profit**: how much chip weight sits below the current price.

The **add zone** is drawn around the top support shelf (`0.98×` to `1.03×` of the
peak). "At support" = price within 3% above that shelf.

### 4. The state machine — the accumulate/don't decision
`danny_signal()` combines the engines into exactly one state per name. **There is
no SELL state by design.**

| State | Condition | Meaning |
|---|---|---|
| ⭐ **ACCUMULATE** | monthly UP + weekly RED + price at a major chip-support shelf | the add zone — trend intact *and* price sitting on defended cost basis |
| 🟢 **HOLD** | monthly UP + weekly RED, but extended above support | good name, wrong price — wait for a pullback |
| 🟡 **PULLBACK** | weekly AMBER while monthly UP | dip forming — stalk the support zone |
| 🔵 **BOTTOMING** | trend broken, BUT price broke *above* a volatility hole | Danny's early reversal signal — watch for the trend engines to confirm |
| ⚪ **CAUTION** | weekly WHITE or monthly trend down | pause adds — thesis review, **not** a sell call |

So **what gets accumulated** = names in ⭐ ACCUMULATE (trend up + at support), or
🔵 BOTTOMING (early reversal), plus the one narrow whale exception below. **What
does not** = anything in ⚪ CAUTION (trend broken) or 🟢 HOLD (too extended to add
cheaply) — you hold what you own but don't add.

### 5. The one permitted ⚪ exception — WHALE-DIP
Normally ⚪ CAUTION pauses adds. The single exception: a ⚪ shelf dip (🎯) that
*also* shows the 🐳 whale footprint. The backtest (`homily_whale_backtest.py`, 58
names incl. 2021 wrecks, point-in-time) **passed**: ⚪+🎯+🐳 dips returned +10.9%
fwd-60d vs +9.5% DCA and +9.7% for plain ⚪ dips. Crucially, the shelf *alone*
(🎯 without 🐳) **lost** — the footprint carries the edge, not the level. So
WHALE-DIP is a discretionary add, ≤2% of account.

### 6. Sizing — how much to accumulate (`homily_conviction.py`)
Ranking *what* to buy is separate from *how much*. Every name runs **5 hard
gates** — all must pass to earn a 🚀 tier:

- **G1 size** — avg 20-day dollar volume < $5B/day (megacaps by trading value
  can't 5× quickly)
- **G2 trend** — monthly UP and weekly RED (leaders only, no falling knives)
- **G3 leader** — 12-month return beats SPY by ≥ 20 points (relative strength)
- **G4 basis** — price above POC (the crowd's cost basis is defended)
- **G5 data** — ≥ 200 daily bars (too-fresh IPOs are unratable)

Survivors get a transparent **0–100 score** (trend 25 · relative strength 25 ·
structure 15 · vol-hole 10 · size/room 15 · age 10) that sets the sizing tier:

- **≥ 75 CONVICTION** → up to **5%** of account
- **60–74 STARTER** → up to **2%**, prove itself first
- **< 60** → watch only, no capital
- **Hard cap: no single name above 10% of the account**, including what's held.

### 7. Market regime overlay — priced tail insurance (`homily_regime.py`)
A month-end 10-month-SMA rule on **both** SPY and QQQ. Both below = 🐻 **BEAR** →
PLAYBOOK §4: margin to zero, sell weak satellites *once*, keep buying the index
through the whole bear, re-enter stars in thirds when 🐂 returns. The index core
never sells. Decomposed honestly (D-63, 2026-07-10): over 33 years the protocol
gave up **~1 pt/yr** vs never-selling and cut the worst drawdown from **−76% to
−29%**; in a V-shaped bear (2022) it costs ~7 pts/yr of its 5-year window. It is
insurance against −70% grinders (2000–02, 2008) — a priced policy, not a return
enhancer, and the digest banner words it that way.

### 8. Self-improvement + safety
`homily_refine.py` runs a **walk-forward** refine daily: a challenger replaces the
champion parameters only if it wins **out-of-sample**. `homily_validate.py`
self-tests the math (EMA/MACD, no look-ahead, chip decay). The whole thing ships a
Telegram digest via a GitHub Actions cron (09:00 SGT Mon–Fri) — no server.

### The honesty constraints (baked into the digest on purpose)
1. Mechanically holding 🔴 / cutting ⚪ **trails** buy-and-hold → **no sell state.**
2. Waiting for the ⭐ zone got a **worse** average cost than plain monthly DCA on
   every name tested (−1% to −13%) → the levels are *context* for discretionary
   adds, **not** a reason to sit in cash.
3. The volatility hole's bullish side has a real but modest edge; its bearish side
   does **not** → a breakdown is a ⚠ note, never a no-add veto.
4. The whale gate passed, but only 🎯+🐳 together — the shelf alone lost.

**This is not a clone** of Homily's or Danny's proprietary formulas (both
undisclosed). It's a transparent approximation of their publicly documented
behaviour, and it deliberately does **not** copy Danny's leverage.

---

## Explain it like I'm 5

Imagine you collect a few favourite toys, and you only ever want to **buy more**
of the good ones — you never sell them. The tricky part is: *which* toy should
you buy more of today, and *when*?

The bot is like a careful friend who checks every toy each morning and puts it in
one of five buckets:

- ⭐ **"Buy now!"** — this toy is getting more popular over time (going up), AND
  right now it's on a little sale, sitting on a price where lots of people already
  bought it and won't let it drop. Good toy + good price = add.
- 🟢 **"Wait"** — great toy, but today it's a bit *too* expensive. Don't chase it;
  wait for it to come back down.
- 🟡 **"Getting cheaper, keep watching"** — it's starting to dip. Get ready.
- 🔵 **"Maybe waking up"** — it had a rough patch, but it just jumped over a quiet
  spot on the chart, which is often the first sign it's turning around.
- ⚪ **"Hands off"** — this toy is falling and looks sick. Don't buy more. (But you
  also **don't throw it away** — the friend has learned that selling usually turns
  out to be a mistake.)

**How does it know where the "good price" is?** It looks at *where all the other
kids bought* the toy. If tons of kids bought it around $10, then $10 is a strong
floor — they'll defend it — so buying near $10 is safe-ish. That crowded price is
the "shelf." The bot pays *more* attention to recent buyers than old ones.

**How much should you buy?** The friend has a strict allowance rule. A toy only
gets real money if it passes **five tests** (it's popular, going up, beating the
average, defended by buyers, and old enough to judge). The best ones get up to 5%
of your piggy bank, okay ones up to 2%, and **no single toy is ever more than 10%**
— so one bad pick can't wipe you out.

**One big weather rule:** if the *whole toy market* turns stormy (a special
signal using the two biggest baskets of stocks), the friend says **"stop buying
anything new, keep your cash"** — but still doesn't sell the core toys.

And the friend is honest: it openly admits the times its tricks *didn't* beat
just buying a little every month — so you always know exactly how much to trust
it.
