"""Public synthetic snippet suite.

Handcrafted, public snippets modelling common AI-generated Qiskit/OpenQASM
mistakes (and clean baselines). Each case asserts the expected exit code and
that the expected rule IDs fire, and that clean snippets stay clean. No private
benchmark data, prompts, or model outputs are used.
"""
import pytest

from qcheck.cli import verify_text, _exit_code

EXIT_PASS, EXIT_FAIL, EXIT_UNSAFE = 0, 1, 2

# (id, filename, source, expected_exit, must_include_rule_ids)
CASES = [
    # --- clean baselines: must stay quiet ---
    ("clean_qiskit_bell", "bell.py",
     "from qiskit import QuantumCircuit\n"
     "qc = QuantumCircuit(2, 2)\nqc.h(0)\nqc.cx(0, 1)\nqc.measure([0, 1], [0, 1])\n",
     EXIT_PASS, set()),
    ("clean_qasm_bell", "bell.qasm",
     'OPENQASM 2.0;\ninclude "qelib1.inc";\nqreg q[2];\ncreg c[2];\n'
     "h q[0];\ncx q[0],q[1];\nmeasure q -> c;\n",
     EXIT_PASS, set()),

    # --- Qiskit API compatibility ---
    ("qiskit_execute", "execute.py",
     "from qiskit import QuantumCircuit, execute\nqc = QuantumCircuit(2, 2)\n",
     EXIT_FAIL, {"QISKIT-REMOVED-IMPORT"}),
    ("qiskit_assemble", "assemble.py",
     "from qiskit import QuantumCircuit, assemble\n"
     "qc = QuantumCircuit(1, 1)\nqc.measure_all()\nqobj = assemble(qc)\n",
     EXIT_FAIL, {"QISKIT-ASSEMBLE-REMOVED"}),
    ("qiskit_removed_module", "aqua.py",
     "from qiskit.aqua import QuantumInstance\n",
     EXIT_FAIL, {"QISKIT-REMOVED-MODULE"}),

    # --- Qiskit structure ---
    ("qiskit_missing_import", "noimp.py",
     "qc = QuantumCircuit(2, 2)\nqc.h(0)\nqc.measure_all()\n",
     EXIT_FAIL, {"QISKIT-MISSING-IMPORT"}),
    ("qiskit_index_range", "range.py",
     "from qiskit import QuantumCircuit\nqc = QuantumCircuit(2, 2)\n"
     "qc.h(5)\nqc.measure_all()\n",
     EXIT_FAIL, {"QISKIT-QUBIT-INDEX-RANGE"}),
    ("qiskit_measure_no_clbits", "noclb.py",
     "from qiskit import QuantumCircuit\nqc = QuantumCircuit(2)\nqc.measure(0, 0)\n",
     EXIT_FAIL, {"QISKIT-MEASURE-NO-CLBITS"}),
    ("qiskit_zero_qubits", "zero.py",
     "from qiskit import QuantumCircuit\nqc = QuantumCircuit(0)\n",
     EXIT_FAIL, {"QISKIT-ZERO-QUBITS"}),

    # --- Python safety ---
    ("unsafe_os", "unsafe.py",
     "import os\nos.system('rm -rf /tmp/x')\n",
     EXIT_UNSAFE, {"PY-UNSAFE-IMPORT"}),

    # --- OpenQASM ---
    ("qasm_no_header", "nohdr.qasm",
     'include "qelib1.inc";\nqreg q[1];\ncreg c[1];\nmeasure q -> c;\n',
     EXIT_FAIL, {"QASM-NO-HEADER"}),
    ("qasm_undeclared", "undecl.qasm",
     'OPENQASM 2.0;\ninclude "qelib1.inc";\ncreg c[2];\nh q[0];\nmeasure q -> c;\n',
     EXIT_FAIL, {"QASM-UNDECLARED-REG"}),
    ("qasm_dup_register", "dupreg.qasm",
     'OPENQASM 2.0;\ninclude "qelib1.inc";\nqreg q[2];\nqreg q[3];\n'
     "creg c[2];\nmeasure q -> c;\n",
     EXIT_FAIL, {"QASM-DUP-REGISTER"}),
    ("qasm_classical_as_qubit", "casq.qasm",
     'OPENQASM 2.0;\ninclude "qelib1.inc";\nqreg q[2];\ncreg c[2];\n'
     "h c[0];\nmeasure q -> c;\n",
     EXIT_FAIL, {"QASM-CLASSICAL-AS-QUBIT"}),
    ("qasm_measure_size_mismatch", "sizemm.qasm",
     'OPENQASM 2.0;\ninclude "qelib1.inc";\nqreg q[3];\ncreg c[2];\n'
     "h q[0];\nmeasure q -> c;\n",
     EXIT_PASS, {"QASM-MEASURE-SIZE-MISMATCH"}),  # warning only -> exit 0

    # --- more clean baselines ---
    ("clean_qiskit_measure_all", "measall.py",
     "from qiskit import QuantumCircuit\nqc = QuantumCircuit(2, 2)\n"
     "qc.h(0)\nqc.cx(0, 1)\nqc.measure_all()\n",
     EXIT_PASS, set()),
    ("clean_qiskit_registers", "regs.py",
     "from qiskit import QuantumCircuit, QuantumRegister, ClassicalRegister\n"
     "qr = QuantumRegister(2)\ncr = ClassicalRegister(2)\n"
     "qc = QuantumCircuit(qr, cr)\nqc.h(0)\nqc.measure(qr, cr)\n",
     EXIT_PASS, set()),
    ("clean_qasm3_bell", "bell3.qasm",
     'OPENQASM 3.0;\ninclude "stdgates.inc";\nqubit[2] q;\nbit[2] c;\n'
     "h q[0];\ncx q[0], q[1];\nc = measure q;\n",
     EXIT_PASS, set()),

    # --- Qiskit: pack 3 & 4 & coverage ---
    ("qiskit_get_counts_no_measure", "gc.py",
     "from qiskit import QuantumCircuit\nqc = QuantumCircuit(2, 2)\nqc.h(0)\n"
     "counts = result.get_counts(qc)\n",
     EXIT_PASS, {"QISKIT-GET-COUNTS-NO-MEASURE"}),  # warnings only
    ("qiskit_removed_provider_path", "prov.py",
     "from qiskit.providers.aer import AerSimulator\n",
     EXIT_PASS, {"QISKIT-DEPRECATED-PROVIDER-PATH"}),  # warning only
    ("qiskit_transpile_missing_import", "trans.py",
     "from qiskit import QuantumCircuit\nqc = QuantumCircuit(2, 2)\n"
     "qc.measure_all()\nt = transpile(qc)\n",
     EXIT_FAIL, {"QISKIT-TRANSPILE-MISSING-IMPORT"}),
    ("qiskit_negative_qubits", "neg.py",
     "from qiskit import QuantumCircuit\nqc = QuantumCircuit(-1)\n",
     EXIT_FAIL, {"QISKIT-NEGATIVE-QUBITS"}),
    ("qiskit_zero_sized_register", "zreg.py",
     "from qiskit import QuantumCircuit, QuantumRegister\n"
     "qr = QuantumRegister(0)\nqc = QuantumCircuit(qr)\n",
     EXIT_FAIL, {"QISKIT-ZERO-SIZED-REGISTER"}),
    ("qiskit_bind_parameters", "bind.py",
     "from qiskit import QuantumCircuit\nqc = QuantumCircuit(1, 1)\n"
     "qc.measure_all()\nqc2 = qc.bind_parameters({})\n",
     EXIT_PASS, {"QISKIT-BIND-PARAMETERS-DEPRECATED"}),  # warning only
    ("qiskit_parameter_missing_import", "param.py",
     "from qiskit import QuantumCircuit\nqc = QuantumCircuit(1, 1)\n"
     "qc.rx(Parameter('t'), 0)\nqc.measure_all()\n",
     EXIT_FAIL, {"QISKIT-PARAMETER-MISSING-IMPORT"}),
    ("qiskit_tools_removed", "tools.py",
     "from qiskit.tools import job_monitor\n",
     EXIT_FAIL, {"QISKIT-REMOVED-MODULE"}),

    # --- OpenQASM: pack 3 & 4 & coverage ---
    ("qasm_version_mismatch", "vmix.qasm",
     'OPENQASM 2.0;\ninclude "qelib1.inc";\nqubit[2] q;\nbit[2] c;\n',
     EXIT_PASS, {"QASM-VERSION-MISMATCH"}),  # warning only
    ("qasm_no_measure", "nomeas.qasm",
     'OPENQASM 2.0;\ninclude "qelib1.inc";\nqreg q[2];\ncreg c[2];\n'
     "h q[0];\ncx q[0],q[1];\n",
     EXIT_PASS, {"QASM-NO-MEASURE"}),  # warning only
    ("qasm_zero_register", "zeroreg.qasm",
     'OPENQASM 2.0;\ninclude "qelib1.inc";\nqreg q[0];\ncreg c[2];\n'
     "measure q -> c;\n",
     EXIT_FAIL, {"QASM-ZERO-REGISTER"}),
    ("qasm_duplicate_include", "dupinc.qasm",
     'OPENQASM 2.0;\ninclude "qelib1.inc";\ninclude "qelib1.inc";\n'
     "qreg q[2];\ncreg c[2];\nmeasure q -> c;\n",
     EXIT_PASS, {"QASM-DUPLICATE-INCLUDE"}),  # warning only
    ("qasm_bare_measure_undeclared_target", "baretgt.qasm",
     'OPENQASM 2.0;\ninclude "qelib1.inc";\nqreg q[2];\nh q[0];\nmeasure q -> c;\n',
     EXIT_FAIL, {"QASM-MEASURE-TGT"}),
    ("qasm_index_range", "idx.qasm",
     'OPENQASM 2.0;\ninclude "qelib1.inc";\nqreg q[2];\ncreg c[2];\n'
     "h q[5];\nmeasure q -> c;\n",
     EXIT_FAIL, {"QASM-INDEX-RANGE"}),

    # --- PennyLane ---
    ("clean_pennylane", "pl_ok.py",
     "import pennylane as qml\ndev = qml.device('default.qubit', wires=2)\n"
     "@qml.qnode(dev)\ndef circ():\n    qml.Hadamard(wires=0)\n"
     "    qml.CNOT(wires=[0, 1])\n    return qml.expval(qml.PauliZ(0))\n",
     EXIT_PASS, set()),
    ("pennylane_missing_import", "pl_imp.py",
     "dev = qml.device('default.qubit', wires=2)\n"
     "@qml.qnode(dev)\ndef circ():\n    return qml.expval(qml.PauliZ(0))\n",
     EXIT_FAIL, {"PENNYLANE-QML-MISSING-IMPORT"}),
    ("pennylane_zero_wires", "pl_zw.py",
     "import pennylane as qml\ndev = qml.device('default.qubit', wires=0)\n",
     EXIT_FAIL, {"PENNYLANE-DEVICE-ZERO-WIRES"}),
    ("pennylane_negative_wires", "pl_nw.py",
     "import pennylane as qml\ndev = qml.device('default.qubit', wires=-2)\n",
     EXIT_FAIL, {"PENNYLANE-DEVICE-NEGATIVE-WIRES"}),
    ("pennylane_qnode_no_return", "pl_nr.py",
     "import pennylane as qml\ndev = qml.device('default.qubit', wires=2)\n"
     "@qml.qnode(dev)\ndef circ():\n    qml.Hadamard(wires=0)\n",
     EXIT_PASS, {"PENNYLANE-QNODE-NO-RETURN"}),  # warning only
]


@pytest.mark.parametrize("case", CASES, ids=[c[0] for c in CASES])
def test_snippet(case):
    _id, name, src, expected_exit, must_include = case
    report = verify_text(name, src)
    ids = {f.id for f in report.findings}
    assert _exit_code(report) == expected_exit, f"{_id}: exit mismatch, findings={ids}"
    missing = must_include - ids
    assert not missing, f"{_id}: expected rules not fired: {missing} (got {ids})"


def test_clean_snippets_have_no_findings():
    for _id, name, src, exp, must in CASES:
        if _id.startswith("clean_"):
            assert not verify_text(name, src).findings, f"{_id} should be clean"
