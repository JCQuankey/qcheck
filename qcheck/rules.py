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
SURFACES = ("qiskit", "openqasm", "python", "cli")


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
