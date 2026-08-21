# CRYPTO_PLAYBOOK — the plain-English operating manual for the crypto sleeve

Companion to `CRYPTO_SLEEVE.md` (the policy, and its unsigned owner line) and
BACKTEST_RESULTS §41/§42 (the evidence). **PLAYBOOK.md governs the stock book
and none of it applies here.** This file is what you actually *do*.

The whole plan in one sentence:

> **Buy spot Bitcoin while it is cheap, keep it somewhere that cannot be
> liquidated, and only after the market proves the bottom is behind us, run a
> small capped leveraged engine whose profits are swept into the safe pile
> every month.**

## 1 · Where we are right now (2026-08-21 — re-read the digest, not this line)

| | |
|---|---|
| last cycle peak | 2025-10-06, $124,753 |
| cycle low so far | **$57,748** (2026-07-01) — 53.7% below the peak |
| BTC today | ~$75,360 |
| projected trough window | **2026-08-25 … 2026-12-23** |
| leverage signal | **🟡 ARMED 2026-08-21**, 0/56 days held, trigger $75,072 |
| your BTC | **zero** — the sleeve was liquidated in the 2026-08 reset |

**Phase: 1. Buy spot. The engine is OFF and stays off for at least 8 weeks.**

## 2 · Two buckets, and why

**The safe** — spot BTC (self-custody or IBIT). Cannot be liquidated, costs
~0.25%/yr to hold, and is where the sleeve actually compounds.

**The engine** — a capped leveraged perp position. Can be liquidated and
probably will be (it was liquidated in ~2 of 3 backtested cycles, and it did
not matter). Its job is to manufacture spot BTC, not to hold value.

Everyone who blows up on crypto runs one bucket. The separation *is* the
strategy: §41 measured a levered arm losing **98% of its coins** because the
whole stack sat in the liquidatable bucket.

## 3 · The four phases

**Phase 1 — NOW → confirmation. Unlevered spot only.**
Contribute **2.5× your base rate inside the trough window** (2026-08-25 →
2026-12-23) and **0.4× outside it**. Same total money, front-loaded into the
cheap part — worth +22.2% / +14.4% in coins across the two analogs (§41.6).
No perps, no leverage, no ETH.

**Phase 2 — confirmation fires → switch the engine on.**
Trigger: **BTC ≥ +30% above the running cycle low, held 8 consecutive weeks**
(§42), *and* CRYPTO_SLEEVE §3's other three conditions — **note condition 1
requires the trough window to have CLOSED (2026-12-23), so a confirmation
arriving in October does not authorise anything until January.** Then: BTC
perp at **≤3× inside the sweep structure** (§43; ≤2× without it), working
capital capped at **W = 12 months of contributions**. New money tops up the
engine; **every month sweep everything above W into spot.**

**You never switch to "leverage only."** The spot pile you already own is
never touched, and the engine has a hard ceiling — once it is at W, further
contributions are swept straight through to spot the same month. Routing
25% vs 100% of new money to the engine moved the result by ~2pp in one
analog and ~19pp in the other (§43), so it is a second-order dial, not a
gear change.

**Phase 3 — ~12 months before the projected peak (~2029-10). Sweep to CASH.**
Same engine, but harvest to USD instead of BTC. This is distribution.

**Phase 4 — peak window. Close the engine.** Then decide what the spot pile is
for; that decision is deferrable for ~3 years and is not made here.

## 4 · The monthly routine (10 minutes, on the 1st)

1. **Read the ₿ CYCLE line in the digest.** It tells you the phase. Nothing
   else in the digest governs this sleeve.
2. **Send the month's contribution** at the Phase-1 weight (2.5× or 0.4×), or
   into the engine if Phase 2 has begun.
3. **If Phase 2: sweep.** Anything in the engine above W goes to spot. Do this
   even when it feels early. Especially when it feels early.
4. **Write down what you did.** One line. Date, amount, price, bucket.

## 5 · What the digest line means

| line | meaning | what you do |
|---|---|---|
| 🟠 **leverage OFF** | below the trigger | buy spot; nothing else |
| 🟡 **ARMING — n/56d** | above the trigger, clock running | buy spot; **nothing changes until 56** |
| 🟢 **MARKUP CONFIRMED** | timing condition met | *check §3's other conditions*, then Phase 2 |
| 🎯 **in trough window** | inside 2026-08-25…12-23 | contribute at the **2.5×** weight |

**🟢 is not permission.** It reports the timing condition only. Conditions 1,
3 and 4 of CRYPTO_SLEEVE §3 still bind, and the sleeve's owner line is
unsigned, so today no amount of green authorises a levered order.

## 6 · The rules that never bend

1. **The safe is never collateral.** Not for a margin loan, not for a perp,
   not "just this once."
2. **W is the maximum you can lose.** Set it at a number that, if it went to
   zero tomorrow, would not change your life. That is the whole risk decision.
3. **Never rebalance the engine upward after a loss.** Adding notional into a
   drawdown is how the §41 arms died.
4. **No leverage on ETH, ever.** Every setting above 1.5× had a negative
   median; 3× const was 0.30× with 100% of windows liquidated.
5. **Never hold a perp as a long-term position.** Funding accrues on the whole
   notional forever: a 1× *perp* returned 0.21× where spot DCA returned 0.90×
   over the same window (§41.3).
6. **The 8-week clock resets on any close below the trigger.** No "it only
   dipped for a day." The reset is the rule that works.
7. **A realised liquidation of the engine bans leverage in this sleeve
   permanently**, pending a post-mortem (CRYPTO_SLEEVE §6).

## 7 · How confident to be, claim by claim

Read this before betting anything you care about.

**Near-certain (arithmetic, not statistics).** Liquidation prices at each
leverage. Funding costing ~35%/yr of equity at 3×. A liquidation being
permanent in coin terms. That harvesting bounds your loss to W. These are
mechanical and do not depend on the cycle repeating.

**Reasonably supported.** The harvest engine beating plain leverage (45
rolling windows, but only ~2.5 *independent* cycles). Cycle-weighted buying
beating flat buying (n=2 analogs, robust to the trough date being wrong by
±120 days). The 8-week hold — **25 bear-phase rallies measured, 0 survived
8 weeks; median 2 days, longest 46 days.**

**Weak — three observations each.** That the 4-year cycle continues at all.
The trough-window date (±47d out-of-sample error). The +30% threshold, which
§42 states outright is inside the noise.

**The plan is built so the weak parts cannot ruin you.** If the signal is
wrong, you lose W. If the cycle stops working, Phase 1 was just "buy Bitcoin
steadily," which is a fine plan on its own and needs no thesis at all.

## 8 · What would prove this wrong (write it down before, not after)

* **The trough arrives outside 2026-08-25…12-23 by more than 60 days** →
  the timing component is suspended, sleeve reverts to flat unlevered DCA.
* **A bear rally sustains 8 weeks above the +30% line** → the first such
  episode in 25; the hold lengthens to 12 weeks (also 0/25) and §42 is re-cut.
* **The engine is liquidated once** → leverage is banned here permanently.
* **ETH's unlevered coins-per-dollar trails BTC's over the accumulation
  phase** → the split goes to 100/0 mechanically.

## 9 · The live tension you should be holding in mind

The signal armed at −43% from the peak. **Every prior confirmation fired at
−54% to −80% from the peak**, and both completed cycles bottomed at −75.7% and
−83.1% against this cycle's −53.7% low. So two honest readings compete:

* **(a)** this cycle is genuinely shallower — ETF and institutional flows
  changed the structure; or
* **(b)** the bottom is not in, and this is the first false positive in 25
  measured episodes.

**Phase 1 is correct under both.** That is precisely why the plan buys spot
now and waits 8 weeks before risking anything — the disagreement resolves
itself while you are accumulating either way, and nothing is staked on which
reading is right.
