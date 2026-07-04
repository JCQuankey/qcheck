"""PennyLane static-review MVP: positive + negative tests, routing, safety."""
from qcheck.cli import verify_text
from qcheck.detect import detect_framework


def _report(name, text):
    return verify_text(name, text)


def _ids(name, text):
    return {f.id for f in _report(name, text).findings}


CLEAN = ("import pennylane as qml\n"
         "dev = qml.device('default.qubit', wires=2)\n"
         "@qml.qnode(dev)\ndef circ():\n"
         "    qml.Hadamard(wires=0)\n    qml.CNOT(wires=[0, 1])\n"
         "    return qml.expval(qml.PauliZ(0))\n")


# --- routing ---

def test_detects_pennylane_framework():
    assert detect_framework("s.py", "import pennylane as qml\n") == "pennylane"
    assert detect_framework("s.py", "dev = qml.device('x', wires=2)\n") == "pennylane"


def test_qiskit_not_routed_to_pennylane():
    text = "from qiskit import QuantumCircuit, execute\nqc = QuantumCircuit(2, 2)\n"
    r = _report("s.py", text)
    assert r.framework == "qiskit"
    assert not any(f.id.startswith("PENNYLANE-") for f in r.findings)


def test_generic_python_not_pennylane():
    assert detect_framework("s.py", "def add(a, b):\n    return a + b\n") == "python_unknown"


# --- clean baseline ---

def test_clean_pennylane_has_no_findings():
    assert not _report("s.py", CLEAN).findings


# --- PENNYLANE-QML-MISSING-IMPORT ---

def test_missing_import_fires():
    text = ("dev = qml.device('default.qubit', wires=2)\n"
            "@qml.qnode(dev)\ndef circ():\n    return qml.expval(qml.PauliZ(0))\n")
    assert "PENNYLANE-QML-MISSING-IMPORT" in _ids("s.py", text)


def test_imported_qml_does_not_fire_missing_import():
    assert "PENNYLANE-QML-MISSING-IMPORT" not in _ids("s.py", CLEAN)


# --- PENNYLANE-DEVICE-ZERO-WIRES / NEGATIVE-WIRES ---

def test_device_zero_wires_fires():
    text = "import pennylane as qml\ndev = qml.device('default.qubit', wires=0)\n"
    assert "PENNYLANE-DEVICE-ZERO-WIRES" in _ids("s.py", text)


def test_device_negative_wires_fires():
    text = "import pennylane as qml\ndev = qml.device('default.qubit', wires=-1)\n"
    assert "PENNYLANE-DEVICE-NEGATIVE-WIRES" in _ids("s.py", text)


def test_device_positive_wires_clean():
    text = "import pennylane as qml\ndev = qml.device('default.qubit', wires=4)\n"
    ids = _ids("s.py", text)
    assert "PENNYLANE-DEVICE-ZERO-WIRES" not in ids
    assert "PENNYLANE-DEVICE-NEGATIVE-WIRES" not in ids


def test_device_positional_wires_zero_fires():
    text = "import pennylane as qml\ndev = qml.device('default.qubit', 0)\n"
    assert "PENNYLANE-DEVICE-ZERO-WIRES" in _ids("s.py", text)


# --- PENNYLANE-QNODE-NO-RETURN ---

def test_qnode_no_return_fires():
    text = ("import pennylane as qml\ndev = qml.device('default.qubit', wires=2)\n"
            "@qml.qnode(dev)\ndef circ():\n    qml.Hadamard(wires=0)\n")
    assert "PENNYLANE-QNODE-NO-RETURN" in _ids("s.py", text)


def test_qnode_with_return_clean():
    assert "PENNYLANE-QNODE-NO-RETURN" not in _ids("s.py", CLEAN)


def test_plain_function_no_return_not_flagged():
    # A non-qnode function without a return must NOT trigger the qnode rule.
    text = ("import pennylane as qml\ndev = qml.device('default.qubit', wires=2)\n"
            "def helper():\n    qml.Hadamard(wires=0)\n")
    assert "PENNYLANE-QNODE-NO-RETURN" not in _ids("s.py", text)


# --- safety still applies to PennyLane files ---

def test_unsafe_pennylane_is_unsafe():
    text = "import pennylane as qml\nimport os\nos.system('x')\n"
    r = _report("s.py", text)
    assert r.unsafe is True
