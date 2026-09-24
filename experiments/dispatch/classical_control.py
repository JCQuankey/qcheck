"""Greedy assignment control. Explicitly NOT the strong classical baseline."""

from time import perf_counter

from .contract import validate_input
from .validate_plan import check_plan


def solve_control(case, max_candidates=250000):
    started = perf_counter()
    try:
        validate_input(case)
        if type(max_candidates) is not int or not 0 <= max_candidates <= 250000:
            raise ValueError("invalid candidate budget")
    except ValueError as exc:
        return {"status": "INVALID_INPUT", "error": str(exc), "optimal": False}
    jobs = {j["id"]: j for j in case["jobs"]}
    plan = [{k: a[k] for k in ("job", "technician", "start")}
            for a in case["current"] if a["pinned"] or jobs[a["job"]]["state"] != "pending"]
    evaluation = check_plan(case, plan)
    if not evaluation["feasible"]:
        return {"status": "NO_SOLUTION_WITHIN_BUDGET", "optimal": False, "plan": None,
                "evaluation": evaluation, "wall_seconds": perf_counter() - started}
    protected = {a["job"] for a in plan}
    count = 0
    for job in sorted(jobs.values(), key=lambda j: (not j["critical"], j["window"][1], j["id"])):
        if job["id"] in protected:
            continue
        best, best_evaluation = plan, evaluation
        for tech in case["technicians"]:
            for start in range(max(case["now"], job["window"][0]), job["window"][1] + 1):
                if count >= max_candidates:
                    return {"status": "FEASIBLE", "optimal": False, "plan": best,
                            "evaluation": best_evaluation, "budget_exhausted": True,
                            "candidates": count, "wall_seconds": perf_counter() - started}
                count += 1
                candidate = plan + [{"job": job["id"], "technician": tech["id"], "start": start}]
                checked = check_plan(case, candidate)
                if checked["feasible"] and checked["objective"] < best_evaluation["objective"]:
                    best, best_evaluation = candidate, checked
        plan, evaluation = best, best_evaluation
    return {"status": "FEASIBLE", "optimal": False, "plan": plan,
            "evaluation": evaluation, "budget_exhausted": False,
            "candidates": count, "wall_seconds": perf_counter() - started}
