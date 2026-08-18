"""Tests for Hourly Sensor integration metadata."""

import json
from pathlib import Path


def test_manifest_exposes_config_entries_as_devices() -> None:
    """Ensure configured sensors are categorized as devices."""
    manifest_path = (
        Path(__file__).parents[1]
        / "custom_components"
        / "hourly_sensor"
        / "manifest.json"
    )
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))

    assert manifest["config_flow"] is True
    assert manifest["after_dependencies"] == ["recorder"]
    assert manifest["integration_type"] == "device"
    assert manifest["version"] == "0.3.1"
