"""Tests for the leaderboard evaluation script. No network / no code execution."""
from pathlib import Path

from conftest import LEADERBOARD
import evaluate_submission as ev

SAMPLE_DIR = LEADERBOARD / "submissions" / "sample" / "demo_model"
TASKS_ROOT = LEADERBOARD / "tasks"

REQUIRED_FIELDS = {
    "model", "provider", "is_sample", "scored_by", "qcheck_version",
    "generated_at", "tasks_attempted", "tasks_passed", "pass_rate",
    "counts", "unsafe_count", "failures", "warnings", "tasks",
}


def _evaluate():
    return ev.evaluate_submission(SAMPLE_DIR, TASKS_ROOT)


def test_sample_submission_evaluates_with_required_fields():
    result = _evaluate()
    assert REQUIRED_FIELDS.issubset(result.keys())
    assert result["model"] == "demo-model"
    assert result["is_sample"] is True


def test_sample_pass_rate_and_counts():
    result = _evaluate()
    # 6 hand-written demo files: 3 pass, 2 fail, 1 unsafe.
    assert result["tasks_attempted"] == 6
    assert result["tasks_passed"] == 3
    assert result["pass_rate"] == 0.5
    assert result["counts"]["pass"] == 3
    assert result["counts"]["fail"] == 2


def test_unsafe_file_is_counted():
    result = _evaluate()
    assert result["unsafe_count"] == 1
    unsafe = [t for t in result["tasks"] if t["status"] == "unsafe"]
    assert len(unsafe) == 1
    assert unsafe[0]["file"].endswith(".py")


def test_files_map_to_known_task_ids():
    result = _evaluate()
    mapped = [t for t in result["tasks"] if t["task_id"] is not None]
    # All six sample files are named after real task ids.
    assert len(mapped) == 6


def test_output_is_deterministic():
    assert _evaluate() == _evaluate()


def test_pass_rate_zero_on_empty_dir(tmp_path: Path):
    result = ev.evaluate_submission(tmp_path, TASKS_ROOT)
    assert result["tasks_attempted"] == 0
    assert result["pass_rate"] == 0.0


def test_no_network_imports():
    # The evaluator must not depend on any HTTP client.
    import sys
    for mod in ("requests", "httpx", "aiohttp"):
        assert mod not in sys.modules
