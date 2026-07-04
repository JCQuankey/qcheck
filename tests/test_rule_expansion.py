"""Rule-expansion pack 1: positive (fires) + negative (no false positive) tests."""
from qcheck.cli import verify_text


def _ids(path, text):
    return {f.id for f in verify_text(path, text).findings}


# --- QISKIT-GET-COUNTS-NO-MEASURE ---

def test_get_counts_without_measure_fires():
    text = ("from qiskit import QuantumCircuit\n"
            "qc = QuantumCircuit(2, 2)\nqc.h(0)\n"
            "counts = result.get_counts(qc)\n")
    assert "QISKIT-GET-COUNTS-NO-MEASURE" in _ids("s.py", text)


def test_get_counts_with_measure_does_not_fire():
    text = ("from qiskit import QuantumCircuit\n"
            "qc = QuantumCircuit(2, 2)\nqc.h(0)\nqc.measure_all()\n"
            "counts = result.get_counts(qc)\n")
    ids = _ids("s.py", text)
    assert "QISKIT-GET-COUNTS-NO-MEASURE" not in ids
    assert "QISKIT-NO-MEASURE" not in ids


# --- QISKIT-ASSEMBLE-REMOVED ---

def test_assemble_call_fires():
    text = ("from qiskit import QuantumCircuit, assemble\n"
            "qc = QuantumCircuit(1, 1)\nqc.measure_all()\nqobj = assemble(qc)\n")
    assert "QISKIT-ASSEMBLE-REMOVED" in _ids("s.py", text)


def test_no_assemble_does_not_fire():
    text = ("from qiskit import QuantumCircuit\n"
            "qc = QuantumCircuit(1, 1)\nqc.measure_all()\n")
    assert "QISKIT-ASSEMBLE-REMOVED" not in _ids("s.py", text)


# --- QASM-DUP-REGISTER ---

def test_duplicate_register_fires():
    text = ('OPENQASM 2.0;\ninclude "qelib1.inc";\n'
            "qreg q[2];\nqreg q[3];\ncreg c[2];\nmeasure q -> c;\n")
    assert "QASM-DUP-REGISTER" in _ids("s.qasm", text)


def test_distinct_registers_do_not_fire_dup():
    text = ('OPENQASM 2.0;\ninclude "qelib1.inc";\n'
            "qreg q[2];\nqreg r[2];\ncreg c[2];\nmeasure q -> c;\n")
    assert "QASM-DUP-REGISTER" not in _ids("s.qasm", text)


# --- QASM-NO-MEASURE ---

def test_qasm_no_measure_fires():
    text = ('OPENQASM 2.0;\ninclude "qelib1.inc";\n'
            "qreg q[2];\ncreg c[2];\nh q[0];\ncx q[0],q[1];\n")
    assert "QASM-NO-MEASURE" in _ids("s.qasm", text)


def test_qasm_with_measure_does_not_fire():
    text = ('OPENQASM 2.0;\ninclude "qelib1.inc";\n'
            "qreg q[2];\ncreg c[2];\nh q[0];\ncx q[0],q[1];\nmeasure q -> c;\n")
    assert "QASM-NO-MEASURE" not in _ids("s.qasm", text)


# --- QASM-VERSION-MISMATCH ---

def test_qasm3_syntax_in_qasm2_fires():
    text = ('OPENQASM 2.0;\ninclude "qelib1.inc";\nqubit[2] q;\nbit[2] c;\n')
    assert "QASM-VERSION-MISMATCH" in _ids("s.qasm", text)


def test_plain_qasm2_does_not_fire_version_mismatch():
    text = ('OPENQASM 2.0;\ninclude "qelib1.inc";\n'
            "qreg q[2];\ncreg c[2];\nmeasure q -> c;\n")
    assert "QASM-VERSION-MISMATCH" not in _ids("s.qasm", text)
