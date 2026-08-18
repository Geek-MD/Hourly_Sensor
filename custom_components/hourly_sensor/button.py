"""Button platform for Hourly Sensor."""

from __future__ import annotations

from homeassistant.components.button import ButtonEntity
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import EntityCategory
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback

from . import HourlySensorConfigEntry
from .const import CONF_SOURCE_ENTITY
from .device import device_info_for_source


async def async_setup_entry(
    hass: HomeAssistant,
    entry: HourlySensorConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """Add the history recalculation button for a configured sensor."""
    async_add_entities([HourlySensorRecalculateButton(hass, entry)])


class HourlySensorRecalculateButton(ButtonEntity):
    """Force an hourly sensor to rebuild itself from Recorder history."""

    _attr_has_entity_name = True
    _attr_entity_category = EntityCategory.CONFIG
    _attr_icon = "mdi:history"
    _attr_translation_key = "recalculate"

    def __init__(self, hass: HomeAssistant, entry: HourlySensorConfigEntry) -> None:
        """Initialize the button."""
        self._controller = entry.runtime_data.controller
        self._attr_unique_id = f"{entry.entry_id}_recalculate"
        config = {**entry.data, **entry.options}
        self._attr_device_info = device_info_for_source(
            hass, config[CONF_SOURCE_ENTITY]
        )

    async def async_press(self) -> None:
        """Rebuild the paired sensor from its source history."""
        await self._controller.async_recalculate()
