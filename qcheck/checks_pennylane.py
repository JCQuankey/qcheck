"""Static checks for PennyLane snippets via the stdlib `ast` module.

No execution, no PennyLane import, stdlib only. Detects a small set of
high-confidence, deterministic mistakes common in AI-generated PennyLane code:
using `qml` without importing it, zero/negative device wires, and a QNode with
no return. Low false-positive by design - heuristic checks are intentionally
left out of this MVP.
"""
from __future__ import annotations

import ast
from typing import List, Tuple

from .report import Finding
from .safety import scan_python_safety

# Attribute names that, accessed as `qml.<name>`, clearly mean PennyLane.
_KNOWN_QML = {
    "device", "qnode", "QNode", "RX", "RY", "RZ", "Rot", "CNOT", "CZ", "CY",
    "Hadamard", "PauliX", "PauliY", "PauliZ", "Identity", "Toffoli", "SWAP",
    "expval", "probs", "state", "sample", "var", "counts", "PhaseShift",
    "ctrl", "adjoint", "measure",
}


def _int_const(node):
    """Int value of a constant AST node (incl. -literal), else None."""
    if isinstance(node, ast.Constant) and isinstance(node.value, int) \
            and not isinstance(node.value, bool):
        return node.value
    if isinstance(node, ast.UnaryOp) and isinstance(node.op, ast.USub) \
            and isinstance(node.operand, ast.Constant) \
            and isinstance(node.operand.value, int) \
            and not isinstance(node.operand.value, bool):
        return -node.operand.value
    return None


def _is_qml_attr(func, attr: str) -> bool:
    """True if `func` is `qml.<attr>`."""
    return (isinstance(func, ast.Attribute) and func.attr == attr
            and isinstance(func.value, ast.Name) and func.value.id == "qml")


def _has_qml_decorator(node: ast.FunctionDef) -> bool:
    for dec in node.decorator_list:
        target = dec.func if isinstance(dec, ast.Call) else dec
        if _is_qml_attr(target, "qnode"):
            return True
    return False


def check_pennylane(text: str) -> Tuple[bool, bool, List[Finding], List[str]]:
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
            "snippets should not need it."]

    bound: set = set()          # names bound in the module (incl. 'qml')
    qml_known_line = None       # first line using qml.<known-symbol>

    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                bound.add((alias.asname or alias.name).split(".")[0])
        elif isinstance(node, ast.ImportFrom):
            for alias in node.names:
                bound.add(alias.asname or alias.name)
        elif isinstance(node, ast.Assign):
            for t in node.targets:
                if isinstance(t, ast.Name):
                    bound.add(t.id)
        elif isinstance(node, ast.Attribute) and isinstance(node.value, ast.Name) \
                and node.value.id == "qml" and node.attr in _KNOWN_QML:
            if qml_known_line is None:
                qml_known_line = getattr(node, "lineno", None)
        # device wires checks
        if isinstance(node, ast.Call) and _is_qml_attr(node.func, "device"):
            _check_device_wires(node, findings)
        # qnode with no return
        if isinstance(node, ast.FunctionDef) and _has_qml_decorator(node):
            if not any(isinstance(n, ast.Return) for n in ast.walk(node)):
                findings.append(Finding(
                    "PENNYLANE-QNODE-NO-RETURN", "warning",
                    f"QNode '{node.name}' has no return; a QNode must return a "
                    f"measurement (e.g. return qml.expval(...)).",
                    getattr(node, "lineno", None)))

    if qml_known_line is not None and "qml" not in bound:
        findings.append(Finding(
            "PENNYLANE-QML-MISSING-IMPORT", "error",
            "PennyLane is used as 'qml' but never imported.", qml_known_line))
        fixes.append("Add 'import pennylane as qml'.")

    return True, False, findings, fixes


def _check_device_wires(node: ast.Call, findings: List[Finding]) -> None:
    """Flag qml.device(..., wires=0) / negative wires (keyword or 2nd positional)."""
    wires_node = None
    for kw in node.keywords:
        if kw.arg == "wires":
            wires_node = kw.value
    if wires_node is None and len(node.args) >= 2:
        wires_node = node.args[1]           # device(name, wires, ...)
    if wires_node is None:
        return
    v = _int_const(wires_node)
    line = getattr(node, "lineno", None)
    if v == 0:
        findings.append(Finding(
            "PENNYLANE-DEVICE-ZERO-WIRES", "error",
            "qml.device(..., wires=0) has no wires.", line))
    elif v is not None and v < 0:
        findings.append(Finding(
            "PENNYLANE-DEVICE-NEGATIVE-WIRES", "error",
            f"qml.device(..., wires={v}) has a negative wire count.", line))
