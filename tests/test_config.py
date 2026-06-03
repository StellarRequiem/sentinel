"""Per-repo overrides must suppress intended-state flags; config must load safely."""
from sentinel.checks import classify
from sentinel.config import load_config


def test_overrides_suppress_intended_flags():
    rep = {"git": {"ahead": 0, "behind": 0, "dirty": 0, "has_remote": False},
           "age": 1, "structure": {"tests": False}, "pypi_false": False,
           "overrides": {"intentional_local": True, "no_tests_ok": True}}
    assert classify(rep)[0] == "green"          # local-only + no-tests both suppressed


def test_no_override_still_flags():
    rep = {"git": {"ahead": 0, "behind": 0, "dirty": 0, "has_remote": False},
           "age": 1, "structure": {"tests": True}, "pypi_false": False, "overrides": {}}
    assert classify(rep)[0] == "yellow"         # local-only still flagged without override


def test_load_config_missing(tmp_path):
    assert load_config(tmp_path / "nope.toml") == {"exclude": [], "repos": {}}


def test_load_config(tmp_path):
    (tmp_path / "c.toml").write_text('exclude = ["x"]\n[repos.foo]\nintentional_local = true\n')
    cfg = load_config(tmp_path / "c.toml")
    assert cfg["exclude"] == ["x"]
    assert cfg["repos"]["foo"]["intentional_local"] is True
