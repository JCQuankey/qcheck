# Methodology

This document is deliberately modest. The leaderboard is an MVP that measures a
narrow, honest thing well, rather than a broad thing badly.

## At a glance

- **Metric:** `static_pass_rate` — the fraction of tasks whose output passes
  qcheck's current static review checks (well-formed, modern APIs, declared
  registers, in-range indices, has a measurement, no unsafe constructs).
- **What it's useful for:** comparing avoidable code-quality failures across a
  small public task set — an early review signal for agents and LLM workflows.
- **How to read it:** as an early review signal, not as a full evaluation of
  quantum algorithm quality (it reviews code without executing it).
- **Current task set:** small, early, and subject to change.
- **Current rows:** SAMPLE/demo unless explicitly marked real.

## Benchmark scope

Each task asks a model to produce a small Qiskit or OpenQASM snippet. Each
submission is scored by **qcheck static verification** into one verdict:
`pass` / `fail` / `unsafe` (plus `error` if the file cannot be read/parsed).

**In scope (what we score):** is the generated code well-formed, using modern
(non-removed) APIs, free of unsafe filesystem/network/process constructs, and
therefore *likely to run*.

**Out of scope (explicitly not measured):**
- Semantic / algorithmic correctness — "runs but produces the wrong state".
- Quantum advantage or any performance claim.
- Mathematical proof of correctness.
- Hardware / QPU behavior.
- Production readiness.

A model can score 100% here and still write the wrong algorithm. Static passing
is necessary, not sufficient.

## Task selection

Six small tasks at launch (four Qiskit, two OpenQASM), covering the failure modes
qcheck v0 actually detects: removed Qiskit 1.0 APIs, missing imports/measurement,
undeclared registers, out-of-range indices, and unsafe side effects. Tasks are
kept intentionally small and are stored as JSON in `tasks/`. Each task's
`expected_features` field is **human-readable intent for future semantic
grading and is not auto-verified in v0**.

## Evaluation process

1. `evaluate_submission.py` scans a `submissions/<model>/` directory.
2. For each `.py` / `.qasm` file it calls `qcheck.verify_text` — which parses the
   code with Python's `ast` (or text-scans QASM) and **never executes it**.
3. Files are mapped to task ids by filename stem where possible.
4. Results aggregate to `tasks_attempted`, `tasks_passed`, `pass_rate`,
   `unsafe_count`, and a per-file breakdown, stamped with the qcheck version.
5. `build_leaderboard.py` renders the result JSONs into a sorted Markdown table
   and a static HTML page.

## Static vs semantic checks

v0 is static-only. Semantic grading (running the parsed circuit on a simulator
inside a sandbox to check the produced distribution) is planned for qcheck v1 and
is **not** part of this leaderboard yet. Until then, do not read a high static
pass rate as "this model writes correct quantum algorithms".

## Fairness concerns

- **Prompt sensitivity:** results depend on the exact prompt; the task prompt is
  published with each task so runs are comparable.
- **Framework bias:** qcheck currently covers Qiskit and OpenQASM; models
  stronger in other frameworks are not represented yet.
- **Small n:** six tasks is not statistically robust; treat early numbers as
  directional, not definitive.
- **Static-only bias:** a model that emits simple, well-formed code may outscore
  a model that attempts richer (but static-valid) circuits.

## Model settings and reproducibility

- Each submission carries a `metadata.json` (`model`, `provider`, `date`,
  `temperature`, `is_sample`).
- Because generation happens outside this repo (no API keys here), results are
  reproducible from the committed submission files + the qcheck version, not from
  re-querying a model.

## Reporting results honestly

- Always label sample/demo rows as SAMPLE (the tooling does this automatically
  from `is_sample`).
- State the qcheck version and task set used.
- Do not present a static pass rate as semantic correctness or as a definitive
  model ranking.

## How not to misuse this leaderboard

Do not cite it as proof that "model X is better at quantum computing", as a
safety certification, or as evidence of quantum advantage. It is a static
code-hygiene benchmark for LLM-generated quantum snippets — nothing more.
