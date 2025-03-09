"""Support for EPB sensors."""

from __future__ import annotations

import logging
from datetime import timedelta
from typing import Any, cast

from homeassistant.components.sensor import (SensorDeviceClass, SensorEntity,
                                             SensorStateClass)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import (CONF_PASSWORD, CONF_SCAN_INTERVAL,
                                 CONF_USERNAME, UnitOfEnergy, UnitOfPower)
from homeassistant.core import HomeAssistant
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.typing import StateType
from homeassistant.helpers.update_coordinator import (CoordinatorEntity,
                                                      DataUpdateCoordinator)

from .api import AccountLink, EPBApiClient, EPBApiError
from .const import DEFAULT_SCAN_INTERVAL, DOMAIN

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the EPB sensor."""
    username = config_entry.data[CONF_USERNAME]
    password = config_entry.data[CONF_PASSWORD]
    scan_interval = config_entry.options.get(CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL)

    session = async_get_clientsession(hass)
    client = EPBApiClient(username, password, session)

    coordinator = EPBDataUpdateCoordinator(
        hass,
        client=client,
        name=DOMAIN,
        update_interval=scan_interval,
    )

    await coordinator.async_config_entry_first_refresh()

    entities = []
    for account_link in coordinator.data:
        account_id = account_link["power_account"]["account_id"]
        gis_id = account_link["power_account"].get("gis_id")
        entities.extend(
            [
                EPBEnergySensor(coordinator, account_id, gis_id),
                EPBCostSensor(coordinator, account_id, gis_id),
            ]
        )

    async_add_entities(entities)


class EPBDataUpdateCoordinator(DataUpdateCoordinator[list[AccountLink]]):
    """Class to manage fetching EPB data."""

    def __init__(
        self,
        hass: HomeAssistant,
        client: EPBApiClient,
        name: str,
        update_interval: timedelta,
    ) -> None:
        """Initialize the coordinator."""
        super().__init__(
            hass,
            _LOGGER,
            name=name,
            update_interval=update_interval,
        )
        self.client = client
        self.account_links: list[AccountLink] = []

    async def _async_update_data(self) -> list[AccountLink]:
        """Fetch data from EPB."""
        try:
            self.account_links = await self.client.get_account_links()
            return self.account_links
        except EPBApiError as err:
            _LOGGER.error("Error communicating with EPB API: %s", err)
            return []


class EPBSensorBase(CoordinatorEntity[EPBDataUpdateCoordinator], SensorEntity):
    """Base class for EPB sensors."""

    def __init__(
        self,
        coordinator: EPBDataUpdateCoordinator,
        account_id: str,
        gis_id: str | None,
    ) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator)
        self.account_id = account_id
        self.gis_id = gis_id
        self._attr_has_entity_name = True

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return the state attributes."""
        return {
            "account_id": self.account_id,
            "gis_id": self.gis_id,
        }

    async def async_update(self) -> None:
        """Update the entity."""
        await self.coordinator.async_request_refresh()


class EPBEnergySensor(EPBSensorBase):
    """Sensor for EPB energy usage."""

    _attr_device_class = SensorDeviceClass.ENERGY
    _attr_state_class = SensorStateClass.TOTAL
    _attr_native_unit_of_measurement = UnitOfEnergy.KILO_WATT_HOUR

    def __init__(
        self,
        coordinator: EPBDataUpdateCoordinator,
        account_id: str,
        gis_id: str | None,
    ) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator, account_id, gis_id)
        self._attr_unique_id = f"{account_id}_energy"
        self._attr_name = "Energy Usage"

    @property
    def native_value(self) -> float | None:
        """Return the state of the sensor."""
        try:
            usage_data = self.coordinator.client.get_usage_data(
                self.account_id, self.gis_id
            )
            return float(usage_data["kwh"])
        except (EPBApiError, KeyError, ValueError):
            return None


class EPBCostSensor(EPBSensorBase):
    """Sensor for EPB energy cost."""

    _attr_device_class = SensorDeviceClass.MONETARY
    _attr_state_class = SensorStateClass.TOTAL
    _attr_native_unit_of_measurement = "USD"

    def __init__(
        self,
        coordinator: EPBDataUpdateCoordinator,
        account_id: str,
        gis_id: str | None,
    ) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator, account_id, gis_id)
        self._attr_unique_id = f"{account_id}_cost"
        self._attr_name = "Energy Cost"

    @property
    def native_value(self) -> float | None:
        """Return the state of the sensor."""
        try:
            usage_data = self.coordinator.client.get_usage_data(
                self.account_id, self.gis_id
            )
            return float(usage_data["cost"])
        except (EPBApiError, KeyError, ValueError):
            return None

    async def async_update(self) -> None:
        """Update the entity."""
        await self.coordinator.async_request_refresh()
