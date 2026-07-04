"""Coverage hardening: Parameter-missing-import, more removed modules, and
bare-form measurement operand checks. Positive + negative tests."""
from qcheck.cli import verify_text


def _ids(path, text):
    return {f.id for f in verify_text(path, text).findings}


# --- QISKIT-PARAMETER-MISSING-IMPORT ---

def test_parameter_missing_import_fires():
    text = ("from qiskit import QuantumCircuit\nqc = QuantumCircuit(1, 1)\n"
            "qc.rx(Parameter('t'), 0)\nqc.measure_all()\n")
    assert "QISKIT-PARAMETER-MISSING-IMPORT" in _ids("s.py", text)


def test_parameter_imported_does_not_fire():
    text = ("from qiskit import QuantumCircuit\nfrom qiskit.circuit import Parameter\n"
            "qc = QuantumCircuit(1, 1)\nqc.rx(Parameter('t'), 0)\nqc.measure_all()\n")
    assert "QISKIT-PARAMETER-MISSING-IMPORT" not in _ids("s.py", text)


# --- QISKIT-REMOVED-MODULE (qiskit.tools) ---

def test_qiskit_tools_removed_module_fires():
    assert "QISKIT-REMOVED-MODULE" in _ids(
        "s.py", "from qiskit.tools import job_monitor\n")


# --- QASM bare-form measurement operands ---

def test_bare_measure_undeclared_target_fires():
    text = ('OPENQASM 2.0;\ninclude "qelib1.inc";\nqreg q[2];\n'
            "h q[0];\nmeasure q -> c;\n")
    assert "QASM-MEASURE-TGT" in _ids("s.qasm", text)


def test_bare_measure_undeclared_source_fires():
    text = ('OPENQASM 2.0;\ninclude "qelib1.inc";\ncreg c[2];\nmeasure q -> c;\n')
    assert "QASM-MEASURE-SRC" in _ids("s.qasm", text)


def test_bare_measure_declared_registers_clean():
    text = ('OPENQASM 2.0;\ninclude "qelib1.inc";\nqreg q[2];\ncreg c[2];\n'
            "h q[0];\nmeasure q -> c;\n")
    ids = _ids("s.qasm", text)
    assert "QASM-MEASURE-TGT" not in ids and "QASM-MEASURE-SRC" not in ids
