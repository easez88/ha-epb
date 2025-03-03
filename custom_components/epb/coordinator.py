"""DataUpdateCoordinator for EPB integration."""
import logging
from datetime import timedelta

from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator
from homeassistant.exceptions import ConfigEntryAuthFailed

from .api import EPBApiClient
from .const import DOMAIN, DEFAULT_SCAN_INTERVAL

_LOGGER = logging.getLogger(__name__)

class EPBUpdateCoordinator(DataUpdateCoordinator):
    """Class to manage fetching EPB data."""

    def __init__(
        self, hass: HomeAssistant, client: EPBApiClient, scan_interval: timedelta
    ) -> None:
        """Initialize."""
        super().__init__(
            hass,
            _LOGGER,
            name=DOMAIN,
            update_interval=scan_interval,
        )
        self.client = client
        self.accounts = []

    async def _async_update_data(self):
        """Update data via library."""
        try:
            # Get account links first if we don't have them
            if not self.accounts:
                self.accounts = await self.client.get_account_links()
                _LOGGER.debug("Initial accounts data: %s", self.accounts)

            # Process each account
            data = {}
            for account in self.accounts:
                power_account = account.get("power_account", {})
                account_id = power_account.get("account_id")
                premise = account.get("premise", {})
                
                if not account_id:
                    continue

                _LOGGER.debug(
                    "Fetching usage data for account %s with GIS ID %s",
                    account_id,
                    premise.get("gis_id")
                )

                usage_data = await self.client.get_usage_data(
                    account_id,
                    premise.get("gis_id")
                )
                _LOGGER.debug("Raw usage data for account %s: %s", account_id, usage_data)

                # Process the usage data
                data[account_id] = {
                    "kwh": float(usage_data.get("kwh", 0)),
                    "cost": float(usage_data.get("cost", 0)),
                    "service_address": premise.get("full_service_address", "Unknown Address"),
                    "gis_id": premise.get("gis_id"),
                    "last_updated": None,  # Will be set by HA
                    "has_usage_data": bool(usage_data),  # True if we got any data
                    "city": premise.get("city"),
                    "state": premise.get("state"),
                    "zip_code": premise.get("zip_code")
                }

                _LOGGER.debug("Final processed data: %s", data)

            return data

        except Exception as err:
            _LOGGER.error("Error updating EPB data: %s", err)
            raise 