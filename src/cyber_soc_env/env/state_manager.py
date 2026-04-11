"""State manager – tracks and updates environment state."""

from __future__ import annotations

from typing import Any

from ..models import SOCAction, SOCState, TaskScenario


class StateManager:
    """Manages the mutable state of the environment."""

    def __init__(self, scenario: TaskScenario):
        self.scenario = scenario
        self.current_state = SOCState(
            step=0,
            alerts_data=[],
            actions_taken=[],
            score=0.0,
            done=False,
            info={}
        )

    def reset(self) -> SOCState:
        """Reset to initial state with scenario alerts."""
        self.current_state = SOCState(
            step=0,
            alerts_data=[a.model_dump() for a in self.scenario.alerts],
            actions_taken=[],
            score=0.0,
            done=False,
        )
        return self.current_state

    def update(
        self, action: SOCAction, reward: float, result: dict[str, Any]
    ) -> SOCState:
        """Apply action results and advance state."""
        from dataclasses import asdict
        self.current_state.step += 1
        self.current_state.actions_taken.append(asdict(action))
        self.current_state.score += reward
        self.current_state.info = result
        return self.current_state
