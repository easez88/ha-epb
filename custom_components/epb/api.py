"""EPB API Client."""
from datetime import datetime
import logging
from typing import Any

import aiohttp
import async_timeout

from .const import LOGIN_URL, ACCOUNT_LINKS_URL, USAGE_URL

_LOGGER = logging.getLogger(__name__)

class EPBApiClient:
    """EPB API Client."""

    def __init__(self, username: str, password: str, session: aiohttp.ClientSession) -> None:
        """Initialize the API client."""
        self._username = username
        self._password = password
        self._session = session
        self._token = None

    async def authenticate(self) -> bool:
        """Authenticate with EPB."""
        try:
            async with async_timeout.timeout(10):
                response = await self._session.post(
                    LOGIN_URL,
                    json={
                        "username": self._username,
                        "password": self._password,
                        "grant_type": "PASSWORD"
                    }
                )
                data = await response.json()
                
                if response.status == 200:
                    self._token = data["tokens"]["access"]["token"]
                    return True
                return False
        except Exception as err:
            _LOGGER.error("Error authenticating with EPB: %s", err)
            return False

    async def get_account_links(self) -> list[dict[str, Any]]:
        """Get account links."""
        if not self._token:
            if not await self.authenticate():
                return []

        try:
            async with async_timeout.timeout(10):
                response = await self._session.get(
                    ACCOUNT_LINKS_URL,
                    headers={"X-User-Token": self._token}
                )
                if response.status == 200:
                    return await response.json()
                return []
        except Exception as err:
            _LOGGER.error("Error getting account links: %s", err)
            return []

    async def get_usage_data(self, account_number: str, gis_id: str) -> dict[str, Any]:
        """Get usage data for an account."""
        if not self._token:
            if not await self.authenticate():
                return {}

        try:
            now = datetime.now()
            payload = {
                "account_number": account_number,
                "gis_id": gis_id,
                "zone_id": "America/New_York",
                "usage_year": now.year,
                "usage_month": now.month
            }

            async with async_timeout.timeout(10):
                response = await self._session.post(
                    USAGE_URL,
                    headers={"X-User-Token": self._token},
                    json=payload
                )
                if response.status == 200:
                    return await response.json()
                return {}
        except Exception as err:
            _LOGGER.error("Error getting usage data: %s", err)
            return {} 