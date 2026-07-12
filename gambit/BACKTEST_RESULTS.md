# GAMBIT BACKTEST_RESULTS — Phase-1 protocol run (2026-07-10)

**Every number here is a survivorship-flattered UPPER BOUND** (Part II): the universe was constructed 2026-07-10 from current listings; point-in-time eligibility gates are applied, but 2015-era delistings cannot be recovered. The paper ledger is the real test; P2's gate inherits nothing from this file.

Protocol as registered in DESIGNS Part II + Amendment A1; implementation choices registered in gambit_arms.py's docstring before this run (incl. Amendment A3: cluster cap → concurrency caps, no key-free sector source). Costs 0.25% RT, stress 0.35% RT. Fills T+1 open, gaps taken in full. Random band: 200 seeded draws, 5 names, 4-week rotation, recomputed at each cost level.

## Windows

### 2015-01-01 → 2020-01-01 (5y) — eligible at open: 80/120

| arm | MOIC | CAGR | MaxDD | MAR | MOIC@0.35% | MAR@0.35% | trades (base) |
|---|---:|---:|---:|---:|---:|---:|---|
| QQQ B&H | 2.14 | 16.5% | -22.8% | 0.72 | — | — | — |
| SPY B&H | 1.72 | 11.5% | -19.3% | 0.59 | — | — | — |
| EW-universe monthly | 2.15 | 16.6% | -20.0% | 0.83 | — | — | — |
| S1-pure | 1.55 | 9.2% | -27.6% | 0.33 | 1.53 | 0.32 | 81 fills · win 0% · avg +0.00R · ΣR +0.0 |
| S1-stopped | 1.06 | 1.2% | -12.7% | 0.10 | 1.04 | 0.05 | 236 fills · win 45% · avg +0.49R · ΣR +64.4 |
| S2 pullback | 1.01 | 0.2% | -5.9% | 0.04 | 1.00 | 0.01 | 54 fills · win 41% · avg +0.40R · ΣR +10.3 |
| S3 vol-hole | 0.90 | -2.2% | -13.5% | -0.16 | 0.89 | -0.16 | 32 fills · win 25% · avg -0.21R · ΣR -11.6 |
| RANDOM-5 ×200 | p10 1.33 · p50 1.80 · **p90 2.36** | | | | p90 2.23 | | |

S3 journal-only VOLHOLE_BREAKDOWN events (base): 403

### 2016-01-01 → 2021-01-01 (5y) — eligible at open: 80/120

| arm | MOIC | CAGR | MaxDD | MAR | MOIC@0.35% | MAR@0.35% | trades (base) |
|---|---:|---:|---:|---:|---:|---:|---|
| QQQ B&H | 2.99 | 24.5% | -28.6% | 0.86 | — | — | — |
| SPY B&H | 2.05 | 15.5% | -33.7% | 0.46 | — | — | — |
| EW-universe monthly | 2.96 | 24.3% | -33.1% | 0.74 | — | — | — |
| S1-pure | 2.29 | 18.1% | -40.2% | 0.45 | 2.26 | 0.44 | 78 fills · win 0% · avg +0.00R · ΣR +0.0 |
| S1-stopped | 1.45 | 7.7% | -9.7% | 0.79 | 1.41 | 0.73 | 237 fills · win 48% · avg +0.75R · ΣR +122.7 |
| S2 pullback | 1.17 | 3.2% | -5.9% | 0.55 | 1.16 | 0.51 | 62 fills · win 47% · avg +1.13R · ΣR +55.8 |
| S3 vol-hole | 0.93 | -1.4% | -10.6% | -0.13 | 0.93 | -0.14 | 34 fills · win 32% · avg +0.06R · ΣR -5.5 |
| RANDOM-5 ×200 | p10 1.76 · p50 2.50 · **p90 3.30** | | | | p90 3.10 | | |

S3 journal-only VOLHOLE_BREAKDOWN events (base): 389

### 2017-01-01 → 2022-01-01 (5y) — eligible at open: 85/120

| arm | MOIC | CAGR | MaxDD | MAR | MOIC@0.35% | MAR@0.35% | trades (base) |
|---|---:|---:|---:|---:|---:|---:|---|
| QQQ B&H | 3.45 | 28.2% | -28.6% | 0.99 | — | — | — |
| SPY B&H | 2.30 | 18.2% | -33.7% | 0.54 | — | — | — |
| EW-universe monthly | 3.21 | 26.3% | -33.1% | 0.80 | — | — | — |
| S1-pure | 2.57 | 20.9% | -40.2% | 0.52 | 2.54 | 0.51 | 65 fills · win 0% · avg +0.00R · ΣR +0.0 |
| S1-stopped | 1.42 | 7.3% | -9.7% | 0.76 | 1.40 | 0.70 | 245 fills · win 50% · avg +0.77R · ΣR +131.3 |
| S2 pullback | 1.09 | 1.8% | -7.6% | 0.23 | 1.08 | 0.21 | 66 fills · win 39% · avg +0.85R · ΣR +43.7 |
| S3 vol-hole | 0.96 | -0.8% | -9.0% | -0.09 | 0.96 | -0.10 | 37 fills · win 41% · avg +0.28R · ΣR +1.0 |
| RANDOM-5 ×200 | p10 1.85 · p50 2.64 · **p90 3.82** | | | | p90 3.59 | | |

S3 journal-only VOLHOLE_BREAKDOWN events (base): 434

### 2018-01-01 → 2023-01-01 (5y) — eligible at open: 90/120

| arm | MOIC | CAGR | MaxDD | MAR | MOIC@0.35% | MAR@0.35% | trades (base) |
|---|---:|---:|---:|---:|---:|---:|---|
| QQQ B&H | 1.76 | 12.0% | -35.1% | 0.34 | — | — | — |
| SPY B&H | 1.55 | 9.2% | -33.7% | 0.27 | — | — | — |
| EW-universe monthly | 1.85 | 13.1% | -33.1% | 0.40 | — | — | — |
| S1-pure | 1.91 | 13.9% | -40.2% | 0.35 | 1.89 | 0.34 | 60 fills · win 0% · avg +0.00R · ΣR +0.0 |
| S1-stopped | 1.42 | 7.3% | -8.5% | 0.86 | 1.40 | 0.81 | 201 fills · win 51% · avg +0.89R · ΣR +128.3 |
| S2 pullback | 1.05 | 0.9% | -8.3% | 0.11 | 1.04 | 0.10 | 48 fills · win 35% · avg +0.84R · ΣR +33.0 |
| S3 vol-hole | 0.97 | -0.6% | -6.2% | -0.09 | 0.97 | -0.10 | 25 fills · win 40% · avg +0.31R · ΣR +1.4 |
| RANDOM-5 ×200 | p10 1.01 · p50 1.54 · **p90 2.24** | | | | p90 2.11 | | |

S3 journal-only VOLHOLE_BREAKDOWN events (base): 351

### 2019-01-01 → 2024-01-01 (5y) — eligible at open: 89/120

| arm | MOIC | CAGR | MaxDD | MAR | MOIC@0.35% | MAR@0.35% | trades (base) |
|---|---:|---:|---:|---:|---:|---:|---|
| QQQ B&H | 2.80 | 22.9% | -35.1% | 0.65 | — | — | — |
| SPY B&H | 2.09 | 16.0% | -33.7% | 0.47 | — | — | — |
| EW-universe monthly | 2.79 | 22.8% | -33.1% | 0.69 | — | — | — |
| S1-pure | 2.71 | 22.2% | -40.2% | 0.55 | 2.69 | 0.54 | 53 fills · win 0% · avg +0.00R · ΣR +0.0 |
| S1-stopped | 1.50 | 8.5% | -11.9% | 0.71 | 1.48 | 0.68 | 197 fills · win 51% · avg +0.89R · ΣR +126.7 |
| S2 pullback | 1.02 | 0.4% | -12.1% | 0.03 | 1.02 | 0.02 | 50 fills · win 34% · avg +0.74R · ΣR +28.7 |
| S3 vol-hole | 1.02 | 0.5% | -4.6% | 0.10 | 1.02 | 0.09 | 31 fills · win 55% · avg +0.68R · ΣR +11.4 |
| RANDOM-5 ×200 | p10 1.59 · p50 2.31 · **p90 3.25** | | | | p90 3.06 | | |

S3 journal-only VOLHOLE_BREAKDOWN events (base): 401

### 2020-01-01 → 2025-01-01 (5y) — eligible at open: 93/120

| arm | MOIC | CAGR | MaxDD | MAR | MOIC@0.35% | MAR@0.35% | trades (base) |
|---|---:|---:|---:|---:|---:|---:|---|
| QQQ B&H | 2.46 | 19.7% | -35.1% | 0.56 | — | — | — |
| SPY B&H | 1.95 | 14.3% | -33.7% | 0.42 | — | — | — |
| EW-universe monthly | 2.88 | 23.6% | -33.1% | 0.71 | — | — | — |
| S1-pure | 4.75 | 36.6% | -45.5% | 0.81 | 4.71 | 0.80 | 56 fills · win 0% · avg +0.00R · ΣR +0.0 |
| S1-stopped | 1.60 | 9.9% | -12.0% | 0.82 | 1.58 | 0.79 | 214 fills · win 51% · avg +0.94R · ΣR +148.3 |
| S2 pullback | 0.98 | -0.4% | -12.1% | -0.04 | 0.97 | -0.04 | 50 fills · win 40% · avg +0.42R · ΣR +11.9 |
| S3 vol-hole | 1.11 | 2.2% | -4.6% | 0.47 | 1.11 | 0.45 | 40 fills · win 60% · avg +1.05R · ΣR +28.5 |
| RANDOM-5 ×200 | p10 1.45 · p50 2.24 · **p90 3.69** | | | | p90 3.47 | | |

S3 journal-only VOLHOLE_BREAKDOWN events (base): 399

### 2021-01-01 → 2026-01-01 (5y) — eligible at open: 99/120

| arm | MOIC | CAGR | MaxDD | MAR | MOIC@0.35% | MAR@0.35% | trades (base) |
|---|---:|---:|---:|---:|---:|---:|---|
| QQQ B&H | 2.01 | 15.0% | -35.1% | 0.43 | — | — | — |
| SPY B&H | 1.94 | 14.3% | -24.5% | 0.58 | — | — | — |
| EW-universe monthly | 3.17 | 26.0% | -32.1% | 0.81 | — | — | — |
| S1-pure | 5.49 | 40.7% | -45.6% | 0.89 | 5.45 | 0.88 | 40 fills · win 0% · avg +0.00R · ΣR +0.0 |
| S1-stopped | 1.17 | 3.2% | -12.9% | 0.25 | 1.16 | 0.22 | 207 fills · win 41% · avg +0.64R · ΣR +88.4 |
| S2 pullback | 0.98 | -0.3% | -11.4% | -0.03 | 0.98 | -0.03 | 41 fills · win 39% · avg +0.34R · ΣR +6.7 |
| S3 vol-hole | 1.09 | 1.7% | -4.6% | 0.36 | 1.08 | 0.34 | 40 fills · win 57% · avg +1.00R · ΣR +28.9 |
| RANDOM-5 ×200 | p10 1.54 · p50 2.55 · **p90 4.15** | | | | p90 3.90 | | |

S3 journal-only VOLHOLE_BREAKDOWN events (base): 391

### 2015-01-01 → 2025-01-01 (10y) — eligible at open: 80/120

| arm | MOIC | CAGR | MaxDD | MAR | MOIC@0.35% | MAR@0.35% | trades (base) |
|---|---:|---:|---:|---:|---:|---:|---|
| QQQ B&H | 5.32 | 18.2% | -35.1% | 0.52 | — | — | — |
| SPY B&H | 3.38 | 12.9% | -33.7% | 0.38 | — | — | — |
| EW-universe monthly | 6.25 | 20.1% | -33.1% | 0.61 | — | — | — |
| S1-pure | 7.41 | 22.2% | -44.0% | 0.50 | 7.24 | 0.49 | 130 fills · win 0% · avg +0.00R · ΣR +0.0 |
| S1-stopped | 1.39 | 3.4% | -20.5% | 0.16 | 1.33 | 0.14 | 459 fills · win 43% · avg +0.64R · ΣR +197.2 |
| S2 pullback | 1.09 | 0.8% | -12.1% | 0.07 | 1.07 | 0.06 | 106 fills · win 42% · avg +0.72R · ΣR +55.7 |
| S3 vol-hole | 1.01 | 0.1% | -13.5% | 0.01 | 1.00 | 0.00 | 73 fills · win 45% · avg +0.56R · ΣR +22.0 |
| RANDOM-5 ×200 | p10 2.42 · p50 4.20 · **p90 6.98** | | | | p90 6.17 | | |

S3 journal-only VOLHOLE_BREAKDOWN events (base): 801

### 2016-01-01 → 2026-01-01 (10y) — eligible at open: 80/120

| arm | MOIC | CAGR | MaxDD | MAR | MOIC@0.35% | MAR@0.35% | trades (base) |
|---|---:|---:|---:|---:|---:|---:|---|
| QQQ B&H | 6.03 | 19.7% | -35.1% | 0.56 | — | — | — |
| SPY B&H | 4.01 | 14.9% | -33.7% | 0.44 | — | — | — |
| EW-universe monthly | 9.47 | 25.2% | -33.1% | 0.76 | — | — | — |
| S1-pure | 9.92 | 25.8% | -45.5% | 0.57 | 9.69 | 0.56 | 128 fills · win 0% · avg +0.00R · ΣR +0.0 |
| S1-stopped | 2.41 | 9.2% | -11.9% | 0.78 | 2.33 | 0.73 | 437 fills · win 49% · avg +0.90R · ΣR +290.3 |
| S2 pullback | 1.15 | 1.4% | -12.1% | 0.12 | 1.14 | 0.11 | 103 fills · win 44% · avg +0.81R · ΣR +62.6 |
| S3 vol-hole | 1.03 | 0.3% | -10.6% | 0.02 | 1.02 | 0.02 | 77 fills · win 48% · avg +0.63R · ΣR +28.5 |
| RANDOM-5 ×200 | p10 3.64 · p50 6.18 · **p90 10.17** | | | | p90 8.99 | | |

S3 journal-only VOLHOLE_BREAKDOWN events (base): 780

## Gate — scored mechanically (PRD §4 + Part-II margin)

Qualifying windows: 2019→2024, 2020→2025, 2021→2026. A window clears iff (a) MOIC ≥ QQQ+0.10 AND (b) MAR > QQQ AND (c) MOIC > random p90 AND (d) all three repeat at 0.35% RT. Candidate passes iff ≥2 of 3 windows clear.

| candidate | window | a:MOIC+0.10 | b:MAR | c:>p90 | d:stress | window clears |
|---|---|---|---|---|---|---|
| S1-pure | 2019→2024 | ✗ | ✗ | ✗ | ✗ | no |
| S1-pure | 2020→2025 | ✓ | ✓ | ✓ | ✓ | YES |
| S1-pure | 2021→2026 | ✓ | ✓ | ✓ | ✓ | YES |
| S1-stopped | 2019→2024 | ✗ | ✓ | ✗ | ✗ | no |
| S1-stopped | 2020→2025 | ✗ | ✓ | ✗ | ✗ | no |
| S1-stopped | 2021→2026 | ✗ | ✗ | ✗ | ✗ | no |
| S2 pullback | 2019→2024 | ✗ | ✗ | ✗ | ✗ | no |
| S2 pullback | 2020→2025 | ✗ | ✗ | ✗ | ✗ | no |
| S2 pullback | 2021→2026 | ✗ | ✗ | ✗ | ✗ | no |
| S3 vol-hole | 2019→2024 | ✗ | ✗ | ✗ | ✗ | no |
| S3 vol-hole | 2020→2025 | ✗ | ✗ | ✗ | ✗ | no |
| S3 vol-hole | 2021→2026 | ✗ | ✗ | ✗ | ✗ | no |

### Verdicts

* **S1-pure: NOT PROMOTABLE (owner directive; 2/3 windows cleared)** (2/3 qualifying windows cleared)
* **S1-stopped: FAIL** (0/3 qualifying windows cleared)
* **S2 pullback: FAIL** (0/3 qualifying windows cleared)
* **S3 vol-hole: FAIL** (0/3 qualifying windows cleared)

Per Part II: no candidate passing → kill memo and the project stops at Phase 1 (PRD §5.2). Any PASS advances that candidate to G-S5 paper, where the P2 gate applies with no credit inherited from this file.

## Addendum 2026-07-11 — owner question: would 10–20% leverage clear the gate?

Answered in LEVERAGE_MEMO.md without a re-run. Condition (c) is invariant under like-for-like leverage (x→x^L is monotone, applied to candidate and random band alike), and every failed candidate failed (c) on all three qualifying windows; the frictionless ×1.2 MOIC bound also misses condition (a) by 0.8–1.9 MOIC per cell. **Verdict unchanged. G7 stands.** Reopen conditions L1–L4 pre-registered in the memo; the ring-fenced sidecar experiment (memo §5) is the sanctioned home for levered discretionary follows.

## Close-out 2026-07-11 — Phase-1 kill memo written

The kill memo owed under PRD §5.2 / §4.1 (and flagged as still-owed in LEVERAGE_MEMO §6) is written: **KILL_MEMO.md**. No arm was promotable under the original §4 stop directive. This file's scored cells are unchanged and remain the sole record of the P1 bar; the kill memo interprets them and pre-registers the reopen conditions.

**Amendment A4 (same day): S1-pure promoted to paper.** The owner then took the reopen lever the memo named — reconsidering the stop directive — and promoted **S1-pure**, which mechanically cleared the gate on 2/3 qualifying windows (2020→2025, 2021→2026: all of a/b/c/d ✓ above), accepting its stop-free −40…−46% drawdowns in writing (AMENDMENT_A4.md). G-S5 (paper loop + journal) is built against it. This does not edit any scored cell — S1-pure's numbers above are exactly what earned the (conditional) promotion; the paper ledger, not this file, is now the live test (P2 gate inherits no credit).
