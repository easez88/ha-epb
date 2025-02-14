"""Support for EPB sensors."""
from __future__ import annotations

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorStateClass,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import UnitOfEnergy, CURRENCY_DOLLAR
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.typing import StateType
from homeassistant.helpers.update_coordinator import (
    CoordinatorEntity,
)
from homeassistant.helpers.entity import DeviceInfo

from .const import DOMAIN
from .coordinator import EPBDataUpdateCoordinator
import logging

_LOGGER = logging.getLogger(__name__)

async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up EPB sensors based on a config entry."""
    coordinator = hass.data[DOMAIN][entry.entry_id]

    # Wait for first update
    await coordinator.async_config_entry_first_refresh()

    entities = []
    for account_id, data in coordinator.data.items():
        entities.extend([
            EPBEnergySensor(coordinator, account_id),
            EPBCostSensor(coordinator, account_id),
        ])

    async_add_entities(entities)

class EPBEnergySensor(CoordinatorEntity, SensorEntity):
    """Representation of an EPB Energy sensor."""

    _attr_device_class = SensorDeviceClass.ENERGY
    _attr_native_unit_of_measurement = UnitOfEnergy.KILO_WATT_HOUR
    _attr_state_class = SensorStateClass.TOTAL_INCREASING

    def __init__(self, coordinator: EPBDataUpdateCoordinator, account_id: str) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator)
        self._account_id = account_id
        self._attr_unique_id = f"{account_id}_energy"
        
        # Get account details from the coordinator
        account_details = coordinator.get_account_details(account_id)
        service_address = account_details.get("service_address", f"Account {account_id}")
        
        self._attr_name = f"EPB Energy - {service_address}"
        self._attr_extra_state_attributes = {
            "account_number": account_id,
            "service_address": service_address,
        }

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

    @callback
    def _handle_coordinator_update(self) -> None:
        """Handle updated data from the coordinator."""
        if self.coordinator.data and self._account_id in self.coordinator.data:
            account_data = self.coordinator.data[self._account_id]
            # Update any dynamic attributes here if needed
            self._attr_extra_state_attributes.update({
                "last_updated": account_data.get("last_updated", "Unknown"),
            })
        super()._handle_coordinator_update()

class EPBCostSensor(CoordinatorEntity, SensorEntity):
    """Representation of an EPB Cost sensor."""

    _attr_device_class = SensorDeviceClass.MONETARY
    _attr_native_unit_of_measurement = CURRENCY_DOLLAR
    _attr_state_class = SensorStateClass.TOTAL

    def __init__(self, coordinator: EPBDataUpdateCoordinator, account_id: str) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator)
        self._account_id = account_id
        self._attr_unique_id = f"{account_id}_cost"
        self._attr_name = f"EPB Cost {account_id}"

    @property
    def native_value(self) -> StateType:
        """Return the state of the sensor."""
        try:
            if self.coordinator.data and self._account_id in self.coordinator.data:
                return self.coordinator.data[self._account_id]["cost"]
            _LOGGER.warning(
                "No data available for account %s. Available accounts: %s",
                self._account_id,
                list(self.coordinator.data.keys()) if self.coordinator.data else "none"
            )
            return None
        except Exception as err:
            _LOGGER.error(
                "Error getting cost value for account %s: %s",
                self._account_id,
                err
            )
            return None 