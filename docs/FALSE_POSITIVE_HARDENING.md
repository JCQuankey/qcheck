# False-positive hardening

qcheck's credibility rests on one property: **an error-level finding means the
code will not run as intended.** This page documents how false positives are
measured and what the measurements have already changed.

## How to measure

`tools/corpus_smoke.py` runs qcheck over a local corpus of code you believe is
correct and aggregates what would be flagged, by rule, level and framework.
Nothing is vendored or downloaded; the corpus stays on your disk.

A convenient real-world corpus is the installed sources of the quantum
frameworks themselves - large bodies of idiomatic, presumptively-correct code:

```bash
python -m venv /tmp/corpus
/tmp/corpus/bin/pip install qiskit pennylane cirq-core
python tools/corpus_smoke.py /tmp/corpus/lib/python3*/site-packages/cirq/ops \
    --markdown report.md
```

Use `--disable UNSUPPORTED` when scanning mixed repositories where many `.py`
files are legitimately not quantum code, and `--expect-clean` to turn the run
into a regression gate (exit 1 on any error-level finding).

## How to read the results

- **Error-level findings on correct code are false positives by definition**
  and get fixed with a regression test (see `tests/test_fp_hardening.py`).
- **Warning-level findings on library code are usually policy, not bugs**: a
  helper that builds and returns an unmeasured circuit legitimately draws
  `QISKIT-NO-MEASURE`; a reviewer aimed at snippets is expected to note that.
  Waive them per line (`# qcheck: ignore[RULE-ID]`) or per run (`--disable`).
- **Safety findings are policy by design**: quantum snippets should not need
  `os`/`subprocess`/`pickle`; library internals legitimately do. Corpus runs
  report them separately - they are the snippet gate working as documented,
  not review errors.

## What measurement has already changed (July 2026 pass)

A pass over the installed sources of qiskit 2.5, pennylane 0.45 and
cirq-core 1.7 (646 files) plus canonical user patterns found the 50 quantum
rules essentially clean (one defensible finding) and two wrapper defects,
both fixed with regression tests:

- **Framework routing**: a `.py` file whose docstring merely mentioned
  OpenQASM was parsed as QASM (qiskit's own `quantumcircuit.py` drew
  thousands of bogus findings). A `.py` extension now always wins over
  content mentions.
- **Receiver-blind safety calls**: `.run()`/`.get()`-style calls were flagged
  on any object, so `backend.run(circuit)` - the pattern qcheck itself
  recommends - was marked unsafe. Attribute calls now flag only when the
  receiver resolves to an unsafe module import; the unsafe import itself
  still always flags, so the screen stays closed.

## Known limitations (documented, not bugs)

- Findings on multi-line statements carry the first line of the statement;
  inline suppression must sit on the reported line.
- `suggested_fixes` strings are not linked to individual findings and are
  not filtered by suppression.
- Structure warnings (`QISKIT-NO-CIRCUIT`, `QISKIT-NO-MEASURE`,
  `QASM-NO-MEASURE`, `PENNYLANE-QNODE-NO-RETURN`) are intentionally kept:
  they are correct for the snippet-review use case and suppressible for
  library-code scans.
- No corpus run proves a global false-positive rate; each run measures one
  corpus. The July 2026 numbers above describe that pass only.
