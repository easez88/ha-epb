"""DataUpdateCoordinator for EPB integration."""
import logging
from datetime import timedelta

from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator
from homeassistant.exceptions import ConfigEntryAuthFailed
from homeassistant.const import CONF_SCAN_INTERVAL
import async_timeout

from .api import EPBApiClient
from .const import DOMAIN, DEFAULT_SCAN_INTERVAL

_LOGGER = logging.getLogger(__name__)

class EPBUpdateCoordinator(DataUpdateCoordinator):
    """Class to manage fetching EPB data."""

    def __init__(
        self, 
        hass: HomeAssistant, 
        client: EPBApiClient,
        scan_interval: timedelta | None = None,
    ) -> None:
        """Initialize the coordinator."""
        self.client = client
        self.accounts = []

        # Use user-configured scan interval or default
        update_interval = scan_interval or DEFAULT_SCAN_INTERVAL

        super().__init__(
            hass,
            _LOGGER,
            name=DOMAIN,
            update_interval=update_interval,
            # Set always_update to False since we can compare data
            always_update=False,
        )

    async def _async_update_data(self):
        """Fetch data from API endpoint.

        This is the place to pre-process the data to lookup tables
        so entities can quickly look up their data.
        """
        try:
            # If we don't have account links yet, fetch them
            if not self.accounts:
                async with async_timeout.timeout(30):
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

                async with async_timeout.timeout(10):
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
                    "has_usage_data": bool(usage_data),  # True if we got any data
                    "city": premise.get("city"),
                    "state": premise.get("state"),
                    "zip_code": premise.get("zip_code")
                }

                _LOGGER.debug("Final processed data: %s", data)

            return data

        except Exception as err:
            if "TOKEN_EXPIRED" in str(err):
                # Force token refresh on next attempt
                self.client._token = None
                raise ConfigEntryAuthFailed("Token expired") from err
            raise 