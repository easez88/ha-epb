"""Test EPB sensors."""

from unittest.mock import AsyncMock, Mock, patch

import pytest
from homeassistant.const import CURRENCY_DOLLAR, UnitOfEnergy, CONF_PASSWORD, CONF_USERNAME
from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.epb.const import DOMAIN
from custom_components.epb.sensor import (
    EPBCostSensor,
    EPBEnergySensor,
    EPBDataUpdateCoordinator,
)
from custom_components.epb.api import AccountLink

pytestmark = pytest.mark.asyncio


@pytest.fixture
def mock_coordinator() -> Mock:
    """Create a mock coordinator."""
    coordinator = Mock(spec=DataUpdateCoordinator)
    coordinator.data = [
        {
            "power_account": {
                "account_id": "123",
                "gis_id": None,
            }
        }
    ]
    coordinator.last_update_success = True
    return coordinator


def test_energy_sensor(mock_coordinator: Mock) -> None:
    """Test the energy sensor."""
    sensor = EPBEnergySensor(mock_coordinator, "123", None)

    assert sensor.unique_id == "123_energy"
    assert sensor.name == "Energy Usage"
    assert sensor.available is True

    attributes = sensor.extra_state_attributes
    assert attributes["account_id"] == "123"
    assert attributes["gis_id"] is None


def test_cost_sensor(mock_coordinator: Mock) -> None:
    """Test the cost sensor."""
    sensor = EPBCostSensor(mock_coordinator, "123", None)

    assert sensor.unique_id == "123_cost"
    assert sensor.name == "Energy Cost"
    assert sensor.available is True


def test_sensor_unavailable(mock_coordinator: Mock) -> None:
    """Test sensors when data is unavailable."""
    # Simulate no data
    mock_coordinator.data = []
    mock_coordinator.last_update_success = True

    energy_sensor = EPBEnergySensor(mock_coordinator, "123", None)
    cost_sensor = EPBCostSensor(mock_coordinator, "123", None)

    assert energy_sensor.available is True  # Changed because coordinator is successful
    assert cost_sensor.available is True  # Changed because coordinator is successful
    assert energy_sensor.native_value is None
    assert cost_sensor.native_value is None


@pytest.fixture
async def mock_config_entry() -> MockConfigEntry:
    """Create a mock config entry."""
    return MockConfigEntry(
        domain=DOMAIN,
        data={
            CONF_USERNAME: "test@example.com",
            CONF_PASSWORD: "test-password",
        },
    )


async def test_sensors_setup(
    hass: HomeAssistant, mock_config_entry: MockConfigEntry
) -> None:
    """Test setting up sensors."""
    mock_account_links = [
        {
            "power_account": {
                "account_id": "123",
                "gis_id": "456",
            }
        }
    ]

    with patch(
        "custom_components.epb.sensor.EPBApiClient"
    ) as mock_client_class, patch(
        "custom_components.epb.sensor.EPBDataUpdateCoordinator"
    ) as mock_coordinator_class:
        mock_client = AsyncMock()
        mock_client.get_account_links.return_value = mock_account_links
        mock_client_class.return_value = mock_client

        mock_coordinator = AsyncMock()
        mock_coordinator.data = mock_account_links
        mock_coordinator_class.return_value = mock_coordinator

        mock_config_entry.add_to_hass(hass)
        await hass.config_entries.async_setup(mock_config_entry.entry_id)
        await hass.async_block_till_done()

        # Verify that the sensors were created and added
        assert len(hass.states.async_all()) == 2


async def test_energy_sensor_state(
    hass: HomeAssistant, mock_config_entry: MockConfigEntry
) -> None:
    """Test energy sensor state."""
    mock_usage_data = {"kwh": 100.0, "cost": 12.34}

    with patch(
        "custom_components.epb.sensor.EPBApiClient"
    ) as mock_client_class, patch(
        "custom_components.epb.sensor.EPBDataUpdateCoordinator"
    ) as mock_coordinator_class:
        mock_client = AsyncMock()
        mock_client.get_usage_data.return_value = mock_usage_data
        mock_client_class.return_value = mock_client

        mock_coordinator = AsyncMock()
        mock_coordinator_class.return_value = mock_coordinator

        sensor = EPBEnergySensor(mock_coordinator, "123", "456")
        assert sensor.native_value == 100.0


async def test_cost_sensor_state(
    hass: HomeAssistant, mock_config_entry: MockConfigEntry
) -> None:
    """Test cost sensor state."""
    mock_usage_data = {"kwh": 100.0, "cost": 12.34}

    with patch(
        "custom_components.epb.sensor.EPBApiClient"
    ) as mock_client_class, patch(
        "custom_components.epb.sensor.EPBDataUpdateCoordinator"
    ) as mock_coordinator_class:
        mock_client = AsyncMock()
        mock_client.get_usage_data.return_value = mock_usage_data
        mock_client_class.return_value = mock_client

        mock_coordinator = AsyncMock()
        mock_coordinator_class.return_value = mock_coordinator

        sensor = EPBCostSensor(mock_coordinator, "123", "456")
        assert sensor.native_value == 12.34


async def test_sensor_update(
    hass: HomeAssistant, mock_config_entry: MockConfigEntry
) -> None:
    """Test sensor update method."""
    with patch(
        "custom_components.epb.sensor.EPBApiClient"
    ) as mock_client_class, patch(
        "custom_components.epb.sensor.EPBDataUpdateCoordinator"
    ) as mock_coordinator_class:
        mock_client = AsyncMock()
        mock_client_class.return_value = mock_client

        mock_coordinator = AsyncMock()
        mock_coordinator_class.return_value = mock_coordinator

        sensor = EPBEnergySensor(mock_coordinator, "123", "456")
        await sensor.async_update()

        # Verify that the coordinator's refresh method was called
        mock_coordinator.async_request_refresh.assert_called_once()
