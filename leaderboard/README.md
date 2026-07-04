# qcheck leaderboard — "Which LLM writes correct quantum code?"

An **experimental** benchmark scaffold that runs [qcheck](../README.md) over
model-generated quantum code and reports a **static** pass/fail/unsafe verdict.

> Status: MVP. The only results published today are hand-written **SAMPLE**
> demos (see `submissions/sample/`). No real model has been run yet.

## Hosted site

Once GitHub Pages is enabled for this repo, the static leaderboard in
`leaderboard/site/` is published at **https://jcquankey.github.io/qcheck/**.
Until real model runs exist, the page shows only the SAMPLE/demo row.

## Why this exists

LLMs generate quantum code that fails to run 40–70% of the time one-shot. This
leaderboard makes that concrete and framework-by-framework, and shows why a
static verifier like qcheck is useful in a CI or agent loop. It is the public
top-of-funnel for the tool.

## What the score means

The score is the **qcheck static verdict** on small Qiskit / OpenQASM tasks:

- **pass** — well-formed, uses modern APIs, no unsafe constructs, likely to run.
- **fail** — a static problem (e.g. `execute()`/`Aer` removed in Qiskit 1.0,
  undeclared register, out-of-range index, missing measurement).
- **unsafe** — the snippet touches the filesystem/network/process or uses
  dynamic exec; qcheck refuses it (exit code 2) and never runs it.

## What the score does NOT mean

It does **not** measure semantic/algorithmic correctness ("runs but produces the
wrong distribution"), quantum advantage, mathematical correctness, or hardware
performance. A snippet can pass the static verdict and still be the wrong
algorithm. See [`methodology.md`](methodology.md).

## Layout

```
leaderboard/
  README.md            this file
  methodology.md       scope, limitations, fairness, reproducibility
  tasks/               benchmark task definitions (qiskit/, openqasm/)
  submissions/         model outputs (sample/ = demo only)
  results/             evaluation output JSON (generated)
  site/                generated static leaderboard (leaderboard.md, index.html)
  scripts/             evaluate_submission.py, build_leaderboard.py
```

## Add a submission (manual)

1. Create `submissions/<model_name>/` and add files named after task ids, e.g.
   `qiskit_bell_state.py`, `openqasm_bell_state.qasm`.
2. Add a `metadata.json` (`model`, `provider`, `date`, `is_sample`).
3. There is **no automatic model generation in this repo** — you paste the
   model's output yourself. No API keys are used or stored.

## Evaluate

```bash
python3 leaderboard/scripts/evaluate_submission.py \
    leaderboard/submissions/sample/demo_model \
    --out leaderboard/results/sample_results.json
```

qcheck **never executes** the submitted code — it is parsed statically.

## Build the static leaderboard

```bash
python3 leaderboard/scripts/build_leaderboard.py leaderboard/results \
    --out leaderboard/site/leaderboard.md
```

This writes `site/leaderboard.md` and `site/index.html`.

## How this feeds qcheck

The failures the leaderboard surfaces become new qcheck fixtures and rules, and
(later, opt-in only) an anonymized error taxonomy. No telemetry exists today.

## Privacy

- Sample submissions are local files in this repo.
- Nothing is uploaded; no raw user code is collected.
- Contributors add submissions intentionally via pull request.
- Any future telemetry will be **opt-in** and will never transmit raw code.

## Future work

Real multi-model runs (via a separate, key-gated generator kept out of this
repo), import of public task sets (e.g. Qiskit HumanEval, Apache-2.0, with
attribution), and semantic grading via sandboxed simulation in qcheck v1.
