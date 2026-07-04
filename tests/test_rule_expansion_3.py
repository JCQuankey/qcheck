"""Rule-expansion pack 3: positive (fires) + negative (no false positive) tests."""
from qcheck.cli import verify_text


def _ids(path, text):
    return {f.id for f in verify_text(path, text).findings}


# --- QISKIT-REMOVED-MODULE ---

def test_removed_module_fires():
    assert "QISKIT-REMOVED-MODULE" in _ids(
        "s.py", "from qiskit.aqua import QuantumInstance\n")


def test_current_qiskit_import_no_removed_module():
    assert "QISKIT-REMOVED-MODULE" not in _ids(
        "s.py", "from qiskit import QuantumCircuit\n")


# --- QISKIT-DEPRECATED-PROVIDER-PATH ---

def test_deprecated_provider_path_fires():
    assert "QISKIT-DEPRECATED-PROVIDER-PATH" in _ids(
        "s.py", "from qiskit.providers.aer import AerSimulator\n")


def test_qiskit_aer_package_not_flagged():
    assert "QISKIT-DEPRECATED-PROVIDER-PATH" not in _ids(
        "s.py", "from qiskit_aer import AerSimulator\n")


# --- QISKIT-REGISTER-MISSING-IMPORT ---

def test_register_missing_import_fires():
    text = ("from qiskit import QuantumCircuit\n"
            "qr = QuantumRegister(2)\nqc = QuantumCircuit(qr)\n")
    assert "QISKIT-REGISTER-MISSING-IMPORT" in _ids("s.py", text)


def test_register_imported_does_not_fire():
    text = ("from qiskit import QuantumCircuit, QuantumRegister\n"
            "qr = QuantumRegister(2)\nqc = QuantumCircuit(qr)\n")
    assert "QISKIT-REGISTER-MISSING-IMPORT" not in _ids("s.py", text)


# --- QISKIT-TRANSPILE-MISSING-IMPORT ---

def test_transpile_missing_import_fires():
    text = ("from qiskit import QuantumCircuit\n"
            "qc = QuantumCircuit(2, 2)\nqc.measure_all()\nt = transpile(qc)\n")
    assert "QISKIT-TRANSPILE-MISSING-IMPORT" in _ids("s.py", text)


def test_transpile_imported_does_not_fire():
    text = ("from qiskit import QuantumCircuit, transpile\n"
            "qc = QuantumCircuit(2, 2)\nqc.measure_all()\nt = transpile(qc)\n")
    assert "QISKIT-TRANSPILE-MISSING-IMPORT" not in _ids("s.py", text)


# --- QASM-CLASSICAL-AS-QUBIT ---

def test_classical_as_qubit_fires():
    text = ('OPENQASM 2.0;\ninclude "qelib1.inc";\nqreg q[2];\ncreg c[2];\n'
            "h c[0];\nmeasure q -> c;\n")
    assert "QASM-CLASSICAL-AS-QUBIT" in _ids("s.qasm", text)


def test_gate_on_qubit_does_not_fire():
    text = ('OPENQASM 2.0;\ninclude "qelib1.inc";\nqreg q[2];\ncreg c[2];\n'
            "h q[0];\nmeasure q -> c;\n")
    assert "QASM-CLASSICAL-AS-QUBIT" not in _ids("s.qasm", text)


# --- QASM-MEASURE-SIZE-MISMATCH ---

def test_measure_size_mismatch_fires():
    text = ('OPENQASM 2.0;\ninclude "qelib1.inc";\nqreg q[3];\ncreg c[2];\n'
            "h q[0];\nmeasure q -> c;\n")
    assert "QASM-MEASURE-SIZE-MISMATCH" in _ids("s.qasm", text)


def test_matching_measure_sizes_do_not_fire():
    text = ('OPENQASM 2.0;\ninclude "qelib1.inc";\nqreg q[2];\ncreg c[2];\n'
            "h q[0];\nmeasure q -> c;\n")
    assert "QASM-MEASURE-SIZE-MISMATCH" not in _ids("s.qasm", text)
