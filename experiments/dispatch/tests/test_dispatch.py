from copy import deepcopy

import pytest

from experiments.dispatch.contract import apply_event, validate_input
from experiments.dispatch.validate_plan import check_plan
from experiments.dispatch.exact_reference import solve_exact
from experiments.dispatch.classical_control import solve_control


def case():
    return {
        "version": 1, "now": 0, "travel": [[0, 1], [1, 0]],
        "technicians": [{"id": "t", "skills": ["electric"], "shift": [0, 8],
                         "location": 0, "base": 0, "available": True}],
        "jobs": [{"id": "a", "skills": ["electric"], "duration": 2,
                  "window": [1, 5], "location": 1, "critical": False,
                  "state": "pending"}],
        "current": [{"job": "a", "technician": "t", "start": 3, "pinned": False}],
    }


def assignment(start=3, job="a", technician="t"):
    return {"job": job, "technician": technician, "start": start}


def test_analytic_metrics_and_stability_optimum():
    c = case()
    assert check_plan(c, [assignment()])["objective"] == [0, 0, 0, 0, 2, 2]
    result = solve_exact(c)
    assert result["status"] == "FEASIBLE" and result["optimal"]
    assert result["plan"] == [assignment()]


@pytest.mark.parametrize("mutate", [
    lambda c: c.update(now=True),
    lambda c: c.update(version=2),
    lambda c: c.update(extra="code"),
    lambda c: c["travel"][0].__setitem__(1, -1),
    lambda c: c["travel"].pop(),
    lambda c: c["jobs"].append(deepcopy(c["jobs"][0])),
    lambda c: c["jobs"][0].update(duration=0),
    lambda c: c["jobs"][0].update(location=2),
    lambda c: c["jobs"][0].update(window=[6, 2]),
    lambda c: c["current"][0].update(technician="missing"),
    lambda c: c["jobs"][0].update(state="unknown"),
])
def test_invalid_input_is_rejected(mutate):
    c = case()
    mutate(c)
    with pytest.raises(ValueError):
        validate_input(c)
    assert solve_exact(c)["status"] == "INVALID_INPUT"


@pytest.mark.parametrize("plan, code", [
    ([assignment(0)], "WINDOW"),
    ([assignment(0)], "TRAVEL_OR_OVERLAP"),
    ([assignment(6)], "WINDOW"),
    ([assignment(), assignment()], "DUPLICATE_JOB"),
    ([assignment(technician="missing")], "UNKNOWN_REFERENCE"),
    ([assignment(start=True)], "INVALID_PLAN"),
])
def test_adversarial_plans(plan, code):
    result = check_plan(case(), plan)
    assert not result["feasible"] and code in result["errors"]


def test_skills_return_to_base_and_shift():
    c = case()
    c["technicians"][0]["skills"] = []
    assert "SKILLS" in check_plan(c, [assignment()])["errors"]
    c = case()
    c["technicians"][0]["shift"][1] = 5
    assert "RETURN_AFTER_SHIFT" in check_plan(c, [assignment()])["errors"]


def test_absence_unassigned_reason_and_no_mutation():
    c = case()
    saved = deepcopy(c)
    changed = apply_event(c, {"type": "absence", "technician": "t"})
    assert c == saved
    result = solve_exact(changed)
    assert result["optimal"] and result["plan"] == []
    assert result["evaluation"]["unassigned"] == [
        {"job": "a", "reason": "NO_ELIGIBLE_TECHNICIAN"}]


def test_urgent_impossible_never_relaxes_skills():
    urgent = deepcopy(case()["jobs"][0])
    urgent.update(id="urgent", critical=True, skills=["gas"])
    c = apply_event(case(), {"type": "urgent", "job": urgent})
    r = solve_exact(c)
    assert r["evaluation"]["objective"][0] == 1
    assert r["evaluation"]["feasible"]


def test_pinned_infeasibility_is_proven_only_after_exhaustion():
    c = case()
    c["current"][0]["pinned"] = True
    c = apply_event(c, {"type": "absence", "technician": "t"})
    assert solve_exact(c)["status"] == "PROVEN_INFEASIBLE"
    r = solve_exact(c, max_candidates=0)
    assert r["status"] == "NO_SOLUTION_WITHIN_BUDGET" and not r["optimal"]


def test_budget_with_incumbent_does_not_claim_optimum():
    r = solve_exact(case(), max_candidates=1)
    assert r["status"] == "FEASIBLE" and not r["optimal"]


def test_in_progress_and_completed_are_preserved():
    for state, now in [("in_progress", 4), ("completed", 5)]:
        c = case()
        c["now"] = now
        c["jobs"][0]["state"] = state
        c["technicians"][0]["location"] = 1
        r = solve_exact(c)
        assert r["plan"] == [assignment()]
        assert "PROTECTED_CHANGED" in check_plan(c, [assignment(4)])["errors"]
        assert "PROTECTED_CHANGED" in check_plan(c, [])["errors"]


def test_duration_increase_invalidates_pinned_plan():
    c = case()
    c["current"][0]["pinned"] = True
    c = apply_event(c, {"type": "duration", "job": "a", "duration": 7})
    assert solve_exact(c)["status"] == "PROVEN_INFEASIBLE"


def test_overlap_between_jobs_detected():
    c = case()
    other = deepcopy(c["jobs"][0])
    other["id"] = "b"
    c["jobs"].append(other)
    assert "TRAVEL_OR_OVERLAP" in check_plan(c, [assignment(), assignment(4, "b")])["errors"]


def test_control_and_exact_use_same_contract_without_mutation():
    c = case()
    saved = deepcopy(c)
    for solver in [solve_exact, solve_control]:
        result = solver(c)
        assert check_plan(c, result["plan"])["feasible"]
    assert c == saved


def test_control_budget_is_explicit_and_never_proves_infeasibility():
    result = solve_control(case(), max_candidates=0)
    assert result["status"] == "FEASIBLE"
    assert result["budget_exhausted"] and result["candidates"] == 0
    assert not result["optimal"]


def test_reassignment_to_qualified_available_technician():
    c = case()
    backup = deepcopy(c["technicians"][0])
    backup["id"] = "backup"
    c["technicians"].append(backup)
    c = apply_event(c, {"type": "absence", "technician": "t"})
    r = solve_exact(c)
    assert r["plan"] == [assignment(technician="backup")]
    assert r["evaluation"]["metrics"]["technician_changes"] == 1


def test_in_progress_duration_increase_moves_future_job_only():
    c = case()
    c["now"] = 4
    c["jobs"][0]["state"] = "in_progress"
    c["technicians"][0]["location"] = 1
    c["technicians"][0]["shift"][1] = 12
    b = deepcopy(c["jobs"][0])
    b.update(id="b", state="pending", window=[5, 9])
    c["jobs"].append(b)
    c["current"].append({"job": "b", "technician": "t", "start": 5, "pinned": False})
    c = apply_event(c, {"type": "duration", "job": "a", "duration": 4})
    r = solve_exact(c)
    assert r["plan"] == [assignment(), assignment(7, "b")]
    assert r["evaluation"]["metrics"]["start_shift_minutes"] == 2


@pytest.mark.parametrize("event", [
    {"type": "absence", "technician": "missing"},
    {"type": "duration", "job": "a", "duration": 1},
    {"type": "duration", "job": "a", "duration": True},
    {"type": "execute", "code": "ignored"},
    {"type": "absence", "technician": "t", "extra": 1},
])
def test_event_contract_rejects_invalid_or_unsupported_events(event):
    with pytest.raises(ValueError):
        apply_event(case(), event)
