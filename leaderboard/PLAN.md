# Leaderboard — build plan

## Now (v0, done)
- Task format (`tasks/*.json`), one sample task.
- `evaluate.py`: runs qcheck over `submissions/<model>/*` (or fixtures in demo mode), emits `results/*.json`. No LLM API calls. Runs today.

## Next (needs the user, NOT in this turn)
1. `generate.py` (separate, key-gated): for each task × model, prompt the model, save output to `submissions/<model>/<task_id>.{py,qasm}`. Models: GPT-4o/5, Claude, Gemini, DeepSeek, Qwen/Llama (local via Ollama, free), Qiskit Code Assistant (local model). Keep keys in env, never commit.
2. Import Qiskit HumanEval tasks (Apache-2.0, attribute) → 150+ tasks.
3. Static site (just renders `results/*.json` as a ranked table + per-model error breakdown + "run your own snippet" CTA to qcheck).
4. v1 grading: add sandboxed simulation for semantic-correctness (runs-but-wrong), the failure mode static checks can't catch.

## Distribution
Show HN ("Show HN: Which LLM writes correct quantum code? — most fail 40-70%"),
r/QuantumComputing, r/LocalLLaMA, X, Qiskit/Unitary communities. The leaderboard
is the funnel into qcheck installs.

## Metrics to watch
Leaderboard traffic/backlinks/citations; click-through to qcheck repo; qcheck
installs; measured per-model failure-rate (the headline stat).

## License hygiene
Qiskit HumanEval = Apache-2.0 (OK, attribute). QuanBench+ / QCoder = contact
authors before reusing tasks (license unverified). Original tasks are ours.
