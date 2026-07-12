"""[K6] LIVE_ORDERS safety gate (PRD §5.3, DESIGNS D-G1).

Prime directive: paper only. Live requires TWO artifacts (env flag + owner-
signed LIVE_ENABLE.md) AND a PRD that no longer defers P3. These tests pin
every arm of that gate.
"""
from pathlib import Path

import gambit_validate

PRD_DEFERRED = "... P3 (live pilot) is **deferred sine die**; ..."
PRD_P3_OPEN = "... P3 begins 2027-01-01 per owner sign-off ..."


def _root(tmp_path, prd=PRD_DEFERRED, enable=None):
    (tmp_path / "PRD.md").write_text(prd, encoding="utf-8")
    if enable is not None:
        (tmp_path / "LIVE_ENABLE.md").write_text(enable, encoding="utf-8")
    return tmp_path


def test_off_is_green(tmp_path):
    assert gambit_validate.check_k6(env={}, root=_root(tmp_path)) == []


def test_dry_is_green(tmp_path):
    assert gambit_validate.check_k6(
        env={"LIVE_ORDERS": "dry"}, root=_root(tmp_path)) == []


def test_unknown_flag_value_fails(tmp_path):
    fails = gambit_validate.check_k6(
        env={"LIVE_ORDERS": "yes-please"}, root=_root(tmp_path))
    assert any("not a legal state" in f for f in fails)


def test_on_without_enable_file_fails(tmp_path):
    fails = gambit_validate.check_k6(
        env={"LIVE_ORDERS": "on"}, root=_root(tmp_path))
    assert any("without owner-signed LIVE_ENABLE.md" in f for f in fails)


def test_enable_file_while_prd_defers_p3_fails(tmp_path):
    # staging the enable file early is itself a breach, even with flag off
    root = _root(tmp_path, enable="Enabled. — GY 2026-07-10")
    fails = gambit_validate.check_k6(env={}, root=root)
    assert any("PRD still defers P3" in f for f in fails)


def test_on_with_enable_but_deferred_prd_still_fails(tmp_path):
    root = _root(tmp_path, enable="Enabled. — GY 2026-07-10")
    fails = gambit_validate.check_k6(env={"LIVE_ORDERS": "on"}, root=root)
    assert fails, "two artifacts are not enough while the PRD defers P3"


def test_undated_enable_file_fails(tmp_path):
    root = _root(tmp_path, prd=PRD_P3_OPEN, enable="go live — GY")
    fails = gambit_validate.check_k6(env={"LIVE_ORDERS": "on"}, root=root)
    assert any("no dated owner line" in f for f in fails)


def test_legal_live_state_is_green(tmp_path):
    # the only configuration that may ever be green with flag=on: PRD no
    # longer defers P3 AND a dated owner-signed enable file exists
    root = _root(tmp_path, prd=PRD_P3_OPEN,
                 enable="I authorize live orders. — GY, 2027-01-05")
    assert gambit_validate.check_k6(env={"LIVE_ORDERS": "on"}, root=root) == []


def test_repo_state_is_paper_only():
    # the real repo, right now: no enable file, PRD defers P3, flag off
    root = Path(gambit_validate.__file__).resolve().parent
    assert not (root / "LIVE_ENABLE.md").exists()
    assert gambit_validate.check_k6(env={}, root=root) == []
