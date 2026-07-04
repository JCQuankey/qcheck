"""Cirq static-review MVP: positive + negative tests, routing, safety."""
from qcheck.cli import verify_text
from qcheck.detect import detect_framework


def _report(name, text):
    return verify_text(name, text)


def _ids(name, text):
    return {f.id for f in _report(name, text).findings}


# Clean fixtures stop at circuit construction (repo convention): execution
# calls like sim.run(...) trip the generic .run() safety screen on every
# Python surface, Qiskit included.
CLEAN = ("import cirq\n"
         "qubits = cirq.LineQubit.range(2)\n"
         "circuit = cirq.Circuit()\n"
         "circuit.append(cirq.H(qubits[0]))\n"
         "circuit.append(cirq.CNOT(qubits[0], qubits[1]))\n"
         "circuit.append(cirq.measure(*qubits, key='m'))\n")


# --- routing ---

def test_detects_cirq_framework_by_import():
    assert detect_framework("s.py", "import cirq\n") == "cirq"
    assert detect_framework("s.py", "from cirq import Circuit\n") == "cirq"


def test_detects_cirq_framework_by_usage():
    assert detect_framework("s.py", "q = cirq.LineQubit.range(2)\n") == "cirq"


def test_import_evidence_beats_mention():
    # A Qiskit file whose docstring mentions Cirq stays on the Qiskit surface.
    text = ('"""Ported from Cirq."""\n'
            "from qiskit import QuantumCircuit\n"
            "qc = QuantumCircuit(2, 2)\n")
    assert detect_framework("s.py", text) == "qiskit"


def test_dual_import_routes_to_qiskit():
    # Interop files importing both keep the larger Qiskit rule set.
    text = "import qiskit\nimport cirq\n"
    assert detect_framework("s.py", text) == "qiskit"


def test_pennylane_cirq_plugin_routes_to_pennylane():
    text = ("import pennylane as qml\n"
            "dev = qml.device('cirq.simulator', wires=2)\n")
    assert detect_framework("s.py", text) == "pennylane"


def test_qiskit_not_routed_to_cirq():
    text = "from qiskit import QuantumCircuit\nqc = QuantumCircuit(2, 2)\n"
    r = _report("s.py", text)
    assert r.framework == "qiskit"
    assert not any(f.id.startswith("CIRQ-") for f in r.findings)


def test_generic_python_not_cirq():
    assert detect_framework("s.py", "def add(a, b):\n    return a + b\n") == "python_unknown"


# --- clean baseline ---

def test_clean_cirq_has_no_findings():
    r = _report("s.py", CLEAN)
    assert r.framework == "cirq"
    assert not r.findings


# --- CIRQ-MISSING-IMPORT ---

def test_missing_import_fires():
    text = ("qubits = cirq.LineQubit.range(2)\n"
            "circuit = cirq.Circuit()\n")
    assert "CIRQ-MISSING-IMPORT" in _ids("s.py", text)


def test_imported_cirq_does_not_fire():
    assert "CIRQ-MISSING-IMPORT" not in _ids("s.py", CLEAN)


def test_aliased_import_does_not_fire():
    # `import cirq as cq` binds cq; bare `cirq.` is never used.
    text = "import cirq as cq\nqs = cq.LineQubit.range(2)\n"
    assert "CIRQ-MISSING-IMPORT" not in _ids("s.py", text)


def test_assigned_cirq_name_does_not_fire():
    # A module-level binding of the name `cirq` counts as bound.
    text = "cirq = get_backend()\nqs = cirq.LineQubit.range(2)\n"
    assert "CIRQ-MISSING-IMPORT" not in _ids("s.py", text)


def test_unknown_attribute_does_not_fire():
    # `cirq.something_unrelated` is not proof of Cirq usage.
    text = "x = cirq.custom_helper()\n"
    assert "CIRQ-MISSING-IMPORT" not in _ids("s.py", text)


# --- CIRQ-MEASURE-NO-QUBITS ---

def test_measure_no_qubits_fires():
    text = "import cirq\nm = cirq.measure()\n"
    ids = _ids("s.py", text)
    assert "CIRQ-MEASURE-NO-QUBITS" in ids


def test_measure_no_qubits_is_error():
    text = "import cirq\nm = cirq.measure()\n"
    r = _report("s.py", text)
    assert any(f.id == "CIRQ-MEASURE-NO-QUBITS" and f.level == "error"
               for f in r.findings)
    assert r.status == "fail"


def test_measure_with_starred_qubits_clean():
    assert "CIRQ-MEASURE-NO-QUBITS" not in _ids("s.py", CLEAN)


def test_measure_with_positional_qubit_clean():
    text = ("import cirq\nq = cirq.LineQubit.range(1)\n"
            "m = cirq.measure(q[0], key='m')\n")
    assert "CIRQ-MEASURE-NO-QUBITS" not in _ids("s.py", text)


def test_measure_keyword_only_fires():
    # cirq.measure(key='m') with no qubits still raises in Cirq.
    text = "import cirq\nm = cirq.measure(key='m')\n"
    assert "CIRQ-MEASURE-NO-QUBITS" in _ids("s.py", text)


# --- CIRQ-EMPTY-LINEQUBITS ---

def test_linequbit_range_zero_fires_warning():
    text = "import cirq\nqs = cirq.LineQubit.range(0)\n"
    r = _report("s.py", text)
    assert any(f.id == "CIRQ-EMPTY-LINEQUBITS" and f.level == "warning"
               for f in r.findings)
    # Legal Cirq: a warning must not fail the review.
    assert r.status == "warning"


def test_linequbit_range_negative_fires():
    text = "import cirq\nqs = cirq.LineQubit.range(-1)\n"
    assert "CIRQ-EMPTY-LINEQUBITS" in _ids("s.py", text)


def test_linequbit_range_positive_clean():
    text = "import cirq\nqs = cirq.LineQubit.range(3)\n"
    assert "CIRQ-EMPTY-LINEQUBITS" not in _ids("s.py", text)


def test_linequbit_range_variable_clean():
    text = "import cirq\nn = 0\nqs = cirq.LineQubit.range(n)\n"
    assert "CIRQ-EMPTY-LINEQUBITS" not in _ids("s.py", text)


def test_linequbit_range_start_stop_clean():
    # range(-2, 3) is idiomatic Cirq and yields 5 qubits.
    text = "import cirq\nqs = cirq.LineQubit.range(-2, 3)\n"
    assert "CIRQ-EMPTY-LINEQUBITS" not in _ids("s.py", text)


# --- CIRQ-SAME-QUBIT-2Q ---

def test_same_qubit_cnot_fires_warning():
    text = ("import cirq\nq0 = cirq.LineQubit(0)\n"
            "op = cirq.CNOT(q0, q0)\n")
    r = _report("s.py", text)
    assert any(f.id == "CIRQ-SAME-QUBIT-2Q" and f.level == "warning"
               for f in r.findings)


def test_same_qubit_subscript_fires():
    text = ("import cirq\nqs = cirq.LineQubit.range(2)\n"
            "op = cirq.CZ(qs[0], qs[0])\n")
    assert "CIRQ-SAME-QUBIT-2Q" in _ids("s.py", text)


def test_distinct_qubits_clean():
    assert "CIRQ-SAME-QUBIT-2Q" not in _ids("s.py", CLEAN)


def test_distinct_subscripts_clean():
    text = ("import cirq\nqs = cirq.LineQubit.range(2)\n"
            "op = cirq.CZ(qs[0], qs[1])\n")
    assert "CIRQ-SAME-QUBIT-2Q" not in _ids("s.py", text)


def test_unprovable_operands_clean():
    # Different names may still be the same qubit; qcheck stays silent.
    text = ("import cirq\na = cirq.LineQubit(0)\nb = a\n"
            "op = cirq.CNOT(a, b)\n")
    assert "CIRQ-SAME-QUBIT-2Q" not in _ids("s.py", text)


# --- safety + syntax on the cirq surface ---

def test_unsafe_cirq_file_flagged():
    text = "import cirq\nimport os\nos.system('ls')\n"
    r = _report("s.py", text)
    assert r.unsafe
    assert "PY-UNSAFE-CALL" in {f.id for f in r.findings} or \
           "PY-UNSAFE-IMPORT" in {f.id for f in r.findings}


def test_cirq_syntax_error_reported():
    text = "import cirq\ndef broken(:\n"
    r = _report("s.py", text)
    assert not r.syntax_valid
    assert "PY-SYNTAX" in {f.id for f in r.findings}


# --- cross-surface non-interference ---

def test_pennylane_rules_do_not_fire_on_cirq():
    r = _report("s.py", CLEAN)
    assert not any(f.id.startswith("PENNYLANE-") for f in r.findings)


def test_qiskit_rules_do_not_fire_on_cirq():
    r = _report("s.py", CLEAN)
    assert not any(f.id.startswith("QISKIT-") for f in r.findings)
