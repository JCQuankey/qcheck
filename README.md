# qcheck

**AI writes quantum code. qcheck reviews it.**

`qcheck` is a lightweight review layer for AI-generated Qiskit and OpenQASM
snippets. It catches common issues early — removed-in-1.0 APIs, unsafe patterns,
missing measurements, parse errors — so agents and developers can improve quantum
code before it reaches humans, CI, or simulators. Tiny, dependency-free, and it
reviews code without ever executing it.

Why it matters: LLMs write quantum code that fails to run **40–70% of the time**
one-shot (QuanBench+ 2026: Qiskit 59.5% / PennyLane 42.9% pass; QCoder 2026: ~70%
one-shot failure). qcheck catches the avoidable share of that early.

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

## Scope

qcheck v0 focuses on static review signals for Qiskit and OpenQASM: API usage
(including Qiskit 1.0 removals), unsafe patterns, missing measurements, parse
issues, and common LLM-generated mistakes. It reviews code without executing it,
so it's safe to run on untrusted model output inside an agent loop or CI.

It's a fast first-pass reviewer — pair it with your tests and simulators for the
rest. For methodology and scope details, see the
[leaderboard methodology](leaderboard/methodology.md).

## Roadmap

- v0 (this): CLI, Qiskit + OpenQASM static checks, JSON, safety screen. **Zero runtime deps.**
- v1: sandboxed simulation (opt-in), PennyLane + Cirq, LLM-powered fix suggestions, GitHub Action, MCP server (`verify_quantum_code`).
- Public **static-check leaderboard** for LLM-generated quantum code (see `leaderboard/`) + anonymized error dataset.

## Leaderboard

qcheck includes a **static review benchmark** for AI-generated quantum code: it
tracks how often model outputs pass qcheck's current review checks
(`static_pass_rate`) on a small public Qiskit/OpenQASM task set — an early quality
signal for agents and LLM workflows. The rows shown today are labelled **SAMPLE/demo**.

- [`leaderboard/README.md`](leaderboard/README.md) — how to add a submission and run it
- [`leaderboard/methodology.md`](leaderboard/methodology.md) — scope and methodology
- [`leaderboard/site/leaderboard.md`](leaderboard/site/leaderboard.md) — the generated table

## Contributing

Issues and PRs welcome — especially new failure fixtures (a real LLM-generated
snippet that should fail but currently passes, or vice versa). Each fixture
makes qcheck sharper and feeds the public error taxonomy.

## Contact

- Technical questions / maintainer contact: **dev@quankey.xyz**
- Security issues: **security@quankey.xyz** (see [`SECURITY.md`](SECURITY.md))

Maintained by JCQuankey / qcheck contributors. qcheck runs locally, sends no
telemetry, and reviews code without executing it.

## License

Apache-2.0.
