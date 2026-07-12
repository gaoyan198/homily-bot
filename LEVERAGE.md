# LEVERAGE.md — the regime-gated, sleeve-only leverage policy (#91 / D-91)

**Status: SIGNED 2026-07-12 (owner override — see the owner line at the
bottom).** Constants pinned by `homily_leverage_backtest.py` (run
2026-07-12, BACKTEST_RESULTS §15): the pre-registered readout PASSED at
L = 1.30 — zero margin-call breaches across every rolling ≥5y window since
2015 AND the 1999→2026 max-history path (dot-com + 2008 + 2022), at base
**and** stress financing, while beating unlevered QQQ net of financing on
3/3 construction-honest read windows. This document is the two-artifact
governance record (the A4 / LIVE_ENABLE pattern): D-91 is the design, this
file is the signature. It deliberately does NOT enter `promotions.json` —
that registry's schema is ledger-rank-specific (verify_registry requires a
`rank_column` forward check); this file IS the registry entry for the
policy, with its own review rule in §5.

## 1 · The ladder (account-level gross leverage caps)

| Regime (frozen 10m-SMA rule, month-end SPY+QQQ) | Account gross cap |
|---|---|
| 🐂 BULL — both above | **≤ 1.30×** |
| ⚖️ MIXED — one above | **≤ 1.15×** — no NEW margin; paydown drift |
| 🐻 BEAR — onset fires | **1.00× — margin to zero at onset** (already PLAYBOOK §4 step 1 "margin first"; re-lever only on the §4.7 thirds re-entry schedule) |

Derivation (D-91): margin call at uniform drop d\* = (1−mL)/(L(1−m)),
m = 0.25. At 1.30× the boundary is −69.2%; the worst measured path reached
equity/position 0.68 (1999→2026, levered through three bears) — never near
0.25. At 1.50× a COVID-speed crash landing before the month-end signal is
one gap from a call on concentrated maintenance — excluded. Concentrated
books carry m > 0.25 at IBKR; every number above flatters leverage, so a
breach in the model is certainly a breach live.

## 2 · What borrowed dollars may buy — and may never buy

* **NEVER the core monthly book.** Its own measured paths (−59…−76%
  MaxDD, BACKTEST_RESULTS §3) sit INSIDE the call boundary at any constant
  L ≥ 1.25. This is arithmetic, not caution; no backtest can soften it.
  Re-confirmed by the §15 core-ban table.
* **Only 4–12wk swing-sleeve entries**, journaled, stop written before
  entry, and only from an arm that has passed its unlevered gate
  (LEVERAGE_MEMO L1, inherited — S1-pure's P2 paper gate reads earliest
  ~2027-01-09; #93/D-93 is the arming session).
* **Per levered position:** sized so a p5 episode (−31.7%, §12) × L costs
  ≤ 0.5% of net liq — ≈ 1.6% notional at 2× position leverage, the same
  dispersion math that derived the whale-dip cap.
* **The sidecar** (gambit/LEVERAGE_MEMO §5) continues on its own frozen
  terms (US$2k house money, ≤US$5k notional, scored vs QQQ 2027-07); it
  counts against the account ladder like everything else.

## 3 · The referee (pre-registered, non-negotiable)

Any levered arm is scored against **regime-gated levered QQQ at the same
L, same financing** — never against unlevered QQQ. §15's numbers make the
bar concrete: ladder-1.30 QQQ did 2.57 / 2.29 / 9.43 MOIC on the read
windows. Leverage that cannot beat the same leverage on the index belongs
on the index. This referee is also the honest answer to "beat QQQ":
regime-gated 1.30× QQQ **is itself an above-QQQ strategy** (+0.15…+2.13
MOIC on the read windows, net of 5.8% financing, surviving 7.8% stress) —
any cleverness added on top must clear it, not just QQQ.

## 4 · The transition (account reality, 2026-07-12)

The account runs ~1.23× legacy margin (S$42.9k net liq, −S$9.8k cash,
2026-07-10) — borrowed against the CORE book, which §2 forbids going
forward. Grandfathered **shrink-only**: no new core margin ever;
contributions and the standing MARGIN_ZERO task pay it down; new levered
swing entries may use only the headroom between current gross and the
ladder cap (~S$3.1k at signing). Nothing is force-sold (§5 never-sell
stands). In BULL the legacy block is inside the 1.30 cap; on a MIXED print
it exceeds the no-new-margin posture (paydown continues); on 🐻 onset it
goes to zero per §1 — that was already the PLAYBOOK rule.

## 5 · Review + shrink rule (the policy's own demotion)

* Re-run `homily_leverage_backtest.py` at every #40 yearly-harness pass.
  Any breach cell appearing, or the levered edge inverting (ladder-1.30 <
  unlevered QQQ on ≥2/3 of the then-current read windows), **shrinks the
  ladder one step mechanically** (1.30 → 1.15 → 1.00); shrinks are
  recorded here, never debated.
* A realized margin call — any forced liquidation, any size — sets the
  ladder to 1.00× permanently pending a full post-mortem in
  BACKTEST_RESULTS.
* The daily digest prints the ladder line (`homily_leverage.py`, validate
  [49]) from the signing date; gross-L automation waits on #32 Flex
  secrets — until then the line reminds, the owner reconciles.

## 6 · What this policy does NOT change

The falsifiable bar stays beat-QQQ (§9.0). The swing sleeve stays PAPER
until #93's gate. The 🐻 protocol, the caps, the ⭐ discipline, the
never-sell rule — untouched. KILL_MEMO and LEVERAGE_MEMO stand: leverage
amplifies edge, it cannot create it; what changed today is that the
*index* edge it amplifies is now measured, pinned, and capped.

---

**Owner line (two-artifact pattern; the A4/#24 override precedent):**

> 2026-07-12 — Owner directive, recorded verbatim by the executing session:
> *"leverage is now ok because we are aiming to be maximum return like
> danny"* … *"execute them NOW, dont stop until you're done."* Per that
> instruction this policy signs today, same-session as its gate backtest —
> a recorded Part-III rule-5 override (PRD §8.5), accepted because the
> policy's only immediate live effects are CONSTRAINTS (shrink-only legacy
> margin, BEAR = margin-zero, core-book ban); no levered order can exist
> before #93's gate regardless. — owner (gaoyan), via directive; amend
> this line directly if the wording should differ.
