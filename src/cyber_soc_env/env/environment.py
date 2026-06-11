"""Core SOC environment – manages scenario lifecycle, conforming to OpenEnv ABC."""

from __future__ import annotations

from typing import Any, Optional

from openenv_core.env_server.interfaces import Environment

from ..models import SOCAction, SOCObservation, SOCState, ActionType, TaskScenario, Alert
from .action_handlers import handle_action
from .reward_engine import RewardEngine
from .state_manager import StateManager
from ..tasks.registry import TaskRegistry
from ..tasks.task1_brute_force import BruteForceTask
from ..tasks.task2_malware import MalwareTask
from ..tasks.task3_apt import APTTask


# Initialize global registry for tasks
_registry = TaskRegistry()
_registry.register(BruteForceTask.build_scenario())
_registry.register(MalwareTask.build_scenario())
_registry.register(APTTask.build_scenario())

def _resolve_scenario(task_id: str) -> TaskScenario:
    """Resolve a task_id (task1, task2, task3) to a TaskScenario."""
    # Strict mapping to ensure perfect alignment with competition spec
    mapping = {
        "task1": BruteForceTask,
        "task2": MalwareTask,
        "task3": APTTask,
    }
    # Basic normalization
    tid = task_id.lower().strip()
    if tid in mapping:
        return mapping[tid].build_scenario()
    
    # Fallback to Task 1 if not found
    return BruteForceTask.build_scenario()


class SOCEnvironment(Environment):
    """Gym-like environment for SOC analyst training tasks.

    Conforms to the OpenEnv ABC:
      - reset()  → Observation
      - step(action) → Observation
      - state (property) → State
    """

    def __init__(self, task_id: str = "task1", **kwargs):
        super().__init__(**kwargs)
        self.task_id = task_id
        self.scenario = _resolve_scenario(task_id)
        self.state_manager = StateManager(self.scenario)
        self.reward_engine = RewardEngine(self.scenario)
        self._actions_raw: list[SOCAction] = []

    def reset(self, task_id: Optional[str] = None) -> SOCObservation:
        """Reset environment to initial state. Optionally switch tasks."""
        if task_id:
            self.task_id = task_id
            self.scenario = _resolve_scenario(task_id)
            self.state_manager = StateManager(self.scenario)
            self.reward_engine = RewardEngine(self.scenario)
            
        self.state_manager.reset()
        self._actions_raw = []

        obs = SOCObservation(
            logs=[a.raw_log for a in self.scenario.alerts if a.raw_log],
            alerts=[f"[{a.severity.upper()}] {a.description}" for a in self.scenario.alerts],
            network_status={},
            threat_level="high" if any(a.severity in ["high", "critical"] for a in self.scenario.alerts) else "low",
            message=f"Environment reset. Task: {self.scenario.name}. Investigate the alerts.",
            done=False,
            reward=0.0
        )
        return obs

    def step(self, action) -> SOCObservation:
        """Execute an action and return the new observation.

        The returned SOCObservation contains done and reward fields
        (inherited from base Observation dataclass).
        """
        current_state = self.state_manager.current_state
        if current_state.done:
            return SOCObservation(
                message="Episode already done. Call reset().",
                done=True,
                reward=0.0,
            )

        # Ensure we have a proper SOCAction with robust validation
        try:
            if isinstance(action, dict):
                # Sanitize dict keys for SOCAction
                sanitized = {k: v for k, v in action.items() if k in ["action_type", "target", "reasoning"]}
                action = SOCAction(**sanitized)
            elif not isinstance(action, SOCAction):
                # If it's something totally weird, fallback to a safe investigation action
                action = SOCAction(action_type=ActionType.ANALYZE_LOG, target="unknown", reasoning="Invalid action object received")
        except Exception as e:
             action = SOCAction(action_type=ActionType.ANALYZE_LOG, target="error", reasoning=f"Action coercion failed: {str(e)}")

        # Process the action
        try:
            result = handle_action(action, current_state)
            if not isinstance(result, dict):
                result = {"observation": str(result), "success": False, "terminate": False}
        except Exception as e:
            result = {"observation": f"Internal handler error: {str(e)}", "success": False, "terminate": False}

        # Compute reward
        try:
            reward = self.reward_engine.compute_reward(action, current_state)
        except Exception:
            reward = 0.0

        # Update state and record action BEFORE checking termination
        new_state = self.state_manager.update(action, reward, result)
        self._actions_raw.append(action)  # Persist for grading

        # Check termination conditions
        done = new_state.step >= self.scenario.max_steps or result.get("terminate", False)
        
        # Note: Removed auto-termination logic to let full episode play out
        # This ensures all actions are captured for grading
        
        if done:
            new_state.done = True

        # Construct descriptive feedback message
        action_type_val = action.action_type.value if hasattr(action.action_type, 'value') else str(action.action_type)
        action_desc = f"{action_type_val.replace('_', ' ').capitalize()}"
        target_desc = f"'{action.target}'" if action.target else "target"
        obs_msg = result.get("observation", "Action processed successfully.")
        
        obs = SOCObservation(
            logs=[a.raw_log for a in self.scenario.alerts if a.raw_log],
            alerts=[f"[{a.severity.upper()}] {a.description}" for a in self.scenario.alerts],
            network_status={},
            threat_level="low" if done else "medium",
            message=f"[{action_desc} on {target_desc}] {obs_msg}",
            done=done,
            reward=reward,
        )
        return obs

    @property
    def state(self) -> SOCState:
        """Return the current environment state for OpenEnv."""
        return self.state_manager.current_state

    @property
    def is_done(self) -> bool:
        return self.state_manager.current_state.done

    def grade_episode(self, task_id: str = None) -> Any:
        """Call the appropriate grader. Returns GradeResult object."""
        tid = (task_id or self.task_id).lower().strip()
        # Ensure we use the raw actions collected in this instance
        actions = self._actions_raw

        if tid == "task1":
            from ..graders.grader_task1 import BruteForceGrader
            return BruteForceGrader(self.scenario).grade(actions)
        elif tid == "task2":
            from ..graders.grader_task2 import MalwareGrader
            return MalwareGrader(self.scenario).grade(actions)
        elif tid == "task3":
            from ..graders.grader_task3 import APTGrader
            return APTGrader(self.scenario).grade(actions)
        else:
            from ..models import GradeResult
            return GradeResult(task_id=tid, score=0.0)

    def close(self):
        """Clean up resources."""
        pass
