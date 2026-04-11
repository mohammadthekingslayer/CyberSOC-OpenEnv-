"""Baseline agent API routes."""

from fastapi import APIRouter

router = APIRouter()


@router.post("/run/{task_id}")
async def run_baseline(task_id: str):
    """Run the AI baseline agent on a task.

    Note: Requires OPENAI_API_KEY to be set.
    This is a skeleton endpoint – full implementation pending.
    """
    return {
        "task_id": task_id,
        "status": "not_implemented",
        "message": "Baseline agent execution is a placeholder. Set OPENAI_API_KEY and implement run_baseline.py.",
    }
