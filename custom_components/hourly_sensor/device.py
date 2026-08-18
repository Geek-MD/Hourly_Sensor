"""Device metadata shared by Hourly Sensor entities."""

from homeassistant.helpers.device_registry import DeviceInfo

from . import HourlySensorConfigEntry
from .const import DOMAIN


def device_info_for_entry(entry: HourlySensorConfigEntry) -> DeviceInfo:
    """Describe the virtual device represented by one config entry."""
    return DeviceInfo(
        identifiers={(DOMAIN, entry.entry_id)},
        name=entry.title,
        manufacturer="Hourly Sensor",
        model="Rolling hourly sensor",
    )
