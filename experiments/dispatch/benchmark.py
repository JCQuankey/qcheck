"""Print complete synthetic benchmark evidence; no files or external calls."""

from copy import deepcopy
from hashlib import sha256
import json
import platform
import random
from time import perf_counter

from .contract import apply_event
from .validate_plan import check_plan
from .exact_reference import solve_exact
from .classical_control import solve_control


DEVELOPMENT_SEEDS = (11, 12)
EVALUATION_SEEDS = tuple(range(101, 111))
CANDIDATE_BUDGET = 250000


def synthetic_case(seed):
    rng = random.Random(seed)
    case = {
        "version": 1, "now": 0,
        "travel": [[abs(i - j) for j in range(4)] for i in range(4)],
        "technicians": [{"id": f"t{i}", "skills": ["electric"], "shift": [0, 12],
                         "location": 0, "base": 0, "available": True} for i in range(2)],
        "jobs": [{"id": f"j{i}", "skills": ["electric"], "duration": rng.randint(2, 3),
                  "window": [1, rng.randint(4, 6)], "location": rng.randint(1, 3),
                  "critical": False, "state": "pending"} for i in range(2)],
        "current": [{"job": f"j{i}", "technician": f"t{i}", "start": 3,
                     "pinned": False} for i in range(2)],
    }
    if seed % 3 == 0:
        event = {"type": "absence", "technician": "t0"}
    elif seed % 3 == 1:
        urgent = deepcopy(case["jobs"][0])
        urgent.update(id="urgent", critical=True, window=[1, 3])
        event = {"type": "urgent", "job": urgent}
    else:
        event = {"type": "duration", "job": "j0", "duration": 5}
    return case, event


def run(seeds=DEVELOPMENT_SEEDS):
    rows = []
    for seed in seeds:
        started = perf_counter()
        original, event = synthetic_case(seed)
        original_plan = [{k: a[k] for k in ("job", "technician", "start")}
                         for a in original["current"]]
        before = check_plan(original, original_plan)
        assert before["feasible"], "generator supplied an invalid current plan"
        case = apply_event(original, event)
        exact = solve_exact(case, max_candidates=CANDIDATE_BUDGET)
        control = solve_control(case, max_candidates=CANDIDATE_BUDGET)
        for result in (exact, control):
            assert result["status"] == "FEASIBLE"
            assert check_plan(case, result["plan"])["feasible"]
        assert exact["optimal"], "inconclusive reference; do not score this as an optimum"
        assert exact["evaluation"]["objective"] <= control["evaluation"]["objective"]
        rows.append({"seed": seed, "event": event["type"],
                     "input_sha256": sha256(json.dumps(case, sort_keys=True).encode()).hexdigest(),
                     "original_plan_before_event": before,
                     "original_plan_after_event": check_plan(case, original_plan),
                     "exact": exact, "control": control,
                     "total_wall_seconds": perf_counter() - started})
    return {"data": "SYNTHETIC_NOT_CUSTOMER_DATA", "python": platform.python_version(),
            "candidate_budget_per_solver": CANDIDATE_BUDGET,
            "timing": "local monotonic wall clock; includes validation, not remote queues",
            "cost_eur": None, "commercial_validation": "NOT_TESTED",
            "strong_baseline": "STRONG_BASELINE_NOT_TESTED",
            "quantum": "QUANTUM_NOT_TESTED", "rows": rows}


if __name__ == "__main__":
    print(json.dumps({"development": run(), "evaluation": run(EVALUATION_SEEDS)}, indent=2))
