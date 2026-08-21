# CRYPTO_PLAYBOOK — step by step

Policy: `CRYPTO_SLEEVE.md` (owner line **UNSIGNED**). Evidence:
BACKTEST_RESULTS §41–§44. **PLAYBOOK.md governs the stock book and none of it
applies here.**

---

# PART A — WHAT TO DO THIS MONTH

## Step 1 · Open the digest, read three lines

```
₿ 🐻 BTC BEAR — last month-end $62,814 vs 10m SMA $77,257 (-18.7%)
  · phase MARKDOWN: past the peak, trough window not yet open
₿ ❌ NO LEVERAGE — entry gate OPEN; regime is BEAR; phase MARKDOWN
₿ CYCLE: 🟠 $69,266 is +20% off the $57,748 low · live $74,740 (unsettled)
```

Line 2 is the instruction. **✅ = leverage permitted. ❌ = spot only.**
Nothing else in the digest governs this sleeve.

## Step 2 · Look up the regime. Do exactly what the row says.

| regime | what it means | **contribution** | **the engine** |
|---|---|---|---|
| 🐻 **BEAR** | cycle is MARKDOWN/TROUGH, **or** 0–1 of 3 indicators | **spot BTC only** — 2.5× base rate inside the trough window, 0.4× outside | must be **FLAT**. If open, close it and move the proceeds to spot. |
| ⚖️ **MIXED** | cycle permits, 2 of 3 indicators | **spot BTC only**, base rate | **no new money in.** An open engine stays open with its stop; it is not topped up. |
| 🐂 **BULL** | cycle permits **and** 3 of 3 **and** entry signal fired | base rate into the engine; overflow above W → spot | **ON**, ≤3× inside the sweep, W capped, swept monthly, **stop always resting** |

There is no fourth case and no judgement call. The digest prints the regime;
you read the row.

## Step 2b · If the engine is open, RESET THE STOP (every month, without fail)

Place a resting stop where **equity ÷ notional = 5%**. Hyperliquid liquidates
at **1.25%**, so this fires first:

```
stop price = (size × avg_entry − collateral) ÷ (size × 0.95)
```

**Recompute it every month.** Funding drains collateral, which *raises* this
price over time. §46 tested a fixed price-from-entry stop and it was outrun by
funding — the exchange liquidated first. Expressing the stop as a margin
*ratio* is what makes it un-outrunnable.

Measured (§46): this took liquidations to **zero** across both peak-to-peak
windows **at no cost to returns** (16.0806 vs 16.0561 BTC, and identical in
the second window).

## Step 3 · Send this month's contribution

| digest says | you buy | how much |
|---|---|---|
| ❌ NO LEVERAGE + `🎯 in trough window` | **spot BTC** | **2.5× base rate** |
| ❌ NO LEVERAGE, no 🎯 | **spot BTC** | **0.4× base rate** |
| ✅ LEVERAGE PERMITTED | **top up the engine to W** | base rate; overflow → spot |

"Base rate" is your chosen monthly crypto budget. The 2.5×/0.4× weighting
deploys the *same total* money, front-loaded into the cheap window — worth
+22.2% / +14.4% in coins (§41.6).

**Trough window: 2026-08-25 → 2026-12-23.** You are in it from this month.

## Step 4 · If — and only if — the digest says 🐂 BULL, sweep

Every month, move everything in the engine above **W** into spot. Do it when
it feels early. That sweep is the entire reason leverage is allowed here
(§43: worst case 0.07× → 0.96× *while* the median rises).

## Step 5 · Check the ₿ TARGET line

It reads `✅ ON TRACK` or `⚠️ BEHIND`, and when behind it names the run-rate
that would fix it. Two things must be set in `contributions.json` for it to
score anything: `balances.btc_qty` / `ibit_qty` (what you actually hold) and
`balances.crypto_monthly_usd` (your sleeve run-rate). **Until both are set it
prints "run-rate NOT SET" and scores nothing — by design.**

The US$1M target needs **S$4,250/mo** and BTC at **$261k (2.1× the last
peak)** — inside the historical 1.9–3.4× range. At S$5,500/mo it needs 1.6×,
below the weakest cycle on record. At S$3,000/mo it needs 2.9×, which is
possible but is betting on a strong cycle.

## Step 6 · Write one line in a log

`date · amount · price · spot or engine`. That is the whole record-keeping
requirement.

---

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
4. **No leverage on ETH or any alt, ever.** Every ETH setting above 1.5× has a
   negative median; 3× const was 0.30× with 100% of windows liquidated.
   **HYPE is not covered by any of this work** — 1.7 years of history, 2.6×
   BTC's volatility, and it has never seen a bear market.
5. **Never hold a perp long-term.** Funding accrues on the whole notional: a 1×
   *perp* returned 0.21× where spot DCA returned 0.90× (§41.3).
6. **The 8-week clock resets on any close below the trigger.** No exceptions
   for "it only dipped a day."
7. **One realised liquidation of the engine bans sleeve leverage permanently**
   (CRYPTO_SLEEVE §6), pending a written post-mortem.
8. **The engine never runs without a resting stop**, and the stop is reset
   every month. An unstopped engine is the only configuration in this
   playbook that has ever been liquidated in testing.

---

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
