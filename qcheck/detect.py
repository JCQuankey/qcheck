"""Detect which framework a snippet is, from extension + content."""
from __future__ import annotations

import os


def detect_framework(path: str, text: str) -> str:
    """Return one of: qasm2, qasm3, qiskit, python_unknown, unknown."""
    ext = os.path.splitext(path)[1].lower()
    low = text.lower()

    if ext == ".qasm" or "openqasm" in low:
        if "openqasm 3" in low:
            return "qasm3"
        if "openqasm 2" in low:
            return "qasm2"
        if "qubit[" in low or "bit[" in low:
            return "qasm3"
        if "qreg" in low or "creg" in low:
            return "qasm2"
        return "qasm2"

    if ext == ".py":
        if "pennylane" in low or "qml." in low:
            return "pennylane"
        if "qiskit" in low or "quantumcircuit" in low:
            return "qiskit"
        return "python_unknown"

    return "unknown"
