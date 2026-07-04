# Using qcheck from an agent or CI

qcheck's outputs are machine-readable so an AI agent that just generated quantum
code - or a CI workflow - can act on findings automatically. This page shows the
common consumption patterns. See [`CONTRACTS.md`](CONTRACTS.md) for the exact
output shapes.

## Review generated code and decide whether to revise

```bash
qcheck verify snippet.py --json | python examples/consume_json.py
```

[`examples/consume_json.py`](../examples/consume_json.py) reads the JSON, prints a
compact per-finding summary, and exits non-zero when there is an error-level or
unsafe finding - a natural signal for an agent loop to revise the code and try
again. It handles both the single-file object and the multi-file envelope.

## Explain a finding by its rule id

```bash
qcheck rules --json | python examples/consume_rules_json.py QISKIT-EXECUTE
```

[`examples/consume_rules_json.py`](../examples/consume_rules_json.py) builds a
`rule id -> guidance` lookup from the catalog. Given a finding's stable rule id,
an agent can fetch the title, why it matters, and a recommended action, so it can
act without guessing.

## Surface findings in CI

Emit SARIF and let your workflow upload it to code scanning:

```bash
qcheck verify . --format sarif --output qcheck.sarif
```

Rule ids are stable across releases, so the same id means the same check as
qcheck grows - dashboards, gates and agent loops stay consistent.

## Notes

- These examples are stdlib-only and have no external dependencies.
- Exit codes: `0` pass, `1` findings, `2` unsafe/unsupported, `3` usage/internal.
- The JSON, `qcheck rules --json` and SARIF shapes are documented, tested
  contracts (see [`CONTRACTS.md`](CONTRACTS.md)).
