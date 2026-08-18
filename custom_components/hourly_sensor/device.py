"""Attach Hourly Sensor entities to their source entity's device."""

from homeassistant.core import HomeAssistant
from homeassistant.helpers import entity_registry as er


def attach_entity_to_source_device(
    hass: HomeAssistant, entity_id: str, source_entity: str
) -> None:
    """Move an entity registry entry onto the source entity's existing device.

    Updating the entity registry directly is intentional. Supplying ``device_info``
    would make Home Assistant register the source device against this config entry,
    causing an Hourly Sensor entry to be presented as a device integration.
    """
    registry = er.async_get(hass)
    source_entry = registry.async_get(source_entity)
    generated_entry = registry.async_get(entity_id)
    if source_entry is None or generated_entry is None:
        return

    if generated_entry.device_id != source_entry.device_id:
        registry.async_update_entity(entity_id, device_id=source_entry.device_id)
