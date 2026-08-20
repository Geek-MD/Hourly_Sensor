"""Tests for the Hourly Sensor recalculation button."""

import asyncio
from types import SimpleNamespace

from homeassistant.helpers.entity import EntityCategory

from custom_components.hourly_sensor import button as button_module
from custom_components.hourly_sensor.button import HourlySensorRecalculateButton


def test_button_forces_controller_recalculation() -> None:
    """Pressing the entity delegates the history rebuild to its controller."""
    pressed = 0

    class _Controller:
        async def async_recalculate(self) -> bool:
            nonlocal pressed
            pressed += 1
            return True

    button = object.__new__(HourlySensorRecalculateButton)
    button._controller = _Controller()

    asyncio.run(button.async_press())

    assert pressed == 1
    assert button.entity_category is EntityCategory.CONFIG
    assert button.translation_key == "recalculate"
    assert button.icon == "mdi:history"


def test_button_exposes_source_device_in_config_entry(monkeypatch) -> None:
    """The control uses the same device metadata as its paired sensor."""
    monkeypatch.setattr(
        button_module,
        "device_info_for_source",
        lambda hass, source, **kwargs: {
            "identifiers": {("weather_station", "outdoor")}
        },
    )
    entry = SimpleNamespace(
        entry_id="entry-id",
        title="Hourly rain",
        data={"name": "Hourly rain", "source_entity": "sensor.source"},
        options={},
        runtime_data=SimpleNamespace(controller=object()),
    )

    button = HourlySensorRecalculateButton(SimpleNamespace(), entry)

    assert button.device_info["identifiers"] == {("weather_station", "outdoor")}
    assert button._source_entity == "sensor.source"
