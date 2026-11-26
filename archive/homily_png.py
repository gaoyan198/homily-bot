#!/usr/bin/env python3
"""
F1 chart cards (backlog #35) — pure-stdlib PNG chart per actionable name.
==========================================================================

One 900×500 PNG per name (D-35): price panel (1y closes, add-zone band,
POC / nearest-resistance lines) · right 200px horizontal chip histogram ·
bottom weekly-circle ribbon. daily_run sendPhoto's the top-3 actionable
names (⭐/🔵/🎯) after the digest, so the digest becomes glanceable with
zero dependencies and zero hosting.

Engine freeze (EXECUTION.md §0): every SIGNAL on the chart — add zone,
POC, resistance, state, weekly circles — is read from the frozen engines'
own outputs (DannySignal fields; homily_clone.homily_circle called on
weekly-close prefixes for the ribbon's history). The only locally computed
visual is the chip-histogram BACKDROP: ChipProfile deliberately exposes
peaks, not bins, and homily_chips is frozen, so _display_bins() re-bins
the same decayed volume-at-price using the engine's own NBINS/HALF_LIFE
constants — presentation only, never a signal input. If Phase C ever
re-tunes those constants the backdrop follows automatically.

Determinism is the test contract: no clock, no randomness, text rendered
from a built-in 5×7 bitmap font — identical inputs give identical pixels,
so validate (check [28]) pins a SHA-256 of the raw RGB buffer on fixture
bars. Hash the PIXELS, not the .png: zlib's compressed bytes aren't
guaranteed stable across library builds; the pixel buffer is.
"""
import struct
import zlib
import hashlib

from homily_chips import NBINS, HALF_LIFE
from homily_clone import homily_circle
from homily_data import weekly_closes

W, H = 900, 500
PAD_L, PAD_T = 56, 30          # room for price labels / title
HIST_W = 200                   # right-hand chip-histogram panel
RIBBON_H = 18                  # weekly-circle strip along the bottom
PLOT_R = W - HIST_W - 12       # price panel right edge
PLOT_B = H - RIBBON_H - 14     # price panel bottom edge
VIEW_BARS = 252                # ~1 trading year in the price panel
RIBBON_WEEKS = 52

BG = (255, 255, 255)
TEXT = (40, 40, 40)
AXIS = (120, 120, 120)
GRID = (228, 228, 228)
PRICE = (25, 70, 160)
ZONE = (205, 235, 210)         # add-zone band fill
POC = (240, 150, 30)
RES = (205, 60, 60)
HIST_PROFIT = (160, 205, 170)  # chips below last close (in profit)
HIST_TRAPPED = (215, 170, 170) # chips above last close (trapped)
RIB = {"RED": (215, 60, 50), "AMBER": (235, 180, 60),
       "WHITE": (208, 208, 208)}

# 5×7 bitmap font, one int per row, bit 4 = leftmost pixel. Digits, A–Z and
# the handful of punctuation the labels use — nothing else ever renders.
FONT = {
    "A": (0x0E, 0x11, 0x11, 0x1F, 0x11, 0x11, 0x11),
    "B": (0x1E, 0x11, 0x11, 0x1E, 0x11, 0x11, 0x1E),
    "C": (0x0E, 0x11, 0x10, 0x10, 0x10, 0x11, 0x0E),
    "D": (0x1E, 0x11, 0x11, 0x11, 0x11, 0x11, 0x1E),
    "E": (0x1F, 0x10, 0x10, 0x1E, 0x10, 0x10, 0x1F),
    "F": (0x1F, 0x10, 0x10, 0x1E, 0x10, 0x10, 0x10),
    "G": (0x0E, 0x11, 0x10, 0x17, 0x11, 0x11, 0x0F),
    "H": (0x11, 0x11, 0x11, 0x1F, 0x11, 0x11, 0x11),
    "I": (0x0E, 0x04, 0x04, 0x04, 0x04, 0x04, 0x0E),
    "J": (0x07, 0x02, 0x02, 0x02, 0x02, 0x12, 0x0C),
    "K": (0x11, 0x12, 0x14, 0x18, 0x14, 0x12, 0x11),
    "L": (0x10, 0x10, 0x10, 0x10, 0x10, 0x10, 0x1F),
    "M": (0x11, 0x1B, 0x15, 0x15, 0x11, 0x11, 0x11),
    "N": (0x11, 0x11, 0x19, 0x15, 0x13, 0x11, 0x11),
    "O": (0x0E, 0x11, 0x11, 0x11, 0x11, 0x11, 0x0E),
    "P": (0x1E, 0x11, 0x11, 0x1E, 0x10, 0x10, 0x10),
    "Q": (0x0E, 0x11, 0x11, 0x11, 0x15, 0x12, 0x0D),
    "R": (0x1E, 0x11, 0x11, 0x1E, 0x14, 0x12, 0x11),
    "S": (0x0F, 0x10, 0x10, 0x0E, 0x01, 0x01, 0x1E),
    "T": (0x1F, 0x04, 0x04, 0x04, 0x04, 0x04, 0x04),
    "U": (0x11, 0x11, 0x11, 0x11, 0x11, 0x11, 0x0E),
    "V": (0x11, 0x11, 0x11, 0x11, 0x11, 0x0A, 0x04),
    "W": (0x11, 0x11, 0x11, 0x15, 0x15, 0x15, 0x0A),
    "X": (0x11, 0x11, 0x0A, 0x04, 0x0A, 0x11, 0x11),
    "Y": (0x11, 0x11, 0x0A, 0x04, 0x04, 0x04, 0x04),
    "Z": (0x1F, 0x01, 0x02, 0x04, 0x08, 0x10, 0x1F),
    "0": (0x0E, 0x11, 0x13, 0x15, 0x19, 0x11, 0x0E),
    "1": (0x04, 0x0C, 0x04, 0x04, 0x04, 0x04, 0x0E),
    "2": (0x0E, 0x11, 0x01, 0x02, 0x04, 0x08, 0x1F),
    "3": (0x1F, 0x02, 0x04, 0x02, 0x01, 0x11, 0x0E),
    "4": (0x02, 0x06, 0x0A, 0x12, 0x1F, 0x02, 0x02),
    "5": (0x1F, 0x10, 0x1E, 0x01, 0x01, 0x11, 0x0E),
    "6": (0x06, 0x08, 0x10, 0x1E, 0x11, 0x11, 0x0E),
    "7": (0x1F, 0x01, 0x02, 0x04, 0x08, 0x08, 0x08),
    "8": (0x0E, 0x11, 0x11, 0x0E, 0x11, 0x11, 0x0E),
    "9": (0x0E, 0x11, 0x11, 0x0F, 0x01, 0x02, 0x0C),
    ".": (0x00, 0x00, 0x00, 0x00, 0x00, 0x0C, 0x0C),
    "-": (0x00, 0x00, 0x00, 0x1F, 0x00, 0x00, 0x00),
    "/": (0x01, 0x01, 0x02, 0x04, 0x08, 0x10, 0x10),
    ":": (0x00, 0x0C, 0x0C, 0x00, 0x0C, 0x0C, 0x00),
    "%": (0x19, 0x1A, 0x02, 0x04, 0x08, 0x0B, 0x13),
    " ": (0, 0, 0, 0, 0, 0, 0),
}


class Canvas:
    """Row-major RGB byte buffer with the few primitives the chart needs."""

    def __init__(self, w=W, h=H, bg=BG):
        self.w, self.h = w, h
        self.px = bytearray(bytes(bg) * (w * h))

    def put(self, x, y, c):
        if 0 <= x < self.w and 0 <= y < self.h:
            i = (y * self.w + x) * 3
            self.px[i:i + 3] = bytes(c)

    def rect(self, x0, y0, x1, y1, c):
        for y in range(max(0, y0), min(self.h - 1, y1) + 1):
            for x in range(max(0, x0), min(self.w - 1, x1) + 1):
                self.put(x, y, c)

    def hline(self, x0, x1, y, c):
        for x in range(min(x0, x1), max(x0, x1) + 1):
            self.put(x, y, c)

    def vline(self, x, y0, y1, c):
        for y in range(min(y0, y1), max(y0, y1) + 1):
            self.put(x, y, c)

    def line(self, x0, y0, x1, y1, c):
        dx, dy = abs(x1 - x0), -abs(y1 - y0)
        sx, sy = (1 if x0 < x1 else -1), (1 if y0 < y1 else -1)
        err = dx + dy
        while True:
            self.put(x0, y0, c)
            if x0 == x1 and y0 == y1:
                return
            e2 = 2 * err
            if e2 >= dy:
                err += dy
                x0 += sx
            if e2 <= dx:
                err += dx
                y0 += sy

    def text(self, x, y, s, c=TEXT, scale=1):
        for ch in str(s).upper():
            glyph = FONT.get(ch, FONT[" "])
            for r, row in enumerate(glyph):
                for k in range(5):
                    if row & (1 << (4 - k)):
                        self.rect(x + k * scale, y + r * scale,
                                  x + k * scale + scale - 1,
                                  y + r * scale + scale - 1, c)
            x += 6 * scale


def png_bytes(canvas):
    """RGB canvas -> a valid 8-bit truecolour PNG (filter 0 per scanline)."""
    def chunk(typ, data):
        return (struct.pack(">I", len(data)) + typ + data
                + struct.pack(">I", zlib.crc32(typ + data)))
    ihdr = struct.pack(">IIBBBBB", canvas.w, canvas.h, 8, 2, 0, 0, 0)
    stride = canvas.w * 3
    raw = b"".join(b"\x00" + bytes(canvas.px[y * stride:(y + 1) * stride])
                   for y in range(canvas.h))
    return (b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", ihdr)
            + chunk(b"IDAT", zlib.compress(raw, 9)) + chunk(b"IEND", b""))


def _display_bins(bars, nbins=NBINS, half_life=HALF_LIFE):
    """Decayed volume-at-price over the full window — the histogram BACKDROP
    only (see module docstring); mirrors homily_chips' binning with the
    engine's own constants. -> (lo, width, [weight]*nbins)."""
    lo = min(b[3] for b in bars)
    hi = max(b[2] for b in bars)
    if hi <= lo:
        hi = lo * 1.001
    width = (hi - lo) / nbins
    weights = [0.0] * nbins
    decay = 0.5 ** (1.0 / half_life)
    n = len(bars)
    for idx, (_d, _o, h, l, _c, v) in enumerate(bars):
        w = v * (decay ** (n - 1 - idx))
        b_lo = max(0, min(nbins - 1, int((l - lo) / width)))
        b_hi = max(0, min(nbins - 1, int((h - lo) / width)))
        span = b_hi - b_lo + 1
        if span == 1:
            weights[b_lo] += w
            continue
        mid = (b_lo + b_hi) / 2.0
        tri = [1.0 - abs(j - mid) / (span / 2.0 + 1e-9) + 0.1
               for j in range(b_lo, b_hi + 1)]
        tsum = sum(tri)
        for j, t in zip(range(b_lo, b_hi + 1), tri):
            weights[j] += w * t / tsum
    return lo, width, weights


def _ribbon_circles(ticker, bars, weeks=RIBBON_WEEKS):
    """Last `weeks` weekly circles, oldest first — homily_circle() re-run on
    each weekly-close prefix (reading the frozen engine, not re-deriving it)."""
    wk = weekly_closes(bars)
    out = []
    for i in range(max(35, len(wk) - weeks), len(wk)):   # EMA needs warm-up
        out.append(homily_circle(ticker, wk[:i + 1]).circle)
    return out[-weeks:]


def chart_canvas(ticker, bars, sig):
    """The deterministic renderer: ticker + raw bars + that name's
    DannySignal -> Canvas. Everything level-shaped comes from `sig`."""
    cv = Canvas()
    view = bars[-VIEW_BARS:]
    closes = [b[4] for b in view]
    chips = sig.chips

    # y-scale: the 1y closes + the add zone (the actionable level). POC and
    # resistance draw only if they land inside — a resistance 8× above a
    # crashed price would squash the price action into a sliver otherwise.
    marks = list(closes)
    if sig.add_zone:
        marks += list(sig.add_zone)
    lo, hi = min(marks), max(marks)
    pad = (hi - lo or lo * 0.01) * 0.05
    lo, hi = lo - pad, hi + pad

    def ynorm(p):
        return int(round(PLOT_B - (p - lo) / (hi - lo) * (PLOT_B - PAD_T)))

    def xnorm(i):
        return int(round(PAD_L + i / max(1, len(view) - 1) * (PLOT_R - PAD_L)))

    # add-zone band first, under everything else
    if sig.add_zone:
        cv.rect(PAD_L + 1, ynorm(sig.add_zone[1]), PLOT_R - 1,
                ynorm(sig.add_zone[0]), ZONE)

    # horizontal grid + price labels
    for k in range(5):
        p = lo + (hi - lo) * k / 4
        y = ynorm(p)
        cv.hline(PAD_L + 1, PLOT_R - 1, y, GRID)
        cv.text(4, y - 3, f"{p:g}"[:8])

    # engine levels: POC (orange) and nearest chip resistance (red), each
    # drawn only when it falls inside the 1y view
    if lo <= chips.poc <= hi:
        cv.hline(PAD_L + 1, PLOT_R - 1, ynorm(chips.poc), POC)
        cv.text(PLOT_R - 58, ynorm(chips.poc) - 9,
                f"POC {chips.poc:g}"[:12], POC)
    if chips.resistance and lo <= chips.resistance[0][0] <= hi:
        r0 = chips.resistance[0][0]
        cv.hline(PAD_L + 1, PLOT_R - 1, ynorm(r0), RES)
        cv.text(PLOT_R - 58, ynorm(r0) + 3, f"RES {r0:g}"[:12], RES)

    # 1y close polyline (doubled for a 2px stroke)
    for i in range(1, len(view)):
        x0, y0 = xnorm(i - 1), ynorm(closes[i - 1])
        x1, y1 = xnorm(i), ynorm(closes[i])
        cv.line(x0, y0, x1, y1, PRICE)
        cv.line(x0, y0 + 1, x1, y1 + 1, PRICE)

    # axes
    cv.vline(PAD_L, PAD_T, PLOT_B, AXIS)
    cv.hline(PAD_L, PLOT_R, PLOT_B, AXIS)

    # right panel: chip-histogram backdrop on the SAME y-scale; green below
    # the close (in profit), red above (trapped) — the Homily read at a glance
    blo, bw, weights = _display_bins(bars)
    wmax = max(weights) or 1.0
    hx0 = PLOT_R + 8
    for j, wgt in enumerate(weights):
        p = blo + (j + 0.5) * bw
        if not lo <= p <= hi or wgt <= 0:
            continue
        y = ynorm(p)
        ln = int(wgt / wmax * (HIST_W - 16))
        if ln:
            colour = HIST_PROFIT if p <= chips.last else HIST_TRAPPED
            cv.hline(hx0, hx0 + ln, y, colour)
            cv.hline(hx0, hx0 + ln, y + 1, colour)
    cv.vline(hx0 - 4, PAD_T, PLOT_B, AXIS)
    cv.text(hx0, PLOT_B + 4, "CHIPS", AXIS)

    # weekly-circle ribbon along the bottom of the price panel
    circles = _ribbon_circles(ticker, bars)
    if circles:
        cw = (PLOT_R - PAD_L) // max(1, len(circles))
        for i, circ in enumerate(circles):
            x0 = PAD_L + i * cw
            cv.rect(x0 + 1, PLOT_B + 4, x0 + cw - 1,
                    PLOT_B + RIBBON_H - 2, RIB.get(circ, RIB["WHITE"]))
    cv.text(4, PLOT_B + 4, "1Y WK", AXIS)

    # title: everything else in the digest row stays in the caption
    zone = (f"  ADD {sig.add_zone[0]:g}-{sig.add_zone[1]:g}"
            if sig.add_zone else "")
    cv.text(PAD_L, 8, f"{ticker} {sig.state} {chips.last:g}{zone}"[:60],
            TEXT, scale=2)
    return cv


def chart_png(ticker, bars, sig):
    return png_bytes(chart_canvas(ticker, bars, sig))


def pixel_hash(canvas):
    """SHA-256 of the raw RGB buffer — the check-[28] contract (stable where
    compressed PNG bytes may not be across zlib builds)."""
    return hashlib.sha256(bytes(canvas.px)).hexdigest()


if __name__ == "__main__":
    # eyeball run: render the golden archetypes to files + print pixel hashes
    import os
    import sys
    import tempfile
    from homily_golden import _up, _dn, _bottoming, _bars

    out = sys.argv[1] if len(sys.argv) > 1 else tempfile.mkdtemp(
        prefix="homily_charts_")
    os.makedirs(out, exist_ok=True)
    fixtures = {
        "UPP": (_bars([100 * 1.003 ** i for i in range(900)], [1e6] * 900),
                _up("UPP")[0]),
        "DWN": (_bars([100 * 0.997 ** i for i in range(900)], [1e6] * 900),
                _dn("DWN")[0]),
    }
    for tk, (bars, sig) in fixtures.items():
        cvs = chart_canvas(tk, bars, sig)
        path = os.path.join(out, f"chart_{tk}.png")
        with open(path, "wb") as f:
            f.write(png_bytes(cvs))
        print(f"{tk}: {sig.state:<10} pixel_hash {pixel_hash(cvs)}  -> {path}")
