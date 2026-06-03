"""containment actions — groom (de-cruft) and rescue (save work-at-risk).

Reversible-first: `rescue` commits (never pushes, never discards); `groom` only
adds ignore patterns. The CLI defaults both to a dry-run.
"""
from __future__ import annotations

import subprocess
from datetime import datetime
from fnmatch import fnmatch
from pathlib import Path

# the standard ignore set every repo should carry
STD_IGNORE = [".DS_Store", "__pycache__/", "*.py[cod]", ".pytest_cache/",
              "*.command", "*.log", "*.tmp", "venv/", ".venv/",
              "node_modules/", "*.egg-info/", "dist/", "build/"]

# uncommitted files matching these are cruft (ignore), not work (commit)
CRUFT = ("*.command", "*.log", "*_logs.json", ".DS_Store", "*.tmp")


def _git(repo, *args) -> subprocess.CompletedProcess:
    return subprocess.run(["git", "-C", str(repo), *args], capture_output=True, text=True)


def _is_cruft(path: str) -> bool:
    base = path.rsplit("/", 1)[-1]
    return any(fnmatch(base, pat) or fnmatch(path, pat) for pat in CRUFT)


def uncommitted(repo) -> list[str]:
    return [ln[3:] for ln in _git(repo, "status", "--porcelain").stdout.splitlines() if ln.strip()]


def _append_ignore(repo, patterns) -> list[str]:
    gi = Path(repo) / ".gitignore"
    existing = gi.read_text(encoding="utf-8").splitlines() if gi.exists() else []
    have = {ln.strip() for ln in existing}
    add = [p for p in patterns if p not in have]
    if add:
        sep = "\n" if (existing and existing[-1].strip()) else ""
        with gi.open("a", encoding="utf-8") as f:
            f.write(sep + "\n".join(add) + "\n")
    return add


def groom(repo, apply=False) -> dict:
    """Report (and optionally add) the standard .gitignore patterns this repo lacks."""
    gi = Path(repo) / ".gitignore"
    have = ({ln.strip() for ln in gi.read_text(encoding="utf-8").splitlines()}
            if gi.exists() else set())
    missing = [p for p in STD_IGNORE if p not in have]
    if apply and missing:
        _append_ignore(repo, missing)
    return {"missing": missing, "applied": bool(apply and missing)}


def rescue(repo, commit=False) -> dict:
    """Classify a repo's uncommitted files into work vs. cruft; optionally
    gitignore the cruft and dated-WIP-commit the work. Never pushes, never discards."""
    files = uncommitted(repo)
    cruft = [f for f in files if _is_cruft(f)]
    work = [f for f in files if not _is_cruft(f)]
    out = {"work": work, "cruft": cruft, "committed": False, "sha": None}
    if commit and work:
        if cruft:
            _append_ignore(repo, sorted({f.rsplit("/", 1)[-1] for f in cruft}))
        _git(repo, "add", "-A")
        msg = (f"WIP rescue: {len(work)} uncommitted file(s) secured "
               f"({datetime.now():%Y-%m-%d})\n\nSecured by `sentinel rescue` — not pushed.")
        if _git(repo, "commit", "-q", "-m", msg).returncode == 0:
            out["committed"] = True
            out["sha"] = _git(repo, "rev-parse", "--short", "HEAD").stdout.strip()
    return out
