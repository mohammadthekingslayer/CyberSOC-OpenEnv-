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

    def _compute_kpis(self, actions: list[SOCAction], expected_steps: int = 3) -> dict[str, Any]:
        """Compute standard SOC KPIs (MTTD, MTTR, Efficiency)."""
        mttd = -1
        mttr = -1
        
        for i, action in enumerate(actions):
            at = str(action.action_type)
            if "analyze_log" in at and mttd == -1:
                mttd = i + 1
            if ("block_ip" in at or "isolate_device" in at or "mark_safe" in at) and mttr == -1:
                mttr = i + 1
                
        actual_steps = max(1, len(actions))
        efficiency = min(1.0, expected_steps / actual_steps)
        
        return {
            "mttd_steps": mttd if mttd > 0 else 0,
            "mttr_steps": mttr if mttr > 0 else 0,
            "action_efficiency": round(efficiency, 2)
        }
