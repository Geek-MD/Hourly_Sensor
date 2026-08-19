"""Tests for Hourly Sensor integration metadata."""

import json
from pathlib import Path


def test_manifest_exposes_plain_config_entries() -> None:
    """Ensure configured sensors are integration entries, not services."""
    manifest_path = (
        Path(__file__).parents[1]
        / "custom_components"
        / "hourly_sensor"
        / "manifest.json"
    )
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))

    assert manifest["config_flow"] is True
    assert manifest["after_dependencies"] == ["recorder"]
    assert "integration_type" not in manifest
    assert manifest["version"] == "0.3.5"
