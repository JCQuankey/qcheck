"""Rule-expansion pack 2: positive (fires) + negative (no false positive) tests."""
from qcheck.cli import verify_text


def _ids(path, text):
    return {f.id for f in verify_text(path, text).findings}


# --- QISKIT-ZERO-QUBITS ---

def test_zero_qubit_circuit_fires():
    assert "QISKIT-ZERO-QUBITS" in _ids(
        "s.py", "from qiskit import QuantumCircuit\nqc = QuantumCircuit(0)\n")


def test_nonzero_circuit_no_zero_qubits():
    assert "QISKIT-ZERO-QUBITS" not in _ids(
        "s.py", "from qiskit import QuantumCircuit\nqc = QuantumCircuit(2)\n")


# --- QISKIT-QUBIT-INDEX-RANGE ---

def test_qubit_index_out_of_range_fires():
    text = ("from qiskit import QuantumCircuit\nqc = QuantumCircuit(2, 2)\n"
            "qc.h(5)\nqc.measure_all()\n")
    assert "QISKIT-QUBIT-INDEX-RANGE" in _ids("s.py", text)


def test_qubit_index_in_range_does_not_fire():
    text = ("from qiskit import QuantumCircuit\nqc = QuantumCircuit(2, 2)\n"
            "qc.h(0)\nqc.cx(0, 1)\nqc.measure_all()\n")
    assert "QISKIT-QUBIT-INDEX-RANGE" not in _ids("s.py", text)


def test_index_check_silent_when_size_unknown():
    # size comes from a variable -> no literal size -> stay quiet (no false positive)
    text = ("from qiskit import QuantumCircuit\nn = 2\nqc = QuantumCircuit(n)\n"
            "qc.h(5)\n")
    assert "QISKIT-QUBIT-INDEX-RANGE" not in _ids("s.py", text)


# --- QISKIT-CLBIT-INDEX-RANGE ---

def test_clbit_index_out_of_range_fires():
    text = ("from qiskit import QuantumCircuit\nqc = QuantumCircuit(2, 1)\n"
            "qc.measure(0, 3)\n")
    assert "QISKIT-CLBIT-INDEX-RANGE" in _ids("s.py", text)


def test_clbit_index_in_range_does_not_fire():
    text = ("from qiskit import QuantumCircuit\nqc = QuantumCircuit(2, 2)\n"
            "qc.measure(0, 0)\n")
    assert "QISKIT-CLBIT-INDEX-RANGE" not in _ids("s.py", text)


# --- QISKIT-MEASURE-NO-CLBITS ---

def test_measure_without_clbits_fires():
    text = ("from qiskit import QuantumCircuit\nqc = QuantumCircuit(2)\n"
            "qc.measure(0, 0)\n")
    assert "QISKIT-MEASURE-NO-CLBITS" in _ids("s.py", text)


def test_measure_with_clbits_does_not_fire():
    text = ("from qiskit import QuantumCircuit\nqc = QuantumCircuit(2, 2)\n"
            "qc.measure(0, 0)\n")
    assert "QISKIT-MEASURE-NO-CLBITS" not in _ids("s.py", text)


# --- QISKIT-SAME-QUBIT-2Q ---

def test_same_qubit_two_qubit_gate_fires():
    text = ("from qiskit import QuantumCircuit\nqc = QuantumCircuit(2, 2)\n"
            "qc.cx(0, 0)\nqc.measure_all()\n")
    assert "QISKIT-SAME-QUBIT-2Q" in _ids("s.py", text)


def test_distinct_qubit_two_qubit_gate_does_not_fire():
    text = ("from qiskit import QuantumCircuit\nqc = QuantumCircuit(2, 2)\n"
            "qc.cx(0, 1)\nqc.measure_all()\n")
    assert "QISKIT-SAME-QUBIT-2Q" not in _ids("s.py", text)


# --- QASM-ZERO-REGISTER ---

def test_qasm_zero_register_fires():
    text = ('OPENQASM 2.0;\ninclude "qelib1.inc";\nqreg q[0];\ncreg c[2];\n')
    assert "QASM-ZERO-REGISTER" in _ids("s.qasm", text)


def test_qasm_nonzero_register_does_not_fire():
    text = ('OPENQASM 2.0;\ninclude "qelib1.inc";\nqreg q[2];\ncreg c[2];\n'
            "measure q -> c;\n")
    assert "QASM-ZERO-REGISTER" not in _ids("s.qasm", text)


# --- QASM-SAME-QUBIT-2Q ---

def test_qasm_same_qubit_fires():
    text = ('OPENQASM 2.0;\ninclude "qelib1.inc";\nqreg q[2];\ncreg c[2];\n'
            "cx q[0],q[0];\nmeasure q -> c;\n")
    assert "QASM-SAME-QUBIT-2Q" in _ids("s.qasm", text)


def test_qasm_distinct_qubits_do_not_fire():
    text = ('OPENQASM 2.0;\ninclude "qelib1.inc";\nqreg q[2];\ncreg c[2];\n'
            "cx q[0],q[1];\nmeasure q -> c;\n")
    assert "QASM-SAME-QUBIT-2Q" not in _ids("s.qasm", text)
