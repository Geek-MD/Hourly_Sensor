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
