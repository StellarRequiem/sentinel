"""sentinel — ecosystem health monitor. One command, 🟢🟡🔴 across your repos."""
from __future__ import annotations

import argparse
import json
from pathlib import Path

from . import checks

_ICON = {"green": "🟢", "yellow": "🟡", "red": "🔴"}
_ORDER = {"red": 0, "yellow": 1, "green": 2}


def discover(root) -> list[Path]:
    root = Path(root).expanduser()
    if not root.is_dir():
        return []
    return sorted(p for p in root.iterdir() if p.is_dir() and (p / ".git").exists())


def check_repo(path, net=True) -> dict:
    rep = {"name": Path(path).name, "path": str(path),
           "git": checks.git_status(path), "age": checks.commit_age_days(path),
           "structure": checks.structure(path), "pypi_false": False}
    pkg = rep["structure"].get("name")
    if net and pkg and checks.readme_claims_pypi(path, pkg):
        rep["pypi_false"] = checks.pypi_published(pkg) is False
    rep["level"], rep["reasons"] = checks.classify(rep)
    return rep


def render(reports) -> str:
    counts = {"green": 0, "yellow": 0, "red": 0}
    lines = []
    for r in sorted(reports, key=lambda r: (_ORDER[r["level"]], r["name"])):
        counts[r["level"]] += 1
        age = r.get("age")
        agestr = f"{int(age)}d" if age is not None else "?"
        branch = r["git"].get("branch", "")
        extra = f" · {branch}" if branch and branch not in ("main", "master") else ""
        lines.append(f"{_ICON[r['level']]} {r['name']:<22} {', '.join(r['reasons'])}"
                     f"   ·  {agestr}{extra}")
    summary = (f"{counts['green']} 🟢   {counts['yellow']} 🟡   {counts['red']} 🔴"
               f"   ·   {len(reports)} repos")
    return "\n".join(lines) + "\n\n" + summary


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(prog="sentinel", description="ecosystem health monitor")
    ap.add_argument("root", nargs="?", default="~", help="directory to scan (default: ~)")
    ap.add_argument("--no-net", action="store_true", help="skip PyPI / network checks")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of a report")
    ap.add_argument("--exclude", default="", help="comma-separated repo names to skip")
    a = ap.parse_args(argv)
    skip = {x.strip() for x in a.exclude.split(",") if x.strip()}
    reports = [check_repo(p, net=not a.no_net) for p in discover(a.root) if p.name not in skip]
    if a.json:
        print(json.dumps(reports, indent=2, default=str))
    else:
        print(f"SENTINEL · {len(reports)} repos under {a.root}\n")
        print(render(reports) if reports else "  no git repos found")
    return 1 if any(r["level"] == "red" for r in reports) else 0
