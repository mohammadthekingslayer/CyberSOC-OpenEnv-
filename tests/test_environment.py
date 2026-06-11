"""Tests for the CyberSOC environment."""

import pytest

from cyber_soc_env.env.environment import SOCEnvironment
from cyber_soc_env.tasks.task1_brute_force import BruteForceTask
from cyber_soc_env.models import SOCAction, ActionType


class TestCyberSOCEnvironment:
    def test_reset(self):
        env = SOCEnvironment("task1")
        obs = env.reset()
        assert env.state.step == 0
        assert len(env.state.alerts_data) == 3
        assert env.state.done is False

    def test_step(self):
        env = SOCEnvironment("task1")
        env.reset()
        action = SOCAction(
            action_type=ActionType.ANALYZE_LOG,
            target="10.0.0.55",
        )
        obs = env.step(action)
        assert env.state.step == 1
        assert len(env.state.actions_taken) == 1
        assert env.state.score > 0

    def test_step_after_done_raises(self):
        env = SOCEnvironment("task1")
        env.reset()
        env.state_manager.current_state.done = True
        action = SOCAction(action_type=ActionType.ANALYZE_LOG, target="test")
        obs = env.step(action)
        assert obs.done is True
        assert obs.message == "Episode already done. Call reset()."

    def test_multiple_steps(self):
        env = SOCEnvironment("task1")
        env.reset()
        actions = [
            SOCAction(action_type=ActionType.ANALYZE_LOG, target="10.0.0.55"),
            SOCAction(action_type=ActionType.BLOCK_IP, target="block_ip"),
        ]
        for action in actions:
            env.step(action)
        assert env.state.step == 2
        assert len(env.state.actions_taken) == 2
