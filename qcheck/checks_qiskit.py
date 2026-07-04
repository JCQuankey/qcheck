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

_REMOVED_FROM_QISKIT = {"execute", "Aer", "IBMQ", "BasicAer"}
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
            elif isinstance(func, ast.Attribute):
                if func.attr in ("measure", "measure_all", "measure_active"):
                    has_measure = True
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

    if not uses_quantumcircuit:
        findings.append(Finding(
            "QISKIT-NO-CIRCUIT", "warning",
            "No QuantumCircuit(...) construction detected.", None))

    return True, False, findings, fixes
