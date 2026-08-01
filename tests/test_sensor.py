"""Tests for metadata exposed by the hourly sensor entity."""

from types import SimpleNamespace

from homeassistant.components.sensor import SensorDeviceClass, SensorStateClass
from homeassistant.core import State

from custom_components.hourly_sensor.sensor import HourlySensorEntity


class _States:
    """Minimal state machine used by metadata property tests."""

    def __init__(self, state: State | None) -> None:
        self.state = state

    def get(self, entity_id: str) -> State | None:
        assert entity_id == "sensor.rain"
        return self.state


def _entity(source_state: State | None) -> HourlySensorEntity:
    entity = HourlySensorEntity.__new__(HourlySensorEntity)
    entity._source_entity = "sensor.rain"
    entity.hass = SimpleNamespace(states=_States(source_state))
    return entity


def test_source_metadata_is_exposed() -> None:
    """Unit, device class, and state class come from the source sensor."""
    entity = _entity(
        State(
            "sensor.rain",
            "0",
            {
                "unit_of_measurement": "mm",
                "device_class": SensorDeviceClass.PRECIPITATION.value,
                "state_class": SensorStateClass.MEASUREMENT.value,
            },
        )
    )

    assert entity.native_unit_of_measurement == "mm"
    assert entity.device_class == SensorDeviceClass.PRECIPITATION
    assert entity.state_class == SensorStateClass.MEASUREMENT


def test_source_metadata_can_appear_after_entity_creation() -> None:
    """Metadata is read dynamically rather than cached during initialization."""
    entity = _entity(None)

    assert entity.native_unit_of_measurement is None
    assert entity.device_class is None
    assert entity.state_class is None

    entity.hass.states.state = State(
        "sensor.rain",
        "0",
        {
            "unit_of_measurement": "mm",
            "device_class": SensorDeviceClass.PRECIPITATION.value,
            "state_class": SensorStateClass.MEASUREMENT.value,
        },
    )

    assert entity.native_unit_of_measurement == "mm"
    assert entity.device_class == SensorDeviceClass.PRECIPITATION
    assert entity.state_class == SensorStateClass.MEASUREMENT
