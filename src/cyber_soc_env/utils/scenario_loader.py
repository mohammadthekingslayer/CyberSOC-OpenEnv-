"""Scenario loader – reads task scenarios from YAML/JSON files."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml

from ..models import TaskScenario


def load_scenario(path: str | Path) -> dict[str, Any]:
    """Load a scenario definition from a YAML file.

    Args:
        path: Path to the scenario YAML file.

    Returns:
        Parsed scenario dictionary.
    """
    path = Path(path)
    if not path.exists():
        raise FileNotFoundError(f"Scenario file not found: {path}")

    with open(path) as f:
        return yaml.safe_load(f)


def load_all_scenarios(directory: str | Path) -> list[dict[str, Any]]:
    """Load all YAML scenario files from a directory."""
    directory = Path(directory)
    scenarios = []
    for yaml_file in sorted(directory.glob("*.yaml")):
        scenarios.append(load_scenario(yaml_file))
    return scenarios
