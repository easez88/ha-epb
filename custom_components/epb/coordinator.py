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

    async def _async_update_data(self):
        """Update data via library."""
        try:
            # First, get all accounts
            if not self.accounts:
                self.accounts = await self.api.get_account_links()
                _LOGGER.debug("Found accounts: %s", [
                    account["power_account"]["account_id"] 
                    for account in self.accounts
                ])
                if not self.accounts:
                    raise UpdateFailed("No accounts found")

            # Then get usage data for each account
            data = {}
            for account in self.accounts:
                account_id = account["power_account"]["account_id"]
                gis_id = account["premise"]["gis_id"]
                
                _LOGGER.debug("Fetching usage data for account %s", account_id)
                usage = await self.api.get_usage_data(account_id, gis_id)
                
                if usage and "data" in usage:
                    today_index = datetime.now().day - 1
                    try:
                        data[account_id] = {
                            "kwh": usage["data"][today_index]["a"]["values"]["pos_kwh"],
                            "cost": usage["data"][today_index]["a"]["values"]["pos_wh_est_cost"],
                            "account_number": account_id
                        }
                        _LOGGER.debug(
                            "Got usage data for account %s: %s",
                            account_id,
                            data[account_id]
                        )
                    except (KeyError, IndexError) as err:
                        _LOGGER.error(
                            "Error parsing usage data for account %s: %s. Data: %s",
                            account_id,
                            err,
                            usage
                        )
                else:
                    _LOGGER.warning(
                        "No usage data returned for account %s",
                        account_id
                    )

            if not data:
                raise UpdateFailed("No usage data found for any account")

            return data

        except Exception as err:
            _LOGGER.error("Error communicating with API: %s", err)
            raise UpdateFailed(f"Error communicating with API: {err}") 