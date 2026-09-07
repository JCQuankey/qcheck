"""Evaluate an explicit plan independently of all candidate-generation logic."""

from .contract import validate_input


def check_plan(case, plan):
    validate_input(case)
    errors = []
    jobs = {j["id"]: j for j in case["jobs"]}
    techs = {t["id"]: t for t in case["technicians"]}
    current = {a["job"]: a for a in case["current"]}
    assignments = {}
    if type(plan) is not list or len(plan) > 100:
        return {"feasible": False, "errors": ["INVALID_PLAN"]}
    for a in plan:
        if (type(a) is not dict or set(a) != {"job", "technician", "start"}
                or type(a["job"]) is not str or type(a["technician"]) is not str
                or type(a["start"]) is not int or not 0 <= a["start"] <= 1440):
            errors.append("INVALID_PLAN")
            continue
        if a["job"] not in jobs or a["technician"] not in techs:
            errors.append("UNKNOWN_REFERENCE")
            continue
        if a["job"] in assignments:
            errors.append("DUPLICATE_JOB")
        assignments[a["job"]] = a
    for job_id, old in current.items():
        if old["pinned"] or jobs[job_id]["state"] != "pending":
            actual = assignments.get(job_id)
            if actual != {k: old[k] for k in ("job", "technician", "start")}:
                errors.append("PROTECTED_CHANGED")
    travel = wait = changes = shift = cancellations = 0
    for job_id, a in assignments.items():
        job, tech = jobs[job_id], techs[a["technician"]]
        start, end = a["start"], a["start"] + job["duration"]
        if not set(job["skills"]) <= set(tech["skills"]):
            errors.append("SKILLS")
        if not job["window"][0] <= start <= job["window"][1]:
            errors.append("WINDOW")
        if start < tech["shift"][0] or end > tech["shift"][1]:
            errors.append("SHIFT")
        if job["state"] != "completed" and not tech["available"]:
            errors.append("UNAVAILABLE")
        old = current.get(job_id)
        if old:
            changes += a["technician"] != old["technician"]
            shift += abs(a["start"] - old["start"])
    for tech_id, tech in techs.items():
        route = sorted((a for a in assignments.values()
                        if a["technician"] == tech_id and jobs[a["job"]]["state"] != "completed"),
                       key=lambda a: (a["start"], a["job"]))
        time = max(case["now"], tech["shift"][0])
        location = tech["location"]
        for index, a in enumerate(route):
            job = jobs[a["job"]]
            if job["state"] == "in_progress":
                if index != 0:
                    errors.append("TRAVEL_OR_OVERLAP")
                time = a["start"] + job["duration"]
            else:
                leg = case["travel"][location][job["location"]]
                arrival = time + leg
                if a["start"] < arrival:
                    errors.append("TRAVEL_OR_OVERLAP")
                travel += leg
                wait += max(0, a["start"] - arrival)
                time = a["start"] + job["duration"]
            location = job["location"]
        # An absent technician with no future work is outside this dispatch plan.
        if route or tech["available"]:
            leg = case["travel"][location][tech["base"]]
            travel += leg
            if time + leg > tech["shift"][1]:
                errors.append("RETURN_AFTER_SHIFT")
    unassigned = []
    critical = other = 0
    for job in jobs.values():
        if job["id"] in assignments:
            continue
        eligible = any(t["available"] and set(job["skills"]) <= set(t["skills"])
                       for t in techs.values())
        unassigned.append({"job": job["id"], "reason": "NOT_SELECTED_NOT_PROVEN_IMPOSSIBLE"
                           if eligible else "NO_ELIGIBLE_TECHNICIAN"})
        critical += job["critical"]
        other += not job["critical"]
        cancellations += job["id"] in current
    objective = [critical, other, changes, shift, travel, wait]
    return {"feasible": not errors, "errors": sorted(set(errors)), "objective": objective,
            "unassigned": unassigned, "metrics": {
                "critical_unassigned": critical, "other_unassigned": other,
                "technician_changes": changes, "start_shift_minutes": shift,
                "travel_minutes": travel, "wait_minutes": wait,
                "current_cancellations": cancellations},
            "history_travel": "NOT_VERIFIABLE_FROM_SNAPSHOT"}
