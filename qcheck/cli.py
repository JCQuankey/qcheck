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
import sys
from typing import List, Optional

from . import __version__
from .detect import detect_framework
from .report import Report
from .checks_qasm import check_qasm
from .checks_qiskit import check_qiskit
from .safety import scan_python_safety

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


def main(argv: Optional[List[str]] = None) -> int:
    parser = argparse.ArgumentParser(
        prog="qcheck",
        description="Verify LLM-generated quantum code (Qiskit / OpenQASM).")
    parser.add_argument("--version", action="version",
                        version=f"qcheck {__version__}")
    sub = parser.add_subparsers(dest="command")
    p_verify = sub.add_parser("verify", help="verify a .qasm or .py file")
    p_verify.add_argument("file")
    p_verify.add_argument("--json", action="store_true",
                          help="emit machine-readable JSON (for agents/CI)")

    args = parser.parse_args(argv)

    if args.command != "verify":
        parser.print_help()
        return EXIT_INTERNAL

    try:
        with open(args.file, "r", encoding="utf-8") as fh:
            text = fh.read()
    except OSError as e:
        print(f"qcheck: cannot read {args.file}: {e}", file=sys.stderr)
        return EXIT_INTERNAL

    try:
        report = verify_text(args.file, text)
    except Exception as e:  # never crash on bad input -> internal error code
        print(f"qcheck: internal error: {e}", file=sys.stderr)
        return EXIT_INTERNAL

    if args.json:
        print(json.dumps(report.to_dict(), indent=2))
    else:
        _print_human(report, args.file)

    return _exit_code(report)


if __name__ == "__main__":
    sys.exit(main())
