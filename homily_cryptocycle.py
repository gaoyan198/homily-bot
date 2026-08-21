#!/usr/bin/env python3
"""
#148 (D-148) — the crypto-cycle digest line. Pure computation + render: the
signal constants live here (single source), the state is a deterministic
function of the BTC daily bars handed in, and nothing is fetched or written.

Policy provenance: CRYPTO_SLEEVE.md, evidence BACKTEST_RESULTS §41/§42.

WHAT THIS LINE IS FOR. The sleeve accumulates unlevered spot through the
markdown, and may switch on a levered harvest engine ONLY after the markup
confirms. This line is the confirmation watch — it answers "is the engine
allowed on yet?" every morning so the answer is never a judgement call made
in a strong week.

THE SIGNAL (frozen, §42): BTC closes >= (1 + PCT) x the RUNNING cycle low,
and holds above that line for HOLD_WKS consecutive weeks.
  * measured against the RUNNING low, so the trigger CHASES a falling market
    down and never has to guess where the bottom is;
  * any close back below the line RESETS the clock to zero;
  * the hold period is the load-bearing part, not the percentage — every
    4wk/6wk variant tested produced a false positive (2018-03-08 fired at
    $9,395, then BTC fell to $3,191: a wipeout at 3x), every 8wk variant
    produced none across three cycles.

SETTLED BARS ONLY (#150). The 8-week clock is armed and disarmed on SETTLED
daily closes, never on the in-progress bar. Crypto trades 24/7, so a live
fetch always returns a provisional last bar whose "close" is just the current
quote — and on 2026-08-21 that provisional print crossed the trigger intraday
($75,360 vs a $75,072 trigger) and fell back below it the same day. Reading
the unsettled bar would have started a 56-day clock on a wick, which is NOT
the rule §42 measured: the backtest evaluated settled closes throughout. The
provisional price is still reported (`live_price`) so the digest can show
where the market is, but it never moves the clock. Compare #106, which marks
provisional bars rather than dropping them — that is display-only; this one
gates an irreversible action, so it drops.

The engine ALSO requires CRYPTO_SLEEVE §3's other conditions (trough window
closed, BTC-only, <= the sanctioned leverage). This line reports the timing
condition only and says so — it is a WATCH, never an authorisation.
"""
import collections
import datetime

PCT = 0.30                 # above the running cycle low
HOLD_WKS = 8               # consecutive weeks above the line
LAST_PEAK = datetime.date(2025, 10, 6)          # frozen chronology, §41
TROUGH_WINDOW = (datetime.date(2026, 8, 25), datetime.date(2026, 12, 23))


def cycle_state(bars, pct=PCT, hold_wks=HOLD_WKS, since=LAST_PEAK, today=None,
                asof=None):
    """bars: ascending [(date, o, h, l, c), ...] daily BTC. -> state dict, or
    None when there is nothing to read.

    Replays the SAME loop the study used, so the digest and BACKTEST_RESULTS
    can never drift: track the running low, arm on the first close above the
    trigger, disarm on any close back below, fire after hold_wks weeks."""
    w = [b for b in bars if b[0] >= since]
    if len(w) < 2:
        return None
    # #150: the clock reads SETTLED closes only — drop the in-progress bar.
    asof = asof or datetime.date.today()
    live = w[-1]
    w = [b for b in w if b[0] < asof]
    if len(w) < 2:
        return None
    low = w[0][3]
    low_date = w[0][0]
    armed = None
    fired = None
    for dt, o, h, lo, c in w:
        if lo < low:
            low, low_date = lo, dt
        if c >= low * (1 + pct):
            if armed is None:
                armed = dt
            elif (dt - armed).days >= hold_wks * 7 and fired is None:
                fired = dt
        else:
            armed = None
    dt, o, h, lo, c = w[-1]
    today = today or dt
    trigger = low * (1 + pct)
    live_px = live[4]
    provisional = live[0] >= asof
    held = (today - armed).days if armed else 0
    return dict(price=c, asof=dt, live_price=live_px, provisional=provisional,
                low=low, low_date=low_date, trigger=trigger,
                above=c >= trigger, pct_off_low=(c / low - 1) if low else 0.0,
                armed_since=armed, held_days=held,
                need_days=max(0, hold_wks * 7 - held),
                gap_to_trigger=(trigger / c - 1) if c else 0.0,
                fired=fired, in_trough_window=(TROUGH_WINDOW[0] <= today
                                               <= TROUGH_WINDOW[1]))


def cycle_line(state, esc=lambda x: x):
    """-> one ₿ digest line, or "" when there is no state (additive-only)."""
    if not state:
        return ""
    s = state
    px = f"${s['price']:,.0f}"
    low = f"${s['low']:,.0f}"
    trig = f"${s['trigger']:,.0f}"
    if s["fired"]:
        head = (f"🟢 MARKUP CONFIRMED {s['fired']:%Y-%m-%d} — the "
                f"{int(PCT*100)}%/{HOLD_WKS}wk timing condition is MET")
        tail = ("engine may switch on ONLY if CRYPTO_SLEEVE §3's other "
                "conditions also hold (BTC-only, sanctioned size); "
                "this line is a watch, not an authorisation")
    elif s["armed_since"]:
        head = (f"🟡 ARMING — {s['held_days']}/{HOLD_WKS*7}d above {trig} "
                f"(since {s['armed_since']:%Y-%m-%d})")
        tail = (f"{s['need_days']}d left; any close below {trig} RESETS the "
                "clock to zero — leverage stays OFF meanwhile")
    else:
        head = (f"🟠 leverage OFF — {px} is +{s['pct_off_low']:.0%} off the "
                f"{low} cycle low ({s['low_date']:%Y-%m-%d})")
        tail = (f"needs {trig} ({s['gap_to_trigger']:+.1%}) THEN "
                f"{HOLD_WKS}wk held; trigger falls with any new low")
    prov = ""
    if s.get("provisional") and abs(s["live_price"] - s["price"]) > 1e-9:
        prov = (f" · live ${s['live_price']:,.0f} (unsettled — the clock reads "
                f"the {s['asof']:%b %d} close, not the tape)")
    win = ""
    if s["in_trough_window"]:
        win = (f" · 🎯 in the projected trough window "
               f"({TROUGH_WINDOW[0]:%Y-%m-%d}…{TROUGH_WINDOW[1]:%Y-%m-%d}) "
               f"— spot accumulation is HEAVY here")
    return f"₿ <i>CYCLE: {esc(head)} — {esc(tail)}{prov}{win}</i>"


# ─────────────────────── #151: regime + phase ────────────────────────
# The stock book classifies BULL/BEAR off a 10-month SMA of COMPLETED
# month-end closes (homily_regime.sma10_state). Measured on BTC over 134
# months (BACKTEST_RESULTS §44): BULL months average +8.61% forward vs
# BEAR +0.96%, and long-only-in-BULL returns 395x against 284x buy-and-
# hold at a 60% max drawdown instead of 76%. Same rule, same shape, so
# one regime vocabulary covers both books.
SMA_N = 10
HALVING_NEXT = datetime.date(2028, 4, 16)
PEAK_NEXT = datetime.date(2029, 10, 4)


def month_ends(bars):
    """Daily bars -> [(date, close)] one row per month, last print wins."""
    out = collections.OrderedDict()
    for b in bars:
        out[(b[0].year, b[0].month)] = (b[0], b[4])
    return [out[k] for k in sorted(out)]


def btc_regime(bars, asof=None):
    """-> (label, last_completed_close, sma) using COMPLETED months only.

    Identical construction to homily_regime.sma10_state: the running month
    never votes, because a month is complete when the calendar leaves it."""
    asof = asof or datetime.date.today()
    rows = [(d, c) for d, c in month_ends(bars)
            if (d.year, d.month) < (asof.year, asof.month)]
    if len(rows) < SMA_N + 1:
        return None, None, None
    sma = sum(c for _, c in rows[-SMA_N:]) / SMA_N
    last = rows[-1][1]
    return ("BULL" if last > sma else "BEAR"), last, sma


def cycle_phase(asof=None):
    """Where the 4-year clock says we are. Dates frozen in §41's chronology."""
    asof = asof or datetime.date.today()
    if asof < TROUGH_WINDOW[0]:
        return "MARKDOWN", "past the peak, trough window not yet open"
    if asof <= TROUGH_WINDOW[1]:
        return "TROUGH WINDOW", "the projected bottom is HERE — buy heaviest"
    if asof < HALVING_NEXT:
        return "ACCUMULATION", f"post-trough, pre-halving ({HALVING_NEXT})"
    if asof < PEAK_NEXT - datetime.timedelta(days=365):
        return "MARKUP", f"post-halving, running to ~{PEAK_NEXT}"
    if asof < PEAK_NEXT + datetime.timedelta(days=120):
        return "DISTRIBUTION", "peak window — harvest to CASH, wind the engine down"
    return "MARKDOWN", "past the peak"


def leverage_verdict(state, regime):
    """The single ON/OFF the owner asked for, with the binding reason.

    ENTRY is gated by the §42 signal, EXIT by the regime (§44): measured
    peak-to-peak, signal-only took 2 liquidations and regime-only took 5,
    while signal-ENTRY + regime-EXIT took 1. Under CRYPTO_SLEEVE §6 a
    realised liquidation bans sleeve leverage permanently, so the arm with
    5 kills itself on the first one."""
    reasons = []
    if not state:
        return False, ["no BTC read"]
    if not state.get("fired"):
        need = state["need_days"] if state.get("armed_since") else HOLD_WKS * 7
        reasons.append(f"entry gate OPEN — needs ${state['trigger']:,.0f} "
                       f"held {need}d more")
    if regime != "BULL":
        reasons.append(f"regime is {regime or 'unknown'} (10m SMA) — "
                       "exit gate says flat")
    phase, _ = cycle_phase()
    if phase in ("MARKDOWN", "TROUGH WINDOW"):
        reasons.append(f"cycle phase {phase} — CRYPTO_SLEEVE §3 cond.1 "
                       "requires the trough window CLOSED")
    return (not reasons), reasons


def regime_line(bars, state=None, esc=lambda x: x, asof=None):
    """-> the 🐂/🐻 regime + phase + leverage verdict line (or "")."""
    label, last, sma = btc_regime(bars, asof=asof)
    if not label:
        return ""
    phase, why = cycle_phase(asof)
    icon = "🐂" if label == "BULL" else "🐻"
    ok, reasons = leverage_verdict(state, label)
    head = (f"{icon} BTC {label} — last month-end ${last:,.0f} vs 10m SMA "
            f"${sma:,.0f} ({last/sma-1:+.1%})")
    mid = f"phase {phase}: {why}"
    if ok:
        tail = ("✅ LEVERAGE PERMITTED — entry gate met, regime BULL, window "
                "closed. Size per CRYPTO_SLEEVE §3.4 (≤3× inside the sweep, "
                "W = your max loss)")
    else:
        tail = "❌ NO LEVERAGE — " + "; ".join(reasons)
    return (f"₿ <i>{esc(head)} · {esc(mid)}</i>\n"
            f"₿ <i>{esc(tail)}</i>")


# ───────────────── #152: the unambiguous regime board ─────────────────
# Owner: "our crypto sleeve needs to be SUPER CRYSTAL clear on whether we
# are still in bear or bull market, the last time i got it off and lost a
# lot of money ... prioritise the 4 year cycle where possible but also
# look at indicators like 200 sma."
#
# Measured (BACKTEST_RESULTS §45), forward 30d, BTC 2014->2026:
#   200d SMA        +8.77% when BULL vs +2.83% BEAR · 14% markdown false-bull
#   50d>200d cross  +8.36% / +3.47%                 · 20%
#   20wk (140d) SMA +9.31% / +2.02%                 · 14%
#   10m SMA (ours)  +8.25% / +2.40%                 · 23%
# Each works alone; each is wrong often enough alone to lose money on.
# UNANIMITY is what fixes it: 4/4 fires on only 9% of markdown days, and
# its forward 30d is +9.89% vs +3.36% at 2-3/4 and +2.45% at 0-1/4.
#
# HIERARCHY (deterministic — there is no judgement call anywhere in it):
#   1. The 4-year cycle is PRIMARY. In MARKDOWN or the TROUGH WINDOW the
#      verdict is BEAR no matter what the indicators say.
#   2. Only once the cycle permits do the indicators decide, and only
#      UNANIMITY reads BULL.
IND_BULL_MIN = 3          # of 3 — unanimity or it is not a bull
# #153: the 50d/200d cross is DROPPED. Subset-swept all 15 combinations on
# markdown false-BULL rate (§46): every set containing the 20-week SMA scores
# 9%; every set without it scores 14-24%. The cross is the weakest single
# indicator (+4.89% spread, 20% false-BULL) and adds nothing to any set that
# already has the 20wk. Kept: 200d (owner-requested), 20wk (the one that
# works), 10m (the stock book's own rule, kept for one vocabulary across
# both books). 3/3 scores the same 9% as 4/4 did.
MARGIN_STOP = 0.05        # delever when equity/notional hits 5% (HL liquidates
                          # at 1.25%). §46: zero liquidations across both
                          # peak-to-peak windows at no return cost.


def _sma(closes, n):
    return sum(closes[-n:]) / n if len(closes) >= n else None


def indicator_board(bars, asof=None):
    """-> [(name, bullish|None, detail)] for the four confirming indicators."""
    closes = [b[4] for b in bars]
    px = closes[-1] if closes else None
    out = []
    s200, s140 = _sma(closes, 200), _sma(closes, 140)
    out.append(("20-week SMA", (px > s140) if s140 else None,
                f"${px:,.0f} vs ${s140:,.0f}" if s140 else "—"))
    out.append(("200-day SMA", (px > s200) if s200 else None,
                f"${px:,.0f} vs ${s200:,.0f}" if s200 else "insufficient history"))
    lab, last, sma = btc_regime(bars, asof=asof)
    out.append(("10-month SMA", (lab == "BULL") if lab else None,
                f"${last:,.0f} vs ${sma:,.0f}" if lab else "—"))
    return out


def regime_verdict(bars, asof=None):
    """-> (verdict, phase, why, board, n_bull, n_known). Deterministic."""
    board = indicator_board(bars, asof=asof)
    known = [b for _, b, _ in board if b is not None]
    n_bull, n_known = sum(1 for b in known if b), len(known)
    phase, why = cycle_phase(asof)
    if phase in ("MARKDOWN", "TROUGH WINDOW"):     # rule 1: cycle is PRIMARY
        return "BEAR", phase, why, board, n_bull, n_known
    if n_known < 3:
        return "MIXED", phase, why, board, n_bull, n_known
    if n_bull >= IND_BULL_MIN:
        return "BULL", phase, why, board, n_bull, n_known
    if n_bull <= 1:
        return "BEAR", phase, why, board, n_bull, n_known
    return "MIXED", phase, why, board, n_bull, n_known


def regime_block(bars, state=None, esc=lambda x: x, asof=None):
    """The crystal-clear block: one verdict, then exactly why."""
    if not bars:
        return ""
    verdict, phase, why, board, n_bull, n_known = regime_verdict(bars, asof)
    icon = {"BULL": "🐂", "MIXED": "⚖️", "BEAR": "🐻"}[verdict]
    action = {"BULL": "leverage ALLOWED if the entry signal has fired",
              "MIXED": "SPOT ONLY — no new leverage",
              "BEAR": "SPOT ONLY — no leverage"}[verdict]
    lines = [f"₿ <b>═══ CRYPTO REGIME: {icon} {verdict} ═══ {esc(action)}</b>"]
    prim = "🐻" if phase in ("MARKDOWN", "TROUGH WINDOW") else "🐂"
    tag = " ← OVERRIDES the indicators" if phase in ("MARKDOWN",
                                                     "TROUGH WINDOW") else ""
    lines.append(f"₿ <i>PRIMARY · 4-year cycle: {prim} {esc(phase)} — "
                 f"{esc(why)}{tag}</i>")
    bits = " · ".join(f"{'🐂' if b else '🐻' if b is not None else '·'} "
                      f"{n} {d}" for n, b, d in board)
    lines.append(f"₿ <i>CONFIRMING · {n_bull} of {n_known} bullish "
                 f"(need {IND_BULL_MIN}/3 for 🐂): {esc(bits)}</i>")
    ok, reasons = leverage_verdict(state, "BULL" if verdict == "BULL" else verdict)
    if verdict != "BULL":
        reasons = [r for r in reasons if "regime" not in r]
        reasons.insert(0, f"regime is {verdict}")
    lines.append("₿ <i>" + ("✅ LEVERAGE PERMITTED — size per CRYPTO_SLEEVE §3.4"
                            if ok and verdict == "BULL"
                            else "❌ NO LEVERAGE — " + esc("; ".join(reasons)))
                 + "</i>")
    return "\n".join(lines)


def stop_price(entry, size, collateral, mstop=MARGIN_STOP):
    """Price at which equity/notional falls to `mstop` -> the resting stop.

    MUST be recomputed monthly, not set once: funding drains collateral, which
    raises this price over time. §46 found a fixed price-from-entry stop is
    outrun by funding and lets the exchange liquidate first — the whole point
    of expressing it as a margin RATIO is that it cannot be outrun."""
    if size <= 0:
        return None
    return (size * entry - collateral) / (size * (1 - mstop))
