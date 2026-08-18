"""Tests for Hourly Sensor source-device metadata."""

from types import SimpleNamespace

from custom_components.hourly_sensor import device


def test_generated_entities_use_source_device(monkeypatch) -> None:
    """The source device identifiers and connections are reused."""
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
        SimpleNamespace(), "sensor.outdoor_rain"
    )

    assert device_info is not None
    assert device_info["identifiers"] == {("weather_station", "outdoor")}
    assert device_info["connections"] == {("mac", "00:11:22:33:44:55")}


def test_source_without_device_leaves_entities_unassigned(monkeypatch) -> None:
    """A source without a device does not create a misleading virtual one."""
    entity_registry = SimpleNamespace(
        async_get=lambda entity_id: SimpleNamespace(device_id=None)
    )
    monkeypatch.setattr(device.er, "async_get", lambda hass: entity_registry)

    assert (
        device.device_info_for_source(SimpleNamespace(), "sensor.helper") is None
    )
