from conftest import FIXTURES
from qcheck.cli import verify_text


def _verify(name):
    p = FIXTURES / name
    return verify_text(str(p), p.read_text())


def test_valid_qiskit_passes():
    r = _verify("valid_bell_qiskit.py")
    assert r.framework == "qiskit"
    assert r.status == "pass"
    assert r.errors == []


def test_missing_import_is_error():
    r = _verify("qiskit_missing_import.py")
    assert r.status == "fail"
    assert any(f.id == "QISKIT-MISSING-IMPORT" for f in r.errors)


def test_removed_api_is_error():
    r = _verify("qiskit_invalid_api.py")
    assert r.status == "fail"
    ids = {f.id for f in r.findings}
    assert "QISKIT-REMOVED-IMPORT" in ids or "QISKIT-EXECUTE" in ids
    # deprecated gate alias surfaces as a warning + a fix
    assert any(f.id == "QISKIT-DEPRECATED-GATE" for f in r.warnings)


def test_syntax_error_handled():
    r = verify_text("bad.py", "from qiskit import QuantumCircuit\nqc = QuantumCircuit(\n")
    assert r.syntax_valid is False
    assert r.status == "fail"
