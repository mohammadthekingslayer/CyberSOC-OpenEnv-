"""WebSocket client for the CyberSOC OpenEnv environment.

Uses the OpenEnv EnvClient base class for persistent WebSocket sessions.
Each connection gets its own isolated environment instance server-side.

Usage (async):
    async with CyberSOCEnv(base_url="http://localhost:8000") as env:
        result = await env.reset(task_id="task1")
        result = await env.step(SOCAction(action_type="analyze_log", target="10.0.0.55"))

Usage (sync wrapper):
    with CyberSOCEnv(base_url="http://localhost:8000").sync() as env:
        result = env.reset(task_id="task1")
        result = env.step(SOCAction(action_type="analyze_log", target="10.0.0.55"))
"""

from __future__ import annotations

from typing import Any, Dict

from openenv_core import HTTPEnvClient as EnvClient
from openenv_core.client_types import StepResult

from .models import SOCAction, SOCObservation, SOCState


class CyberSOCEnv(EnvClient[SOCAction, SOCObservation]):
    """WebSocket client for the CyberSOC OpenEnv environment.

    Provides persistent sessions over WebSocket (/ws endpoint).
    Each step() call is a lightweight frame (~0.1ms overhead) over
    an existing connection, instead of TCP handshake per HTTP request.
    """

    def _step_payload(self, action: SOCAction) -> Dict[str, Any]:
        """Convert SOCAction object to JSON dict for sending over WebSocket."""
        return {
            "action_type": action.action_type.value if hasattr(action.action_type, "value") else action.action_type,
            "target": action.target,
            "reasoning": action.reasoning or "",
        }

    def _parse_result(self, payload: Dict[str, Any]) -> StepResult[SOCObservation]:
        """Convert WebSocket response dict into a StepResult with SOCObservation."""
        obs_data = payload.get("observation", payload)

        observation = SOCObservation(
            logs=obs_data.get("logs", []),
            alerts=obs_data.get("alerts", []),
            network_status=obs_data.get("network_status", {}),
            threat_level=obs_data.get("threat_level", "low"),
            message=obs_data.get("message", ""),
            done=payload.get("done", obs_data.get("done", False)),
            reward=payload.get("reward", obs_data.get("reward", 0.0)) or 0.0,
        )

        return StepResult(
            observation=observation,
            reward=payload.get("reward", obs_data.get("reward")),
            done=payload.get("done", obs_data.get("done", False)),
        )

    def _parse_state(self, payload: Dict[str, Any]) -> SOCState:
        """Convert WebSocket state response dict into SOCState object."""
        return SOCState(
            step=payload.get("step", 0),
            actions_taken=[],  # Actions are SOCAction objects, reconstruct if needed
            score=payload.get("score", 0.0),
            done=payload.get("done", False),
            info=payload.get("info", {}),
        )
