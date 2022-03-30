from __future__ import annotations
import os.path
import logging
from custom_components.smartac.const import CONF_CONTROLLER_DATA, CONF_CONTROLLER_TYPE
from custom_components.smartac.controller import ESPHOME_CONTROLLER
from homeassistant.const import Platform
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant

_LOGGER = logging.getLogger(__name__)

COMPONENT_ABS_DIR = os.path.dirname(
    os.path.abspath(__file__))

CODES_AB_DIR = os.path.join(COMPONENT_ABS_DIR, 'codes')

PLATFORMS = [Platform.CLIMATE]


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry
) -> bool:
    entry.add_update_listener(async_reload_entry)
    hass.config_entries.async_setup_platforms(entry, PLATFORMS)
    return True


async def async_unload_entry(
    hass: HomeAssistant, config_entry: ConfigEntry
) -> bool:
    # Forward to the same platform as async_setup_entry did
    return await hass.config_entries.async_unload_platforms(config_entry, PLATFORMS)


async def async_reload_entry(hass: HomeAssistant, config_entry: ConfigEntry) -> None:
    await async_unload_entry(hass, config_entry)
    await async_setup_entry(hass, config_entry)

async def async_migrate_entry(hass: HomeAssistant, config_entry: ConfigEntry) -> bool:
    """Migrate old entry."""
    if config_entry.version == 1:
        data = {**config_entry.data, CONF_CONTROLLER_TYPE:ESPHOME_CONTROLLER}
        data[CONF_CONTROLLER_DATA] = data['controller_service']
        data.pop('controller_service')
        config_entry.version = 2
        hass.config_entries.async_update_entry(
                config_entry,
                data = data,
            )    

    return True