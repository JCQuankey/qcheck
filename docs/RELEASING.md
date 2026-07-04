# Releasing qcheck

qcheck is published to PyPI as the distribution **`qcheck-quantum`** (the CLI
command and import package are both `qcheck`). Publishing uses **PyPI OIDC
Trusted Publishing** - there are **no API tokens** stored in GitHub.

## Release model

| Target | Trigger | Workflow job |
|---|---|---|
| **TestPyPI** | manual `workflow_dispatch` on `release.yml` | `publish-testpypi` |
| **live PyPI** | a **published GitHub Release** | `publish-pypi` |

`build.yml` (runs on PRs) builds and `twine check`s the distribution but can
never publish. Normal pushes never publish anything.

## One-time setup (maintainer)

The TestPyPI and PyPI trusted publishers for `qcheck-quantum` are already
configured and `0.2.0` shipped on 2026-07-04. The steps below are kept for
reference / re-setup. They must be done in a browser and cannot be automated.
Do TestPyPI first.

1. **Create the GitHub Environments** (repo -> Settings -> Environments):
   `testpypi` and `pypi`. Optionally require a reviewer on `pypi`.
2. **TestPyPI trusted publisher** (https://test.pypi.org -> account -> Publishing):
   add a *pending* publisher:
   - PyPI Project Name: `qcheck-quantum`
   - Owner: `JCQuankey`
   - Repository: `qcheck`
   - Workflow name: `release.yml`
   - Environment: `testpypi`
3. **PyPI trusted publisher** (https://pypi.org -> account -> Publishing): same,
   with Environment `pypi`.
4. Confirm the distribution name `qcheck-quantum` on PyPI (already reserved by
   the `0.2.0` release).

## Cutting a release

1. Bump `version` in `pyproject.toml` and `qcheck/__init__.py` (keep them equal).
2. Open a PR, get CI green (`build.yml` builds + checks the artifact).
3. **Dry run to TestPyPI:** Actions -> *Release (PyPI Trusted Publishing)* ->
   Run workflow. Then `pip install -i https://test.pypi.org/simple/ qcheck-quantum`
   in a clean venv and smoke-test `qcheck --version` / `qcheck verify`.
4. **Live:** publish a GitHub Release for the new version tag. The
   `publish-pypi` job runs automatically via OIDC.

## Notes

- Keep runtime dependencies at zero unless there is a strong, documented reason.
- The artifacts contain only the `qcheck` package + `LICENSE`/`NOTICE`. No tests,
  examples, docs, or private files are shipped.
