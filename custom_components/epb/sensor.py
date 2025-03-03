"""Sensor platform for EPB integration."""
from __future__ import annotations

import logging
from typing import Any

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorStateClass,
)
from homeassistant.const import UnitOfEnergy, CURRENCY_DOLLAR
from homeassistant.core import callback
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .coordinator import EPBUpdateCoordinator
from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)

class EPBBaseSensor(CoordinatorEntity, SensorEntity):
    """Base class for EPB sensors."""

    def __init__(
        self, 
        coordinator: EPBUpdateCoordinator,
        account_id: str,
        address: str,
    ) -> None:
        """Initialize the base sensor."""
        super().__init__(coordinator)
        self._account_id = account_id
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, account_id)},
            name=f"EPB - {address}",
            manufacturer="Electric Power Board",
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
    """Representation of an EPB Energy sensor."""

    _attr_device_class = SensorDeviceClass.ENERGY
    _attr_native_unit_of_measurement = UnitOfEnergy.KILO_WATT_HOUR
    _attr_state_class = SensorStateClass.TOTAL_INCREASING

    def __init__(
        self,
        coordinator: EPBUpdateCoordinator,
        account_id: str,
        address: str,
    ) -> None:
        """Initialize the energy sensor."""
        super().__init__(coordinator, account_id, address)
        self._attr_unique_id = f"epb_energy_{account_id}"
        self._attr_name = f"EPB Energy - {address}"

    @property
    def native_value(self) -> float | None:
        """Return the state of the sensor."""
        try:
            return self.coordinator.data[self._account_id]["kwh"]
        except (KeyError, TypeError):
            _LOGGER.warning(
                "Unable to get data for account %s. Coordinator data: %s",
                self._account_id,
                self.coordinator.data
            )
            return None
        return float(self.coordinator.data[self._account_id]["kwh"])

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
    """Representation of an EPB Cost sensor."""

    _attr_device_class = SensorDeviceClass.MONETARY
    _attr_native_unit_of_measurement = CURRENCY_DOLLAR
    _attr_state_class = SensorStateClass.TOTAL

    def __init__(
        self,
        coordinator: EPBUpdateCoordinator,
        account_id: str,
        address: str,
    ) -> None:
        """Initialize the cost sensor."""
        super().__init__(coordinator, account_id, address)
        self._attr_unique_id = f"epb_cost_{account_id}"
        self._attr_name = f"EPB Cost - {address}"

    @property
    def native_value(self) -> float | None:
        """Return the cost value."""
        if not self.available:
            return None
        return float(self.coordinator.data[self._account_id]["cost"])

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