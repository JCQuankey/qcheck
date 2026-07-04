#!/usr/bin/env python3
"""Example: consume `qcheck verify --json` as an AI agent or CI step.

    qcheck verify snippet.py --json | python examples/consume_json.py
    qcheck verify . --json          | python examples/consume_json.py

Reads qcheck's JSON on stdin and prints a compact, agent-friendly summary.
Exit code is 1 if any error-level or unsafe finding is present, else 0 - so a
model that just generated the code can decide whether to revise it. Stdlib only;
no external dependencies. See docs/CONTRACTS.md for the JSON shape.
"""
import json
import sys


def summarize(report):
    """Return (text, has_blocking) for one single-file report object."""
    findings = report.get("static_checks", [])
    blocking = report.get("unsafe") or any(f["level"] == "error" for f in findings)
    lines = [f"status: {report['status']} ({len(findings)} finding(s))"]
    for f in findings:
        loc = f" (line {f['line']})" if f.get("line") else ""
        lines.append(f"  [{f['level']}] {f['id']}: {f['message']}{loc}")
    return "\n".join(lines), blocking


def main():
    data = json.load(sys.stdin)
    # Single file -> a bare object; multiple files/dir -> {"results": [...]}.
    reports = data["results"] if "results" in data else [data]
    blocking = False
    for r in reports:
        if "path" in r:
            print(r["path"])
        text, r_block = summarize(r)
        print(text)
        blocking = blocking or r_block
    return 1 if blocking else 0


if __name__ == "__main__":
    sys.exit(main())
