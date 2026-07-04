import json
from pathlib import Path

from conftest import FIXTURES
from qcheck.cli import main, EXIT_PASS, EXIT_FAIL, EXIT_UNSAFE


def test_valid_qasm_exit_pass():
    assert main(["verify", str(FIXTURES / "valid_bell.qasm")]) == EXIT_PASS


def test_invalid_qasm_exit_fail():
    assert main(["verify", str(FIXTURES / "invalid_missing_register.qasm")]) == EXIT_FAIL


def test_malicious_exit_unsafe():
    assert main(["verify", str(FIXTURES / "malicious.py")]) == EXIT_UNSAFE


def test_valid_qiskit_exit_pass():
    assert main(["verify", str(FIXTURES / "valid_bell_qiskit.py")]) == EXIT_PASS


def test_no_command_prints_help_returns_internal():
    # no subcommand -> usage + internal code (3)
    assert main([]) == 3


def test_unreadable_file_returns_internal():
    assert main(["verify", "/nonexistent/path/to/file.qasm"]) == 3


def test_json_flag_emits_valid_json(capsys):
    rc = main(["verify", str(FIXTURES / "valid_bell.qasm"), "--json"])
    out = capsys.readouterr().out
    data = json.loads(out)
    assert rc == EXIT_PASS
    assert data["status"] == "pass"
    assert "results" not in data  # single file -> bare object (backward compatible)
    for key in ("qcheck_version", "status", "framework", "syntax_valid",
                "unsafe", "runnable_in_simulator", "static_checks", "errors",
                "warnings", "suggested_fixes", "confidence"):
        assert key in data


def test_directory_scans_recursively_worst_case_exit():
    # FIXTURES contains malicious.py (unsafe) -> worst-case exit is UNSAFE.
    assert main(["verify", str(FIXTURES)]) == EXIT_UNSAFE


def test_multiple_files_worst_case_exit():
    rc = main(["verify", str(FIXTURES / "valid_bell.qasm"),
               str(FIXTURES / "malicious.py")])
    assert rc == EXIT_UNSAFE


def test_multiple_files_fail_when_no_unsafe():
    rc = main(["verify", str(FIXTURES / "valid_bell.qasm"),
               str(FIXTURES / "invalid_missing_register.qasm")])
    assert rc == EXIT_FAIL


def test_aggregate_json_envelope(capsys):
    rc = main(["verify", str(FIXTURES), "--json"])
    data = json.loads(capsys.readouterr().out)
    assert rc == EXIT_UNSAFE
    assert isinstance(data["results"], list) and len(data["results"]) > 1
    assert data["summary"]["files"] == len(data["results"])
    assert data["summary"]["unsafe"] >= 1
    assert all("path" in r for r in data["results"])


def test_empty_dir_returns_pass(tmp_path):
    assert main(["verify", str(tmp_path)]) == EXIT_PASS


def test_stdin_reads_and_reviews(monkeypatch):
    import io
    monkeypatch.setattr("sys.stdin",
                        io.StringIO("from qiskit import QuantumCircuit, execute\n"))
    assert main(["verify", "-"]) == EXIT_FAIL


def test_stdin_unsafe(monkeypatch):
    import io
    monkeypatch.setattr("sys.stdin", io.StringIO("import os\nos.system('x')\n"))
    assert main(["verify", "-", "--lang", "python"]) == EXIT_UNSAFE


def test_recursion_skips_vendor_and_hidden_dirs(tmp_path, capsys):
    # Two real files the user owns (so the aggregate envelope path is exercised)...
    (tmp_path / "circuit.py").write_text(
        "from qiskit import QuantumCircuit\n"
        "qc = QuantumCircuit(1, 1)\nqc.measure(0, 0)\n")
    (tmp_path / "bell.qasm").write_text(
        'OPENQASM 2.0;\ninclude "qelib1.inc";\nqreg q[1];\ncreg c[1];\n'
        "h q[0];\nmeasure q -> c;\n")
    # ...and third-party/build/hidden dirs that must NOT be reviewed.
    for d in (".venv/lib/site-packages", "node_modules", ".git"):
        sub = tmp_path / d
        sub.mkdir(parents=True)
        (sub / "vendor.py").write_text("import os\nos.system('rm -rf /')\n")
    rc = main(["verify", str(tmp_path), "--json"])
    data = json.loads(capsys.readouterr().out)
    reviewed = {r["path"] for r in data["results"]}
    assert rc == EXIT_PASS                     # only the clean user file was seen
    assert any("circuit.py" in p for p in reviewed)
    assert not any("vendor.py" in p for p in reviewed)


def test_explicit_file_inside_vendor_dir_still_reviewed(tmp_path):
    # Pruning applies to *recursion*, not to an explicitly named path.
    sub = tmp_path / ".venv"
    sub.mkdir()
    f = sub / "thing.py"
    f.write_text("import os\nos.system('x')\n")
    assert main(["verify", str(f)]) == EXIT_UNSAFE
