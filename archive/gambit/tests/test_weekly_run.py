"""G-S5 loop + digest + freeze tests. The digest golden (homily #49) is built
BEFORE the first send and pins the render byte-for-byte; validate gates the send
on it. weekly_run.run_once must write a hash-verifiable ledger and snapshot
(the K4 integrity property). The engine-freeze manifest must pass on the tree as
committed and fail the moment a frozen signal file changes (EXECUTION §0.6).
"""
from pathlib import Path

import gambit_digest as gd
import gambit_freeze
import gambit_journal as gj
import gambit_paper as gp
import weekly_run
import test_gambit_paper as T

GOLDEN = Path(__file__).parent / "golden_digest.txt"


def _scenario():
    series, inds, qqq = T.world()
    frs = T.late_fridays(qqq)
    state = gj.new_state(frs[0])
    gp.weekly_step(state, series, inds, qqq, frs[0])
    _, digest = gp.weekly_step(state, series, inds, qqq, frs[1])
    return state, series, inds, qqq, frs, digest


def test_digest_matches_golden():
    _, _, _, _, _, digest = _scenario()
    got = gd.render(digest)
    want = GOLDEN.read_text().rstrip("\n")
    assert got == want, (
        "digest render drifted from the golden — regenerate deliberately "
        "(scratchpad gen_golden.py) and eyeball before committing.\n\n"
        f"--- got ---\n{got}\n--- want ---\n{want}")


def test_digest_never_implies_a_live_order():
    _, _, _, _, _, digest = _scenario()
    text = gd.render(digest).lower()
    assert "live_orders=off" in text and "paper" in text
    assert "no real order" in text


def test_run_once_writes_verifiable_ledger_and_snapshot(tmp_path):
    series, inds, qqq = T.world()
    frs = T.late_fridays(qqq)
    j, s = tmp_path / "j.csv", tmp_path / "snap.json"
    state = gj.new_state(frs[0])
    weekly_run.run_once(state, series, inds, qqq, frs[0], journal=j, snapshot=s)
    weekly_run.run_once(state, series, inds, qqq, frs[1], journal=j, snapshot=s)
    ok, bad = gj.verify(j)
    assert ok and bad is None, "the loop must leave a hash-verifiable ledger"
    assert gj.load_snapshot(s)["positions"], "snapshot must persist the book"
    assert any(r["event"] == "FILL" for r in gj.read_rows(j)), "fills journaled"


def test_freeze_manifest_passes_on_committed_tree():
    assert gambit_freeze.check() == [], \
        "the frozen engine must match its manifest as committed"


def test_freeze_detects_a_changed_engine_file(tmp_path):
    # copy the frozen set + manifest, mutate one file, expect a failure
    import json
    man = {f: gambit_freeze._sha(Path(f)) for f in gambit_freeze.FROZEN}
    (tmp_path / "engine_manifest.json").write_text(json.dumps(man))
    for f in gambit_freeze.FROZEN:
        (tmp_path / f).write_bytes(Path(f).read_bytes())
    tampered = tmp_path / gambit_freeze.FROZEN[0]
    tampered.write_bytes(tampered.read_bytes() + b"\n# silent edit\n")
    fails = gambit_freeze.check(root=tmp_path,
                                manifest=tmp_path / "engine_manifest.json")
    assert fails and gambit_freeze.FROZEN[0] in fails[0], \
        "a changed frozen file must fail the freeze check"
