# GAMBIT EXECUTION — start here (entry point for the executing model)

> **QUEUE STATE (2026-07-11): P2 PAPER — S1-pure promoted by Amendment A4.**
> Phase 1 (G-S1…G-S4) scored no arm promotable under the original stop
> directive (KILL_MEMO.md). The owner then rescinded that directive for
> S1-pure — which cleared the gate on 2/3 windows — accepting its
> stop-free −40…−46% drawdowns in writing (AMENDMENT_A4.md). **G-S5
> (paper loop + journal) is now BUILT against S1-pure.** Next queue items:
> **G-S6** (schedule + monthly report) and **G-S7** (dark MCP orders),
> each its own session. S1-stopped/S2/S3 stay FAILed. `LIVE_ORDERS`
> stays `off`.

Read the queue item, restate its gate, build it, `gambit_validate.py`
green, commit. One item per session. PRD.md is the constitution;
DESIGNS.md holds the specs referenced below.

## 0. Prime directives (violating any of these fails the session)

1. **Paper only.** `LIVE_ORDERS` never leaves `off`/`dry`. No real
   order is ever placed. Validate [K6] enforces; build it early.
2. **No margin, even simulated** — paper cash ≥ 0 always.
3. **Pre-registration is law.** DESIGNS Part II froze the backtest
   protocol; changing arms/windows/costs/thresholds requires a logged
   amendment, never a silent edit.
4. **No look-ahead.** Signal on close T → fill at open T+1. Dates come
   from bar timestamps (US session date), never local `now()`.
5. **Copy from homily-bot, never import it.** Ported code brings its
   tests along.
6. After the first journal row exists: engine freeze (SHA manifest,
   homily #61 pattern), one promoted change per quarter.

## 1. Session queue

| # | Item | Gate (restate before coding) |
|---|---|---|
| G-S1 | Bootstrap: port `homily_data.py` fetch → `gambit_data.py` (host rotation, backoff, epoch params, **non-daily-bars refusal** — the validate-[22] bug class); bars-contract tests; `gambit_validate.py` skeleton with [K6] LIVE_ORDERS check; pytest layout; CI workflow running validate only. Prereq: create private GitHub remote (`gh repo create`). | validate green in CI on the remote; a deliberately-broken bars fixture fails the contract test |
| G-S2 | `gambit_universe.py` per DESIGNS D-G2 (NASDAQ Trader source, filters, top-120, quarterly refresh, `constructed:` stamp, filter trace). | universe.json builds deterministically from a fixture snapshot; live build produces 100–140 names; stamp present |
| G-S3 | `gambit_backtest.py` harness: portfolio accounting, cost model (0.25%/0.35% RT), benchmark arms (QQQ/SPY B&H, equal-weight, 200 seeded random-5), point-in-time eligibility. NO strategy arms yet. | random-arm p10/p50/p90 reproducible under fixed seed; QQQ B&H MOIC matches an independent hand-check within 1% |
| G-S4 | Strategy arms S1-pure / S1-stopped / S2 / S3 (vol-hole breakout — port `homily_vol.py` per DESIGNS D-G3b, incl. its one-cluster-one-breakout parsimony fixture) + the D-G3 exit stack; run the full Part-II protocol (incl. Amendment A1); write `BACKTEST_RESULTS.md`; score the gate mechanically. **Then STOP — do not build the paper loop in the same session.** Owner + Fable read the results first. | every pre-registered cell filled; gate verdict stated as PASS/FAIL per candidate with zero editorializing |
| G-S5 | *(only if G-S4 passed a candidate)* Paper loop: `weekly_run.py`, simulator with D-G3 fill model, `gambit_journal.csv` + hash guard + snapshot.json, digest + golden tests (build goldens BEFORE first send — homily #49). | golden tests pin the digest; journal survives an append-only tamper test; simulated week replays deterministically |
| G-S6 | Schedule + reporting: weekly Sat job, daily Tue–Sat stop-monitor job, state-change-only alerts (#15 pattern), monthly report generator → `PAPER_RESULTS.md` + digest (DESIGNS D-G6 §6-part format incl. K1–K6 dashboard). **Prereq: owner-created dedicated Telegram bot; `TELEGRAM_BOT_TOKEN` + `TELEGRAM_CHAT_ID` secrets on this repo (owner decision 2026-07-10 — NOT homily's bot).** Paper fills are auto-approved per Amendment A2 (PRD §5.1). | validate gates the send (red test = no send, no commit); a fixture month renders the full report incl. kill-condition dashboard |
| G-S7 | `gambit_orders.py` dark: render exact IBKR MCP `create_order_instruction` payloads in `dry` mode, journal them, never send; LIVE_ENABLE.md two-artifact gate per DESIGNS D-G1. | payloads logged for a fixture week; [K6] fails the build when flag forced `on` without LIVE_ENABLE.md |

After G-S7 the build *would* have entered steady-state P2 — but only on
a passing candidate. **That path did not open.** G-S4 (2026-07-10)
passed none; the leverage question (2026-07-11, LEVERAGE_MEMO.md) did not
change that; Phase 1 is closed by KILL_MEMO.md. The engine freeze
(§0.6) never armed — it triggers on the first journal row, and no row
ever accrued — so the harness stays editable for a future hypothesis.
Next Fable items are no longer G-S5+: they are (a) an optional
`docs/OPTIONS_101.md` (D-G4, owed during any paper phase — moot until one
exists) and (b) whenever the owner brings one, registering a NEW arm per
KILL_MEMO §8 to re-open Phase 1 against the same unchanged gate.

## 2. Execution traps (learned the hard way in homily)

* **Yahoo returns monthly bars for long ranges while claiming 1d** —
  the ported refusal guard + test is non-negotiable (G-S1).
* **TZ drift (homily R7):** one date helper keyed to bar timestamps,
  pinned by test BEFORE the first journal row.
* **Workflow order (homily R5/#16):** validate → run → commit. Never
  let a job mutate state or send before tests pass.
* **Goldens are regenerated deliberately** (`--update` flag + eyeball),
  never as a side effect.
* **The random benchmark is the referee.** If a strategy arm can't beat
  the p90 band, the finding is luck — that filter already killed a
  scoring model once (homily #24, conviction score).
