# Changelog

All notable changes to qcheck (`qcheck-quantum` on PyPI). This project follows
semantic versioning.

## 0.9.0

qcheck 0.9.0 adds a new review surface: **Cirq**. The catalog grows to 50 rules
and now covers Qiskit, OpenQASM, PennyLane and Cirq - the four most common
surfaces for AI-generated quantum code.

### Added
- **Cirq static review** (four new rules, catalog now 50):
  - `CIRQ-MISSING-IMPORT` - `cirq.*` used without importing cirq.
  - `CIRQ-MEASURE-NO-QUBITS` - `cirq.measure()` with no qubits (raises
    ValueError in Cirq).
  - `CIRQ-EMPTY-LINEQUBITS` - a literal `LineQubit.range(n <= 0)`; warning,
    because the call is legal Cirq that yields an empty qubit list.
  - `CIRQ-SAME-QUBIT-2Q` - a two-qubit gate given the same qubit twice
    (Cirq raises "Duplicate qids").
- Public Cirq snippet cases in the regression suite.

### Improved
- **Framework detection weighs import evidence above bare mentions**: a Qiskit
  file whose docstring mentions Cirq stays on the Qiskit surface, and files
  importing both qiskit and cirq route to the larger Qiskit rule set.
- CLI description, `UNSUPPORTED` guidance and package metadata now name all
  four supported surfaces.

### Unchanged
- `pip install qcheck-quantum`; the command and import package remain `qcheck`.
- `qcheck verify` output, `--json` (single object and multi-file envelope),
  `qcheck rules --json`, SARIF 2.1.0 and exit codes are backward compatible.
- Zero runtime dependencies; qcheck reviews code without executing it.

## 0.8.0

qcheck 0.8.0 adds a new review surface: **PennyLane**. The catalog grows to 46
rules and now covers Qiskit, OpenQASM and PennyLane.

### Added
- **PennyLane static review** (four new rules, catalog now 46):
  - `PENNYLANE-QML-MISSING-IMPORT` - `qml.*` used without importing pennylane.
  - `PENNYLANE-DEVICE-ZERO-WIRES` - `qml.device(..., wires=0)`.
  - `PENNYLANE-DEVICE-NEGATIVE-WIRES` - a negative device wires count.
  - `PENNYLANE-QNODE-NO-RETURN` - a `@qml.qnode` function with no return.
- Public PennyLane snippet cases in the regression suite.

### Unchanged
- `pip install qcheck-quantum`; the command and import package remain `qcheck`.
- `qcheck verify` output, `--json` (single object and multi-file envelope),
  `qcheck rules --json`, SARIF 2.1.0 and exit codes are backward compatible.
- Zero runtime dependencies; qcheck reviews code without executing it.

## 0.7.0

qcheck 0.7.0 improves CI usability and review coverage. The GitHub Action now
accepts one path per line so paths with spaces work, and the catalog grows to
42 rules with wider coverage of common AI-generated mistakes.

### Added
- **GitHub Action: one-path-per-line input.** `paths` may now be a newline-
  delimited list, so a single path containing spaces is supported. The existing
  space-separated form is unchanged.
- **QISKIT-PARAMETER-MISSING-IMPORT** (catalog now 42): `Parameter` used without
  an import.

### Improved
- **Wider removed-module coverage**: `qiskit.tools` and `qiskit.test` imports are
  now flagged.
- **Bare-form OpenQASM measurement checks**: `measure q -> c` referencing an
  undeclared register is now caught (previously only indexed operands were
  checked).

### Unchanged
- `pip install qcheck-quantum`; the command and import package remain `qcheck`.
- `qcheck verify` output, `--json` (single object and multi-file envelope),
  `qcheck rules --json`, SARIF 2.1.0 and exit codes are backward compatible.
- Zero runtime dependencies; qcheck reviews code without executing it.

## 0.6.0

qcheck 0.6.0 expands review coverage to 41 rules and strengthens regression
testing. This release adds five static review rules for more common
AI-generated Qiskit and OpenQASM mistakes, extends the deprecated-gate check to
`u1`/`u2`/`u3`, and adds a public synthetic snippet suite.

### Added
- **Five new review rules** (catalog now 41):
  - `QISKIT-NEGATIVE-QUBITS` - a circuit built with a negative qubit count.
  - `QISKIT-ZERO-SIZED-REGISTER` - `QuantumRegister(0)`/`ClassicalRegister(0)`.
  - `QISKIT-BIND-PARAMETERS-DEPRECATED` - `bind_parameters()` (use `assign_parameters()`).
  - `QISKIT-SNAPSHOT-REMOVED` - `snapshot()` removed from Qiskit Aer.
  - `QASM-DUPLICATE-INCLUDE` - the same include listed more than once.
- **Wider deprecated-gate coverage**: `u1`/`u2`/`u3` are now flagged.
- **Public synthetic snippet suite** for regression coverage across the catalog.

### Unchanged
- `pip install qcheck-quantum`; the command and import package remain `qcheck`.
- `qcheck verify` output, `--json` (single object and multi-file envelope),
  `qcheck rules --json`, SARIF 2.1.0 and exit codes are backward compatible.
- Zero runtime dependencies; qcheck reviews code without executing it.

## 0.5.0

qcheck 0.5.0 expands review coverage to 36 rules and improves day-to-day CI and
CLI usability. This release adds six static review rules for common AI-generated
Qiskit and OpenQASM mistakes, hardens GitHub Action argument handling, improves
CLI help, and adds more false-positive guard tests.

### Added
- **Six new review rules** (catalog now 36):
  - `QISKIT-REMOVED-MODULE` - import of a subpackage removed from Qiskit.
  - `QISKIT-DEPRECATED-PROVIDER-PATH` - the `qiskit.providers.aer` import path.
  - `QISKIT-REGISTER-MISSING-IMPORT` - QuantumRegister/ClassicalRegister used unimported.
  - `QISKIT-TRANSPILE-MISSING-IMPORT` - `transpile()` used unimported.
  - `QASM-CLASSICAL-AS-QUBIT` - a classical register used where a qubit is expected.
  - `QASM-MEASURE-SIZE-MISMATCH` - a whole-register measurement with mismatched sizes.
- **More false-positive guard tests** so legitimate and teaching snippets stay quiet.

### Improved
- **GitHub Action**: arguments are assembled as an array; a SARIF `output` path
  with spaces now works. Existing inputs and behavior are unchanged.
- **CLI help**: `qcheck --help` now shows common commands and the exit-code meanings.

### Unchanged
- `pip install qcheck-quantum`; the command and import package remain `qcheck`.
- `qcheck verify` output, `--json` (single object and multi-file envelope),
  `qcheck rules --json`, SARIF 2.1.0 and exit codes are backward compatible.
- Zero runtime dependencies; qcheck reviews code without executing it.

## 0.4.0

qcheck 0.4.0 expands static review coverage with seven new circuit-integrity
checks for common AI-generated Qiskit and OpenQASM mistakes. The catalog now
includes 30 rules, each with structured guidance for developers, CI and agents.
This release also documents qcheck's public machine-readable output contracts.

### Added
- **Seven circuit-integrity rules** (catalog now 30):
  - `QISKIT-ZERO-QUBITS` - a zero-qubit circuit.
  - `QISKIT-QUBIT-INDEX-RANGE` - a qubit index past the circuit size.
  - `QISKIT-CLBIT-INDEX-RANGE` - a classical-bit index past the circuit size.
  - `QISKIT-MEASURE-NO-CLBITS` - `measure()` on a circuit with no classical bits.
  - `QISKIT-SAME-QUBIT-2Q` - a two-qubit gate using one qubit twice.
  - `QASM-ZERO-REGISTER` - a register declared with size 0.
  - `QASM-SAME-QUBIT-2Q` - a two-qubit gate using one qubit twice.
- **Output contract documentation** ([`docs/CONTRACTS.md`](docs/CONTRACTS.md)):
  the stable JSON, `qcheck rules --json`, SARIF and exit-code contracts that
  agents and CI can rely on, backed by contract tests.

### Unchanged
- `pip install qcheck-quantum`; the command and import package remain `qcheck`.
- `qcheck verify` output, `--json` (single object and multi-file envelope),
  SARIF 2.1.0 and exit codes are backward compatible.
- Zero runtime dependencies; qcheck reviews code without executing it.

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
