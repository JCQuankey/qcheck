# Changelog

All notable changes to qcheck (`qcheck-quantum` on PyPI). This project follows
semantic versioning.

## 0.3.0

qcheck 0.3.0 makes findings easier to understand and act on. This release adds a
structured rule catalog, a `qcheck rules` command for developers and agents,
richer SARIF metadata for CI, and five new static checks for common
AI-generated Qiskit and OpenQASM issues.

### Added
- **Rule catalog / explain layer**: every finding's rule id now carries stable
  metadata (title, category, severity, summary, why it matters, recommended
  action).
- **`qcheck rules`** and **`qcheck rules --json`**: browse the full catalog from
  the terminal or read it as machine-readable JSON for agents and CI.
- **Richer SARIF**: `driver.rules[]` is enriched from the catalog
  (shortDescription, fullDescription, help and default severity), so code
  scanning alerts show guidance inline.
- **Five new review rules** (23 rules total):
  - `QISKIT-GET-COUNTS-NO-MEASURE` - `get_counts()` on an unmeasured circuit.
  - `QISKIT-ASSEMBLE-REMOVED` - `assemble()` removed in Qiskit 1.0.
  - `QASM-DUP-REGISTER` - a register declared more than once.
  - `QASM-NO-MEASURE` - gates applied but the circuit is never measured.
  - `QASM-VERSION-MISMATCH` - OpenQASM 3 syntax inside an OpenQASM 2 program.

### Unchanged
- `pip install qcheck-quantum`; the command and import package remain `qcheck`.
- `qcheck verify` output, `--json` (single object and multi-file envelope),
  SARIF 2.1.0 and exit codes are backward compatible.
- Zero runtime dependencies; qcheck reviews code without executing it.

## 0.2.0

- Review multiple files, directories (recursive) and stdin in one command, with
  an aggregate JSON envelope and a worst-case exit code.
- SARIF 2.1.0 output (`--format sarif`) for GitHub Code Scanning.
- Composite GitHub Action for CI.

## 0.1.0

- First public release: static review for Qiskit and OpenQASM, JSON output,
  safety screen, and a static-check leaderboard. Zero runtime dependencies.
