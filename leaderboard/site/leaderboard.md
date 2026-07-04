# Which LLM writes correct quantum code?

_Experimental qcheck static leaderboard. See [methodology](../methodology.md)._

**What this measures:** the qcheck *static* verdict (is the generated code well-formed, modern, safe, and likely to run?) on small Qiskit/OpenQASM tasks. **What it does NOT measure:** semantic/algorithmic correctness, quantum advantage, or hardware performance. Rows marked _SAMPLE_ are hand-written demos, not real model results.

| # | Model | Provider | Static pass rate | Passed / Attempted | Unsafe | qcheck |
|---|-------|----------|------------------|--------------------|--------|--------|
| 1 | demo-model _(SAMPLE)_ | sample | 50.0% | 3 / 6 | 1 | v0.1.0 |

Run your own snippet through the tool: `qcheck verify <file>` (see the [repo README](../../README.md)).

