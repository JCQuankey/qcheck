"""False-positive guards: legitimate/teaching snippets must not trip warning
rules. These lock in current low-noise behavior (no detection-logic change)."""
from qcheck.cli import verify_text

WARNINGS = {
    "QISKIT-NO-MEASURE", "QISKIT-NO-CIRCUIT", "QISKIT-GET-COUNTS-NO-MEASURE",
    "QISKIT-SAME-QUBIT-2Q", "QISKIT-DEPRECATED-PROVIDER-PATH",
    "QASM-NO-MEASURE", "QASM-SAME-QUBIT-2Q", "QASM-VERSION-MISMATCH",
    "QASM-MEASURE-SIZE-MISMATCH",
}


def _ids(path, text):
    return {f.id for f in verify_text(path, text).findings}


def test_complete_qiskit_bell_has_no_warnings():
    text = ("from qiskit import QuantumCircuit\n"
            "qc = QuantumCircuit(2, 2)\nqc.h(0)\nqc.cx(0, 1)\n"
            "qc.measure([0, 1], [0, 1])\n")
    assert not (_ids("s.py", text) & WARNINGS)


def test_qiskit_measure_all_then_get_counts_clean():
    text = ("from qiskit import QuantumCircuit\n"
            "qc = QuantumCircuit(2, 2)\nqc.h(0)\nqc.cx(0, 1)\nqc.measure_all()\n"
            "counts = result.get_counts(qc)\n")
    assert "QISKIT-GET-COUNTS-NO-MEASURE" not in _ids("s.py", text)
    assert "QISKIT-NO-MEASURE" not in _ids("s.py", text)


def test_qiskit_registers_properly_imported_clean():
    text = ("from qiskit import QuantumCircuit, QuantumRegister, ClassicalRegister\n"
            "qr = QuantumRegister(2)\ncr = ClassicalRegister(2)\n"
            "qc = QuantumCircuit(qr, cr)\nqc.h(0)\nqc.measure(qr, cr)\n")
    assert "QISKIT-REGISTER-MISSING-IMPORT" not in _ids("s.py", text)


def test_complete_qasm_bell_has_no_warnings():
    text = ('OPENQASM 2.0;\ninclude "qelib1.inc";\nqreg q[2];\ncreg c[2];\n'
            "h q[0];\ncx q[0],q[1];\nmeasure q -> c;\n")
    assert not (_ids("s.qasm", text) & WARNINGS)


def test_genuine_qasm3_no_version_mismatch():
    # Real OpenQASM 3 program -> qubit[] syntax is correct, must NOT be flagged.
    text = ('OPENQASM 3.0;\ninclude "stdgates.inc";\nqubit[2] q;\nbit[2] c;\n'
            "h q[0];\ncx q[0], q[1];\nc = measure q;\n")
    assert "QASM-VERSION-MISMATCH" not in _ids("s.qasm", text)


def test_matching_size_full_register_measure_clean():
    text = ('OPENQASM 2.0;\ninclude "qelib1.inc";\nqreg q[2];\ncreg c[2];\n'
            "h q[0];\ncx q[0],q[1];\nmeasure q -> c;\n")
    assert "QASM-MEASURE-SIZE-MISMATCH" not in _ids("s.qasm", text)


def test_distinct_qubit_multiqubit_gate_clean():
    text = ('OPENQASM 2.0;\ninclude "qelib1.inc";\nqreg q[3];\ncreg c[3];\n'
            "ccx q[0],q[1],q[2];\nmeasure q -> c;\n")
    assert "QASM-SAME-QUBIT-2Q" not in _ids("s.qasm", text)
