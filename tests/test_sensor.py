"""Tests for the Hourly Sensor entity metadata."""

from types import SimpleNamespace
from typing import Any

from custom_components.hourly_sensor.sensor import HourlySensorEntity


class _States:
    """Minimal state machine used by entity metadata properties."""

    def __init__(self) -> None:
        self.state: Any = None

    def get(self, entity_id: str) -> Any:
        """Return the configured source state."""
        assert entity_id == "sensor.source"
        return self.state


def _entity(states: _States) -> HourlySensorEntity:
    entity = object.__new__(HourlySensorEntity)
    entity._source_entity = "sensor.source"
    entity.hass = SimpleNamespace(states=states)
    return entity


def test_source_metadata_is_inherited() -> None:
    """The generated sensor exposes all relevant source metadata."""
    states = _States()
    states.state = SimpleNamespace(
        attributes={
            "unit_of_measurement": "mm",
            "device_class": "precipitation",
            "state_class": "measurement",
        }
    )
    entity = _entity(states)

    assert entity.native_unit_of_measurement == "mm"
    assert entity.device_class == "precipitation"
    assert entity.state_class == "measurement"


def test_source_metadata_is_resolved_after_source_loads() -> None:
    """Metadata remains dynamic when the source is initially unavailable."""
    states = _States()
    entity = _entity(states)

    assert entity.native_unit_of_measurement is None
    assert entity.device_class is None
    assert entity.state_class is None

    states.state = SimpleNamespace(
        attributes={
            "unit_of_measurement": "mm",
            "device_class": "precipitation",
            "state_class": "measurement",
        }
    )

    assert entity.native_unit_of_measurement == "mm"
    assert entity.device_class == "precipitation"
    assert entity.state_class == "measurement"


def test_last_period_attribute_uses_configured_precision() -> None:
    """The stable completed-period value is available to automations."""
    states = _States()
    entity = _entity(states)
    entity._aggregation = "change"
    entity._hours = 1
    entity._precision = 2
    entity._controller = SimpleNamespace(
        accumulator=SimpleNamespace(
            completed_hours=1,
            last_completed_hour="2026-08-02T10:00:00",
            last_period=1.234,
            sample_statistics=None,
        )
    )

    assert entity.extra_state_attributes["last_period"] == 1.23
