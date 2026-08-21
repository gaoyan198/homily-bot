# CRYPTO_SLEEVE.md — the 4-year-cycle accumulation policy (#147 / D-147)

**Status: PROPOSED 2026-08-20, awaiting the owner line at the bottom.**
**Amended 2026-08-21 (#148):** the §3 markup confirmation moved from +40% to
**+30%, held 8 weeks**, on measurement (BACKTEST_RESULTS §42), and is now
watched daily in the digest. Constants pinned by
`homily_cryptocycle_backtest.py` (run 2026-08-20, BACKTEST_RESULTS §41) and
`homily_cryptocycle.py` (§42). This is the two-artifact governance record, same
pattern as LEVERAGE.md: §41 is the evidence, this file is the policy.

**The objective is BTC UNITS, not dollars.** Every rule below is written
to maximise coins held at the next cycle peak. A month that ends with
more dollars and fewer coins is a losing month. This is the owner's
stated mandate — *"the goal is to collect as much btc as possible"* —
and it is the metric §41's gate (R7) was pre-registered on.

## 1 · Position today (2026-08-20)

Zero BTC. The sleeve was liquidated in the 2026-08 household reset
(commit 5256145). This policy starts the rebuild from flat, which is the
best possible position to be in 10.4 months past a cycle peak.

## 2 · The cycle map (frozen; re-derived only at §6 review)

| event | date | basis |
|---|---|---|
| last halving | 2024-04-19 | actual |
| last peak | 2025-10-06 | actual, $124,753 |
| **projected trough** | **2026-10-24** | peak + mean(prior peak→trough) = 383d |
| **trough WINDOW** | **2026-08-25 … 2026-12-23** | ±60d, from measured OOS error |
| next halving | ~2028-04-16 | ~1458d spacing |
| next peak | ~2029-10-04 | halving + mean(last 3) = 536d |

The estimator is scored out-of-sample in §41.5: **−47d** on the 2018
trough, **−10d** on the 2022 trough. It is used as a **window**, never as
a date. Three observations. Treat it as a planning aid that has earned
some trust, not as knowledge.

## 3 · The leverage rule — the short version is NO, and here is when that changes

**No leverage is carried through the trough window. None.** §41.4's gate
(levered must beat unlevered spot on units in BOTH accumulation analogs)
returned **1/2 on every setting tested** — 2x and 3x, const and entry.
The failing analog is not a near-miss: it is **−98%** of units, because
a liquidation is permanent in a metric denominated in coins.

The arithmetic that makes this non-negotiable (§41.5): the **mildest**
completed cycle drawdown (−75.7%) implies a trough of **$30,315**, which
is **below** the liquidation price of a position opened today at 3x
($48,437), 2.5x ($43,593), 2x ($36,328) **and 1.5x** ($24,218 clears it,
but only by assuming this cycle is milder than any measured one).

> **You cannot hold the 4-year-cycle thesis and hold leverage through the
> trough.** They are the same bet placed in opposite directions. The
> stronger the conviction in the cycle, the stronger the case against
> leverage right now.

**When leverage may be reconsidered — all four, together:**

1. The trough window (§2) has **closed**, and
2. **the markup confirmation has fired** — BTC closing **≥ +30% above the
   RUNNING cycle low and holding above that line for 8 consecutive weeks**
   (§42; constant revised 0.40 → 0.30 on measurement). The trigger is
   measured off the *running* low, so it falls with any new low and never
   requires guessing where the bottom is; **any close back below resets the
   clock to zero.** The 8-week hold is the load-bearing part and is not
   negotiable — every 4wk/6wk variant tested produced a false positive
   (2018-03-08 fired at $9,395, then BTC fell to $3,191: a wipeout at 3x).
   The 30% threshold is inside the noise at n=3 and may be argued with; the
   hold may not. Watched daily by `homily_cryptocycle.py` (validate [72]),
   which prints the ₿ CYCLE line in the digest — **a watch, not an
   authorisation: it reports condition 2 only, and 1/3/4 still bind**, and
3. the instrument is **BTC only** — ETH is banned at any leverage (§4), and
4. gross sleeve leverage **≤ 2.0×**, sized so the liquidation price sits
   below the confirmed trough print.

Any re-lever is a new dated entry in this file with its own numbers. It
is not a judgement call made in a strong week.

## 4 · ETH is not a levered instrument here

Across rolling 3-year windows (§41), every ETH setting above 1.5x has a
**negative median**: 2x const 0.60x with 69% of windows liquidated, 3x
const **0.30x with 100% liquidated**. ETH also lost money unlevered over
the whole 2022→2026 cycle (1.02x in ~4 years). ETHA/ETH may be held
**unlevered and secondary** at the §5 weight; it never carries margin,
and it is never the reason to add risk.

## 5 · What actually ships — the accumulation rule

* **Instrument: SPOT.** Self-custodied BTC or IBIT. **Not perps.** §41.3:
  a 1x *perp* returned **0.21x** where spot DCA returned 0.90x over the
  same window, because funding accrues on the full notional forever
  ($49,703 on $72,000 contributed). Perps are a trading instrument; this
  is a holding thesis. IBIT costs 0.25%/yr to hold; a perp cost ~12%/yr
  on average and 45% in the last bull.
* **Split: 70/30 BTC/ETH**, rebalanced never. BTC is the mandate; ETH is
  a satellite that must earn its place at the §6 review.
* **Schedule: cycle-weighted, 2.5× inside the trough window, 0.4×
  outside** — the one arm that beat flat DCA in **both** analogs (+22.2%,
  +14.4% in units, §41.6). Concretely, against a base sleeve rate `B`:
  contribute **2.5·B** for months landing in 2026-08-25…2026-12-23, and
  **0.4·B** thereafter until the §3 re-lever review.
* **Size: from savings, never from margin, never from the IBKR book.**
  The account already runs 1.216× on a grandfathered core-book loan that
  LEVERAGE.md §2 forbids extending. The crypto sleeve must not be the
  reason that loan grows. Sleeve contributions come out of the S$4,250/mo
  savings, and the sleeve's own budget line is the owner's to set — this
  file deliberately does not name a dollar figure, because §41 measured
  *ratios and survival*, not a household allocation.
* **All-in at the projected trough is NOT the rule.** §41.6 prints it
  (+52.1% / +49.1%) as the ceiling of perfect conditioning. It stakes the
  whole budget on one month carrying a ±47d error. The weighted schedule
  captures roughly half that edge and survives being wrong about the date.

## 6 · Review + demotion (this policy's own kill rule)

* **At the close of the trough window (2026-12-23):** re-run the harness,
  re-derive §2 from actuals, and record whether the trough landed inside
  the window. **If it did not, the estimator's error set is updated and
  §5's weighting is widened, not re-fitted to the miss.**
* **A realised liquidation anywhere in this sleeve** — any size — bans
  leverage in the sleeve permanently, pending a full post-mortem in
  BACKTEST_RESULTS. Same rule as LEVERAGE.md §5.
* **If ETH's unlevered units-per-dollar trails BTC's across the full
  accumulation phase**, the §5 split goes to 100/0 mechanically at the
  next review. Recorded, not debated.
* **The cycle thesis itself is falsifiable**: if the trough arrives more
  than 60d outside the §2 window, or trough→trough spacing departs from
  the 1431/1437d pattern by >10%, the timing component of this policy is
  suspended and the sleeve reverts to flat unlevered DCA.

## 7 · What this policy does NOT do

It touches no signal, no selection rule, and no part of the stock engine.
It does not move LEVERAGE.md's account ladder (crypto is off-IBKR; #128's
assertion that the sleeve never moves the printed ladder reading stands).
It is not evidence about the stock engine in either direction, and §9.0's
beat-QQQ bar is unaffected by anything in here.

---

**Owner line (two-artifact pattern).** This policy is PROPOSED, not
signed. It ships with a NO on leverage that the owner asked to be
evaluated at 3x and 2x — the gate was pre-registered and both failed, so
the honest artifact is a refusal plus the conditions under which the
answer changes (§3). The long-run $1M BTC thesis is **not** in dispute
here and is not what §41 tested; the finding is narrower and survives
that thesis being right: *leverage does not increase the number of coins
you end the accumulation phase holding, and one liquidation permanently
reduces it.*

> Sign below to adopt, or amend §5's weights/split directly — the
> schedule is the part most worth arguing with, and the leverage rule is
> the part that should not be re-shopped in a strong week.
>
> — owner (gaoyan): ______________________  date: ____________
