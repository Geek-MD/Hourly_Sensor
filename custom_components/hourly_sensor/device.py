"""Resolve the physical device shared by Hourly Sensor entities."""

from homeassistant.core import HomeAssistant
from homeassistant.helpers import device_registry as dr
from homeassistant.helpers import entity_registry as er
from homeassistant.helpers.device_registry import DeviceInfo


def device_info_for_source(
    hass: HomeAssistant, source_entity: str
) -> DeviceInfo | None:
    """Return identifiers that attach generated entities to the source device."""
    source_entry = er.async_get(hass).async_get(source_entity)
    if source_entry is None or source_entry.device_id is None:
        return None

    source_device = dr.async_get(hass).async_get(source_entry.device_id)
    if source_device is None:
        return None

    # Reusing the source device's stable identifiers/connections makes Home
    # Assistant place the generated sensor and button on that existing device.
    # Its device-level area assignment is therefore inherited automatically.
    return DeviceInfo(
        identifiers=source_device.identifiers,
        connections=source_device.connections,
    )
