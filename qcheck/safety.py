"""Static safety screen for Python snippets, using the stdlib `ast` module.

qcheck NEVER executes the input. This module only inspects the parsed AST and
flags constructs that would let an untrusted snippet touch the filesystem,
network, processes, or dynamic code execution. If any are present the snippet is
marked unsafe and qcheck refuses to treat it as a benign circuit.
"""
from __future__ import annotations

import ast
from typing import List

from .report import Finding

UNSAFE_MODULES = {
    "os", "sys", "subprocess", "shutil", "socket", "requests", "urllib",
    "http", "ctypes", "pickle", "marshal", "importlib", "pty", "signal",
    "multiprocessing", "threading", "asyncio", "pathlib", "glob", "tempfile",
}

UNSAFE_BUILTINS = {"eval", "exec", "compile", "__import__", "open", "input"}

UNSAFE_ATTRS = {
    "system", "popen", "spawn", "spawnl", "spawnv", "call", "run", "Popen",
    "remove", "rmtree", "unlink", "rename", "chmod", "chown", "kill",
    "connect", "urlopen", "get", "post", "request", "load", "loads",
}


def scan_python_safety(tree: ast.AST) -> List[Finding]:
    findings: List[Finding] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                root = alias.name.split(".")[0]
                if root in UNSAFE_MODULES:
                    findings.append(Finding(
                        "PY-UNSAFE-IMPORT", "error",
                        f"Unsafe import '{alias.name}' is not allowed in quantum "
                        f"code; qcheck rejects it as a potential RCE vector.",
                        getattr(node, "lineno", None)))
        elif isinstance(node, ast.ImportFrom):
            root = (node.module or "").split(".")[0]
            if root in UNSAFE_MODULES:
                findings.append(Finding(
                    "PY-UNSAFE-IMPORT", "error",
                    f"Unsafe import 'from {node.module} import ...' is not allowed.",
                    getattr(node, "lineno", None)))
        elif isinstance(node, ast.Call):
            func = node.func
            if isinstance(func, ast.Name) and func.id in UNSAFE_BUILTINS:
                findings.append(Finding(
                    "PY-UNSAFE-CALL", "error",
                    f"Unsafe call '{func.id}(...)' is not allowed.",
                    getattr(node, "lineno", None)))
            elif isinstance(func, ast.Attribute) and func.attr in UNSAFE_ATTRS:
                findings.append(Finding(
                    "PY-UNSAFE-CALL", "error",
                    f"Unsafe call '.{func.attr}(...)' is not allowed.",
                    getattr(node, "lineno", None)))
    return findings
