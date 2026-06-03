"""sentinel config — per-repo overrides so the report is signal, not noise.

A TOML file (default ``~/.sentinel.toml``) declares intended states::

    exclude = ["powerlevel10k", "oasis"]      # third-party clones — never scan

    [repos.operator]
    intentional_local = true                  # no remote is fine
    no_tests_ok = true                        # CLIs, no test suite expected

    [repos.Forest-Soul-Forge]
    generated = ["examples/audit_chain.jsonl"]  # a tracked fixture that drifts — ignore it
"""
from __future__ import annotations

from pathlib import Path

try:
    import tomllib
except ModuleNotFoundError:  # pragma: no cover
    tomllib = None


def load_config(path="~/.sentinel.toml") -> dict:
    p = Path(path).expanduser()
    if tomllib is None or not p.exists():
        return {"exclude": [], "repos": {}}
    try:
        data = tomllib.loads(p.read_text(encoding="utf-8"))
    except Exception:
        return {"exclude": [], "repos": {}}
    return {"exclude": data.get("exclude", []), "repos": data.get("repos", {})}
