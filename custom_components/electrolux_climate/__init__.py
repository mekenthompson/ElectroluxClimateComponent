"""The Electrolux Control integration."""

from __future__ import annotations

import base64

import broadlink
from broadlink.exceptions import BroadlinkException, NetworkTimeoutError

from homeassistant.components.climate.const import ATTR_MAX_TEMP, ATTR_MIN_TEMP
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_HOST, CONF_MAC, CONF_NAME, CONF_TIMEOUT
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryNotReady

from .const import DEFAULT_MAX, DEFAULT_MIN, DOMAIN, PLATFORMS
from .coordinator import ElectroluxCoordinator
from .electrolux import DEVICE_TYPE, electrolux


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    host = entry.data[CONF_HOST]
    mac = bytes.fromhex(entry.data[CONF_MAC])
    try:
        device = await hass.async_add_executor_job(_connect, host, mac, entry.title)
    except (NetworkTimeoutError, OSError, BroadlinkException) as err:
        raise ConfigEntryNotReady from err

    coordinator = ElectroluxCoordinator(hass, entry, device, mac)
    await coordinator.async_config_entry_first_refresh()
    hass.data.setdefault(DOMAIN, {})[entry.entry_id] = coordinator
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unload_ok:
        hass.data.get(DOMAIN, {}).pop(entry.entry_id, None)
    return unload_ok


async def async_migrate_entry(hass: HomeAssistant, config_entry: ConfigEntry) -> bool:
    if config_entry.version == 1 and "ip" in config_entry.data:
        new = {**config_entry.data}
        new[CONF_NAME] = config_entry.title
        new[CONF_HOST] = config_entry.data["ip"]
        new[CONF_MAC] = base64.b64decode(config_entry.data["mac"]).hex()
        new[CONF_TIMEOUT] = broadlink.DEFAULT_TIMEOUT
        new[ATTR_MIN_TEMP] = DEFAULT_MIN
        new[ATTR_MAX_TEMP] = DEFAULT_MAX
        hass.config_entries.async_update_entry(
            config_entry,
            title=config_entry.title,
            data=new,
            version=2,
        )
    return True


def _connect(host: str, mac: bytes, name: str) -> electrolux:
    """Connect off the event loop. The device constructor authenticates."""
    return electrolux(
        (host, broadlink.DEFAULT_PORT),
        mac,
        DEVICE_TYPE,
        broadlink.DEFAULT_TIMEOUT,
        name,
        "",
        "Kelvinator",
        False,
    )
