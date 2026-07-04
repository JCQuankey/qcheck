# qcheck output contracts

qcheck produces structured, machine-readable output so that **agents can act on
findings** and **CI systems can consume results** reliably. This page documents
the public output contracts: the CLI exit codes, the JSON shapes, the rule
catalog, and the SARIF report.

**Stability:** rule IDs and the top-level fields below are stable identifiers you
can build on. qcheck adds new rules and may add new fields over time; existing
fields and exit codes stay backward compatible within the 0.x line. The internal
detection logic and heuristics may evolve - build on the documented fields, not
on internal implementation details.

Contract tests in `tests/test_contracts.py` guard these shapes.

## Exit codes

`qcheck verify` returns a findings-based exit code (independent of output format):

| Code | Meaning |
|-----:|---------|
| `0` | review completed with no error-level findings (pass, or pass-with-warnings) |
| `1` | review completed with error-level findings |
| `2` | unsafe input (a safety rule fired) or unsupported input |
| `3` | CLI usage or internal error (for example an unreadable path) |

For multiple paths, the exit code is the worst result found (`2` outranks `1`
outranks `0`).

## `verify --json` - single file

`qcheck verify <file> --json` emits one JSON object:

```json
{
  "qcheck_version": "0.7.0",
  "status": "fail",
  "framework": "qiskit",
  "syntax_valid": true,
  "unsafe": false,
  "runnable_in_simulator": "not_run",
  "runnable_reason": "static review only",
  "static_checks": [
    { "id": "QISKIT-REMOVED-IMPORT", "level": "error",
      "message": "'from qiskit import execute' was removed in Qiskit 1.0", "line": 1 }
  ],
  "errors": [ /* the error-level subset of static_checks */ ],
  "warnings": [ /* the warning-level subset of static_checks */ ],
  "suggested_fixes": ["..."],
  "confidence": 0.6
}
```

**Stable fields agents can rely on:**
- `qcheck_version` - the version that produced the output.
- `status` - one of `pass`, `warning`, `fail`.
- `framework` - `qasm2`, `qasm3`, `qiskit`, `python_unknown`, or `unknown`.
- `static_checks` - the full list of findings. Each finding has:
  - `id` - the stable rule ID (see the catalog).
  - `level` - `error`, `warning`, or `info`.
  - `message` - a human-readable description.
  - `line` - the 1-based source line, or `null` when not line-specific.
- `errors` / `warnings` - convenience subsets of `static_checks` by level.
- `suggested_fixes` - practical guidance strings.

`confidence` is a heuristic 0.0-1.0 signal, not a correctness guarantee.

## `verify --json` - multiple files or a directory

For more than one reviewed file, qcheck emits an aggregate envelope:

```json
{
  "qcheck_version": "0.7.0",
  "results": [
    { "path": "circuits/bell.py", "status": "pass", "static_checks": [], "...": "..." }
  ],
  "summary": { "files": 3, "passed": 1, "failed": 1, "unsafe": 1, "read_errors": 0 }
}
```

- `results` - an array; each entry is the single-file object above **plus** a
  `path` field naming the reviewed file.
- `summary` - counts across the run: `files`, `passed`, `failed`, `unsafe`,
  `read_errors`.

A single reviewed file uses the single-object shape above (no envelope), which
keeps existing single-file consumers working.

## `qcheck rules --json` - the rule catalog

`qcheck rules --json` emits the full catalog, sorted by rule `id`
(deterministic):

```json
{
  "qcheck_version": "0.7.0",
  "rules": [
    {
      "id": "QISKIT-EXECUTE",
      "title": "execute() removed in Qiskit 1.0",
      "category": "api-compatibility",
      "default_level": "error",
      "applies_to": "qiskit",
      "summary": "Flags use of the top-level execute() call.",
      "why_it_matters": "execute() was removed in Qiskit 1.0 ...",
      "recommended_action": "Use a primitive (Sampler/Estimator) or backend.run()."
    }
  ]
}
```

Every rule provides: `id`, `title`, `category`, `default_level`, `applies_to`,
`summary`, `why_it_matters`, `recommended_action`. Agents can use this catalog as
a stable knowledge base of what qcheck reviews and how to act on each finding.

## SARIF (GitHub Code Scanning)

`qcheck verify <path> --format sarif` emits a single-run **SARIF 2.1.0** document:

- `version` is `"2.1.0"`; `runs` has exactly one run.
- `runs[0].tool.driver` carries `name` (`qcheck`), `version`, `informationUri`,
  and `rules[]`.
- `runs[0].tool.driver.rules[]` is enriched from the catalog: each entry has
  `id`, `name`, `shortDescription`, `fullDescription`, `help`,
  `defaultConfiguration.level`, and `properties` (category, surface). Only rules
  observed in the run are listed.
- `runs[0].results[]` each have `ruleId`, `level` (`error`/`warning`/`note`),
  `message.text`, and `locations[]` with an `artifactLocation.uri` and a
  `region.startLine` when a line is available.
- `runs[0].invocations[0].executionSuccessful` reflects whether the run
  completed without an internal error.

This qcheck-specific rule metadata gives CI and code-scanning tools inline
guidance for each finding.

## GitHub Action

Pin the composite action to a released tag:

```yaml
- uses: actions/checkout@v4
- uses: JCQuankey/qcheck@v0.7.0
  with:
    paths: "."          # files or folders to review
    format: sarif       # optional: human (default) or sarif
    output: qcheck.sarif # optional: write SARIF to a file for upload
```

`paths` is space-separated for multiple paths; to review a path that
contains spaces, pass one path per line (a YAML block scalar). 

The action installs qcheck (zero runtime dependencies) and runs `qcheck verify`;
it needs no secrets. To surface findings as code scanning alerts, add a separate
`github/codeql-action/upload-sarif` step (which needs `security-events: write` in
the consuming repository). See [`README.md`](../README.md) for full examples.
