"""Tests for ha_services/device_handlers module."""
from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock

import pytest
from homeassistant.core import ServiceCall

from smart_heating.ha_services.device_handlers import (
    async_handle_add_device,
    async_handle_remove_device,
)
from smart_heating.const import (
    ATTR_AREA_ID,
    ATTR_DEVICE_ID,
    ATTR_DEVICE_TYPE,
    DEVICE_TYPE_THERMOSTAT,
)


@pytest.fixture
def mock_area_manager():
    """Create mock area manager."""
    manager = MagicMock()
    manager.add_device_to_area = MagicMock()
    manager.remove_device_from_area = MagicMock()
    manager.async_save = AsyncMock()
    return manager


@pytest.fixture
def mock_coordinator():
    """Create mock coordinator."""
    coordinator = MagicMock()
    coordinator.async_request_refresh = AsyncMock()
    return coordinator


class TestDeviceHandlers:
    """Test device service handlers."""

    @pytest.mark.asyncio
    async def test_async_handle_add_device_success(
        self, mock_area_manager, mock_coordinator
    ):
        """Test adding device to area successfully."""
        call = MagicMock(spec=ServiceCall)
        call.data = {
            ATTR_AREA_ID: "living_room",
            ATTR_DEVICE_ID: "climate.thermostat",
            ATTR_DEVICE_TYPE: DEVICE_TYPE_THERMOSTAT,
        }
        
        await async_handle_add_device(call, mock_area_manager, mock_coordinator)
        
        # Verify device was added
        mock_area_manager.add_device_to_area.assert_called_once_with(
            "living_room", "climate.thermostat", DEVICE_TYPE_THERMOSTAT
        )
        # Verify data was saved
        mock_area_manager.async_save.assert_called_once()
        # Verify coordinator refresh
        mock_coordinator.async_request_refresh.assert_called_once()

    @pytest.mark.asyncio
    async def test_async_handle_add_device_error(
        self, mock_area_manager, mock_coordinator
    ):
        """Test adding device when area manager raises error."""
        call = MagicMock(spec=ServiceCall)
        call.data = {
            ATTR_AREA_ID: "unknown_area",
            ATTR_DEVICE_ID: "climate.thermostat",
            ATTR_DEVICE_TYPE: DEVICE_TYPE_THERMOSTAT,
        }
        
        # Make add_device_to_area raise ValueError
        mock_area_manager.add_device_to_area.side_effect = ValueError("Area not found")
        
        # Should not raise, just log error
        await async_handle_add_device(call, mock_area_manager, mock_coordinator)
        
        # Verify device add was attempted
        mock_area_manager.add_device_to_area.assert_called_once()
        # Should not save or refresh on error
        mock_area_manager.async_save.assert_not_called()
        mock_coordinator.async_request_refresh.assert_not_called()

    @pytest.mark.asyncio
    async def test_async_handle_remove_device_success(
        self, mock_area_manager, mock_coordinator
    ):
        """Test removing device from area successfully."""
        call = MagicMock(spec=ServiceCall)
        call.data = {
            ATTR_AREA_ID: "living_room",
            ATTR_DEVICE_ID: "climate.thermostat",
        }
        
        await async_handle_remove_device(call, mock_area_manager, mock_coordinator)
        
        # Verify device was removed
        mock_area_manager.remove_device_from_area.assert_called_once_with(
            "living_room", "climate.thermostat"
        )
        # Verify data was saved
        mock_area_manager.async_save.assert_called_once()
        # Verify coordinator refresh
        mock_coordinator.async_request_refresh.assert_called_once()

    @pytest.mark.asyncio
    async def test_async_handle_remove_device_error(
        self, mock_area_manager, mock_coordinator
    ):
        """Test removing device when area manager raises error."""
        call = MagicMock(spec=ServiceCall)
        call.data = {
            ATTR_AREA_ID: "living_room",
            ATTR_DEVICE_ID: "unknown_device",
        }
        
        # Make remove_device_from_area raise ValueError
        mock_area_manager.remove_device_from_area.side_effect = ValueError(
            "Device not found"
        )
        
        # Should not raise, just log error
        await async_handle_remove_device(call, mock_area_manager, mock_coordinator)
        
        # Verify device remove was attempted
        mock_area_manager.remove_device_from_area.assert_called_once()
        # Should not save or refresh on error
        mock_area_manager.async_save.assert_not_called()
        mock_coordinator.async_request_refresh.assert_not_called()
