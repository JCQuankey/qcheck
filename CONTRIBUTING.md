# Contributing to qcheck

Thanks for helping make qcheck sharper. The most valuable contribution is a new
**failure fixture**: a real LLM-generated quantum snippet that *should* fail but
currently passes (or vice versa). Every fixture improves the checks and feeds the
public error taxonomy.

## Setup

```bash
git clone https://github.com/JCQuankey/qcheck && cd qcheck
python3 -m pip install -e ".[dev]"
python3 -m pytest -q          # expect all tests passing
```

## Running the tool

```bash
qcheck verify examples/bell.qasm
qcheck verify examples/broken_qiskit_execute.py --json
```

## Adding a fixture

1. Add the snippet under `fixtures/` (valid → `valid_*`, invalid → `invalid_*`
   or `qiskit_*`).
2. Add a test in `tests/` asserting the expected status and check IDs.
3. Run `python3 -m pytest -q`.

## Adding a rule

- QASM rules live in `qcheck/checks_qasm.py`, Qiskit rules in
  `qcheck/checks_qiskit.py`.
- Give each rule a stable ID (e.g. `QISKIT-REMOVED-IMPORT`) and a clear,
  actionable message with a suggested fix.
- Cover the rule with at least one passing and one failing fixture.

## Hard rules (non-negotiable)

- **Never execute or import the analyzed snippet.** Static analysis only. Do not
  add `exec`, `eval`, or dynamic import of user input. See [`SECURITY.md`](SECURITY.md).
- **Do not add remote telemetry**, and do not enable any telemetry by default.
- **Keep the JSON output schema stable** — agents and CI depend on it. Add fields
  additively; do not rename or remove existing ones without a version note.
- **Keep v0 dependency-light.** Avoid new runtime dependencies unless clearly justified.

## Pull requests

Keep PRs focused. Include tests. Describe what the change detects and why. By
contributing you agree your work is licensed under Apache-2.0.

## Questions

General or technical questions: **dev@quankey.xyz**. For security issues, use
**security@quankey.xyz** (see [`SECURITY.md`](SECURITY.md)), not a public issue.
