"""API client for EPB."""
from __future__ import annotations

import logging
from datetime import datetime
from typing import Any, Dict, List, Optional

from aiohttp import ClientSession, ClientError

_LOGGER = logging.getLogger(__name__)

class EPBApiError(Exception):
    """Base exception for EPB API errors."""

class EPBAuthError(EPBApiError):
    """Authentication error from EPB API."""

class EPBApiClient:
    """API Client for EPB (Electric Power Board).
    
    This client handles authentication and data fetching from the EPB API.
    It manages token refresh and provides methods to get account and usage data.
    """

    def __init__(self, username: str, password: str, session: ClientSession) -> None:
        """Initialize the EPB API client.
        
        Args:
            username: The EPB account username
            password: The EPB account password
            session: The aiohttp client session to use for requests
        """
        self._username = username
        self._password = password
        self._session = session
        self._token: Optional[str] = None
        self.base_url = "https://api.epb.com"
        _LOGGER.debug("Initializing EPB API client for user: %s", username)

    async def authenticate(self) -> None:
        """Authenticate with EPB API.
        
        Raises:
            EPBAuthError: If authentication fails
            EPBApiError: If there is an API error
        """
        auth_url = f"{self.base_url}/web/api/v1/login/"
        _LOGGER.info("Authenticating with EPB API at %s", auth_url)
        
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
                    raise EPBAuthError(f"Authentication failed with status {response.status}: {text}")
                
                json_response = await response.json()
                self._token = json_response.get("tokens", {}).get("access", {}).get("token")
                
                if not self._token:
                    raise EPBAuthError("No token in authentication response")
                    
                _LOGGER.info("Successfully authenticated with EPB API")
                
        except ClientError as err:
            raise EPBApiError(f"Connection error during authentication: {err}") from err
        except Exception as err:
            raise EPBApiError(f"Unexpected error during authentication: {err}") from err

    async def _ensure_token(self) -> None:
        """Ensure we have a valid token.
        
        Authenticates if no token is present.
        """
        if not self._token:
            await self.authenticate()

    async def get_account_links(self) -> List[Dict[str, Any]]:
        """Get account links from the EPB API.
        
        Returns:
            A list of account link dictionaries containing account and premise information
            
        Raises:
            EPBAuthError: If authentication fails
            EPBApiError: If there is an API error
        """
        await self._ensure_token()

        url = f"{self.base_url}/web/api/v1/account-links/"
        _LOGGER.debug("Fetching account links from %s", url)
        
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
                    raise EPBApiError(f"Failed to get account links: {text}")
                    
                return await response.json()
                
        except ClientError as err:
            raise EPBApiError(f"Connection error fetching account links: {err}") from err
        except Exception as err:
            raise EPBApiError(f"Error fetching account links: {err}") from err

    def _extract_usage_data(self, data: Dict[str, Any]) -> Dict[str, float]:
        """Extract usage data from API response.
        
        Args:
            data: The raw API response data
            
        Returns:
            A dictionary containing kwh and cost values
        """
        try:
            # Constants for rate calculation
            ENERGY_CHARGE_RATE = 0.095  # Base energy charge per kWh
            TVA_FUEL_COST_ADJUSTMENT = 0.029  # Current TVA fuel cost adjustment
            CUSTOMER_CHARGE = 9.81  # Fixed monthly customer charge
            
            # First try to get data from daily format
            if "data" in data and data["data"]:
                # Find the last entry that has actual data
                daily_data = data["data"]
                latest_data = None
                
                for entry in reversed(daily_data):
                    if "a" in entry and "values" in entry["a"]:
                        latest_data = entry["a"]["values"]
                        break
                
                if latest_data:
                    kwh = float(latest_data.get("pos_kwh", 0))
                    # Calculate cost using EPB's rate structure
                    total_rate = ENERGY_CHARGE_RATE + TVA_FUEL_COST_ADJUSTMENT
                    cost = (kwh * total_rate) + CUSTOMER_CHARGE
                    return {
                        "kwh": kwh,
                        "cost": cost
                    }
                    
            # If that fails or no daily data found, try the monthly format
            if "interval_a_totals" in data:
                totals = data["interval_a_totals"]
                kwh = float(totals.get("pos_kwh", 0))
                # Calculate cost using EPB's rate structure
                total_rate = ENERGY_CHARGE_RATE + TVA_FUEL_COST_ADJUSTMENT
                cost = (kwh * total_rate) + CUSTOMER_CHARGE
                return {
                    "kwh": kwh,
                    "cost": cost
                }
                
            # If both attempts fail, try interval_a_averages
            if "interval_a_averages" in data:
                averages = data["interval_a_averages"]
                kwh = float(averages.get("pos_kwh", 0))
                # Calculate cost using EPB's rate structure
                total_rate = ENERGY_CHARGE_RATE + TVA_FUEL_COST_ADJUSTMENT
                cost = (kwh * total_rate) + CUSTOMER_CHARGE
                return {
                    "kwh": kwh,
                    "cost": cost
                }
                
            _LOGGER.warning("No valid data format found in response: %s", data)
            return {"kwh": 0.0, "cost": 0.0}
            
        except (KeyError, IndexError, TypeError, ValueError) as err:
            _LOGGER.error("Error parsing usage data: %s. Data: %s", err, data)
            return {"kwh": 0.0, "cost": 0.0}

    async def get_usage_data(self, account_id: str, gis_id: Optional[str]) -> Dict[str, float]:
        """Get usage data for an account.
        
        Args:
            account_id: The EPB account ID
            gis_id: The optional GIS ID for the account
            
        Returns:
            A dictionary containing kwh and cost values
            
        Raises:
            EPBAuthError: If authentication fails
            EPBApiError: If there is an API error
        """
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
                    raise EPBApiError(f"Failed to get usage data: {text}")
                
                data = await response.json()
                return self._extract_usage_data(data)
                
        except ClientError as err:
            raise EPBApiError(f"Connection error fetching usage data: {err}") from err
        except Exception as err:
            _LOGGER.error(
                "Error getting usage data for account %s: %s",
                account_id,
                err,
            )
            return {"kwh": 0.0, "cost": 0.0} 