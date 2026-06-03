# sentinel

**An ecosystem health monitor *and containment toolkit* — detect problems across all your repos, then fix them, reversibly. Deterministic, dependency-free.**

If you keep more than a couple of repos on a machine, you lose track: which has uncommitted work, which never got pushed, which has rotted, which has a README that *claims* a `pip install` that doesn't exist. `sentinel` scans them all in seconds and tells you — and exits non-zero on anything red, so you can drop it in a cron or a pre-flight check.

## Use it

```sh
pip install "git+https://github.com/StellarRequiem/sentinel"

# DETECT — health across every repo under a root
sentinel ~                              # alias for `sentinel scan ~`
sentinel scan ~/code --exclude vendored-theme

# CONTAIN — act on what it finds (reversible; dry-run by default)
sentinel rescue ~/some-repo             # classify uncommitted work vs cruft (dry-run)
sentinel rescue ~/some-repo --commit    # dated WIP-commit the real work — never pushes
sentinel groom  ~/some-repo --apply     # add the standard .gitignore patterns
```

## What a run looks like

```
SENTINEL · 9 repos under /home/you      (example output)

🔴 payment-service     2 unpushed, 12 uncommitted        ·  3d
🔴 legacy-cron         1 uncommitted, 90d stale, no tests ·  90d
🟡 api-gateway         3 uncommitted                      ·  1d
🟡 scratch             local-only, no tests               ·  0d
🟢 widgets-lib         clean                              ·  0d
🟢 auth-core           clean                              ·  0d

4 🟢   2 🟡   2 🔴   ·   9 repos
```

On a real machine it routinely catches the things you forgot: unpushed work at risk, a repo that rotted for months, a README that lies about being on PyPI.

## What it checks — all deterministic (no flaky test-running)

- **Git hygiene** — uncommitted changes, **unpushed commits** (work at risk), commits behind the remote, local-only repos.
- **Staleness** — days since the last commit.
- **Structure** — README / tests / `pyproject` present.
- **Honesty** — a README that says `pip install <name>` for a package that **isn't actually on PyPI** (the lie that ships broken installs).

## Severity

- 🔴 unpushed commits · uncommitted + stale · a false PyPI claim
- 🟡 recent uncommitted changes · local-only · stale · no tests
- 🟢 clean, pushed, claims accurate

Exit code is `1` if anything is red — CI- and cron-friendly.

## Containment — detect, then *fix*

`sentinel` doesn't just report; it contains, reversibly:

- **`rescue <repo>`** — splits a repo's uncommitted files into **work vs. cruft**, gitignores the cruft, and dated-WIP-commits the real work. *Never pushes, never discards.* Dry-run unless `--commit`.
- **`groom <repo>`** — adds the standard `.gitignore` patterns the repo is missing (`.DS_Store`, `__pycache__`, `*.command`, logs, `venv/`, …). Dry-run unless `--apply`.

The discipline, inherited from the operator who built it: **cruft is never committed, work is never discarded, and nothing is ever pushed without you.**

## Tests

```sh
pip install -e ".[dev]"
pytest
```

No dependencies — pure standard library.

## License

Apache-2.0. Built by [@StellarRequiem](https://github.com/StellarRequiem).
