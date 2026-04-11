"""Task registry – central catalog of all available SOC tasks."""

from __future__ import annotations

from typing import Any, Optional

import yaml

from ..models import TaskScenario


class TaskRegistry:
    """Registry that discovers and manages SOC task definitions."""

    def __init__(self):
        self._tasks: dict[str, TaskScenario] = {}

    def register(self, task: TaskScenario) -> None:
        """Register a task scenario."""
        self._tasks[task.task_id] = task

    def get(self, task_id: str) -> Optional[TaskScenario]:
        """Retrieve a task by ID."""
        return self._tasks.get(task_id)

    def list_tasks(self) -> list[TaskScenario]:
        """Return all registered tasks."""
        return list(self._tasks.values())

    def load_from_yaml(self, path: str) -> None:
        """Load task definitions from an openenv.yaml file."""
        with open(path) as f:
            config = yaml.safe_load(f)

        for task_def in config.get("tasks", []):
            scenario = TaskScenario(
                task_id=task_def["id"],
                name=task_def["name"],
                description=task_def["description"],
                difficulty=task_def["difficulty"],
            )
            self.register(scenario)

    def __len__(self) -> int:
        return len(self._tasks)

    def __contains__(self, task_id: str) -> bool:
        return task_id in self._tasks
