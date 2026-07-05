"""Tests for tools/corpus_smoke.py using tiny local fixture directories."""
import json
import os
import sys

import pytest

TOOLS = os.path.join(os.path.dirname(__file__), "..", "tools")
sys.path.insert(0, TOOLS)

import corpus_smoke  # noqa: E402


@pytest.fixture()
def corpus(tmp_path):
    (tmp_path / "clean.qasm").write_text(
        'OPENQASM 2.0;\ninclude "qelib1.inc";\nqreg q[2];\ncreg c[2];\n'
        "h q[0];\ncx q[0],q[1];\nmeasure q -> c;\n")
    (tmp_path / "broken.py").write_text(
        "from qiskit import QuantumCircuit, execute\n"
        "qc = QuantumCircuit(2, 2)\nqc.measure_all()\n"
        "r = execute(qc, backend)\n")
    (tmp_path / "helper.py").write_text("def add(a, b):\n    return a + b\n")
    sub = tmp_path / ".venv"          # must be pruned
    sub.mkdir()
    (sub / "vendored.py").write_text("import os\nos.system('x')\n")
    return tmp_path


def test_collect_files_prunes_vendor_dirs(corpus):
    files = corpus_smoke.collect_files([str(corpus)])
    names = {os.path.basename(f) for f in files}
    assert names == {"clean.qasm", "broken.py", "helper.py"}


def test_run_aggregates_by_rule(corpus):
    s = corpus_smoke.run([str(corpus)])
    assert s["files_reviewed"] == 3
    assert s["by_rule"].get("QISKIT-REMOVED-IMPORT") == 1
    assert s["by_rule"].get("QISKIT-EXECUTE") == 1
    assert s["by_rule"].get("UNSUPPORTED") == 1          # helper.py
    # No QASM rules may fire: the only .qasm file is clean and .py files
    # never route to the QASM parser (router regression, PR #44).
    assert not any(k.startswith("QASM-") for k in s["by_rule"])
    assert s["by_level"]["error"] >= 3
    assert "note" in s


def test_run_respects_disable(corpus):
    s = corpus_smoke.run([str(corpus)], disabled=frozenset({"UNSUPPORTED"}))
    assert "UNSUPPORTED" not in s["by_rule"]


def test_main_report_only_exits_zero(corpus, capsys):
    rc = corpus_smoke.main([str(corpus)])
    out = json.loads(capsys.readouterr().out)
    assert rc == 0
    assert out["files_reviewed"] == 3


def test_expect_clean_fails_on_errors(corpus, capsys):
    rc = corpus_smoke.main([str(corpus), "--expect-clean"])
    assert rc == 1
    assert "error-level" in capsys.readouterr().err


def test_expect_clean_passes_on_clean_corpus(tmp_path, capsys):
    (tmp_path / "ok.qasm").write_text(
        'OPENQASM 2.0;\ninclude "qelib1.inc";\nqreg q[1];\ncreg c[1];\n'
        "measure q -> c;\n")
    rc = corpus_smoke.main([str(tmp_path), "--expect-clean"])
    assert rc == 0


def test_json_and_markdown_outputs(corpus, tmp_path):
    j = tmp_path / "out.json"
    m = tmp_path / "out.md"
    rc = corpus_smoke.main([str(corpus), "--json", str(j),
                            "--markdown", str(m)])
    assert rc == 0
    data = json.loads(j.read_text())
    assert data["findings_total"] >= 3
    md = m.read_text()
    assert "| QISKIT-EXECUTE |" in md and "corpus smoke report" in md


def test_max_files_cap(corpus, capsys):
    s = corpus_smoke.run([str(corpus)], max_files=1)
    assert s["files_reviewed"] == 1
