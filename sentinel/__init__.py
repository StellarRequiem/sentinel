"""sentinel — a deterministic, dependency-free ecosystem health monitor.

Scans the git repos under a root and reports 🟢🟡🔴 health: uncommitted /
unpushed / behind, staleness, missing tests, and READMEs that claim a PyPI
install that doesn't exist. Exit 1 on any red — drop it in a cron or CI.
"""
from .checks import classify, git_status, structure

__version__ = "0.1.0"
__all__ = ["classify", "git_status", "structure"]
