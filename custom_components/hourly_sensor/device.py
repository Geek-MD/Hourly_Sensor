"""Device metadata shared by Hourly Sensor entities."""

from homeassistant.core import HomeAssistant
from homeassistant.helpers import device_registry as dr
from homeassistant.helpers import entity_registry as er
from homeassistant.helpers.device_registry import DeviceInfo

from . import HourlySensorConfigEntry
from .const import DOMAIN


def device_info_for_entry(
    hass: HomeAssistant,
    entry: HourlySensorConfigEntry,
    source_entity: str,
) -> DeviceInfo:
    """Describe the integration device and its relationship to the source."""
    via_device: tuple[str, str] | None = None
    source_entry = er.async_get(hass).async_get(source_entity)
    if source_entry is not None and source_entry.device_id is not None:
        source_device = dr.async_get(hass).async_get(source_entry.device_id)
        if source_device is not None and source_device.identifiers:
            # DeviceInfo can express a parent relationship through one stable
            # identifier. Keep our own device so it remains visible on the
            # integration page, and link it to the device providing the data.
            via_device = sorted(source_device.identifiers)[0]

    device_info = DeviceInfo(
        identifiers={(DOMAIN, entry.entry_id)},
        name=entry.title,
        manufacturer="Hourly Sensor",
        model="Rolling hourly sensor",
    )
    if via_device is not None:
        device_info["via_device"] = via_device
    return device_info
