import json

from conftest import FIXTURES
from qcheck.cli import main, EXIT_PASS, EXIT_FAIL, EXIT_UNSAFE
from qcheck.sarif import build_sarif
from qcheck.report import Report, Finding


def _sarif(capsys, argv):
    rc = main(argv)
    return rc, json.loads(capsys.readouterr().out)


def test_sarif_is_valid_json_version_and_single_run(capsys):
    _, d = _sarif(capsys, ["verify", str(FIXTURES / "valid_bell.qasm"), "--format", "sarif"])
    assert d["version"] == "2.1.0"
    assert isinstance(d["runs"], list) and len(d["runs"]) == 1


def test_sarif_driver_metadata(capsys):
    _, d = _sarif(capsys, ["verify", str(FIXTURES / "valid_bell.qasm"), "--format", "sarif"])
    drv = d["runs"][0]["tool"]["driver"]
    assert drv["name"] == "qcheck"
    assert drv["version"] and isinstance(drv["version"], str)
    assert drv["informationUri"].startswith("https://")
    assert d["runs"][0]["invocations"][0]["executionSuccessful"] is True


def test_sarif_clean_file_zero_results_exit_pass(capsys):
    rc, d = _sarif(capsys, ["verify", str(FIXTURES / "valid_bell.qasm"), "--format", "sarif"])
    assert rc == EXIT_PASS
    assert d["runs"][0]["results"] == []


def test_sarif_failing_file_has_results_and_fail_exit(capsys):
    rc, d = _sarif(capsys, ["verify", str(FIXTURES / "qiskit_invalid_api.py"), "--format", "sarif"])
    results = d["runs"][0]["results"]
    assert rc in (EXIT_FAIL, EXIT_UNSAFE)
    assert len(results) >= 1
    r = results[0]
    assert r["ruleId"]
    assert r["level"] in ("error", "warning", "note")
    assert r["message"]["text"]
    assert r["locations"][0]["physicalLocation"]["artifactLocation"]["uri"]


def test_sarif_unsafe_file_exit_unsafe(capsys):
    rc, _d = _sarif(capsys, ["verify", str(FIXTURES / "malicious.py"), "--format", "sarif"])
    assert rc == EXIT_UNSAFE


def test_sarif_rules_are_deterministic_and_cover_results(capsys):
    _, d = _sarif(capsys, ["verify", str(FIXTURES), "--format", "sarif"])
    drv = d["runs"][0]["tool"]["driver"]
    rule_ids = [r["id"] for r in drv["rules"]]
    assert rule_ids == sorted(rule_ids)                 # deterministic order
    used = {r["ruleId"] for r in d["runs"][0]["results"]}
    assert used.issubset(set(rule_ids))                 # every result's rule is defined


def test_sarif_multifile_includes_multiple_files(capsys):
    _, d = _sarif(capsys, ["verify", str(FIXTURES), "--format", "sarif"])
    uris = {r["locations"][0]["physicalLocation"]["artifactLocation"]["uri"]
            for r in d["runs"][0]["results"]}
    assert len(uris) > 1


def test_sarif_directory_skips_vendor_dirs(tmp_path, capsys):
    (tmp_path / "bad.py").write_text("from qiskit import execute\n")
    venv = tmp_path / ".venv"
    venv.mkdir()
    (venv / "vendor.py").write_text("import os\nos.system('x')\n")
    _, d = _sarif(capsys, ["verify", str(tmp_path), "--format", "sarif"])
    uris = {r["locations"][0]["physicalLocation"]["artifactLocation"]["uri"]
            for r in d["runs"][0]["results"]}
    assert any("bad.py" in u for u in uris)
    assert not any("vendor.py" in u for u in uris)


def test_sarif_stdin_uses_synthetic_uri(monkeypatch, capsys):
    import io
    monkeypatch.setattr("sys.stdin", io.StringIO("from qiskit import execute\n"))
    _, d = _sarif(capsys, ["verify", "-", "--format", "sarif"])
    uris = {r["locations"][0]["physicalLocation"]["artifactLocation"]["uri"]
            for r in d["runs"][0]["results"]}
    assert uris == {"stdin"}


def test_sarif_deterministic_output(capsys):
    _, d1 = _sarif(capsys, ["verify", str(FIXTURES), "--format", "sarif"])
    _, d2 = _sarif(capsys, ["verify", str(FIXTURES), "--format", "sarif"])
    assert json.dumps(d1, sort_keys=True) == json.dumps(d2, sort_keys=True)


def test_sarif_output_to_file(tmp_path, capsys):
    out = tmp_path / "q.sarif"
    rc = main(["verify", str(FIXTURES / "qiskit_invalid_api.py"),
               "--format", "sarif", "--output", str(out)])
    assert rc in (EXIT_FAIL, EXIT_UNSAFE)
    assert capsys.readouterr().out == ""            # nothing to stdout
    d = json.loads(out.read_text())
    assert d["version"] == "2.1.0"


def test_build_sarif_level_mapping_and_line_optional():
    rep = Report(framework="qiskit", syntax_valid=True, findings=[
        Finding("R-INFO", "info", "an info note", None),
        Finding("R-WARN", "warning", "a warning", 5),
        Finding("R-ERR", "error", "an error", 2),
    ])
    d = build_sarif([("x.py", rep)])
    by_id = {r["ruleId"]: r for r in d["runs"][0]["results"]}
    assert by_id["R-INFO"]["level"] == "note"          # info -> note
    assert by_id["R-WARN"]["level"] == "warning"
    assert by_id["R-ERR"]["level"] == "error"
    # line-less finding omits region
    assert "region" not in by_id["R-INFO"]["locations"][0]["physicalLocation"]
    assert by_id["R-WARN"]["locations"][0]["physicalLocation"]["region"]["startLine"] == 5
