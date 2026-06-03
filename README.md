# sentinel

**An ecosystem health monitor — one command, 🟢🟡🔴 across all your repos. Deterministic, dependency-free.**

If you keep more than a couple of repos on a machine, you lose track: which has uncommitted work, which never got pushed, which has rotted, which has a README that *claims* a `pip install` that doesn't exist. `sentinel` scans them all in seconds and tells you — and exits non-zero on anything red, so you can drop it in a cron or a pre-flight check.

## Use it

```sh
pip install "git+https://github.com/StellarRequiem/sentinel"
sentinel ~                              # scan every git repo under your home dir
sentinel ~/code --exclude vendored-theme
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

## Tests

```sh
pip install -e ".[dev]"
pytest
```

No dependencies — pure standard library.

## License

Apache-2.0. Built by [@StellarRequiem](https://github.com/StellarRequiem).
