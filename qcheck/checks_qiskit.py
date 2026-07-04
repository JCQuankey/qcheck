"""Static checks for Qiskit Python snippets via the stdlib `ast` module.

No execution. Detects: syntax errors, missing QuantumCircuit import, missing
measurement, and Qiskit 1.0 breaking changes that LLMs still emit constantly
(execute(), `from qiskit import Aer/execute`, deprecated gate aliases).
"""
from __future__ import annotations

import ast
from typing import List, Tuple

from .report import Finding
from .safety import scan_python_safety

_REMOVED_FROM_QISKIT = {"execute", "Aer", "IBMQ", "BasicAer", "assemble"}
# Gates whose positional arguments are all qubit indices (no angle parameters),
# so every integer literal argument is a qubit index we can range-check.
_1Q_POS_GATES = {"h", "x", "y", "z", "s", "t", "sdg", "tdg", "sx", "sxdg", "id"}
_2Q_POS_GATES = {"cx", "cz", "cy", "ch", "swap", "dcx", "iswap", "ecr"}
_DEPRECATED_METHODS = {
    "cnot": "cx", "toffoli": "ccx", "fredkin": "cswap", "iden": "id",
    "mct": "mcx",
}


def check_qiskit(text: str) -> Tuple[bool, bool, List[Finding], List[str]]:
    """Return (syntax_valid, unsafe, findings, suggested_fixes)."""
    findings: List[Finding] = []
    fixes: List[str] = []

    try:
        tree = ast.parse(text)
    except SyntaxError as e:
        findings.append(Finding(
            "PY-SYNTAX", "error", f"Python syntax error: {e.msg}", e.lineno))
        return False, False, findings, fixes

    safety = scan_python_safety(tree)
    if safety:
        findings.extend(safety)
        return True, True, findings, [
            "Remove filesystem/network/process/dynamic-exec code; quantum "
            "circuit snippets should not need it."]

    imported_names: set[str] = set()
    module_imports: set[str] = set()
    uses_quantumcircuit = False
    has_measure = False
    get_counts_line = None

    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom):
            mod = (node.module or "")
            for alias in node.names:
                imported_names.add(alias.asname or alias.name)
                if mod == "qiskit" and alias.name in _REMOVED_FROM_QISKIT:
                    findings.append(Finding(
                        "QISKIT-REMOVED-IMPORT", "error",
                        f"'from qiskit import {alias.name}' was removed in "
                        f"Qiskit 1.0; this code will not run on modern Qiskit.",
                        getattr(node, "lineno", None)))
                    if alias.name == "execute":
                        fixes.append("Replace execute() with a primitive "
                                     "(Sampler/Estimator) or backend.run().")
                    if alias.name == "Aer":
                        fixes.append("Import Aer from qiskit_aer: "
                                     "'from qiskit_aer import Aer'.")
        elif isinstance(node, ast.Import):
            for alias in node.names:
                module_imports.add(alias.name.split(".")[0])
        elif isinstance(node, ast.Call):
            func = node.func
            if isinstance(func, ast.Name):
                if func.id == "QuantumCircuit":
                    uses_quantumcircuit = True
                elif func.id == "execute":
                    findings.append(Finding(
                        "QISKIT-EXECUTE", "error",
                        "execute() was removed in Qiskit 1.0; use Sampler/"
                        "Estimator primitives or backend.run().",
                        getattr(node, "lineno", None)))
                elif func.id == "assemble":
                    findings.append(Finding(
                        "QISKIT-ASSEMBLE-REMOVED", "error",
                        "assemble() was removed in Qiskit 1.0; primitives "
                        "(Sampler/Estimator) or backend.run() take circuits "
                        "directly.", getattr(node, "lineno", None)))
                    fixes.append("Remove assemble(); pass circuits straight to "
                                 "a primitive or backend.run().")
            elif isinstance(func, ast.Attribute):
                if func.attr in ("measure", "measure_all", "measure_active"):
                    has_measure = True
                elif func.attr == "get_counts":
                    get_counts_line = getattr(node, "lineno", None)
                elif func.attr in _DEPRECATED_METHODS:
                    repl = _DEPRECATED_METHODS[func.attr]
                    findings.append(Finding(
                        "QISKIT-DEPRECATED-GATE", "warning",
                        f"QuantumCircuit.{func.attr}() is deprecated; use "
                        f".{repl}().", getattr(node, "lineno", None)))
                    fixes.append(f"Replace .{func.attr}() with .{repl}().")

    if uses_quantumcircuit and "QuantumCircuit" not in imported_names:
        findings.append(Finding(
            "QISKIT-MISSING-IMPORT", "error",
            "QuantumCircuit is used but never imported "
            "('from qiskit import QuantumCircuit').", 1))
        fixes.append("Add 'from qiskit import QuantumCircuit'.")

    if uses_quantumcircuit and not has_measure:
        findings.append(Finding(
            "QISKIT-NO-MEASURE", "warning",
            "Circuit has no measurement; sampling it returns nothing useful.",
            None))
        fixes.append("Add qc.measure_all() (or explicit measure) before running.")

    if get_counts_line is not None and not has_measure:
        findings.append(Finding(
            "QISKIT-GET-COUNTS-NO-MEASURE", "warning",
            "get_counts() is called but the circuit is never measured; counts "
            "will be empty or meaningless.", get_counts_line))
        fixes.append("Measure the circuit (qc.measure_all()) before reading "
                     "get_counts().")

    if not uses_quantumcircuit:
        findings.append(Finding(
            "QISKIT-NO-CIRCUIT", "warning",
            "No QuantumCircuit(...) construction detected.", None))

    findings.extend(_check_circuit_sizes(tree))

    return True, False, findings, fixes


def _int_const(node):
    """Return the int value of a constant AST node, else None."""
    if isinstance(node, ast.Constant) and isinstance(node.value, int) \
            and not isinstance(node.value, bool):
        return node.value
    return None


def _check_circuit_sizes(tree) -> List[Finding]:
    """Statically range-check gate/measure calls against literal circuit sizes.

    Only engages when the snippet has exactly one QuantumCircuit(...) with a
    literal qubit count, assigned to a variable - the common AI-snippet shape -
    which keeps false positives low. Also flags zero-qubit circuits.
    """
    out: List[Finding] = []
    circuits = []  # (var_name, n_qubits, n_clbits)
    for node in ast.walk(tree):
        # Zero-qubit circuit, wherever it appears.
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name) \
                and node.func.id == "QuantumCircuit":
            if node.args and _int_const(node.args[0]) == 0:
                out.append(Finding(
                    "QISKIT-ZERO-QUBITS", "error",
                    "QuantumCircuit(0) has no qubits; it cannot hold a circuit.",
                    getattr(node, "lineno", None)))
        # Track `var = QuantumCircuit(<int>[, <int>])`.
        if isinstance(node, ast.Assign) and len(node.targets) == 1 \
                and isinstance(node.targets[0], ast.Name) \
                and isinstance(node.value, ast.Call) \
                and isinstance(node.value.func, ast.Name) \
                and node.value.func.id == "QuantumCircuit":
            args = node.value.args
            nq = _int_const(args[0]) if len(args) >= 1 else None
            nc = _int_const(args[1]) if len(args) >= 2 else 0
            circuits.append((node.targets[0].id, nq, nc))

    sized = [c for c in circuits if c[1] is not None]
    if len(sized) != 1:
        return out                      # ambiguous or unknown size -> stay quiet
    var, nq, nc = sized[0]
    if nq <= 0:
        return out                      # zero-qubit already reported

    for node in ast.walk(tree):
        if not (isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute)
                and isinstance(node.func.value, ast.Name)
                and node.func.value.id == var):
            continue
        attr = node.func.attr
        line = getattr(node, "lineno", None)
        if attr in _1Q_POS_GATES or attr in _2Q_POS_GATES:
            ints = [v for v in (_int_const(a) for a in node.args) if v is not None]
            for idx in ints:
                if idx >= nq:
                    out.append(Finding(
                        "QISKIT-QUBIT-INDEX-RANGE", "error",
                        f"Qubit index {idx} is out of range for a "
                        f"{nq}-qubit circuit (valid 0..{nq - 1}).", line))
            if attr in _2Q_POS_GATES and len(ints) >= 2 and ints[0] == ints[1]:
                out.append(Finding(
                    "QISKIT-SAME-QUBIT-2Q", "warning",
                    f"Two-qubit gate {attr}() uses qubit {ints[0]} as both "
                    f"control and target.", line))
        elif attr == "measure":
            if nc == 0:
                out.append(Finding(
                    "QISKIT-MEASURE-NO-CLBITS", "error",
                    "measure() called on a circuit with no classical bits; "
                    "construct it as QuantumCircuit(n, m) with m >= 1.", line))
            elif len(node.args) == 2:
                q, c = _int_const(node.args[0]), _int_const(node.args[1])
                if q is not None and q >= nq:
                    out.append(Finding(
                        "QISKIT-QUBIT-INDEX-RANGE", "error",
                        f"Qubit index {q} is out of range for a {nq}-qubit "
                        f"circuit (valid 0..{nq - 1}).", line))
                if c is not None and c >= nc:
                    out.append(Finding(
                        "QISKIT-CLBIT-INDEX-RANGE", "error",
                        f"Classical bit index {c} is out of range for "
                        f"{nc} classical bit(s) (valid 0..{nc - 1}).", line))
    return out
