"""Tests for the Hourly Sensor recalculation button."""

import asyncio

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
    assert button.translation_key == "recalculate"
    assert button.icon == "mdi:history"
