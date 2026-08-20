"""Resolve the device displayed for an Hourly Sensor config entry."""

from homeassistant.core import HomeAssistant
from homeassistant.helpers import device_registry as dr
from homeassistant.helpers import entity_registry as er
from homeassistant.helpers.device_registry import DeviceInfo

from .const import DOMAIN


def device_info_for_source(
    hass: HomeAssistant,
    source_entity: str,
    *,
    entry_id: str,
    entry_name: str,
) -> DeviceInfo:
    """Return device metadata matching HA Daily Counter's integration layout.

    A source backed by a device reuses that device's stable identifiers and
    connections. Home Assistant then displays the physical device inside this
    config entry and groups the generated sensor and button beneath it.

    Sources without a device receive one virtual device for their config entry,
    keeping the same expandable integration-entry layout in every case.
    """
    source_entry = er.async_get(hass).async_get(source_entity)
    if source_entry is not None and source_entry.device_id is not None:
        source_device = dr.async_get(hass).async_get(source_entry.device_id)
        if source_device is not None and (
            source_device.identifiers or source_device.connections
        ):
            return DeviceInfo(
                identifiers=set(source_device.identifiers),
                connections=set(source_device.connections),
            )

    return DeviceInfo(
        identifiers={(DOMAIN, entry_id)},
        name=entry_name,
        manufacturer="Geek-MD",
        model="Hourly Sensor",
    )
