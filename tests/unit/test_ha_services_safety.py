"""Tests for ha_services/safety_handlers module."""
from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock

import pytest
from homeassistant.core import HomeAssistant, ServiceCall

from smart_heating.ha_services.safety_handlers import (
    async_handle_set_safety_sensor,
    async_handle_remove_safety_sensor,
)
from smart_heating.const import DOMAIN


@pytest.fixture
def mock_hass():
    """Create mock Home Assistant instance."""
    hass = MagicMock(spec=HomeAssistant)
    hass.data = {DOMAIN: {}}
    return hass


@pytest.fixture
def mock_safety_monitor():
    """Create mock safety monitor."""
    monitor = MagicMock()
    monitor.async_reconfigure = AsyncMock()
    return monitor


@pytest.fixture
def mock_area_manager():
    """Create mock area manager."""
    manager = MagicMock()
    manager.add_safety_sensor = MagicMock()
    manager.remove_safety_sensor = MagicMock()
    manager.async_save = AsyncMock()
    return manager


@pytest.fixture
def mock_coordinator():
    """Create mock coordinator."""
    coordinator = MagicMock()
    coordinator.async_request_refresh = AsyncMock()
    return coordinator


class TestSafetyHandlers:
    """Test safety sensor service handlers."""

    @pytest.mark.asyncio
    async def test_async_handle_set_safety_sensor_success(
        self, mock_hass, mock_safety_monitor, mock_area_manager, mock_coordinator
    ):
        """Test setting safety sensor successfully."""
        mock_hass.data[DOMAIN]["safety_monitor"] = mock_safety_monitor
        
        call = MagicMock(spec=ServiceCall)
        call.data = {
            "sensor_id": "binary_sensor.smoke_detector",
            "attribute": "smoke",
            "alert_value": True,
            "enabled": True,
        }
        
        await async_handle_set_safety_sensor(
            call, mock_hass, mock_area_manager, mock_coordinator
        )
        
        # Verify sensor was added
        mock_area_manager.add_safety_sensor.assert_called_once_with(
            "binary_sensor.smoke_detector", "smoke", True, True
        )
        # Verify data was saved
        mock_area_manager.async_save.assert_called_once()
        # Verify safety monitor was reconfigured
        mock_safety_monitor.async_reconfigure.assert_called_once()

    @pytest.mark.asyncio
    async def test_async_handle_set_safety_sensor_defaults(
        self, mock_hass, mock_safety_monitor, mock_area_manager, mock_coordinator
    ):
        """Test setting safety sensor with default values."""
        mock_hass.data[DOMAIN]["safety_monitor"] = mock_safety_monitor
        
        call = MagicMock(spec=ServiceCall)
        call.data = {"sensor_id": "binary_sensor.smoke_detector"}
        
        await async_handle_set_safety_sensor(
            call, mock_hass, mock_area_manager, mock_coordinator
        )
        
        # Verify sensor was added with defaults
        mock_area_manager.add_safety_sensor.assert_called_once_with(
            "binary_sensor.smoke_detector", "smoke", True, True
        )

    @pytest.mark.asyncio
    async def test_async_handle_set_safety_sensor_no_monitor(
        self, mock_hass, mock_area_manager, mock_coordinator
    ):
        """Test setting safety sensor when safety monitor not found."""
        # No safety_monitor in hass.data
        call = MagicMock(spec=ServiceCall)
        call.data = {"sensor_id": "binary_sensor.smoke_detector"}
        
        await async_handle_set_safety_sensor(
            call, mock_hass, mock_area_manager, mock_coordinator
        )
        
        # Verify sensor was still added
        mock_area_manager.add_safety_sensor.assert_called_once()
        # Verify data was saved
        mock_area_manager.async_save.assert_called_once()

    @pytest.mark.asyncio
    async def test_async_handle_set_safety_sensor_error(
        self, mock_hass, mock_area_manager, mock_coordinator
    ):
        """Test setting safety sensor when error occurs."""
        call = MagicMock(spec=ServiceCall)
        call.data = {"sensor_id": "binary_sensor.smoke_detector"}
        
        # Make add_safety_sensor raise exception
        mock_area_manager.add_safety_sensor.side_effect = Exception("Sensor error")
        
        # Should not raise, just log error
        await async_handle_set_safety_sensor(
            call, mock_hass, mock_area_manager, mock_coordinator
        )

    @pytest.mark.asyncio
    async def test_async_handle_remove_safety_sensor_success(
        self, mock_hass, mock_safety_monitor, mock_area_manager, mock_coordinator
    ):
        """Test removing safety sensor successfully."""
        mock_hass.data[DOMAIN]["safety_monitor"] = mock_safety_monitor
        
        call = MagicMock(spec=ServiceCall)
        call.data = {"sensor_id": "binary_sensor.smoke_detector"}
        
        await async_handle_remove_safety_sensor(
            call, mock_hass, mock_area_manager, mock_coordinator
        )
        
        # Verify sensor was removed
        mock_area_manager.remove_safety_sensor.assert_called_once_with(
            "binary_sensor.smoke_detector"
        )
        # Verify data was saved
        mock_area_manager.async_save.assert_called_once()
        # Verify safety monitor was reconfigured
        mock_safety_monitor.async_reconfigure.assert_called_once()

    @pytest.mark.asyncio
    async def test_async_handle_remove_safety_sensor_no_monitor(
        self, mock_hass, mock_area_manager, mock_coordinator
    ):
        """Test removing safety sensor when safety monitor not found."""
        # No safety_monitor in hass.data
        call = MagicMock(spec=ServiceCall)
        call.data = {"sensor_id": "binary_sensor.smoke_detector"}
        
        await async_handle_remove_safety_sensor(
            call, mock_hass, mock_area_manager, mock_coordinator
        )
        
        # Verify sensor was still removed
        mock_area_manager.remove_safety_sensor.assert_called_once()
        # Verify data was saved
        mock_area_manager.async_save.assert_called_once()

    @pytest.mark.asyncio
    async def test_async_handle_remove_safety_sensor_error(
        self, mock_hass, mock_area_manager, mock_coordinator
    ):
        """Test removing safety sensor when error occurs."""
        call = MagicMock(spec=ServiceCall)
        call.data = {"sensor_id": "binary_sensor.smoke_detector"}
        
        # Make remove_safety_sensor raise exception
        mock_area_manager.remove_safety_sensor.side_effect = Exception("Sensor not found")
        
        # Should not raise, just log error
        await async_handle_remove_safety_sensor(
            call, mock_hass, mock_area_manager, mock_coordinator
        )
