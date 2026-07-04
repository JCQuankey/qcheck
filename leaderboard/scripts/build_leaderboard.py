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

SITE_CSS = """
:root{--navy:#1f3a65;--navy-2:#2b4d85;--ink:#161b26;--muted:#5b6472;
--bg:#ffffff;--tint:#f6f8fc;--line:#e6e9f0;--chip:#eef2f9}
*{box-sizing:border-box}
body{margin:0;color:var(--ink);background:var(--bg);
font-family:system-ui,-apple-system,Segoe UI,Roboto,Helvetica,Arial,sans-serif;
line-height:1.6;-webkit-font-smoothing:antialiased}
a{color:var(--navy);text-decoration:none}
a:hover{text-decoration:underline}
.wrap{max-width:960px;margin:0 auto;padding:0 1.25rem}
.hero{background:var(--tint);border-bottom:1px solid var(--line);padding:3.5rem 0 3rem}
.hero .wrap{display:flex;flex-direction:column;align-items:center;text-align:center}
.hero img{width:104px;height:104px}
.hero h1{font-size:2rem;margin:.6rem 0 .1rem;letter-spacing:-.02em}
.tag{font-size:1.35rem;font-weight:650;margin:.4rem 0 .2rem;color:var(--navy)}
.sub{color:var(--muted);max-width:38rem;margin:.2rem 0 1.4rem}
.btns{display:flex;gap:.75rem;flex-wrap:wrap;justify-content:center}
.btn{display:inline-block;padding:.6rem 1.15rem;border-radius:8px;font-weight:600;
border:1px solid var(--navy)}
.btn.primary{background:var(--navy);color:#fff}
.btn.primary:hover{background:var(--navy-2);text-decoration:none}
.btn.ghost{background:#fff;color:var(--navy)}
.btn.ghost:hover{background:var(--chip);text-decoration:none}
section{padding:2.6rem 0;border-bottom:1px solid var(--line)}
h2{font-size:1.25rem;letter-spacing:-.01em;margin:0 0 1rem}
.lead{color:var(--muted);margin:0 0 1.4rem;max-width:44rem}
.cards{display:grid;grid-template-columns:repeat(auto-fit,minmax(210px,1fr));gap:1rem}
.card{border:1px solid var(--line);border-radius:10px;padding:1rem 1.1rem;background:#fff}
.card h3{margin:0 0 .35rem;font-size:1rem;color:var(--navy)}
.card p{margin:0;color:var(--muted);font-size:.95rem}
table{border-collapse:collapse;width:100%;font-size:.95rem}
th,td{border-bottom:1px solid var(--line);padding:.6rem .7rem;text-align:left}
th{color:var(--muted);font-weight:600;font-size:.85rem;text-transform:uppercase;letter-spacing:.03em}
.badge{display:inline-block;font-size:.72rem;font-weight:700;color:var(--navy);
background:var(--chip);border-radius:99px;padding:.1rem .5rem;vertical-align:middle}
.note{color:var(--muted);font-size:.92rem;margin:1rem 0 0}
.steps{display:grid;grid-template-columns:repeat(auto-fit,minmax(200px,1fr));gap:1rem}
.step{border:1px solid var(--line);border-radius:10px;padding:1rem 1.1rem}
.step .when{font-size:.75rem;font-weight:700;text-transform:uppercase;letter-spacing:.04em;color:var(--muted)}
.step h3{margin:.25rem 0 .3rem;font-size:1rem;color:var(--navy)}
.step p{margin:0;color:var(--muted);font-size:.95rem}
footer{padding:2rem 0 3rem;color:var(--muted);font-size:.92rem}
footer .wrap{display:flex;flex-wrap:wrap;gap:.4rem 1.5rem;align-items:center}
code{background:var(--chip);border-radius:5px;padding:.05rem .35rem;font-size:.9em}
""".strip()


def _row_cells(rows: list) -> str:
    out = ""
    for i, r in enumerate(rows, 1):
        label = html.escape(str(r.get("model", "?")))
        if r.get("is_sample"):
            label += " <span class='badge'>SAMPLE</span>"
        out += (
            f"<tr><td>{i}</td><td>{label}</td>"
            f"<td>{html.escape(str(r.get('provider', '?')))}</td>"
            f"<td>{float(r.get('pass_rate', 0.0)) * 100:.1f}%</td>"
            f"<td>{r.get('tasks_passed', 0)} / {r.get('tasks_attempted', 0)}</td>"
            f"<td>{r.get('unsafe_count', 0)}</td>"
            f"<td>v{html.escape(str(r.get('qcheck_version', '?')))}</td></tr>"
        )
    return out or "<tr><td colspan='7'><em>no results yet</em></td></tr>"


def to_html(rows: list) -> str:
    return (
        "<!doctype html><html lang='en'><head><meta charset='utf-8'>"
        "<meta name='viewport' content='width=device-width, initial-scale=1'>"
        "<title>qcheck — review AI-generated quantum code</title>"
        "<meta name='description' content='qcheck is a lightweight review layer for "
        "AI-generated Qiskit and OpenQASM snippets. It catches common issues early.'>"
        "<link rel='icon' type='image/png' href='assets/favicon.png'>"
        f"<style>{SITE_CSS}</style></head><body>"
        # hero
        "<header class='hero'><div class='wrap'>"
        "<img src='assets/qcheck-logo.png' alt='qcheck logo' width='104' height='104'>"
        "<h1>qcheck</h1>"
        "<p class='tag'>AI writes quantum code. qcheck reviews it.</p>"
        "<p class='sub'>A lightweight review layer for AI-generated Qiskit and OpenQASM "
        "snippets. It catches common issues early, so agents and developers can improve "
        "quantum code before it reaches humans, CI, or simulators.</p>"
        "<div class='btns'>"
        f"<a class='btn primary' href='{GITHUB}'>View on GitHub</a>"
        "<a class='btn ghost' href='#benchmark'>See the static benchmark</a>"
        "</div></div></header>"
        "<main>"
        # what qcheck checks
        "<section><div class='wrap'>"
        "<h2>What qcheck checks</h2>"
        "<p class='lead'>qcheck v0 focuses on static review signals — no execution "
        "required, so it is safe to run on untrusted model output in an agent loop or CI.</p>"
        "<div class='cards'>"
        "<div class='card'><h3>Qiskit API usage</h3><p>Flags removed-in-1.0 imports "
        "like <code>execute()</code> and <code>Aer</code>, and deprecated gate aliases.</p></div>"
        "<div class='card'><h3>OpenQASM parsing</h3><p>Header, register declarations, "
        "index ranges, and measurement validity.</p></div>"
        "<div class='card'><h3>Unsafe patterns</h3><p>Filesystem, network, process, or "
        "dynamic-exec constructs are flagged before anything runs.</p></div>"
        "<div class='card'><h3>Missing measurements</h3><p>Common structural mistakes "
        "that make a circuit fail or return nothing useful.</p></div>"
        "<div class='card'><h3>Common LLM mistakes</h3><p>The recurring errors models "
        "make in generated quantum snippets.</p></div>"
        "</div></div></section>"
        # benchmark
        "<section id='benchmark'><div class='wrap'>"
        "<h2>Static benchmark</h2>"
        "<p class='lead'>The qcheck benchmark tracks how AI-generated snippets perform "
        "against qcheck's current static review checks. It reports "
        "<code>static_pass_rate</code> on a small public task set as an early quality "
        "signal. Rows marked <span class='badge'>SAMPLE</span> are demo data.</p>"
        "<table><thead><tr><th>#</th><th>Model</th><th>Provider</th>"
        "<th>Static pass rate</th><th>Passed / Attempted</th><th>Unsafe</th>"
        "<th>qcheck</th></tr></thead><tbody>"
        + _row_cells(rows) +
        "</tbody></table>"
        f"<p class='note'>Real runs will include provenance, task counts, qcheck version, "
        f"and prompt hash. See the <a href='{METHODOLOGY_URL}'>methodology</a>.</p>"
        "</div></section>"
        # roadmap
        "<section><div class='wrap'>"
        "<h2>Where it is going</h2>"
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
        f"<a href='{GITHUB}'>GitHub</a>"
        "<a href='mailto:dev@quankey.xyz'>dev@quankey.xyz</a>"
        "<a href='mailto:security@quankey.xyz'>security@quankey.xyz</a>"
        f"<a href='{GITHUB}/blob/main/LICENSE'>Apache-2.0</a>"
        "</div></footer></body></html>"
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
