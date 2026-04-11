"""SOCAction handlers – process analyst actions and return results."""

from __future__ import annotations

from typing import Any

from ..models import SOCAction, ActionType, SOCState


def handle_action(action: SOCAction, state: SOCState) -> dict[str, Any]:
    """Process an action and return the result.

    Args:
        action: The analyst action to process.
        state: Current environment state.

    Returns:
        Dict with action results and observations.
    """
    handlers = {
        ActionType.ANALYZE_LOG: _handle_investigate,
        ActionType.BLOCK_IP: _handle_contain,
        ActionType.ISOLATE_DEVICE: _handle_eradicate,
        ActionType.MARK_SAFE: _handle_recover,
        ActionType.ESCALATE: _handle_escalate,
        ActionType.RUN_SCAN: _handle_investigate,
        ActionType.CORRELATE_EVENTS: _handle_investigate,
    }
    handler = handlers.get(action.action_type, _handle_unknown)
    return handler(action, state)


def _handle_investigate(action: SOCAction, state: SOCState) -> dict[str, Any]:
    """Handle investigation actions."""
    return {
        "observation": f"Investigation of '{action.target}' complete. Relevant IOCs found.",
        "success": True,
        "terminate": False,
    }


def _handle_contain(action: SOCAction, state: SOCState) -> dict[str, Any]:
    """Handle containment actions."""
    return {
        "observation": f"Containment applied to '{action.target}'. Threat isolated.",
        "success": True,
        "terminate": False,
    }


def _handle_eradicate(action: SOCAction, state: SOCState) -> dict[str, Any]:
    """Handle eradication actions."""
    return {
        "observation": f"Eradication on '{action.target}' executed. Artifacts removed.",
        "success": True,
        "terminate": False,
    }


def _handle_recover(action: SOCAction, state: SOCState) -> dict[str, Any]:
    """Handle recovery actions."""
    return {
        "observation": f"Recovery process for '{action.target}' initiated.",
        "success": True,
        "terminate": True,
    }


def _handle_escalate(action: SOCAction, state: SOCState) -> dict[str, Any]:
    """Handle escalation actions."""
    return {
        "observation": f"Incident escalated regarding '{action.target}'.",
        "success": True,
        "terminate": False,
    }


def _handle_unknown(action: SOCAction, state: SOCState) -> dict[str, Any]:
    """Fallback for unknown action types."""
    return {
        "observation": f"Unknown action type: {action.action_type}",
        "success": False,
        "terminate": False,
    }
