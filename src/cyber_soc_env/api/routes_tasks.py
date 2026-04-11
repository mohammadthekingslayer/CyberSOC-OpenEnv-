"""Task-related API routes."""

from fastapi import APIRouter, HTTPException

from ..models import SOCAction, SOCState
from ..tasks.registry import TaskRegistry
from ..tasks.task1_brute_force import BruteForceTask
from ..tasks.task2_malware import MalwareTask
from ..tasks.task3_apt import APTTask
from ..env.environment import SOCEnvironment

router = APIRouter()

# Initialize registry and environments
_registry = TaskRegistry()
_registry.register(BruteForceTask.build_scenario())
_registry.register(MalwareTask.build_scenario())
_registry.register(APTTask.build_scenario())

_environments: dict[str, SOCEnvironment] = {}


@router.get("/")
async def list_tasks():
    """List all available tasks."""
    return [
        {"task_id": t.task_id, "name": t.name, "difficulty": t.difficulty.value}
        for t in _registry.list_tasks()
    ]


@router.get("/{task_id}")
async def get_task(task_id: str):
    """Get task details."""
    task = _registry.get(task_id)
    if not task:
        raise HTTPException(status_code=404, detail=f"Task '{task_id}' not found")
    return task.model_dump()


@router.post("/{task_id}/reset")
async def reset_task(task_id: str):
    """Reset environment for a task."""
    task = _registry.get(task_id)
    if not task:
        raise HTTPException(status_code=404, detail=f"Task '{task_id}' not found")
    env = SOCEnvironment(task_id)
    _environments[task_id] = env
    import dataclasses
    state = env.reset()
    return dataclasses.asdict(state)


@router.post("/{task_id}/step")
async def step_task(task_id: str, action: SOCAction):
    """Take an action in the environment."""
    env = _environments.get(task_id)
    if not env:
        raise HTTPException(status_code=400, detail=f"Task '{task_id}' not started. Call /reset first.")
    import dataclasses
    state = env.step(action)
    return dataclasses.asdict(state)
