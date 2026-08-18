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
    CONF_SOURCE_TYPE,
    DEFAULT_AGGREGATION,
    DEFAULT_HOURS,
    DEFAULT_SOURCE_TYPE,
    DOMAIN,
)
from .controller import HourlySensorController
from .device import migrate_config_entry_devices

CONFIG_SCHEMA = cv.config_entry_only_config_schema(DOMAIN)
PLATFORMS = (Platform.SENSOR, Platform.BUTTON)


@dataclass(slots=True)
class HourlySensorRuntimeData:
    """Runtime data attached to a config entry."""

    controller: HourlySensorController


HourlySensorConfigEntry = ConfigEntry[HourlySensorRuntimeData]


async def async_setup(hass: HomeAssistant, config: vol.Schema) -> bool:
    """Set up the integration domain."""
    return True


async def async_migrate_entry(
    hass: HomeAssistant, entry: HourlySensorConfigEntry
) -> bool:
    """Migrate legacy data and device-based entries to the current model."""
    if entry.version == 1:
        data = {**entry.data, CONF_SOURCE_TYPE: DEFAULT_SOURCE_TYPE}
        hass.config_entries.async_update_entry(entry, data=data)
    if entry.version < 3:
        migrate_config_entry_devices(hass, entry.entry_id)
        hass.config_entries.async_update_entry(entry, version=3)
    return True


async def async_setup_entry(
    hass: HomeAssistant, entry: HourlySensorConfigEntry
) -> bool:
    """Set up Hourly Sensor from a config entry."""
    config = {**entry.data, **entry.options}
    controller = HourlySensorController(
        hass,
        entry_id=entry.entry_id,
        source_entity=config[CONF_SOURCE_ENTITY],
        window_hours=config.get(CONF_HOURS, DEFAULT_HOURS),
        aggregation=config.get(CONF_AGGREGATION, DEFAULT_AGGREGATION),
        source_type=config.get(CONF_SOURCE_TYPE, DEFAULT_SOURCE_TYPE),
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
