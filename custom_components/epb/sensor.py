"""Sensor platform for EPB integration."""
from __future__ import annotations

import logging
from typing import Any

import voluptuous as vol

from homeassistant.const import UnitOfEnergy
from homeassistant.components.sensor import (
    PLATFORM_SCHEMA,
    SensorDeviceClass,
    SensorEntity,
    SensorStateClass,
)
from homeassistant.const import (
    CONF_PASSWORD,
    CONF_USERNAME,
    CURRENCY_DOLLAR,
)
import homeassistant.helpers.config_validation as cv
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .coordinator import EPBUpdateCoordinator
from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)

PLATFORM_SCHEMA = PLATFORM_SCHEMA.extend(
    {
        vol.Required(CONF_USERNAME): cv.string,
        vol.Required(CONF_PASSWORD): cv.string,
    }
)

class EPBBaseSensor(CoordinatorEntity, SensorEntity):
    """Base class for EPB sensors."""

    def __init__(
        self,
        coordinator: EPBUpdateCoordinator,
        account_id: str,
        gis_id: str | None,
    ) -> None:
        """Initialize the sensor.
        
        Args:
            coordinator: The EPB update coordinator
            account_id: The EPB account ID
            gis_id: The GIS ID for the account (optional)
        """
        super().__init__(coordinator)
        self._account_id = account_id
        self._gis_id = gis_id
        self._attr_has_entity_name = True
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, account_id)},
            name=f"EPB Account {account_id}",
            manufacturer="EPB",
            model="Power Account",
        )

    @property
    def available(self) -> bool:
        """Return if entity is available."""
        return (
            self.coordinator.last_update_success and
            self._account_id in self.coordinator.data and
            self.coordinator.data[self._account_id].get("has_usage_data", False)
        )

class EPBEnergySensor(EPBBaseSensor):
    """Sensor for EPB energy usage."""

    _attr_device_class = SensorDeviceClass.ENERGY
    _attr_state_class = SensorStateClass.TOTAL
    _attr_native_unit_of_measurement = UnitOfEnergy.KILO_WATT_HOUR
    _attr_icon = "mdi:flash"

    def __init__(
        self,
        coordinator: EPBUpdateCoordinator,
        account_id: str,
        gis_id: str | None,
    ) -> None:
        """Initialize the energy sensor."""
        super().__init__(coordinator, account_id, gis_id)
        self._attr_unique_id = f"{DOMAIN}_{account_id}_energy"

    @property
    def name(self) -> str:
        """Return the name of the sensor."""
        return "Energy Usage"

    @property
    def native_value(self) -> float | None:
        """Return the state of the sensor."""
        if self.coordinator.data is None:
            return None
        return self.coordinator.data.get(self._account_id, {}).get("kwh")

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return additional state attributes."""
        if not self.coordinator.data or self._account_id not in self.coordinator.data:
            return {}
        
        data = self.coordinator.data[self._account_id]
        return {
            "account_number": self._account_id,
            "service_address": data.get("service_address"),
            "city": data.get("city"),
            "state": data.get("state"),
            "zip_code": data.get("zip_code"),
        }

class EPBCostSensor(EPBBaseSensor):
    """Sensor for EPB energy cost."""

    _attr_device_class = SensorDeviceClass.MONETARY
    _attr_state_class = SensorStateClass.MEASUREMENT
    _attr_native_unit_of_measurement = CURRENCY_DOLLAR
    _attr_icon = "mdi:currency-usd"

    def __init__(
        self,
        coordinator: EPBUpdateCoordinator,
        account_id: str,
        gis_id: str | None,
    ) -> None:
        """Initialize the cost sensor."""
        super().__init__(coordinator, account_id, gis_id)
        self._attr_unique_id = f"{DOMAIN}_{account_id}_cost"

    @property
    def name(self) -> str:
        """Return the name of the sensor."""
        return "Energy Cost"

    @property
    def native_value(self) -> float | None:
        """Return the state of the sensor."""
        if self.coordinator.data is None:
            return None
        cost = self.coordinator.data.get(self._account_id, {}).get("cost")
        if cost is not None:
            return abs(cost)
        return None

async def async_setup_entry(hass, entry, async_add_entities):
    """Set up EPB sensors based on a config entry."""
    coordinator = hass.data[DOMAIN][entry.entry_id]

    # Wait for coordinator to do first update
    await coordinator.async_config_entry_first_refresh()

    entities = []
    seen_accounts = set()  # Track accounts we've already processed

    for account in coordinator.accounts:
        account_id = account["power_account"]["account_id"]
        
        # Skip if we've already processed this account
        if account_id in seen_accounts:
            continue
            
        seen_accounts.add(account_id)
        
        # Get the address from the premise data
        address = account["premise"].get("full_service_address", account_id)
        
        entities.extend([
            EPBEnergySensor(coordinator, account_id, address),
            EPBCostSensor(coordinator, account_id, address),
        ])

    async_add_entities(entities) 