"""Tests for source data-type detection."""

from types import SimpleNamespace

import pytest

from custom_components.hourly_sensor.const import (
    SOURCE_TYPE_AUTO,
    SOURCE_TYPE_CUMULATIVE,
    SOURCE_TYPE_INSTANTANEOUS,
)
from custom_components.hourly_sensor.controller import HourlySensorController


@pytest.mark.parametrize(
    ("state_class", "expected"),
    [
        ("total", SOURCE_TYPE_CUMULATIVE),
        ("total_increasing", SOURCE_TYPE_CUMULATIVE),
        ("measurement", SOURCE_TYPE_INSTANTANEOUS),
        (None, SOURCE_TYPE_INSTANTANEOUS),
    ],
)
def test_automatic_source_type_uses_state_class(
    state_class: str | None, expected: str
) -> None:
    """Home Assistant total state classes identify cumulative meters."""
    controller = object.__new__(HourlySensorController)
    controller.configured_source_type = SOURCE_TYPE_AUTO
    controller.source_entity = "sensor.source"
    state = SimpleNamespace(attributes={"state_class": state_class})
    controller.hass = SimpleNamespace(states=SimpleNamespace(get=lambda _: state))

    assert controller._resolve_source_type() == expected


def test_explicit_source_type_overrides_metadata() -> None:
    """Users can correct sources whose integrations publish bad metadata."""
    controller = object.__new__(HourlySensorController)
    controller.configured_source_type = SOURCE_TYPE_INSTANTANEOUS
    controller.source_entity = "sensor.source"
    state = SimpleNamespace(attributes={"state_class": "total_increasing"})
    controller.hass = SimpleNamespace(states=SimpleNamespace(get=lambda _: state))

    assert controller._resolve_source_type() == SOURCE_TYPE_INSTANTANEOUS


def test_storage_from_another_source_is_not_restored() -> None:
    """Editing the source cannot mix its readings with the previous entity."""
    controller = object.__new__(HourlySensorController)
    controller.source_entity = "sensor.new_source"
    controller.source_type = SOURCE_TYPE_CUMULATIVE

    assert not controller._can_restore("sensor.old_source", SOURCE_TYPE_CUMULATIVE)
    assert controller._can_restore("sensor.new_source", SOURCE_TYPE_CUMULATIVE)


def test_storage_from_another_data_type_is_not_restored() -> None:
    """Changing interpretation starts with a clean accumulator."""
    controller = object.__new__(HourlySensorController)
    controller.source_entity = "sensor.source"
    controller.source_type = SOURCE_TYPE_INSTANTANEOUS

    assert not controller._can_restore("sensor.source", SOURCE_TYPE_CUMULATIVE)
