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


# ─────────────────── #154: the $1M target tracker ────────────────────
# Owner: "i need 1mm by the next bull run." A goal without a feedback loop
# is a wish, so the digest now prints progress against it every day.
#
# Every assumption below is a CONSTANT, not a hidden fudge, because the
# answer is extremely sensitive to all three and the owner must be able to
# argue with each one:
TARGET_USD = 1_000_000.0
LAST_PEAK = 124753.0            # 2025-10-06, frozen chronology §41
TARGET_PEAK_MULT = 2.1          # next peak vs last. History: 3.4x then 1.9x.
                                # 2.1x is INSIDE that range and is the level
                                # S$4,250/mo needs (§46 path table).
AVG_COST_ASSUMPTION = 60000.0   # average accumulation price over the sleeve
STRATEGY_MULT = 1.72            # units vs flat spot DCA (§43/§46, 5x + stop)


def target_state(units_held, monthly_usd, asof=None, peak_date=PEAK_NEXT,
                 btc_share=1.0):
    """-> progress dict, or None when there is nothing to report.

    `units_held` is BTC-equivalent (spot BTC + IBIT), read from the same
    contributions.json balances the household scorecard uses — never
    invented here. `monthly_usd` is the owner-set sleeve run-rate; 0 means
    unset and the line says so rather than guessing."""
    asof = asof or datetime.date.today()
    months = max(0, round((peak_date - asof).days / 30.44))
    peak_px = LAST_PEAK * TARGET_PEAK_MULT
    need = TARGET_USD / peak_px
    # #155: only the BTC SHARE of contributions builds BTC. At a 50/50
    # split the other half is an alt bet the BTC-denominated target cannot
    # count, and the tracker must not pretend otherwise.
    btc_usd = monthly_usd * btc_share
    add = ((btc_usd * months) / AVG_COST_ASSUMPTION) * STRATEGY_MULT \
        if btc_usd else 0.0
    proj = units_held + add
    other_usd = monthly_usd * (1 - btc_share) * months
    shortfall = max(0.0, TARGET_USD - proj * peak_px)
    return dict(units=units_held, need=need, months=months, proj=proj,
                peak_px=peak_px, monthly=monthly_usd, btc_share=btc_share,
                other_usd=other_usd, shortfall=shortfall,
                other_mult=(shortfall / other_usd) if other_usd else None,
                on_track=(proj >= need) if monthly_usd else None,
                # the peak price the CURRENT path would need to hit $1M
                implied=(TARGET_USD / proj) if proj > 0 else None,
                # the run-rate that WOULD get there from here
                need_monthly=(max(0.0, (need - units_held))
                              * AVG_COST_ASSUMPTION / STRATEGY_MULT / months)
                if months else None)


def target_line(st, esc=lambda x: x):
    """-> one ₿ TARGET line, or "" (additive-only)."""
    if not st:
        return ""
    if not st["monthly"]:
        return (f"₿ <i>TARGET ${TARGET_USD/1e6:.0f}M: {st['units']:.4f} BTC held · "
                f"need {st['need']:.2f} BTC @ ${st['peak_px']:,.0f} peak · "
                f"{st['months']}mo left — <b>run-rate NOT SET</b>, so no "
                f"progress can be scored (set balances.crypto_monthly_usd)</i>")
    mark = "✅ ON TRACK" if st["on_track"] else "⚠️ BEHIND"
    gap = ""
    if not st["on_track"]:
        gap = (f" — needs <b>${st['need_monthly']:,.0f}/mo to BTC</b> "
               f"(${st['monthly']*st['btc_share']:,.0f} set)")
    if st["btc_share"] < 1.0 and st["other_mult"]:
        gap += (f" · the non-BTC {(1-st['btc_share'])*100:.0f}% "
                f"(${st['other_usd']:,.0f}) must return "
                f"<b>{st['other_mult']:.1f}×</b> to close the rest")
    return (f"₿ <i>TARGET ${TARGET_USD/1e6:.0f}M: {mark} · {st['units']:.4f} BTC now "
            f"→ {st['proj']:.2f} projected vs {st['need']:.2f} needed · "
            f"{st['months']}mo left · implied peak ${st['implied']:,.0f} "
            f"({st['implied']/LAST_PEAK:.1f}× last){gap}</i>")


# ─────────────── #155: the HYPE monitor — watched, not governed ───────────
# Owner decision 2026-08-21: the sleeve runs 50/50 BTC/HYPE, reaffirmed after
# the §48 analysis. HYPE is therefore HALF the sleeve and NONE of this
# module's machinery applies to it: the 4-year cycle, the trough window, the
# regime board, the +30%/8wk signal and the 5% margin stop are all calibrated
# on 12 years of BTC across three complete cycles. HYPE has 1.7 years and has
# never seen a bear market.
#
# This line therefore reports RISK TELEMETRY ONLY and says so on every print.
# It deliberately renders no verdict, because inventing one from 1.7 years
# would be worse than admitting there isn't one.
HYPE_SYM = "HYPE32196-USD"


def hype_line(bars, esc=lambda x: x):
    """-> one telemetry line for the unmanaged half, or ""."""
    if not bars or len(bars) < 30:
        return ""
    closes = [b[4] for b in bars]
    px = closes[-1]
    ath = max(closes)
    ath_i = closes.index(ath)
    trough = min(closes[ath_i:]) if ath_i < len(closes) - 1 else px
    d30 = closes[-30]
    hist_d = (bars[-1][0] - bars[0][0]).days
    return (f"◈ <i>HYPE (UNMANAGED — no cycle rule, no regime gate, no stop): "
            f"${px:,.2f} · {px/ath-1:+.0%} from ATH ${ath:,.2f} · "
            f"{px/d30-1:+.0%} 30d · worst drawdown since ATH "
            f"{trough/ath-1:.0%} · only {hist_d//365}y{(hist_d%365)//30}m of "
            f"history, never through a bear — <b>sized by conviction, not by "
            f"evidence</b></i>")


# ───────────────── #157: the buy-day contribution line ──────────────────
# Owner: "my buy day should be same as buy day as my ibkr trad fi stuff."
# The stock book's buy day is homily_buyday.is_buy_day — the FIRST digest run
# of a calendar month, not a fixed date. The crypto sleeve rides the same
# trigger, so there is one buy day and one routine, not two.
#
# Amounts are owner-set in contributions.json and NEVER guessed. Unset prints
# the setup instruction instead of a number, same discipline as the tracker.
RESERVE_MONTHS = 8      # §49.2: being EARLY is punished, being late is not —
                        # deploy a reserve over ~8 months, not 4.


def contribution(monthly, reserve, btc_share, in_window, months_left=None):
    """-> (total, btc, alt, reserve_slice). The reserve slice is BTC-only:
    the trough-window rule is 'buy what is cheap', and on 2026-08-21 BTC was
    −40% from its high while HYPE was AT its high (CRYPTO_SLEEVE §5)."""
    if not monthly:
        return None
    slice_ = 0.0
    if reserve and in_window:
        n = months_left or RESERVE_MONTHS
        slice_ = reserve / max(1, n)
    btc = monthly * btc_share + slice_
    alt = monthly * (1 - btc_share)
    return dict(total=monthly + slice_, btc=btc, alt=alt, reserve=slice_)


def buyday_line(buy_day, monthly, reserve, btc_share, in_window,
                cur="US$", esc=lambda x: x):
    """-> the 📌 action line on buy day, "" otherwise (additive-only)."""
    if not buy_day:
        return ""
    if not monthly:
        return ("📌 <b>CRYPTO BUY DAY</b> <i>— amounts NOT SET, so no order is "
                "printed. Set balances.crypto_monthly_usd (what you can afford "
                "every month) and balances.crypto_reserve_usd (cash you already "
                "hold). Until then this line will not guess.</i>")
    c = contribution(monthly, reserve, btc_share, in_window)
    body = (f"send {cur}{c['total']:,.0f} — {cur}{c['btc']:,.0f} BTC "
            f"+ {cur}{c['alt']:,.0f} HYPE")
    if c["reserve"]:
        body += (f" (incl. {cur}{c['reserve']:,.0f} reserve slice, BTC-only, "
                 f"1 of ~{RESERVE_MONTHS})")
    return f"📌 <b>CRYPTO BUY DAY</b> — <i>{esc(body)}</i>"


# ──────────────── #158: the emergency-fund floor ────────────────────
# Owner, 2026-08-21, verbatim: "I have reduced my emergency fund to 15k sgd
# and i will not touch that ever again and u should hold me accountable for
# that."  Taken literally. The digest prints the floor on every buy day —
# the day money moves — because a commitment that is never restated is a
# commitment that quietly lapses.
#
# This line CANNOT read the balance (no bank feed exists here), so it does
# not pretend to verify. It asks. That is the honest form of accountability
# available: a standing question on the day the temptation occurs.
EMERGENCY_FLOOR_SGD = 15000.0


def emergency_line(floor_sgd, buy_day, esc=lambda x: x):
    """-> the floor reminder, on buy day only, or ""."""
    if not buy_day or not floor_sgd:
        return ""
    return (f"🛟 <i>EMERGENCY FUND FLOOR <b>S${floor_sgd:,.0f}</b> — owner "
            f"commitment 2026-08-21, never to be touched. This line cannot "
            f"read your bank; it asks. <b>Is it still whole?</b> If today's "
            f"crypto buy needs it, the buy is too big — cut the buy, not the "
            f"floor.</i>")
