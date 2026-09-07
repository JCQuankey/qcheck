"""Tiny exhaustive integer-time reference, not a scalable routing algorithm."""

from itertools import product
from time import perf_counter

from .contract import validate_input
from .validate_plan import check_plan


def solve_exact(case, max_candidates=250000):
    started = perf_counter()
    try:
        validate_input(case)
        if type(max_candidates) is not int or not 0 <= max_candidates <= 250000:
            raise ValueError("invalid candidate budget")
        if (len(case["jobs"]) > 5 or len(case["technicians"]) > 2
                or case["now"] > 60
                or any(t["shift"][1] > 60 for t in case["technicians"])
                or any(j["window"][1] > 60 for j in case["jobs"])):
            raise ValueError("outside tiny reference limits")
    except ValueError as exc:
        return {"status": "INVALID_INPUT", "error": str(exc), "optimal": False}
    old = {a["job"]: a for a in case["current"]}
    choices = []
    for job in case["jobs"]:
        previous = old.get(job["id"])
        if previous and (previous["pinned"] or job["state"] != "pending"):
            options = [{k: previous[k] for k in ("job", "technician", "start")}]
        else:
            options = [None]
            for tech in case["technicians"]:
                for start in range(max(case["now"], job["window"][0]), job["window"][1] + 1):
                    options.append({"job": job["id"], "technician": tech["id"], "start": start})
        choices.append(options)
    best = evaluation = None
    count = 0
    exhausted = True
    for candidate in product(*choices):
        if count >= max_candidates:
            exhausted = False
            break
        count += 1
        plan = [a for a in candidate if a is not None]
        checked = check_plan(case, plan)
        if checked["feasible"] and (evaluation is None or checked["objective"] < evaluation["objective"]):
            best, evaluation = plan, checked
    status = "FEASIBLE" if best is not None else (
        "PROVEN_INFEASIBLE" if exhausted else "NO_SOLUTION_WITHIN_BUDGET")
    return {"status": status, "optimal": exhausted and best is not None,
            "search_exhausted": exhausted, "candidates": count, "plan": best,
            "evaluation": evaluation, "wall_seconds": perf_counter() - started}
