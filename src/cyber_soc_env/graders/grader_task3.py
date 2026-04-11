"""Grader for Task 3 – APT Investigation."""

from __future__ import annotations

from ..models import SOCAction, ActionType, GradeResult
from .base import BaseGrader


class APTGrader(BaseGrader):
    """Grader for the APT investigation task.
    
    Evaluates a multi-stage APT response:
    1. Phishing delivery vector investigation (PDF, CFO email)
    2. Lateral movement detection (DC-01)
    3. Containment of infection source (WS-042)
    4. Eradication on sensitive assets (DC-01, SPN)
    5. Proper escalation
    6. Recovery and post-incident actions
    """

    def grade(self, actions: list[SOCAction]) -> GradeResult:
        score = 0.0
        feedback_parts: list[str] = []

        # Normalize targets for case-insensitive matching
        targets_str = " ".join([str(a.target).lower() for a in actions])
        action_types = [a.action_type for a in actions]
        
        # Target identifiers with flexible formatting
        phishing_keywords = ["pdf", "cfo@example.com", "cfo"]
        dc_host = "dc-01"
        infection_source = "ws-042"
        eradication_keywords = ["dc-01", "spn"]

        # Check phishing investigation (cfo@example.com or weaponized PDF)
        investigated_phishing = False
        for action in actions:
            if action.action_type == ActionType.ANALYZE_LOG:
                target_lower = str(action.target).lower()
                if any(keyword in target_lower for keyword in phishing_keywords):
                    investigated_phishing = True
                    break
        
        if investigated_phishing:
            score += 15
            feedback_parts.append("✅ Investigated phishing delivery vector")
        else:
            feedback_parts.append("❌ Did not investigate phishing delivery")

        # Check lateral movement investigation (DC-01)
        investigated_lateral = False
        for action in actions:
            if action.action_type == ActionType.ANALYZE_LOG:
                target_lower = str(action.target).lower()
                if dc_host in target_lower:
                    investigated_lateral = True
                    break
        
        if investigated_lateral:
            score += 20
            feedback_parts.append("✅ Identified lateral movement to Domain Controller")
        else:
            feedback_parts.append("❌ Did not investigate lateral movement")

        # Check containment (Blocking the compromised IP WS-042)
        contained_source = False
        for action in actions:
            if action.action_type == ActionType.BLOCK_IP:
                target_lower = str(action.target).lower()
                if infection_source in target_lower:
                    contained_source = True
                    break
        
        if contained_source:
            score += 25
            feedback_parts.append("✅ Contained the infection source (WS-042)")
        else:
            feedback_parts.append("❌ Did not contain infection source")

        # Check eradication (Isolating DC-01 or resetting SPN)
        eradicated = False
        for action in actions:
            if action.action_type == ActionType.ISOLATE_DEVICE:
                target_lower = str(action.target).lower()
                if any(keyword in target_lower for keyword in eradication_keywords):
                    eradicated = True
                    break
        
        if eradicated:
            score += 20
            feedback_parts.append("✅ Performed eradication on sensitive tier-0 assets")
        else:
            feedback_parts.append("❌ No eradication performed")

        # Check escalation
        if ActionType.ESCALATE in action_types:
            score += 10
            feedback_parts.append("✅ Escalated the multi-stage incident")
        else:
            feedback_parts.append("⚠️ No escalation performed")

        # Check recovery
        if ActionType.MARK_SAFE in action_types:
            score += 10
            feedback_parts.append("✅ Initiated recovery and post-incident review")
        else:
            feedback_parts.append("⚠️ No recovery actions taken")

        if not feedback_parts:
            feedback_parts.append("❌ No relevant defense actions identified")

        return GradeResult(
            task_id=self.scenario.task_id,
            score=min(score / 100.0, 1.0),
            passed=score >= 70,
            feedback="\n".join(feedback_parts),
        )
