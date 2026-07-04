from conftest import FIXTURES
from qcheck.cli import verify_text


def test_malicious_python_marked_unsafe():
    p = FIXTURES / "malicious.py"
    r = verify_text(str(p), p.read_text())
    assert r.unsafe is True
    assert any(f.id in ("PY-UNSAFE-IMPORT", "PY-UNSAFE-CALL") for f in r.findings)


def test_eval_call_rejected():
    r = verify_text("x.py", "from qiskit import QuantumCircuit\neval('2+2')\n")
    assert r.unsafe is True


def test_subprocess_import_rejected():
    r = verify_text("x.py", "import subprocess\nsubprocess.run(['ls'])\n")
    assert r.unsafe is True


def test_qasm_with_injected_shell_is_suspicious():
    r = verify_text("x.qasm", "OPENQASM 2.0;\n// rm -rf /\nimport os\n")
    assert any(f.id == "QASM-SUSPICIOUS" for f in r.findings)
    assert r.syntax_valid is False
