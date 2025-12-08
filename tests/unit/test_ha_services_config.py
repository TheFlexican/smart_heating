"""Tests for ha_services/config_handlers module."""
from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock

import pytest
from homeassistant.core import HomeAssistant, ServiceCall

from smart_heating.ha_services.config_handlers import (
    async_handle_set_hysteresis,
    async_handle_set_opentherm_gateway,
    async_handle_set_trv_temperatures,
    async_handle_set_frost_protection,
    async_handle_set_history_retention,
)
from smart_heating.const import (
    ATTR_HYSTERESIS,
    ATTR_FROST_PROTECTION_ENABLED,
    ATTR_FROST_PROTECTION_TEMP,
    ATTR_HISTORY_RETENTION_DAYS,
    DOMAIN,
)


@pytest.fixture
def mock_hass():
    """Create mock Home Assistant instance."""
    hass = MagicMock(spec=HomeAssistant)
    hass.data = {DOMAIN: {}}
    return hass


@pytest.fixture
def mock_climate_controller():
    """Create mock climate controller."""
    controller = MagicMock()
    controller._hysteresis = 0.5
    return controller


@pytest.fixture
def mock_history_tracker():
    """Create mock history tracker."""
    tracker = MagicMock()
    tracker.set_retention_days = MagicMock()
    tracker.async_save = AsyncMock()
    tracker._async_cleanup_old_entries = AsyncMock()
    return tracker


@pytest.fixture
def mock_area_manager():
    """Create mock area manager."""
    manager = MagicMock()
    manager.set_opentherm_gateway = MagicMock()
    manager.set_trv_temperatures = MagicMock()
    manager.add_safety_sensor = MagicMock()
    manager.remove_safety_sensor = MagicMock()
    manager.frost_protection_enabled = False
    manager.frost_protection_temp = 7.0
    manager.async_save = AsyncMock()
    return manager


@pytest.fixture
def mock_coordinator():
    """Create mock coordinator."""
    coordinator = MagicMock()
    coordinator.async_request_refresh = AsyncMock()
    return coordinator


class TestConfigHandlers:
    """Test configuration service handlers."""

    @pytest.mark.asyncio
    async def test_async_handle_set_hysteresis_success(
        self, mock_hass, mock_climate_controller, mock_coordinator
    ):
        """Test setting hysteresis successfully."""
        mock_hass.data[DOMAIN]["climate_controller"] = mock_climate_controller
        
        call = MagicMock(spec=ServiceCall)
        call.data = {ATTR_HYSTERESIS: 0.8}
        
        await async_handle_set_hysteresis(call, mock_hass, mock_coordinator)
        
        # Verify hysteresis was set
        assert mock_climate_controller._hysteresis == 0.8

    @pytest.mark.asyncio
    async def test_async_handle_set_hysteresis_no_controller(
        self, mock_hass, mock_coordinator
    ):
        """Test setting hysteresis when climate controller not found."""
        # No climate_controller in hass.data
        call = MagicMock(spec=ServiceCall)
        call.data = {ATTR_HYSTERESIS: 0.8}
        
        # Should not raise, just log error
        await async_handle_set_hysteresis(call, mock_hass, mock_coordinator)

    @pytest.mark.asyncio
    async def test_async_handle_set_opentherm_gateway_success(
        self, mock_area_manager, mock_coordinator
    ):
        """Test setting OpenTherm gateway successfully."""
        call = MagicMock(spec=ServiceCall)
        call.data = {
            "gateway_id": "climate.gateway",
            "enabled": True,
        }
        
        await async_handle_set_opentherm_gateway(call, mock_area_manager, mock_coordinator)
        
        # Verify gateway was set
        mock_area_manager.set_opentherm_gateway.assert_called_once_with("climate.gateway", True)
        # Verify data was saved
        mock_area_manager.async_save.assert_called_once()

    @pytest.mark.asyncio
    async def test_async_handle_set_opentherm_gateway_default_enabled(
        self, mock_area_manager, mock_coordinator
    ):
        """Test setting OpenTherm gateway with default enabled=True."""
        call = MagicMock(spec=ServiceCall)
        call.data = {"gateway_id": "climate.gateway"}
        
        await async_handle_set_opentherm_gateway(call, mock_area_manager, mock_coordinator)
        
        # Verify gateway was set with default enabled=True
        mock_area_manager.set_opentherm_gateway.assert_called_once_with("climate.gateway", True)

    @pytest.mark.asyncio
    async def test_async_handle_set_opentherm_gateway_error(
        self, mock_area_manager, mock_coordinator
    ):
        """Test setting OpenTherm gateway when error occurs."""
        call = MagicMock(spec=ServiceCall)
        call.data = {"gateway_id": "climate.gateway"}
        
        # Make set_opentherm_gateway raise ValueError
        mock_area_manager.set_opentherm_gateway.side_effect = ValueError("Invalid gateway")
        
        # Should not raise, just log error
        await async_handle_set_opentherm_gateway(call, mock_area_manager, mock_coordinator)
        
        # Should not save on error
        mock_area_manager.async_save.assert_not_called()

    @pytest.mark.asyncio
    async def test_async_handle_set_trv_temperatures_success(
        self, mock_area_manager, mock_coordinator
    ):
        """Test setting TRV temperatures successfully."""
        call = MagicMock(spec=ServiceCall)
        call.data = {
            "heating_temp": 26.0,
            "idle_temp": 8.0,
            "temp_offset": 1.5,
        }
        
        await async_handle_set_trv_temperatures(call, mock_area_manager, mock_coordinator)
        
        # Verify temperatures were set
        mock_area_manager.set_trv_temperatures.assert_called_once_with(26.0, 8.0, 1.5)
        # Verify data was saved
        mock_area_manager.async_save.assert_called_once()

    @pytest.mark.asyncio
    async def test_async_handle_set_trv_temperatures_defaults(
        self, mock_area_manager, mock_coordinator
    ):
        """Test setting TRV temperatures with default values."""
        call = MagicMock(spec=ServiceCall)
        call.data = {}
        
        await async_handle_set_trv_temperatures(call, mock_area_manager, mock_coordinator)
        
        # Verify temperatures were set with defaults
        mock_area_manager.set_trv_temperatures.assert_called_once_with(25.0, 10.0, None)

    @pytest.mark.asyncio
    async def test_async_handle_set_trv_temperatures_error(
        self, mock_area_manager, mock_coordinator
    ):
        """Test setting TRV temperatures when error occurs."""
        call = MagicMock(spec=ServiceCall)
        call.data = {}
        
        # Make set_trv_temperatures raise ValueError
        mock_area_manager.set_trv_temperatures.side_effect = ValueError("Invalid temperatures")
        
        # Should not raise, just log error
        await async_handle_set_trv_temperatures(call, mock_area_manager, mock_coordinator)
        
        # Should not save on error
        mock_area_manager.async_save.assert_not_called()

    @pytest.mark.asyncio
    async def test_async_handle_set_frost_protection_success(
        self, mock_area_manager, mock_coordinator
    ):
        """Test setting frost protection successfully."""
        call = MagicMock(spec=ServiceCall)
        call.data = {
            ATTR_FROST_PROTECTION_ENABLED: True,
            ATTR_FROST_PROTECTION_TEMP: 5.0,
        }
        
        await async_handle_set_frost_protection(call, mock_area_manager, mock_coordinator)
        
        # Verify frost protection was set
        assert mock_area_manager.frost_protection_enabled is True
        assert mock_area_manager.frost_protection_temp == 5.0
        # Verify data was saved
        mock_area_manager.async_save.assert_called_once()
        # Verify coordinator refresh
        mock_coordinator.async_request_refresh.assert_called_once()

    @pytest.mark.asyncio
    async def test_async_handle_set_frost_protection_partial(
        self, mock_area_manager, mock_coordinator
    ):
        """Test setting only frost protection enabled."""
        call = MagicMock(spec=ServiceCall)
        call.data = {ATTR_FROST_PROTECTION_ENABLED: True}
        
        original_temp = mock_area_manager.frost_protection_temp
        
        await async_handle_set_frost_protection(call, mock_area_manager, mock_coordinator)
        
        # Verify only enabled was set
        assert mock_area_manager.frost_protection_enabled is True
        # Verify temp was not changed
        assert mock_area_manager.frost_protection_temp == original_temp

    @pytest.mark.asyncio
    async def test_async_handle_set_frost_protection_error(
        self, mock_area_manager, mock_coordinator
    ):
        """Test setting frost protection when error occurs."""
        call = MagicMock(spec=ServiceCall)
        call.data = {ATTR_FROST_PROTECTION_ENABLED: True}
        
        # Make async_save raise ValueError
        mock_area_manager.async_save.side_effect = ValueError("Save failed")
        
        # Should not raise, just log error
        await async_handle_set_frost_protection(call, mock_area_manager, mock_coordinator)
        
        # Should not refresh on error
        mock_coordinator.async_request_refresh.assert_not_called()

    @pytest.mark.asyncio
    async def test_async_handle_set_history_retention_success(
        self, mock_hass, mock_history_tracker, mock_coordinator
    ):
        """Test setting history retention successfully."""
        mock_hass.data[DOMAIN]["history"] = mock_history_tracker
        
        call = MagicMock(spec=ServiceCall)
        call.data = {ATTR_HISTORY_RETENTION_DAYS: 30}
        
        await async_handle_set_history_retention(call, mock_hass, mock_coordinator)
        
        # Verify retention was set
        mock_history_tracker.set_retention_days.assert_called_once_with(30)
        # Verify data was saved
        mock_history_tracker.async_save.assert_called_once()
        # Verify cleanup was triggered
        mock_history_tracker._async_cleanup_old_entries.assert_called_once()

    @pytest.mark.asyncio
    async def test_async_handle_set_history_retention_no_tracker(
        self, mock_hass, mock_coordinator
    ):
        """Test setting history retention when tracker not found."""
        # No history tracker in hass.data
        call = MagicMock(spec=ServiceCall)
        call.data = {ATTR_HISTORY_RETENTION_DAYS: 30}
        
        # Should not raise, just log error
        await async_handle_set_history_retention(call, mock_hass, mock_coordinator)

    @pytest.mark.asyncio
    async def test_async_handle_set_history_retention_error(
        self, mock_hass, mock_history_tracker, mock_coordinator
    ):
        """Test setting history retention when error occurs."""
        mock_hass.data[DOMAIN]["history"] = mock_history_tracker
        
        call = MagicMock(spec=ServiceCall)
        call.data = {ATTR_HISTORY_RETENTION_DAYS: 30}
        
        # Make set_retention_days raise exception
        mock_history_tracker.set_retention_days.side_effect = Exception("Invalid retention")
        
        # Should not raise, just log error
        await async_handle_set_history_retention(call, mock_hass, mock_coordinator)
