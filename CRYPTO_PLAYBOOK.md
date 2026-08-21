# CRYPTO_PLAYBOOK — step by step

Policy: `CRYPTO_SLEEVE.md` (owner line **UNSIGNED**). Evidence:
BACKTEST_RESULTS §41–§44. **PLAYBOOK.md governs the stock book and none of it
applies here.**

---

# PART A — WHAT TO DO THIS MONTH

## Step 1 · Open the digest. Read the verdict line.

```
₿ ═══ CRYPTO REGIME: 🐻 BEAR ═══ SPOT ONLY — no leverage
```

Three possible verdicts, and they send you down different paths:

| verdict | go to |
|---|---|
| 🐻 **BEAR** or ⚖️ **MIXED** | **Step 2** (spot only) |
| 🐂 **BULL** | **Step 3** (the engine routine) |

There is no fourth case and no judgement call.

## Step 2 · SPOT PATH (🐻 BEAR or ⚖️ MIXED) — this is where you are today

Buy spot, **split 50/50 BTC / HYPE**, at the weight the window dictates:

| | weight | why |
|---|---|---|
| inside the trough window (`🎯` shows) | **2.5× base rate** | the cycle says the bottom is here |
| outside it | **0.4× base rate** | same total money, spent smarter |

**Trough window: 2026-08-25 → 2026-12-23.**

The engine must be **FLAT**. If it is open and the verdict has turned, close
it and move the proceeds to spot. Then stop — Steps 3 and 4 do not apply.

## Step 3 · ENGINE ROUTINE (🐂 BULL only) — do these FOUR in this ORDER

**Order matters.** Resetting the stop before you re-lever leaves it stale the
moment you finish, which is how a stop stops protecting you.

**Worked example — engine cap W = $24,000, BTC has risen, engine now $30,000:**

| # | do this | example |
|---|---|---|
| **1** | **Contribute** your base rate into the engine | engine $30,000 → **$32,000** |
| **2** | **Sweep** everything above **W** out to **spot BTC** | $8,000 out → engine back to **$24,000** |
| **3** | **Re-lever** to 3× the remaining equity | hold **$72,000** of BTC on $24,000 |
| **4** | **Reset the stop** — recompute it now, last | see Step 4 |

**Three rules inside this routine:**

* **The sweep buys BTC, not HYPE.** Your 50/50 governs *contributions* — the
  part you control. Engine profits are BTC profits and stay BTC. Sweeping
  them into HYPE would grow the unmanaged half out of the managed half's
  earnings.
* **W is your maximum loss.** It is the only real sizing decision in this
  sleeve. Pick a number that, if it went to zero tomorrow, would change
  nothing.
* **Do the sweep even when it feels early.** Especially then. The sweep is
  the entire reason leverage is permitted here (§43: worst case 0.07× → 0.96×
  *while* the median rises).

**Monthly, never quarterly.** Returns between the two were a coin flip
(+54.5% vs +40.5% in one window, +63.8% vs +71.6% in the other). Monthly wins
on a different argument: the stop must be reset every month regardless, so
you are touching the position monthly anyway.

## Step 4 · Reset the stop (part of Step 3, called out because it is the one that saves you)

Place a resting stop where **equity ÷ notional = 5%**. Hyperliquid liquidates
at **1.25%**, so yours fires first:

```
stop price = (size × avg_entry − collateral) ÷ (size × 0.95)
```

**Recompute every month — this is the mechanism, not housekeeping.** Funding
drains collateral, which *raises* this price over time. §46 tested a stop
fixed at a price below your entry: funding outran it and the exchange
liquidated first. A stop that can be outrun is not a stop.

Measured: this took liquidations to **zero** across both peak-to-peak windows
**at no cost to returns**.

## Step 5 · Check the ₿ TARGET line

It reads `✅ ON TRACK` or `⚠️ BEHIND`, and when behind it names the run-rate
that would fix it. Three things must be set in `contributions.json` for it to
score anything: `balances.btc_qty` / `ibit_qty` (what you hold),
`balances.crypto_monthly_usd` (your run-rate) and `balances.crypto_btc_share`
(0.5 for the 50/50). **Until they are set it prints "run-rate NOT SET" and
scores nothing — by design.**

US$1M needs **S$4,250/mo** and BTC at **$261k (2.1× the last peak)** — inside
the historical 1.9–3.4× range. At 50/50 the BTC half only gets you part way,
and the line states what the HYPE half must return to close the rest.

## Step 6 · Write one line in a log

`date · amount · price · spot or engine`. That is the whole requirement.

# PART B — THE GATES (why the digest says what it says)

Leverage turns on only when **all four** are true. The digest checks them for
you and names every one that is open.

| # | gate | today |
|---|---|---|
| 1 | **Cycle phase** — trough window CLOSED (after 2026-12-23) | ❌ MARKDOWN |
| 2 | **Entry signal** — BTC ≥ +30% above the running low, held **8 weeks** | ❌ needs $75,072 |
| 3 | **Regime** — 10-month SMA reads BULL | ❌ BEAR |
| 4 | **Owner line** on CRYPTO_SLEEVE.md signed | ❌ unsigned |

## Gate 2 — the entry signal (unchanged)

BTC closes **≥ +30% above the RUNNING cycle low**, and holds for **8
consecutive weeks**. Any close below resets the clock to zero. The trigger is
measured off the running low, so it *falls* with any new low — you never have
to guess where the bottom is.

## Gate 3 — the regime board (§45)

**One verdict, four confirming indicators, and the 4-year cycle outranks all
of them.** Measured markdown false-BULL rates: 20wk SMA 14%, 200d SMA 14%, 10m SMA 24%,
50/200 cross 20% — **every single indicator is wrong often enough inside a
markdown to lose money on.** Unanimity of the three kept ones cuts it to
**9%**, the best achievable on this data.

* **PRIMARY — the 4-year cycle.** In MARKDOWN or the TROUGH WINDOW the verdict
  is 🐻 BEAR *no matter what the indicators say*. The digest prints
  `← OVERRIDES the indicators` when this fires, so you can see it happen.
* **CONFIRMING — 3 of 3 or it is not a bull.** 0–1 = 🐻 BEAR, 2 = ⚖️ MIXED
  (spot only), 3 = 🐂 BULL. The three are **20-week SMA · 200-day SMA ·
  10-month SMA**. The 50d/200d cross was dropped (§46): every indicator set
  containing the 20-week scores 9% markdown false-BULL, every set without it
  scores 14–24%, and the cross adds nothing to a set that already has it.

**Today: 2 of 3 bullish and the cycle says MARKDOWN → 🐻 BEAR.** Two
indicators are bullish and the verdict is still BEAR. That is the override
working, not a malfunction.

## Gate 3a — the 10-month SMA, in detail (same maths as your stock book)

10-month SMA of **completed** month-end closes. Above = 🐂 BULL, below =
🐻 BEAR. The running month never votes. Identical construction to
`homily_regime.sma10_state` for SPY/QQQ — and it earns its place on BTC on its
own evidence (§44): BULL months average **+8.61%** forward vs BEAR **+0.96%**;
long-only-in-BULL returns **395× vs 284×** buy-and-hold at **60%** max
drawdown instead of **76%**.

**The two gates do different jobs.** The signal guards the ENTRY — it cannot
fire during a markdown, but it never turns off. The regime guards the EXIT —
it turns off, but it fires early in a markdown (it mislabels 26% of markdown
months as BULL). Measured peak-to-peak: signal-only 2 liquidations,
regime-only **5**, both together **1**.

---

# PART C — THE FOUR PHASES

| phase | when | what you do |
|---|---|---|
| **1 · MARKDOWN / TROUGH** ← *you are here* | now → gates open | spot only, 2.5× inside the window |
| **2 · MARKUP** | all four gates ✅ | engine ≤3× inside the sweep, W capped, sweep monthly → spot |
| **3 · DISTRIBUTION** | ~12mo before the projected peak (~2029-10) | same engine, sweep to **CASH** not BTC |
| **4 · PEAK** | peak window | close the engine; decide what the spot pile is for |

---

# PART D — RULES THAT NEVER BEND

1. **The safe is never collateral.** Not for margin, not for a perp, not once.
2. **W is your maximum loss.** Set it so losing it entirely changes nothing.
3. **Never add to the engine after a loss.** That is how the §41 arms died.
4. **The sleeve is 50/50 BTC/HYPE** (owner decision 2026-08-21). Spot buys
   split 50/50. **HYPE is unmanaged** — no regime gate, no cycle rule, no
   stop — and **never carries leverage.** Every gate, phase and signal in
   this playbook governs the BTC half ONLY.
5. **No leverage on ETH, HYPE or any alt, ever.** Every ETH setting above 1.5× has a
   negative median; 3× const was 0.30× with 100% of windows liquidated.
   **HYPE is not covered by any of this work** — 1.7 years of history, 2.6×
   BTC's volatility, and it has never seen a bear market.
6. **Never hold a perp long-term.** Funding accrues on the whole notional: a 1×
   *perp* returned 0.21× where spot DCA returned 0.90× (§41.3).
7. **The 8-week clock resets on any close below the trigger.** No exceptions
   for "it only dipped a day."
8. **One realised liquidation of the engine bans sleeve leverage permanently**
   (CRYPTO_SLEEVE §6), pending a written post-mortem.
9. **The engine never runs without a resting stop**, and the stop is reset
   every month. An unstopped engine is the only configuration in this
   playbook that has ever been liquidated in testing.

---

# PART D2 — TESTED AND REJECTED (do not reinvent these)

Each of these was proposed, tested against real data, and **lost**. They are
recorded so nobody — including a future session — quietly reintroduces one.

| idea | what happened | verdict |
|---|---|---|
| **Hold 20% USDC, buy on a −20% dip** | BTC dipped 20% **23 times in 3 years** — every 6–8 weeks. Not a bargain, just Tuesday. Lost in **11 of 15** tests; worst −13.6%, best +2.9% | ❌ the **6th** failure of hold-cash-for-dips in this repo |
| **Add leverage during dips** | Returns fell (+51.0% vs +54.5%) and stop-outs went **1 → 6** | ❌ this is Rule 3 as data |
| **Quarterly engine rebalance** | Coin flip on returns, but the stop needs a monthly reset anyway | ❌ more parts, no gain |
| **Fixed price stop (−25% from entry)** | Funding drain raises the liquidation price until it passes your stop. Still liquidated at **every** level tested | ❌ use the margin-ratio stop |
| **Held leverage, no sweep** | −97% of coins in the losing analog | ❌ the sweep is why leverage is allowed at all |
| **ETH in the accumulation leg** | 100% BTC beat 70/30 in **both** accumulation analogs | ❌ Phase-2 question at most |
| **Leverage on ETH / HYPE / any alt** | ETH 3× = 0.30× median, **100%** of windows liquidated | ❌ never |
| **Majority-vote regime (2 of 3)** | Reintroduces the false-BULL that costs money in markdowns | ❌ unanimity or it is not a bull |
| **Shorter entry hold (4wk / 6wk)** | Measured *better* with the regime gate, but only the 8wk hold is independently sufficient — at 4wk only the regime exit stands between the engine and a markdown | ⚠️ judgement call, logged in §44.1 |

## The one that looks the same but WORKS

**Buying heavy when the 4-year cycle says the bottom is due** gave **+22.2% /
+14.4%** more coins.

Same instinct as the dip fund — hold back, buy cheap. The difference is what
tells you *when*. **A price drop tells you nothing** (they happen every six
weeks). **The cycle tells you something** (three bottoms, same place, ±47
days).

**So your cash buffer is trough-window ammunition, not a dip fund.** To buy at
2.5× weight for the four months of the window you need roughly **S$67,800**,
against about **S$17,000** of salary over that stretch — a **~S$50,800 gap**
that only existing cash can fill. Held back for dips, that cash costs you the
single largest edge in the plan.

# PART E — CONFIDENCE, AND WHAT WOULD PROVE THIS WRONG

**Near-certain (arithmetic).** Liquidation prices. Funding costing ~35%/yr of
equity at 3×. That a liquidation is permanent in coin terms. That the sweep
bounds your loss to W.

**Reasonably supported.** The regime rule (134 months). The sweep structure
(45 rolling windows ≈ 2.5 independent cycles). The 8-week hold (25 bear
episodes; 0 survived).

**Weak — three observations each.** That the 4-year cycle continues. The
trough-window date (±47d out-of-sample). The +30% threshold, which §42 states
outright is inside the noise.

**Known open question.** With the regime gate in series, **4wk and 6wk holds
measured BETTER than 8wk** in both peak-to-peak windows (§44.1). 8wk is kept
because it is the only setting where the two gates are independently
sufficient rather than serially dependent — a judgement call on an n=2 return
estimate, logged as one.

**Falsifiers, written before the fact:**
* trough arrives >60d outside 2026-08-25…12-23 → timing component suspended
* a bear rally sustains 8 weeks above the +30% line → hold goes to 12wk
* the engine is liquidated once → leverage banned here permanently
* ETH/alt coins-per-dollar trails BTC over the accumulation phase → 100/0

**The live tension.** The signal would confirm near −43% from the peak; every
prior confirmation fired at −54% to −80%, on cycles that bottomed −75.7% and
−83.1% against this one's −53.7%. Either this cycle is genuinely milder, or
the bottom is not in. **Phase 1 is correct under both** — which is why the
plan buys spot now and stakes nothing on which reading is right.
