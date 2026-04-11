"""Task 1 – Brute Force Attack Detection."""

from __future__ import annotations

from ..models import Alert, TaskScenario, Difficulty


class BruteForceTask:
    """SSH/RDP brute force attack detection task."""

    TASK_ID = "task1"

    @staticmethod
    def build_scenario() -> TaskScenario:
        """Create the brute force detection scenario."""
        alerts = [
            Alert(
                alert_id="BF-001",
                severity="high",
                source="IDS",
                description="Multiple failed SSH login attempts from 10.0.0.55",
                timestamp="2025-01-15T08:30:00Z",
                raw_log="Jan 15 08:30:00 server sshd[12345]: Failed password for root from 10.0.0.55 port 22",
            ),
            Alert(
                alert_id="BF-002",
                severity="medium",
                source="SIEM",
                description="Account lockout triggered for user admin",
                timestamp="2025-01-15T08:35:00Z",
            ),
            Alert(
                alert_id="BF-003",
                severity="critical",
                source="IDS",
                description="Successful login after 50 failed attempts from 10.0.0.55",
                timestamp="2025-01-15T08:40:00Z",
                raw_log="Jan 15 08:40:00 server sshd[12400]: Accepted password for root from 10.0.0.55 port 22",
            ),
        ]

        return TaskScenario(
            task_id=BruteForceTask.TASK_ID,
            name="Brute Force Attack Detection",
            description="Detect and respond to SSH brute force login attempts targeting a critical server.",
            difficulty=Difficulty.BEGINNER,
            alerts=alerts,
            max_steps=20,
        )
