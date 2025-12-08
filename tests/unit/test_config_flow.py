"""Tests for Config Flow."""
from __future__ import annotations

from unittest.mock import AsyncMock, patch

import pytest
from homeassistant import config_entries
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType

from smart_heating.config_flow import SmartHeatingConfigFlow, SmartHeatingOptionsFlowHandler
from smart_heating.const import DOMAIN


class TestConfigFlow:
    """Test the config flow."""

    async def test_form(self, hass: HomeAssistant):
        """Test we get the form."""
        flow = SmartHeatingConfigFlow()
        flow.hass = hass
        
        result = await flow.async_step_user(user_input=None)
        
        assert result["type"] == FlowResultType.FORM

    async def test_user_flow_success(self, hass: HomeAssistant):
        """Test successful user flow."""
        flow = SmartHeatingConfigFlow()
        flow.hass = hass
        
        result = await flow.async_step_user(user_input={})
        
        assert result["type"] == FlowResultType.CREATE_ENTRY
        assert result["title"] == "Smart Heating"

    async def test_options_flow(
        self, hass: HomeAssistant, mock_config_entry
    ):
        """Test options flow."""
        mock_config_entry.add_to_hass(hass)
        
        # Create options flow with proper initialization
        flow = SmartHeatingOptionsFlowHandler()
        flow.hass = hass
        # Set the handler property which contains entry_id
        flow.handler = mock_config_entry.entry_id
        
        result = await flow.async_step_init(user_input=None)

        assert result["type"] == FlowResultType.FORM
        assert result["step_id"] == "init"

    async def test_options_flow_update(
        self, hass: HomeAssistant, mock_config_entry
    ):
        """Test updating options."""
        mock_config_entry.add_to_hass(hass)
        
        flow = SmartHeatingOptionsFlowHandler()
        flow.hass = hass
        flow.handler = mock_config_entry.entry_id
        
        # First show the form
        result = await flow.async_step_init(user_input=None)
        
        # Then submit with data
        result = await flow.async_step_init(
            user_input={"opentherm_gateway_id": "", "opentherm_enabled": True}
        )

        assert result["type"] == FlowResultType.CREATE_ENTRY


class TestImportFlow:
    """Test the import flow."""

    async def test_import_flow(self, hass: HomeAssistant):
        """Test import flow."""
        flow = SmartHeatingConfigFlow()
        flow.hass = hass
        
        # Config flow doesn't have import step, use user step
        result = await flow.async_step_user(user_input={})

        assert result["type"] == FlowResultType.CREATE_ENTRY
