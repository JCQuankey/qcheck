"""Contract tests: protect the public JSON / rules / SARIF / exit-code shapes
that agents and CI depend on (see docs/CONTRACTS.md). These assert stable field
presence, not exact values, so they guard compatibility without freezing detail.
"""
import json

from conftest import FIXTURES
from qcheck.cli import main, EXIT_PASS, EXIT_FAIL, EXIT_UNSAFE
from qcheck import rules as rc


def _json(capsys, argv):
    main(argv)
    return json.loads(capsys.readouterr().out)


# --- exit codes ---

def test_exit_codes_contract():
    assert main(["verify", str(FIXTURES / "valid_bell.qasm")]) == EXIT_PASS
    assert main(["verify", str(FIXTURES / "qiskit_invalid_api.py")]) == EXIT_FAIL
    assert main(["verify", str(FIXTURES / "malicious.py")]) == EXIT_UNSAFE
    assert main(["verify", "/no/such/file.qasm"]) == 3


# --- single-file JSON ---

def test_single_file_json_top_level_fields(capsys):
    d = _json(capsys, ["verify", str(FIXTURES / "qiskit_invalid_api.py"), "--json"])
    for field in ("qcheck_version", "status", "framework", "syntax_valid",
                  "unsafe", "static_checks", "errors", "warnings",
                  "suggested_fixes", "confidence", "runnable_in_simulator"):
        assert field in d, f"missing top-level contract field {field}"
    assert "results" not in d          # single file stays a bare object
    assert d["status"] in ("pass", "warning", "fail")


def test_finding_fields_contract(capsys):
    d = _json(capsys, ["verify", str(FIXTURES / "qiskit_invalid_api.py"), "--json"])
    assert d["static_checks"], "expected at least one finding"
    f = d["static_checks"][0]
    for field in ("id", "level", "message", "line"):
        assert field in f, f"finding missing contract field {field}"
    assert f["level"] in ("error", "warning", "info")


# --- multi-file envelope ---

def test_multifile_envelope_contract(capsys):
    d = _json(capsys, ["verify", str(FIXTURES / "valid_bell.qasm"),
                       str(FIXTURES / "malicious.py"), "--json"])
    assert set(("qcheck_version", "results", "summary")) <= set(d)
    for field in ("files", "passed", "failed", "unsafe", "read_errors"):
        assert field in d["summary"]
    assert all("path" in r for r in d["results"])


# --- rules catalog ---

def test_rules_json_contract(capsys):
    d = _json(capsys, ["rules", "--json"])
    assert "qcheck_version" in d and isinstance(d["rules"], list)
    assert len(d["rules"]) >= 30
    ids = [r["id"] for r in d["rules"]]
    assert ids == sorted(ids)          # deterministic order
    required = ("id", "title", "category", "default_level", "applies_to",
                "summary", "why_it_matters", "recommended_action")
    for r in d["rules"]:
        for field in required:
            assert r.get(field), f"rule {r.get('id')} missing {field}"


# --- SARIF ---

def test_sarif_contract(capsys):
    d = _json(capsys, ["verify", str(FIXTURES / "qiskit_invalid_api.py"), "--format", "sarif"])
    assert d["version"] == "2.1.0"
    run = d["runs"][0]
    assert run["tool"]["driver"]["name"] == "qcheck"
    assert isinstance(run["tool"]["driver"]["rules"], list)
    assert run["results"] and "ruleId" in run["results"][0]
    assert "executionSuccessful" in run["invocations"][0]


def test_sarif_enriched_metadata_for_pack2_rule(capsys):
    # A Pack 2 rule (no classical bits) should carry enriched catalog metadata.
    import io
    # write via fixture-independent snippet through stdin
    import qcheck.cli as cli
    from qcheck.report import Report, Finding
    from qcheck.sarif import build_sarif
    rep = Report(framework="qiskit", syntax_valid=True,
                 findings=[Finding("QISKIT-MEASURE-NO-CLBITS", "error", "x", 3)])
    doc = build_sarif([("s.py", rep)])
    rule = doc["runs"][0]["tool"]["driver"]["rules"][0]
    assert rule["id"] == "QISKIT-MEASURE-NO-CLBITS"
    assert rule["shortDescription"]["text"]
    assert rule["defaultConfiguration"]["level"] == "error"
    assert "help" in rule
    assert rc.known("QISKIT-MEASURE-NO-CLBITS")
