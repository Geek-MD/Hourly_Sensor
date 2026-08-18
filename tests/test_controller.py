"""Tests for source data-type detection."""

import asyncio
from datetime import UTC, datetime
from types import SimpleNamespace

import pytest
from homeassistant.core import State

from custom_components.hourly_sensor import controller as controller_module
from custom_components.hourly_sensor.const import (
    SOURCE_TYPE_AUTO,
    SOURCE_TYPE_CUMULATIVE,
    SOURCE_TYPE_INSTANTANEOUS,
)
from custom_components.hourly_sensor.controller import HourlySensorController
from custom_components.hourly_sensor.model import HourlyAccumulator


def _moment(hour: int, minute: int = 0) -> datetime:
    return datetime(2026, 8, 2, hour, minute, tzinfo=UTC)


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


def test_recorder_history_rebuilds_changed_cumulative_source() -> None:
    """A source change retains cumulative growth already recorded in the window."""
    controller = object.__new__(HourlySensorController)
    controller.accumulator = HourlyAccumulator(2, "change")
    states = [
        State("sensor.source", "0.0", last_updated=_moment(10)),
        State("sensor.source", "0.3", last_updated=_moment(10, 20)),
        State("sensor.source", "0.3", last_updated=_moment(11)),
    ]

    controller._add_historical_states(states)

    assert controller.accumulator.value == pytest.approx(0.3)


def test_manual_recalculation_replaces_window_from_recorder(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """The manual action replaces stale buckets and notifies its sensor."""
    states = [
        State("sensor.source", "1", last_updated=_moment(10)),
        State("sensor.source", "3", last_updated=_moment(10, 30)),
        State("sensor.source", "4", last_updated=_moment(11)),
    ]

    class _Recorder:
        async def async_add_executor_job(self, target: object, *args: object) -> object:
            return {"sensor.source": states}

    controller = object.__new__(HourlySensorController)
    controller.hass = SimpleNamespace()
    controller.source_entity = "sensor.source"
    controller.accumulator = HourlyAccumulator(1, "change")
    controller._numeric_state = lambda: 4.0
    updates = 0

    def updated() -> None:
        nonlocal updates
        updates += 1

    controller._updated = updated
    monkeypatch.setattr(controller_module, "get_instance", lambda hass: _Recorder())
    monkeypatch.setattr(controller_module.dt_util, "now", lambda: _moment(11, 15))

    assert asyncio.run(controller.async_recalculate())
    assert controller.accumulator.value == pytest.approx(2.0)
    assert updates == 1


def test_manual_recalculation_preserves_data_without_history(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """An empty Recorder result must not erase the existing calculation."""

    class _Recorder:
        async def async_add_executor_job(self, target: object, *args: object) -> object:
            return {"sensor.source": []}

    controller = object.__new__(HourlySensorController)
    controller.hass = SimpleNamespace()
    controller.source_entity = "sensor.source"
    controller.accumulator = HourlyAccumulator(1, "change")
    original = controller.accumulator
    controller._updated = lambda: None
    monkeypatch.setattr(controller_module, "get_instance", lambda hass: _Recorder())

    assert not asyncio.run(controller.async_recalculate())
    assert controller.accumulator is original
