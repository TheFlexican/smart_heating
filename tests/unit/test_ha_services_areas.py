"""Tests for ha_services/area_handlers module."""
from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock

import pytest
from homeassistant.core import ServiceCall

from smart_heating.ha_services.area_handlers import (
    async_handle_set_temperature,
    async_handle_enable_area,
    async_handle_disable_area,
)
from smart_heating.const import ATTR_AREA_ID, ATTR_TEMPERATURE


@pytest.fixture
def mock_area_manager():
    """Create mock area manager."""
    manager = MagicMock()
    manager.set_area_target_temperature = MagicMock()
    manager.enable_area = MagicMock()
    manager.disable_area = MagicMock()
    manager.async_save = AsyncMock()
    return manager


@pytest.fixture
def mock_coordinator():
    """Create mock coordinator."""
    coordinator = MagicMock()
    coordinator.async_request_refresh = AsyncMock()
    return coordinator


class TestAreaHandlers:
    """Test area service handlers."""

    @pytest.mark.asyncio
    async def test_async_handle_set_temperature_success(
        self, mock_area_manager, mock_coordinator
    ):
        """Test setting area temperature successfully."""
        call = MagicMock(spec=ServiceCall)
        call.data = {
            ATTR_AREA_ID: "living_room",
            ATTR_TEMPERATURE: 21.5,
        }
        
        await async_handle_set_temperature(call, mock_area_manager, mock_coordinator)
        
        # Verify temperature was set
        mock_area_manager.set_area_target_temperature.assert_called_once_with(
            "living_room", 21.5
        )
        # Verify data was saved
        mock_area_manager.async_save.assert_called_once()
        # Verify coordinator refresh
        mock_coordinator.async_request_refresh.assert_called_once()

    @pytest.mark.asyncio
    async def test_async_handle_set_temperature_error(
        self, mock_area_manager, mock_coordinator
    ):
        """Test setting temperature when area manager raises error."""
        call = MagicMock(spec=ServiceCall)
        call.data = {
            ATTR_AREA_ID: "unknown_area",
            ATTR_TEMPERATURE: 21.5,
        }
        
        # Make set_area_target_temperature raise ValueError
        mock_area_manager.set_area_target_temperature.side_effect = ValueError(
            "Area not found"
        )
        
        # Should not raise, just log error
        await async_handle_set_temperature(call, mock_area_manager, mock_coordinator)
        
        # Verify temperature set was attempted
        mock_area_manager.set_area_target_temperature.assert_called_once()
        # Should not save or refresh on error
        mock_area_manager.async_save.assert_not_called()
        mock_coordinator.async_request_refresh.assert_not_called()

    @pytest.mark.asyncio
    async def test_async_handle_enable_area_success(
        self, mock_area_manager, mock_coordinator
    ):
        """Test enabling area successfully."""
        call = MagicMock(spec=ServiceCall)
        call.data = {ATTR_AREA_ID: "living_room"}
        
        await async_handle_enable_area(call, mock_area_manager, mock_coordinator)
        
        # Verify area was enabled
        mock_area_manager.enable_area.assert_called_once_with("living_room")
        # Verify data was saved
        mock_area_manager.async_save.assert_called_once()
        # Verify coordinator refresh
        mock_coordinator.async_request_refresh.assert_called_once()

    @pytest.mark.asyncio
    async def test_async_handle_enable_area_error(
        self, mock_area_manager, mock_coordinator
    ):
        """Test enabling area when area manager raises error."""
        call = MagicMock(spec=ServiceCall)
        call.data = {ATTR_AREA_ID: "unknown_area"}
        
        # Make enable_area raise ValueError
        mock_area_manager.enable_area.side_effect = ValueError("Area not found")
        
        # Should not raise, just log error
        await async_handle_enable_area(call, mock_area_manager, mock_coordinator)
        
        # Verify enable was attempted
        mock_area_manager.enable_area.assert_called_once()
        # Should not save or refresh on error
        mock_area_manager.async_save.assert_not_called()
        mock_coordinator.async_request_refresh.assert_not_called()

    @pytest.mark.asyncio
    async def test_async_handle_disable_area_success(
        self, mock_area_manager, mock_coordinator
    ):
        """Test disabling area successfully."""
        call = MagicMock(spec=ServiceCall)
        call.data = {ATTR_AREA_ID: "living_room"}
        
        await async_handle_disable_area(call, mock_area_manager, mock_coordinator)
        
        # Verify area was disabled
        mock_area_manager.disable_area.assert_called_once_with("living_room")
        # Verify data was saved
        mock_area_manager.async_save.assert_called_once()
        # Verify coordinator refresh
        mock_coordinator.async_request_refresh.assert_called_once()

    @pytest.mark.asyncio
    async def test_async_handle_disable_area_error(
        self, mock_area_manager, mock_coordinator
    ):
        """Test disabling area when area manager raises error."""
        call = MagicMock(spec=ServiceCall)
        call.data = {ATTR_AREA_ID: "unknown_area"}
        
        # Make disable_area raise ValueError
        mock_area_manager.disable_area.side_effect = ValueError("Area not found")
        
        # Should not raise, just log error
        await async_handle_disable_area(call, mock_area_manager, mock_coordinator)
        
        # Verify disable was attempted
        mock_area_manager.disable_area.assert_called_once()
        # Should not save or refresh on error
        mock_area_manager.async_save.assert_not_called()
        mock_coordinator.async_request_refresh.assert_not_called()
