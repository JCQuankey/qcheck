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
    "A small public benchmark for reviewing AI-generated Qiskit and OpenQASM "
    "snippets with qcheck. It reports `static_pass_rate` — the share of snippets "
    "that pass qcheck's current static review checks — as an early quality signal. "
    "Rows marked _SAMPLE_ are demo data; real runs will include provenance, task "
    "counts, qcheck version, and prompt hash."
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
        "# qcheck static review benchmark",
        "",
        "_A small public benchmark for reviewing AI-generated Qiskit and OpenQASM "
        "snippets with qcheck. See [methodology](../methodology.md)._",
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


GITHUB = "https://github.com/JCQuankey/qcheck"
METHODOLOGY_URL = GITHUB + "/blob/main/leaderboard/methodology.md"



def _row_cells(rows: list) -> str:
    out = ""
    for i, r in enumerate(rows, 1):
        label = html.escape(str(r.get("model", "?")))
        if r.get("is_sample"):
            label += " <span class='pill'>SAMPLE</span>"
        out += (
            f"<tr><td class='num'>{i}</td><td>{label}</td>"
            f"<td>{html.escape(str(r.get('provider', '?')))}</td>"
            f"<td class='num'>{float(r.get('pass_rate', 0.0)) * 100:.1f}%</td>"
            f"<td class='num'>{r.get('tasks_passed', 0)} / {r.get('tasks_attempted', 0)}</td>"
            f"<td class='num'>{r.get('unsafe_count', 0)}</td>"
            f"<td class='num'>v{html.escape(str(r.get('qcheck_version', '?')))}</td></tr>"
        )
    return out or "<tr><td colspan='7'><em>no results yet</em></td></tr>"


SITE_URL = "https://jcquankey.github.io/qcheck/"


def to_html(rows: list) -> str:
    return (
        "<!doctype html><html lang='en'><head><meta charset='utf-8'>"
        "<meta name='viewport' content='width=device-width, initial-scale=1'>"
        "<title>qcheck — review AI-generated quantum code</title>"
        "<meta name='description' content='qcheck is a review layer for AI-generated "
        "Qiskit and OpenQASM. Catch the avoidable before code reaches humans, CI, or simulators.'>"
        f"<link rel='canonical' href='{SITE_URL}'>"
        "<link rel='icon' sizes='32x32' type='image/png' href='assets/favicon-32.png'>"
        "<link rel='icon' sizes='16x16' type='image/png' href='assets/favicon-16.png'>"
        "<link rel='apple-touch-icon' href='assets/apple-touch-icon.png'>"
        "<meta property='og:title' content='qcheck — AI writes quantum code. qcheck reviews it.'>"
        "<meta property='og:description' content='A review layer for AI-generated Qiskit and OpenQASM.'>"
        "<meta property='og:type' content='website'>"
        f"<meta property='og:url' content='{SITE_URL}'>"
        "<meta property='og:image' content='assets/og-qcheck.png'>"
        "<meta name='twitter:card' content='summary_large_image'>"
        "<link rel='stylesheet' href='brand.css'>"
        "</head><body>"
        "<a class='skip' href='#main'>Skip to content</a>"
        # nav
        "<nav class='nav' id='nav'><div class='wrap'>"
        "<a class='brand' href='#top'><img src='assets/favicon-32.png' alt=''>"
        "Quankey <span class='prod'>qcheck</span></a>"
        "<div class='links'>"
        "<a href='#benchmark'>Benchmark</a><a href='#checks'>Checks</a>"
        "<a href='#roadmap'>Roadmap</a>"
        f"<a class='btn primary' href='{GITHUB}'>GitHub</a>"
        "</div></div></nav>"
        "<main id='main'>"
        # hero (2 columns)
        "<header class='hero' id='top'><div class='wrap'>"
        "<div>"
        "<p class='eyebrow'>Quantum code review</p>"
        "<h1>AI writes quantum code. qcheck reviews it.</h1>"
        "<p class='sub'>A review layer for AI-generated Qiskit and OpenQASM.</p>"
        "<p class='lede'>Catch the avoidable before code reaches humans, CI, or simulators.</p>"
        "<div class='btns'>"
        f"<a class='btn primary' href='{GITHUB}'>View on GitHub</a>"
        "<a class='btn ghost' href='#benchmark'>See the benchmark</a>"
        "</div></div>"
        # evidence artifact (terminal)
        "<div class='terminal'><div class='bar'><i></i><i></i><i></i></div>"
        "<div class='body'>"
        "<div><span class='p'>$</span> qcheck review bell.py</div>"
        "<div class='c'># static review, no execution</div>"
        "<div><span class='ok'>pass</span>  QuantumCircuit + measurement</div>"
        "<div><span class='fl'>flag</span>  execute() removed in Qiskit 1.0</div>"
        "<div><span class='fl'>flag</span>  Aer import removed</div>"
        "<div class='c'># 1 passed &middot; 2 flagged</div>"
        "</div></div>"
        "</div></header>"
        # what qcheck checks
        "<section class='section'><div class='wrap'>"
        "<p class='eyebrow'>Signals</p><h2>What qcheck reviews</h2>"
        "<p class='lead'>qcheck v0 reviews static signals — no execution required, so it "
        "runs safely on untrusted model output inside an agent loop or CI.</p>"
        "<div class='cards'>"
        "<div class='card'><div class='kicker'>Qiskit</div><h3>API usage</h3><p>Flags "
        "removed-in-1.0 imports like <code>execute()</code> and <code>Aer</code>, and "
        "deprecated gate aliases.</p></div>"
        "<div class='card'><div class='kicker'>OpenQASM</div><h3>Parse issues</h3><p>Header, "
        "register declarations, index ranges, and measurement validity.</p></div>"
        "<div class='card'><div class='kicker'>Safety</div><h3>Unsafe patterns</h3><p>Filesystem, "
        "network, process, or dynamic-exec constructs are flagged before anything runs.</p></div>"
        "<div class='card'><div class='kicker'>Structure</div><h3>Missing measurements</h3><p>Common "
        "mistakes that make a circuit fail or return nothing useful.</p></div>"
        "<div class='card'><div class='kicker'>Models</div><h3>Common LLM mistakes</h3><p>The "
        "recurring errors models make in generated quantum snippets.</p></div>"
        "</div></div></section>"
        # checks panel
        "<section class='section' id='checks'><div class='wrap'>"
        "<p class='eyebrow'>Review</p><h2>A review, not a verdict</h2>"
        "<p class='lead'>Each snippet returns a set of signals — passed or flagged — that "
        "a developer or agent can act on before the code runs.</p>"
        "<div class='checks'>"
        "<div class='row'><span class='dot pass'></span><span class='name'>modern_qiskit_api</span>"
        "<span class='msg'>no removed 1.0 imports</span></div>"
        "<div class='row'><span class='dot pass'></span><span class='name'>declared_registers</span>"
        "<span class='msg'>qreg / creg present, in range</span></div>"
        "<div class='row'><span class='dot pass'></span><span class='name'>has_measurement</span>"
        "<span class='msg'>circuit measures qubits</span></div>"
        "<div class='row'><span class='dot flag'></span><span class='name'>execute_removed</span>"
        "<span class='msg'>execute() removed in Qiskit 1.0</span></div>"
        "<div class='row'><span class='dot flag'></span><span class='name'>unsafe_side_effect</span>"
        "<span class='msg'>writes to disk</span></div>"
        "<div class='summary'>3 passed &middot; 2 flagged</div>"
        "</div></div></section>"
        # scope
        "<section class='section'><div class='wrap'>"
        "<p class='eyebrow'>Scope</p><h2>What it does — and doesn't</h2>"
        "<div class='scope'>"
        "<div class='col in'><h3>In scope</h3><ul>"
        "<li>Static review of Qiskit / OpenQASM snippets</li>"
        "<li>Common, avoidable failures</li>"
        "<li>CI and agent preflight</li>"
        "<li>Machine-readable JSON output</li></ul></div>"
        "<div class='col out'><h3>Not in scope</h3><ul>"
        "<li>Hardware execution</li>"
        "<li>Algorithm correctness or formal proof</li>"
        "<li>PQC migration</li></ul></div>"
        "</div></div></section>"
        # benchmark
        "<section class='section' id='benchmark'><div class='wrap'>"
        "<p class='eyebrow'>Benchmark</p><h2>Static review benchmark</h2>"
        "<p class='lead'>Tracks how AI-generated snippets perform against qcheck's current "
        "static review checks. It reports <code>static_pass_rate</code> on a small public "
        "task set as an early quality signal. Rows marked "
        "<span class='pill'>SAMPLE</span> are demo data.</p>"
        "<div class='tablewrap'><table><thead><tr>"
        "<th>#</th><th>Model</th><th>Provider</th><th>Static pass rate</th>"
        "<th>Passed / Attempted</th><th>Unsafe</th><th>qcheck</th>"
        "</tr></thead><tbody>"
        + _row_cells(rows) +
        "</tbody></table></div>"
        f"<p class='note'>Real runs will include provenance, task counts, qcheck version, "
        f"and prompt hash. See the <a href='{METHODOLOGY_URL}'>methodology</a>.</p>"
        "</div></section>"
        # roadmap
        "<section class='section' id='roadmap'><div class='wrap'>"
        "<p class='eyebrow'>Roadmap</p><h2>Where it is going</h2>"
        "<div class='steps'>"
        "<div class='step'><div class='when'>Today</div><h3>CLI</h3>"
        "<p>Static review for Qiskit and OpenQASM, with JSON output for agents and CI.</p></div>"
        "<div class='step'><div class='when'>Next</div><h3>GitHub Action &amp; MCP</h3>"
        "<p>Review in CI and as an agent-callable tool.</p></div>"
        "<div class='step'><div class='when'>Later</div><h3>Hosted API</h3>"
        "<p>A review endpoint for agent workflows.</p></div>"
        "</div></div></section>"
        "</main>"
        # footer
        "<footer><div class='wrap'>"
        "<p class='disc'>qcheck runs static review on AI-generated quantum code. It does "
        "not run the code and does not claim algorithm correctness.</p>"
        f"<a href='{GITHUB}'>GitHub</a>"
        "<a href='mailto:dev@quankey.xyz'>dev@quankey.xyz</a>"
        "<a href='mailto:security@quankey.xyz'>security@quankey.xyz</a>"
        f"<a href='{GITHUB}/blob/main/LICENSE'>Apache-2.0</a>"
        "</div></footer>"
        "</body></html>"
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
