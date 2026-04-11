"""Validators for CyberSOC OpenEnv data structures."""

from __future__ import annotations

from ..models import SOCAction, ActionType


def validate_action(action: SOCAction) -> list[str]:
    """Validate an analyst action and return a list of issues.

    Args:
        action: The action to validate.

    Returns:
        List of validation error messages (empty if valid).
    """
    issues: list[str] = []

    if not action.target or not action.target.strip():
        issues.append("SOCAction target cannot be empty")

    if action.action_type not in ActionType:
        issues.append(f"Invalid action type: {action.action_type}")

    if len(action.target) > 500:
        issues.append("SOCAction target exceeds maximum length (500 chars)")

    return issues
