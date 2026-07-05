"""Static safety screen for Python snippets, using the stdlib `ast` module.

qcheck NEVER executes the input. This module only inspects the parsed AST and
flags constructs that would let an untrusted snippet touch the filesystem,
network, processes, or dynamic code execution. If any are present the snippet is
marked unsafe and qcheck refuses to treat it as a benign circuit.

Attribute calls are receiver-aware: `.run(...)` / `.get(...)` style calls are
flagged only when the receiver is a name bound to an unsafe module import
(`subprocess.run(...)`, `import subprocess as sp; sp.run(...)`), so benign
quantum code such as `backend.run(circuit)` or `counts.get(key)` is not
reported. The unsafe import itself is always flagged, which keeps the screen
closed against aliasing tricks: any path to an unsafe module starts with an
import, and that import already marks the snippet unsafe.

The screen is a denylist, not a sandbox: it raises the bar against the common
indirect-access tricks below, but a determined snippet can still find gaps.
Anything that must actually EXECUTE untrusted output needs OS-level containment,
not this static check.
"""
from __future__ import annotations

import ast
from typing import List

from .report import Finding

UNSAFE_MODULES = {
    "os", "sys", "subprocess", "shutil", "socket", "requests", "urllib",
    "http", "ctypes", "pickle", "marshal", "importlib", "pty", "signal",
    "multiprocessing", "threading", "asyncio", "pathlib", "glob", "tempfile",
    # `builtins` gives back open/eval/exec/__import__ etc. and is never needed
    # in a quantum snippet; importing it is an indirect-access red flag.
    "builtins",
}

UNSAFE_BUILTINS = {"eval", "exec", "compile", "__import__", "open", "input"}

UNSAFE_ATTRS = {
    "system", "popen", "spawn", "spawnl", "spawnv", "call", "run", "Popen",
    "remove", "rmtree", "unlink", "rename", "chmod", "chown", "kill",
    "connect", "urlopen", "get", "post", "request", "load", "loads",
}

# Symbols that must never be reached through the builtins namespace
# (`__builtins__['open']`, `builtins.system`, `getattr(__builtins__, 'eval')`).
_DANGEROUS_VIA_BUILTINS = UNSAFE_BUILTINS | UNSAFE_ATTRS
# Names that denote the builtins namespace itself.
_BUILTINS_NS_NAMES = {"__builtins__", "__builtin__"}


def _const_str(node):
    return node.value if isinstance(node, ast.Constant) and isinstance(node.value, str) else None


def scan_python_safety(tree: ast.AST) -> List[Finding]:
    findings: List[Finding] = []

    # Pass 1: imports. Record which local names are bound to unsafe modules
    # (module aliases) and which names were imported FROM unsafe modules,
    # so the call pass below can resolve receivers. Order-independent.
    unsafe_aliases: set = set()     # `import os` -> "os"; `import subprocess as sp` -> "sp"
    unsafe_names: set = set()       # `from os import system` -> "system"
    builtins_aliases: set = set(_BUILTINS_NS_NAMES)   # names denoting builtins ns
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
                    unsafe_aliases.add(alias.asname or root)
                    if root in ("builtins", "__builtin__"):
                        builtins_aliases.add(alias.asname or root)
        elif isinstance(node, ast.ImportFrom):
            root = (node.module or "").split(".")[0]
            if root in UNSAFE_MODULES:
                findings.append(Finding(
                    "PY-UNSAFE-IMPORT", "error",
                    f"Unsafe import 'from {node.module} import ...' is not allowed.",
                    getattr(node, "lineno", None)))
                for alias in node.names:
                    unsafe_names.add(alias.asname or alias.name)

    def _is_builtins_ns(n) -> bool:
        return isinstance(n, ast.Name) and n.id in builtins_aliases

    # Pass 2: calls and indirect builtins-namespace access.
    for node in ast.walk(tree):
        line = getattr(node, "lineno", None)

        # Indirect access to a dangerous builtin through the builtins namespace:
        #   __builtins__['open'](...)   builtins.system   __builtin__.eval
        if isinstance(node, ast.Subscript) and _is_builtins_ns(node.value):
            key = _const_str(node.slice)
            if key is None or key in _DANGEROUS_VIA_BUILTINS:
                findings.append(Finding(
                    "PY-UNSAFE-CALL", "error",
                    "Unsafe indirect access to the builtins namespace "
                    "(__builtins__[...]) is not allowed.", line))
            continue
        if isinstance(node, ast.Attribute) and _is_builtins_ns(node.value):
            if node.attr in _DANGEROUS_VIA_BUILTINS:
                findings.append(Finding(
                    "PY-UNSAFE-CALL", "error",
                    f"Unsafe indirect access '{node.attr}' via the builtins "
                    f"namespace is not allowed.", line))
            continue

        if not isinstance(node, ast.Call):
            continue
        func = node.func

        # getattr(__builtins__, 'open') / getattr(builtins, 'system')
        if isinstance(func, ast.Name) and func.id == "getattr" \
                and node.args and _is_builtins_ns(node.args[0]):
            key = _const_str(node.args[1]) if len(node.args) > 1 else None
            if key is None or key in _DANGEROUS_VIA_BUILTINS:
                findings.append(Finding(
                    "PY-UNSAFE-CALL", "error",
                    "Unsafe getattr() on the builtins namespace is not allowed.",
                    line))
                continue

        if isinstance(func, ast.Name):
            if func.id in UNSAFE_BUILTINS:
                findings.append(Finding(
                    "PY-UNSAFE-CALL", "error",
                    f"Unsafe call '{func.id}(...)' is not allowed.", line))
            elif func.id in unsafe_names:
                findings.append(Finding(
                    "PY-UNSAFE-CALL", "error",
                    f"Unsafe call '{func.id}(...)' (imported from an unsafe "
                    f"module) is not allowed.", line))
        elif isinstance(func, ast.Attribute) and func.attr in UNSAFE_ATTRS \
                and isinstance(func.value, ast.Name) \
                and func.value.id in unsafe_aliases:
            findings.append(Finding(
                "PY-UNSAFE-CALL", "error",
                f"Unsafe call '{func.value.id}.{func.attr}(...)' is not allowed.",
                line))
    return findings
