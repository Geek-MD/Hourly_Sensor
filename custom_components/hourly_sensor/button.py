"""Button platform for Hourly Sensor."""

from __future__ import annotations

from homeassistant.components.button import ButtonEntity
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import EntityCategory
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback

from . import HourlySensorConfigEntry
from .const import CONF_SOURCE_ENTITY
from .device import attach_entity_to_source_device


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
        self._source_entity = config[CONF_SOURCE_ENTITY]

    async def async_added_to_hass(self) -> None:
        """Attach the button to the source entity's existing device."""
        await super().async_added_to_hass()
        attach_entity_to_source_device(self.hass, self.entity_id, self._source_entity)

    async def async_press(self) -> None:
        """Rebuild the paired sensor from its source history."""
        await self._controller.async_recalculate()
