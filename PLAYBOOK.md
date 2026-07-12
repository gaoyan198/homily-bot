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
   exceed 10% of your stock book.
   *(#24 promoted 2026-07-12 — by owner override, AHEAD of its live
   forward-check; the check keeps publishing at each month-start through
   2026-10 and a FAIL demotes this back to equal-split-max-5 mechanically
   (promotions.json). The 10% cap is priced, not gut — #67,
   BACKTEST_RESULTS §12: it cost ~0.05 MOIC per $1 on the honest
   2021→2026 control (essentially free) and pays +0.26…+0.40 MOIC when
   the book's biggest name gaps −80…−95% and never recovers. It exists
   for the gap-down the trend gate can't see; wrecks lose ⭐ long before
   they reach 10%, so in practice it binds on winners — that is the
   premium you're paying.)*
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
   the account per name**, same monthly budget, same 10% hard cap. A ⚪
   row with 🎯 but NO 🐳 stays a no — the level alone tested WORSE than
   plain dip-buying; it's the footprint that carries the edge.
7. Close the app. Do not look at prices until next month.

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

1. **Size, not earned:** a position bought (not grown) above 10% of the
   stock book → trim back to 10%, proceeds to ⭐/index. *(A grown position
   gets a pass — see Bucket B — but its adds stop at CAUTION.)*
2. **Broken business, not just broken chart:** in ⚪ CAUTION for 12+ weeks
   **and** fundamentals failing (profit check failed / F:0–1) → sell half,
   set a note to review the remainder in one quarter. A broken chart with a
   healthy business (F:2+) is a drawdown; a broken chart with a broken
   business is how "temporary" becomes permanent. *(Measured, D-63 mode f,
   2026-07-10: on the wreck-salted 2021 control this rule — tested without
   even its F-gate — beat holding-everything by ~3 pts/yr over 10y, because
   it's what gets you out of the PTON/ZM class. It is a return protector on
   broken names, NOT crash insurance: it kept the full −79% grinder
   drawdown. §4 is the insurance; this is the trash-taker.)*
3. **You need the money, or margin exists.**

**Never trim** a Bucket-B compounder in RED/uptrend because it "got big by
itself" — that is the entire engine of this method. (It's also exactly the
Pop Mart lesson in reverse: the problem was never that a winner grew; it
was adding size to a name whose trend had broken.)

---

## 6 · Margin policy: zero. Always.

Floating mortgage + margin loan + concentrated stocks is the one
configuration that can end the compounding permanently (a margin call in a
bear forces you to sell Bucket B at the bottom — the unrecoverable error).
Margin is cleared **now, in the bull, from strength** — before the first
dollar of new DCA. The backtested strategies in this repo assume zero
leverage; with margin, their −30% drawdowns become forced liquidations.

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

*Everything in this file is pre-commitment, not prediction. The edge is
discipline; the indicators just tell you where to point it.*
