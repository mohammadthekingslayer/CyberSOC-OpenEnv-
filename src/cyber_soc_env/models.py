"""Typed models for CyberSOC OpenEnv — dataclass-based for OpenEnv SDK compatibility."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Optional

from pydantic import BaseModel, Field
from openenv_core.env_server.types import Action as BaseAction, Observation as BaseObservation, State as BaseState


class Difficulty(str, Enum):
    """Task difficulty levels."""
    BEGINNER = "beginner"
    INTERMEDIATE = "intermediate"
    ADVANCED = "advanced"


class ActionType(str, Enum):
    """Types of SOC analyst actions."""
    ANALYZE_LOG = "analyze_log"
    BLOCK_IP = "block_ip"
    ISOLATE_DEVICE = "isolate_device"
    MARK_SAFE = "mark_safe"
    ESCALATE = "escalate"
    RUN_SCAN = "run_scan"
    CORRELATE_EVENTS = "correlate_events"


class Alert(BaseModel):
    """Security alert model (Pydantic for easy serialization)."""
    alert_id: str = Field(..., description="Unique alert identifier")
    severity: str = Field(..., description="Alert severity: low, medium, high, critical")
    source: str = Field(..., description="Alert source system")
    description: str = Field(..., description="Alert description")
    timestamp: str = Field(..., description="ISO 8601 timestamp")
    raw_log: Optional[str] = Field(None, description="Raw log data")
    metadata: dict[str, Any] = Field(default_factory=dict)


@dataclass
class SOCAction(BaseAction):
    """SOC analyst action — extends OpenEnv Action dataclass."""
    action_type: str = ""
    target: str = ""
    reasoning: Optional[str] = None

    def __post_init__(self):
        """Coerce string action_type to ActionType enum when deserialized from JSON."""
        if isinstance(self.action_type, str) and self.action_type:
            try:
                self.action_type = ActionType(self.action_type)
            except ValueError:
                pass  # Keep as string if not a valid enum value


@dataclass
class SOCObservation(BaseObservation):
    """Observation returned after an action — extends OpenEnv Observation dataclass."""
    logs: list[str] = field(default_factory=list)
    alerts: list[str] = field(default_factory=list)
    network_status: dict[str, Any] = field(default_factory=dict)
    threat_level: str = "low"
    message: str = ""


@dataclass
class SOCState(BaseState):
    """Current state of the SOC environment — extends OpenEnv State dataclass."""
    step: int = 0
    alerts_data: list[dict] = field(default_factory=list)
    actions_taken: list[dict] = field(default_factory=list)
    score: float = 0.0
    done: bool = False
    info: dict[str, Any] = field(default_factory=dict)


class GradeResult(BaseModel):
    """Result of grading an analyst's response."""
    task_id: str
    score: float = Field(..., ge=0.0, le=1.0)
    max_score: float = 1.0
    passed: bool = False
    feedback: str = ""
    details: dict[str, Any] = Field(default_factory=dict)
    kpis: dict[str, Any] = Field(default_factory=dict)


class TaskScenario(BaseModel):
    """A SOC task scenario definition."""
    task_id: str
    name: str
    description: str
    difficulty: str
    alerts: list[Alert] = Field(default_factory=list)
    expected_actions: list[dict] = Field(default_factory=list)
    max_steps: int = 50
    time_limit_seconds: Optional[int] = None
