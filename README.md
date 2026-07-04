# qcheck

**AI writes quantum code. qcheck reviews it.**

`qcheck` is a lightweight review layer for AI-generated Qiskit and OpenQASM
snippets. It catches common issues early - removed-in-1.0 APIs, unsafe patterns,
missing measurements, parse errors - so agents and developers can improve quantum
code before it reaches humans, CI, or simulators. Tiny, dependency-free, and it
reviews code without ever executing it.

Why it matters: LLMs write quantum code that fails to run **40-70% of the time**
one-shot (QuanBench+ 2026: Qiskit 59.5% / PennyLane 42.9% pass; QCoder 2026: ~70%
one-shot failure). qcheck catches the avoidable share of that early.

```bash
qcheck verify circuit.qasm
qcheck verify snippet.py --json
```

## Why this exists

An LLM agent (or a developer pasting from a chat assistant) produces a Qiskit/QASM snippet.
Will it run? Is it using an API that was removed in Qiskit 1.0? Does it measure?
Is it even safe to touch? Today you find out by running it - wasting time, and
in an agent loop, running untrusted model output. `qcheck` answers in
milliseconds, statically.

## Install

```bash
pip install qcheck-quantum
```

The PyPI **distribution** name is `qcheck-quantum` (the bare `qcheck` name is
taken on PyPI); the installed **command** and the import package are both
`qcheck`. v0 has **zero runtime dependencies** (standard library only).

To work on qcheck itself, install from source:

```bash
git clone https://github.com/JCQuankey/qcheck && cd qcheck
pip install -e ".[dev]"     # editable install + pytest
```

Release process: [`docs/RELEASING.md`](https://github.com/JCQuankey/qcheck/blob/main/docs/RELEASING.md).

## Quickstart

```bash
qcheck verify examples/broken_qiskit_execute.py   # one file
qcheck verify examples/                            # a whole directory (recursive)
qcheck verify a.py b.qasm circuits/                # several paths at once
cat snippet.py | qcheck verify -                   # stdin (for agents)
```

Example output:

```
qcheck 0.4.0  [FAIL]  examples/broken_qiskit_execute.py  (qiskit)
  [error] QISKIT-REMOVED-IMPORT: 'from qiskit import execute' was removed in Qiskit 1.0
  [warning] QISKIT-DEPRECATED-GATE: QuantumCircuit.cnot() is deprecated; use .cx().
  fix -> Replace execute() with a primitive (Sampler/Estimator) or backend.run().
```

Reviewing multiple files prints a per-file summary and exits with the worst
result found (unsafe > failed > passed). Directory recursion skips virtualenvs,
VCS, caches, and build output (`.venv`, `node_modules`, `.git`, `site-packages`,
`build`, `dist`, ...) so it reviews your code, not your dependencies. To review a
file inside one of those, pass it explicitly.

## JSON output (for agents & CI)

```bash
qcheck verify snippet.py --json
```

For a single file, returns `{status, framework, syntax_valid, unsafe,
static_checks, errors, warnings, suggested_fixes, confidence,
runnable_in_simulator, qcheck_version}`. For multiple files or a directory,
returns an envelope `{qcheck_version, results: [<per-file object + "path">...],
summary: {files, passed, failed, unsafe, read_errors}}`. Designed to be parsed by
an LLM agent that just generated the code, or by a CI gate. Exit codes: `0` pass,
`1` verification failed, `2` unsafe/unsupported, `3` internal error.

## Use it in CI (GitHub Action)

qcheck ships a composite GitHub Action. In your repo's
`.github/workflows/qcheck.yml`:

```yaml
- uses: actions/checkout@v4
- uses: JCQuankey/qcheck@v0.4.0
  with:
    paths: "."     # or a folder, e.g. "circuits/"
```

The step fails the job when qcheck finds errors or unsafe code. See
[`examples/github-action.yml`](https://github.com/JCQuankey/qcheck/blob/main/examples/github-action.yml).

## SARIF output (GitHub Code Scanning)

qcheck can emit SARIF 2.1.0 so findings show up as **code scanning alerts** on
the Security tab and inline on pull requests, instead of only in the log:

```bash
qcheck verify . --format sarif --output qcheck.sarif
```

In a workflow, generate the SARIF and let the caller upload it (upload needs
`security-events: write`, best granted by the consuming repo):

```yaml
permissions:
  contents: read
  security-events: write
steps:
  - uses: actions/checkout@v4
  - uses: JCQuankey/qcheck@v0.4.0
    with:
      format: sarif
      output: qcheck.sarif
  - uses: github/codeql-action/upload-sarif@v3
    with:
      sarif_file: qcheck.sarif
```

SARIF reports static qcheck findings (rule id, level, file, line). `stdin` input
uses a synthetic `stdin` URI and is not meant for code-scanning upload.

## Rule catalog (explain your findings)

qcheck ships **30 rules**, and every finding carries a **stable rule id** (for
example `QISKIT-REMOVED-IMPORT`). Each id is backed by catalog metadata - a
title, category, default severity, a plain-language summary, why it matters, and
a recommended next step - so a developer or an agent can act on a finding right
away and triage faster.

Browse the catalog from the CLI:

```bash
qcheck rules            # table: id, level, category, summary
qcheck rules --json     # full metadata, for agents and CI
```

The same metadata enriches SARIF `driver.rules[]`, so code-scanning alerts show
each rule's description, severity and guidance inline. Rule ids are stable across
releases, which keeps CI gates and agent loops consistent as qcheck grows.

qcheck's JSON, `qcheck rules --json`, SARIF and exit codes are documented as
stable output contracts for agents and CI in [`docs/CONTRACTS.md`](https://github.com/JCQuankey/qcheck/blob/main/docs/CONTRACTS.md).

## What v0 checks

**OpenQASM 2/3:** missing header, undeclared, duplicate and zero-sized
registers, index-out-of-range, malformed measurements, missing measurement,
two-qubit gates on a single qubit, OpenQASM 2/3 syntax mismatches, unsupported
includes, suspicious non-QASM content.
**Qiskit Python:** Python syntax, missing `QuantumCircuit` import, zero-qubit
circuits, qubit/classical-bit indices out of range, `measure()` with no
classical bits, two-qubit gates on one qubit, missing measurement,
`get_counts()` on an unmeasured circuit, and Qiskit-1.0 breaking changes LLMs
still emit (`execute()`, `assemble()`, `from qiskit import Aer/execute`,
deprecated gate aliases like `cnot`->`cx`).

Run `qcheck rules` to see the full catalog with guidance for each rule.

## Safety policy

`qcheck` **never executes the input.** Qiskit snippets are analyzed with the
Python `ast` module (parse, don't run). Any filesystem/network/process/dynamic-
exec construct (`os`, `subprocess`, `eval`, `open`, ...) marks the snippet
**unsafe** and exits `2`. QASM input is text-scanned. This is deliberate: an
agent-facing verifier that *ran* untrusted model output would be a remote-code-
execution vector (see Qiskit CVE-2025-2000 for the QPY/pickle precedent). See
[`SECURITY.md`](https://github.com/JCQuankey/qcheck/blob/main/SECURITY.md) for the full threat model.

## Scope

qcheck v0 focuses on static review signals for Qiskit and OpenQASM: API usage
(including Qiskit 1.0 removals), unsafe patterns, missing measurements, parse
issues, and common LLM-generated mistakes. It reviews code without executing it,
so it's safe to run on untrusted model output inside an agent loop or CI.

It's a fast first-pass reviewer - pair it with your tests and simulators for the
rest. For methodology and scope details, see the
[leaderboard methodology](https://github.com/JCQuankey/qcheck/blob/main/leaderboard/methodology.md).

## Roadmap

- v0 (shipped, on PyPI): CLI, Qiskit + OpenQASM static checks, JSON + SARIF output, safety screen, GitHub Action. **Zero runtime deps.**
- Next: PennyLane + Cirq, more rules with a documented rule catalog, LLM-powered fix suggestions, MCP server (`verify_quantum_code`), sandboxed simulation (opt-in).
- Public **static-check leaderboard** for LLM-generated quantum code (see `leaderboard/`) + anonymized error dataset.

## Leaderboard

qcheck includes a **static review benchmark** for AI-generated quantum code: it
tracks how often model outputs pass qcheck's current review checks
(`static_pass_rate`) on a small public Qiskit/OpenQASM task set - an early quality
signal for agents and LLM workflows. The rows shown today are labelled **SAMPLE/demo**.

- [`leaderboard/README.md`](https://github.com/JCQuankey/qcheck/blob/main/leaderboard/README.md) - how to add a submission and run it
- [`leaderboard/methodology.md`](https://github.com/JCQuankey/qcheck/blob/main/leaderboard/methodology.md) - scope and methodology
- [`leaderboard/site/leaderboard.md`](https://github.com/JCQuankey/qcheck/blob/main/leaderboard/site/leaderboard.md) - the generated table

## Contributing

Issues and PRs welcome - especially new failure fixtures (a real LLM-generated
snippet that should fail but currently passes, or vice versa). Each fixture
makes qcheck sharper and feeds the public error taxonomy.

## Contact

- Technical questions / maintainer contact: **dev@quankey.xyz**
- Security issues: **security@quankey.xyz** (see [`SECURITY.md`](https://github.com/JCQuankey/qcheck/blob/main/SECURITY.md))

Maintained by JCQuankey / qcheck contributors. qcheck runs locally, sends no
telemetry, and reviews code without executing it.

## License

Apache-2.0.
