from conftest import FIXTURES
from qcheck.cli import verify_text


def _verify(name):
    p = FIXTURES / name
    return verify_text(str(p), p.read_text())


def test_valid_bell_passes():
    r = _verify("valid_bell.qasm")
    assert r.status == "pass"
    assert r.framework == "qasm2"
    assert r.errors == []


def test_missing_register_is_error():
    r = _verify("invalid_missing_register.qasm")
    assert r.status == "fail"
    assert any(f.id == "QASM-UNDECLARED-REG" for f in r.errors)


def test_bad_measurement_out_of_range():
    r = _verify("invalid_bad_measurement.qasm")
    assert r.status == "fail"
    assert any(f.id in ("QASM-INDEX-RANGE", "QASM-MEASURE-TGT") for f in r.errors)


def test_missing_header_detected():
    r = verify_text("snippet.qasm", 'include "qelib1.inc";\nqreg q[1];\nh q[0];\n')
    assert any(f.id == "QASM-NO-HEADER" for f in r.errors)
