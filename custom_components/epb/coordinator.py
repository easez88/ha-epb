"""Data update coordinator for EPB integration."""
from __future__ import annotations

import logging
from datetime import timedelta
from typing import Any

from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import (
    DataUpdateCoordinator,
    UpdateFailed,
)
from homeassistant.exceptions import ConfigEntryAuthFailed

from epb_api import EPBApiClient, EPBAuthError, EPBApiError

from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)

class EPBUpdateCoordinator(DataUpdateCoordinator[dict[str, Any]]):
    """Class to manage fetching EPB data."""

    def __init__(
        self,
        hass: HomeAssistant,
        client: EPBApiClient,
        update_interval: timedelta,
    ) -> None:
        """Initialize the coordinator."""
        super().__init__(
            hass,
            _LOGGER,
            name=DOMAIN,
            update_interval=update_interval,
        )
        self.client = client
        self.accounts = []

    async def _async_update_data(self) -> dict[str, Any]:
        """Fetch data from EPB."""
        try:
            if not self.accounts:
                self.accounts = await self.client.get_account_links()

            data = {}
            for account in self.accounts:
                account_id = account["power_account"]["account_id"]
                gis_id = account["premise"].get("gis_id")
                
                try:
                    usage_data = await self.client.get_usage_data(account_id, gis_id)
                    data[account_id] = {
                        "kwh": usage_data["kwh"],
                        "cost": usage_data["cost"],
                        "has_usage_data": True,
                        "service_address": account["premise"].get("full_service_address"),
                        "city": account["premise"].get("city"),
                        "state": account["premise"].get("state"),
                        "zip_code": account["premise"].get("zip_code"),
                    }
                except EPBApiError as err:
                    _LOGGER.error(
                        "Error fetching usage data for account %s: %s",
                        account_id,
                        err,
                    )
                    data[account_id] = {"has_usage_data": False}

            return data

        except EPBAuthError as err:
            raise ConfigEntryAuthFailed from err
        except EPBApiError as err:
            raise UpdateFailed(f"Error communicating with EPB API: {err}") from err
        except Exception as err:
            raise UpdateFailed(f"Unexpected error: {err}") from err 