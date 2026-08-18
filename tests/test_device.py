"""Tests for Hourly Sensor device metadata."""

from types import SimpleNamespace

from custom_components.hourly_sensor import device


def _entry() -> SimpleNamespace:
    return SimpleNamespace(entry_id="entry-id", title="Hourly rain")


def test_integration_device_is_linked_to_source_device(monkeypatch) -> None:
    """A dedicated integration device points to the physical source device."""
    source_entry = SimpleNamespace(device_id="source-device")
    source_device = SimpleNamespace(
        identifiers={("weather_station", "outdoor")},
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

    device_info = device.device_info_for_entry(
        SimpleNamespace(), _entry(), "sensor.outdoor_rain"
    )

    assert device_info["identifiers"] == {("hourly_sensor", "entry-id")}
    assert device_info["name"] == "Hourly rain"
    assert device_info["via_device"] == ("weather_station", "outdoor")


def test_source_without_device_keeps_integration_device(monkeypatch) -> None:
    """A helper source still gets a device on the integration page."""
    entity_registry = SimpleNamespace(
        async_get=lambda entity_id: SimpleNamespace(device_id=None)
    )
    monkeypatch.setattr(device.er, "async_get", lambda hass: entity_registry)

    device_info = device.device_info_for_entry(
        SimpleNamespace(), _entry(), "sensor.helper"
    )

    assert device_info["identifiers"] == {("hourly_sensor", "entry-id")}
    assert "via_device" not in device_info
