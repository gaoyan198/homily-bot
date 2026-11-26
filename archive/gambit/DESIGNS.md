# GAMBIT DESIGNS — deep specs behind PRD v0.2 (2026-07-10)

Read PRD.md first. This file is Fable output for the executing model;
Part III is the handoff contract. Nothing here authorizes real orders.

---

## Part I — resolved-decision designs

### D-G1 · Paper-first + the LIVE_ORDERS gate

* Paper book: notional **US$20,000**, cash-only (simulator refuses any
  entry that would take cash below zero — G7 applies to paper too).
* `LIVE_ORDERS` is a tri-state read at startup: `off` (default, only
  value that exists in P2) / `dry` (format + log MCP payloads, never
  send — this is what P2 actually runs) / `on` (P3+, forbidden for now).
* `on` requires **both** an env flag **and** a committed
  `LIVE_ENABLE.md` containing an owner-written line with date and
  initial. Validate check **[K6]** fails the build if the flag is `on`
  without that file, and ALSO fails if the file exists while the PRD
  still says P3 is deferred — flipping live is a deliberate two-artifact
  action, not a config edit.
* The MCP path (`gambit_orders.py`) is built in G-S7 and exercised every
  week in `dry` mode: it renders the exact
  `create_order_instruction` payload (symbol, LIMIT price, qty, TIF=DAY)
  and writes it to the journal. When live day comes, zero new code —
  only the gate flips.

### D-G2 · Mechanical US universe (construction date = first build day, stamped)

* Source: NASDAQ Trader symbol directory (`nasdaqlisted.txt` +
  `otherlisted.txt`) — same base as homily D-65.
* Filters, in order: common shares only (drop ETFs, units, warrants,
  preferreds, test issues, SPAC shells by name heuristics) → last close
  ≥ **$10** → 20-day median dollar volume ≥ **US$25M** → keep the top
  **120** by 6-month median dollar volume.
* Refresh **quarterly** (first weekly run of Jan/Apr/Jul/Oct); adds and
  drops are journaled. A dropped name with an open position keeps being
  tracked until the position exits (no forced sale on universe churn).
* File: `gambit_universe.py` writes `universe.json` with
  `constructed: <date>` and the full filter trace per symbol.

### D-G3 · Exit stack + honest paper-fill model (pre-registered — do not tune)

Defined at entry, written to the journal BEFORE the simulated fill (K4):

| Layer | Rule |
|---|---|
| Initial stop | entry − 2×ATR(14). 1R ≡ that distance. |
| Take-profit | at +2R: close **half**; remainder trails |
| Trail | higher of (initial stop, rolling 20-day low), ratchets up only |
| Time stop | close of the 8th week in position, unconditional |
| Regime | 🐻 flip (QQQ weekly close < 40-week MA, two consecutive weeks) → close everything at next open; re-entry in thirds over 3 weeks after flip-back — the D-63 "no half-measures" rule |

Fill model (no fiction, gaps hurt like they do in life):

* Signals computed on day T's close → fills at day T+1's **open**.
* Stop breach: if T+1 opens below the stop, fill at the **open** (gap
  taken in full); else if the day's low touches the stop, fill at the
  stop.
* TP mirror-image (gap up through TP fills at open).
* Costs: **0.125% per side** (commission+spread+slippage proxy; 0.25%
  RT as per PRD §4; stress arm 0.35% RT).
* Position sizing: risk-parity on R — size = (0.75% of sleeve equity) /
  1R distance, capped by PRD's 40%-of-sleeve and 2-per-cluster limits.
  (0.75% risk/trade × ~6 positions ≈ 4.5% open risk — conservative;
  revisit only via a gated change.)

### D-G3b · Vol-hole detector port (S3's setup input)

Copy `homily_vol.py` (do not import): hole day = new 60-day low in
relative volatility (ATR5/close); consecutive hole days cluster; the
zone = cluster high/low, valid until closed through on either side.
S3 entry trigger = first daily close above the upper bound with volume
> 1.5× its 20-day median. Close below the lower bound = `VOLHOLE_BREAK
DOWN` journal row, **no trade action** (homily 5b: breakdowns don't
predict weakness). Port the module's tests; add a fixture where the
same bars produce exactly one cluster and one breakout — the parsimony
check that the detector doesn't spray signals.

### D-G4 · Options sleeve — parked

Owner is interested but knows nothing about options. During P2 Fable
writes `docs/OPTIONS_101.md`: plain language, covered calls +
cash-secured puts only, worked examples on names the owner holds,
assignment/exercise mechanics, why premium is not free money, what the
suits on the other side of an option actually price. **No option code,
no option backtests, before the owner has read it and said go.**

### D-G6 · Journal (= ledger) schema + the monthly report

`gambit_journal.csv`, append-only, SHA-256 checkpoint over prior rows
(homily #62 pattern), one row per event:

`date · event(SCAN|PROPOSE|FILL|STOP|TP|TRAIL|TIME|REGIME|SKIP) ·
symbol · side · qty · price · stop · tp · r_distance · reason_code ·
rank_rs · regime · equity_after · notes`

Plus per-closed-trade derived rows: R-multiple, holding days, MFE/MAE
(max favorable/adverse excursion, for exit-quality review).

**Monthly report** (owner-facing, generated by the first weekly run of
each month; appended to `PAPER_RESULTS.md` + sent via digest channel):

1. Verdict line: month P&L in $ and R; equity vs same-dollar QQQ and SPY
   since inception (the bar, PRD §1).
2. Closed trades table (entry/exit/R/reason).
3. Open book with current stops/TPs and days-in-trade.
4. Expectancy (trailing 20 trades), win rate, avg win/loss, MaxDD.
5. **Kill-condition dashboard K1–K6, each 🟢/🟡/🔴** (PRD §5.3).
6. One paragraph, plain words: what the system did and why — written
   for the owner's 2-minute read, not for the machine.

### D-G7 · Runtime + schedule

* Private GitHub repo + Actions (prereq: owner or Opus creates remote
  via `gh repo create`, same account as homily).
* **Weekly job** — Saturday 10:00 SGT: fetch, universe check, rank,
  regime, generate proposals + digest (validate gates the send — homily
  #16 pattern: red test = no digest, no commit).
* **Daily job** — Tue–Sat 09:30 SGT (after US close): mark stops/
  TP/time-stops against the paper book, journal any simulated exits,
  alert **only on state change** (homily #15 pattern). Zero owner load.
* Date discipline (homily R7 lesson): every row keyed to the **US
  exchange session date taken from the bar timestamps**, never local
  `now()`. One helper, one test, pinned before row 1 accrues.
* Telegram: **dedicated GAMBIT bot** (owner decision 2026-07-10,
  reversing the same-bot default): owner creates it via @BotFather and
  sets `TELEGRAM_BOT_TOKEN` + `TELEGRAM_CHAT_ID` secrets on the gambit
  repo before G-S6 ships. "♟️ GAMBIT" message prefix kept. Full channel
  separation from homily from day 1.
* Paper approvals (Amendment A2, 2026-07-10, owner decision): the
  weekly digest is informative, not blocking — paper proposals
  auto-fill Monday open unless vetoed before Monday. Per-order
  approval is a P3/live behaviour.

---

## Part II — Phase-1 backtest protocol (pre-registered 2026-07-10, BEFORE any harness code exists)

**Survivorship honesty (the construction-date rule, hardest case):** a
mechanical universe built in 2026 from *current* listings cannot see
2018's delistings — every historical window is survivorship-flattered,
and unlike homily's curated list there is no pre-2026 construction date
to hide behind. We cannot fully fix this without point-in-time listings
data. Pre-registered mitigations, all three mandatory:

1. Universe membership at each window start is recomputed **point-in-time
   over fetchable names** (gates applied using only data before the
   window; a name with no bars then simply isn't eligible yet).
2. The gate demands a **margin**, not a tie: beat QQQ B&H by ≥ **+0.10
   MOIC** per qualifying window (a tie under survivorship bias is a
   loss).
3. The backtest verdict is explicitly labeled *upper bound*; **the paper
   ledger is the real test** and P2's own gate (PRD §5.2) does not
   inherit any credit from P1.

**Arms** (identical accounting, identical exit stack where marked):
S1-pure (rotation exit only) · S1-stopped (rotation + D-G3 stack —
the only promotable S1) · S2 pullback · S3 vol-hole breakout (per
Amendment A1) · QQQ B&H · SPY B&H · equal-weight-universe monthly ·
200 seeded random-5 draws.

> **Amendment A1 (2026-07-10, before G-S3 began — logged per the freeze
> rule):** owner directed clean, sparse signals with the volatility-hole
> → resolution pattern as the setup archetype. S3 redefined from plain
> new-high breakout to **vol-hole breakout** (contraction cluster → close
> above zone upper bound + volume, RS-top-decile names), grounded in
> homily's §5b event study (breakouts +11.5% vs +8.5% baseline fwd 60d;
> breakdowns did NOT predict weakness → journal-only warning, never a
> trade signal). PRD §4.1 signal-parsimony rules added: ≤3 orthogonal
> inputs per arm, one-in-one-out, event-study before admission, quiet
> weeks are valid output. No other protocol cell changed.

**Windows:** rolling 5-year starts every Jan from 2015, plus the two
10-year windows — same shape as `homily_multiwindow_backtest.py`.

**Gate (restated from PRD §4, margin added):** a candidate is promotable
iff on ≥2 of the 3 most recent 5y windows it (a) beats QQQ B&H MOIC by
≥ +0.10, (b) beats QQQ on MAR (CAGR/MaxDD), (c) sits above the random
p90, and (d) still clears (a)–(c) at 0.35% RT stress. No candidate →
kill memo, project stops (PRD §5.2).

**Decision rule freeze:** this section is the registration. Any change
to arms, windows, costs, or thresholds after G-S3 begins must be logged
in BACKTEST_RESULTS.md as a protocol amendment with a reason — silent
edits are a K4-class integrity breach.

---

## Part III — execution handoff (Fable plans, Opus executes)

Inherited verbatim from homily EXECUTION.md culture:

1. One queue item per session, in EXECUTION.md order. Open EXECUTION.md
   first, restate the item's gate before writing code.
2. `gambit_validate.py` green before every commit; validate gates the
   send in CI from the first workflow.
3. Golden-file tests for the digest before the digest ships (homily #49
   pattern).
4. After the first journal row accrues, engine files freeze (SHA
   manifest in validate, homily #61 pattern); changes only via a gated
   session, max one promoted behaviour change per quarter (R10).
5. Never promote a signal in the session that builds it.
6. Copy homily modules, don't import them — the repos must not couple.
