"""Grader for Task 2 – Malware Analysis & Containment."""

from __future__ import annotations

from ..models import SOCAction, ActionType, GradeResult
from .base import BaseGrader


class MalwareGrader(BaseGrader):
    """Grader for the malware analysis task.
    
    Evaluates whether the analyst correctly:
    1. Investigated the malware executable (invoice.exe)
    2. Investigated C2 communication (198.51.100.42)
    3. Blocked the command and control IP
    4. Isolated the infected workstation (WS-042)
    """

    def grade(self, actions: list[SOCAction]) -> GradeResult:
        score = 0.0
        feedback_parts: list[str] = []

        # Normalize targets for case-insensitive matching
        targets_str = " ".join([str(a.target).lower() for a in actions])
        action_types = [a.action_type for a in actions]
        
        # Target identifiers with flexible formatting
        malware_keywords = ["invoice.exe", "invoice"]
        c2_ip = "198.51.100.42"
        workstation = "ws-042"

        # Check investigation of malware sample (invoice.exe)
        investigated_malware = False
        for action in actions:
            if action.action_type == ActionType.ANALYZE_LOG:
                target_lower = str(action.target).lower()
                if any(keyword in target_lower for keyword in malware_keywords):
                    investigated_malware = True
                    break
        
        if investigated_malware:
            score += 25
            feedback_parts.append("✅ Investigated malware executable (invoice.exe)")
        else:
            feedback_parts.append("❌ Did not investigate the malicious file")

        # Check C2 investigation (198.51.100.42)
        investigated_c2 = False
        for action in actions:
            if action.action_type == ActionType.ANALYZE_LOG:
                target_lower = str(action.target).lower()
                if c2_ip in target_lower:
                    investigated_c2 = True
                    break
        
        if investigated_c2:
            score += 25
            feedback_parts.append("✅ Investigated C2 communication (198.51.100.42)")
        else:
            feedback_parts.append("❌ Did not investigate C2 infrastructure")

        # Check containment (blocking C2)
        blocked_c2 = False
        for action in actions:
            if action.action_type == ActionType.BLOCK_IP:
                target_lower = str(action.target).lower()
                if c2_ip in target_lower:
                    blocked_c2 = True
                    break
        
        if blocked_c2:
            score += 30
            feedback_parts.append("✅ Blocked command and control IP")
        else:
            feedback_parts.append("❌ No containment action for C2")

        # Check eradication (isolating workstation WS-042)
        isolated_host = False
        for action in actions:
            if action.action_type == ActionType.ISOLATE_DEVICE:
                target_lower = str(action.target).lower()
                if workstation in target_lower:
                    isolated_host = True
                    break
        
        if isolated_host:
            score += 20
            feedback_parts.append("✅ Isolated infected workstation (WS-042)")
        else:
            feedback_parts.append("⚠️ No isolation performed for the infected host")

        return GradeResult(
            task_id=self.scenario.task_id,
            score=min(score / 100.0, 1.0),
            passed=score >= 70,
            feedback="\n".join(feedback_parts),
            kpis=self._compute_kpis(actions, expected_steps=3)
        )
