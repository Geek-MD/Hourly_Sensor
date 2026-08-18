"""Tests for Hourly Sensor source-device association."""

from types import SimpleNamespace

from custom_components.hourly_sensor import device


def test_existing_config_entry_device_associations_are_removed(monkeypatch) -> None:
    """All devices claimed by a legacy config entry are released."""
    devices = [SimpleNamespace(id="source-device"), SimpleNamespace(id="virtual")]
    updates: list[tuple[str, str]] = []
    device_registry = SimpleNamespace(
        async_update_device=lambda device_id, **changes: updates.append(
            (device_id, changes["remove_config_entry_id"])
        )
    )
    monkeypatch.setattr(device.dr, "async_get", lambda hass: device_registry)
    monkeypatch.setattr(
        device.dr,
        "async_entries_for_config_entry",
        lambda registry, entry_id: devices,
    )

    device.migrate_config_entry_devices(SimpleNamespace(), "legacy-entry")

    assert updates == [
        ("source-device", "legacy-entry"),
        ("virtual", "legacy-entry"),
    ]


def test_generated_entity_is_moved_to_source_device(monkeypatch) -> None:
    """The entity registry relation is updated without registering a device."""
    entries = {
        "sensor.outdoor_rain": SimpleNamespace(device_id="source-device"),
        "sensor.hourly_rain": SimpleNamespace(device_id=None),
    }
    updates: list[tuple[str, str | None]] = []
    entity_registry = SimpleNamespace(
        async_get=lambda entity_id: entries.get(entity_id),
        async_update_entity=lambda entity_id, **changes: updates.append(
            (entity_id, changes["device_id"])
        ),
    )
    monkeypatch.setattr(device.er, "async_get", lambda hass: entity_registry)

    device.attach_entity_to_source_device(
        SimpleNamespace(), "sensor.hourly_rain", "sensor.outdoor_rain"
    )

    assert updates == [("sensor.hourly_rain", "source-device")]


def test_source_without_device_leaves_entity_unassigned(monkeypatch) -> None:
    """A helper source makes the generated entity device-less too."""
    entries = {
        "sensor.helper": SimpleNamespace(device_id=None),
        "sensor.hourly_helper": SimpleNamespace(device_id="old-device"),
    }
    updates: list[tuple[str, str | None]] = []
    entity_registry = SimpleNamespace(
        async_get=lambda entity_id: entries.get(entity_id),
        async_update_entity=lambda entity_id, **changes: updates.append(
            (entity_id, changes["device_id"])
        ),
    )
    monkeypatch.setattr(device.er, "async_get", lambda hass: entity_registry)

    device.attach_entity_to_source_device(
        SimpleNamespace(), "sensor.hourly_helper", "sensor.helper"
    )

    assert updates == [("sensor.hourly_helper", None)]


def test_missing_registry_entry_is_ignored(monkeypatch) -> None:
    """Setup tolerates a source entity that has no registry entry."""
    entity_registry = SimpleNamespace(
        async_get=lambda entity_id: None,
        async_update_entity=lambda *args, **kwargs: None,
    )
    monkeypatch.setattr(device.er, "async_get", lambda hass: entity_registry)

    device.attach_entity_to_source_device(
        SimpleNamespace(), "sensor.hourly_helper", "sensor.missing"
    )
