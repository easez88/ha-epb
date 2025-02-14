"""DataUpdateCoordinator for EPB."""
from datetime import datetime
import logging

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .api import EPBApiClient
from .const import DOMAIN, SCAN_INTERVAL

_LOGGER = logging.getLogger(__name__)

class EPBDataUpdateCoordinator(DataUpdateCoordinator):
    """Class to manage fetching EPB data."""

    def __init__(self, hass: HomeAssistant, entry: ConfigEntry) -> None:
        """Initialize the coordinator."""
        super().__init__(
            hass,
            _LOGGER,
            name=DOMAIN,
            update_interval=SCAN_INTERVAL,
        )
        self.api = EPBApiClient(
            entry.data["username"],
            entry.data["password"],
            async_get_clientsession(hass),
        )
        self.accounts = []
        self._account_details = {}

    async def _async_update_data(self) -> dict:
        """Fetch data from API."""
        try:
            if not self.accounts:
                self.accounts = await self.api.get_account_links()
                # Store account details for later use
                for account in self.accounts:
                    account_id = account["power_account"]["account_id"]
                    self._account_details[account_id] = {
                        "service_address": account["premise"].get("address", "Unknown Address"),
                        "gis_id": account["power_account"].get("gis_id"),
                    }

            data = {}
            for account in self.accounts:
                account_id = account["power_account"]["account_id"]
                gis_id = account["power_account"].get("gis_id")
                
                usage_data = await self.api.get_usage_data(account_id, gis_id)
                
                if usage_data and "daily_usage" in usage_data:
                    # Get the most recent day's usage
                    latest_usage = usage_data["daily_usage"][-1] if usage_data["daily_usage"] else {}
                    
                    data[account_id] = {
                        "kwh": float(latest_usage.get("kwh", 0)),
                        "service_address": self._account_details[account_id]["service_address"],
                        "gis_id": gis_id,
                    }
                else:
                    _LOGGER.warning("No usage data available for account %s", account_id)
                    data[account_id] = {
                        "kwh": 0,
                        "service_address": self._account_details[account_id]["service_address"],
                        "gis_id": gis_id,
                    }

            return data

        except Exception as err:
            _LOGGER.error("Error updating EPB data: %s", err)
            raise UpdateFailed(f"Error communicating with API: {err}")

    def get_account_details(self, account_id: str) -> dict:
        """Get stored account details."""
        return self._account_details.get(account_id, {}) 