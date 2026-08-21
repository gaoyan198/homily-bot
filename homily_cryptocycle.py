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

The engine ALSO requires CRYPTO_SLEEVE §3's other conditions (trough window
closed, BTC-only, <= the sanctioned leverage). This line reports the timing
condition only and says so — it is a WATCH, never an authorisation.
"""
import datetime

PCT = 0.30                 # above the running cycle low
HOLD_WKS = 8               # consecutive weeks above the line
LAST_PEAK = datetime.date(2025, 10, 6)          # frozen chronology, §41
TROUGH_WINDOW = (datetime.date(2026, 8, 25), datetime.date(2026, 12, 23))


def cycle_state(bars, pct=PCT, hold_wks=HOLD_WKS, since=LAST_PEAK, today=None):
    """bars: ascending [(date, o, h, l, c), ...] daily BTC. -> state dict, or
    None when there is nothing to read.

    Replays the SAME loop the study used, so the digest and BACKTEST_RESULTS
    can never drift: track the running low, arm on the first close above the
    trigger, disarm on any close back below, fire after hold_wks weeks."""
    w = [b for b in bars if b[0] >= since]
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
    held = (today - armed).days if armed else 0
    return dict(price=c, asof=dt, low=low, low_date=low_date, trigger=trigger,
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
    win = ""
    if s["in_trough_window"]:
        win = (f" · 🎯 in the projected trough window "
               f"({TROUGH_WINDOW[0]:%Y-%m-%d}…{TROUGH_WINDOW[1]:%Y-%m-%d}) "
               f"— spot accumulation is HEAVY here")
    return f"₿ <i>CYCLE: {esc(head)} — {esc(tail)}{win}</i>"
