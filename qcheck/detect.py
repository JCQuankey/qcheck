"""Detect which framework a snippet is, from extension + content."""
from __future__ import annotations

import os


def detect_framework(path: str, text: str) -> str:
    """Return one of: qasm2, qasm3, qiskit, pennylane, cirq,
    python_unknown, unknown."""
    ext = os.path.splitext(path)[1].lower()
    low = text.lower()

    # A .py file is Python, full stop: a docstring that merely mentions
    # OpenQASM (as qiskit's own sources do) must never route it to the QASM
    # parser. Content-based QASM detection applies only to non-.py inputs.
    if ext != ".py" and (ext == ".qasm" or "openqasm" in low):
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
        # Import evidence first: what a file imports beats what it merely
        # mentions (a docstring saying "ported from Cirq" must not reroute a
        # Qiskit file). Files importing several frameworks route to the first
        # match below - qiskit before cirq, so interop code keeps the larger
        # Qiskit rule set.
        if "import pennylane" in low or "from pennylane" in low:
            return "pennylane"
        if "import qiskit" in low or "from qiskit" in low:
            return "qiskit"
        if "import cirq" in low or "from cirq" in low:
            return "cirq"
        # Mention fallback: catches snippets that forgot the import (the
        # missing-import rules exist exactly for these).
        if "pennylane" in low or "qml." in low:
            return "pennylane"
        if "qiskit" in low or "quantumcircuit" in low:
            return "qiskit"
        if "cirq." in low:
            return "cirq"
        return "python_unknown"

    return "unknown"
