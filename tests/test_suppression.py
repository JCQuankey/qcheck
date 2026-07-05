"""Suppression mechanism: inline ignores, --disable, safety floor, contracts."""
import json

from qcheck.cli import main, verify_text, _exit_code
from qcheck.suppress import inline_ignores, UNSUPPRESSIBLE


# Emits QISKIT-REMOVED-IMPORT (line 1) and QISKIT-EXECUTE (line 5).
BROKEN_QISKIT = ("from qiskit import QuantumCircuit, execute\n"
                 "qc = QuantumCircuit(2, 2)\nqc.h(0)\nqc.measure_all()\n"
                 "result = execute(qc, backend)\n")


def _ids(name, text, **kw):
    return {f.id for f in verify_text(name, text, **kw).findings}


# --- inline parsing ---

def test_inline_ignores_parses_python_comment():
    ig = inline_ignores("x = 1  # qcheck: ignore[QISKIT-EXECUTE]\n")
    assert ig == {1: frozenset({"QISKIT-EXECUTE"})}


def test_inline_ignores_parses_qasm_comment_and_multiple_ids():
    ig = inline_ignores("cx q[0], q[0]; // qcheck: ignore[QASM-SAME-QUBIT-2Q, QASM-NO-MEASURE]\n")
    assert ig[1] == frozenset({"QASM-SAME-QUBIT-2Q", "QASM-NO-MEASURE"})


def test_bare_ignore_without_ids_is_not_a_directive():
    assert inline_ignores("x = 1  # qcheck: ignore\n") == {}
    assert inline_ignores("x = 1  # qcheck: ignore[]\n") == {}


# --- inline suppression per surface ---

def test_inline_suppression_qiskit():
    text = ("from qiskit import QuantumCircuit\n"
            "qc = QuantumCircuit(2, 2)\nqc.h(0)\n"
            "qc.cnot(0, 1)  # qcheck: ignore[QISKIT-DEPRECATED-GATE]\n"
            "qc.measure_all()\n")
    r = verify_text("s.py", text)
    assert "QISKIT-DEPRECATED-GATE" not in {f.id for f in r.findings}
    assert r.suppressed == 1
    assert _exit_code(r) == 0


def test_inline_suppression_qasm():
    text = ('OPENQASM 2.0;\ninclude "qelib1.inc";\nqreg q[2];\ncreg c[2];\n'
            "cx q[0], q[0]; // qcheck: ignore[QASM-SAME-QUBIT-2Q]\n"
            "measure q -> c;\n")
    r = verify_text("s.qasm", text)
    assert "QASM-SAME-QUBIT-2Q" not in {f.id for f in r.findings}
    assert r.suppressed == 1


def test_inline_suppression_pennylane():
    text = ("import pennylane as qml\n"
            "dev = qml.device('default.qubit', wires=2)\n"
            "@qml.qnode(dev)\n"
            "def circ():  # qcheck: ignore[PENNYLANE-QNODE-NO-RETURN]\n"
            "    qml.Hadamard(wires=0)\n")
    r = verify_text("s.py", text)
    assert "PENNYLANE-QNODE-NO-RETURN" not in {f.id for f in r.findings}
    assert r.suppressed == 1


def test_inline_suppression_cirq():
    text = ("import cirq\nq0 = cirq.LineQubit(0)\n"
            "op = cirq.CNOT(q0, q0)  # qcheck: ignore[CIRQ-SAME-QUBIT-2Q]\n")
    r = verify_text("s.py", text)
    assert "CIRQ-SAME-QUBIT-2Q" not in {f.id for f in r.findings}
    assert r.suppressed == 1


def test_inline_suppression_is_line_scoped():
    # QISKIT-EXECUTE fires on line 5; a directive on line 1 must not reach it.
    text = ("# qcheck: ignore[QISKIT-EXECUTE]\n" + BROKEN_QISKIT)
    r = verify_text("s.py", text)
    assert "QISKIT-EXECUTE" in {f.id for f in r.findings}
    # ...but the directive on the offending line itself does suppress it.
    text2 = BROKEN_QISKIT.replace(
        "result = execute(qc, backend)",
        "result = execute(qc, backend)  # qcheck: ignore[QISKIT-EXECUTE]")
    r2 = verify_text("s.py", text2)
    assert "QISKIT-EXECUTE" not in {f.id for f in r2.findings}
    assert r2.suppressed == 1


def test_wrong_rule_id_does_not_suppress():
    text = ("from qiskit import QuantumCircuit\n"
            "qc = QuantumCircuit(2, 2)\nqc.h(0)\n"
            "qc.cnot(0, 1)  # qcheck: ignore[QISKIT-EXECUTE]\n"
            "qc.measure_all()\n")
    r = verify_text("s.py", text)
    assert "QISKIT-DEPRECATED-GATE" in {f.id for f in r.findings}
    assert r.suppressed == 0


# --- safety floor ---

def test_unsafe_findings_not_inline_suppressible():
    text = ("import subprocess  # qcheck: ignore[PY-UNSAFE-IMPORT]\n"
            "subprocess.run(['ls'])  # qcheck: ignore[PY-UNSAFE-CALL]\n")
    r = verify_text("s.py", text)
    ids = {f.id for f in r.findings}
    assert "PY-UNSAFE-IMPORT" in ids and "PY-UNSAFE-CALL" in ids
    assert r.unsafe
    assert _exit_code(r) == 2
    assert r.suppressed == 0


def test_disable_refuses_safety_rules(capsys):
    rc = main(["verify", "-", "--disable", "PY-UNSAFE-CALL"])
    assert rc == 3
    assert "refusing to disable" in capsys.readouterr().err


def test_unsuppressible_set_is_the_safety_screen():
    assert UNSUPPRESSIBLE == {"PY-UNSAFE-IMPORT", "PY-UNSAFE-CALL",
                              "QASM-SUSPICIOUS"}


# --- --disable ---

def test_disable_drops_findings_and_exit_code():
    r = verify_text("s.py", BROKEN_QISKIT,
                    disabled=frozenset({"QISKIT-EXECUTE",
                                        "QISKIT-REMOVED-IMPORT"}))
    assert not {f.id for f in r.findings} & {"QISKIT-EXECUTE",
                                             "QISKIT-REMOVED-IMPORT"}
    assert r.suppressed == 2
    assert _exit_code(r) == 0


def test_disable_unsupported_is_the_mixed_repo_hatch():
    r = verify_text("s.py", "def add(a, b):\n    return a + b\n",
                    disabled=frozenset({"UNSUPPORTED"}))
    assert "UNSUPPORTED" not in {f.id for f in r.findings}
    assert _exit_code(r) == 0


def test_unsupported_not_inline_suppressible():
    text = "def add(a, b):  # qcheck: ignore[UNSUPPORTED]\n    return a + b\n"
    r = verify_text("s.py", text)
    assert "UNSUPPORTED" in {f.id for f in r.findings}


def test_unknown_disable_warns_but_runs(tmp_path, capsys):
    p = tmp_path / "ok.qasm"
    p.write_text('OPENQASM 2.0;\ninclude "qelib1.inc";\nqreg q[1];\n'
                 "creg c[1];\nmeasure q -> c;\n")
    rc = main(["verify", str(p), "--disable", "NOT-A-RULE"])
    err = capsys.readouterr().err
    assert rc == 0
    assert "does not match any known rule" in err


# --- --no-inline-suppress ---

def test_no_inline_suppress_ignores_directives():
    text = ("from qiskit import QuantumCircuit\n"
            "qc = QuantumCircuit(2, 2)\nqc.h(0)\n"
            "qc.cnot(0, 1)  # qcheck: ignore[QISKIT-DEPRECATED-GATE]\n"
            "qc.measure_all()\n")
    r = verify_text("s.py", text, no_inline_suppress=True)
    assert "QISKIT-DEPRECATED-GATE" in {f.id for f in r.findings}
    assert r.suppressed == 0


# --- output contracts ---

def test_json_carries_suppressed_count(tmp_path, capsys):
    p = tmp_path / "s.py"
    p.write_text("from qiskit import QuantumCircuit\n"
                 "qc = QuantumCircuit(2, 2)\nqc.h(0)\n"
                 "qc.cnot(0, 1)  # qcheck: ignore[QISKIT-DEPRECATED-GATE]\n"
                 "qc.measure_all()\n")
    rc = main(["verify", str(p), "--json"])
    d = json.loads(capsys.readouterr().out)
    assert rc == 0
    assert d["suppressed"] == 1
    assert all(f["id"] != "QISKIT-DEPRECATED-GATE" for f in d["static_checks"])


def test_multifile_summary_carries_suppressed(tmp_path, capsys):
    a = tmp_path / "a.py"
    a.write_text("from qiskit import QuantumCircuit\n"
                 "qc = QuantumCircuit(2, 2)\nqc.h(0)\n"
                 "qc.cnot(0, 1)  # qcheck: ignore[QISKIT-DEPRECATED-GATE]\n"
                 "qc.measure_all()\n")
    b = tmp_path / "b.qasm"
    b.write_text('OPENQASM 2.0;\ninclude "qelib1.inc";\nqreg q[1];\n'
                 "creg c[1];\nmeasure q -> c;\n")
    rc = main(["verify", str(a), str(b), "--json"])
    d = json.loads(capsys.readouterr().out)
    assert rc == 0
    assert d["summary"]["suppressed"] == 1


def test_sarif_omits_suppressed_findings(tmp_path, capsys):
    p = tmp_path / "s.py"
    p.write_text("from qiskit import QuantumCircuit\n"
                 "qc = QuantumCircuit(2, 2)\nqc.h(0)\n"
                 "qc.cnot(0, 1)  # qcheck: ignore[QISKIT-DEPRECATED-GATE]\n"
                 "qc.measure_all()\n")
    rc = main(["verify", str(p), "--format", "sarif"])
    doc = json.loads(capsys.readouterr().out)
    assert rc == 0
    assert doc["version"] == "2.1.0"
    assert all(res["ruleId"] != "QISKIT-DEPRECATED-GATE"
               for res in doc["runs"][0]["results"])


def test_no_suppression_means_zero_and_unchanged_behavior():
    r = verify_text("s.py", BROKEN_QISKIT)
    assert r.suppressed == 0
    assert _exit_code(r) == 1
