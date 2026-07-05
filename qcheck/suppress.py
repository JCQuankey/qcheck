"""Finding suppression: inline `qcheck: ignore[...]` comments and --disable.

Two operator-facing mechanisms, both opt-in and both counted (never silent):

- Inline, line-scoped: `# qcheck: ignore[RULE-ID]` (Python) or
  `// qcheck: ignore[RULE-ID]` (OpenQASM), with one or more comma-separated
  rule IDs. The directive suppresses only findings reported on that same
  line, and the rule IDs are mandatory - there is no bare `ignore`.
- Run-wide: `--disable RULE-ID` (repeatable, comma lists accepted) from the
  CLI. This is the operator speaking, not the code under review.

Safety-critical rules are never suppressible by either mechanism: inline
directives live inside the very untrusted, often AI-generated code qcheck
exists to review, so the safety screen cannot be waived from in-band. The
`UNSUPPORTED` input gate may be disabled from the CLI (the escape hatch for
scanning mixed repos) but not from inline comments.
"""
from __future__ import annotations

import re
from typing import Dict, FrozenSet

from .report import Report

# Never suppressible, by either mechanism. These are the rules that keep
# untrusted input from silently passing the safety screen.
UNSUPPRESSIBLE: FrozenSet[str] = frozenset({
    "PY-UNSAFE-IMPORT", "PY-UNSAFE-CALL", "QASM-SUSPICIOUS",
})

# Suppressible only via --disable (operator-side), never inline.
CLI_ONLY: FrozenSet[str] = frozenset({"UNSUPPORTED"})

# `# qcheck: ignore[ID]` or `// qcheck: ignore[ID, ID2]`. IDs are mandatory.
_INLINE = re.compile(
    r"(?:#|//)\s*qcheck:\s*ignore\[([A-Za-z0-9\-_,\s]+)\]")


def inline_ignores(text: str) -> Dict[int, FrozenSet[str]]:
    """Map 1-based line number -> rule IDs ignored on that line."""
    out: Dict[int, FrozenSet[str]] = {}
    for n, line in enumerate(text.splitlines(), start=1):
        m = _INLINE.search(line)
        if m:
            ids = frozenset(p.strip().upper()
                            for p in m.group(1).split(",") if p.strip())
            if ids:
                out[n] = ids
    return out


def apply_suppressions(report: Report, text: str,
                       disabled: FrozenSet[str] = frozenset(),
                       no_inline: bool = False) -> Report:
    """Filter suppressed findings out of `report`, counting what was dropped.

    Mutates and returns `report`: `findings` keeps only unsuppressed entries
    and `suppressed` records how many were dropped. Status, errors/warnings,
    confidence and exit codes all derive from `findings`, so every output
    format stays consistent automatically.
    """
    ignores = {} if no_inline else inline_ignores(text)
    if not ignores and not disabled:
        return report

    kept = []
    dropped = 0
    for f in report.findings:
        if f.id in UNSUPPRESSIBLE:
            kept.append(f)
            continue
        if f.id in disabled:
            dropped += 1
            continue
        if f.id not in CLI_ONLY and f.line is not None \
                and f.id in ignores.get(f.line, frozenset()):
            dropped += 1
            continue
        kept.append(f)
    report.findings = kept
    report.suppressed += dropped
    return report
