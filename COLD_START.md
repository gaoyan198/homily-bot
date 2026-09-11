# COLD START — from a fresh clone to a verified run, no memory assumed

**Item:** #115 (ROADMAP §5) · **Written:** 2026-09-11, from a drill actually
run that day (log in §10) · **Re-drilled:** every July, by a session with NO
prior context of this repo — a new model, preferably. The drill's rule:
**every failure patches THIS file in the same session**, never the
drill-runner's memory. If you are the July runner, start at §10.

This is the operator's manual for the day nobody who built the system is
around. It assumes: a machine with git and Python, a terminal, and this
file. It does not assume you know what Homily, Danny, a chip histogram or
a 🐻 regime is — those are in the reading order (§8), and you do not need
them to get to a green run. What you must produce, in order:

1. a green self-test (`homily_validate.py` — checks numbered to [82] as of 2026-09-11);
2. a daily digest printed locally, no secrets;
3. one buy-day order sheet (a rehearsal — any day of the month);
4. the swing sleeve's own self-test green;
5. (restore path) the digest and one backtest reproduced from the bars
   vault with the network off.

Everything below was executed in order on 2026-09-11 on macOS / Python
3.14.6 from a clone with no local state. Timings are from that run.

---

## 1 · Prerequisites

| Need | Why | Check |
|---|---|---|
| git | the repo IS the state (ledger, books, vault) | `git --version` |
| Python ≥ 3.12 | CI runs 3.12; 3.14 verified locally 2026-09-11 | `python3 --version` |
| **nothing else for the core book** | pure standard library — no `pip install`, by design (ROADMAP §4: every dependency is a ten-year liability) | — |
| `pytest` — for the swing sleeve's validate ONLY | `gambit/gambit_validate.py` runs its suite under pytest; CI does `pip install pytest` | see §4 |
| outbound HTTPS to `query1/query2.finance.yahoo.com` | the tape | the daily run tells you if not |
| optionally `api.nasdaq.com` | #114 failover source (US names) the day Yahoo fails | — |

No account, no API key, no broker connection is needed to get to a green
run. Secrets only matter for the *scheduled* run on GitHub (§6).

## 2 · Clone and self-test (≈1 minute)

```
git clone https://github.com/<owner>/homily-bot.git
cd homily-bot                      # ~56 MB .git, ~125 top-level files
python3 homily_validate.py         # expect: "All structural assertions passed."
```

2.9 s on the drill machine. Every line prints `[n] … PASS`; the last line
is the sentence above. **A red validate means stop** — this is the same
gate CI runs before any digest is sent (EXECUTION.md R5), and nothing in
this file is worth doing on a red tree. If it is red on a fresh clone of
`main`, `main` is red: look at the last `merge` commits, and at
`.github/workflows/homily-daily.yml`'s recent runs.

## 3 · The daily digest, locally (≈20 seconds)

```
python3 daily_run.py
```

With no `TELEGRAM_*` environment it prints the whole digest to stdout and
logs `[no TELEGRAM_* env — printed only]` and `[chart rendered … not
sent]` — nothing is sent anywhere. 16 s on the drill machine (≈200 Yahoo
fetches, 4 workers). The first lines are the market regime banner
(`🐂 REGIME: BULL …`) and the crypto regime board; the block you will care
about most, `⏳ SETUP`, lists which owner switches are unset (§6).

**A local run WRITES state.** It appends today's rows to
`homily_signals_log.csv`, a row to `homily_refine_log.csv`, and rewrites
`docs/snapshot.json` + `docs/dashboard.html` — exactly what CI commits every
weekday. **Do not commit a local run.** Either run in a throwaway clone
(what the drill does) or reset afterwards:

```
git checkout -- homily_signals_log.csv homily_refine_log.csv homily_ledger_hash.json docs/snapshot.json docs/dashboard.html
git status                          # must be clean before you commit anything else
```

Why it matters: the ledger is the live track record the whole
multi-year plan is scored on (ROADMAP §1–§4); a duplicated local row is a
corrupted referee. This was drill finding #2 (§10).

## 4 · The swing sleeve's self-test (≈10 seconds + one pip install)

```
python3 -m venv .venv && .venv/bin/pip install pytest     # or: pip install pytest
cd gambit && ../.venv/bin/python gambit_validate.py        # expect: "gambit_validate: ALL GREEN"
cd ..
```

Without pytest this fails as `pytest suite FAILED — nothing ships` +
`ModuleNotFoundError: No module named 'pytest'` — drill finding #1 (§10).
That is the ONLY non-stdlib requirement in the repo. Do **not** run
`gambit/weekly_run.py` or `gambit/live_run.py` locally unless you mean to
advance the paper/live books by a week — they write the journals
(`gambit/README.md`).

## 5 · One buy-day order sheet (any day, fetch-free, writes nothing)

The live sheet only appears in the digest on the **first run of a
calendar month** (detected from the ledger, not the calendar — `homily_buyday.py`
docstring) and only when the repo variable `BUY_BUDGET_USD` is set. To
prove the money path on a fresh clone on any day:

```
python3 homily_buyday.py --rehearse 2325       # 2325 = the budget in USD, any number works
```

It renders the 🛒 block from the states in the committed
`docs/snapshot.json` (the last CI run's screen), with the same 👁
observation fence and symbol map the live call uses. It prints
`REHEARSAL — … nothing written, not an order sheet` first, writes no
basket CSV, and places nothing — no code path in this repo ever places an
order (PRD §7). The real sheets CI wrote are `docs/orders_YYYY-MM.csv`.
Non-USD names print as `manual: …` (EXECUTION.md R12) — that is correct,
not a bug.

## 6 · Secrets and variables — the complete inventory

GitHub **secrets** are write-only: once set you cannot read them back, so
keep a recoverable copy of each in a password manager. **Variables** are
plain values. Both are set with `gh` (or Settings → Secrets and variables
→ Actions). Everything is optional in the sense that an unset one leaves
the corresponding rail dark and the run green; the `⏳ SETUP` digest line
nags for the ones the owner has said should be on.

| Name | Kind | Used by | Unset = | Notes |
|---|---|---|---|---|
| `TELEGRAM_BOT_TOKEN` | secret | both workflows | digest printed to the CI log only | BotFather token |
| `TELEGRAM_CHAT_ID` | secret | both workflows | same | the chat the bot posts to |
| `IBKR_FLEX_TOKEN` | secret | daily | `holdings.json` stays a manual file (#32) | **expires 2027-06-26** — rotate BEFORE (ROADMAP §6 has the click-path); expiry is silent: CI stays green, only the `📒 book sync` digest line changes |
| `IBKR_FLEX_QUERY` | secret | daily | same | the Flex query id |
| `HEALTHCHECK_URL_DAILY` | secret | daily | no liveness watchdog (#118c) | an external monitor's ping URL; alerts on ABSENCE of the ping |
| `HEALTHCHECK_URL_GAMBIT` | secret | gambit-weekly | same, for the sleeve | must be a DIFFERENT check |
| `BUY_BUDGET_USD` | variable | daily | buy-day copilot dark | monthly cash budget, USD, whole number |
| `SRS_COVERS_INDEX` | variable | daily | index leg funded from the same budget | `true` when SRS is the index leg (PRD §9.4) |
| `MARGIN_ZERO` | variable | both | swing sleeve unarmed; monthly rehearsal nags | owner sets it when the core book carries no margin (PLAYBOOK §6); read by `gambit/live_run.py` too |
| `HOMILY_DELIVERY` | variable (or plain env on a box) | daily | Telegram is the channel | #118a alternate delivery: `file:<dir>` writes the digest + charts + documents as one HTML bundle per day into `<dir>` and never touches Telegram that run. Meant for a box running the job from cron with a synced folder (§7); dormant when unset |

```
gh secret set TELEGRAM_BOT_TOKEN   -b'<token>'
gh secret set TELEGRAM_CHAT_ID     -b'<chat id>'
gh secret set IBKR_FLEX_TOKEN      -b'<24-digit token>'
gh secret set IBKR_FLEX_QUERY      -b'<query id>'
gh secret set HEALTHCHECK_URL_DAILY  -b'<ping url>'
gh secret set HEALTHCHECK_URL_GAMBIT -b'<ping url>'
gh variable set BUY_BUDGET_USD     -b'2325'
gh variable set SRS_COVERS_INDEX   -b'true'
gh variable set MARGIN_ZERO        -b'true'
```

Validate [68] pins the watchdog wiring; [80] the vault step; nothing pins
the secrets' values — the digest's `⏳ SETUP` line and the Telegram
message itself are the only evidence they are right.

## 7 · The schedule, and what runs it

| When (UTC) | Workflow | Does |
|---|---|---|
| Mon–Fri 01:00 (09:00 SGT) | `homily-daily.yml` | validate → #113 vault snapshot (monthly, idempotent) → `daily_run.py` (digest + refine) → commit state → watchdog ping |
| Sun 02:00 | `homily-daily.yml` | `daily_run.py` detects Sunday → fetch-free weekly deep dive (#33) |
| Sat 02:00 | `gambit-weekly.yml` | both validates → paper book → LIVE book + order sheet → commit journals → ♟️ digest → watchdog ping |

Both have a manual **Run workflow** button (`workflow_dispatch`). The
repo is **public**: GitHub disables scheduled workflows after 60 days
without a commit, and the disable takes the button with it. The daily
state commit is what resets that clock; the watchdog exists because a
silently broken run is exactly what stops it (PRD §8.5, 2026-07-25). Do
not add a keep-alive commit — it is a ToS violation and validate [68]
rejects it.

**Running the daily job from any other box** (ROADMAP #118b — the
scheduler can die). The job is one shell line; the YAML adds only the
watchdog ping:

```
cd /path/to/homily-bot && git pull -q && python3 homily_validate.py && python3 daily_run.py \
  && git add -A && git commit -qm "daily refine $(date -u +%F)" && git push -q
```

with `TELEGRAM_*` (or `HOMILY_DELIVERY=file:<synced folder>` for the
#118a channel), and optionally the Flex/budget variables, in the
environment. Cron, Mon–Fri 09:00 local:

```
0 9 * * 1-5  HOMILY_DELIVERY=file:$HOME/Dropbox/homily  /bin/sh -c 'cd $HOME/homily-bot && git pull -q && python3 homily_validate.py && python3 daily_run.py && git add -A && git commit -qm "daily refine $(date -u +%F)" && git push -q' >> $HOME/homily-cron.log 2>&1
```

macOS launchd (`~/Library/LaunchAgents/com.homily.daily.plist`, then
`launchctl load` it):

```
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0"><dict>
  <key>Label</key><string>com.homily.daily</string>
  <key>ProgramArguments</key><array>
    <string>/bin/sh</string><string>-c</string>
    <string>cd $HOME/homily-bot && git pull -q && python3 homily_validate.py && python3 daily_run.py && git add -A && git commit -qm "daily refine $(date -u +%F)" && git push -q</string>
  </array>
  <key>EnvironmentVariables</key><dict>
    <key>HOMILY_DELIVERY</key><string>file:/Users/you/Dropbox/homily</string>
    <key>PATH</key><string>/opt/homebrew/bin:/usr/local/bin:/usr/bin:/bin</string>
  </dict>
  <key>StartCalendarInterval</key><dict><key>Hour</key><integer>9</integer><key>Minute</key><integer>0</integer></dict>
  <key>StandardOutPath</key><string>/Users/you/homily-launchd.log</string>
  <key>StandardErrorPath</key><string>/Users/you/homily-launchd.log</string>
</dict></plist>
```

Both were drilled for real on 2026-09-11 (one launchd-fired run delivering
through the file-drop, then unloaded — nothing left standing; PRD §8.5).
The `git push` needs a credential on the box; without it the run still
delivers, and the state commit waits for the next push from anywhere.

## 8 · Reading order (when you need to understand, not just run)

1. `PLAYBOOK.md` — the plain-English operating manual: buckets, the
   monthly buy routine, the 🐻 bear steps, when to sell, margin zero.
2. `README.md` — signal states, the file map, schedule, setup.
3. `HOW_TO_READ.md` — the chart cards and the dashboard.
4. `EXECUTION.md` — the rules every change obeys (R1–R12), the engine
   freeze. **Read §0 before touching any `homily_*.py`.**
5. `PRD.md` §8 — the backlog: items, gates, §8.5 where reality
   contradicted the plan (newest first — read the top five).
6. `ROADMAP.md` — the multi-year arc and the three pre-registered verdict
   reads. §3/§4 are hash-pinned (#117): edit them only via
   `python3 homily_verdict.py --repin` + a dated PRD §8.5 note.
7. `DESIGNS.md` Part III — the execution protocol for the model doing the
   work; Part I the deep designs.
8. `BACKTEST_RESULTS.md` — every number ever claimed, and the honest
   ones that lost.
9. `LEVERAGE.md`, `CRYPTO_SLEEVE.md`, `gambit/` docs — the sleeves.

The owner's working split (DESIGNS Part III, the memory this file
replaces): a *planning* model writes designs and gates into PRD/DESIGNS; an
*executing* model builds one item per session, validate green before every
commit, and records contradictions in PRD §8.5 instead of improvising. A
new model reads this file, then EXECUTION.md, then the item.

## 9 · The restore paths (things that will die; ROADMAP §4)

| Death | What happens by itself | What you do |
|---|---|---|
| **Yahoo down for a day** | #114: per name, Nasdaq serves US listings, the vault serves the rest (stale); the digest prints one `📡 SOURCE` line and writes NO ledger/snapshot/refine/alert/dashboard state that day | nothing; read the line |
| **Yahoo gone for good** | same, every day — the ledger stops accruing | set `HOMILY_BARS_SOURCE=vault` to run entirely from the committed vault while a new primary is written into `homily_data.py` behind the same `fetch_series` contract; prove it with `python3 homily_vault.py --drill` |
| **Yahoo rewrites history** | the monthly vault delta detects it and re-vaults the name in full; the digest says so that morning (#113); the daily SPY check against the vault says so the same day (#60) | read the line; the frozen `vault/base-YYYY.json.gz` is the tape as it WAS |
| **Telegram gone** | CI stays green, digest lands in the CI log only | swap the three `send*()` functions in `daily_run.py` — they are the only Telegram code (#118a is the drill for this; not yet run) |
| **GitHub Actions gone / disabled** | watchdog alerts on the missing ping | §7's one-line cron on any box |
| **IBKR Flex token expired (2027-06-26)** | silent: `📒 book sync` line changes, CI green | rotate per ROADMAP §6; `holdings.json` is the manual fallback meanwhile |
| **Danny's feed goes quiet** | nothing changes — no code reads it | the system stands on its own record; that was the point |

Verify the vault restore path from your clone (≈5 min, ~2 of them Yahoo
throttling the live control run):

```
python3 homily_vault.py --check      # every vaulted symbol decodes
python3 homily_vault.py --drill      # expect the last line: DRILL PASS
```

## 10 · The July drill — protocol and log

**Protocol.** A session with no prior context of this repo (new model
preferred; a human stranger is the gold standard) is given ONLY this
file and a clone. It executes §2–§5 and the vault drill in §9, in order,
without asking the owner anything. Every point where it had to guess,
search another file, or hit an error is a **finding**; each finding is
fixed by editing THIS file (or the code, if the doc was right and the
code wrong) in the same session, then the step is re-run. The session
appends a row below. A drill with zero findings is suspicious — say what
was checked.

| Date | Runner | Result | Findings → patched |
|---|---|---|---|
| 2026-09-11 | the item's author (Opus 5, full context — so this proves the MECHANICS, not the docs' sufficiency; the 2027-07 run by a context-free session is the first real test) | validate 2.9 s green (to [82]) · daily run 16 s, digest printed, no send · buy-day rehearsal rendered · gambit validate green after pytest · vault drill PASS from the clone (4:50) | **#1** gambit's validate needs `pytest` — was nowhere in the docs but the workflow → §1/§4. **#2** a local `daily_run.py` silently writes four state files into the tree; an operator would commit them → §3 reset line. **#3** no way to see a buy-day sheet on a fresh clone except on the 1st of a month → `homily_buyday.py --rehearse` built (fetch-free, writes nothing), and its first cut skipped the 👁 observation fence and printed a fenced name (CYPH) → fixed to pass the live fence + symbol map. **#4** the drill itself was run against an uncommitted working tree once (the clone lacked the new flag) → the protocol above says "a clone", and means it |
