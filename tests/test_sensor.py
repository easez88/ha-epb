"""Test EPB sensors."""

from unittest.mock import AsyncMock, Mock, patch

import pytest
from homeassistant.const import CURRENCY_DOLLAR, UnitOfEnergy
from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.epb.const import DOMAIN
from custom_components.epb.sensor import EPBCostSensor, EPBEnergySensor

pytestmark = pytest.mark.asyncio


@pytest.fixture
def mock_coordinator():
    """Create a mock coordinator."""
    coordinator = Mock(spec=DataUpdateCoordinator)
    coordinator.data = {
        "123": {
            "kwh": 100.0,
            "cost": 12.34,
            "service_address": "123 Test St",
            "city": "Test City",
            "state": "TS",
            "zip_code": "12345",
            "has_usage_data": True,
        }
    }
    coordinator.last_update_success = True
    return coordinator


def test_energy_sensor(mock_coordinator):
    """Test the energy sensor."""
    sensor = EPBEnergySensor(mock_coordinator, "123", "123 Test St")

    assert sensor.unique_id == "epb_energy_123"
    assert sensor.name == "EPB Energy - 123 Test St"
    assert sensor.native_value == 100.0
    assert sensor.native_unit_of_measurement == UnitOfEnergy.KILO_WATT_HOUR
    assert sensor.available is True

    attributes = sensor.extra_state_attributes
    assert attributes["account_number"] == "123"
    assert attributes["service_address"] == "123 Test St"
    assert attributes["city"] == "Test City"
    assert attributes["state"] == "TS"
    assert attributes["zip_code"] == "12345"


def test_cost_sensor(mock_coordinator):
    """Test the cost sensor."""
    sensor = EPBCostSensor(mock_coordinator, "123", "123 Test St")

    assert sensor.unique_id == "epb_cost_123"
    assert sensor.name == "EPB Cost - 123 Test St"
    assert sensor.native_value == 12.34
    assert sensor.native_unit_of_measurement == CURRENCY_DOLLAR
    assert sensor.available is True


def test_sensor_unavailable(mock_coordinator):
    """Test sensors when data is unavailable."""
    # Simulate no data
    mock_coordinator.data = {}
    mock_coordinator.last_update_success = True

    energy_sensor = EPBEnergySensor(mock_coordinator, "123", "123 Test St")
    cost_sensor = EPBCostSensor(mock_coordinator, "123", "123 Test St")

    assert energy_sensor.available is False
    assert cost_sensor.available is False
    assert energy_sensor.native_value is None
    assert cost_sensor.native_value is None


async def test_sensor_setup(hass: HomeAssistant):
    """Test sensor setup."""
    entry = MockConfigEntry(
        domain=DOMAIN,
        data={
            "username": "test@example.com",
            "password": "test-password",
        },
    )

    mock_coordinator = Mock(spec=DataUpdateCoordinator)
    mock_coordinator.data = {
        "123": {
            "kwh": 100.0,
            "cost": 12.34,
            "service_address": "123 Test St",
            "has_usage_data": True,
        }
    }
    mock_coordinator.last_update_success = True
    mock_coordinator.accounts = [
        {
            "power_account": {"account_id": "123"},
            "premise": {"full_service_address": "123 Test St"},
        }
    ]
    mock_coordinator.async_config_entry_first_refresh = AsyncMock()

    with patch(
        "custom_components.epb.sensor.EPBUpdateCoordinator",
        return_value=mock_coordinator,
    ):
        entry.add_to_hass(hass)
        await hass.config_entries.async_setup(entry.entry_id)
        await hass.async_block_till_done()

    state = hass.states.get("sensor.epb_energy_123_test_st")
    assert state
    assert state.state == "100.0"

    state = hass.states.get("sensor.epb_cost_123_test_st")
    assert state
    assert state.state == "12.34"
