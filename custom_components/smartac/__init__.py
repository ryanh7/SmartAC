from __future__ import annotations
import os.path
import logging
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
