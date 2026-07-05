"""Regression tests for measured false positives (July 2026 corpus pass).

Frozen from a run of qcheck over the installed sources of qiskit 2.5,
pennylane 0.45 and cirq-core 1.7 plus canonical user patterns: the quantum
rules were clean, but the framework router and the safety screen produced
the false positives pinned here. Each test encodes one measured failure.
"""
from qcheck.cli import verify_text, _exit_code
from qcheck.detect import detect_framework


def _ids(name, text):
    return {f.id for f in verify_text(name, text).findings}


# --- router: a .py file must never be parsed as OpenQASM ---

def test_py_file_with_openqasm_docstring_stays_python():
    # qiskit/circuit/quantumcircuit.py mentions OpenQASM in its docstring and
    # was misrouted to the QASM parser (16k+ bogus findings).
    text = ('"""Helpers for exporting a circuit to OpenQASM 2.0."""\n'
            "from qiskit import QuantumCircuit\n"
            "qc = QuantumCircuit(2, 2)\nqc.h(0)\nqc.measure_all()\n")
    assert detect_framework("quantumcircuit.py", text) == "qiskit"
    assert not any(f.id.startswith("QASM-")
                   for f in verify_text("quantumcircuit.py", text).findings)


def test_qasm_file_still_routes_to_qasm():
    text = 'OPENQASM 2.0;\ninclude "qelib1.inc";\nqreg q[1];\ncreg c[1];\nmeasure q -> c;\n'
    assert detect_framework("bell.qasm", text) == "qasm2"


def test_extensionless_openqasm_content_still_routes_to_qasm():
    # stdin and unnamed snippets keep content-based detection.
    text = "OPENQASM 2.0;\nqreg q[1];\n"
    assert detect_framework("stdin.qasm", text) == "qasm2"


# --- safety screen: receiver-aware attribute calls ---
# Canonical-correct Qiskit 1.0 patterns (the ones qcheck's own guidance
# recommends) must not be flagged unsafe.

def test_backend_run_is_not_unsafe():
    text = ("from qiskit import QuantumCircuit, transpile\n"
            "qc = QuantumCircuit(2, 2)\nqc.h(0)\nqc.measure_all()\n"
            "tqc = transpile(qc, backend)\n"
            "job = backend.run(tqc)\n")
    r = verify_text("s.py", text)
    assert not r.unsafe
    assert "PY-UNSAFE-CALL" not in {f.id for f in r.findings}
    assert _exit_code(r) == 0


def test_sampler_run_is_not_unsafe():
    text = ("from qiskit import QuantumCircuit\n"
            "qc = QuantumCircuit(1, 1)\nqc.measure_all()\n"
            "job = sampler.run([qc])\n")
    assert "PY-UNSAFE-CALL" not in _ids("s.py", text)


def test_dict_get_is_not_unsafe():
    text = ("from qiskit import QuantumCircuit\n"
            "qc = QuantumCircuit(1, 1)\nqc.measure_all()\n"
            "n = counts.get('00', 0)\n")
    assert "PY-UNSAFE-CALL" not in _ids("s.py", text)


def test_list_remove_is_not_unsafe():
    text = ("from qiskit import QuantumCircuit\n"
            "qc = QuantumCircuit(1, 1)\nqc.measure_all()\n"
            "gates.remove('cx')\n")
    assert "PY-UNSAFE-CALL" not in _ids("s.py", text)


def test_cirq_simulator_run_is_not_unsafe():
    text = ("import cirq\nqs = cirq.LineQubit.range(2)\n"
            "c = cirq.Circuit([cirq.H(qs[0]), cirq.measure(*qs, key='m')])\n"
            "sim = cirq.Simulator()\nresult = sim.run(c)\n")
    r = verify_text("s.py", text)
    assert not r.unsafe


# --- safety screen: real threats must still be flagged ---

def test_subprocess_run_still_flagged():
    r = verify_text("s.py", "import subprocess\nsubprocess.run(['ls'])\n")
    assert r.unsafe
    assert "PY-UNSAFE-CALL" in {f.id for f in r.findings}


def test_aliased_subprocess_run_still_flagged():
    r = verify_text("s.py", "import subprocess as sp\nsp.run(['ls'])\n")
    assert r.unsafe
    assert "PY-UNSAFE-CALL" in {f.id for f in r.findings}


def test_from_import_run_still_flagged():
    r = verify_text("s.py", "from subprocess import run\nrun(['ls'])\n")
    assert r.unsafe
    assert "PY-UNSAFE-CALL" in {f.id for f in r.findings}


def test_from_import_aliased_still_flagged():
    r = verify_text("s.py", "from os import system as sh\nsh('ls')\n")
    assert r.unsafe
    assert "PY-UNSAFE-CALL" in {f.id for f in r.findings}


def test_eval_still_flagged():
    r = verify_text("s.py", "eval('2+2')\n")
    assert "PY-UNSAFE-CALL" in {f.id for f in r.findings}


def test_open_still_flagged():
    r = verify_text("s.py", "data = open('x.txt').read()\n")
    assert "PY-UNSAFE-CALL" in {f.id for f in r.findings}


def test_unsafe_import_alone_still_marks_unsafe():
    # The import itself is the closed gate: even with no flagged call, an
    # unsafe module import marks the snippet unsafe.
    r = verify_text("s.py", "import os\nx = 1\n")
    assert r.unsafe
    assert "PY-UNSAFE-IMPORT" in {f.id for f in r.findings}
