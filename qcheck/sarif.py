"""SARIF 2.1.0 formatter for qcheck results (GitHub Code Scanning compatible).

Pure formatter over Report objects — no execution, no new dependencies, and it
does not touch the human or --json output. SARIF reports static qcheck findings;
it does not assert quantum correctness. Output ordering is deterministic.
"""
from __future__ import annotations

from typing import List, Optional, Tuple

from . import __version__
from .report import Report

INFORMATION_URI = "https://github.com/JCQuankey/qcheck"
SCHEMA = "https://json.schemastore.org/sarif-2.1.0.json"

# qcheck level -> SARIF level. SARIF levels: none | note | warning | error.
_LEVEL = {"error": "error", "warning": "warning", "info": "note"}

# Stable, human-readable rule metadata. Unknown ids still get a rule entry
# (falling back to the id) so results always reference a defined rule.
_RULE_DESC = {
    "QASM-NO-HEADER": "OpenQASM header missing",
    "QASM-UNDECLARED-REG": "Use of an undeclared quantum/classical register",
    "QASM-INDEX-RANGE": "Register index out of declared range",
    "QASM-MEASURE-SRC": "Invalid measurement source operand",
    "QASM-MEASURE-TGT": "Invalid measurement target operand",
    "QASM-INCLUDE": "Unsupported or missing include",
    "QASM-NO-SEMICOLON": "Statement missing a terminating semicolon",
    "QASM-SUSPICIOUS": "Content does not look like valid OpenQASM",
    "QISKIT-MISSING-IMPORT": "QuantumCircuit used without importing it",
    "QISKIT-NO-CIRCUIT": "No QuantumCircuit construction detected",
    "QISKIT-NO-MEASURE": "Circuit has no measurement",
    "QISKIT-EXECUTE": "Use of execute(), removed in Qiskit 1.0",
    "QISKIT-REMOVED-IMPORT": "Import removed in Qiskit 1.0 (e.g. execute, Aer)",
    "QISKIT-DEPRECATED-GATE": "Deprecated gate alias",
    "PY-SYNTAX": "Python syntax error",
    "PY-UNSAFE-IMPORT": "Unsafe import (potential remote-code-execution vector)",
    "PY-UNSAFE-CALL": "Unsafe call (potential remote-code-execution vector)",
    "UNSUPPORTED": "Unsupported framework or file type",
}


def _sarif_uri(display: str) -> str:
    # stdin has no path on disk; use a stable synthetic URI (not uploadable).
    return "stdin" if display == "-" else display.replace("\\", "/")


def build_sarif(results: List[Tuple[str, Report]],
                execution_successful: bool = True) -> dict:
    """Build a single-run SARIF 2.1.0 document from (display_path, Report) pairs."""
    sarif_results = []
    rule_ids = set()
    for display, report in results:
        uri = _sarif_uri(display)
        for f in report.findings:
            rule_ids.add(f.id)
            loc = {"physicalLocation": {"artifactLocation": {"uri": uri}}}
            if f.line:
                loc["physicalLocation"]["region"] = {"startLine": int(f.line)}
            sarif_results.append({
                "ruleId": f.id,
                "level": _LEVEL.get(f.level, "warning"),
                "message": {"text": f.message},
                "locations": [loc],
            })

    # Deterministic ordering: by file, then rule, then line, then message.
    sarif_results.sort(key=lambda r: (
        r["locations"][0]["physicalLocation"]["artifactLocation"]["uri"],
        r["ruleId"],
        r["locations"][0]["physicalLocation"].get("region", {}).get("startLine", 0),
        r["message"]["text"],
    ))

    rules = [{
        "id": rid,
        "name": rid,
        "shortDescription": {"text": _RULE_DESC.get(rid, rid)},
    } for rid in sorted(rule_ids)]

    return {
        "version": "2.1.0",
        "$schema": SCHEMA,
        "runs": [{
            "tool": {"driver": {
                "name": "qcheck",
                "informationUri": INFORMATION_URI,
                "version": __version__,
                "rules": rules,
            }},
            "results": sarif_results,
            "invocations": [{"executionSuccessful": bool(execution_successful)}],
        }],
    }
