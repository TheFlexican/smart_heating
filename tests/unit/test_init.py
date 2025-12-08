"""Tests for __init__.py integration setup."""
from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from homeassistant.core import HomeAssistant

from smart_heating import (
    async_setup_entry,
    async_unload_entry,
)
from smart_heating.const import DOMAIN, PLATFORMS


class TestIntegrationSetup:
    """Test integration setup."""

    async def test_async_setup_entry_success(
        self, hass: HomeAssistant, mock_config_entry
    ):
        """Test successful integration setup."""
        mock_config_entry.add_to_hass(hass)
        
        with patch(
            "smart_heating.AreaManager"
        ) as mock_area_manager_class, \
        patch("smart_heating.HistoryTracker") as mock_history_class, \
        patch("smart_heating.AreaLogger") as mock_logger_class, \
        patch("smart_heating.VacationManager") as mock_vacation_class, \
        patch("smart_heating.SafetyMonitor") as mock_safety_class, \
        patch("smart_heating.LearningEngine") as mock_learning_class, \
        patch("smart_heating.SmartHeatingCoordinator") as mock_coordinator_class, \
        patch("smart_heating.ClimateController") as mock_climate_class, \
        patch("smart_heating.ScheduleExecutor") as mock_schedule_class, \
        patch("smart_heating.setup_api") as mock_setup_api, \
        patch("smart_heating.setup_websocket") as mock_setup_ws, \
        patch("smart_heating.async_register_panel") as mock_register_panel, \
        patch("smart_heating.async_setup_services") as mock_setup_services, \
        patch("smart_heating.async_track_time_interval"), \
        patch.object(hass.config_entries, "async_forward_entry_setups", new=AsyncMock()):
            
            # Configure mocks
            mock_area_manager = AsyncMock()
            mock_area_manager.async_load = AsyncMock()
            mock_area_manager_class.return_value = mock_area_manager
            
            mock_history = AsyncMock()
            mock_history.async_load = AsyncMock()
            mock_history_class.return_value = mock_history
            
            mock_logger = MagicMock()
            mock_logger_class.return_value = mock_logger
            
            mock_vacation = AsyncMock()
            mock_vacation.async_load = AsyncMock()
            mock_vacation_class.return_value = mock_vacation
            
            mock_safety = AsyncMock()
            mock_safety.async_setup = AsyncMock()
            mock_safety_class.return_value = mock_safety
            
            mock_learning = MagicMock()
            mock_learning_class.return_value = mock_learning
            
            mock_coordinator = AsyncMock()
            mock_coordinator.async_setup = AsyncMock()
            mock_coordinator_class.return_value = mock_coordinator
            
            mock_climate = MagicMock()
            mock_climate.async_control_heating = AsyncMock()
            mock_climate_class.return_value = mock_climate
            
            mock_schedule = AsyncMock()
            mock_schedule.async_start = AsyncMock()
            mock_schedule_class.return_value = mock_schedule
            
            mock_setup_api.return_value = AsyncMock()
            mock_setup_ws.return_value = AsyncMock()
            mock_register_panel.return_value = AsyncMock()
            mock_setup_services.return_value = AsyncMock()
            
            # Run setup
            result = await async_setup_entry(hass, mock_config_entry)
            
            # Assert success
            assert result is True
            
            # Verify AreaManager was created and loaded
            mock_area_manager_class.assert_called_once_with(hass)
            mock_area_manager.async_load.assert_called_once()
            
            # Verify domain data structure
            assert DOMAIN in hass.data
            assert mock_config_entry.entry_id in hass.data[DOMAIN]
            assert hass.data[DOMAIN]["history"] == mock_history
            assert hass.data[DOMAIN]["area_logger"] == mock_logger
            assert hass.data[DOMAIN]["vacation_manager"] == mock_vacation
            assert hass.data[DOMAIN]["safety_monitor"] == mock_safety
            assert hass.data[DOMAIN]["learning_engine"] == mock_learning
            assert hass.data[DOMAIN]["climate_controller"] == mock_climate
            assert hass.data[DOMAIN]["schedule_executor"] == mock_schedule
            
            # Verify coordinator stored
            assert hass.data[DOMAIN][mock_config_entry.entry_id] == mock_coordinator
            
            # Verify all components were initialized
            mock_history.async_load.assert_called_once()
            mock_vacation.async_load.assert_called_once()
            mock_safety.async_setup.assert_called_once()
            mock_coordinator.async_setup.assert_called_once()
            mock_schedule.async_start.assert_called_once()

    async def test_async_setup_entry_with_opentherm_config(
        self, hass: HomeAssistant
    ):
        """Test setup with OpenTherm gateway configuration."""
        # Create config entry with options
        from pytest_homeassistant_custom_component.common import MockConfigEntry
        mock_config_entry = MockConfigEntry(
            domain=DOMAIN,
            data={"name": "Smart Heating"},
            entry_id="test_entry_id",
            title="Smart Heating",
            options={
                "opentherm_gateway_id": "climate.opentherm",
                "opentherm_enabled": True,
            },
        )
        mock_config_entry.add_to_hass(hass)
        
        with patch(
            "smart_heating.AreaManager"
        ) as mock_area_manager_class, \
        patch("smart_heating.HistoryTracker") as mock_history_class, \
        patch("smart_heating.AreaLogger"), \
        patch("smart_heating.VacationManager") as mock_vacation_class, \
        patch("smart_heating.SafetyMonitor") as mock_safety_class, \
        patch("smart_heating.LearningEngine"), \
        patch("smart_heating.SmartHeatingCoordinator") as mock_coordinator_class, \
        patch("smart_heating.ClimateController"), \
        patch("smart_heating.ScheduleExecutor") as mock_schedule_class, \
        patch("smart_heating.setup_api"), \
        patch("smart_heating.setup_websocket"), \
        patch("smart_heating.async_register_panel"), \
        patch("smart_heating.async_setup_services"), \
        patch("smart_heating.async_track_time_interval"), \
        patch.object(hass.config_entries, "async_forward_entry_setups", new=AsyncMock()):
        
            # Setup all async mocks properly
            mock_area_manager = MagicMock()
            mock_area_manager.async_load = AsyncMock()
            mock_area_manager.set_opentherm_gateway = MagicMock()
            mock_area_manager_class.return_value = mock_area_manager
            
            mock_history = MagicMock()
            mock_history.async_load = AsyncMock()
            mock_history_class.return_value = mock_history
            
            mock_vacation = MagicMock()
            mock_vacation.async_load = AsyncMock()
            mock_vacation_class.return_value = mock_vacation
            
            mock_safety = MagicMock()
            mock_safety.async_setup = AsyncMock()
            mock_safety_class.return_value = mock_safety
            
            mock_schedule = MagicMock()
            mock_schedule.async_start = AsyncMock()
            mock_schedule_class.return_value = mock_schedule
            
            mock_coordinator = MagicMock()
            mock_coordinator.async_setup = AsyncMock()
            mock_coordinator_class.return_value = mock_coordinator            # Run setup
            await async_setup_entry(hass, mock_config_entry)
            
            # Verify OpenTherm gateway was set
            mock_area_manager.set_opentherm_gateway.assert_called_once_with(
                "climate.opentherm",
                enabled=True
            )

    async def test_async_unload_entry_success(
        self, hass: HomeAssistant, mock_config_entry
    ):
        """Test successful integration unload."""
        mock_config_entry.add_to_hass(hass)
        
        # Setup hass.data structure
        hass.data[DOMAIN] = {
            mock_config_entry.entry_id: MagicMock(async_shutdown=AsyncMock()),
            "safety_monitor": MagicMock(async_shutdown=AsyncMock()),
            "climate_unsub": MagicMock(),
            "schedule_executor": MagicMock(async_stop=AsyncMock()),
            "history": MagicMock(async_unload=AsyncMock()),
        }
        
        with patch.object(
            hass.config_entries, "async_unload_platforms", return_value=True
        ) as mock_unload_platforms, \
        patch("homeassistant.components.frontend.async_remove_panel") as mock_remove_panel:
            
            # Run unload
            result = await async_unload_entry(hass, mock_config_entry)
            
            # Assert success
            assert result is True
            
            # Verify platforms were unloaded
            mock_unload_platforms.assert_called_once_with(mock_config_entry, PLATFORMS)
            
            # Verify components were shutdown
            hass.data[DOMAIN]["safety_monitor"].async_shutdown.assert_called_once()
            hass.data[DOMAIN]["climate_unsub"].assert_called_once()
            hass.data[DOMAIN]["schedule_executor"].async_stop.assert_called_once()
            hass.data[DOMAIN]["history"].async_unload.assert_called_once()
            
            # Verify coordinator was removed from hass.data
            assert mock_config_entry.entry_id not in hass.data[DOMAIN]

    async def test_async_unload_entry_platform_unload_fails(
        self, hass: HomeAssistant, mock_config_entry
    ):
        """Test unload when platform unload fails."""
        mock_config_entry.add_to_hass(hass)
        
        hass.data[DOMAIN] = {}
        
        with patch.object(
            hass.config_entries, "async_unload_platforms", return_value=False
        ) as mock_unload_platforms:
            
            # Run unload
            result = await async_unload_entry(hass, mock_config_entry)
            
            # Assert failure
            assert result is False
            
            # Verify platforms unload was attempted
            mock_unload_platforms.assert_called_once_with(mock_config_entry, PLATFORMS)


class TestIntegrationData:
    """Test integration data management."""

    async def test_coordinator_stored_correctly(
        self, hass: HomeAssistant, mock_config_entry
    ):
        """Test that coordinator is stored correctly in hass.data."""
        mock_config_entry.add_to_hass(hass)
        
        with patch("smart_heating.AreaManager") as mock_area_class, \
        patch("smart_heating.HistoryTracker") as mock_history_class, \
        patch("smart_heating.AreaLogger"), \
        patch("smart_heating.VacationManager") as mock_vacation_class, \
        patch("smart_heating.SafetyMonitor") as mock_safety_class, \
        patch("smart_heating.LearningEngine") as mock_learning_class, \
        patch("smart_heating.SmartHeatingCoordinator") as mock_coordinator_class, \
        patch("smart_heating.ClimateController"), \
        patch("smart_heating.ScheduleExecutor") as mock_schedule_class, \
        patch("smart_heating.setup_api"), \
        patch("smart_heating.setup_websocket"), \
        patch("smart_heating.async_register_panel"), \
        patch("smart_heating.async_setup_services"), \
        patch("smart_heating.async_track_time_interval"), \
        patch.object(hass.config_entries, "async_forward_entry_setups", new=AsyncMock()):\
            
            # Setup all async mocks properly
            mock_area = MagicMock()
            mock_area.async_load = AsyncMock()
            mock_area_class.return_value = mock_area
            
            mock_history = MagicMock()
            mock_history.async_load = AsyncMock()
            mock_history_class.return_value = mock_history
            
            mock_vacation = MagicMock()
            mock_vacation.async_load = AsyncMock()
            mock_vacation_class.return_value = mock_vacation
            
            mock_safety = MagicMock()
            mock_safety.async_setup = AsyncMock()
            mock_safety_class.return_value = mock_safety
            
            mock_learning = MagicMock()
            mock_learning_class.return_value = mock_learning
            
            mock_schedule = MagicMock()
            mock_schedule.async_start = AsyncMock()
            mock_schedule_class.return_value = mock_schedule
            
            mock_coordinator = MagicMock()
            mock_coordinator.async_setup = AsyncMock()
            mock_coordinator_class.return_value = mock_coordinator
            
            await async_setup_entry(hass, mock_config_entry)
            
            # Verify coordinator is stored with entry_id as key
            assert hass.data[DOMAIN][mock_config_entry.entry_id] == mock_coordinator

    async def test_all_managers_stored(
        self, hass: HomeAssistant, mock_config_entry
    ):
        """Test that all managers are stored in hass.data."""
        mock_config_entry.add_to_hass(hass)
        
        with patch("smart_heating.AreaManager") as mock_area_class, \
        patch("smart_heating.HistoryTracker") as mock_history_class, \
        patch("smart_heating.AreaLogger") as mock_logger_class, \
        patch("smart_heating.VacationManager") as mock_vacation_class, \
        patch("smart_heating.SafetyMonitor") as mock_safety_class, \
        patch("smart_heating.LearningEngine") as mock_learning_class, \
        patch("smart_heating.SmartHeatingCoordinator") as mock_coordinator_class, \
        patch("smart_heating.ClimateController") as mock_climate_class, \
        patch("smart_heating.ScheduleExecutor") as mock_schedule_class, \
        patch("smart_heating.setup_api"), \
        patch("smart_heating.setup_websocket"), \
        patch("smart_heating.async_register_panel"), \
        patch("smart_heating.async_setup_services"), \
        patch("smart_heating.async_track_time_interval"), \
        patch.object(hass.config_entries, "async_forward_entry_setups", new=AsyncMock()):
        
            # Setup all async mocks properly
            mock_area = MagicMock()
            mock_area.async_load = AsyncMock()
            mock_area_class.return_value = mock_area
            
            mock_history = MagicMock()
            mock_history.async_load = AsyncMock()
            mock_history_class.return_value = mock_history
            
            mock_logger = MagicMock()
            mock_logger_class.return_value = mock_logger
            
            mock_vacation = MagicMock()
            mock_vacation.async_load = AsyncMock()
            mock_vacation_class.return_value = mock_vacation
            
            mock_safety = MagicMock()
            mock_safety.async_setup = AsyncMock()
            mock_safety_class.return_value = mock_safety
            
            mock_learning = MagicMock()
            mock_learning_class.return_value = mock_learning
            
            mock_climate = MagicMock()
            mock_climate_class.return_value = mock_climate
            
            mock_schedule = MagicMock()
            mock_schedule.async_start = AsyncMock()
            mock_schedule_class.return_value = mock_schedule
            
            mock_coordinator = MagicMock()
            mock_coordinator.async_setup = AsyncMock()
            mock_coordinator_class.return_value = mock_coordinator
            
            await async_setup_entry(hass, mock_config_entry)
            
            # Verify all managers are stored
            assert hass.data[DOMAIN]["history"] == mock_history
            assert hass.data[DOMAIN]["area_logger"] == mock_logger
            assert hass.data[DOMAIN]["vacation_manager"] == mock_vacation
            assert hass.data[DOMAIN]["safety_monitor"] == mock_safety
            assert hass.data[DOMAIN]["learning_engine"] == mock_learning
            assert hass.data[DOMAIN]["climate_controller"] == mock_climate
            assert hass.data[DOMAIN]["schedule_executor"] == mock_schedule
