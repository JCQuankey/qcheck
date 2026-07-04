"""Tests for the leaderboard build script. Static output only, no network."""
import json
from pathlib import Path

import build_leaderboard as bl


def _write_result(path: Path, model: str, pass_rate: float, is_sample=True):
    path.write_text(json.dumps({
        "model": model,
        "provider": "sample",
        "is_sample": is_sample,
        "pass_rate": pass_rate,
        "tasks_passed": int(round(pass_rate * 6)),
        "tasks_attempted": 6,
        "unsafe_count": 0,
        "qcheck_version": "0.1.0",
    }), encoding="utf-8")


def test_build_creates_markdown_and_html(tmp_path: Path):
    results = tmp_path / "results"
    results.mkdir()
    _write_result(results / "a.json", "model-a", 0.5)
    out = tmp_path / "site" / "leaderboard.md"
    rc = bl.main([str(results), "--out", str(out)])
    assert rc == 0
    assert out.is_file()
    assert (tmp_path / "site" / "index.html").is_file()


def test_markdown_labels_sample_and_shows_rate(tmp_path: Path):
    results = tmp_path / "results"
    results.mkdir()
    _write_result(results / "a.json", "model-a", 0.5)
    out = tmp_path / "leaderboard.md"
    bl.main([str(results), "--out", str(out)])
    md = out.read_text(encoding="utf-8")
    assert "model-a" in md
    assert "SAMPLE" in md
    assert "50.0%" in md
    assert "does NOT measure" in md  # honesty caveat present


def test_rows_sorted_by_pass_rate_desc(tmp_path: Path):
    results = tmp_path / "results"
    results.mkdir()
    _write_result(results / "low.json", "low-model", 0.2)
    _write_result(results / "high.json", "high-model", 0.9)
    rows = bl.load_results(results)
    assert [r["model"] for r in rows] == ["high-model", "low-model"]


def test_empty_results_dir_produces_placeholder(tmp_path: Path):
    results = tmp_path / "results"
    results.mkdir()
    out = tmp_path / "leaderboard.md"
    bl.main([str(results), "--out", str(out)])
    md = out.read_text(encoding="utf-8")
    assert "no results yet" in md
