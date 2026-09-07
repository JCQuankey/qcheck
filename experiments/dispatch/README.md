# Dispatch contract experiment

Experimental, offline, synthetic data only. Not an operational dispatch service.
No QPU, hosted endpoint, payment, telemetry or customer data. qcheck's package,
CLI and mandatory dependencies are unchanged.

## Design and acceptance fixed before implementation

JSON-compatible dictionaries, integer minutes, one day (0..1440), explicit
directed travel matrix, skills, shifts, current positions, current plan and
an urgent job, absence or duration-increase event. One technician per job.
Completed and in-progress visits, and pinned future commitments, must retain
their technician and start. Historical travel cannot be verified from a current
position snapshot; only future travel is checked. Breaks, multi-technician jobs,
time-dependent travel, stock and geographic data are unsupported.

`contract.py`: strict bounded input and copy-on-event transformation.
`validate_plan.py`: independent feasibility checker, no solver imports.
`exact_reference.py`: enumerate every integer-time assignment on tiny cases,
including unassigned jobs, under a deterministic candidate budget.
`classical_control.py`: deliberately simple incremental control, NOT a strong
classical benchmark. Uses the checker as a feasibility filter, so its quality
comparison does not independently validate the checker.
`benchmark.py`: fixed synthetic cases and a reproducible JSON report.

Input top-level keys: `version=1`, `now`, `travel`, `technicians`, `jobs`,
`current`. Technician: `id`, `skills`, `shift=[start,end]`, `location`, `base`,
`available`. Job: `id`, `skills`, `duration`, `window=[earliest,latest]` (START
window), `location`, `critical`, `state` (`pending`, `in_progress`, `completed`).
Current assignment: `job`, `technician`, `start`, `pinned`. Output assignments
omit `pinned`; the input alone owns commitments. Unknown keys are rejected.
No executable input or file loading is accepted by the solver.

Hard constraints: skills, availability for unfinished work, unique assignment,
window, no overlap, future travel from supplied current location, shift and
return to base. A protected commitment made impossible by an event is not
silently relaxed. Missing optional jobs remain explicit; generic reasons do
not assert proven impossibility.

Lexicographic objective (not money): unassigned critical count, unassigned other
count, technician changes, absolute start changes, future travel minutes, wait
minutes. Counts/metrics are also returned separately. Current-plan cancellations
are reported separately; they already incur unassigned penalties. An urgent
job is not guaranteed feasible. Safety never enters a weighted trade-off.

Statuses: `INVALID_INPUT`, `FEASIBLE`, `PROVEN_INFEASIBLE`,
`NO_SOLUTION_WITHIN_BUDGET`. `optimal=true` requires exhausted enumeration.
A feasible solution with an exhausted budget is not called optimal. Exact
reference limits: five jobs, two technicians, horizon <= 60 minutes, at most
250000 complete candidate assignments. Budget does not promise wall-clock SLA.

## Implementation plan

1. Write analytic and deliberately invalid plan tests; run them red.
2. Implement strict input/event contract and independent checker; run tests.
3. Add exhaustive reference and simple control; verify hand-calculated optimum,
   infeasibility proof, interruption, preserved commitments and event behavior.
4. Run fixed development cases (seeds 11, 12); then reserved evaluation cases
   (101..110) once without tuning. Report all results, not only wins.
5. Run existing tests and static CLI; inspect diff and preserve a draft PR.

Acceptance: zero accepted hard-constraint violations in adversarial tests;
exact optimum matches hand calculation; no optimum/proof claim on budget
exhaustion; inputs unchanged by events/solvers. Larger comparison is explicitly
`STRONG_BASELINE_NOT_TESTED`; hardware comparison `QUANTUM_NOT_TESTED`.

## Reproduce

From repository root with Python 3.11 or 3.12 and existing pytest:

```sh
python -m pytest -q experiments/dispatch/tests
python -m experiments.dispatch.benchmark
```

No installation or network needed for the experiment. Synthetic findings cannot
establish demand, real savings, production safety, margin, learning or quantum
advantage. Next technical gate is an independently formulated strong classical
baseline at larger scale, with the same constraints and full time accounting.

## Recorded execution (2026-09-07)

`results/2026-09-07.json` records the initial experiment at `c37b2bc`.
Independent review subsequently found that historical service overlaps were not
checked. Four independently authored frozen regression tests reproduced the
defect (two failed, two adjacent-interval controls passed). `66d9612` fixes it
without changing those tests. Full suite after correction: 313 tests passed.

`results/2026-09-07-verified.json` is the corrected-code evidence: seeds 101..110
are now regression reruns, not untouched evaluation. New seeds 201..210 were
evaluated after the safety fix, with no subsequent tuning. To reproduce:

```sh
python -c 'import json; from experiments.dispatch.benchmark import run; print(json.dumps(run(tuple(range(201, 211))), indent=2))'
```

The exact reference and control both use the checker, so independent adversarial
tests, not their agreement, establish the tested constraint behavior. Benchmark
seeds are now public; reserve fresh seeds before subsequent optimization work.
