"""Report and Finding data structures + status/confidence logic.

Pure stdlib (dataclasses) so qcheck v0 installs with zero runtime dependencies.
"""
from __future__ import annotations

from dataclasses import dataclass, asdict, field
from typing import List, Optional

from . import __version__


@dataclass
class Finding:
    id: str            # stable check id, e.g. "QASM-UNDECLARED-REG"
    level: str         # "error" | "warning" | "info"
    message: str
    line: Optional[int] = None


@dataclass
class Report:
    framework: str
    syntax_valid: bool
    findings: List[Finding] = field(default_factory=list)
    suggested_fixes: List[str] = field(default_factory=list)
    unsafe: bool = False
    # Count of findings dropped by suppression (inline ignores / --disable).
    # Additive field: 0 means nothing was suppressed.
    suppressed: int = 0
    # v0 does NOT execute code. This field documents that explicitly.
    runnable_in_simulator: str = "not_run"
    runnable_reason: str = (
        "qcheck v0 performs static verification only; it never executes the "
        "input. Simulator execution is deferred to a sandboxed v1 (see SECURITY.md)."
    )

    @property
    def errors(self) -> List[Finding]:
        return [f for f in self.findings if f.level == "error"]

    @property
    def warnings(self) -> List[Finding]:
        return [f for f in self.findings if f.level == "warning"]

    @property
    def status(self) -> str:
        if not self.syntax_valid or self.errors:
            return "fail"
        if self.warnings:
            return "warning"
        return "pass"

    @property
    def confidence(self) -> float:
        """Deterministic rubric: high when it parses cleanly with no findings."""
        c = 1.0 - 0.4 * len(self.errors) - 0.1 * len(self.warnings)
        if not self.syntax_valid:
            c = min(c, 0.2)
        return round(max(0.0, min(1.0, c)), 2)

    def to_dict(self) -> dict:
        return {
            "qcheck_version": __version__,
            "status": self.status,
            "framework": self.framework,
            "syntax_valid": self.syntax_valid,
            "unsafe": self.unsafe,
            "runnable_in_simulator": self.runnable_in_simulator,
            "runnable_reason": self.runnable_reason,
            "static_checks": [asdict(f) for f in self.findings],
            "errors": [asdict(f) for f in self.errors],
            "warnings": [asdict(f) for f in self.warnings],
            "suggested_fixes": self.suggested_fixes,
            "suppressed": self.suppressed,
            "confidence": self.confidence,
        }
