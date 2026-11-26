#!/usr/bin/env python3
"""
Delivery adapter (#118a, ROADMAP §5) — the digest behind ONE send interface,
with a second channel that is not Telegram.

ROADMAP §4 plans for the delivery channel to die within the decade. The
three Telegram senders in daily_run (send / send_photo / send_document)
are the only Telegram code in the book, and each now asks this module
first: if `HOMILY_DELIVERY` names an alternate sink, the message goes
there and Telegram is never touched. Unset (the default) = Telegram,
unchanged. Kept as a dormant code path — no standing infra, no secret.

Sinks
  file:<dir>   file-drop. One self-contained HTML bundle per run date,
               `<dir>/digest_YYYY-MM-DD.html`: the digest text (it is
               already Telegram-HTML), then every chart card inline as a
               data-URI PNG with its caption, then a link per document
               (copied beside it). `<dir>/latest.html` is a copy of the
               newest bundle. A synced folder (iCloud/Dropbox/Syncthing)
               or a web root turns this into a channel with no code.

Not built: SMTP. It needs a credential kept live, which the item's own
gate forbids, and a file in a synced folder already reaches a phone.
Drilled 2026-09-11: one real launchd-scheduled run (#118b) on the owner's
Mac delivered through this sink — PRD §8.5.
"""
import os, html, base64, shutil, datetime

ENV = "HOMILY_DELIVERY"
_STYLE = ("<style>body{font:15px/1.45 -apple-system,Segoe UI,sans-serif;"
          "max-width:52em;margin:1.5em auto;padding:0 1em;white-space:pre-wrap}"
          "pre{white-space:pre;overflow-x:auto;background:#f4f4f4;padding:.5em}"
          "img{max-width:100%;display:block;margin:.5em 0}"
          "figure{margin:1.2em 0}figcaption{color:#555}</style>")


def sink():
    """-> ("file", dir) or None when Telegram (the default) is the channel."""
    v = os.getenv(ENV, "").strip()
    if v.startswith("file:") and v[5:]:
        return "file", os.path.expanduser(v[5:])
    return None


def active():
    return sink() is not None


def _day():
    import homily_ledger
    return homily_ledger.run_date()


def _bundle(d, day=None):
    day = day or _day()
    os.makedirs(d, exist_ok=True)
    return os.path.join(d, f"digest_{day.isoformat()}.html")


def _append(path, fragment, title=None):
    new = not os.path.exists(path)
    with open(path, "a", encoding="utf-8") as f:
        if new:
            f.write(f"<meta charset='utf-8'><title>{html.escape(title or 'Homily digest')}"
                    f"</title>{_STYLE}\n")
        f.write(fragment + "\n")
    shutil.copyfile(path, os.path.join(os.path.dirname(path), "latest.html"))
    return path


def send(text, day=None):
    """The digest text. It is Telegram-HTML (<b>/<i>/<pre>/<code>) which
    is a browser subset, so it is written as-is inside a <div>."""
    _, d = sink()
    p = _bundle(d, day)
    _append(p, f"<div class='digest'>{text}</div>",
            title=f"Homily digest {os.path.basename(p)[7:17]}")
    print(f"[delivered to file-drop {p}]")
    return p


def send_photo(png, caption, day=None):
    _, d = sink()
    p = _bundle(d, day)
    b64 = base64.b64encode(png).decode()
    _append(p, f"<figure><img src='data:image/png;base64,{b64}' alt=''>"
               f"<figcaption>{html.escape(caption)}</figcaption></figure>")
    print(f"[chart delivered to file-drop, {len(png)} bytes]")
    return p


def send_document(path, caption, day=None):
    _, d = sink()
    p = _bundle(d, day)
    name = os.path.basename(path)
    dest = os.path.join(d, name)
    if os.path.abspath(dest) != os.path.abspath(path):
        shutil.copyfile(path, dest)
    _append(p, f"<p>📎 <a href='{html.escape(name)}'>{html.escape(name)}</a> — "
               f"{html.escape(caption)}</p>")
    print(f"[document {name} delivered to file-drop]")
    return p
