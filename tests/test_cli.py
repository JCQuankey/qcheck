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
    for key in ("qcheck_version", "status", "framework", "syntax_valid",
                "unsafe", "runnable_in_simulator", "static_checks", "errors",
                "warnings", "suggested_fixes", "confidence"):
        assert key in data
