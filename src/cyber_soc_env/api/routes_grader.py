"""Grader API routes."""

from fastapi import APIRouter, HTTPException

from ..graders.grader_task1 import BruteForceGrader
from ..graders.grader_task2 import MalwareGrader
from ..graders.grader_task3 import APTGrader
from ..tasks.task1_brute_force import BruteForceTask
from ..tasks.task2_malware import MalwareTask
from ..tasks.task3_apt import APTTask

router = APIRouter()

# Map of task_id -> (grader_class, scenario_builder)
_GRADER_MAP = {
    "task1_brute_force": (BruteForceGrader, BruteForceTask.build_scenario),
    "task2_malware": (MalwareGrader, MalwareTask.build_scenario),
    "task3_apt": (APTGrader, APTTask.build_scenario),
}


@router.post("/{task_id}/grade")
async def grade_task(task_id: str):
    """Grade the current session for a task.

    Note: In a production system, this would pull stored actions from
    the active environment session. This skeleton returns a placeholder.
    """
    if task_id not in _GRADER_MAP:
        raise HTTPException(status_code=404, detail=f"No grader for task '{task_id}'")

    grader_cls, scenario_fn = _GRADER_MAP[task_id]
    scenario = scenario_fn()
    grader = grader_cls(scenario)

    # Placeholder: grade with empty actions (skeleton)
    result = grader.grade([])
    return result.model_dump()
