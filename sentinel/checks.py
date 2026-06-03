"""sentinel checks — pure, deterministic repo health checks (stdlib only)."""
from __future__ import annotations

import subprocess
import urllib.error
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

try:
    import tomllib
except ModuleNotFoundError:  # pragma: no cover
    tomllib = None

_RANK = {"green": 0, "yellow": 1, "red": 2}


def _git(repo, *args) -> subprocess.CompletedProcess:
    return subprocess.run(["git", "-C", str(repo), *args], capture_output=True, text=True)


def is_git(repo) -> bool:
    return (Path(repo) / ".git").exists()


def git_status(repo) -> dict:
    branch = _git(repo, "branch", "--show-current").stdout.strip()
    dirty = len([ln for ln in _git(repo, "status", "--porcelain").stdout.splitlines() if ln.strip()])
    has_remote = bool(_git(repo, "remote").stdout.strip())
    ahead = behind = 0
    has_upstream = _git(repo, "rev-parse", "--abbrev-ref",
                        "--symbolic-full-name", "@{u}").returncode == 0
    if has_upstream:
        lr = _git(repo, "rev-list", "--left-right", "--count", "@{u}...HEAD").stdout.split()
        if len(lr) == 2:
            behind, ahead = int(lr[0]), int(lr[1])
    return {"branch": branch, "dirty": dirty, "has_remote": has_remote,
            "has_upstream": has_upstream, "ahead": ahead, "behind": behind}


def commit_age_days(repo):
    r = _git(repo, "log", "-1", "--format=%ct")
    if r.returncode != 0 or not r.stdout.strip():
        return None
    return (datetime.now(timezone.utc).timestamp() - int(r.stdout.strip())) / 86400


def pyproject_name(repo):
    p = Path(repo) / "pyproject.toml"
    if not p.exists() or tomllib is None:
        return None
    try:
        return tomllib.loads(p.read_text(encoding="utf-8")).get("project", {}).get("name")
    except Exception:
        return None


def structure(repo) -> dict:
    repo = Path(repo)
    has_tests = ((repo / "tests").is_dir() or any(repo.glob("test_*.py"))
                 or any(repo.glob("*/test_*.py")))
    return {"readme": (repo / "README.md").exists(), "tests": has_tests,
            "pyproject": (repo / "pyproject.toml").exists(), "name": pyproject_name(repo)}


def pypi_published(name, timeout=6):
    """True if on PyPI, False if 404, None if unknown (network error)."""
    if not name:
        return None
    try:
        with urllib.request.urlopen(f"https://pypi.org/pypi/{name}/json", timeout=timeout) as r:
            return r.status == 200
    except urllib.error.HTTPError as e:
        return False if e.code == 404 else None
    except Exception:
        return None


def readme_claims_pypi(repo, name) -> bool:
    """True if the README tells users to `pip install <name>` / `uv add <name>`
    in a way that implies PyPI (not a git+ / path / editable install)."""
    if not name:
        return False
    p = Path(repo) / "README.md"
    if not p.exists():
        return False
    for line in p.read_text(encoding="utf-8", errors="ignore").splitlines():
        low = line.lower()
        if (("pip install" in low or "uv add" in low) and name.lower() in low
                and "git+" not in low and "@" not in low and "install -e" not in low):
            return True
    return False


def classify(rep: dict) -> tuple[str, list[str]]:
    """Return (level, reasons) from a repo report dict. Pure — easy to test."""
    reasons: list[str] = []
    level = "green"

    def bump(to):
        nonlocal level
        if _RANK[to] > _RANK[level]:
            level = to

    g = rep.get("git", {})
    age = rep.get("age")
    st = rep.get("structure", {})

    if g.get("ahead", 0) > 0:
        reasons.append(f"{g['ahead']} unpushed")
        bump("red")
    if g.get("behind", 0) > 0:
        reasons.append(f"{g['behind']} behind remote")
        bump("yellow")
    if g.get("dirty", 0) > 0:
        reasons.append(f"{g['dirty']} uncommitted")
        bump("red" if (age and age > 3) else "yellow")
    if not g.get("has_remote", True):
        reasons.append("local-only")
        bump("yellow")
    if age is not None and age > 30:
        reasons.append(f"{int(age)}d stale")
        bump("yellow")
    if rep.get("pypi_false"):
        reasons.append("README claims PyPI but NOT published")
        bump("red")
    if not st.get("tests", True):
        reasons.append("no tests")
        bump("yellow")
    if not reasons:
        reasons.append("clean")
    return level, reasons
