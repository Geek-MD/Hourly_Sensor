"""Tests for Hourly Sensor virtual-device metadata."""

from types import SimpleNamespace

from custom_components.hourly_sensor.const import DOMAIN
from custom_components.hourly_sensor.device import device_info_for_entry


def test_config_entry_has_dedicated_device() -> None:
    """Each helper is exposed as a named device owned by its config entry."""
    entry = SimpleNamespace(entry_id="rain-last-hour", title="Rain last hour")

    device_info = device_info_for_entry(entry)

    assert device_info["identifiers"] == {(DOMAIN, "rain-last-hour")}
    assert device_info["name"] == "Rain last hour"
    assert device_info["manufacturer"] == "Hourly Sensor"
    assert device_info["model"] == "Rolling hourly sensor"
