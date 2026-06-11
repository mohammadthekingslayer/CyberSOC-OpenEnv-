"""Tests for task definitions."""

import pytest

from cyber_soc_env.tasks.task1_brute_force import BruteForceTask
from cyber_soc_env.tasks.task2_malware import MalwareTask
from cyber_soc_env.tasks.task3_apt import APTTask
from cyber_soc_env.tasks.registry import TaskRegistry
from cyber_soc_env.models import Difficulty


class TestBruteForceTask:
    def test_build_scenario(self):
        scenario = BruteForceTask.build_scenario()
        assert scenario.task_id == "task1"
        assert scenario.difficulty == Difficulty.BEGINNER
        assert len(scenario.alerts) == 3

    def test_alerts_have_required_fields(self):
        scenario = BruteForceTask.build_scenario()
        for alert in scenario.alerts:
            assert alert.alert_id
            assert alert.severity
            assert alert.source


class TestMalwareTask:
    def test_build_scenario(self):
        scenario = MalwareTask.build_scenario()
        assert scenario.task_id == "task2"
        assert scenario.difficulty == Difficulty.INTERMEDIATE
        assert len(scenario.alerts) == 3


class TestAPTTask:
    def test_build_scenario(self):
        scenario = APTTask.build_scenario()
        assert scenario.task_id == "task3"
        assert scenario.difficulty == Difficulty.ADVANCED
        assert len(scenario.alerts) == 5


class TestTaskRegistry:
    def test_register_and_get(self):
        registry = TaskRegistry()
        scenario = BruteForceTask.build_scenario()
        registry.register(scenario)
        assert registry.get("task1") is scenario

    def test_list_tasks(self):
        registry = TaskRegistry()
        registry.register(BruteForceTask.build_scenario())
        registry.register(MalwareTask.build_scenario())
        assert len(registry.list_tasks()) == 2

    def test_contains(self):
        registry = TaskRegistry()
        registry.register(BruteForceTask.build_scenario())
        assert "task1" in registry
        assert "nonexistent" not in registry
