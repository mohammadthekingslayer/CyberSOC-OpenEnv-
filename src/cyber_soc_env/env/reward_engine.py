"""Reward engine – computes rewards for analyst actions with task-specific scaling."""

from __future__ import annotations

from ..models import SOCAction, ActionType, SOCState, TaskScenario


class RewardEngine:
    """Computes rewards based on action quality and scenario context.
    
    Implements dynamic reward scaling based on task difficulty:
    - Easy tasks (task1): 1.0x multiplier
    - Medium tasks (task2): 1.2x multiplier  
    - Hard tasks (task3): 1.5x multiplier
    """

    # Base reward values for each action type
    REWARD_MAP = {
        ActionType.ANALYZE_LOG: 10.0,
        ActionType.ISOLATE_DEVICE: 15.0,
        ActionType.BLOCK_IP: 15.0,
        ActionType.MARK_SAFE: 5.0,
        ActionType.ESCALATE: 5.0,
        ActionType.RUN_SCAN: 10.0,
        ActionType.CORRELATE_EVENTS: 10.0,
    }
    
    # Task difficulty multipliers for dynamic reward scaling
    DIFFICULTY_MULTIPLIERS = {
        "easy": 1.0,
        "medium": 1.2,
        "hard": 1.5,
    }

    def __init__(self, scenario: TaskScenario):
        self.scenario = scenario
        self.difficulty_multiplier = self.DIFFICULTY_MULTIPLIERS.get(
            scenario.difficulty.lower(), 1.0
        )

    def compute_reward(self, action: SOCAction, state: SOCState) -> float:
        """Compute reward for a given action in current state.

        Provides signal at every step:
        - Positive reward for constructive actions (scaled by task difficulty)
        - Early-investigation bonus
        - Penalty for duplicate actions
        - Penalty for reckless behavior (acting without investigation)
        """
        base_reward = self.REWARD_MAP.get(action.action_type, 0.0)
        
        # Apply task difficulty scaling
        base_reward *= self.difficulty_multiplier

        # Bonus for investigating early in the episode
        if action.action_type == ActionType.ANALYZE_LOG and state.step < 5:
            base_reward *= 1.5

        # Penalty for duplicate actions (same type + same target)
        duplicate_count = sum(
            1 for a in state.actions_taken
            if a.get('action_type') == action.action_type and a.get('target') == action.target
        )
        if duplicate_count > 0:
            base_reward *= 0.5 ** duplicate_count

        # Penalty: blocking/isolating without investigating first
        destructive_actions = {ActionType.BLOCK_IP, ActionType.ISOLATE_DEVICE}
        if action.action_type in destructive_actions:
            has_investigated = any(
                a.get('action_type') == ActionType.ANALYZE_LOG for a in state.actions_taken
            )
            if not has_investigated and state.step == 0:
                # Acting without any investigation = risky, penalty
                base_reward *= 0.3

        # Penalty: marking something safe without investigating
        if action.action_type == ActionType.MARK_SAFE:
            has_investigated = any(
                a.get('action_type') == ActionType.ANALYZE_LOG for a in state.actions_taken
            )
            if not has_investigated:
                base_reward = -5.0  # False safety declaration is dangerous

        return round(base_reward, 2)
