# HOW TO READ — the chart card manual (筹码图 reading guide)

This teaches you to read one **chart card** on the Danny board (#83 /
`docs/mockup-83.html`; any-ticker cards via #84 once built). Siblings:
`HOW_IT_WORKS.md` explains *why* the engines compute what they compute;
`PLAYBOOK.md` §2 reads the *text* digest; this file reads the *picture*.
Every mark on the card is a frozen-engine output — the chart never draws
anything the digest doesn't already know.

---

## 0 · The card at a glance (top to bottom)

```
 TICKER  [state pill]                        held · note
 [close][add zone][POC][% in profit][dip d2][VH][🐳][RS12][conv][F:n/3]
 ┌──────────────────────────────────────┬────────────┬─────────┐
 │  ~6 months of daily candles          │ chip       │ price   │
 │  + add-zone band (teal)              │ histogram  │ axis +  │
 │  + volatility-hole zone (violet)     │ (筹码分布) │ level   │
 │  + POC / support / resistance lines  │            │ labels  │
 ├──────────────────────────────────────┴────────────┴─────────┤
 │  52-week circle ribbon      wk circle · RED 15w · med run 8w │
 └───────────────────────────────────────────────────────────────┘
```

Read it in this order: **state pill → where price sits vs the teal zone →
the histogram's shape → the ribbon**. That's the whole method; the rest of
this file is what each of those four looks means.

---

## 1 · Candles — the colour IS the signal, and it's the Chinese convention

**⚠ Red = BULLISH. Yellow = bearish.** This is Homily/Danny's colour
language, the inverse of Western charts. The legend is pinned on the board
because misreading this one convention inverts every chart.

Exact definition (`homily_danny.daily_candle`, computed fresh for every
bar on the card):

| Colour | Condition | Meaning |
|---|---|---|
| 🟥 red | close > EMA10(daily) **and** MACD histogram > 0 | short-term momentum up |
| 🟨 yellow | close < EMA10(daily) **and** MACD histogram < 0 | short-term momentum down |
| ▪ gray | anything else | transition / no signal |

How to use it: a long red stretch = the trend is being *paid for* daily; a
few yellow candles inside an intact red ribbon = a normal dip (see the dip
counter, §4). What NOT to do: trade candle colours on their own — Danny's
own words, Mar 2026: *"Never simply follow red or yellow candles."* The
hierarchy is monthly trend → weekly circle → chip context; daily colour is
the entry-timing garnish, and a 🔵 volatility-hole breakout outranks it.

## 2 · The chip histogram (筹码分布) — where the holders live

The right-hand panel is the cost distribution: every past day's volume
spread over that day's price range, decayed with a 60-trading-day
half-life, so **recent accumulation dominates**. Each horizontal bar =
how much (decayed) volume changed hands at that price.

| Mark | What it is | How to read it |
|---|---|---|
| **Teal bars** (below price) | chips **in profit** (获利盘) | holders defending a winning basis — support |
| **Slate bars** (above price) | **trapped** chips (套牢盘) | holders waiting to break even — sellers into rallies |
| **Orange bar + dashed line** | **POC**, the heaviest bin | the crowd's dominant cost basis; the market's centre of gravity |
| **`sup` dashed teal line** | biggest peak below price | the shelf the add zone is built on |
| **`res` dashed slate line** | biggest peak above price | where rallies tend to stall first |
| **Teal band across the plot** | the **add zone** = 0.98×–1.03× of the top support shelf | the price range where adding is sensible; "at support" = within 3% above the shelf |
| **% chips in profit** (facts row) | share of chip weight below price | >90% = everyone's happy, few sellers above (momentum-friendly, but extended); <40% = heavy overhead supply |

Shape intuition: a **tall, tight histogram near price** = consolidation,
basis agreed, moves from here are cleanly decided at the shelf. A
**stretched, two-humped histogram** = old holders far below, recent buyers
far above — the gap between humps is air; price crosses it fast in both
directions.

## 3 · The violet band — the volatility hole (Danny: "the most crucial part")

A **hole** day = relative volatility (ATR5/close) making a new 60-day low
— the coil fully compressed. Consecutive hole days cluster into a **zone**
(the cluster's high/low), drawn as the violet band from where it formed to
the right edge; it stays in force ~90 bars or until price escapes it.

| Label on the card | Meaning | Honest evidence (PRD §5b) |
|---|---|---|
| `vh breakout ↑` | close above the upper boundary | modest bullish edge, measured: +4.4% vs +2.8% baseline fwd 20d; +11.5% vs +8.5% fwd 60d. Powers the 🔵 state |
| `vh breakdown ↓` | close below the lower boundary | **NOT predictive** in our backtest (breakdowns outperformed baseline). Warning note only — it never vetoes an add |
| `vh zone` | price still inside | spring loaded, direction undecided — watch which side gives |

Multi-timeframe footnote (#77, run 2026-07-11): weekly/monthly holes added
**nothing** in our universes, and Danny's SPY-monthly "perfect record" was
the market's own base rate. Only the daily hole earns its place on the card.

## 4 · The ribbon and the two clocks

The bottom strip is the **weekly circle** (the 4-factor Homily-clone
engine) for the last 52 weeks: 🟥 RED = healthy uptrend structure, 🟨
AMBER = wobbling, ▫ WHITE = broken. It's the chart's memory — you see at a
glance whether this name grinds red for months (trend keeper) or flickers.

Two measured base rates are printed so you don't have to guess (info-only,
they gate nothing):

* **`med run 8w`** — the median completed weekly-RED spell across 1,439
  historical spells (p25 2w · p75 23w · p90 42w). A quarter of red runs
  last 23+ weeks: a fresh ⭐ window is usually not urgent-tomorrow.
* **`dip d{n} (med 4d · p90 22d)`** — n = trading days the current
  non-red-candle pullback has run inside an intact weekly-RED. Median
  healthy dip: 4 days (Danny's "3–7 days" holds at the median, not the
  spread). **Deliberately NOT a warning:** we tested "dip older than p90 =
  trend failing" and it's REFUTED — failures actually resolve *faster*
  (median 3d). Dip age alone tells you nothing about failure; that's why
  the counter has no colour.

## 5 · The facts row, chip by chip

| Chip | What it means | What you do (PLAYBOOK ref) |
|---|---|---|
| ⭐ ACCUMULATE | monthly UP + weekly RED + price at/near a major chip shelf | candidate for the monthly buy (§3); caps: 10%/name, max 5 names (§3.4) |
| 🟢 HOLD | uptrend intact but price extended above support | do nothing; wait for the pullback to the teal band |
| 🟡 PULLBACK | weekly AMBER while monthly still UP | dip forming — watch the shelf; 🎯 on a 🟡 = optional aggressive add (§3 step 6) |
| ⚪ CAUTION | weekly WHITE or monthly trend down | pause adds. **Not a sell** — selling has its own three rules (§5) and none of them is "the chart turned white" |
| 🔵 BOTTOMING | trend broken but upside VH breakout fired | early-bottom candidate, discretionary |
| 🎯 at support | a non-⭐ name trading inside its add zone | context only. 🎯 alone on ⚪ tested WORSE than waiting — needs 🐳 |
| 🐳 whale footprint | dip + ≥2 of: absorption print · OBV+A/D divergence · shelf replenished | ⚪+🎯+🐳 = the ONE permitted ⚪ add (WHALE-DIP, ≤2%/name, 10% sleeve cap, §3.6b) |
| `close` / `add` / `POC` | last close; the teal band; the orange line | compare: below add = gift, inside = act on buy day, far above = wait |
| `RS12` | 12-month **total** return minus SPY's (dividends counted, pts) | the selection ranker — the October rs12-top3 read concentrates buys in the top-3 if its forward-check passes |
| `conv NN` | conviction score 0–100 | honesty (#20, BACKTEST §11): the score's *ranking* is real OOS; the 75/60 tier labels separate nothing. Compare names by score, ignore the label |
| `F:n/3` | EDGAR checks: revenue growth >10% · NI>0 or OCF>0 · dilution <12% | info-only; `F:—` = non-US. Sharpens hold-through-⚪ judgment, never times entries |
| `x% of book` / ⚠ cap note | position awareness | ⚠ means an add would breach the 10% cap — copilot already sized for it |

## 6 · How it combines — worked examples (the three mockup cards)

**NVDA (⭐, the setup you're hunting):** ribbon red 15w with a shallow
2-day dip · price sitting ON the teal add band · POC below (basis support,
70% in profit) · VH breakout above the zone. Monthly up + weekly red +
at-shelf = ⭐. Action: it's on the buy-day list; add inside 196–206, know
that res 209 is the first fight overhead.

**TSLA (⚪ + 🐳, the trap to NOT buy... yet):** ribbon flipped WHITE 3w
ago · VH **breakdown** (warning, not veto) · price above a still-fat POC
but the histogram's profit share is only 55% — half the crowd underwater.
⚪ = pause adds. The 🐳 says big buyers absorbed the dip — IF a 🎯 prints
(price into the shelf), the ≤2% WHALE-DIP exception applies. Otherwise:
hands off, let the ribbon repair.

**SHOP (🔵, the early-bottom speculation):** trend broken (WHITE 22w) but
an upside VH breakout fired out of a long coil, whale prints present,
price back above POC. This is the *earliest* legitimate signal in the
system and the least proven — discretionary, small, or just watchlist it.

## 7 · What the chart will NEVER show — and what's actually proven

Never on the card, by design: **price targets or measured moves** (Danny
himself mocked pattern-target callers; §5k rejected them), **sell signals
on core names** (no SELL state exists; §5's three trim rules are the only
sells and they're rules, not chart marks), leverage, options, or any claim
of replicating Homily's/Danny's proprietary formulas — every element is
our documented approximation.

Evidence status of what you're looking at (so the chart can't oversell
itself — receipts in `BACKTEST_RESULTS.md`):

| Element | Status |
|---|---|
| Selection + never-sell (the core) | the measured edge lives here (§3–§4) — and still doesn't reliably beat QQQ; the live ledger is the referee |
| ⭐ at-shelf entry timing | per-name ⭐-waiting LOST to DCA (§5f) — ⭐ picks *which* names, buy-day discipline does the rest |
| VH breakout / 🔵 | modest measured edge (§5b) |
| VH breakdown warning | null — printed as context only |
| 🐳 accumulation | gate PASSED → the one ⚪ exception (§5h) |
| dip/run counters, % in profit, Q/F labels | info-only, gate nothing |
| conviction tier labels | null (§11) — read the number, not the label |

## 8 · Looking up any stock

* **Board search (#83):** the production board carries a card for **every
  screened name** (~68) — type in the search bar or tap a ticker chip.
* **Any ticker at all (#84):** `python3 homily_chart.py TICKER` fetches
   2y of bars, runs the same frozen engines read-only, and renders the
  same card for any Yahoo-resolvable symbol (incl. `.HK`/`.SI`). The card
  carries an `ad-hoc — not screened, no ledger history` banner: a chart on
  demand is context, not a tracked call.
* **Make it permanent:** add the name to `WATCH`/universe and it appears
  on the board (and in the ledger) from the next run, provenance-tagged.
* Until #83/#84 ship: the digest's top-3 PNG cards, `docs/mockup-83.html`
  for the pattern, or ask Claude in a session.

*Levels are context, not advice. The chart is an approximation of
documented Danny/Homily behaviour — not their formulas, and never a
promise of their returns.*
