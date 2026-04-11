"""Base grader interface for all CyberSOC tasks."""

from __future__ import annotations

from abc import ABC, abstractmethod

from ..models import SOCAction, GradeResult, TaskScenario


class BaseGrader(ABC):
    """Abstract base class for task graders."""

    def __init__(self, scenario: TaskScenario):
        self.scenario = scenario

    @abstractmethod
    def grade(self, actions: list[SOCAction]) -> GradeResult:
        """Grade the analyst's actions against the expected response.

        Args:
            actions: List of actions taken by the analyst.

        Returns:
            GradeResult with score and feedback.
        """
        ...

    def _compute_action_coverage(
        self, taken: list[SOCAction], expected: list[SOCAction]
    ) -> float:
        """Compute what fraction of expected actions were matched."""
        if not expected:
            return 1.0
        matched = sum(
            1 for exp in expected
            if any(a.action_type == exp.action_type and a.target == exp.target for a in taken)
        )
        return matched / len(expected)
