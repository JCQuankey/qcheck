#!/usr/bin/env python3
"""Evaluate LLM quantum-code submissions with qcheck. No LLM API calls.

Scans a submissions directory of the form:
    submissions/<model>/<task_id>.{py,qasm}
runs qcheck on each file, and writes an aggregated results JSON.

For v0, with no submissions present, it evaluates the qcheck fixtures as a demo
"model" so the pipeline is runnable today.
"""
from __future__ import annotations

import json
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
from qcheck.cli import verify_text  # noqa: E402


def evaluate_dir(model_name: str, directory: Path) -> dict:
    per_task = []
    counts = {"pass": 0, "warning": 0, "fail": 0, "unsafe": 0}
    for path in sorted(directory.glob("*")):
        if path.suffix not in (".py", ".qasm"):
            continue
        report = verify_text(str(path), path.read_text())
        status = "unsafe" if report.unsafe else report.status
        counts[status] = counts.get(status, 0) + 1
        per_task.append({
            "file": path.name,
            "framework": report.framework,
            "status": status,
            "error_ids": [f.id for f in report.errors],
            "confidence": report.confidence,
        })
    total = sum(counts.values()) or 1
    return {
        "model": model_name,
        "counts": counts,
        "pass_rate": round(counts["pass"] / total, 3),
        "tasks": per_task,
    }


def main() -> int:
    subs = ROOT / "leaderboard" / "submissions"
    results = []
    if subs.is_dir() and any(subs.iterdir()):
        for model_dir in sorted(p for p in subs.iterdir() if p.is_dir()):
            results.append(evaluate_dir(model_dir.name, model_dir))
    else:
        # demo mode: treat the fixtures as one "model" so the pipeline runs today
        results.append(evaluate_dir("demo-fixtures", ROOT / "fixtures"))

    results.sort(key=lambda r: r["pass_rate"], reverse=True)
    out = ROOT / "leaderboard" / "results" / "sample_results.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps({"leaderboard": results}, indent=2))
    print(f"wrote {out}")
    for r in results:
        print(f"  {r['model']:20s} pass_rate={r['pass_rate']} counts={r['counts']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
