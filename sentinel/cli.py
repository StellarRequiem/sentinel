"""sentinel — ecosystem health + containment. Detect, then contain."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from . import checks, contain

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


def _scan(a) -> int:
    skip = {x.strip() for x in a.exclude.split(",") if x.strip()}
    reports = [check_repo(p, net=not a.no_net) for p in discover(a.root) if p.name not in skip]
    if a.json:
        print(json.dumps(reports, indent=2, default=str))
    else:
        print(f"SENTINEL · {len(reports)} repos under {a.root}\n")
        print(render(reports) if reports else "  no git repos found")
    return 1 if any(r["level"] == "red" for r in reports) else 0


def _rescue(a) -> int:
    plan = contain.rescue(Path(a.repo).expanduser(), commit=a.commit)
    print(f"rescue {a.repo}")
    print(f"  work to save  ({len(plan['work'])}): " + (", ".join(plan["work"]) or "—"))
    print(f"  cruft to ignore ({len(plan['cruft'])}): " + (", ".join(plan["cruft"]) or "—"))
    if a.commit:
        print(f"  → committed {plan['sha']} (NOT pushed)" if plan["committed"]
              else "  → nothing to commit")
    else:
        print("  (dry-run — add --commit to secure it; it never pushes or discards)")
    return 0


def _groom(a) -> int:
    res = contain.groom(Path(a.repo).expanduser(), apply=a.apply)
    if not res["missing"]:
        print(f"groom {a.repo}: .gitignore already covers the standard patterns ✓")
    elif a.apply:
        print(f"groom {a.repo}: added {len(res['missing'])} pattern(s) → " + ", ".join(res["missing"]))
    else:
        print(f"groom {a.repo}: missing {len(res['missing'])} pattern(s): " + ", ".join(res["missing"]))
        print("  (dry-run — add --apply to write them)")
    return 0


def main(argv=None) -> int:
    argv = list(sys.argv[1:] if argv is None else argv)
    known = {"scan", "rescue", "groom", "-h", "--help"}
    if not argv or argv[0] not in known:
        argv = ["scan", *argv]                       # default subcommand: scan
    ap = argparse.ArgumentParser(
        prog="sentinel", description="ecosystem health + containment — detect, then contain")
    sub = ap.add_subparsers(dest="cmd", required=True)

    sp = sub.add_parser("scan", help="🟢🟡🔴 health across all repos under a root")
    sp.add_argument("root", nargs="?", default="~", help="directory to scan (default: ~)")
    sp.add_argument("--no-net", action="store_true", help="skip PyPI / network checks")
    sp.add_argument("--json", action="store_true")
    sp.add_argument("--exclude", default="", help="comma-separated repo names to skip")

    rp = sub.add_parser("rescue", help="dated WIP-commit a repo's uncommitted work (dry-run unless --commit)")
    rp.add_argument("repo")
    rp.add_argument("--commit", action="store_true", help="actually commit — never pushes")

    gp = sub.add_parser("groom", help="add standard .gitignore patterns (dry-run unless --apply)")
    gp.add_argument("repo")
    gp.add_argument("--apply", action="store_true")

    a = ap.parse_args(argv)
    return {"scan": _scan, "rescue": _rescue, "groom": _groom}[a.cmd](a)
