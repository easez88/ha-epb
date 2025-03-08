"""The EPB integration.

This integration provides support for monitoring EPB (Electric Power Board) power usage
and cost.
"""

from __future__ import annotations

import logging
from datetime import timedelta

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import (CONF_PASSWORD, CONF_SCAN_INTERVAL,
                                 CONF_USERNAME, Platform)
from homeassistant.core import HomeAssistant
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .api import EPBApiClient
from .const import DEFAULT_SCAN_INTERVAL, DOMAIN
from .coordinator import EPBUpdateCoordinator

PLATFORMS: list[Platform] = [Platform.SENSOR]

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up EPB from a config entry."""
    session = async_get_clientsession(hass)
    client = EPBApiClient(
        entry.data[CONF_USERNAME],
        entry.data[CONF_PASSWORD],
        session,
    )

    scan_interval = entry.options.get(CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL)
    if isinstance(scan_interval, int):
        scan_interval = timedelta(minutes=scan_interval)

    coordinator = EPBUpdateCoordinator(
        hass,
        client,
        update_interval=scan_interval,
    )

    await coordinator.async_config_entry_first_refresh()

    hass.data.setdefault(DOMAIN, {})[entry.entry_id] = coordinator

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    entry.async_on_unload(entry.add_update_listener(update_listener))

    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    if unload_ok := await hass.config_entries.async_unload_platforms(entry, PLATFORMS):
        hass.data[DOMAIN].pop(entry.entry_id)

    return unload_ok


async def update_listener(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Update listener."""
    await hass.config_entries.async_reload(entry.entry_id)
