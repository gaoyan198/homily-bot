# Archive — shipped PRD §8 phase items (full original text)

Moved verbatim from `PRD.md` on 2026-07-11 (#76 planning-doc pruning).
These items shipped; SPECS.md §0 is the status ledger, this file is the back-story.

<a id="item-13"></a>

13. **Signals ledger** (S) — `homily_ledger.py`: every run appends one row
    per screened name to `homily_signals_log.csv` (committed by the
    workflow like the refine log): date, ticker, held?, close, state, zone
    lo/hi, POC, %-in-profit, weekly circle/score/weeks, monthlyUP, VH
    status, 🐳 bools, conviction score + failed gates, F-tag. Idempotent per
    (date, ticker) — re-runs overwrite, no dupes (the refine log currently
    logs 12 rows on a 12-run day). Also emits `docs/snapshot.json` — full
    structured state for the dashboard track (F) and for Claude sessions to
    answer questions without refetching. Append-only history = point-in-time
    by construction, no look-ahead. Everything in phases C–F consumes this.
    **Gate:** none (pure measurement).

<a id="item-15"></a>

15. **State-change alerts** (#3) (S; needs 13) — diff today's ledger vs
    yesterday's; send a second, tiny Telegram message ONLY on transitions
    (⭐ appears/lapses, 🔵 fires, 🐳 appears, 🐂/🐻 flips, 🚀 enters/exits).
    Quiet day = no second message; the signal stops drowning in the wall.
    **Gate:** none (delivery only).

<a id="item-64"></a>

64. **Universe-entry provenance** (S; ships with or right after 13) — every
    `UNIVERSE` / `WATCH` entry carries an `origin`: `screen` (arrived by a
    mechanical liquidity/G5 rule) or `owner-request` (added on request —
    today: D05.SI, IBIT, ETHA per §5c; arguably the whole pre-#44 list).
    `homily_ledger.py` logs it per row; 14 splits the scorecard by it.
    Rationale: §8.0 makes 14 the referee for every later promotion, but the
    universe is a discretionary list (§5c/§5f — the 3.69 MOIC number is
    hindsight-biased *because* of how these names were chosen). Without the
    field, an ⭐ on an owner-requested name and an ⭐ on a screened name enter
    the live record indistinguishable, and the referee inherits the
    selection bias it exists to detect. Does not make inclusion rule-based —
    that needs point-in-time constituents and stays blocked behind 45 — it
    makes the bias *visible and measurable* in the meantime, which is the
    part that isn't blocked. **Gate:** none (labelling only; no live
    behaviour changes). **Note:** if the two origins later diverge
    materially in the scorecard, that is evidence *for* prioritising 44/45,
    not a reason to drop names by hand.

<a id="item-70"></a>

70. **Missed-run detector** (S; rides 13) (added 2026-07-11) — each run
    compares the ledger's last row date against the trading calendar since;
    a gap prints one digest line ("⚠️ no ledger rows for 2026-07-08 —
    runner missed, live record has a hole") and `docs/snapshot.json` gains
    a `coverage` field that 14 reports alongside its returns. Rationale:
    #16 catches a run that *fails*; nothing catches a run that never
    *starts* — and a track record with silent holes is biased toward the
    days the infra was healthy, which corrupts the referee exactly like
    backfilling would (R3's mirror image). **Gate:** none (measurement);
    validate fixture with a planted gap.

<a id="item-16"></a>

16. **Self-tests gate the send** (S) — the workflow currently runs
    `daily_run.py` (which sends) *then* `homily_validate.py`: a broken
    engine ships its digest, then fails CI. Reorder: validate → digest. On
    failure send one line — "⚠️ digest suppressed, self-tests failed" — so
    silence is never ambiguous. **Gate:** none.

<a id="item-17"></a>

17. **Fetch hardening** (M) — `homily_data.py` has no retry, no fallback,
    and ~75 sequential 5y fetches per run. Add: retry with backoff + jitter,
    query1/query2 host rotation, `ThreadPoolExecutor` (stdlib) fan-out,
    Stooq daily CSV as key-free fallback (rows tagged `src:stooq` when
    used), and a partial-digest banner ("screened 61/71 — fetch failed:
    …") instead of a silent short list. **Gate:** validate test with a
    mocked flaky fetch.

<a id="item-18"></a>

18. **Total-return correctness** (M) — all return math (RS12/G3, THE test,
    scorecard) uses raw closes: dividends are invisible, so payers (V MA
    COST LLY NVO, SPY itself) are systematically docked vs zero-div growth
    names. Parse `adjclose` from the same Yahoo response; use it for ALL
    return/RS computations; keep raw OHLC for chip levels (levels must be
    tradeable prices). Re-run G3 both ways and publish the delta.
    **Gate:** validate test: NVO RS12 (raw) < RS12 (adj); backtest tables
    regenerated with a footnote.

<a id="item-19"></a>

19. **Corporate-action sanity check** (S) — a mis-adjusted split poisons the
    chip histogram and every level printed for weeks. Detector: |1-day
    move| > 45% on a volume spike → suppress that name's chip levels for the
    day ("levels suspended — corporate action?"), keep the state row.
    **Gate:** validate test on a synthetic 10:1 split series.

<a id="item-69"></a>

69. **Promotion lifecycle registry + rs12 forward-checker** (S–M) (added
    2026-07-11) — the promotion machinery is currently prose scattered
    across §5h/§5j/R10; make it mechanical. Committed `promotions.json`:
    one entry per gate-passed candidate — the pre-registered rule
    verbatim, gate date + artifact (backtest file, BACKTEST_RESULTS
    section), earliest promotion date, the forward-check criteria, AND a
    **demotion rule written the same day**. Ships now with the rs12-top3
    forward-checker as executable code (reads #13 rows, computes forward
    returns of top-3-by-`rs12_rank` ⭐ names vs the other ⭐ names, prints
    PASS/FAIL against the frozen criteria) so the 2026-10-01 decision is
    a program's output, not a fresh judgment call made three months from
    now with the result already visible. Standing rule adopted with this
    item: **nothing is promoted without a pre-registered demotion rule in
    the registry** (e.g. rs12-top3, if promoted, demotes back to
    equal-split when top-3 rows underperform other-⭐ rows over a rolling
    6-month ledger window — exact figure frozen in the registry entry
    before promotion). A promoted signal that stops working leaves by
    rule, not by debate — that, not refusing new signals, is how the
    algorithm stays uncluttered. **Gate:** none (guard infra, the #61/#62
    pattern); validate asserts every entry names its gate artifact.

<a id="item-75"></a>

75. **Snapshot schema contract** (S; rides 13/36, blocks T3) (added
    2026-07-11) — `docs/snapshot.json` is read by the dashboard (36),
    Claude sessions, and eventually the T3 order routine — the first
    consumer for whom a silently renamed field costs money. Add `"_v"`
    to the snapshot, a validate check pinning the buy-day block's
    required fields and types, and one more T3 hard guardrail in §9.2:
    the routine refuses to act on a schema version it doesn't know.
    **Gate:** validate contract test.

<a id="item-26"></a>

26. **Breadth canary** (S, info-only) — % of universe above 200d SMA and %
    weekly RED, one line under the regime banner when <30% ("hostile tape —
    historically poor month for new adds"). Never gates anything until a
    year of ledger data says it should. **Gate:** info-only by design.

<a id="item-27"></a>

27. **Position-aware digest** (M) — extend `holdings.json` to
    `{symbol, shares, cost}` (`"_v": 2`; synced via IBKR MCP in Claude
    sessions until #11/32 automates it). Unlocks: per-name % of stock book
    printed on its row, automatic Bucket A/B/C classification per PLAYBOOK
    §1 (earned vs bought via cost basis + ledger add-history), and 10%-cap
    proximity warnings ("NVDA 9.4% — next add breaches the cap").
    **Gate:** validate test on a fixture book.

<a id="item-28"></a>

28. **Trim-rule flags** (S; needs 27) — PLAYBOOK §5 becomes executable
    flags, not prose: "⚠️ RULE 1: RDDT 12% — bought-not-earned, trim to
    10%"; "⚠️ RULE 2 REVIEW: ZETA ⚪ 13w + F:1/3 — sell-half rule". Flags
    only — there is still no SELL state; the PRD §1 principle survives.
    **Gate:** rules mirror PLAYBOOK §5 verbatim; validate fixtures.

<a id="item-29"></a>

29. **Concentration / correlation lens** (M) — 90d daily-return correlation
    across held names (stdlib), greedy clustering, one digest line: "book
    clusters: AI/semis 68% (NVDA AMD AVGO TSM MU DRAM VST) · software 14% ·
    other 18%" + a warning when a ⭐ add would deepen a >60% cluster
    ("⭐ MU deepens the 68% cluster — non-cluster ⭐ first per §3").
    Info-only, but this is the highest-expected-value risk feature in the
    plan: the current book is one trade wearing 15 tickers.
    **Gate:** correlation math test; info-only.

<a id="item-30"></a>

30. **Bear-readiness line** (S; needs 27) — first-Monday digest: satellites%
    vs core%, margin=0 confirmation, and the pre-computed 🐻 sell list in
    PLAYBOOK §4 order ("if 🐻 fired tomorrow you would sell: …"). The bear
    playbook stays rehearsed instead of theoretical. **Gate:** none.

<a id="item-31"></a>

31. **Buy-day copilot** (M; needs 27) — on the first trading day each month
    (SGT), the digest leads with a 🛒 BUY DAY section: the ⭐ list resolved
    into exact orders from `BUY_BUDGET_USD` (repo *variable*, not secret):
    50% → Bucket A per §3, remainder equal-split across ⭐ (max 5),
    respecting the 10% cap (27), cluster warning (29), F-preference; prints
    IBKR-ready lines — "BUY 3 TSM @ mkt (~$1,302)". No ⭐ → "full amount →
    Bucket A" per §3.5. Turns the 10-minute routine into 2. **Gate:**
    fixture test: budget in → orders out, caps respected; info-only (it
    prints orders, never places them — §7 stands).

<a id="item-32"></a>

32. **IBKR Flex auto-sync** (#11, unchanged) (M) — Flex Web Service token +
    queryId as secrets → positions fetched at run start → feeds 27 without
    manual syncs. Fallback stays: tell Claude after trades / edit the JSON.

<a id="item-33"></a>

33. **Sunday deep-dive** (#9, now concrete) (M; needs 13, 36) — weekly
    edition = the F2 dashboard regenerated + one summary message: per-holding
    state timeline (12w), conviction drift, distance-to-zone, the week's
    🐳/VH events, scorecard refresh (14). Replaces "more text" with the
    dashboard link/file.

<a id="item-34"></a>

34. **F0 — digest typography v2** (S) — switch sends to Telegram HTML parse
    mode (kills the Markdown-entity fallback class of bugs in
    `daily_run.py send()`); align rows in `<pre>` blocks; unicode chip
    sparklines per row (`▁▃█▅▂` with a price marker — the histogram in 8
    chars); fold the legend + algo-health footer into an expandable
    blockquote so the actionable digest is ~10 lines tall. **Gate:**
    validate test for HTML entity escaping.

<a id="item-35"></a>

35. **F1 — chart cards, stdlib PNG** (M) — `homily_png.py`: a pure-stdlib
    PNG writer (`zlib` + `struct`, filter-0 scanlines, ~200 lines) drawing
    1y price + zone/POC/res bands + chip-histogram side panel + state
    ribbon; `sendPhoto` (multipart via urllib) the top-3 actionable names
    (⭐/🔵/🎯) daily. The digest becomes glanceable without any dependency
    or host. **Gate:** deterministic pixel-hash test on fixture bars.

<a id="item-36"></a>

36. **F2 — daily dashboard, self-contained HTML** (L; needs 13) —
    `homily_dashboard.py` renders `docs/dashboard.html` nightly: inline-SVG
    interactive (hover = values, zero external assets): every holding's
    card (price + levels + chip histogram), ledger state-history heatmap,
    scorecard tables (14), conviction drift, refine log chart, and an
    **alerts timeline** (every #15 state-change alert ever sent, newest
    first, reconstructed from ledger diffs — so a missed Telegram ping is
    recoverable and the alert history is auditable in one place; owner
    request 2026-07-10). Committed by
    the workflow AND sent via `sendDocument` — private in the chat, one tap
    to open, works offline, repo stays private, nothing hosted. **Gate:**
    HTML self-containment test (no external URLs) in validate.
    *Owner note 2026-07-10: the charts UI (#35 chip-chart cards + this
    dashboard) is explicitly wanted — keep #35 next in the Month-1 queue
    after #18/#19, and treat #36 as the Quarter item's centrepiece.*
