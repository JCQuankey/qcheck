"""Independent regression cases for service overlap in protected history."""

import pytest

from experiments.dispatch.validate_plan import check_plan


def historical_case(second_state, second_start):
    """The first visit ends at minute 3; the snapshot is at minute 4."""
    second_duration = (4 if second_state == "completed" else 5) - second_start
    case = {
        "version": 1,
        "now": 4,
        "travel": [[0]],
        "technicians": [{
            "id": "t", "skills": [], "shift": [0, 8],
            "location": 0, "base": 0, "available": True,
        }],
        "jobs": [
            {
                "id": "a", "skills": [], "duration": 2,
                "window": [0, 6], "location": 0,
                "critical": False, "state": "completed",
            },
            {
                "id": "b", "skills": [], "duration": second_duration,
                "window": [0, 6], "location": 0,
                "critical": False, "state": second_state,
            },
        ],
        "current": [
            {"job": "a", "technician": "t", "start": 1, "pinned": False},
            {"job": "b", "technician": "t", "start": second_start, "pinned": False},
        ],
    }
    plan = [
        {"job": "a", "technician": "t", "start": 1},
        {"job": "b", "technician": "t", "start": second_start},
    ]
    return case, plan


@pytest.mark.parametrize("second_state", ["completed", "in_progress"])
def test_overlapping_protected_service_intervals_are_rejected(second_state):
    # a occupies [1, 3); b begins at 2, overlapping by one minute.
    case, plan = historical_case(second_state, second_start=2)
    result = check_plan(case, plan)
    assert not result["feasible"], result


@pytest.mark.parametrize("second_state", ["completed", "in_progress"])
def test_adjacent_protected_service_intervals_are_feasible(second_state):
    # a occupies [1, 3); b begins exactly at 3, so there is no overlap.
    case, plan = historical_case(second_state, second_start=3)
    result = check_plan(case, plan)
    assert result["feasible"], result
