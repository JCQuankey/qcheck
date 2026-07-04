# qcheck static-check leaderboard — LLM-generated quantum code

_Experimental static-check table (not a correctness ranking). See [methodology](../methodology.md)._

**Static checks only — this does not prove quantum correctness.** **What this measures:** the qcheck *static* pass rate (is the generated code well-formed, using modern APIs, safe, and likely to run?) on a small public Qiskit/OpenQASM task set. **What it does NOT measure:** semantic/algorithmic correctness, quantum advantage, hardware performance, or runtime success. This is a small, illustrative static-check benchmark, not a definitive model ranking. Rows marked _SAMPLE_ are hand-written demos, not real model results.

| # | Model | Provider | Static pass rate | Passed / Attempted | Unsafe | qcheck |
|---|-------|----------|------------------|--------------------|--------|--------|
| 1 | demo-model _(SAMPLE)_ | sample | 50.0% | 3 / 6 | 1 | v0.1.0 |

Run your own snippet through the tool: `qcheck verify <file>` (see the [repo README](../../README.md)).

