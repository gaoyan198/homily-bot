# PLAYBOOK — the plain-English operating manual

You don't need to understand the indicators. You need to follow this file.
Everything here is pre-decided so that nothing is decided in panic.

---

## 1 · Your money lives in three buckets

| Bucket | What's in it | Rule |
|---|---|---|
| **A — INDEX CORE** | SRS SPY+QQQ, CSPX | **Never sold. Never timed. Bear or bull.** This is the retirement engine. |
| **B — EARNED CORE** | Any single stock that GREW to ≥10% of the stock book *while you followed the add rules*, and passes fundamentals (F:2+ or a real profitable business) | Hold through drawdowns. No adds while it's in CAUTION. |
| **C — SATELLITES** | Every stock position below 10% | These are the only things you ever sell. |

**Core is earned, not declared.** You never *decide* something is core — it
becomes core by compounding. A position that is big because you *bought* big
(not because it grew) is not core; it's an oversized satellite.

---

## 2 · How to read the daily digest (2-minute version)

Only three things matter daily:

1. **First line — the regime banner.** 🐂 = normal life. 🐻 = go to §4 of
   this file. ⚖️ = do nothing, wait for month-end. *This line is the whole
   reason the digest exists.*
2. **The ⭐ ACCUMULATE section** = the shopping list for your next monthly
   buy. Ignore every other section on buy day.
3. **Your own big positions' state.** If a Bucket-B name shows ⚪ CAUTION —
   stop adding to it. That's all it means. It is not a sell signal.

Decoder for one row:
`⭐ TSM 434 — add 416-437 · POC 341 · res 439 · 84% in profit · wk RED/4 (57w) · mUP · dY · F:3/3`
= "TSM is a buy-zone name. Good price to add: 416–437. The crowd's average
cost is 341 (they're happy, they'll defend it). Next ceiling ~439. Trend has
been healthy 57 weeks. F:3/3 = the business itself checks out."
Everything else (dY, VH, score) is detail for when you're curious — never
required for action. One exception worth knowing: `🎯 + 🐳` on a ⚪ row =
a dip that reached the chip shelf AND shows big buyers absorbing it — the
one backtested case where adding to a ⚪ name is allowed (§3 step 6b).

---

## 3 · Monthly buy routine (10 minutes, once a month)

*Since 2026-07 the month's first digest leads with a 🛒 BUY DAY section
(#31) that resolves the steps below into exact orders from your
`BUY_BUDGET_USD` repo variable, plus an importable basket CSV
(`docs/orders_YYYY-MM.csv`). It prints, you decide and type — nothing is
ever placed for you (§7). Non-USD names (9992.HK) are listed as "manual"
— size those yourself. These steps stay the source of truth and the
fallback.*

1. Open today's digest. Banner 🐂? Continue. (🐻 → §4. ⚖️ → still continue,
   ⚖️ only pauses *selling* decisions.)
2. Take your monthly DCA amount (see §7).
3. Half of it → Bucket A (index). **Your SRS contributions ARE this half**
   (provided the SRS cash is actually deployed into SPY/QQQ, not idle) —
   if SRS is funded and invested, your cash DCA may go fully to step 4.
4. Other half → split across the **top-3 ⭐ names by RS12** (holdings +
   discovery; the digest marks them `RS#1–3`). Skip any name that would
   exceed **25%** of your stock book.
   *(#24 promoted 2026-07-12 — by owner override, AHEAD of its live
   forward-check; the check keeps publishing at each month-start through
   2026-10 and a FAIL demotes this back to equal-split-max-5 mechanically
   (promotions.json). The add-cap was 10% until 2026-07-12: #92/D-92
   promoted it to 25% — the move D-67 (§12) had already priced as
   formally adoptable (ties-or-beats 10% in 7/9 windows) at a RECORDED
   cost: when the book's biggest name gaps −95% and never recovers, the
   25% cap keeps 1.70 MOIC vs the 10% cap's 1.89 — half the insurance
   payout, surrendered deliberately for room to add into winners. What
   still contains wrecks is the ⭐ gate itself (wrecks lose ⭐ long
   before they accumulate — D-67 step 2a). The demotion rule is armed
   and checked every run: any name ≥15% of the stock book closing −50%
   from its post-promotion high prints a 🚨 banner and the cap reverts
   to 10% in the next session, mandatorily. Uncapped remains excluded —
   its −95% shock number is 1.49.)*
5. **If there are no ⭐ names: buy Bucket A with the full amount.** The
   backtest is clear — cash waiting for stars costs more than it saves.
6. **Optional aggressive add (🎯 on a 🟡 row):** a still-bullish name whose
   dip has reached its support shelf — the Danny-style add. Allowed, but it
   is DISCRETIONARY: it isn't part of the backtested routine, comes out of
   the same monthly budget (never extra money), and respects the same caps.
6b. **WHALE-DIP add (🎯 + 🐳 on a ⚪ row):** the ONE case a ⚪ name may be
   bought — the dip has reached the chip shelf AND the tape shows the
   whale-accumulation footprint (heavy-volume absorption print, money
   flowing in vs price, shelf being replenished). This one IS backtested
   (58 names incl. the 2021 wrecks: beat both DCA and plain dip-buying at
   20d and 60d) — but the edge is modest, so the cap is small: **≤2% of
   the account per name**, same monthly budget, same 25% add-cap. A ⚪
   row with 🎯 but NO 🐳 stays a no — the level alone tested WORSE than
   plain dip-buying; it's the footprint that carries the edge.
7. Close the app. Do not look at prices until next month.

*Patience calibration (#107, measured 2026-07-18): an ⭐ window is a
**moment**, not a campaign — the median completed ⭐ spell lasts 2 weeks
(p90 5w; 1,295 spells, both universes), while Danny's own accumulation
campaigns run 3 months to a year. His campaign length is built from
repeated visits to the zone, which is exactly what this monthly routine
does — so a closed ⭐ window is never a missed bus, and stretching one
add across many extra tranches inside a single window has no measured
basis: the window will usually be gone before the tranches are.*

---

## 4 · 🐻 BEAR PLAYBOOK — prescriptive steps

**Trigger:** the digest banner reads 🐻 BEAR. Nothing else is a trigger —
not headlines, not a red week, not a feeling. (The banner fires when both
SPY and QQQ close a MONTH below their 10-month average. It fires a handful
of times per decade.)

**Know before it happens:** the signal typically fires after the market is
already down 10–15%. It will feel late. It is still worth following — its
value is avoiding the −40…−80% middle, not the first −15%.

**What this insurance costs — measured, not asserted (D-63, 2026-07-10):**
across 33 years spanning the dot-com grind, 2008 and 2022 (survivor-biased
high-beta basket), following these exact steps returned 20.4%/yr vs
21.3%/yr for never-selling — roughly **−1 pt/yr and one-third less final
wealth — in exchange for cutting the worst peak-to-trough from −76% to
−29%.** In a V-shaped bear the premium is much bigger: the 2022 episode
cost ~7 pts/yr over its surrounding 5-year window, and most of that cost
came from the *recovery* months (hold-through kept averaging into crushed
satellites; this protocol re-enters in thirds). False alarms AND V-bears
are the premium; the −70% grinders are what the policy exists for. If you
are certain you would sit through −76% without capitulating or needing the
money, hold-through earns more — but that certainty is exactly what §8
says most people don't have.

**No half-measures:** "I'll just pause adds but not sell" tested as the
worst of both worlds (D-63 mode c): it kept the entire −76% grinder
drawdown AND still gave up return in the V-window. Follow the steps below,
or consciously choose hold-through — don't improvise a blend in the
moment.

**The steps, in order (you have days, not minutes — it's a monthly signal):**

1. **Do not touch anything on the day you see it.** Sleep on it once. The
   signal is unchanged tomorrow.
2. **Margin first.** If any margin loan exists (it shouldn't — §6), sell
   satellites until it is zero. Nothing else happens before this.
3. **Sell satellites (Bucket C), in this order:**
   a. everything in ⚪ CAUTION with weak fundamentals (F:0–1) — all of it;
   b. everything else in ⚪ CAUTION — until satellites total ≤10% of book;
   c. keep any satellite still ⭐/🟢 (rare in a real bear) if you wish.
4. **Do NOT sell Bucket A. Do NOT sell Bucket B** (earned cores with real
   businesses). Write down today: *"I accept my earned core may fall 50%
   and I will not sell it."* If you can't sign that, the position is too
   big — trim it to where you can, NOW, in the bull.
5. **Proceeds = dry powder.** Park in cash/T-bill MMF. It is earmarked for
   stocks, not for spending.
6. **Keep the monthly routine running** — but step 4 of §3 changes: the
   stock half also goes into Bucket A while 🐻. You are buying the index
   through the entire bear. This is where bear-market wealth is actually
   made, quietly.
7. **Re-entry:** when the banner returns to 🐂, redeploy the dry powder into
   ⭐ names **in thirds over three months** (first month ⅓, second ⅓, third
   ⅓). Never all at once — first signals whipsaw.

**What the signal cannot do (accept in advance):** a COVID-style crash is
over before a monthly signal reacts — your protection there is position
sizing, not the signal. And expect 1–2 false alarms per decade: you'll sell
satellites, market recovers, you re-enter slightly higher. That's the
premium on the insurance, not a malfunction.

---

## 5 · Trim rules — the ONLY three reasons to sell a stock in a bull market

1. **Size, not earned:** a position bought (not grown) above 25% of the
   stock book → trim back to 25%, proceeds to ⭐/index. *(A grown position
   gets a pass — see Bucket B — but its adds stop at CAUTION. Threshold
   moved 10→25 with the #92 cap promotion, 2026-07-12; it reverts with
   the cap if the demotion rule fires.)*
2. **Broken business, not just broken chart:** in ⚪ CAUTION for 8+ weeks
   **and** fundamentals failing (profit check failed / F:0–1) → sell half,
   set a note to review the remainder in one quarter. A broken chart with a
   healthy business (F:2+) is a drawdown; a broken chart with a broken
   business is how "temporary" becomes permanent. *(Measured, D-63 mode f,
   2026-07-10: on the wreck-salted 2021 control this rule — tested without
   even its F-gate — beat holding-everything by ~3 pts/yr over 10y, because
   it's what gets you out of the PTON/ZM class. It is a return protector on
   broken names, NOT crash insurance: it kept the full −79% grinder
   drawdown. §4 is the insurance; this is the trash-taker.)* *(Threshold
   moved 12→8 weeks on 2026-07-22 by the #51 calibration — `homily_
   timestop_backtest.py`'s pre-registered grid, run 2026-07-17 and
   re-run 2026-07-22 on rolled data, put ~8wk ahead of the declared ~12wk
   on both honest-control windows at equal-or-better drawdown. Read the
   honest limit with it: on the 10y control the whole engine still LOSES
   to QQQ-DCA (2.69 vs 2.86 MOIC at −62% vs −34% drawdown) — this change
   narrows that gap, it does not close it. promotions.json
   "timestop-8wk" carries the demotion rule; it reverts to 12.)*
3. **You need the money, or margin exists** *(margin on the CORE book,
   that is — LEVERAGE.md (2026-07-12) governs the regime-gated swing
   ladder separately; the core monthly book still never carries margin)*.

**Never trim** a Bucket-B compounder in RED/uptrend because it "got big by
itself" — that is the entire engine of this method. (It's also exactly the
Pop Mart lesson in reverse: the problem was never that a winner grew; it
was adding size to a name whose trend had broken.)

---

## 6 · Margin policy: zero on the core book. Always.

Floating mortgage + margin loan + concentrated stocks is the one
configuration that can end the compounding permanently (a margin call in a
bear forces you to sell Bucket B at the bottom — the unrecoverable error).
Legacy margin is cleared **now, in the bull, from strength** — before the
first dollar of new DCA. The backtested strategies in this repo assume
zero leverage; with margin, their −30% drawdowns become forced
liquidations.

*(Amended 2026-07-12: LEVERAGE.md governs the ONE sanctioned exception —
the ring-fenced swing sleeve of §9, regime-gated BULL ≤1.30× / MIXED
≤1.15× / BEAR margin-zero, sized so even its total loss is a bounded
"cost of business". Buckets A/B/C — the core book — never carry margin;
that is arithmetic (BACKTEST_RESULTS §15's core-ban table), not
preference. The sleeve arms only after the legacy loan is cleared.)*

---

## 7 · How much to DCA

```
monthly investable =
    income
  − living expenses
  − mortgage payment + buffer while rates float
  − margin paydown (until zero — this outranks investing)
  − emergency fund top-up (until 6 months of expenses)
```
Whatever remains: **50% Bucket A / 50% ⭐ routine** (§3). SRS counts as
the Bucket-A half while its contributions are actually invested. If a −50% month on
the stock half would make you break the rules, shift the split toward A
until it wouldn't. The split you can hold through a bear beats the split
that's optimal on paper.

*Once a quarter the swing sleeve's flywheel skim (§9 / #95) adds to this
month's investable on top of the formula above — it prints as "+ swing
skim US$X" in the 🛒 BUY DAY block. Deploy it through the same §3 routine;
it is proceeds from the experiment, never borrowed, and a losing quarter
adds nothing.*

---

## 8 · Honest expectations (read once a year)

- The 2026-07-10 multi-window re-test (BACKTEST_RESULTS.md §3) says it
  plainly: on construction-honest windows the method **beats the S&P more
  often than not, does NOT reliably beat QQQ**, and carries 2–3× the index
  drawdown. What it measurably provides instead: the §5.2 exit's edge on
  broken names, §4's priced crash insurance, and the discipline to keep
  investing. No tool can promise index outperformance; anyone who does is
  selling something.
- The compounding math is brutal about one thing: **at realistic returns,
  the savings rate matters more than the strategy.** Doubling your DCA
  reliably beats any indicator improvement we will ever ship.
- The system self-improves daily (out-of-sample-gated refine), the
  strategy re-test re-runs every July, and the improvement backlog lives in
  PRD.md §6. Expect evolution, not miracles.

### 8.1 · Owner target (set 2026-07-24) — S$2,000,000 before turning 40 (2032)

**The number:** S$2M household net worth — the #94 household-scorecard
figure (core + SRS + ESPP + swing − margin, in SGD) — before the owner's
40th birthday in 2032. *(This line is ROADMAP #119's dated trigger.)*

**The arithmetic, priced the day it was set** (so nobody re-derives it
softer later): from ~S$50k and ~S$3.5k/mo, hitting S$2M by 2032 requires
**~60%/yr compounded for six straight years** — beyond every documented
public-market track record. Even at a heroic sustained 20%/yr the gap
needs ~S$15.5k/mo saved; at a normal-good 12%/yr, ~S$19.5k/mo. The
owner's own conclusion, recorded verbatim in spirit: *it's a savings
problem, not an investing problem — the real lever is a better-paying
job, held for a long time.*

**So the target is assigned to the savings lever, and ONLY that lever:**

- The tracked variable is **monthly contributions** (contributions.json /
  the #94 block), not the book's return. Raising S$3.5k/mo toward
  S$6–8k/mo as income grows moves the 2032 number more than anything in
  the alpha program.
- **This target changes no investing rule. Ever.** It never justifies
  core margin (§6), cap breaches, off-zone adds, or sizing beyond the
  ladder — the 2026-07-16 episode is the named failure mode of chasing a
  number, and it was chasing far less than this. A target that needs 60%
  makes discipline feel like failure; that feeling is the signal to
  reread this section, not to trade.
- **Checkpoint, not summit:** ~S$600–700k by the 40th birthday (growing
  contributions + strong-but-real returns) keeps S$2M on track for
  ~age 46–48 with no rule ever bent. The multibagger right tail (§8
  bullet 1 notwithstanding, it exists) can pull that forward; it is
  never load-bearing.
- The monthly #94 household block is the referee; progress is read
  there, in SGD, against the same QQQ counterfactual as everything else.

---

## 9 · The swing sleeve — LIVE, levered, 5 minutes a week (#93 / A5)

The one levered book. Ring-fenced experiment money: **US$3,000
contributed** (top-ups allowed, total ≤10% of net liq, each recorded).
Proceeds fund the monthly DCA; losses are the recorded cost of business.
The bot decides and prints; **you place every order** — nothing is
automated.

**Before it starts (once):** clear the legacy margin loan, then set the
`MARGIN_ZERO` repo variable. The first order sheet prints the Saturday
after. Until then the digest says "waiting for the clean slate."

**The weekly routine (Monday morning, ~5 minutes):**
1. Open Saturday's ♟️ weekly digest. Find the **ORDER SHEET**.
2. Place exactly what it says: for a BUY — market order, then the GTC
   STOP (−20%) and the GTC LIMIT sell for half (+40%) at the printed
   prices. For a SELL — market, and cancel that name's GTC orders.
3. Close the app. **Never move a stop or TP between sheets.** Adjustments
   happen only when a re-rank sheet says so — that is the pre-commitment
   that keeps this from becoming day-trading.

**What the machine does for you:** sizes every entry to the LEVERAGE.md
ladder (BULL 1.30× / MIXED 1.15× / BEAR = flat, margin zero) · mirrors
the S1 rotation (4-weekly re-ranks) · enforces the 12-week time stop ·
marks the book every Friday · reports **realized P&L monthly** in the
daily digest, per trade, with the reason (STOP / TP / TIME / ROTATE /
REGIME / KILL) · keeps a hash-chained journal of every decision.

**The flywheel — how proceeds actually reach the DCA (#95):** once a
quarter (the first weekly run of Jan/Apr/Jul/Oct) the machine banks the
sleeve's profit above your contributed capital as a **skim**: a 💧 line
prints on the order sheet and again in that month's 🛒 BUY DAY block
("+ swing skim US$X"). **You move that cash** from the swing account into
the monthly DCA and deploy it with the normal §3 routine — the skim is
extra money on top of `BUY_BUDGET`, not a change to how you split it.
Only *realized* profit is ever skimmed (never principal, never a forced
sale); a quarter that ends below your contributed capital skims **US$0**,
and that is correct — a red quarter pays nothing (no borrowing to fake a
steady payout). The skim is measured, not guessed: the monthly report
shows cumulative banked skims and the sleeve's true score (equity + all
skims vs contributed). **Skims never move the kill line** — banked money
leaves the book, so the experiment must always survive on what remains.

**The kill rules (pre-registered, mandatory, not a discussion):**
- **KILL-A — the "too huge" number: equity ≤ 70% of contributed capital**
  (on US$3,000: a US$900 total loss). The sheet says LIQUIDATE, you
  liquidate, the experiment is over and declared a failure in writing.
- **KILL-B: expectancy ≤ 0 over the trailing 20 closed trades** — a
  system that loses on average has no business borrowing money. Same
  ending.
- **Any margin call, any size** → LEVERAGE.md §5 already answers: ladder
  to 1.00× permanently pending post-mortem.
- No restart after a kill without a brand-new gated design and a signed
  amendment. "One more try" is how experiments become habits.

**Honesty box (why this is an experiment, not a strategy):** the P2 paper
gate was overridden by the owner (A5) — this book runs on ~2 days of
paper history, not the 26 weeks the gate asked for. The stops it carries
FAILED the backtest (S1-stopped: 0/3 windows; KILL_MEMO) — they are here
to bound losses, not to add return, and the paper S1-pure book runs
beside this one as the no-stops counterfactual so we measure exactly what
they cost. Fills in the report are modeled (Monday opens, trigger
prices); reconcile against IBKR statements monthly.

*Everything in this file is pre-commitment, not prediction. The edge is
discipline; the indicators just tell you where to point it.*
