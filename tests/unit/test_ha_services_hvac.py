"""Tests for ha_services/hvac_handlers module."""
from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock

import pytest
from homeassistant.core import ServiceCall

from smart_heating.ha_services.hvac_handlers import (
    async_handle_set_preset_mode,
    async_handle_set_boost_mode,
    async_handle_cancel_boost,
    async_handle_set_hvac_mode,
)
from smart_heating.const import (
    ATTR_AREA_ID,
    ATTR_PRESET_MODE,
    ATTR_BOOST_DURATION,
    ATTR_BOOST_TEMP,
    ATTR_HVAC_MODE,
)


@pytest.fixture
def mock_area():
    """Create mock area."""
    area = MagicMock()
    area.set_preset_mode = MagicMock()
    area.set_boost_mode = MagicMock()
    area.cancel_boost_mode = MagicMock()
    area.hvac_mode = "heat"
    area.boost_temp = 22.0
    return area


@pytest.fixture
def mock_area_manager(mock_area):
    """Create mock area manager."""
    manager = MagicMock()
    manager.get_area = MagicMock(return_value=mock_area)
    manager.async_save = AsyncMock()
    return manager


@pytest.fixture
def mock_coordinator():
    """Create mock coordinator."""
    coordinator = MagicMock()
    coordinator.async_request_refresh = AsyncMock()
    return coordinator


class TestHvacHandlers:
    """Test HVAC service handlers."""

    @pytest.mark.asyncio
    async def test_async_handle_set_preset_mode_success(
        self, mock_area_manager, mock_coordinator
    ):
        """Test setting preset mode successfully."""
        call = MagicMock(spec=ServiceCall)
        call.data = {
            ATTR_AREA_ID: "living_room",
            ATTR_PRESET_MODE: "eco",
        }
        
        await async_handle_set_preset_mode(call, mock_area_manager, mock_coordinator)
        
        # Verify preset mode was set
        mock_area_manager.get_area.assert_called_once_with("living_room")
        area = mock_area_manager.get_area.return_value
        area.set_preset_mode.assert_called_once_with("eco")
        # Verify data was saved
        mock_area_manager.async_save.assert_called_once()
        # Verify coordinator refresh
        mock_coordinator.async_request_refresh.assert_called_once()

    @pytest.mark.asyncio
    async def test_async_handle_set_preset_mode_area_not_found(
        self, mock_area_manager, mock_coordinator
    ):
        """Test setting preset mode when area not found."""
        call = MagicMock(spec=ServiceCall)
        call.data = {
            ATTR_AREA_ID: "unknown_area",
            ATTR_PRESET_MODE: "eco",
        }
        
        # Make get_area return None
        mock_area_manager.get_area.return_value = None
        
        # Should not raise, just log error
        await async_handle_set_preset_mode(call, mock_area_manager, mock_coordinator)
        
        # Verify get_area was called
        mock_area_manager.get_area.assert_called_once_with("unknown_area")
        # Should not save or refresh on error
        mock_area_manager.async_save.assert_not_called()
        mock_coordinator.async_request_refresh.assert_not_called()

    @pytest.mark.asyncio
    async def test_async_handle_set_preset_mode_error(
        self, mock_area_manager, mock_coordinator
    ):
        """Test setting preset mode when set_preset_mode raises error."""
        call = MagicMock(spec=ServiceCall)
        call.data = {
            ATTR_AREA_ID: "living_room",
            ATTR_PRESET_MODE: "invalid",
        }
        
        # Make set_preset_mode raise ValueError
        area = mock_area_manager.get_area.return_value
        area.set_preset_mode.side_effect = ValueError("Invalid preset mode")
        
        # Should not raise, just log error
        await async_handle_set_preset_mode(call, mock_area_manager, mock_coordinator)
        
        # Verify set_preset_mode was attempted
        area.set_preset_mode.assert_called_once()
        # Should not save or refresh on error
        mock_area_manager.async_save.assert_not_called()
        mock_coordinator.async_request_refresh.assert_not_called()

    @pytest.mark.asyncio
    async def test_async_handle_set_boost_mode_success(
        self, mock_area_manager, mock_coordinator
    ):
        """Test setting boost mode successfully."""
        call = MagicMock(spec=ServiceCall)
        call.data = {
            ATTR_AREA_ID: "living_room",
            ATTR_BOOST_DURATION: 30,
            ATTR_BOOST_TEMP: 23.0,
        }
        
        await async_handle_set_boost_mode(call, mock_area_manager, mock_coordinator)
        
        # Verify boost mode was set
        area = mock_area_manager.get_area.return_value
        area.set_boost_mode.assert_called_once_with(30, 23.0)
        # Verify data was saved
        mock_area_manager.async_save.assert_called_once()
        # Verify coordinator refresh
        mock_coordinator.async_request_refresh.assert_called_once()

    @pytest.mark.asyncio
    async def test_async_handle_set_boost_mode_default_duration(
        self, mock_area_manager, mock_coordinator
    ):
        """Test setting boost mode with default duration."""
        call = MagicMock(spec=ServiceCall)
        call.data = {ATTR_AREA_ID: "living_room"}
        
        await async_handle_set_boost_mode(call, mock_area_manager, mock_coordinator)
        
        # Verify boost mode was set with default duration of 60 minutes
        area = mock_area_manager.get_area.return_value
        area.set_boost_mode.assert_called_once_with(60, None)

    @pytest.mark.asyncio
    async def test_async_handle_set_boost_mode_area_not_found(
        self, mock_area_manager, mock_coordinator
    ):
        """Test setting boost mode when area not found."""
        call = MagicMock(spec=ServiceCall)
        call.data = {ATTR_AREA_ID: "unknown_area"}
        
        # Make get_area return None
        mock_area_manager.get_area.return_value = None
        
        # Should not raise, just log error
        await async_handle_set_boost_mode(call, mock_area_manager, mock_coordinator)
        
        # Should not save or refresh on error
        mock_area_manager.async_save.assert_not_called()
        mock_coordinator.async_request_refresh.assert_not_called()

    @pytest.mark.asyncio
    async def test_async_handle_set_boost_mode_error(
        self, mock_area_manager, mock_coordinator
    ):
        """Test setting boost mode when set_boost_mode raises error."""
        call = MagicMock(spec=ServiceCall)
        call.data = {ATTR_AREA_ID: "living_room"}
        
        # Make set_boost_mode raise ValueError
        area = mock_area_manager.get_area.return_value
        area.set_boost_mode.side_effect = ValueError("Invalid boost settings")
        
        # Should not raise, just log error
        await async_handle_set_boost_mode(call, mock_area_manager, mock_coordinator)
        
        # Should not save or refresh on error
        mock_area_manager.async_save.assert_not_called()
        mock_coordinator.async_request_refresh.assert_not_called()

    @pytest.mark.asyncio
    async def test_async_handle_cancel_boost_success(
        self, mock_area_manager, mock_coordinator
    ):
        """Test cancelling boost mode successfully."""
        call = MagicMock(spec=ServiceCall)
        call.data = {ATTR_AREA_ID: "living_room"}
        
        await async_handle_cancel_boost(call, mock_area_manager, mock_coordinator)
        
        # Verify boost mode was cancelled
        area = mock_area_manager.get_area.return_value
        area.cancel_boost_mode.assert_called_once()
        # Verify data was saved
        mock_area_manager.async_save.assert_called_once()
        # Verify coordinator refresh
        mock_coordinator.async_request_refresh.assert_called_once()

    @pytest.mark.asyncio
    async def test_async_handle_cancel_boost_area_not_found(
        self, mock_area_manager, mock_coordinator
    ):
        """Test cancelling boost mode when area not found."""
        call = MagicMock(spec=ServiceCall)
        call.data = {ATTR_AREA_ID: "unknown_area"}
        
        # Make get_area return None
        mock_area_manager.get_area.return_value = None
        
        # Should not raise, just log error
        await async_handle_cancel_boost(call, mock_area_manager, mock_coordinator)
        
        # Should not save or refresh on error
        mock_area_manager.async_save.assert_not_called()
        mock_coordinator.async_request_refresh.assert_not_called()

    @pytest.mark.asyncio
    async def test_async_handle_cancel_boost_error(
        self, mock_area_manager, mock_coordinator
    ):
        """Test cancelling boost mode when cancel_boost_mode raises error."""
        call = MagicMock(spec=ServiceCall)
        call.data = {ATTR_AREA_ID: "living_room"}
        
        # Make cancel_boost_mode raise ValueError
        area = mock_area_manager.get_area.return_value
        area.cancel_boost_mode.side_effect = ValueError("No boost mode active")
        
        # Should not raise, just log error
        await async_handle_cancel_boost(call, mock_area_manager, mock_coordinator)
        
        # Should not save or refresh on error
        mock_area_manager.async_save.assert_not_called()
        mock_coordinator.async_request_refresh.assert_not_called()

    @pytest.mark.asyncio
    async def test_async_handle_set_hvac_mode_success(
        self, mock_area_manager, mock_coordinator
    ):
        """Test setting HVAC mode successfully."""
        call = MagicMock(spec=ServiceCall)
        call.data = {
            ATTR_AREA_ID: "living_room",
            ATTR_HVAC_MODE: "off",
        }
        
        await async_handle_set_hvac_mode(call, mock_area_manager, mock_coordinator)
        
        # Verify HVAC mode was set
        area = mock_area_manager.get_area.return_value
        assert area.hvac_mode == "off"
        # Verify data was saved
        mock_area_manager.async_save.assert_called_once()
        # Verify coordinator refresh
        mock_coordinator.async_request_refresh.assert_called_once()

    @pytest.mark.asyncio
    async def test_async_handle_set_hvac_mode_area_not_found(
        self, mock_area_manager, mock_coordinator
    ):
        """Test setting HVAC mode when area not found."""
        call = MagicMock(spec=ServiceCall)
        call.data = {
            ATTR_AREA_ID: "unknown_area",
            ATTR_HVAC_MODE: "off",
        }
        
        # Make get_area return None
        mock_area_manager.get_area.return_value = None
        
        # Should not raise, just log error
        await async_handle_set_hvac_mode(call, mock_area_manager, mock_coordinator)
        
        # Should not save or refresh on error
        mock_area_manager.async_save.assert_not_called()
        mock_coordinator.async_request_refresh.assert_not_called()
