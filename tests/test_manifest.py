"""Tests for Hourly Sensor integration metadata."""

import json
from pathlib import Path


def test_manifest_exposes_config_entries_as_an_integration() -> None:
    """Ensure configured sensors remain reachable from Integrations."""
    manifest_path = (
        Path(__file__).parents[1]
        / "custom_components"
        / "hourly_sensor"
        / "manifest.json"
    )
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))

    assert manifest["config_flow"] is True
    assert manifest["after_dependencies"] == ["recorder"]
    assert manifest["integration_type"] == "service"
    assert manifest["version"] == "0.2.1"
