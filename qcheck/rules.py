"""qcheck rule catalog: stable metadata for every rule qcheck can report.

Single source of truth for rule descriptions. The verifier emits findings with a
rule `id`; this catalog explains each id (what it means, why it matters, what to
do next) so developers, CI and agents can act on a finding without guessing.
Stdlib only; no runtime dependencies. Positive, practical guidance - where a fix
is a suggestion rather than something qcheck applies, it is phrased as guidance.
"""
from __future__ import annotations

from dataclasses import dataclass, asdict
from typing import Dict, List

VALID_LEVELS = ("error", "warning", "info")

# Categories group rules by the kind of signal they raise.
CATEGORIES = ("api-compatibility", "structure", "syntax", "safety", "input")

# Which surface a rule applies to.
SURFACES = ("qiskit", "openqasm", "python", "cli", "pennylane")


@dataclass(frozen=True)
class Rule:
    id: str
    title: str
    category: str
    default_level: str          # one of VALID_LEVELS
    applies_to: str             # one of SURFACES
    summary: str                # one line: what the rule detects
    why_it_matters: str         # why a developer/agent should care
    recommended_action: str     # practical next step (guidance, not auto-fix)

    def to_dict(self) -> dict:
        return asdict(self)


def _r(*a) -> Rule:
    return Rule(*a)


# NOTE: keep this in sync with the rule ids the checks emit. tests/test_rules.py
# fails if a reported id is missing here (drift guard).
_RULES: List[Rule] = [
    # --- Qiskit API compatibility ---
    _r("QISKIT-EXECUTE", "execute() removed in Qiskit 1.0", "api-compatibility",
       "error", "qiskit",
       "Flags use of the top-level execute() call.",
       "execute() was removed in Qiskit 1.0, so the snippet will not run on a modern Qiskit install.",
       "Use a primitive (Sampler/Estimator) or backend.run() instead of execute()."),
    _r("QISKIT-REMOVED-IMPORT", "Import removed in Qiskit 1.0", "api-compatibility",
       "error", "qiskit",
       "Flags imports removed in Qiskit 1.0, such as execute and Aer.",
       "These imports raise ImportError on Qiskit 1.0+, a very common LLM mistake.",
       "Import Aer from qiskit_aer and replace execute with a primitive or backend.run()."),
    _r("QISKIT-DEPRECATED-GATE", "Deprecated gate alias", "api-compatibility",
       "warning", "qiskit",
       "Flags deprecated QuantumCircuit gate aliases (for example cnot).",
       "Deprecated aliases still work today but are slated for removal and add noise for reviewers.",
       "Use the current gate name (for example .cx() instead of .cnot())."),
    _r("QISKIT-REMOVED-MODULE", "Removed Qiskit subpackage", "api-compatibility",
       "error", "qiskit",
       "Imports a subpackage removed from Qiskit (qiskit.aqua, qiskit.ignis).",
       "These subpackages no longer ship with Qiskit, so the import fails on a modern install.",
       "Use the current replacement package (for example qiskit-algorithms) or remove the import."),
    _r("QISKIT-DEPRECATED-PROVIDER-PATH", "Moved provider import path", "api-compatibility",
       "warning", "qiskit",
       "Imports from qiskit.providers.aer, which moved to its own package.",
       "The old path is deprecated and may stop resolving on newer installs.",
       "Import from qiskit_aer instead (for example 'from qiskit_aer import AerSimulator')."),
    _r("QISKIT-REGISTER-MISSING-IMPORT", "Register used without import", "structure",
       "error", "qiskit",
       "QuantumRegister or ClassicalRegister is used but never imported.",
       "The snippet raises NameError at runtime.",
       "Add 'from qiskit import QuantumRegister, ClassicalRegister'."),
    _r("QISKIT-TRANSPILE-MISSING-IMPORT", "transpile() used without import", "structure",
       "error", "qiskit",
       "transpile() is called but never imported.",
       "The snippet raises NameError at runtime.",
       "Add 'from qiskit import transpile'."),
    _r("QISKIT-PARAMETER-MISSING-IMPORT", "Parameter used without import", "structure",
       "error", "qiskit",
       "Parameter is used but never imported.",
       "The snippet raises NameError at runtime.",
       "Add 'from qiskit.circuit import Parameter'."),
    # --- Qiskit structure ---
    _r("QISKIT-MISSING-IMPORT", "QuantumCircuit used without import", "structure",
       "error", "qiskit",
       "QuantumCircuit is referenced but never imported.",
       "The snippet raises NameError at runtime.",
       "Add `from qiskit import QuantumCircuit`."),
    _r("QISKIT-NO-CIRCUIT", "No QuantumCircuit construction", "structure",
       "warning", "qiskit",
       "No QuantumCircuit(...) construction was detected.",
       "A quantum snippet with no circuit usually means the code is incomplete.",
       "Confirm the snippet builds a circuit, or that a circuit-free helper was intended."),
    _r("QISKIT-NO-MEASURE", "Circuit has no measurement", "structure",
       "warning", "qiskit",
       "A circuit is built but never measured.",
       "Without a measurement the circuit returns no classical result on most backends.",
       "Add a measurement (for example qc.measure_all()) if a result is expected."),
    _r("QISKIT-GET-COUNTS-NO-MEASURE", "get_counts() without a measurement", "structure",
       "warning", "qiskit",
       "get_counts() is read but the circuit is never measured.",
       "Reading counts from an unmeasured circuit yields empty or meaningless results, a frequent AI mistake.",
       "Measure the circuit (for example qc.measure_all()) before calling get_counts()."),
    _r("QISKIT-ASSEMBLE-REMOVED", "assemble() removed in Qiskit 1.0", "api-compatibility",
       "error", "qiskit",
       "Flags use of the top-level assemble() call.",
       "assemble() was removed in Qiskit 1.0, so the snippet will not run on a modern Qiskit install.",
       "Pass circuits directly to a primitive (Sampler/Estimator) or backend.run(); assemble() is no longer needed."),
    _r("QISKIT-ZERO-QUBITS", "Zero-qubit circuit", "structure",
       "error", "qiskit",
       "QuantumCircuit(0) is constructed with no qubits.",
       "A zero-qubit circuit cannot hold any gates and is almost always a generation slip.",
       "Construct the circuit with the number of qubits it needs, e.g. QuantumCircuit(2)."),
    _r("QISKIT-NEGATIVE-QUBITS", "Negative qubit count", "structure",
       "error", "qiskit",
       "QuantumCircuit is constructed with a negative qubit count.",
       "A negative size is invalid and raises an error at construction.",
       "Use a positive qubit count, e.g. QuantumCircuit(2)."),
    _r("QISKIT-ZERO-SIZED-REGISTER", "Zero-sized register", "structure",
       "error", "qiskit",
       "QuantumRegister(0) or ClassicalRegister(0) has no bits.",
       "A zero-sized register holds nothing and cannot be indexed.",
       "Size the register for the bits it needs, e.g. QuantumRegister(2)."),
    _r("QISKIT-BIND-PARAMETERS-DEPRECATED", "bind_parameters() deprecated", "api-compatibility",
       "warning", "qiskit",
       "Uses the deprecated QuantumCircuit.bind_parameters() method.",
       "bind_parameters() is deprecated in favour of assign_parameters() and is slated for removal.",
       "Use .assign_parameters() instead."),
    _r("QISKIT-SNAPSHOT-REMOVED", "snapshot() removed", "api-compatibility",
       "warning", "qiskit",
       "Uses snapshot(), which was removed from Qiskit Aer.",
       "The snapshot instruction was removed, so this call fails on a modern Aer.",
       "Use a save instruction such as save_statevector() instead."),
    _r("QISKIT-QUBIT-INDEX-RANGE", "Qubit index out of range", "structure",
       "error", "qiskit",
       "A gate targets a qubit index outside the circuit's declared size.",
       "Indexing past the circuit size raises CircuitError at runtime.",
       "Use a qubit index within 0..n-1, or size the circuit for the index used."),
    _r("QISKIT-CLBIT-INDEX-RANGE", "Classical bit index out of range", "structure",
       "error", "qiskit",
       "measure() writes to a classical bit index outside the circuit's declared size.",
       "Indexing past the classical register raises CircuitError at runtime.",
       "Use a classical bit index within 0..m-1, or add classical bits to the circuit."),
    _r("QISKIT-MEASURE-NO-CLBITS", "measure() with no classical bits", "structure",
       "error", "qiskit",
       "measure() is called on a circuit constructed with no classical bits.",
       "There is nowhere to store the outcome, so the call fails; a frequent AI mistake.",
       "Construct the circuit as QuantumCircuit(n, m) with m >= 1, or use qc.measure_all()."),
    _r("QISKIT-SAME-QUBIT-2Q", "Two-qubit gate on one qubit", "structure",
       "warning", "qiskit",
       "A two-qubit gate uses the same qubit as both operands.",
       "A two-qubit gate needs two distinct qubits; repeating one is almost always a typo.",
       "Use two different qubit indices for the control and target."),
    # --- PennyLane ---
    _r("PENNYLANE-QML-MISSING-IMPORT", "PennyLane used without import", "structure",
       "error", "pennylane",
       "qml.* PennyLane calls are used but pennylane is never imported.",
       "The snippet raises NameError at runtime.",
       "Add 'import pennylane as qml'."),
    _r("PENNYLANE-DEVICE-ZERO-WIRES", "Device with zero wires", "structure",
       "error", "pennylane",
       "qml.device(...) is created with wires=0.",
       "A device with no wires cannot hold a circuit.",
       "Set wires to the number of qubits the circuit needs, e.g. wires=2."),
    _r("PENNYLANE-DEVICE-NEGATIVE-WIRES", "Device with negative wires", "structure",
       "error", "pennylane",
       "qml.device(...) is created with a negative wires count.",
       "A negative wire count is invalid and fails at device construction.",
       "Use a positive wires count."),
    _r("PENNYLANE-QNODE-NO-RETURN", "QNode has no return", "structure",
       "warning", "pennylane",
       "A function decorated with @qml.qnode(...) has no return statement.",
       "A QNode must return a measurement, so a return-less QNode yields nothing useful.",
       "Return a measurement, for example 'return qml.expval(qml.PauliZ(0))'."),

    # --- OpenQASM structure ---
    _r("QASM-NO-HEADER", "OpenQASM header missing", "structure",
       "error", "openqasm",
       "The OPENQASM version header is missing.",
       "Parsers reject a program without the version header.",
       "Add an `OPENQASM 2.0;` (or 3.0) header at the top."),
    _r("QASM-UNDECLARED-REG", "Undeclared register", "structure",
       "error", "openqasm",
       "A quantum or classical register is used before it is declared.",
       "Referencing an undeclared register is a parse-time error.",
       "Declare the register (qreg/creg or qubit/bit) before using it."),
    _r("QASM-INDEX-RANGE", "Register index out of range", "structure",
       "error", "openqasm",
       "A qubit or bit index falls outside the declared register size.",
       "Out-of-range indexing fails at parse or run time.",
       "Use an index within the declared register length."),
    _r("QASM-MEASURE-SRC", "Invalid measurement source", "structure",
       "error", "openqasm",
       "The source operand of a measure statement is invalid.",
       "A malformed measure will not parse.",
       "Measure a declared qubit register or element."),
    _r("QASM-MEASURE-TGT", "Invalid measurement target", "structure",
       "error", "openqasm",
       "The target operand of a measure statement is invalid.",
       "A malformed measure target will not parse.",
       "Write results into a declared classical register or element."),
    _r("QASM-INCLUDE", "Unsupported or missing include", "structure",
       "warning", "openqasm",
       "An include statement is missing or not recognised.",
       "Gates from a missing include may be undefined.",
       "Include the standard library, for example `include \"qelib1.inc\";`."),
    _r("QASM-DUPLICATE-INCLUDE", "Duplicate include", "structure",
       "warning", "openqasm",
       "The same include file is listed more than once.",
       "A repeated include is redundant and usually a copy-paste slip.",
       "Include each file once."),
    _r("QASM-DUP-REGISTER", "Duplicate register declaration", "structure",
       "error", "openqasm",
       "The same register name is declared more than once.",
       "Redeclaring a register is a parse-time error and usually signals copy-paste or generation noise.",
       "Declare each register once with a unique name."),
    _r("QASM-NO-MEASURE", "No measurement in circuit", "structure",
       "warning", "openqasm",
       "Gates are applied but the program never measures.",
       "A circuit with no measurement returns no classical result when run, a common gap in generated snippets.",
       "Add a measurement (for example `measure q -> c;`) if a result is expected."),
    _r("QASM-VERSION-MISMATCH", "OpenQASM 2/3 syntax mismatch", "syntax",
       "warning", "openqasm",
       "OpenQASM 3 declaration syntax appears in an OpenQASM 2 program.",
       "Mixing OpenQASM 2 and 3 syntax is a frequent AI slip and will not parse under either version.",
       "Use one dialect: `qreg name[n];` for OpenQASM 2, or set the header to `OPENQASM 3.0;`."),
    _r("QASM-ZERO-REGISTER", "Zero-sized register", "structure",
       "error", "openqasm",
       "A quantum or classical register is declared with size 0.",
       "A zero-sized register holds nothing and cannot be indexed.",
       "Declare the register with the size it needs, e.g. `qreg q[2];`."),
    _r("QASM-SAME-QUBIT-2Q", "Two-qubit gate on one qubit", "structure",
       "warning", "openqasm",
       "A gate uses the same register element more than once as an operand.",
       "A two-qubit gate such as cx needs two distinct qubits; repeating one is almost always a typo.",
       "Use two different qubits, e.g. `cx q[0], q[1];`."),
    _r("QASM-CLASSICAL-AS-QUBIT", "Classical register used as a qubit", "structure",
       "error", "openqasm",
       "A gate operand references a classical register where a qubit is expected.",
       "Applying a gate to a classical register is invalid and will not parse or run.",
       "Apply gates to a quantum register (qreg), not a classical one (creg)."),
    _r("QASM-MEASURE-SIZE-MISMATCH", "Measurement register size mismatch", "structure",
       "warning", "openqasm",
       "A whole-register measurement uses quantum and classical registers of different sizes.",
       "Broadcasting a measurement across mismatched register sizes drops or misaligns results.",
       "Match the register sizes, or measure specific indices, e.g. `measure q[0] -> c[0];`."),
    _r("QASM-NO-SEMICOLON", "Missing semicolon", "syntax",
       "warning", "openqasm",
       "A statement appears to be missing its terminating semicolon.",
       "Missing terminators are a frequent, easily fixed parse failure.",
       "End the statement with a semicolon."),
    _r("QASM-SUSPICIOUS", "Not valid OpenQASM", "syntax",
       "error", "openqasm",
       "The content does not look like valid OpenQASM.",
       "The input likely is not OpenQASM, so downstream tooling would fail.",
       "Confirm the file is OpenQASM and well formed."),
    # --- Python syntax + safety ---
    _r("PY-SYNTAX", "Python syntax error", "syntax",
       "error", "python",
       "The Python snippet does not parse.",
       "Invalid Python cannot run.",
       "Fix the reported syntax error before running the snippet."),
    _r("PY-UNSAFE-IMPORT", "Unsafe import", "safety",
       "error", "python",
       "The snippet imports a sensitive module such as os or subprocess.",
       "qcheck reviews without executing; flagging these keeps untrusted model output from becoming a code-execution path in an agent loop or CI.",
       "Remove the import if the quantum snippet does not need it, or run it only in a sandbox you control."),
    _r("PY-UNSAFE-CALL", "Unsafe call", "safety",
       "error", "python",
       "The snippet makes a sensitive call such as os.system, eval, or exec.",
       "These calls can execute arbitrary commands; qcheck flags them so untrusted output is reviewed first.",
       "Remove the call if it is not needed, or isolate execution in a controlled sandbox."),
    # --- CLI / input ---
    _r("UNSUPPORTED", "Unsupported input", "input",
       "error", "cli",
       "The file is not OpenQASM or Qiskit Python.",
       "qcheck v0 reviews OpenQASM 2/3 and Qiskit Python; other inputs are reported so nothing fails silently.",
       "Point qcheck at a .qasm or Qiskit .py file."),
]

RULES: Dict[str, Rule] = {r.id: r for r in _RULES}


def catalog() -> List[Rule]:
    """All rules, sorted by id (deterministic)."""
    return [RULES[k] for k in sorted(RULES)]


def get(rule_id: str) -> Rule:
    return RULES[rule_id]


def known(rule_id: str) -> bool:
    return rule_id in RULES
