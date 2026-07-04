# Which LLM writes correct quantum code?

A public, reproducible leaderboard scoring LLMs on quantum code generation,
graded by [`qcheck`](../README.md) (and, in v1, by sandboxed simulation).

**Why:** no public leaderboard for this exists (verified 2026-06). The benchmarks
that measure it (Qiskit HumanEval — Apache-2.0; QuanBench+; QCoder) are research
papers, not a live, shareable ranking. This is qcheck's content engine: it proves
the pain ("X% of LLM-generated quantum snippets don't run"), it is shareable,
and every result links back to "run your own snippet through qcheck".

## How it works

```
tasks/          one JSON per task: id, prompt, framework, reference notes
submissions/    <model>/<task_id>.{py,qasm}   (the code each model produced)
results/        aggregated scores per model (produced by evaluate.py)
```

For each `(model, task)` submission, `evaluate.py` runs `qcheck` and records
status (pass/warning/fail), errors, and the error taxonomy. Scores aggregate to
a per-model pass-rate, by framework.

## v0 status (today)

- Task format + a sample task defined.
- `evaluate.py` runs qcheck over a submissions directory and emits results JSON.
- **No LLM API calls.** Submissions are committed code files. To generate them
  for various local and hosted models tomorrow, a separate `generate.py` (not in
  v0) will prompt each model and save its output here — keeping evaluation
  (this repo) cleanly separated from generation (which needs keys).

## Run the demo

```bash
python3 leaderboard/evaluate.py            # evaluates the qcheck fixtures as a demo "model"
cat leaderboard/results/sample_results.json
```

## Methodology (planned)

- Tasks drawn from Qiskit HumanEval (Apache-2.0, attributed) + original tasks.
- Metrics: one-shot pass %, with-feedback pass % (v1), runtime-error %,
  semantic-wrong-output % (v1, needs simulation), per framework.
- Every model + version + date stamped; results reproducible from submissions.
