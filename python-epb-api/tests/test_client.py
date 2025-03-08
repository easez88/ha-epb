"""Tests for the EPB API client."""

from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from aiohttp import ClientError, ClientSession
from epb_api import EPBApiClient, EPBApiError, EPBAuthError


@pytest.fixture
def client():
    """Create a test client."""
    session = AsyncMock(spec=ClientSession)
    return EPBApiClient("test_user", "test_pass", session)


@pytest.mark.asyncio
async def test_authenticate_success(client):
    """Test successful authentication."""
    mock_response = AsyncMock()
    mock_response.status = 200
    mock_response.json.return_value = {"tokens": {"access": {"token": "test_token"}}}
    mock_response.text.return_value = "success"

    client._session.post.return_value.__aenter__.return_value = mock_response

    await client.authenticate()
    assert client._token == "test_token"


@pytest.mark.asyncio
async def test_authenticate_failure(client):
    """Test authentication failure."""
    mock_response = AsyncMock()
    mock_response.status = 401
    mock_response.text.return_value = "Unauthorized"

    client._session.post.return_value.__aenter__.return_value = mock_response

    with pytest.raises(EPBAuthError):
        await client.authenticate()


@pytest.mark.asyncio
async def test_authenticate_connection_error(client):
    """Test authentication with connection error."""
    client._session.post.side_effect = ClientError()

    with pytest.raises(EPBApiError):
        await client.authenticate()


@pytest.mark.asyncio
async def test_get_account_links_success(client):
    """Test successful account links retrieval."""
    client._token = "test_token"
    mock_response = AsyncMock()
    mock_response.status = 200
    mock_response.json.return_value = [{"account": "123", "premise": "456"}]
    mock_response.text.return_value = "success"

    client._session.get.return_value.__aenter__.return_value = mock_response

    result = await client.get_account_links()
    assert result == [{"account": "123", "premise": "456"}]


@pytest.mark.asyncio
async def test_get_account_links_token_expired(client):
    """Test account links with expired token."""
    client._token = "expired_token"
    mock_response_expired = AsyncMock()
    mock_response_expired.status = 400
    mock_response_expired.text.return_value = "TOKEN_EXPIRED"

    mock_response_auth = AsyncMock()
    mock_response_auth.status = 200
    mock_response_auth.json.return_value = {
        "tokens": {"access": {"token": "new_token"}}
    }
    mock_response_auth.text.return_value = "success"

    mock_response_links = AsyncMock()
    mock_response_links.status = 200
    mock_response_links.json.return_value = [{"account": "123"}]
    mock_response_links.text.return_value = "success"

    client._session.get.return_value.__aenter__.side_effect = [
        mock_response_expired,
        mock_response_links,
    ]
    client._session.post.return_value.__aenter__.return_value = mock_response_auth

    result = await client.get_account_links()
    assert result == [{"account": "123"}]


@pytest.mark.asyncio
async def test_get_usage_data_success(client):
    """Test successful usage data retrieval."""
    client._token = "test_token"
    mock_response = AsyncMock()
    mock_response.status = 200
    mock_response.json.return_value = {
        "data": [{"a": {"values": {"pos_kwh": "100.5", "pos_wh_est_cost": "12.34"}}}]
    }
    mock_response.text.return_value = "success"

    client._session.post.return_value.__aenter__.return_value = mock_response

    result = await client.get_usage_data("123", "456")
    assert result == {"kwh": 100.5, "cost": 12.34}


@pytest.mark.asyncio
async def test_get_usage_data_monthly_format(client):
    """Test usage data retrieval with monthly format."""
    client._token = "test_token"
    mock_response = AsyncMock()
    mock_response.status = 200
    mock_response.json.return_value = {
        "interval_a_totals": {"pos_kwh": "200.5", "pos_wh_est_cost": "25.67"}
    }
    mock_response.text.return_value = "success"

    client._session.post.return_value.__aenter__.return_value = mock_response

    result = await client.get_usage_data("123", "456")
    assert result == {"kwh": 200.5, "cost": 25.67}


@pytest.mark.asyncio
async def test_get_usage_data_averages_format(client):
    """Test usage data retrieval with averages format."""
    client._token = "test_token"
    mock_response = AsyncMock()
    mock_response.status = 200
    mock_response.json.return_value = {
        "interval_a_averages": {"pos_kwh": "150.5", "pos_wh_est_cost": "18.90"}
    }
    mock_response.text.return_value = "success"

    client._session.post.return_value.__aenter__.return_value = mock_response

    result = await client.get_usage_data("123", "456")
    assert result == {"kwh": 150.5, "cost": 18.90}


@pytest.mark.asyncio
async def test_get_usage_data_no_data(client):
    """Test usage data retrieval with no valid data."""
    client._token = "test_token"
    mock_response = AsyncMock()
    mock_response.status = 200
    mock_response.json.return_value = {}
    mock_response.text.return_value = "success"

    client._session.post.return_value.__aenter__.return_value = mock_response

    result = await client.get_usage_data("123", "456")
    assert result == {"kwh": 0.0, "cost": 0.0}


@pytest.mark.asyncio
async def test_get_usage_data_error(client):
    """Test usage data retrieval with API error."""
    client._token = "test_token"
    mock_response = AsyncMock()
    mock_response.status = 500
    mock_response.text.return_value = "Internal Server Error"

    client._session.post.return_value.__aenter__.return_value = mock_response

    with pytest.raises(EPBApiError):
        await client.get_usage_data("123", "456")
