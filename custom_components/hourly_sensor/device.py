"""Attach Hourly Sensor entities to their source entity's device."""

from homeassistant.core import HomeAssistant
from homeassistant.helpers import device_registry as dr
from homeassistant.helpers import entity_registry as er


def migrate_config_entry_devices(hass: HomeAssistant, config_entry_id: str) -> None:
    """Remove devices claimed by an entry created before version 0.3.4.

    Older releases supplied ``device_info`` while adding the entities. Home
    Assistant consequently associated the source device (and, in 0.3.2, a virtual
    device) with the Hourly Sensor config entry. Removing that association once
    lets the entry return to the entity-only model; the entity registry links are
    restored separately when each platform is loaded.
    """
    registry = dr.async_get(hass)
    for device_entry in dr.async_entries_for_config_entry(registry, config_entry_id):
        registry.async_update_device(
            device_entry.id, remove_config_entry_id=config_entry_id
        )


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
