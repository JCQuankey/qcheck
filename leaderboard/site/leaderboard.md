# qcheck static review benchmark

_A small public benchmark for reviewing AI-generated Qiskit and OpenQASM snippets with qcheck. See [methodology](../methodology.md)._

A small public benchmark for reviewing AI-generated Qiskit and OpenQASM snippets with qcheck. It reports `static_pass_rate` — the share of snippets that pass qcheck's current static review checks — as an early quality signal. Rows marked _SAMPLE_ are demo data; real runs will include provenance, task counts, qcheck version, and prompt hash.

| # | Model | Provider | Static pass rate | Passed / Attempted | Unsafe | qcheck |
|---|-------|----------|------------------|--------------------|--------|--------|
| 1 | demo-model _(SAMPLE)_ | sample | 50.0% | 3 / 6 | 1 | v0.1.0 |

Run your own snippet through the tool: `qcheck verify <file>` (see the [repo README](../../README.md)).

