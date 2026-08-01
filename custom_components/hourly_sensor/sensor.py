"""Sensor platform for Hourly Sensor."""

from __future__ import annotations

from typing import Any

from homeassistant.components.sensor import SensorEntity
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.device import async_entity_id_to_device
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback

from . import HourlySensorConfigEntry
from .const import (
    CONF_AGGREGATION,
    CONF_HOURS,
    CONF_NAME,
    CONF_PRECISION,
    CONF_SOURCE_ENTITY,
    DEFAULT_AGGREGATION,
    DEFAULT_HOURS,
    DEFAULT_PRECISION,
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: HourlySensorConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """Set up the configured hourly sensor."""
    async_add_entities([HourlySensorEntity(hass, entry)])


class HourlySensorEntity(SensorEntity):
    """Rolling statistic over completed clock hours."""

    _attr_has_entity_name = True

    def __init__(self, hass: HomeAssistant, entry: HourlySensorConfigEntry) -> None:
        """Initialize the sensor."""
        self._controller = entry.runtime_data.controller
        self._source_entity = entry.data[CONF_SOURCE_ENTITY]
        self._aggregation = entry.data.get(CONF_AGGREGATION, DEFAULT_AGGREGATION)
        self._hours = int(entry.data.get(CONF_HOURS, DEFAULT_HOURS))
        self._precision = int(entry.data.get(CONF_PRECISION, DEFAULT_PRECISION))
        self._attr_name = entry.data[CONF_NAME]
        self._attr_unique_id = entry.entry_id
        self._attr_suggested_display_precision = self._precision

        source_state = hass.states.get(self._source_entity)
        if source_state is not None:
            self._attr_native_unit_of_measurement = source_state.attributes.get(
                "unit_of_measurement"
            )
            self._attr_device_class = source_state.attributes.get("device_class")

        # Home Assistant 2026.8+ helper integrations link entities directly to
        # the source device instead of merging config entries through DeviceInfo.
        self.device_entry = async_entity_id_to_device(hass, self._source_entity)

    async def async_added_to_hass(self) -> None:
        """Subscribe to controller updates."""
        await super().async_added_to_hass()
        self.async_on_remove(
            self._controller.async_add_listener(self._async_controller_updated)
        )

    @callback
    def _async_controller_updated(self) -> None:
        self.async_write_ha_state()

    @property
    def native_value(self) -> float | None:
        """Return the rolling statistic."""
        value = self._controller.accumulator.value
        return None if value is None else round(value, self._precision)

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return useful diagnostic details."""
        source_state = self.hass.states.get(self._source_entity)
        attributes: dict[str, Any] = {
            "source_entity": self._source_entity,
            "aggregation": self._aggregation,
            "window_hours": self._hours,
            "completed_hours": min(
                self._controller.accumulator.completed_hours, self._hours
            ),
            "last_completed_hour": (self._controller.accumulator.last_completed_hour),
            "source_available": source_state is not None
            and source_state.state not in ("unknown", "unavailable"),
        }
        statistics = self._controller.accumulator.sample_statistics
        if statistics is not None:
            attributes.update(
                {
                    key: round(value, self._precision)
                    for key, value in statistics.items()
                }
            )
        return attributes
