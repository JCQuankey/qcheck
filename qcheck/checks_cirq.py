"""Static checks for Cirq snippets via the stdlib `ast` module.

No execution, no Cirq import, stdlib only. Detects a small set of
high-confidence, deterministic mistakes common in AI-generated Cirq code:
using `cirq` without importing it, `cirq.measure()` with no qubits (raises
ValueError in Cirq), a two-qubit gate given the same qubit twice (raises
"Duplicate qids"), and an empty `cirq.LineQubit.range(...)`. Low
false-positive by design - heuristic checks are intentionally left out.
"""
from __future__ import annotations

import ast
from typing import List, Optional, Tuple

from .report import Finding
from .safety import scan_python_safety

# Attribute names that, accessed as `cirq.<name>`, clearly mean Cirq.
_KNOWN_CIRQ = {
    "Circuit", "LineQubit", "GridQubit", "NamedQubit", "Simulator",
    "measure", "measure_each", "Moment", "ops", "unitary", "sample",
    "H", "X", "Y", "Z", "S", "T", "CNOT", "CZ", "SWAP", "ISWAP",
    "rx", "ry", "rz", "Rx", "Ry", "Rz", "XX", "YY", "ZZ", "TOFFOLI",
}

# `cirq.<gate>(a, b)` calls that require two distinct qubits.
_TWO_QUBIT_GATES = ("CNOT", "CZ", "SWAP", "ISWAP", "XX", "YY", "ZZ")


def _int_const(node) -> Optional[int]:
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


def _is_cirq_attr(func, attr: str) -> bool:
    """True if `func` is `cirq.<attr>`."""
    return (isinstance(func, ast.Attribute) and func.attr == attr
            and isinstance(func.value, ast.Name) and func.value.id == "cirq")


def _same_qubit_operand(a, b) -> bool:
    """True only when `a` and `b` are provably the same qubit expression.

    Deterministic cases only: the same bare name (`q, q`) or the same
    name subscripted by the same int literal (`qs[0], qs[0]`). Anything
    else (calls, attributes, different names) is treated as unknown.
    """
    if isinstance(a, ast.Name) and isinstance(b, ast.Name):
        return a.id == b.id
    if isinstance(a, ast.Subscript) and isinstance(b, ast.Subscript) \
            and isinstance(a.value, ast.Name) and isinstance(b.value, ast.Name) \
            and a.value.id == b.value.id:
        ia, ib = _int_const(a.slice), _int_const(b.slice)
        return ia is not None and ia == ib
    return False


def check_cirq(text: str) -> Tuple[bool, bool, List[Finding], List[str]]:
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

    bound: set = set()          # names bound in the module (incl. 'cirq')
    cirq_known_line = None      # first line using cirq.<known-symbol>

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
                and node.value.id == "cirq" and node.attr in _KNOWN_CIRQ:
            if cirq_known_line is None:
                cirq_known_line = getattr(node, "lineno", None)
        if isinstance(node, ast.Call):
            _check_call(node, findings)

    if cirq_known_line is not None and "cirq" not in bound:
        findings.append(Finding(
            "CIRQ-MISSING-IMPORT", "error",
            "Cirq is used as 'cirq' but never imported.", cirq_known_line))
        fixes.append("Add 'import cirq'.")

    return True, False, findings, fixes


def _check_call(node: ast.Call, findings: List[Finding]) -> None:
    line = getattr(node, "lineno", None)

    # cirq.measure() with no qubits raises ValueError in Cirq.
    # `cirq.measure(*qubits, key=...)` has a Starred arg, so it never matches.
    if _is_cirq_attr(node.func, "measure") and not node.args:
        findings.append(Finding(
            "CIRQ-MEASURE-NO-QUBITS", "error",
            "cirq.measure() is called with no qubits; Cirq raises "
            "ValueError on an empty measurement.", line))
        return

    # cirq.LineQubit.range(0) / range(-n) produce an empty qubit list.
    # Only the exact single-literal form fires; range(a, b) and variables
    # are left alone.
    f = node.func
    if isinstance(f, ast.Attribute) and f.attr == "range" \
            and _is_cirq_attr(f.value, "LineQubit") \
            and len(node.args) == 1 and not node.keywords:
        v = _int_const(node.args[0])
        if v is not None and v <= 0:
            findings.append(Finding(
                "CIRQ-EMPTY-LINEQUBITS", "warning",
                f"cirq.LineQubit.range({v}) produces no qubits; the "
                f"resulting list is empty.", line))
            return

    # Two-qubit gate with the same qubit twice raises "Duplicate qids".
    for gate in _TWO_QUBIT_GATES:
        if _is_cirq_attr(node.func, gate) and len(node.args) == 2 \
                and _same_qubit_operand(node.args[0], node.args[1]):
            findings.append(Finding(
                "CIRQ-SAME-QUBIT-2Q", "warning",
                f"Two-qubit gate cirq.{gate}(...) uses the same qubit as "
                f"both operands; Cirq raises 'Duplicate qids'.", line))
            return
