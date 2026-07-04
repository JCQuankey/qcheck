"""Tests for the public agent-consumption example scripts."""
import importlib.util
import pathlib

from qcheck.cli import verify_text
from qcheck import rules as rule_catalog

EXAMPLES = pathlib.Path(__file__).resolve().parent.parent / "examples"


def _load(name):
    spec = importlib.util.spec_from_file_location(name[:-3], EXAMPLES / name)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def test_consume_json_summarize_flags_blocking():
    cj = _load("consume_json.py")
    rep = verify_text(
        "s.py",
        "from qiskit import QuantumCircuit, execute\nqc = QuantumCircuit(2, 2)\n",
    ).to_dict()
    text, blocking = cj.summarize(rep)
    assert "QISKIT-REMOVED-IMPORT" in text
    assert blocking is True


def test_consume_json_summarize_clean_is_not_blocking():
    cj = _load("consume_json.py")
    rep = verify_text(
        "s.qasm",
        'OPENQASM 2.0;\ninclude "qelib1.inc";\nqreg q[1];\ncreg c[1];\n'
        "h q[0];\nmeasure q -> c;\n",
    ).to_dict()
    _text, blocking = cj.summarize(rep)
    assert blocking is False


def test_consume_rules_index_has_guidance():
    cr = _load("consume_rules_json.py")
    catalog = {"rules": [r.to_dict() for r in rule_catalog.catalog()]}
    index = cr.build_index(catalog)
    assert "QISKIT-EXECUTE" in index
    assert index["QISKIT-EXECUTE"]["recommended_action"]
    assert len(index) == len(rule_catalog.catalog())
