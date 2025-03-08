"""Config flow for EPB integration."""

from __future__ import annotations

import logging
from datetime import timedelta
from typing import Any

import voluptuous as vol
from epb_api import EPBApiClient, EPBApiError, EPBAuthError
from homeassistant import config_entries
from homeassistant.const import (CONF_PASSWORD, CONF_SCAN_INTERVAL,
                                 CONF_USERNAME)
from homeassistant.core import HomeAssistant, callback
from homeassistant.data_entry_flow import FlowResult
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers import selector
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .const import DEFAULT_SCAN_INTERVAL, DOMAIN

_LOGGER = logging.getLogger(__name__)

STEP_USER_DATA_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_USERNAME): str,
        vol.Required(CONF_PASSWORD): str,
        vol.Optional(
            CONF_SCAN_INTERVAL,
            default=DEFAULT_SCAN_INTERVAL.total_seconds() // 60,
        ): selector.NumberSelector(
            selector.NumberSelectorConfig(
                min=1,
                max=60,
                step=1,
                unit_of_measurement="minutes",
                mode=selector.NumberSelectorMode.SLIDER,
            ),
        ),
    }
)


async def validate_input(hass: HomeAssistant, data: dict[str, Any]) -> dict[str, Any]:
    """Validate the user input allows us to connect."""
    session = async_get_clientsession(hass)
    client = EPBApiClient(
        username=data[CONF_USERNAME], password=data[CONF_PASSWORD], session=session
    )

    try:
        await client.authenticate()
    except EPBAuthError:
        _LOGGER.error("Failed to authenticate: %s", EPBAuthError)
        raise InvalidAuth from EPBAuthError
    except EPBApiError:
        _LOGGER.error("Failed to connect to EPB: %s", EPBApiError)
        raise InvalidAuth from EPBApiError
    except Exception as err:
        _LOGGER.error("Unexpected exception: %s", err)
        raise InvalidAuth from err

    # Convert scan_interval from minutes to timedelta
    if CONF_SCAN_INTERVAL in data:
        data[CONF_SCAN_INTERVAL] = timedelta(minutes=data[CONF_SCAN_INTERVAL])

    # Return info to be stored in the config entry
    return {"title": f"EPB ({data[CONF_USERNAME]})"}


class EPBConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for EPB."""

    VERSION = 1

    @staticmethod
    @callback
    def async_get_options_flow(config_entry):
        """Get the options flow for this handler."""
        return EPBOptionsFlow(config_entry)

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle the initial step."""
        errors = {}

        if user_input is not None:
            session = async_get_clientsession(self.hass)
            client = EPBApiClient(
                user_input[CONF_USERNAME],
                user_input[CONF_PASSWORD],
                session,
            )

            try:
                await client.authenticate()
            except EPBAuthError:
                errors["base"] = "invalid_auth"
            except EPBApiError:
                errors["base"] = "cannot_connect"
            except Exception:  # pylint: disable=broad-except
                _LOGGER.exception("Unexpected exception")
                errors["base"] = "unknown"
            else:
                await self.async_set_unique_id(user_input[CONF_USERNAME])
                self._abort_if_unique_id_configured()
                return self.async_create_entry(
                    title=user_input[CONF_USERNAME],
                    data=user_input,
                )

        return self.async_show_form(
            step_id="user",
            data_schema=STEP_USER_DATA_SCHEMA,
            errors=errors,
        )


class EPBOptionsFlow(config_entries.OptionsFlow):
    """Handle options."""

    def __init__(self, config_entry: config_entries.ConfigEntry) -> None:
        """Initialize options flow."""
        self.config_entry = config_entry

    async def async_step_init(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Manage the options."""
        if user_input is not None:
            # Convert minutes to timedelta
            if CONF_SCAN_INTERVAL in user_input:
                user_input[CONF_SCAN_INTERVAL] = timedelta(
                    minutes=user_input[CONF_SCAN_INTERVAL]
                )
            return self.async_create_entry(title="", data=user_input)

        # Convert timedelta to minutes for the form
        current_interval = self.config_entry.options.get(
            CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL
        )
        interval_minutes = current_interval.total_seconds() / 60

        options_schema = vol.Schema(
            {
                vol.Optional(
                    CONF_SCAN_INTERVAL, default=int(interval_minutes)
                ): selector.NumberSelector(
                    selector.NumberSelectorConfig(
                        min=1,
                        max=60,
                        step=1,
                        unit_of_measurement="minutes",
                        mode=selector.NumberSelectorMode.SLIDER,
                    ),
                ),
            }
        )

        return self.async_show_form(
            step_id="init",
            data_schema=options_schema,
        )


class InvalidAuth(HomeAssistantError):
    """Error to indicate there is invalid auth."""
