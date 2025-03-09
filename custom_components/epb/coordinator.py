"""Data update coordinator for EPB integration."""

from __future__ import annotations

import logging
from datetime import timedelta
from typing import Any, Dict

from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import (DataUpdateCoordinator,
                                                      UpdateFailed)

from .api import AccountLink, EPBApiClient, EPBApiError, EPBAuthError

_LOGGER = logging.getLogger(__name__)


class EPBUpdateCoordinator(DataUpdateCoordinator[Dict[str, Any]]):
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
            name="EPB",
            update_interval=update_interval,
        )
        self.client = client
        self.account_links: list[AccountLink] = []

    async def _async_update_data(self) -> Dict[str, Any]:
        """Fetch data from EPB."""
        try:
            if not self.account_links:
                self.account_links = await self.client.get_account_links()

            data: Dict[str, Any] = {}
            for account in self.account_links:
                account_id = account["power_account"]["account_id"]
                gis_id = account["power_account"].get("gis_id")

                if account_id:
                    usage_data = await self.client.get_usage_data(account_id, gis_id)
                    data[account_id] = usage_data

            return data

        except EPBAuthError as err:
            raise UpdateFailed(f"Authentication failed: {err}") from err
        except EPBApiError as err:
            raise UpdateFailed(f"Error communicating with API: {err}") from err
