#!/usr/bin/env python3
"""Evaluate a model's quantum-code submission with qcheck. No LLM/API calls.

Scans a submission directory:
    <submission_dir>/<task_id>.{py,qasm}   (+ optional metadata.json)
runs qcheck statically on each file (qcheck NEVER executes the submitted code),
and writes an aggregated results JSON.

Usage:
    python3 leaderboard/scripts/evaluate_submission.py \
        leaderboard/submissions/sample/demo_model \
        --out leaderboard/results/sample_results.json

Security: this script only reads files and passes their text to qcheck, which
parses (does not run) them. It imports nothing from the submission and never
calls exec/eval on submitted content.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

# Make the repo root importable so we use the local qcheck package.
ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from qcheck import __version__ as QCHECK_VERSION  # noqa: E402
from qcheck.cli import verify_text  # noqa: E402

CODE_SUFFIXES = (".py", ".qasm")


def load_task_ids(tasks_root: Path) -> set:
    """Collect known task ids from leaderboard/tasks/**/*.json."""
    ids = set()
    if not tasks_root.is_dir():
        return ids
    for jf in sorted(tasks_root.rglob("*.json")):
        try:
            data = json.loads(jf.read_text(encoding="utf-8"))
            if isinstance(data, dict) and data.get("id"):
                ids.add(str(data["id"]))
        except (json.JSONDecodeError, OSError):
            continue
    return ids


def evaluate_submission(submission_dir: Path, tasks_root: Path,
                        generated_at: str | None = None) -> dict:
    meta_path = submission_dir / "metadata.json"
    meta = {}
    if meta_path.is_file():
        try:
            meta = json.loads(meta_path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            meta = {}

    known_ids = load_task_ids(tasks_root)

    per_task = []
    counts = {"pass": 0, "warning": 0, "fail": 0, "unsafe": 0, "error": 0}

    for path in sorted(submission_dir.iterdir()):
        if path.suffix not in CODE_SUFFIXES or not path.is_file():
            continue
        task_id = path.stem if path.stem in known_ids else None
        try:
            report = verify_text(str(path), path.read_text(encoding="utf-8"))
            status = "unsafe" if report.unsafe else report.status
            error_ids = [f.id for f in report.errors]
            warn_ids = [f.id for f in report.warnings]
            framework = report.framework
            confidence = report.confidence
        except Exception as exc:  # robust: one bad file must not crash the run
            status = "error"
            error_ids = [f"EVAL-ERROR: {type(exc).__name__}"]
            warn_ids = []
            framework = "unknown"
            confidence = 0.0

        counts[status] = counts.get(status, 0) + 1
        per_task.append({
            "file": path.name,
            "task_id": task_id,
            "framework": framework,
            "status": status,
            "error_ids": error_ids,
            "warning_ids": warn_ids,
            "confidence": round(confidence, 3),
        })

    attempted = len(per_task)
    passed = counts["pass"]
    pass_rate = round(passed / attempted, 3) if attempted else 0.0

    return {
        "model": meta.get("model", submission_dir.name),
        "provider": meta.get("provider", "unknown"),
        "is_sample": bool(meta.get("is_sample", False)),
        "scored_by": f"qcheck-static-v{QCHECK_VERSION}",
        "qcheck_version": QCHECK_VERSION,
        "generated_at": generated_at if generated_at is not None else meta.get("date"),
        "tasks_attempted": attempted,
        "tasks_passed": passed,
        "pass_rate": pass_rate,
        "counts": counts,
        "unsafe_count": counts["unsafe"],
        "failures": [t for t in per_task if t["status"] in ("fail", "unsafe", "error")],
        "warnings": counts["warning"],
        "tasks": per_task,
    }


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description="Evaluate a submission with qcheck (static, no execution).")
    parser.add_argument("submission_dir", help="path to <model> submission directory")
    parser.add_argument("--out", help="write results JSON here (default: stdout)")
    parser.add_argument("--tasks", default=None, help="tasks root (default: leaderboard/tasks)")
    parser.add_argument("--generated-at", default=None, help="ISO timestamp to stamp (default: metadata date or null)")
    args = parser.parse_args(argv)

    submission_dir = Path(args.submission_dir)
    if not submission_dir.is_dir():
        print(f"error: not a directory: {submission_dir}", file=sys.stderr)
        return 2
    tasks_root = Path(args.tasks) if args.tasks else (ROOT / "leaderboard" / "tasks")

    result = evaluate_submission(submission_dir, tasks_root, args.generated_at)
    text = json.dumps(result, indent=2, sort_keys=False)
    if args.out:
        out = Path(args.out)
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(text + "\n", encoding="utf-8")
        print(f"wrote {out}  (model={result['model']} pass_rate={result['pass_rate']})")
    else:
        print(text)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
