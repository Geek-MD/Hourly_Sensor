"""Hourly Sensor integration."""

from __future__ import annotations

from dataclasses import dataclass

import voluptuous as vol
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant
from homeassistant.helpers import config_validation as cv

from .const import (
    CONF_AGGREGATION,
    CONF_HOURS,
    CONF_SOURCE_ENTITY,
    DEFAULT_AGGREGATION,
    DEFAULT_HOURS,
    DOMAIN,
)
from .controller import HourlySensorController

CONFIG_SCHEMA = cv.config_entry_only_config_schema(DOMAIN)
PLATFORMS = (Platform.SENSOR,)


@dataclass(slots=True)
class HourlySensorRuntimeData:
    """Runtime data attached to a config entry."""

    controller: HourlySensorController


HourlySensorConfigEntry = ConfigEntry[HourlySensorRuntimeData]


async def async_setup(hass: HomeAssistant, config: vol.Schema) -> bool:
    """Set up the integration domain."""
    return True


async def async_setup_entry(
    hass: HomeAssistant, entry: HourlySensorConfigEntry
) -> bool:
    """Set up Hourly Sensor from a config entry."""
    controller = HourlySensorController(
        hass,
        entry_id=entry.entry_id,
        source_entity=entry.data[CONF_SOURCE_ENTITY],
        window_hours=entry.data.get(CONF_HOURS, DEFAULT_HOURS),
        aggregation=entry.data.get(CONF_AGGREGATION, DEFAULT_AGGREGATION),
    )
    await controller.async_initialize()
    entry.runtime_data = HourlySensorRuntimeData(controller)
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True


async def async_unload_entry(
    hass: HomeAssistant, entry: HourlySensorConfigEntry
) -> bool:
    """Unload a config entry."""
    if not await hass.config_entries.async_unload_platforms(entry, PLATFORMS):
        return False
    await entry.runtime_data.controller.async_shutdown()
    return True
