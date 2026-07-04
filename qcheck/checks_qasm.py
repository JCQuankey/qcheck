"""Lightweight static checks for OpenQASM 2/3, pure stdlib (regex + line scan).

Not a full parser. It catches the failure modes LLMs commonly produce: missing
header, undeclared registers, out-of-range indices, malformed measurements,
unsupported includes, and suspicious non-QASM content. One statement per line is
assumed (true for almost all generated QASM); spanning statements degrade to a
malformed-statement warning rather than a crash.
"""
from __future__ import annotations

import re
from typing import List, Tuple

from .report import Finding

_INDEXED = re.compile(r"([A-Za-z_][A-Za-z0-9_]*)\s*\[\s*(\d+)\s*\]")
_QREG2 = re.compile(r"^qreg\s+([A-Za-z_]\w*)\s*\[\s*(\d+)\s*\]$")
_CREG2 = re.compile(r"^creg\s+([A-Za-z_]\w*)\s*\[\s*(\d+)\s*\]$")
_QUBIT3 = re.compile(r"^qubit\s*\[\s*(\d+)\s*\]\s*([A-Za-z_]\w*)$")
_BIT3 = re.compile(r"^bit\s*\[\s*(\d+)\s*\]\s*([A-Za-z_]\w*)$")
_INCLUDE = re.compile(r'include\s+"([^"]+)"')
_SUSPICIOUS = re.compile(
    r"(import\s+os|subprocess|os\.system|__import__|<script|rm\s+-rf|eval\(|exec\(|;\s*rm\s)",
    re.IGNORECASE)
_SAFE_INCLUDES = {"qelib1.inc", "stdgates.inc"}


def check_qasm(text: str, framework: str) -> Tuple[bool, List[Finding], List[str]]:
    findings: List[Finding] = []
    fixes: List[str] = []
    qregs: dict[str, int] = {}
    cregs: dict[str, int] = {}
    header_seen = False
    saw_measure = False
    saw_gate = False

    def _dup(name: str, line: int) -> bool:
        if name in qregs or name in cregs:
            findings.append(Finding(
                "QASM-DUP-REGISTER", "error",
                f"Register {name!r} is declared more than once.", line))
            return True
        return False

    for i, raw in enumerate(text.split("\n"), start=1):
        line = raw.split("//", 1)[0].strip()
        if not line:
            continue

        if _SUSPICIOUS.search(line):
            findings.append(Finding(
                "QASM-SUSPICIOUS", "error",
                f"Suspicious non-QASM content on this line: {line[:50]!r}", i))
            continue

        if not line.endswith(";"):
            # Block openers (gate defs) end with { -- ignore those.
            if line.endswith("{") or line.endswith("}"):
                continue
            findings.append(Finding(
                "QASM-NO-SEMICOLON", "warning",
                "Statement does not end with ';' (possibly malformed or split "
                "across lines).", i))
            continue

        stmt = line[:-1].strip()
        low = stmt.lower()

        if low.startswith("openqasm"):
            header_seen = True
            continue
        if low.startswith("include"):
            m = _INCLUDE.search(stmt)
            inc = m.group(1) if m else ""
            if inc not in _SAFE_INCLUDES:
                findings.append(Finding(
                    "QASM-INCLUDE", "warning",
                    f"Unsupported/unknown include {inc!r}.", i))
            continue
        if low in ("", "qelib1.inc"):
            continue

        m = _QREG2.match(stmt)
        if m:
            _dup(m.group(1), i)
            qregs[m.group(1)] = int(m.group(2))
            continue
        m = _CREG2.match(stmt)
        if m:
            _dup(m.group(1), i)
            cregs[m.group(1)] = int(m.group(2))
            continue
        m = _QUBIT3.match(stmt)
        if m:
            if framework == "qasm2":
                findings.append(Finding(
                    "QASM-VERSION-MISMATCH", "warning",
                    "OpenQASM 3 declaration syntax ('qubit[n] name') in an "
                    "OpenQASM 2 program; use 'qreg name[n];' or switch the "
                    "header to 'OPENQASM 3.0;'.", i))
            _dup(m.group(2), i)
            qregs[m.group(2)] = int(m.group(1))
            continue
        m = _BIT3.match(stmt)
        if m:
            if framework == "qasm2":
                findings.append(Finding(
                    "QASM-VERSION-MISMATCH", "warning",
                    "OpenQASM 3 declaration syntax ('bit[n] name') in an "
                    "OpenQASM 2 program; use 'creg name[n];' or switch the "
                    "header to 'OPENQASM 3.0;'.", i))
            _dup(m.group(2), i)
            cregs[m.group(2)] = int(m.group(1))
            continue

        if low.startswith("gate ") or low.startswith("def "):
            continue  # custom gate / subroutine definition, skip in v0

        # measurement
        if "measure" in low:
            saw_measure = True
            _check_measure(stmt, qregs, cregs, i, findings, fixes)
            continue

        # generic gate application: validate every indexed register reference
        saw_gate = True
        _check_refs(stmt, qregs, cregs, i, findings, declared_required=True)

    if framework == "qasm2" and not header_seen:
        findings.insert(0, Finding(
            "QASM-NO-HEADER", "error",
            "Missing 'OPENQASM 2.0;' header.", 1))
        fixes.append("Add 'OPENQASM 2.0;' as the first line.")

    # Gates applied but nothing measured: sampling returns no classical result.
    if qregs and saw_gate and not saw_measure:
        findings.append(Finding(
            "QASM-NO-MEASURE", "warning",
            "Circuit applies gates but never measures; running it returns no "
            "classical result.", None))
        fixes.append("Add a measurement (e.g. 'measure q -> c;').")

    syntax_valid = not any(f.id in ("QASM-SUSPICIOUS",) for f in findings)
    return syntax_valid, findings, fixes


def _check_refs(stmt, qregs, cregs, line, findings, declared_required):
    for name, idx in _INDEXED.findall(stmt):
        idx = int(idx)
        if name in qregs:
            size = qregs[name]
        elif name in cregs:
            size = cregs[name]
        else:
            if declared_required:
                findings.append(Finding(
                    "QASM-UNDECLARED-REG", "error",
                    f"Register {name!r} used before declaration.", line))
            continue
        if idx >= size:
            findings.append(Finding(
                "QASM-INDEX-RANGE", "error",
                f"Index {name}[{idx}] out of range (register size {size}).", line))


def _check_measure(stmt, qregs, cregs, line, findings, fixes):
    # qasm2: measure q[i] -> c[j] ; qasm3: c[j] = measure q[i]
    if "->" in stmt:
        src, _, tgt = stmt.partition("->")
        src = src.replace("measure", "").strip()
        tgt = tgt.strip()
    elif "=" in stmt:
        tgt, _, src = stmt.partition("=")
        tgt = tgt.strip()
        src = src.replace("measure", "").strip()
    else:
        # bare `measure q;` broadcast -- accept, just validate refs
        _check_refs(stmt, qregs, cregs, line, findings, declared_required=True)
        return

    # source must be a qubit register, target a classical register
    for name, idx in _INDEXED.findall(src):
        idx = int(idx)
        if name not in qregs:
            findings.append(Finding(
                "QASM-MEASURE-SRC", "error",
                f"Measurement source {name!r} is not a declared qubit register.",
                line))
        elif idx >= qregs[name]:
            findings.append(Finding(
                "QASM-INDEX-RANGE", "error",
                f"Index {name}[{idx}] out of range (register size {qregs[name]}).",
                line))
    for name, idx in _INDEXED.findall(tgt):
        idx = int(idx)
        if name not in cregs:
            findings.append(Finding(
                "QASM-MEASURE-TGT", "error",
                f"Measurement target {name!r} is not a declared classical register.",
                line))
        elif idx >= cregs[name]:
            findings.append(Finding(
                "QASM-INDEX-RANGE", "error",
                f"Index {name}[{idx}] out of range (register size {cregs[name]}).",
                line))
