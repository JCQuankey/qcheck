"""SARIF 2.1.0 formatter for qcheck results (GitHub Code Scanning compatible).

Pure formatter over Report objects - no execution, no new dependencies, and it
does not touch the human or --json output. SARIF reports static qcheck findings;
it does not assert quantum correctness. Output ordering is deterministic.
"""
from __future__ import annotations

from typing import List, Optional, Tuple

from . import __version__
from .report import Report
from . import rules as rule_catalog

INFORMATION_URI = "https://github.com/JCQuankey/qcheck"
SCHEMA = "https://json.schemastore.org/sarif-2.1.0.json"

# qcheck level -> SARIF level. SARIF levels: none | note | warning | error.
_LEVEL = {"error": "error", "warning": "warning", "info": "note"}


def _rule_entry(rid: str) -> dict:
    """A SARIF reportingDescriptor enriched from the rule catalog."""
    entry = {"id": rid, "name": rid}
    if rule_catalog.known(rid):
        r = rule_catalog.get(rid)
        entry["name"] = r.title
        entry["shortDescription"] = {"text": r.title}
        entry["fullDescription"] = {"text": f"{r.why_it_matters} {r.recommended_action}"}
        entry["help"] = {"text": (f"{r.summary}\n\nWhy it matters: {r.why_it_matters}\n"
                                  f"Recommended action: {r.recommended_action}")}
        entry["defaultConfiguration"] = {"level": _LEVEL.get(r.default_level, "warning")}
        entry["properties"] = {"category": r.category, "appliesTo": r.applies_to}
    else:
        entry["shortDescription"] = {"text": rid}
    return entry


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

    # Only rules observed in this run are described (results reference rules by
    # ruleId, so this stays lean and every result's rule is defined). The full
    # catalog is available via `qcheck rules --json`.
    rules = [_rule_entry(rid) for rid in sorted(rule_ids)]

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
