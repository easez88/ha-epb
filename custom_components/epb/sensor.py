"""Support for EPB sensors."""
from __future__ import annotations

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorStateClass,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import UnitOfEnergy, CURRENCY_DOLLAR
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.typing import StateType
from homeassistant.helpers.update_coordinator import (
    CoordinatorEntity,
)

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
        self._attr_name = f"EPB Energy {account_id}"

    @property
    def native_value(self) -> StateType:
        """Return the state of the sensor."""
        try:
            if self.coordinator.data and self._account_id in self.coordinator.data:
                return self.coordinator.data[self._account_id]["kwh"]
            _LOGGER.warning(
                "No data available for account %s. Available accounts: %s",
                self._account_id,
                list(self.coordinator.data.keys()) if self.coordinator.data else "none"
            )
            return None
        except Exception as err:
            _LOGGER.error(
                "Error getting energy value for account %s: %s",
                self._account_id,
                err
            )
            return None

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