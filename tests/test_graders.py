"""Tests for graders."""

import pytest

from cyber_soc_env.graders.grader_task1 import BruteForceGrader
from cyber_soc_env.graders.grader_task2 import MalwareGrader
from cyber_soc_env.graders.grader_task3 import APTGrader
from cyber_soc_env.tasks.task1_brute_force import BruteForceTask
from cyber_soc_env.tasks.task2_malware import MalwareTask
from cyber_soc_env.tasks.task3_apt import APTTask
from cyber_soc_env.models import SOCAction, ActionType


class TestBruteForceGrader:
    def test_perfect_score(self):
        scenario = BruteForceTask.build_scenario()
        grader = BruteForceGrader(scenario)
        actions = [
            SOCAction(action_type=ActionType.ANALYZE_LOG, target="10.0.0.55"),
            SOCAction(action_type=ActionType.BLOCK_IP, target="block_ip_10.0.0.55"),
            SOCAction(action_type=ActionType.ESCALATE, target="security_team"),
        ]
        result = grader.grade(actions)
        assert result.score == 1.0
        assert result.passed is True

    def test_no_actions(self):
        scenario = BruteForceTask.build_scenario()
        grader = BruteForceGrader(scenario)
        result = grader.grade([])
        assert result.score == 0.0
        assert result.passed is False


class TestMalwareGrader:
    def test_partial_score(self):
        scenario = MalwareTask.build_scenario()
        grader = MalwareGrader(scenario)
        actions = [
            SOCAction(action_type=ActionType.ANALYZE_LOG, target="invoice.exe"),
            SOCAction(action_type=ActionType.BLOCK_IP, target="198.51.100.42"),
        ]
        result = grader.grade(actions)
        assert result.score == 0.55  # investigate(25) + block C2(30) = 55/100
        assert result.passed is False


class TestAPTGrader:
    def test_no_actions(self):
        scenario = APTTask.build_scenario()
        grader = APTGrader(scenario)
        result = grader.grade([])
        assert result.score == 0.0
        assert result.passed is False
