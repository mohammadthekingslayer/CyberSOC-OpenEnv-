#!/usr/bin/env python3
"""Smoke test – quick sanity check for CyberSOC OpenEnv."""

import os
import sys

# Ensure project src/ is on PYTHONPATH
_SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
_PROJECT_ROOT = os.path.dirname(_SCRIPT_DIR)
_SRC_DIR = os.path.join(_PROJECT_ROOT, "src")
if _SRC_DIR not in sys.path:
    sys.path.insert(0, _SRC_DIR)


def main() -> int:
    errors = 0

    print("🔥 CyberSOC OpenEnv Smoke Test")
    print("=" * 40)

    # Test 1: Core imports
    print("\n1. Testing core imports...")
    try:
        from cyber_soc_env.models import SOCAction, SOCObservation, SOCState, ActionType, GradeResult
        from cyber_soc_env.config import get_settings
        print("   ✅ Core models and config imported")
    except Exception as e:
        print(f"   ❌ Import error: {e}")
        errors += 1

    # Test 2: Task creation
    print("\n2. Testing task creation...")
    try:
        from cyber_soc_env.tasks.task1_brute_force import BruteForceTask
        from cyber_soc_env.tasks.task2_malware import MalwareTask
        from cyber_soc_env.tasks.task3_apt import APTTask

        for TaskClass in [BruteForceTask, MalwareTask, APTTask]:
            scenario = TaskClass.build_scenario()
            assert scenario.task_id, "task_id is empty"
            assert len(scenario.alerts) > 0, "No alerts in scenario"
        print("   ✅ All 3 task scenarios created successfully")
    except Exception as e:
        print(f"   ❌ Task creation error: {e}")
        errors += 1

    # Test 3: Environment reset/step
    print("\n3. Testing environment reset/step...")
    try:
        from cyber_soc_env.env.environment import SOCEnvironment
        from cyber_soc_env.models import SOCAction, ActionType

        env = SOCEnvironment()
        obs = env.reset()
        state = env.state
        assert state.step == 0
        assert not state.done

        action = SOCAction(action_type=ActionType.ANALYZE_LOG, target="10.0.0.55")
        obs = env.step(action)
        state = env.state
        assert state.step == 1
        assert state.score > 0
        print(f"   ✅ Environment works (score={state.score} after 1 step)")
    except Exception as e:
        print(f"   ❌ Environment error: {e}")
        errors += 1

    # Test 4: Grading
    print("\n4. Testing grading...")
    try:
        from cyber_soc_env.graders.grader_task1 import BruteForceGrader
        from cyber_soc_env.tasks.task1_brute_force import BruteForceTask

        scenario = BruteForceTask.build_scenario()
        grader = BruteForceGrader(scenario)
        actions = [
            SOCAction(action_type=ActionType.ANALYZE_LOG, target="10.0.0.55"),
            SOCAction(action_type=ActionType.BLOCK_IP, target="block_ip"),
            SOCAction(action_type=ActionType.ESCALATE, target="team"),
        ]
        result = grader.grade(actions)
        assert result.score == 100
        assert result.passed
        print(f"   ✅ Grading works (score={result.score}, passed={result.passed})")
    except Exception as e:
        print(f"   ❌ Grading error: {e}")
        errors += 1

    # Test 5: FastAPI app
    print("\n5. Testing FastAPI app creation...")
    try:
        from cyber_soc_env.api.app import app
        assert app is not None
        print("   ✅ FastAPI app created")
    except Exception as e:
        print(f"   ❌ FastAPI error: {e}")
        errors += 1

    # Test 6: WebSocket client import
    print("\n6. Testing WebSocket client import...")
    try:
        from cyber_soc_env.client import CyberSOCEnv
        print("   ✅ WebSocket client (CyberSOCEnv) imported")
    except Exception as e:
        print(f"   ❌ Client import error: {e}")
        errors += 1

    # Test 7: grade_episode
    print("\n7. Testing grade_episode...")
    try:
        env = SOCEnvironment()
        env.reset()
        score = env.grade_episode(task_id="task1")
        assert 0.0 <= score <= 1.0
        print(f"   ✅ grade_episode works (score={score})")
    except Exception as e:
        print(f"   ❌ grade_episode error: {e}")
        errors += 1

    # Summary
    print("\n" + "=" * 40)
    if errors == 0:
        print("✅ All smoke tests passed!")
    else:
        print(f"❌ {errors} smoke test(s) failed!")

    return errors


if __name__ == "__main__":
    sys.exit(main())
