"""Grader for Task 1 – Brute Force Attack Detection."""

from __future__ import annotations

from ..models import SOCAction, ActionType, GradeResult
from .base import BaseGrader


class BruteForceGrader(BaseGrader):
    """Grader for the brute force detection task.
    
    Evaluates whether the analyst correctly:
    1. Investigated the attacker IP (10.0.0.55)
    2. Blocked the malicious IP at the firewall
    3. Escalated the incident appropriately
    """

    def grade(self, actions: list[SOCAction]) -> GradeResult:
        score = 0.0
        feedback_parts: list[str] = []
        
        # Normalize targets for case-insensitive, flexible matching
        targets_str = " ".join([str(a.target).lower() for a in actions])
        action_types = [a.action_type for a in actions]
        
        # Target IP with flexible formatting (handles "10.0.0.55", "IP: 10.0.0.55", etc.)
        target_ip = "10.0.0.55"

        # Check if analyst investigated the source IP
        investigated = False
        for action in actions:
            if action.action_type == ActionType.ANALYZE_LOG:
                target_lower = str(action.target).lower()
                if target_ip in target_lower:
                    investigated = True
                    break
        
        if investigated:
            score += 30
            feedback_parts.append("✅ Investigated attacker IP 10.0.0.55")
        else:
            feedback_parts.append("❌ Did not investigate attacker IP 10.0.0.55")

        # Check if analyst blocked the malicious IP
        blocked = False
        for action in actions:
            if action.action_type == ActionType.BLOCK_IP:
                target_lower = str(action.target).lower()
                if target_ip in target_lower:
                    blocked = True
                    break
        
        if blocked:
            score += 40
            feedback_parts.append("✅ Successfully blocked malicious IP")
        else:
            feedback_parts.append("❌ Failed to block the source of the brute force")

        # Check if analyst escalated
        if ActionType.ESCALATE in action_types:
            score += 30
            feedback_parts.append("✅ Escalated incident appropriately")
        else:
            feedback_parts.append("⚠️ No escalation performed")

        return GradeResult(
            task_id=self.scenario.task_id,
            score=min(score / 100.0, 1.0),
            passed=score >= 70,
            feedback="\n".join(feedback_parts),
            kpis=self._compute_kpis(actions, expected_steps=2)
        )
