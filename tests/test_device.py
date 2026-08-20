"""Tests for Hourly Sensor source-device metadata."""

from types import SimpleNamespace

from custom_components.hourly_sensor import device
from custom_components.hourly_sensor.const import DOMAIN


def test_config_entry_reuses_source_device(monkeypatch) -> None:
    """The source device is exposed inside the Hourly Sensor config entry."""
    source_entry = SimpleNamespace(device_id="source-device")
    source_device = SimpleNamespace(
        identifiers={("weather_station", "outdoor")},
        connections={("mac", "00:11:22:33:44:55")},
    )
    entity_registry = SimpleNamespace(
        async_get=lambda entity_id: (
            source_entry if entity_id == "sensor.outdoor_rain" else None
        )
    )
    device_registry = SimpleNamespace(
        async_get=lambda device_id: (
            source_device if device_id == "source-device" else None
        )
    )
    monkeypatch.setattr(device.er, "async_get", lambda hass: entity_registry)
    monkeypatch.setattr(device.dr, "async_get", lambda hass: device_registry)

    device_info = device.device_info_for_source(
        SimpleNamespace(),
        "sensor.outdoor_rain",
        entry_id="entry-id",
        entry_name="Hourly rain",
    )

    assert device_info["identifiers"] == {("weather_station", "outdoor")}
    assert device_info["connections"] == {("mac", "00:11:22:33:44:55")}


def test_source_without_device_uses_config_entry_device(monkeypatch) -> None:
    """A device-less source still gets the expandable integration layout."""
    entity_registry = SimpleNamespace(
        async_get=lambda entity_id: SimpleNamespace(device_id=None)
    )
    monkeypatch.setattr(device.er, "async_get", lambda hass: entity_registry)

    device_info = device.device_info_for_source(
        SimpleNamespace(),
        "sensor.helper",
        entry_id="entry-id",
        entry_name="Hourly helper",
    )

    assert device_info["identifiers"] == {(DOMAIN, "entry-id")}
    assert device_info["name"] == "Hourly helper"
    assert device_info["manufacturer"] == "Geek-MD"
    assert device_info["model"] == "Hourly Sensor"


def test_missing_source_uses_config_entry_device(monkeypatch) -> None:
    """Setup remains presentable if the source registry entry is missing."""
    entity_registry = SimpleNamespace(async_get=lambda entity_id: None)
    monkeypatch.setattr(device.er, "async_get", lambda hass: entity_registry)

    device_info = device.device_info_for_source(
        SimpleNamespace(),
        "sensor.missing",
        entry_id="entry-id",
        entry_name="Hourly missing",
    )

    assert device_info["identifiers"] == {(DOMAIN, "entry-id")}
