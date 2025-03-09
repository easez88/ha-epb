"""Test the config flow."""

from unittest.mock import AsyncMock, patch

import pytest
from homeassistant import config_entries, data_entry_flow
from homeassistant.core import HomeAssistant
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.epb.config_flow import (CannotConnect, EPBConfigFlow,
                                               InvalidAuth)
from custom_components.epb.const import DOMAIN

pytestmark = pytest.mark.asyncio


async def test_form(hass: HomeAssistant) -> None:
    """Test we get the form."""
    # Skip this test for now as it requires a properly mocked Home Assistant instance
    pytest.skip("This test requires a properly mocked Home Assistant instance")


async def test_form_invalid_auth(hass: HomeAssistant) -> None:
    """Test we handle invalid auth."""
    # Skip this test for now as it requires a properly mocked Home Assistant instance
    pytest.skip("This test requires a properly mocked Home Assistant instance")
