#!/usr/bin/env python3
"""
R-2029 verdict freeze (#117, ROADMAP §5) — the three-fork rule as a checked
artifact, not a paragraph.

ROADMAP §3 pre-registers what the 2029-07 scorecard read binds us to, and
§4 what the 2036-07 read binds us to, and both say the same thing about
themselves: the rule and the band method are frozen NOW so future-us cannot
re-shop them after seeing the data. A paragraph cannot enforce that — an
edit is a diff nobody re-reads. This module turns the promise into a pin:

  verdict_freeze.json  sha256 of the R-2029 rule text (§3, from the rule's
                       first line through "demotion is not deletion"), of
                       the R-2036 rule text (§4's binding-read paragraph —
                       pinned too, or the 2036 collapse rule would be the
                       one editable clause of the same rule), and of the
                       SOURCE of the band method (#71 reuses D-39's block
                       bootstrap: resample_indices · moic_of · block_moics
                       · percentiles · paired_beats + BLOCK/N_RESAMPLES/
                       SEED/PCTS) — plus the fork clauses verbatim, so a
                       reader sees what was pinned without hashing anything

validate [82] recomputes every hash and fails the build on any drift. A
DELIBERATE change is `python homily_verdict.py --repin`, which rewrites the
file with today's date — and [82] then also requires a PRD §8.5 note dated
that day naming #117, so a re-pin cannot be quiet either. Nothing here
reads market data; it reads two markdown files and one Python module.
"""
import os, re, sys, json, hashlib, inspect, datetime

HERE = os.path.dirname(os.path.abspath(__file__))
FREEZE = os.path.join(HERE, "verdict_freeze.json")
ROADMAP = os.path.join(HERE, "ROADMAP.md")
PRD = os.path.join(HERE, "PRD.md")

# (start marker, end marker) — the rule text is everything from the first
# line that starts with the start marker through the END of the paragraph
# that contains the end marker
R2029 = ("**R-2029 (pre-registered, the three-fork rule):**",
         "demotion is not deletion")
R2036 = ("**R-2036 (pre-registered):**", "recorded as such.")
BAND_FUNCS = ("resample_indices", "moic_of", "block_moics", "percentiles",
              "paired_beats")
BAND_CONSTS = ("BLOCK", "N_RESAMPLES", "SEED", "PCTS")
# the clauses a reader should be able to see pinned; each must appear
# verbatim inside the R-2029 / R-2036 text
FORKS = (
    "**(a) Edge above the band → SCALE.**",
    "**(b) Edge inside the band → HOLD & CHEAPEN.**",
    "**(c) Edge below −band → DEMOTE TO DISCIPLINE MODE.**",
    "the buy-day copilot routes 100% to the index leg",
    "⭐/tiers/ranks go info-only",
    "the swing sleeve winds down at its next KILL/verdict boundary",
    "cash sleeve only, since-inception",
    "any change to the method before this read voids the read",
    "demotion is not deletion",
    "fork (b) collapses into (c)**",
    "No re-benchmarking",
    "no window-shopping the start date",
)


def _sha(text):
    return hashlib.sha256(text.encode()).hexdigest()


def _flat(text):
    """Markdown hard-wraps at ~72 columns, so a clause can straddle a line
    break; markers and fork clauses are matched on whitespace-collapsed
    text. Hashes stay on the RAW text — a re-wrap is still an edit."""
    return re.sub(r"\s+", " ", text)


def section(md, markers):
    """The rule text: from the start marker's line to the end of the
    paragraph holding the end marker. Raises if either is missing — a
    missing marker IS drift."""
    start, end = markers
    i = md.index(start)
    # locate the end marker on flattened text, then map back to the raw
    # paragraph that holds it (paragraphs are blank-line separated)
    paras, pos = md[i:].split("\n\n"), 0
    for n, para in enumerate(paras):
        if end in _flat(para):
            return "\n\n".join(paras[:n + 1])
    raise ValueError(f"end marker not found after start: {end!r}")


def band_method_source():
    import homily_bootstrap as hb
    parts = [f"{c} = {getattr(hb, c)!r}" for c in BAND_CONSTS]
    parts += [inspect.getsource(getattr(hb, f)) for f in BAND_FUNCS]
    return "\n".join(parts)


def compute():
    md = open(ROADMAP, encoding="utf-8").read()
    r29, r36 = section(md, R2029), section(md, R2036)
    both = _flat(r29 + "\n" + r36)
    missing = [f for f in FORKS if f not in both]
    return {"_v": 1,
            "r2029_sha256": _sha(r29), "r2036_sha256": _sha(r36),
            "band_method_sha256": _sha(band_method_source()),
            # JSON-shaped (tuples → lists) so stored == recomputed
            "band_constants": json.loads(json.dumps(
                {c: getattr(__import__("homily_bootstrap"), c)
                 for c in BAND_CONSTS})),
            "forks": list(FORKS), "forks_missing": missing}


def load():
    with open(FREEZE) as f:
        return json.load(f)


def drift(stored=None, current=None):
    """-> list of human lines naming what moved (empty = frozen intact)."""
    stored, current = stored or load(), current or compute()
    out = []
    for k, what in (("r2029_sha256", "ROADMAP §3 R-2029 rule text"),
                    ("r2036_sha256", "ROADMAP §4 R-2036 rule text"),
                    ("band_method_sha256", "band method source (homily_bootstrap)")):
        if stored.get(k) != current.get(k):
            out.append(f"{what} changed since the {stored.get('pinned')} pin")
    if stored.get("band_constants") != current.get("band_constants"):
        out.append(f"band constants moved: {stored.get('band_constants')} → "
                   f"{current.get('band_constants')}")
    if current.get("forks_missing"):
        out.append("fork clauses no longer verbatim in ROADMAP: "
                   + "; ".join(current["forks_missing"]))
    return out


def prd_note_dated(day, prd=PRD):
    """PRD §8.5 carries an entry '**YYYY-MM-DD … #117' for the pin date."""
    text = open(prd, encoding="utf-8").read()
    sec = text[text.index("### 8.5 Execution notes"):]
    return any(day in ln and "#117" in ln
               for ln in sec.split("\n\n") if ln.startswith(f"**{day}"))


def repin(today=None):
    today = today or datetime.date.today()
    doc = compute()
    if doc["forks_missing"]:
        raise SystemExit("cannot pin: fork clauses missing from ROADMAP — "
                         + "; ".join(doc["forks_missing"]))
    doc.pop("forks_missing")
    doc["pinned"] = today.isoformat()
    doc["_comment"] = ("R-2029/R-2036 verdict rules + #71 band method, pinned "
                       "(#117). Re-pin ONLY with `python homily_verdict.py "
                       "--repin` AND a PRD §8.5 note dated the same day naming "
                       "#117; validate [82] enforces both.")
    with open(FREEZE, "w") as f:
        json.dump(doc, f, indent=1, sort_keys=True)
        f.write("\n")
    return doc


if __name__ == "__main__":
    if "--repin" in sys.argv:
        d = repin()
        print(f"pinned {d['pinned']}: R-2029 {d['r2029_sha256'][:12]} · "
              f"R-2036 {d['r2036_sha256'][:12]} · band {d['band_method_sha256'][:12]}")
        sys.exit(0)
    lines = drift()
    print("\n".join(lines) if lines else
          f"verdict freeze intact (pinned {load()['pinned']})")
    sys.exit(1 if lines else 0)
