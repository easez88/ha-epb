"""API client for EPB."""
import logging
from datetime import datetime
import aiohttp
from aiohttp import ClientSession

_LOGGER = logging.getLogger(__name__)

class EPBApiClient:
    """EPB API Client."""

    def __init__(self, username: str, password: str, session: ClientSession) -> None:
        """Initialize the API client."""
        self._username = username
        self._password = password
        self._session = session
        self._token = None
        self.base_url = "https://api.epb.com"
        _LOGGER.debug("Initializing EPB API client for user: %s", username)

    async def authenticate(self) -> None:
        """Authenticate with EPB API."""
        auth_url = f"{self.base_url}/web/api/v1/login/"  # Matches Node-RED flow line 39
        _LOGGER.info("Authenticating with EPB API at %s", auth_url)
        
        # Matches Node-RED flow lines 61-66
        auth_data = {
            "username": self._username,
            "password": self._password,
            "grant_type": "PASSWORD"
        }
        
        try:
            async with self._session.post(auth_url, json=auth_data) as response:
                _LOGGER.debug("Auth response status: %s", response.status)
                text = await response.text()
                _LOGGER.debug("Auth response: %s", text)
                
                if response.status != 200:
                    raise Exception(f"Authentication failed with status {response.status}: {text}")
                
                json_response = await response.json()
                # Matches Node-RED flow line 99
                self._token = json_response.get("tokens", {}).get("access", {}).get("token")
                
                if not self._token:
                    raise Exception("No token in authentication response")
                    
                _LOGGER.info("Successfully authenticated with EPB API")
                
        except Exception as err:
            _LOGGER.error("Authentication error: %s", err, exc_info=True)
            raise

    async def _ensure_token(self) -> None:
        """Ensure we have a valid token."""
        if not self._token:
            await self.authenticate()

    async def get_account_links(self) -> list:
        """Get account links."""
        await self._ensure_token()

        # Matches Node-RED flow line 125
        url = f"{self.base_url}/web/api/v1/account-links/"
        _LOGGER.debug("Fetching account links from %s", url)
        
        # Matches Node-RED flow lines 132-139
        headers = {
            "X-User-Token": self._token
        }
        
        try:
            async with self._session.get(url, headers=headers) as response:
                _LOGGER.debug("Account links response status: %s", response.status)
                text = await response.text()
                _LOGGER.debug("Account links response: %s", text)
                
                if response.status == 400 and "TOKEN_EXPIRED" in text:
                    _LOGGER.info("Token expired, refreshing...")
                    self._token = None
                    await self._ensure_token()
                    return await self.get_account_links()
                
                if response.status != 200:
                    raise Exception(f"Failed to get account links: {text}")
                    
                return await response.json()
                
        except Exception as err:
            _LOGGER.error("Error fetching account links: %s", err, exc_info=True)
            raise

    async def get_usage_data(self, account_id: str, gis_id: str | None) -> dict:
        """Get usage data for an account."""
        await self._ensure_token()

        url = f"{self.base_url}/web/api/v1/usage/power/permanent/compare/daily"
        _LOGGER.debug("Fetching usage data from %s", url)
        
        # Get current date
        date = datetime.now()
        
        # If we're in the first few days of a month, get previous month's data
        if date.day <= 3:
            if date.month == 1:
                usage_year = date.year - 1
                usage_month = 12
            else:
                usage_year = date.year
                usage_month = date.month - 1
        else:
            usage_year = date.year
            usage_month = date.month
        
        payload = {
            "account_number": account_id,
            "gis_id": gis_id,
            "zone_id": "America/New_York",
            "usage_year": usage_year,
            "usage_month": usage_month
        }
        
        _LOGGER.debug("Usage data payload: %s", payload)
        
        headers = {
            "X-User-Token": self._token
        }
        
        try:
            async with self._session.post(url, json=payload, headers=headers) as response:
                _LOGGER.debug("Usage data response status: %s", response.status)
                text = await response.text()
                _LOGGER.debug("Usage data response: %s", text)
                
                if response.status == 400 and "TOKEN_EXPIRED" in text:
                    _LOGGER.info("Token expired, refreshing...")
                    self._token = None
                    await self._ensure_token()
                    return await self.get_usage_data(account_id, gis_id)
                
                if response.status != 200:
                    _LOGGER.error("Failed to get usage data: %s", text)
                    return {}
                
                data = await response.json()
                
                # Process data according to Node-RED flow
                if data.get("data"):
                    # Get the most recent day's data
                    latest_data = data["data"][-1]["a"]["values"]
                    return {
                        "kwh": latest_data.get("pos_kwh", 0),
                        "cost": latest_data.get("pos_wh_est_cost", 0)
                    }
                return {}
                
        except Exception as err:
            _LOGGER.error("Error fetching usage data: %s", err, exc_info=True)
            return {} 