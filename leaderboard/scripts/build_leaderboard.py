#!/usr/bin/env python3
"""Build a static leaderboard (Markdown + minimal HTML) from result JSON files.

Usage:
    python3 leaderboard/scripts/build_leaderboard.py leaderboard/results \
        --out leaderboard/site/leaderboard.md

Reads one result JSON file, or every *.json in a directory, sorts models by
qcheck static pass rate, and writes a Markdown table (and an index.html beside
it). No external calls. Sample/demo results are clearly labelled.
"""
from __future__ import annotations

import argparse
import html
import json
import sys
from pathlib import Path

CAVEAT = (
    "**What this measures:** the qcheck *static* verdict (is the generated code "
    "well-formed, modern, safe, and likely to run?) on small Qiskit/OpenQASM "
    "tasks. **What it does NOT measure:** semantic/algorithmic correctness, "
    "quantum advantage, or hardware performance. Rows marked _SAMPLE_ are "
    "hand-written demos, not real model results."
)


def load_results(path: Path) -> list:
    files = []
    if path.is_dir():
        files = sorted(path.glob("*.json"))
    elif path.is_file():
        files = [path]
    rows = []
    for f in files:
        try:
            data = json.loads(f.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            continue
        if isinstance(data, dict) and "model" in data and "pass_rate" in data:
            rows.append(data)
    # Deterministic order: pass_rate desc, then model asc.
    rows.sort(key=lambda r: (-float(r.get("pass_rate", 0.0)), str(r.get("model", ""))))
    return rows


def _md_cell(value) -> str:
    """Make a value safe for a Markdown table cell (escape pipes, flatten newlines)."""
    return str(value).replace("|", "\\|").replace("\r", " ").replace("\n", " ")


def _label(row: dict) -> str:
    return _md_cell(row.get("model", "?")) + (" _(SAMPLE)_" if row.get("is_sample") else "")


def to_markdown(rows: list) -> str:
    lines = [
        "# Which LLM writes correct quantum code?",
        "",
        "_Experimental qcheck static leaderboard. See "
        "[methodology](../methodology.md)._",
        "",
        CAVEAT,
        "",
        "| # | Model | Provider | Static pass rate | Passed / Attempted | Unsafe | qcheck |",
        "|---|-------|----------|------------------|--------------------|--------|--------|",
    ]
    if not rows:
        lines.append("| - | _(no results yet)_ | - | - | - | - | - |")
    for i, r in enumerate(rows, 1):
        pr = f"{float(r.get('pass_rate', 0.0)) * 100:.1f}%"
        lines.append(
            f"| {i} | {_label(r)} | {_md_cell(r.get('provider', '?'))} | {pr} | "
            f"{r.get('tasks_passed', 0)} / {r.get('tasks_attempted', 0)} | "
            f"{r.get('unsafe_count', 0)} | v{r.get('qcheck_version', '?')} |"
        )
    lines += [
        "",
        "Run your own snippet through the tool: `qcheck verify <file>` "
        "(see the [repo README](../../README.md)).",
        "",
    ]
    return "\n".join(lines)


def to_html(rows: list) -> str:
    head = (
        "<!doctype html><html lang='en'><head><meta charset='utf-8'>"
        "<meta name='viewport' content='width=device-width, initial-scale=1'>"
        "<title>Which LLM writes correct quantum code?</title>"
        "<style>body{font-family:system-ui,sans-serif;max-width:820px;margin:2rem auto;"
        "padding:0 1rem;line-height:1.5}table{border-collapse:collapse;width:100%}"
        "th,td{border:1px solid #ccc;padding:6px 10px;text-align:left}"
        "th{background:#f4f4f4}.caveat{background:#fffbe6;border:1px solid #e6d27a;"
        "padding:.75rem 1rem;border-radius:6px}</style></head><body>"
    )
    rows_html = ""
    for i, r in enumerate(rows, 1):
        label = html.escape(str(r.get("model", "?")))
        if r.get("is_sample"):
            label += " <em>(SAMPLE)</em>"
        rows_html += (
            f"<tr><td>{i}</td><td>{label}</td>"
            f"<td>{html.escape(str(r.get('provider', '?')))}</td>"
            f"<td>{float(r.get('pass_rate', 0.0)) * 100:.1f}%</td>"
            f"<td>{r.get('tasks_passed', 0)} / {r.get('tasks_attempted', 0)}</td>"
            f"<td>{r.get('unsafe_count', 0)}</td>"
            f"<td>v{html.escape(str(r.get('qcheck_version', '?')))}</td></tr>"
        )
    if not rows:
        rows_html = "<tr><td colspan='7'><em>no results yet</em></td></tr>"
    caveat_html = (
        "<p class='caveat'>Measures the qcheck <strong>static</strong> verdict on small "
        "Qiskit/OpenQASM tasks. It does <strong>not</strong> measure semantic correctness, "
        "quantum advantage, or hardware performance. Rows marked <em>(SAMPLE)</em> are "
        "hand-written demos, not real model results.</p>"
    )
    return (
        head
        + "<h1>Which LLM writes correct quantum code?</h1>"
        + "<p><em>Experimental qcheck static leaderboard.</em></p>"
        + caveat_html
        + "<table><thead><tr><th>#</th><th>Model</th><th>Provider</th>"
        + "<th>Static pass rate</th><th>Passed / Attempted</th><th>Unsafe</th>"
        + "<th>qcheck</th></tr></thead><tbody>"
        + rows_html
        + "</tbody></table></body></html>"
    )


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description="Build a static leaderboard from result JSON files.")
    parser.add_argument("results", help="a result JSON file or a directory of them")
    parser.add_argument("--out", default="leaderboard/site/leaderboard.md", help="Markdown output path")
    parser.add_argument("--html", default=None, help="HTML output path (default: index.html beside --out)")
    args = parser.parse_args(argv)

    rows = load_results(Path(args.results))

    md_path = Path(args.out)
    md_path.parent.mkdir(parents=True, exist_ok=True)
    md_path.write_text(to_markdown(rows) + "\n", encoding="utf-8")

    html_path = Path(args.html) if args.html else md_path.parent / "index.html"
    html_path.write_text(to_html(rows) + "\n", encoding="utf-8")

    print(f"wrote {md_path} and {html_path}  ({len(rows)} model row(s))")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
