# qcheck

**Catch broken LLM-generated quantum code before you run it.**

LLMs write quantum code that fails to run **40–70% of the time** one-shot
(QuanBench+ 2026: Qiskit 59.5% / PennyLane 42.9% pass; QCoder 2026: ~70%
one-shot failure). `qcheck` is a tiny, dependency-free CLI that statically verifies
LLM-generated **Qiskit** and **OpenQASM** snippets and tells you what's wrong —
without ever executing the code.

```bash
qcheck verify circuit.qasm
qcheck verify snippet.py --json
```

## Why this exists

An LLM agent (or a developer pasting from a chat assistant) produces a Qiskit/QASM snippet.
Will it run? Is it using an API that was removed in Qiskit 1.0? Does it measure?
Is it even safe to touch? Today you find out by running it — wasting time, and
in an agent loop, running untrusted model output. `qcheck` answers in
milliseconds, statically.

## Install

```bash
# From PyPI (once published — distribution name is qcheck-quantum; the command is qcheck)
pip install qcheck-quantum

# From source (dev)
git clone https://github.com/JCQuankey/qcheck && cd qcheck
pip install -e ".[dev]"     # editable install + pytest
```

The PyPI **distribution** name is `qcheck-quantum` (the bare `qcheck` name was
already taken on PyPI by an unrelated project); the installed **command** is
`qcheck`. v0 has **zero runtime dependencies** (standard library only).

## Quickstart

```bash
qcheck verify examples/broken_qiskit_execute.py     # or: python3 -m qcheck verify <file>
```

Example output:

```
qcheck 0.1.0  [FAIL]  examples/broken_qiskit_execute.py  (qiskit)
  [error] QISKIT-REMOVED-IMPORT: 'from qiskit import execute' was removed in Qiskit 1.0
  [warning] QISKIT-DEPRECATED-GATE: QuantumCircuit.cnot() is deprecated; use .cx().
  fix -> Replace execute() with a primitive (Sampler/Estimator) or backend.run().
```

## JSON output (for agents & CI)

```bash
qcheck verify snippet.py --json
```

Returns `{status, framework, syntax_valid, unsafe, static_checks, errors,
warnings, suggested_fixes, confidence, runnable_in_simulator, qcheck_version}`.
Designed to be parsed by an LLM agent that just generated the code, or by a CI
gate. Exit codes: `0` pass, `1` verification failed, `2` unsafe/unsupported,
`3` internal error.

## What v0 checks

**OpenQASM 2/3:** missing header, undeclared registers, index-out-of-range,
malformed measurements, unsupported includes, suspicious non-QASM content.
**Qiskit Python:** Python syntax, missing `QuantumCircuit` import, missing
measurement, and Qiskit-1.0 breaking changes LLMs still emit (`execute()`,
`from qiskit import Aer/execute`, deprecated gate aliases like `cnot`→`cx`).

## Safety policy

`qcheck` **never executes the input.** Qiskit snippets are analyzed with the
Python `ast` module (parse, don't run). Any filesystem/network/process/dynamic-
exec construct (`os`, `subprocess`, `eval`, `open`, …) marks the snippet
**unsafe** and exits `2`. QASM input is text-scanned. This is deliberate: an
agent-facing verifier that *ran* untrusted model output would be a remote-code-
execution vector (see Qiskit CVE-2025-2000 for the QPY/pickle precedent). See
[`SECURITY.md`](SECURITY.md) for the full threat model.

## What qcheck is NOT

Not a quantum framework. Not a QPU runner. Not an optimizer. It does one thing:
tell you whether LLM-generated quantum code is well-formed, modern, safe, and
likely to run.

## Roadmap

- v0 (this): CLI, Qiskit + OpenQASM static checks, JSON, safety screen. **Zero runtime deps.**
- v1: sandboxed simulation (opt-in), PennyLane + Cirq, LLM-powered fix suggestions, GitHub Action, MCP server (`verify_quantum_code`).
- Public **"Which LLM writes correct quantum code?"** leaderboard (see `leaderboard/`) + anonymized error dataset.

## Leaderboard

qcheck includes an experimental benchmark scaffold:
**"Which LLM writes correct quantum code?"**

It currently measures the static qcheck pass/fail/unsafe verdict on small
Qiskit/OpenQASM tasks. It does **not** prove semantic correctness or hardware
performance. The only results today are clearly-labelled SAMPLE demos.

- [`leaderboard/README.md`](leaderboard/README.md) — how to add a submission and run it
- [`leaderboard/methodology.md`](leaderboard/methodology.md) — scope and limitations
- [`leaderboard/site/leaderboard.md`](leaderboard/site/leaderboard.md) — the generated table

## Contributing

Issues and PRs welcome — especially new failure fixtures (a real LLM-generated
snippet that should fail but currently passes, or vice versa). Each fixture
makes qcheck sharper and feeds the public error taxonomy.

## Contact

- Technical questions / maintainer contact: **dev@quankey.xyz**
- Security issues: **security@quankey.xyz** (see [`SECURITY.md`](SECURITY.md))

Maintained by JCQuankey / qcheck contributors. qcheck runs locally, has no remote
telemetry, and does not execute untrusted Python in v0.

## License

Apache-2.0.
