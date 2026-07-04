"""Rule-expansion pack 4: positive (fires) + negative (no false positive) tests."""
from qcheck.cli import verify_text


def _ids(path, text):
    return {f.id for f in verify_text(path, text).findings}


# --- QISKIT-NEGATIVE-QUBITS ---

def test_negative_qubits_fires():
    assert "QISKIT-NEGATIVE-QUBITS" in _ids(
        "s.py", "from qiskit import QuantumCircuit\nqc = QuantumCircuit(-1)\n")


def test_positive_qubits_no_negative():
    assert "QISKIT-NEGATIVE-QUBITS" not in _ids(
        "s.py", "from qiskit import QuantumCircuit\nqc = QuantumCircuit(2)\n")


# --- QISKIT-ZERO-SIZED-REGISTER ---

def test_zero_sized_register_fires():
    text = ("from qiskit import QuantumCircuit, QuantumRegister\n"
            "qr = QuantumRegister(0)\nqc = QuantumCircuit(qr)\n")
    assert "QISKIT-ZERO-SIZED-REGISTER" in _ids("s.py", text)


def test_nonzero_register_does_not_fire():
    text = ("from qiskit import QuantumCircuit, QuantumRegister\n"
            "qr = QuantumRegister(2)\nqc = QuantumCircuit(qr)\n")
    assert "QISKIT-ZERO-SIZED-REGISTER" not in _ids("s.py", text)


# --- QISKIT-BIND-PARAMETERS-DEPRECATED ---

def test_bind_parameters_fires():
    text = ("from qiskit import QuantumCircuit\nqc = QuantumCircuit(1, 1)\n"
            "qc.measure_all()\nqc2 = qc.bind_parameters({})\n")
    assert "QISKIT-BIND-PARAMETERS-DEPRECATED" in _ids("s.py", text)


def test_assign_parameters_does_not_fire():
    text = ("from qiskit import QuantumCircuit\nqc = QuantumCircuit(1, 1)\n"
            "qc.measure_all()\nqc2 = qc.assign_parameters({})\n")
    assert "QISKIT-BIND-PARAMETERS-DEPRECATED" not in _ids("s.py", text)


# --- QISKIT-SNAPSHOT-REMOVED ---

def test_snapshot_fires():
    text = ("from qiskit import QuantumCircuit\nqc = QuantumCircuit(1, 1)\n"
            "qc.snapshot('s')\nqc.measure_all()\n")
    assert "QISKIT-SNAPSHOT-REMOVED" in _ids("s.py", text)


def test_no_snapshot_does_not_fire():
    text = ("from qiskit import QuantumCircuit\nqc = QuantumCircuit(1, 1)\n"
            "qc.measure_all()\n")
    assert "QISKIT-SNAPSHOT-REMOVED" not in _ids("s.py", text)


# --- QISKIT-DEPRECATED-GATE (u1/u2/u3 extension) ---

def test_u1_gate_flagged_as_deprecated():
    text = ("from qiskit import QuantumCircuit\nqc = QuantumCircuit(2, 2)\n"
            "qc.u1(0.5, 0)\nqc.measure_all()\n")
    assert "QISKIT-DEPRECATED-GATE" in _ids("s.py", text)


def test_current_gate_not_deprecated():
    text = ("from qiskit import QuantumCircuit\nqc = QuantumCircuit(2, 2)\n"
            "qc.p(0.5, 0)\nqc.measure_all()\n")
    assert "QISKIT-DEPRECATED-GATE" not in _ids("s.py", text)


# --- QASM-DUPLICATE-INCLUDE ---

def test_duplicate_include_fires():
    text = ('OPENQASM 2.0;\ninclude "qelib1.inc";\ninclude "qelib1.inc";\n'
            "qreg q[2];\ncreg c[2];\nmeasure q -> c;\n")
    assert "QASM-DUPLICATE-INCLUDE" in _ids("s.qasm", text)


def test_single_include_does_not_fire():
    text = ('OPENQASM 2.0;\ninclude "qelib1.inc";\nqreg q[2];\ncreg c[2];\n'
            "measure q -> c;\n")
    assert "QASM-DUPLICATE-INCLUDE" not in _ids("s.qasm", text)
