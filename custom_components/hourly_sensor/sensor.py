"""Sensor platform for Hourly Sensor."""

from __future__ import annotations

from typing import Any, cast

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorStateClass,
)
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback

from . import HourlySensorConfigEntry
from .const import (
    CONF_AGGREGATION,
    CONF_HOURS,
    CONF_NAME,
    CONF_PRECISION,
    CONF_SOURCE_ENTITY,
    CONF_SOURCE_TYPE,
    DEFAULT_AGGREGATION,
    DEFAULT_HOURS,
    DEFAULT_PRECISION,
    DEFAULT_SOURCE_TYPE,
)
from .device import attach_entity_to_source_device


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
        config = {**entry.data, **entry.options}
        self._controller = entry.runtime_data.controller
        self._source_entity = config[CONF_SOURCE_ENTITY]
        self._aggregation = config.get(CONF_AGGREGATION, DEFAULT_AGGREGATION)
        self._configured_source_type = config.get(CONF_SOURCE_TYPE, DEFAULT_SOURCE_TYPE)
        self._hours = int(config.get(CONF_HOURS, DEFAULT_HOURS))
        self._precision = int(config.get(CONF_PRECISION, DEFAULT_PRECISION))
        self._attr_name = config[CONF_NAME]
        self._attr_unique_id = entry.entry_id
        self._attr_suggested_display_precision = self._precision

    async def async_added_to_hass(self) -> None:
        """Subscribe to controller updates."""
        await super().async_added_to_hass()
        attach_entity_to_source_device(self.hass, self.entity_id, self._source_entity)
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
    def native_unit_of_measurement(self) -> str | None:
        """Return the source sensor's current unit of measurement."""
        return cast(str | None, self._source_attribute("unit_of_measurement"))

    @property
    def device_class(self) -> SensorDeviceClass | None:
        """Return the source sensor's current device class."""
        return cast(SensorDeviceClass | None, self._source_attribute("device_class"))

    @property
    def state_class(self) -> SensorStateClass | None:
        """Return the source sensor's current state class."""
        # A rolling value can decrease as its oldest hour expires, so it must
        # not advertise itself as a monotonically increasing total.
        if self._source_attribute("state_class") is None:
            return None
        return SensorStateClass.MEASUREMENT

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return useful diagnostic details."""
        source_state = self.hass.states.get(self._source_entity)
        attributes: dict[str, Any] = {
            "source_entity": self._source_entity,
            "aggregation": self._aggregation,
            "source_type": self._controller.source_type,
            "source_type_configured": self._configured_source_type,
            "window_hours": self._hours,
            "completed_hours": min(
                self._controller.accumulator.completed_hours, self._hours
            ),
            "last_completed_hour": (self._controller.accumulator.last_completed_hour),
            "last_period": (
                None
                if self._controller.accumulator.last_period is None
                else round(
                    self._controller.accumulator.last_period,
                    self._precision,
                )
            ),
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

    def _source_attribute(self, attribute: str) -> Any:
        """Return an attribute from the source state when it is available."""
        source_state = self.hass.states.get(self._source_entity)
        return None if source_state is None else source_state.attributes.get(attribute)
