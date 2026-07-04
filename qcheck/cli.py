"""qcheck command-line interface (argparse, stdlib only).

Exit codes:
  0  pass (or pass-with-warnings)
  1  verification failed (errors found)
  2  unsafe input / unsupported framework
  3  internal error
"""
from __future__ import annotations

import argparse
import ast
import json
import os
import sys
from typing import List, Optional, Tuple

from . import __version__
from .detect import detect_framework
from .report import Report
from .checks_qasm import check_qasm
from .checks_qiskit import check_qiskit
from .safety import scan_python_safety
from .sarif import build_sarif
from . import rules as rule_catalog

EXIT_PASS = 0
EXIT_FAIL = 1
EXIT_UNSAFE = 2
EXIT_INTERNAL = 3


def verify_text(path: str, text: str) -> Report:
    framework = detect_framework(path, text)

    if framework in ("qasm2", "qasm3"):
        syntax_valid, findings, fixes = check_qasm(text, framework)
        return Report(framework=framework, syntax_valid=syntax_valid,
                      findings=findings, suggested_fixes=fixes)

    if framework == "qiskit":
        syntax_valid, unsafe, findings, fixes = check_qiskit(text)
        return Report(framework=framework, syntax_valid=syntax_valid,
                      findings=findings, suggested_fixes=fixes, unsafe=unsafe)

    # Any .py is safety-screened even if it does not look like qiskit: the RCE
    # threat is identical regardless of imports (defense in depth).
    if framework == "python_unknown":
        r = Report(framework=framework, syntax_valid=True)
        try:
            safety = scan_python_safety(ast.parse(text))
        except SyntaxError as e:
            r.syntax_valid = False
            from .report import Finding
            r.findings.append(Finding("PY-SYNTAX", "error",
                                      f"Python syntax error: {e.msg}", e.lineno))
            return r
        if safety:
            r.unsafe = True
            r.findings.extend(safety)
        else:
            r.findings.append(_unsupported_finding(framework))
        return r

    # unknown extension / non-python, non-qasm
    r = Report(framework=framework, syntax_valid=True)
    r.findings.append(_unsupported_finding(framework))
    return r


def _unsupported_finding(framework):
    from .report import Finding
    return Finding(
        "UNSUPPORTED", "error",
        f"Framework '{framework}' is not supported in qcheck v0 "
        f"(supported: OpenQASM 2/3, Qiskit Python).", None)


def _exit_code(report: Report) -> int:
    if report.unsafe:
        return EXIT_UNSAFE
    if any(f.id == "UNSUPPORTED" for f in report.findings):
        return EXIT_UNSAFE
    if report.status == "fail":
        return EXIT_FAIL
    return EXIT_PASS


def _print_human(report: Report, path: str) -> None:
    icon = {"pass": "PASS", "warning": "WARN", "fail": "FAIL"}[report.status]
    print(f"qcheck {__version__}  [{icon}]  {path}  ({report.framework})")
    print(f"  syntax_valid={report.syntax_valid}  "
          f"unsafe={report.unsafe}  confidence={report.confidence}")
    print(f"  runnable_in_simulator={report.runnable_in_simulator} "
          f"(static-only in v0)")
    if not report.findings:
        print("  no issues found.")
    for f in report.findings:
        loc = f" (line {f.line})" if f.line else ""
        print(f"  [{f.level}] {f.id}: {f.message}{loc}")
    for fix in report.suggested_fixes:
        print(f"  fix -> {fix}")


_LANG_EXT = {"qasm2": ".qasm", "qasm3": ".qasm", "qiskit": ".py", "python": ".py"}

# Directories skipped during recursion: virtualenvs, VCS, caches, build output,
# vendored deps. Without this, `qcheck verify .` in a repo with a .venv would
# review thousands of third-party files (pip, etc.) and flag them as unsafe.
# Explicit file/dir paths passed on the command line are never pruned.
_SKIP_DIRS = frozenset({
    ".git", ".hg", ".svn", ".venv", "venv", "env", "ENV", "virtualenv",
    "node_modules", "__pycache__", ".tox", ".nox", ".mypy_cache",
    ".pytest_cache", ".ruff_cache", "site-packages", "build", "dist",
    ".eggs", ".idea", ".vscode",
})


def _expand_targets(paths: List[str]) -> List[str]:
    """Expand directories into their .py/.qasm files (recursive, sorted).
    Keeps '-' (stdin) and explicit file paths. Deterministic order.
    Recursion skips vendored/build/VCS dirs (see _SKIP_DIRS); hidden dirs
    (dot-prefixed) are skipped too, but an explicitly named dir still descends."""
    out: List[str] = []
    for p in paths:
        if p == "-":
            out.append("-")
        elif os.path.isdir(p):
            found = []
            for root, dirs, files in os.walk(p):
                # Prune in place (topdown walk): don't descend into vendor/hidden dirs.
                dirs[:] = [d for d in dirs
                           if d not in _SKIP_DIRS and not d.startswith(".")]
                for fn in files:
                    if fn.endswith((".py", ".qasm")):
                        found.append(os.path.join(root, fn))
            out.extend(sorted(found))
        else:
            out.append(p)
    # de-dupe while preserving first occurrence
    seen, uniq = set(), []
    for t in out:
        if t not in seen:
            seen.add(t)
            uniq.append(t)
    return uniq


def _detect_name(display: str, text: str, lang: Optional[str]) -> str:
    if lang:
        return "stdin" + _LANG_EXT[lang]
    if display == "-":
        return "stdin.qasm" if "openqasm" in text.lower() else "stdin.py"
    return display


def _verify_one(display: str, lang: Optional[str], stdin_text: Optional[str]) -> Tuple[str, Optional[Report], Optional[str]]:
    """Return (display, report, read_error)."""
    try:
        text = stdin_text if display == "-" else open(display, "r", encoding="utf-8").read()
    except OSError as e:
        return (display, None, f"cannot read {display}: {e}")
    try:
        return (display, verify_text(_detect_name(display, text, lang), text), None)
    except Exception as e:  # never crash on one bad file
        return (display, None, f"internal error: {e}")


def _run_rules(args) -> int:
    """`qcheck rules` - print the rule catalog (human table or JSON)."""
    cat = rule_catalog.catalog()
    if args.json:
        print(json.dumps({"qcheck_version": __version__,
                          "rules": [r.to_dict() for r in cat]}, indent=2))
        return EXIT_PASS
    print(f"qcheck {__version__} - {len(cat)} rules\n")
    print(f"{'RULE':24} {'LEVEL':8} {'CATEGORY':18} SUMMARY")
    for r in cat:
        print(f"{r.id:24} {r.default_level:8} {r.category:18} {r.summary}")
    print("\nRun `qcheck rules --json` for full metadata "
          "(why it matters + recommended action).")
    return EXIT_PASS


def _worst_exit(units) -> int:
    """Worst-case exit code across verified units (findings-based, not format)."""
    worst = EXIT_PASS
    for _display, report, err in units:
        if err is not None:
            worst = max(worst, EXIT_INTERNAL)
            continue
        rc = _exit_code(report)
        worst = EXIT_UNSAFE if EXIT_UNSAFE in (worst, rc) else max(worst, rc)
    return worst


def main(argv: Optional[List[str]] = None) -> int:
    parser = argparse.ArgumentParser(
        prog="qcheck",
        description="Review LLM-generated quantum code (Qiskit / OpenQASM).")
    parser.add_argument("--version", action="version",
                        version=f"qcheck {__version__}")
    sub = parser.add_subparsers(dest="command")
    p_verify = sub.add_parser("verify", help="review .qasm/.py files, directories, or stdin")
    p_verify.add_argument("paths", nargs="+",
                          help="one or more files or directories, or '-' for stdin")
    p_verify.add_argument("--format", choices=("human", "json", "sarif"),
                          default=None,
                          help="output format (default: human). 'sarif' emits "
                               "SARIF 2.1.0 for GitHub Code Scanning.")
    p_verify.add_argument("--json", action="store_true",
                          help="alias for --format json (backwards compatible)")
    p_verify.add_argument("--output", metavar="FILE",
                          help="write SARIF output to FILE instead of stdout "
                               "(used with --format sarif)")
    p_verify.add_argument("--lang", choices=sorted(_LANG_EXT),
                          help="force language for stdin input")

    p_rules = sub.add_parser("rules", help="list qcheck's rule catalog")
    p_rules.add_argument("--json", action="store_true",
                         help="emit the rule catalog as JSON (for agents/CI)")

    args = parser.parse_args(argv)
    if args.command == "rules":
        return _run_rules(args)
    if args.command != "verify":
        parser.print_help()
        return EXIT_INTERNAL

    # Resolve format. --format wins when given; --json is a backwards-compatible
    # alias; default stays human. Exit codes never depend on the format.
    if args.format is not None:
        fmt = args.format
    elif args.json:
        fmt = "json"
    else:
        fmt = "human"
    emit_json = fmt == "json"

    targets = _expand_targets(args.paths)
    if not targets:
        print("qcheck: no .py or .qasm files found.", file=sys.stderr)
        return EXIT_PASS

    stdin_text = sys.stdin.read() if "-" in targets else None
    units = [_verify_one(t, args.lang, stdin_text) for t in targets]

    # SARIF: a single-run document over all units, regardless of count.
    if fmt == "sarif":
        doc = build_sarif(
            [(d, r) for (d, r, e) in units if r is not None],
            execution_successful=all(e is None for (_d, _r, e) in units))
        text = json.dumps(doc, indent=2)
        if args.output:
            with open(args.output, "w", encoding="utf-8") as fh:
                fh.write(text + "\n")
        else:
            print(text)
        return _worst_exit(units)

    # Single unit -> preserve legacy output + exit code exactly.
    if len(units) == 1:
        display, report, err = units[0]
        if err is not None:
            print(f"qcheck: {err}", file=sys.stderr)
            return EXIT_INTERNAL
        if emit_json:
            print(json.dumps(report.to_dict(), indent=2))
        else:
            _print_human(report, display)
        return _exit_code(report)

    # Aggregate over multiple units.
    results, worst = [], EXIT_PASS
    passed = failed = unsafe = err_count = 0
    for display, report, err in units:
        if err is not None:
            err_count += 1
            worst = max(worst, EXIT_INTERNAL)
            results.append({"path": display, "error": err})
            if not emit_json:
                print(f"  [ERROR] {display}: {err}")
            continue
        rc = _exit_code(report)
        worst = EXIT_UNSAFE if EXIT_UNSAFE in (worst, rc) else max(worst, rc)
        if report.unsafe:
            unsafe += 1
        elif report.status == "fail":
            failed += 1
        else:
            passed += 1
        if emit_json:
            d = report.to_dict()
            d["path"] = display
            results.append(d)
        else:
            icon = "UNSAFE" if report.unsafe else {"pass": "PASS", "warning": "WARN", "fail": "FAIL"}[report.status]
            errs = len(report.errors)
            print(f"  [{icon}] {display} ({report.framework})"
                  + (f"  {errs} error(s)" if errs else ""))

    summary = {"files": len(units), "passed": passed, "failed": failed,
               "unsafe": unsafe, "read_errors": err_count}
    if emit_json:
        print(json.dumps({"qcheck_version": __version__, "results": results,
                          "summary": summary}, indent=2))
    else:
        print(f"qcheck {__version__}: {summary['files']} file(s) - "
              f"{passed} passed, {failed} failed, {unsafe} unsafe"
              + (f", {err_count} unreadable" if err_count else ""))
    return worst


if __name__ == "__main__":
    sys.exit(main())
