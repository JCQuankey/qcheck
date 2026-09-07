"""Bounded JSON data contract. Never accepts executable inputs."""

from copy import deepcopy


def _require(condition, message):
    if not condition:
        raise ValueError(message)


def _keys(value, keys):
    _require(type(value) is dict and set(value) == set(keys.split()), "invalid fields")


def _integer(value, low=0, high=1440):
    _require(type(value) is int and low <= value <= high, "invalid integer")


def _span(value):
    _require(type(value) is list and len(value) == 2, "invalid interval")
    for v in value:
        _integer(v)
    _require(value[0] <= value[1], "reversed interval")


def _identifier(value):
    _require(type(value) is str and 0 < len(value) <= 64, "invalid identifier")


def _skills(value):
    _require(type(value) is list and len(value) <= 32, "invalid skills")
    for v in value:
        _identifier(v)
    _require(len(set(value)) == len(value), "duplicate skill")


def validate_input(case):
    _keys(case, "version now travel technicians jobs current")
    _require(type(case["version"]) is int and case["version"] == 1, "unsupported version")
    _integer(case["now"])
    matrix = case["travel"]
    _require(type(matrix) is list and 1 <= len(matrix) <= 100, "invalid matrix")
    for i, row in enumerate(matrix):
        _require(type(row) is list and len(row) == len(matrix), "non-square matrix")
        for value in row:
            _integer(value)
        _require(row[i] == 0, "nonzero diagonal")
    for field, bound in [("technicians", 20), ("jobs", 100), ("current", 100)]:
        _require(type(case[field]) is list and len(case[field]) <= bound, "size limit")
    technicians = {}
    for tech in case["technicians"]:
        _keys(tech, "id skills shift location base available")
        _identifier(tech["id"])
        _require(tech["id"] not in technicians, "duplicate technician")
        _skills(tech["skills"])
        _span(tech["shift"])
        _integer(tech["location"], high=len(matrix) - 1)
        _integer(tech["base"], high=len(matrix) - 1)
        _require(type(tech["available"]) is bool, "invalid availability")
        technicians[tech["id"]] = tech
    jobs = {}
    for job in case["jobs"]:
        _keys(job, "id skills duration window location critical state")
        _identifier(job["id"])
        _require(job["id"] not in jobs, "duplicate job")
        _skills(job["skills"])
        _integer(job["duration"], low=1)
        _span(job["window"])
        _integer(job["location"], high=len(matrix) - 1)
        _require(type(job["critical"]) is bool, "invalid priority")
        _require(job["state"] in ("pending", "completed", "in_progress"), "invalid state")
        jobs[job["id"]] = job
    current = {}
    for a in case["current"]:
        _keys(a, "job technician start pinned")
        _identifier(a["job"])
        _identifier(a["technician"])
        _require(a["job"] in jobs and a["technician"] in technicians, "unknown reference")
        _require(a["job"] not in current, "duplicate current job")
        _integer(a["start"])
        _require(type(a["pinned"]) is bool, "invalid pin")
        current[a["job"]] = a
    active_techs = set()
    for job in jobs.values():
        if job["state"] == "pending":
            continue
        _require(job["id"] in current, "missing protected history")
        a = current[job["id"]]
        end = a["start"] + job["duration"]
        if job["state"] == "completed":
            _require(end <= case["now"], "completed in future")
        else:
            _require(a["start"] <= case["now"] < end, "invalid in-progress interval")
            _require(a["technician"] not in active_techs, "multiple active jobs")
            _require(technicians[a["technician"]]["location"] == job["location"],
                     "active position inconsistent")
            active_techs.add(a["technician"])
    return case


def apply_event(case, event):
    validate_input(case)
    _require(type(event) is dict, "invalid event")
    result = deepcopy(case)
    kind = event.get("type")
    if kind == "absence":
        _keys(event, "type technician")
        matches = [t for t in result["technicians"] if t["id"] == event["technician"]]
        _require(len(matches) == 1, "unknown technician")
        matches[0]["available"] = False
    elif kind == "urgent":
        _keys(event, "type job")
        _require(type(event["job"]) is dict, "invalid urgent job")
        _require(event["job"].get("critical") is True and
                 event["job"].get("state") == "pending", "urgent must be critical and pending")
        result["jobs"].append(deepcopy(event["job"]))
    elif kind == "duration":
        _keys(event, "type job duration")
        _integer(event["duration"], low=1)
        matches = [j for j in result["jobs"] if j["id"] == event["job"]]
        _require(len(matches) == 1, "unknown job")
        job = matches[0]
        _require(job["state"] != "completed" and event["duration"] > job["duration"],
                 "must increase unfinished duration")
        job["duration"] = event["duration"]
    else:
        raise ValueError("unsupported event")
    return validate_input(result)
