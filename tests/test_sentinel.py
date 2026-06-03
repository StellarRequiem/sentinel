"""The classifier and structure checks must be deterministic and correct."""
from sentinel.checks import classify, readme_claims_pypi, structure


def rep(**over):
    r = {"git": {"ahead": 0, "behind": 0, "dirty": 0, "has_remote": True},
         "age": 1, "structure": {"tests": True}, "pypi_false": False}
    r.update(over)
    return r


def test_clean_is_green():
    assert classify(rep())[0] == "green"


def test_unpushed_is_red():
    lvl, reasons = classify(rep(git={"ahead": 2, "behind": 0, "dirty": 0, "has_remote": True}))
    assert lvl == "red"
    assert any("unpushed" in r for r in reasons)


def test_uncommitted_recent_yellow_but_stale_red():
    assert classify(rep(git={"ahead": 0, "behind": 0, "dirty": 3, "has_remote": True}, age=1))[0] == "yellow"
    assert classify(rep(git={"ahead": 0, "behind": 0, "dirty": 3, "has_remote": True}, age=10))[0] == "red"


def test_false_pypi_claim_is_red():
    lvl, reasons = classify(rep(pypi_false=True))
    assert lvl == "red"
    assert any("PyPI" in r for r in reasons)


def test_local_only_and_no_tests_are_yellow():
    assert classify(rep(git={"ahead": 0, "behind": 0, "dirty": 0, "has_remote": False}))[0] == "yellow"
    assert classify(rep(structure={"tests": False}))[0] == "yellow"


def test_structure_and_pypi_claim(tmp_path):
    (tmp_path / "README.md").write_text("install with: pip install foo")
    (tmp_path / "tests").mkdir()
    (tmp_path / "pyproject.toml").write_text('[project]\nname = "foo"\n')
    st = structure(tmp_path)
    assert st["readme"] and st["tests"] and st["name"] == "foo"
    assert readme_claims_pypi(tmp_path, "foo")            # bare pip install -> claims PyPI
    (tmp_path / "README.md").write_text('pip install "git+https://x/foo"')
    assert not readme_claims_pypi(tmp_path, "foo")        # git+ install -> not a PyPI claim
