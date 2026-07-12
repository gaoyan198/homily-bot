"""G-S5 journal tests: the append-only SHA-256 hash chain (homily #62) — the
'un-fakeable from row 1' property (PRD §0.2). A retro-edit, deletion, or
reorder must break verify() at the tampered row; that is the K4 integrity gate
weekly_run refuses to append past.
"""
import datetime

import gambit_journal as gj


def _row(event, sym="", note=""):
    return {"date": "2026-07-10", "event": event, "symbol": sym, "notes": note}


def test_append_builds_verifiable_chain(tmp_path):
    p = tmp_path / "j.csv"
    gj.append_rows(p, [_row("SCAN"), _row("PROPOSE", "AAA"), _row("FILL", "AAA")])
    ok, bad = gj.verify(p)
    assert ok and bad is None, "a freshly written ledger must verify"
    rows = gj.read_rows(p)
    assert [r["event"] for r in rows] == ["SCAN", "PROPOSE", "FILL"]
    assert all(len(r["row_sha"]) == 64 for r in rows)
    assert rows[0]["row_sha"] != rows[1]["row_sha"], "chain must advance"


def test_append_is_incremental_and_still_verifies(tmp_path):
    p = tmp_path / "j.csv"
    tip1 = gj.append_rows(p, [_row("SCAN")])
    tip2 = gj.append_rows(p, [_row("FILL", "AAA")])
    assert tip1 != tip2
    ok, bad = gj.verify(p)
    assert ok and bad is None, "a second append must extend, not break, the chain"


def test_retro_edit_is_detected(tmp_path):
    p = tmp_path / "j.csv"
    gj.append_rows(p, [_row("SCAN"), _row("FILL", "AAA"), _row("FILL", "BBB")])
    text = p.read_text().splitlines()
    # tamper with the middle data row's notes field, leaving its sha in place
    text[2] = text[2].replace("FILL,AAA", "FILL,ZZZ")
    p.write_text("\n".join(text) + "\n")
    ok, bad = gj.verify(p)
    assert not ok and bad == 1, "editing row 1 must fail verify() at row 1"


def test_deletion_breaks_the_chain(tmp_path):
    p = tmp_path / "j.csv"
    gj.append_rows(p, [_row("SCAN"), _row("FILL", "AAA"), _row("FILL", "BBB")])
    lines = p.read_text().splitlines()
    del lines[2]                              # drop the middle row
    p.write_text("\n".join(lines) + "\n")
    ok, bad = gj.verify(p)
    assert not ok, "a deleted row must break the hash chain"


def test_unknown_event_rejected(tmp_path):
    p = tmp_path / "j.csv"
    try:
        gj.append_rows(p, [{"date": "2026-07-10", "event": "HACK"}])
        assert False, "unknown event must raise"
    except ValueError:
        pass


def test_snapshot_roundtrip(tmp_path):
    p = tmp_path / "snap.json"
    st = gj.new_state(datetime.date(2026, 7, 10))
    st["cash"] = 12345.67
    st["positions"]["AAA"] = {"qty": 3.0, "entry": 100.0, "entry_date": "2026-07-10"}
    gj.save_snapshot(p, st)
    back = gj.load_snapshot(p)
    assert back["cash"] == 12345.67 and back["positions"]["AAA"]["qty"] == 3.0
    assert gj.load_snapshot(tmp_path / "missing.json") is None
