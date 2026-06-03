"""Containment logic: cruft classification + groom must be correct."""
from sentinel.contain import _is_cruft, groom, rescue


def test_cruft_vs_work():
    assert _is_cruft("blue_agent_logs.json")
    assert _is_cruft("push-to-github.command")
    assert _is_cruft(".DS_Store")
    assert _is_cruft("sub/dir/run.log")
    assert not _is_cruft("decepticon_attacks.py")
    assert not _is_cruft("README.md")
    assert not _is_cruft("Dockerfile.blue-swarm")


def test_groom_reports_then_applies(tmp_path):
    (tmp_path / ".gitignore").write_text(".DS_Store\n")
    res = groom(tmp_path, apply=False)
    assert "__pycache__/" in res["missing"]
    assert ".DS_Store" not in res["missing"]       # already present
    assert not res["applied"]

    res2 = groom(tmp_path, apply=True)
    assert res2["applied"]
    gi = (tmp_path / ".gitignore").read_text()
    assert "__pycache__/" in gi and "venv/" in gi


def test_rescue_dryrun_classifies(tmp_path, monkeypatch):
    # rescue dry-run on a non-repo: uncommitted() returns nothing, so empty plan
    plan = rescue(tmp_path, commit=False)
    assert plan["work"] == [] and plan["committed"] is False
