"""Test the EPB API client."""

from datetime import datetime
from typing import Any, AsyncGenerator
from unittest.mock import AsyncMock, Mock, patch

import aiohttp
import pytest
from aiohttp import ClientError, ClientSession

from custom_components.epb.api import (AccountLink, EPBApiClient, EPBApiError,
                                       EPBAuthError)

pytestmark = pytest.mark.asyncio


@pytest.fixture
async def mock_session() -> AsyncMock:
    """Create a mock aiohttp session."""
    session = AsyncMock(spec=ClientSession)
    return session


async def test_authentication_success(mock_session: AsyncMock) -> None:
    """Test successful authentication."""
    mock_response = AsyncMock()
    mock_response.status = 200
    mock_response.text.return_value = '{"tokens": {"access": {"token": "test-token"}}}'
    mock_response.json.return_value = {"tokens": {"access": {"token": "test-token"}}}

    mock_session.post.return_value.__aenter__.return_value = mock_response

    client = EPBApiClient("test@example.com", "password", mock_session)
    await client.authenticate()

    assert client._token == "test-token"
    mock_session.post.assert_called_once()


async def test_authentication_failure(mock_session: AsyncMock) -> None:
    """Test failed authentication."""
    mock_response = AsyncMock()
    mock_response.status = 401
    mock_response.text.return_value = "Invalid credentials"

    mock_session.post.return_value.__aenter__.return_value = mock_response

    client = EPBApiClient("test@example.com", "password", mock_session)

    with pytest.raises(EPBAuthError):
        await client.authenticate()


async def test_get_account_links_success(mock_session: AsyncMock) -> None:
    """Test successful account links retrieval."""
    mock_response = AsyncMock()
    mock_response.status = 200
    mock_response.json.return_value = [
        {"power_account": {"account_id": "123", "gis_id": None}}
    ]

    mock_session.get.return_value.__aenter__.return_value = mock_response

    client = EPBApiClient("test@example.com", "password", mock_session)
    client._token = "test-token"

    result = await client.get_account_links()

    assert result == [{"power_account": {"account_id": "123", "gis_id": None}}]
    mock_session.get.assert_called_once()


async def test_get_usage_data_success(mock_session: AsyncMock) -> None:
    """Test successful usage data retrieval."""
    mock_response = AsyncMock()
    mock_response.status = 200
    mock_response.json.return_value = {
        "data": [{"a": {"values": {"pos_kwh": "100", "pos_wh_est_cost": "12.34"}}}]
    }

    mock_session.post.return_value.__aenter__.return_value = mock_response

    client = EPBApiClient("test@example.com", "password", mock_session)
    client._token = "test-token"

    result = await client.get_usage_data("123", "456")

    assert result == {"kwh": 100.0, "cost": 12.34}
    mock_session.post.assert_called_once()


async def test_token_refresh_on_expired(mock_session: AsyncMock) -> None:
    """Test token refresh when expired."""
    # First call returns token expired
    expired_response = AsyncMock()
    expired_response.status = 400
    expired_response.text.return_value = '{"error": "TOKEN_EXPIRED"}'

    # Second call (after refresh) returns success
    success_response = AsyncMock()
    success_response.status = 200
    success_response.json.return_value = [
        {"power_account": {"account_id": "123", "gis_id": None}}
    ]

    # Auth response for token refresh
    auth_response = AsyncMock()
    auth_response.status = 200
    auth_response.text.return_value = '{"tokens": {"access": {"token": "new-token"}}}'
    auth_response.json.return_value = {"tokens": {"access": {"token": "new-token"}}}

    mock_session.get.return_value.__aenter__.side_effect = [
        expired_response,
        success_response,
    ]
    mock_session.post.return_value.__aenter__.return_value = auth_response

    client = EPBApiClient("test@example.com", "password", mock_session)
    client._token = "expired-token"

    result = await client.get_account_links()

    assert result == [{"power_account": {"account_id": "123", "gis_id": None}}]
    assert client._token == "new-token"
    assert mock_session.get.call_count == 2
    assert mock_session.post.call_count == 1
