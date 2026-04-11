"""Task 3 – Advanced Persistent Threat (APT) Investigation."""

from __future__ import annotations

from ..models import Alert, TaskScenario, Difficulty


class APTTask:
    """Multi-stage APT campaign investigation task."""

    TASK_ID = "task3"

    @staticmethod
    def build_scenario() -> TaskScenario:
        """Create the APT investigation scenario."""
        alerts = [
            Alert(
                alert_id="APT-001",
                severity="medium",
                source="Email Gateway",
                description="Spear-phishing email with weaponized PDF attachment",
                timestamp="2025-03-01T09:00:00Z",
                raw_log="From: trusted-partner@spoofed.com To: cfo@example.com Subject: Q4 Report",
            ),
            Alert(
                alert_id="APT-002",
                severity="high",
                source="EDR",
                description="Fileless malware execution via macro – LOLBIN abuse detected",
                timestamp="2025-03-01T09:15:00Z",
            ),
            Alert(
                alert_id="APT-003",
                severity="critical",
                source="AD Monitor",
                description="Kerberoasting attempt detected – service ticket requests for SPN sqlsvc",
                timestamp="2025-03-01T10:00:00Z",
            ),
            Alert(
                alert_id="APT-004",
                severity="critical",
                source="SIEM",
                description="Lateral movement via PsExec to domain controller DC-01",
                timestamp="2025-03-01T11:30:00Z",
                raw_log="PsExec connection from WS-042 to DC-01 using compromised svc_sql account",
            ),
            Alert(
                alert_id="APT-005",
                severity="critical",
                source="DLP",
                description="Large data exfiltration to external cloud storage detected",
                timestamp="2025-03-01T14:00:00Z",
            ),
        ]

        return TaskScenario(
            task_id=APTTask.TASK_ID,
            name="Advanced Persistent Threat Investigation",
            description="Investigate a multi-stage APT campaign involving phishing, lateral movement, and data exfiltration.",
            difficulty=Difficulty.ADVANCED,
            alerts=alerts,
            max_steps=50,
        )
