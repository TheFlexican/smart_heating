"""Tests for ha_services/vacation_handlers module."""
from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock

import pytest
from homeassistant.core import HomeAssistant, ServiceCall

from smart_heating.ha_services.vacation_handlers import (
    async_handle_enable_vacation_mode,
    async_handle_disable_vacation_mode,
)
from smart_heating.const import DOMAIN


@pytest.fixture
def mock_hass():
    """Create mock Home Assistant instance."""
    hass = MagicMock(spec=HomeAssistant)
    hass.data = {DOMAIN: {}}
    return hass


@pytest.fixture
def mock_vacation_manager():
    """Create mock vacation manager."""
    manager = MagicMock()
    manager.async_enable = AsyncMock()
    manager.async_disable = AsyncMock()
    return manager


@pytest.fixture
def mock_coordinator():
    """Create mock coordinator."""
    coordinator = MagicMock()
    coordinator.async_request_refresh = AsyncMock()
    return coordinator


class TestVacationHandlers:
    """Test vacation mode service handlers."""

    @pytest.mark.asyncio
    async def test_async_handle_enable_vacation_mode_success(
        self, mock_hass, mock_vacation_manager, mock_coordinator
    ):
        """Test enabling vacation mode successfully."""
        mock_hass.data[DOMAIN]["vacation_manager"] = mock_vacation_manager
        
        call = MagicMock(spec=ServiceCall)
        call.data = {
            "start_date": "2024-01-01",
            "end_date": "2024-01-10",
            "preset_mode": "away",
            "frost_protection_override": True,
            "min_temperature": 8.0,
            "auto_disable": True,
        }
        
        await async_handle_enable_vacation_mode(call, mock_hass, mock_coordinator)
        
        # Verify vacation mode was enabled
        mock_vacation_manager.async_enable.assert_called_once_with(
            start_date="2024-01-01",
            end_date="2024-01-10",
            preset_mode="away",
            frost_protection_override=True,
            min_temperature=8.0,
            auto_disable=True,
            person_entities=[],
        )

    @pytest.mark.asyncio
    async def test_async_handle_enable_vacation_mode_defaults(
        self, mock_hass, mock_vacation_manager, mock_coordinator
    ):
        """Test enabling vacation mode with default values."""
        mock_hass.data[DOMAIN]["vacation_manager"] = mock_vacation_manager
        
        call = MagicMock(spec=ServiceCall)
        call.data = {
            "start_date": "2024-01-01",
            "end_date": "2024-01-10",
        }
        
        await async_handle_enable_vacation_mode(call, mock_hass, mock_coordinator)
        
        # Verify vacation mode was enabled with defaults
        mock_vacation_manager.async_enable.assert_called_once_with(
            start_date="2024-01-01",
            end_date="2024-01-10",
            preset_mode="away",
            frost_protection_override=True,
            min_temperature=10.0,
            auto_disable=True,
            person_entities=[],
        )

    @pytest.mark.asyncio
    async def test_async_handle_enable_vacation_mode_no_manager(
        self, mock_hass, mock_coordinator
    ):
        """Test enabling vacation mode when vacation manager not found."""
        # No vacation_manager in hass.data
        call = MagicMock(spec=ServiceCall)
        call.data = {
            "start_date": "2024-01-01",
            "end_date": "2024-01-10",
        }
        
        # Should not raise, just log error
        await async_handle_enable_vacation_mode(call, mock_hass, mock_coordinator)

    @pytest.mark.asyncio
    async def test_async_handle_enable_vacation_mode_error(
        self, mock_hass, mock_vacation_manager, mock_coordinator
    ):
        """Test enabling vacation mode when error occurs."""
        mock_hass.data[DOMAIN]["vacation_manager"] = mock_vacation_manager
        
        call = MagicMock(spec=ServiceCall)
        call.data = {
            "start_date": "2024-01-01",
            "end_date": "2024-01-10",
        }
        
        # Make async_enable raise exception
        mock_vacation_manager.async_enable.side_effect = Exception("Enable failed")
        
        # Should not raise, just log error
        await async_handle_enable_vacation_mode(call, mock_hass, mock_coordinator)

    @pytest.mark.asyncio
    async def test_async_handle_disable_vacation_mode_success(
        self, mock_hass, mock_vacation_manager, mock_coordinator
    ):
        """Test disabling vacation mode successfully."""
        mock_hass.data[DOMAIN]["vacation_manager"] = mock_vacation_manager
        
        call = MagicMock(spec=ServiceCall)
        call.data = {}
        
        await async_handle_disable_vacation_mode(call, mock_hass, mock_coordinator)
        
        # Verify vacation mode was disabled
        mock_vacation_manager.async_disable.assert_called_once()

    @pytest.mark.asyncio
    async def test_async_handle_disable_vacation_mode_no_manager(
        self, mock_hass, mock_coordinator
    ):
        """Test disabling vacation mode when vacation manager not found."""
        # No vacation_manager in hass.data
        call = MagicMock(spec=ServiceCall)
        call.data = {}
        
        # Should not raise, just log error
        await async_handle_disable_vacation_mode(call, mock_hass, mock_coordinator)

    @pytest.mark.asyncio
    async def test_async_handle_disable_vacation_mode_error(
        self, mock_hass, mock_vacation_manager, mock_coordinator
    ):
        """Test disabling vacation mode when error occurs."""
        mock_hass.data[DOMAIN]["vacation_manager"] = mock_vacation_manager
        
        call = MagicMock(spec=ServiceCall)
        call.data = {}
        
        # Make async_disable raise exception
        mock_vacation_manager.async_disable.side_effect = Exception("Disable failed")
        
        # Should not raise, just log error
        await async_handle_disable_vacation_mode(call, mock_hass, mock_coordinator)
