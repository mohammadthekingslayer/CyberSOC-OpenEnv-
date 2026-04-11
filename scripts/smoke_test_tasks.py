"""Smoke test for CyberSOC tasks – verifies perfect score for all 3 scenarios."""

import os
import sys

# Add src to path
sys.path.append(os.path.join(os.path.dirname(__file__), "..", "src"))

from cyber_soc_env.env.environment import SOCEnvironment
from cyber_soc_env.models import SOCAction, ActionType

def test_task1():
    print("\n--- Testing Task 1: Brute Force ---")
    env = SOCEnvironment(task_id="task1")
    obs = env.reset()
    print(f"Initial: {obs.message}")
    
    actions = [
        SOCAction(action_type=ActionType.ANALYZE_LOG, target="10.0.0.55", reasoning="Investigating source"),
        SOCAction(action_type=ActionType.BLOCK_IP, target="10.0.0.55", reasoning="Blocking attacker"),
        SOCAction(action_type=ActionType.ESCALATE, target="Security Team", reasoning="Escalating incident"),
    ]
    
    for action in actions:
        obs = env.step(action)
        print(f"Step: {obs.message} | Reward: {obs.reward}")
        
    score = env.grade_episode()
    print(f"FINAL SCORE: {score}")
    assert score == 1.0, f"Task 1 failed with score {score}"

def test_task2():
    print("\n--- Testing Task 2: Malware ---")
    env = SOCEnvironment(task_id="task2")
    obs = env.reset()
    print(f"Initial: {obs.message}")
    
    actions = [
        SOCAction(action_type=ActionType.ANALYZE_LOG, target="invoice.exe", reasoning="Analyzing payload"),
        SOCAction(action_type=ActionType.ANALYZE_LOG, target="198.51.100.42", reasoning="Investigating C2"),
        SOCAction(action_type=ActionType.BLOCK_IP, target="198.51.100.42", reasoning="Blocking C2"),
        SOCAction(action_type=ActionType.ISOLATE_DEVICE, target="WS-042", reasoning="Isolating infected host"),
    ]
    
    for action in actions:
        obs = env.step(action)
        print(f"Step: {obs.message} | Reward: {obs.reward}")
        
    score = env.grade_episode()
    print(f"FINAL SCORE: {score}")
    assert score == 1.0, f"Task 2 failed with score {score}"

def test_task3():
    print("\n--- Testing Task 3: APT ---")
    env = SOCEnvironment(task_id="task3")
    obs = env.reset()
    print(f"Initial: {obs.message}")
    
    actions = [
        SOCAction(action_type=ActionType.ANALYZE_LOG, target="PDF attachment", reasoning="Phishing vector"),
        SOCAction(action_type=ActionType.ANALYZE_LOG, target="DC-01", reasoning="Lateral movement"),
        SOCAction(action_type=ActionType.BLOCK_IP, target="WS-042", reasoning="Containment"),
        SOCAction(action_type=ActionType.ISOLATE_DEVICE, target="DC-01", reasoning="Eradication"),
        SOCAction(action_type=ActionType.ESCALATE, target="Management", reasoning="Reporting"),
        SOCAction(action_type=ActionType.MARK_SAFE, target="DC-01", reasoning="Recovery"),
    ]
    
    for action in actions:
        obs = env.step(action)
        print(f"Step: {obs.message} | Reward: {obs.reward}")
        
    score = env.grade_episode()
    print(f"FINAL SCORE: {score}")
    assert score == 1.0, f"Task 3 failed with score {score}"

if __name__ == "__main__":
    try:
        test_task1()
        test_task2()
        test_task3()
        print("\n✅ ALL TASKS VERIFIED PERFECTLY (1.0 SCORE)!")
    except Exception as e:
        print(f"\n❌ SMOKE TEST FAILED: {e}")
        sys.exit(1)
