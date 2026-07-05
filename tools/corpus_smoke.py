#!/usr/bin/env python3
"""Measure qcheck findings over a local corpus of real-world code.

Maintainer/adopter tool for false-positive hardening: point it at a local
directory of code you believe is correct (an installed framework's sources,
your own repo) and it reports what qcheck would flag, aggregated by rule,
level and framework, with the noisiest files listed. Report-only by default
(exit 0); `--expect-clean` turns error-level findings into a non-zero exit
for use as a regression gate.

The corpus stays on your disk: nothing is vendored, downloaded or uploaded,
and no third-party code enters this repository. Stdlib only; runs qcheck
in-process via its public `verify_text` entry point.

Usage:
  python tools/corpus_smoke.py PATH [PATH ...]
      [--disable RULE-ID] [--expect-clean] [--json FILE] [--markdown FILE]
      [--max-files N]

Example (measure against an installed framework's own sources):
  python -m venv /tmp/corpus && /tmp/corpus/bin/pip install cirq-core
  python tools/corpus_smoke.py /tmp/corpus/lib/python3*/site-packages/cirq/ops
"""
from __future__ import annotations

import argparse
import collections
import json
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from qcheck.cli import verify_text  # noqa: E402

# Mirrors the CLI's recursion pruning: never descend into vendored/VCS/cache
# directories. Kept local so this tool depends only on qcheck's public API.
SKIP_DIRS = frozenset({
    ".git", ".hg", ".svn", ".venv", "venv", "env", "ENV", "virtualenv",
    "node_modules", "__pycache__", ".tox", ".nox", ".mypy_cache",
    ".pytest_cache", ".ruff_cache", "build", "dist", ".eggs",
    ".idea", ".vscode",
})


def collect_files(paths, max_files=0):
    out = []
    for p in paths:
        if os.path.isfile(p):
            out.append(p)
            continue
        for root, dirs, files in os.walk(p):
            dirs[:] = sorted(d for d in dirs
                             if d not in SKIP_DIRS and not d.startswith("."))
            for fn in sorted(files):
                if fn.endswith((".py", ".qasm")):
                    out.append(os.path.join(root, fn))
    out = sorted(set(out))
    if max_files and len(out) > max_files:
        print(f"corpus_smoke: capping at {max_files} of {len(out)} files "
              f"(--max-files)", file=sys.stderr)
        out = out[:max_files]
    return out


def run(paths, disabled=frozenset(), max_files=0):
    files = collect_files(paths, max_files)
    by_rule = collections.Counter()
    by_level = collections.Counter()
    by_framework = collections.Counter()
    noisy = collections.Counter()
    examples = {}
    unreadable = 0
    for path in files:
        try:
            text = open(path, "r", encoding="utf-8", errors="replace").read()
        except OSError:
            unreadable += 1
            continue
        report = verify_text(path, text, disabled=disabled)
        by_framework[report.framework] += 1 if report.findings else 0
        for f in report.findings:
            by_rule[f.id] += 1
            by_level[f.level] += 1
            noisy[path] += 1
            examples.setdefault(f.id, f"{path}:{f.line or '-'}")
    return {
        "files_reviewed": len(files),
        "files_unreadable": unreadable,
        "files_with_findings": sum(1 for _p, n in noisy.items() if n),
        "findings_total": sum(by_rule.values()),
        "by_level": dict(by_level),
        "by_rule": dict(by_rule.most_common()),
        "by_framework_with_findings": dict(by_framework.most_common()),
        "noisiest_files": dict(noisy.most_common(10)),
        "example_per_rule": examples,
        "disabled": sorted(disabled),
        "note": ("Findings on presumptively-correct corpora indicate rules "
                 "to inspect for false positives; they are not a measured "
                 "global false-positive rate."),
    }


def to_markdown(summary):
    lines = ["# qcheck corpus smoke report", ""]
    lines.append(f"- files reviewed: {summary['files_reviewed']}")
    lines.append(f"- findings: {summary['findings_total']} "
                 f"({summary['by_level']})")
    lines.append("")
    lines.append("| Rule | Count | Example |")
    lines.append("|---|---:|---|")
    for rule, n in summary["by_rule"].items():
        lines.append(f"| {rule} | {n} | {summary['example_per_rule'][rule]} |")
    lines.append("")
    lines.append(summary["note"])
    return "\n".join(lines) + "\n"


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("paths", nargs="+", help="local corpus files/directories")
    ap.add_argument("--disable", action="append", default=[],
                    metavar="RULE-ID", help="rule(s) to disable, as in qcheck")
    ap.add_argument("--expect-clean", action="store_true",
                    help="exit 1 if any error-level finding remains")
    ap.add_argument("--json", metavar="FILE", help="write JSON summary")
    ap.add_argument("--markdown", metavar="FILE", help="write Markdown summary")
    ap.add_argument("--max-files", type=int, default=0,
                    help="review at most N files (0 = no cap)")
    args = ap.parse_args(argv)

    disabled = frozenset(p.strip().upper() for chunk in args.disable
                         for p in chunk.split(",") if p.strip())
    summary = run(args.paths, disabled, args.max_files)

    if args.json:
        with open(args.json, "w", encoding="utf-8") as fh:
            json.dump(summary, fh, indent=2)
    if args.markdown:
        with open(args.markdown, "w", encoding="utf-8") as fh:
            fh.write(to_markdown(summary))
    if not args.json and not args.markdown:
        json.dump(summary, sys.stdout, indent=2)
        print()

    if args.expect_clean and summary["by_level"].get("error", 0) > 0:
        print(f"corpus_smoke: {summary['by_level']['error']} error-level "
              f"finding(s) on an expected-clean corpus.", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
