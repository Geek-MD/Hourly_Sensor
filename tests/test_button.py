"""Tests for the Hourly Sensor recalculation button."""

import asyncio
from types import SimpleNamespace

from homeassistant.helpers.entity import EntityCategory

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


def test_button_does_not_claim_source_device_for_config_entry() -> None:
    """The control is initially device-less so the entry owns no device."""
    entry = SimpleNamespace(
        entry_id="entry-id",
        title="Hourly rain",
        data={"source_entity": "sensor.source"},
        options={},
        runtime_data=SimpleNamespace(controller=object()),
    )

    button = HourlySensorRecalculateButton(SimpleNamespace(), entry)

    assert button.device_info is None
    assert button._source_entity == "sensor.source"
