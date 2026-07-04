# Security Policy

## Threat model

qcheck's input is **untrusted, model-generated code**. The dominant risk for any
verifier is that *executing* that code turns the tool into a remote-code-execution
(RCE) vector — the class of bug behind Qiskit CVE-2025-2000 (QPY/pickle
deserialization). An agent calling a verifier in a loop would amplify this.

## How qcheck v0 avoids executing untrusted code

- **qcheck never executes the input.** There is no `exec`, `eval`, or import of
  the analyzed snippet.
- **Qiskit / Python** files are parsed with the standard-library `ast` module
  (parse tree only). A safety screen flags any filesystem / network / process /
  dynamic-exec construct (`os`, `subprocess`, `eval`, `exec`, `open`, `socket`,
  `importlib`, …) and marks the snippet **unsafe** (exit code `2`) before any
  further analysis. Every `.py` is screened, even if it does not look like
  quantum code.
- **OpenQASM** is text-scanned (regex), never interpreted.
- **No pickle / QPY / dill input is accepted** — those are the deserialization
  RCE formats.
- v0 has **zero runtime dependencies** (standard library only), minimizing the
  supply-chain surface.

## Rejected inputs

- Python snippets containing OS / network / process / dynamic-exec calls → `unsafe`, exit `2`.
- Serialized-object formats (pickle, QPY, dill) → not accepted.

## Data and telemetry

- qcheck runs entirely locally and **sends no code or data anywhere**. There is
  **no remote telemetry** in this release.
- No secrets are required to run qcheck, and none are stored in this repository.
- Any future opt-in telemetry would transmit only anonymized, non-reversible
  metadata (a salted structural hash + derived metrics), never raw code, paths,
  or prompts, and would be off by default.

## Not yet implemented

- **Sandboxed simulation** (running the parsed circuit — not arbitrary Python —
  inside a resource-limited, no-network subprocess) is planned for v1 and is
  **not present** in this release. v0 is static-only; `runnable_in_simulator` is
  always `not_run`.

## Reporting a vulnerability

Please report suspected vulnerabilities privately via a
[GitHub security advisory](https://github.com/JCQuankey/qcheck/security/advisories/new)
on this repository, or by opening a minimal issue that does **not** include
exploit details. We aim to acknowledge reports within a few business days.
Please do not disclose publicly until a fix is available.
