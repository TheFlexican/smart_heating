"""Tests for ha_services/sensor_handlers module."""
from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock

import pytest
from homeassistant.core import ServiceCall

from smart_heating.ha_services.sensor_handlers import (
    async_handle_add_window_sensor,
    async_handle_remove_window_sensor,
    async_handle_add_presence_sensor,
    async_handle_remove_presence_sensor,
)
from smart_heating.const import ATTR_AREA_ID


@pytest.fixture
def mock_area():
    """Create mock area."""
    area = MagicMock()
    area.add_window_sensor = MagicMock()
    area.remove_window_sensor = MagicMock()
    area.add_presence_sensor = MagicMock()
    area.remove_presence_sensor = MagicMock()
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


class TestSensorHandlers:
    """Test sensor service handlers."""

    @pytest.mark.asyncio
    async def test_async_handle_add_window_sensor_success(
        self, mock_area_manager, mock_coordinator
    ):
        """Test adding window sensor successfully."""
        call = MagicMock(spec=ServiceCall)
        call.data = {
            ATTR_AREA_ID: "living_room",
            "entity_id": "binary_sensor.window_living_room",
        }
        
        await async_handle_add_window_sensor(call, mock_area_manager, mock_coordinator)
        
        # Verify sensor was added
        area = mock_area_manager.get_area.return_value
        area.add_window_sensor.assert_called_once_with("binary_sensor.window_living_room")
        # Verify data was saved
        mock_area_manager.async_save.assert_called_once()
        # Verify coordinator refresh
        mock_coordinator.async_request_refresh.assert_called_once()

    @pytest.mark.asyncio
    async def test_async_handle_add_window_sensor_area_not_found(
        self, mock_area_manager, mock_coordinator
    ):
        """Test adding window sensor when area not found."""
        call = MagicMock(spec=ServiceCall)
        call.data = {
            ATTR_AREA_ID: "unknown_area",
            "entity_id": "binary_sensor.window",
        }
        
        # Make get_area return None
        mock_area_manager.get_area.return_value = None
        
        # Should not raise, just log error
        await async_handle_add_window_sensor(call, mock_area_manager, mock_coordinator)
        
        # Should not save or refresh on error
        mock_area_manager.async_save.assert_not_called()
        mock_coordinator.async_request_refresh.assert_not_called()

    @pytest.mark.asyncio
    async def test_async_handle_add_window_sensor_error(
        self, mock_area_manager, mock_coordinator
    ):
        """Test adding window sensor when add_window_sensor raises error."""
        call = MagicMock(spec=ServiceCall)
        call.data = {
            ATTR_AREA_ID: "living_room",
            "entity_id": "binary_sensor.window",
        }
        
        # Make add_window_sensor raise ValueError
        area = mock_area_manager.get_area.return_value
        area.add_window_sensor.side_effect = ValueError("Sensor already exists")
        
        # Should not raise, just log error
        await async_handle_add_window_sensor(call, mock_area_manager, mock_coordinator)
        
        # Should not save or refresh on error
        mock_area_manager.async_save.assert_not_called()
        mock_coordinator.async_request_refresh.assert_not_called()

    @pytest.mark.asyncio
    async def test_async_handle_remove_window_sensor_success(
        self, mock_area_manager, mock_coordinator
    ):
        """Test removing window sensor successfully."""
        call = MagicMock(spec=ServiceCall)
        call.data = {
            ATTR_AREA_ID: "living_room",
            "entity_id": "binary_sensor.window_living_room",
        }
        
        await async_handle_remove_window_sensor(call, mock_area_manager, mock_coordinator)
        
        # Verify sensor was removed
        area = mock_area_manager.get_area.return_value
        area.remove_window_sensor.assert_called_once_with("binary_sensor.window_living_room")
        # Verify data was saved
        mock_area_manager.async_save.assert_called_once()
        # Verify coordinator refresh
        mock_coordinator.async_request_refresh.assert_called_once()

    @pytest.mark.asyncio
    async def test_async_handle_remove_window_sensor_area_not_found(
        self, mock_area_manager, mock_coordinator
    ):
        """Test removing window sensor when area not found."""
        call = MagicMock(spec=ServiceCall)
        call.data = {
            ATTR_AREA_ID: "unknown_area",
            "entity_id": "binary_sensor.window",
        }
        
        # Make get_area return None
        mock_area_manager.get_area.return_value = None
        
        # Should not raise, just log error
        await async_handle_remove_window_sensor(call, mock_area_manager, mock_coordinator)
        
        # Should not save or refresh on error
        mock_area_manager.async_save.assert_not_called()
        mock_coordinator.async_request_refresh.assert_not_called()

    @pytest.mark.asyncio
    async def test_async_handle_remove_window_sensor_error(
        self, mock_area_manager, mock_coordinator
    ):
        """Test removing window sensor when remove_window_sensor raises error."""
        call = MagicMock(spec=ServiceCall)
        call.data = {
            ATTR_AREA_ID: "living_room",
            "entity_id": "binary_sensor.window",
        }
        
        # Make remove_window_sensor raise ValueError
        area = mock_area_manager.get_area.return_value
        area.remove_window_sensor.side_effect = ValueError("Sensor not found")
        
        # Should not raise, just log error
        await async_handle_remove_window_sensor(call, mock_area_manager, mock_coordinator)
        
        # Should not save or refresh on error
        mock_area_manager.async_save.assert_not_called()
        mock_coordinator.async_request_refresh.assert_not_called()

    @pytest.mark.asyncio
    async def test_async_handle_add_presence_sensor_success(
        self, mock_area_manager, mock_coordinator
    ):
        """Test adding presence sensor successfully."""
        call = MagicMock(spec=ServiceCall)
        call.data = {
            ATTR_AREA_ID: "living_room",
            "entity_id": "binary_sensor.motion_living_room",
        }
        
        await async_handle_add_presence_sensor(call, mock_area_manager, mock_coordinator)
        
        # Verify sensor was added
        area = mock_area_manager.get_area.return_value
        area.add_presence_sensor.assert_called_once_with("binary_sensor.motion_living_room")
        # Verify data was saved
        mock_area_manager.async_save.assert_called_once()
        # Verify coordinator refresh
        mock_coordinator.async_request_refresh.assert_called_once()

    @pytest.mark.asyncio
    async def test_async_handle_add_presence_sensor_area_not_found(
        self, mock_area_manager, mock_coordinator
    ):
        """Test adding presence sensor when area not found."""
        call = MagicMock(spec=ServiceCall)
        call.data = {
            ATTR_AREA_ID: "unknown_area",
            "entity_id": "binary_sensor.motion",
        }
        
        # Make get_area return None
        mock_area_manager.get_area.return_value = None
        
        # Should not raise, just log error
        await async_handle_add_presence_sensor(call, mock_area_manager, mock_coordinator)
        
        # Should not save or refresh on error
        mock_area_manager.async_save.assert_not_called()
        mock_coordinator.async_request_refresh.assert_not_called()

    @pytest.mark.asyncio
    async def test_async_handle_add_presence_sensor_error(
        self, mock_area_manager, mock_coordinator
    ):
        """Test adding presence sensor when add_presence_sensor raises error."""
        call = MagicMock(spec=ServiceCall)
        call.data = {
            ATTR_AREA_ID: "living_room",
            "entity_id": "binary_sensor.motion",
        }
        
        # Make add_presence_sensor raise ValueError
        area = mock_area_manager.get_area.return_value
        area.add_presence_sensor.side_effect = ValueError("Sensor already exists")
        
        # Should not raise, just log error
        await async_handle_add_presence_sensor(call, mock_area_manager, mock_coordinator)
        
        # Should not save or refresh on error
        mock_area_manager.async_save.assert_not_called()
        mock_coordinator.async_request_refresh.assert_not_called()

    @pytest.mark.asyncio
    async def test_async_handle_remove_presence_sensor_success(
        self, mock_area_manager, mock_coordinator
    ):
        """Test removing presence sensor successfully."""
        call = MagicMock(spec=ServiceCall)
        call.data = {
            ATTR_AREA_ID: "living_room",
            "entity_id": "binary_sensor.motion_living_room",
        }
        
        await async_handle_remove_presence_sensor(call, mock_area_manager, mock_coordinator)
        
        # Verify sensor was removed
        area = mock_area_manager.get_area.return_value
        area.remove_presence_sensor.assert_called_once_with("binary_sensor.motion_living_room")
        # Verify data was saved
        mock_area_manager.async_save.assert_called_once()
        # Verify coordinator refresh
        mock_coordinator.async_request_refresh.assert_called_once()

    @pytest.mark.asyncio
    async def test_async_handle_remove_presence_sensor_area_not_found(
        self, mock_area_manager, mock_coordinator
    ):
        """Test removing presence sensor when area not found."""
        call = MagicMock(spec=ServiceCall)
        call.data = {
            ATTR_AREA_ID: "unknown_area",
            "entity_id": "binary_sensor.motion",
        }
        
        # Make get_area return None
        mock_area_manager.get_area.return_value = None
        
        # Should not raise, just log error
        await async_handle_remove_presence_sensor(call, mock_area_manager, mock_coordinator)
        
        # Should not save or refresh on error
        mock_area_manager.async_save.assert_not_called()
        mock_coordinator.async_request_refresh.assert_not_called()

    @pytest.mark.asyncio
    async def test_async_handle_remove_presence_sensor_error(
        self, mock_area_manager, mock_coordinator
    ):
        """Test removing presence sensor when remove_presence_sensor raises error."""
        call = MagicMock(spec=ServiceCall)
        call.data = {
            ATTR_AREA_ID: "living_room",
            "entity_id": "binary_sensor.motion",
        }
        
        # Make remove_presence_sensor raise ValueError
        area = mock_area_manager.get_area.return_value
        area.remove_presence_sensor.side_effect = ValueError("Sensor not found")
        
        # Should not raise, just log error
        await async_handle_remove_presence_sensor(call, mock_area_manager, mock_coordinator)
        
        # Should not save or refresh on error
        mock_area_manager.async_save.assert_not_called()
        mock_coordinator.async_request_refresh.assert_not_called()
