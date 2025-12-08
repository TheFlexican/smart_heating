"""Tests for Smart Heating Coordinator."""
from __future__ import annotations

from datetime import timedelta
from unittest.mock import AsyncMock, MagicMock, patch, call

import pytest
from homeassistant.core import HomeAssistant, State, Event
from homeassistant.helpers.update_coordinator import UpdateFailed

from smart_heating.coordinator import SmartHeatingCoordinator
from smart_heating.const import DOMAIN, UPDATE_INTERVAL, STATE_INITIALIZED

from tests.unit.const import TEST_AREA_ID


@pytest.fixture
def coordinator(hass: HomeAssistant, mock_config_entry, mock_area_manager) -> SmartHeatingCoordinator:
    """Create a SmartHeatingCoordinator instance."""
    return SmartHeatingCoordinator(hass, mock_config_entry, mock_area_manager)


class TestCoordinatorInitialization:
    """Test Coordinator initialization."""

    def test_init(self, hass: HomeAssistant, mock_config_entry, mock_area_manager):
        """Test coordinator initialization."""
        coordinator = SmartHeatingCoordinator(hass, mock_config_entry, mock_area_manager)

        assert coordinator.hass == hass
        assert coordinator.area_manager == mock_area_manager
        assert coordinator.name == DOMAIN
        assert coordinator.update_interval == UPDATE_INTERVAL
        assert coordinator._unsub_state_listener is None

    def test_update_interval(self, hass: HomeAssistant, mock_config_entry, mock_area_manager):
        """Test update interval configuration."""
        coordinator = SmartHeatingCoordinator(hass, mock_config_entry, mock_area_manager)
        
        # Should use UPDATE_INTERVAL constant
        assert coordinator.update_interval == UPDATE_INTERVAL


class TestCoordinatorSetup:
    """Test coordinator setup."""

    async def test_async_setup_no_devices(self, coordinator: SmartHeatingCoordinator):
        """Test setup with no devices."""
        coordinator.area_manager.get_all_areas.return_value = {}
        
        with patch("smart_heating.coordinator.async_track_state_change_event") as mock_track:
            await coordinator.async_setup()
            
            # Should not set up state listeners if no devices
            mock_track.assert_not_called()
            assert coordinator._unsub_state_listener is None

    async def test_async_setup_with_devices(self, coordinator: SmartHeatingCoordinator, mock_area_data):
        """Test setup with devices."""
        mock_area = MagicMock()
        mock_area.devices = {"climate.test": {"type": "thermostat"}}
        coordinator.area_manager.get_all_areas.return_value = {TEST_AREA_ID: mock_area}
        
        with patch("smart_heating.coordinator.async_track_state_change_event") as mock_track:
            mock_track.return_value = MagicMock()
            await coordinator.async_setup()
            
            # Should set up state listeners for devices
            mock_track.assert_called_once()
            assert coordinator._unsub_state_listener is not None

    async def test_async_shutdown(self, coordinator: SmartHeatingCoordinator):
        """Test coordinator shutdown."""
        mock_unsub = MagicMock()
        coordinator._unsub_state_listener = mock_unsub
        
        await coordinator.async_shutdown()
        
        mock_unsub.assert_called_once()
        assert coordinator._unsub_state_listener is None


class TestCoordinatorDataUpdate:
    """Test Coordinator data update."""

    async def test_async_update_data_success(
        self, coordinator: SmartHeatingCoordinator, mock_area_data
    ):
        """Test successful data update."""
        # Create mock area with proper attributes
        mock_area = MagicMock()
        mock_area.area_id = TEST_AREA_ID
        mock_area.name = "Living Room"
        mock_area.enabled = True
        mock_area.state = "heat"
        mock_area.target_temperature = 21.0
        mock_area.current_temperature = 20.0
        mock_area.devices = {}
        mock_area.schedules = {}
        mock_area.preset_mode = "comfort"
        mock_area.away_temp = 16.0
        mock_area.eco_temp = 18.0
        mock_area.comfort_temp = 21.0
        mock_area.home_temp = 20.0
        mock_area.sleep_temp = 17.0
        mock_area.activity_temp = 22.0
        mock_area.use_global_away = True
        mock_area.use_global_eco = True
        mock_area.use_global_comfort = True
        mock_area.use_global_home = True
        mock_area.use_global_sleep = True
        mock_area.use_global_activity = True
        mock_area.use_global_presence = True
        mock_area.boost_mode_active = False
        mock_area.boost_temp = 23.0
        mock_area.boost_duration = 60
        mock_area.hvac_mode = "heat"
        mock_area.hysteresis_override = None
        mock_area.manual_override = False
        mock_area.hidden = False
        mock_area.shutdown_switches_when_idle = True
        mock_area.window_sensors = []
        mock_area.presence_sensors = []
        mock_area.night_boost_enabled = True
        mock_area.night_boost_offset = 0.5
        mock_area.night_boost_start_time = "22:00"
        mock_area.night_boost_end_time = "06:00"
        mock_area.smart_night_boost_enabled = False
        mock_area.smart_night_boost_target_time = "06:00"
        mock_area.weather_entity_id = None
        mock_area.get_effective_target_temperature.return_value = 21.0
        
        coordinator.area_manager.get_all_areas.return_value = {
            TEST_AREA_ID: mock_area
        }

        data = await coordinator._async_update_data()

        assert data["status"] == STATE_INITIALIZED
        assert data["area_count"] == 1
        assert "areas" in data
        assert TEST_AREA_ID in data["areas"]
        assert data["areas"][TEST_AREA_ID]["name"] == "Living Room"
        assert data["areas"][TEST_AREA_ID]["enabled"] is True

    async def test_async_update_data_empty_areas(
        self, coordinator: SmartHeatingCoordinator
    ):
        """Test data update with no areas."""
        coordinator.area_manager.get_all_areas.return_value = {}

        data = await coordinator._async_update_data()

        assert data["status"] == STATE_INITIALIZED
        assert data["area_count"] == 0
        assert data["areas"] == {}

    async def test_async_update_data_with_thermostat(
        self, coordinator: SmartHeatingCoordinator, hass: HomeAssistant
    ):
        """Test data update includes thermostat device states."""
        mock_area = MagicMock()
        mock_area.area_id = TEST_AREA_ID
        mock_area.name = "Living Room"
        mock_area.enabled = True
        mock_area.state = "heat"
        mock_area.target_temperature = 21.0
        mock_area.current_temperature = 20.0
        mock_area.devices = {"climate.test": {"type": "thermostat"}}
        mock_area.schedules = {}
        mock_area.preset_mode = "comfort"
        mock_area.away_temp = 16.0
        mock_area.eco_temp = 18.0
        mock_area.comfort_temp = 21.0
        mock_area.home_temp = 20.0
        mock_area.sleep_temp = 17.0
        mock_area.activity_temp = 22.0
        mock_area.use_global_away = True
        mock_area.use_global_eco = True
        mock_area.use_global_comfort = True
        mock_area.use_global_home = True
        mock_area.use_global_sleep = True
        mock_area.use_global_activity = True
        mock_area.use_global_presence = True
        mock_area.boost_mode_active = False
        mock_area.boost_temp = 23.0
        mock_area.boost_duration = 60
        mock_area.hvac_mode = "heat"
        mock_area.hysteresis_override = None
        mock_area.manual_override = False
        mock_area.hidden = False
        mock_area.shutdown_switches_when_idle = True
        mock_area.window_sensors = []
        mock_area.presence_sensors = []
        mock_area.night_boost_enabled = True
        mock_area.night_boost_offset = 0.5
        mock_area.night_boost_start_time = "22:00"
        mock_area.night_boost_end_time = "06:00"
        mock_area.smart_night_boost_enabled = False
        mock_area.smart_night_boost_target_time = "06:00"
        mock_area.weather_entity_id = None
        mock_area.get_effective_target_temperature.return_value = 21.0
        
        coordinator.area_manager.get_all_areas.return_value = {
            TEST_AREA_ID: mock_area
        }
        
        # Create actual state in hass
        hass.states.async_set(
            "climate.test",
            "heat",
            {
                "friendly_name": "Test Thermostat",
                "current_temperature": 20.0,
                "temperature": 21.0,
                "hvac_action": "heating"
            }
        )

        data = await coordinator._async_update_data()

        assert "areas" in data
        assert TEST_AREA_ID in data["areas"]
        assert len(data["areas"][TEST_AREA_ID]["devices"]) == 1
        device = data["areas"][TEST_AREA_ID]["devices"][0]
        assert device["id"] == "climate.test"
        assert device["type"] == "thermostat"
        assert device["current_temperature"] == 20.0
        assert device["target_temperature"] == 21.0
        assert device["hvac_action"] == "heating"

    async def test_async_update_data_error(
        self, coordinator: SmartHeatingCoordinator
    ):
        """Test data update with error."""
        coordinator.area_manager.get_all_areas.side_effect = Exception("Test error")

        with pytest.raises(UpdateFailed, match="Test error"):
            await coordinator._async_update_data()


class TestStateChangeHandling:
    """Test state change event handling."""

    def test_handle_state_change_no_new_state(self, coordinator: SmartHeatingCoordinator):
        """Test handling state change with no new state."""
        event = MagicMock()
        event.data = {"entity_id": "climate.test", "new_state": None}
        
        # Should not raise any errors
        coordinator._handle_state_change(event)

    def test_handle_state_change_initial_state(self, coordinator: SmartHeatingCoordinator):
        """Test handling initial state (old_state is None)."""
        mock_new_state = MagicMock()
        mock_new_state.state = "heat"
        
        event = MagicMock()
        event.data = {
            "entity_id": "climate.test",
            "old_state": None,
            "new_state": mock_new_state
        }
        
        with patch.object(coordinator.hass, "async_create_task") as mock_create_task:
            coordinator._handle_state_change(event)
            # Should trigger refresh for initial state
            mock_create_task.assert_called_once()

    def test_handle_state_change_state_changed(self, coordinator: SmartHeatingCoordinator):
        """Test handling state change."""
        mock_old_state = MagicMock()
        mock_old_state.state = "idle"
        mock_old_state.attributes = {"temperature": 20.0, "current_temperature": 19.0}
        
        mock_new_state = MagicMock()
        mock_new_state.state = "heat"
        mock_new_state.attributes = {"temperature": 20.0, "current_temperature": 19.0}
        
        event = MagicMock()
        event.data = {
            "entity_id": "climate.test",
            "old_state": mock_old_state,
            "new_state": mock_new_state
        }
        
        with patch.object(coordinator.hass, "async_create_task") as mock_create_task:
            coordinator._handle_state_change(event)
            # Should trigger refresh when state changes
            mock_create_task.assert_called_once()

    def test_handle_state_change_current_temperature_changed(self, coordinator: SmartHeatingCoordinator):
        """Test handling current temperature change."""
        mock_old_state = MagicMock()
        mock_old_state.state = "heat"
        mock_old_state.attributes = {
            "temperature": 21.0,
            "current_temperature": 19.0,
            "hvac_action": "heating"
        }
        
        mock_new_state = MagicMock()
        mock_new_state.state = "heat"
        mock_new_state.attributes = {
            "temperature": 21.0,
            "current_temperature": 20.0,
            "hvac_action": "heating"
        }
        
        event = MagicMock()
        event.data = {
            "entity_id": "climate.test",
            "old_state": mock_old_state,
            "new_state": mock_new_state
        }
        
        with patch.object(coordinator.hass, "async_create_task") as mock_create_task:
            coordinator._handle_state_change(event)
            # Should trigger refresh when current temperature changes
            mock_create_task.assert_called_once()

    def test_handle_state_change_hvac_action_changed(self, coordinator: SmartHeatingCoordinator):
        """Test handling HVAC action change."""
        mock_old_state = MagicMock()
        mock_old_state.state = "heat"
        mock_old_state.attributes = {
            "temperature": 21.0,
            "current_temperature": 20.0,
            "hvac_action": "idle"
        }
        
        mock_new_state = MagicMock()
        mock_new_state.state = "heat"
        mock_new_state.attributes = {
            "temperature": 21.0,
            "current_temperature": 20.0,
            "hvac_action": "heating"
        }
        
        event = MagicMock()
        event.data = {
            "entity_id": "climate.test",
            "old_state": mock_old_state,
            "new_state": mock_new_state
        }
        
        with patch.object(coordinator.hass, "async_create_task") as mock_create_task:
            coordinator._handle_state_change(event)
            # Should trigger refresh when hvac_action changes
            mock_create_task.assert_called_once()

    def test_handle_state_change_target_temperature_debounced(self, coordinator: SmartHeatingCoordinator):
        """Test that target temperature changes are debounced."""
        mock_old_state = MagicMock()
        mock_old_state.state = "heat"
        mock_old_state.attributes = {
            "temperature": 20.0,
            "current_temperature": 19.0,
            "hvac_action": "heating"
        }
        
        mock_new_state = MagicMock()
        mock_new_state.state = "heat"
        mock_new_state.attributes = {
            "temperature": 21.0,  # Target temp changed
            "current_temperature": 19.0,
            "hvac_action": "heating"
        }
        
        event = MagicMock()
        event.data = {
            "entity_id": "climate.test",
            "old_state": mock_old_state,
            "new_state": mock_new_state
        }
        
        with patch.object(coordinator.hass, "async_create_task") as mock_create_task:
            coordinator._handle_state_change(event)
            # Should create debounce task, not trigger immediate refresh
            mock_create_task.assert_called_once()
            # Task should be stored in debounce_tasks
            assert "climate.test" in coordinator._debounce_tasks



class TestCoordinatorDeviceUpdates:
    """Test Coordinator device state updates."""

    async def test_update_device_state(
        self, coordinator: SmartHeatingCoordinator, hass: HomeAssistant
    ):
        """Test updating device state in coordinator data."""
        # Create mock area with thermostat device
        mock_area = MagicMock()
        mock_area.area_id = TEST_AREA_ID
        mock_area.name = "Living Room"
        mock_area.enabled = True
        mock_area.state = "heat"
        mock_area.target_temperature = 21.0
        mock_area.current_temperature = 20.0
        mock_area.devices = {"climate.test": {"type": "thermostat"}}
        mock_area.schedules = {}
        mock_area.preset_mode = "comfort"
        mock_area.away_temp = 16.0
        mock_area.eco_temp = 18.0
        mock_area.comfort_temp = 21.0
        mock_area.home_temp = 20.0
        mock_area.sleep_temp = 17.0
        mock_area.activity_temp = 22.0
        mock_area.use_global_away = True
        mock_area.use_global_eco = True
        mock_area.use_global_comfort = True
        mock_area.use_global_home = True
        mock_area.use_global_sleep = True
        mock_area.use_global_activity = True
        mock_area.use_global_presence = True
        mock_area.boost_mode_active = False
        mock_area.boost_temp = 23.0
        mock_area.boost_duration = 60
        mock_area.hvac_mode = "heat"
        mock_area.hysteresis_override = None
        mock_area.manual_override = False
        mock_area.hidden = False
        mock_area.shutdown_switches_when_idle = True
        mock_area.window_sensors = []
        mock_area.presence_sensors = []
        mock_area.night_boost_enabled = True
        mock_area.night_boost_offset = 0.5
        mock_area.night_boost_start_time = "22:00"
        mock_area.night_boost_end_time = "06:00"
        mock_area.smart_night_boost_enabled = False
        mock_area.smart_night_boost_target_time = "06:00"
        mock_area.weather_entity_id = None
        mock_area.get_effective_target_temperature.return_value = 21.0
        
        coordinator.area_manager.get_all_areas.return_value = {
            TEST_AREA_ID: mock_area
        }

        # Set device state in hass
        hass.states.async_set(
            "climate.test",
            "heat",
            {
                "friendly_name": "Test Thermostat",
                "current_temperature": 20.0,
                "temperature": 21.0,
                "hvac_action": "heating"
            }
        )

        await coordinator.async_request_refresh()

        # Verify device state was captured
        assert coordinator.data is not None
        assert "areas" in coordinator.data
        assert TEST_AREA_ID in coordinator.data["areas"]
        devices = coordinator.data["areas"][TEST_AREA_ID]["devices"]
        assert len(devices) == 1
        assert devices[0]["state"] == "heat"

    async def test_handle_unavailable_device(
        self, coordinator: SmartHeatingCoordinator, hass: HomeAssistant
    ):
        """Test handling unavailable devices."""
        # Create mock area with device
        mock_area = MagicMock()
        mock_area.area_id = TEST_AREA_ID
        mock_area.name = "Living Room"
        mock_area.enabled = True
        mock_area.state = "heat"
        mock_area.target_temperature = 21.0
        mock_area.current_temperature = 20.0
        mock_area.devices = {"climate.unavailable": {"type": "thermostat"}}
        mock_area.schedules = {}
        mock_area.preset_mode = "comfort"
        mock_area.away_temp = 16.0
        mock_area.eco_temp = 18.0
        mock_area.comfort_temp = 21.0
        mock_area.home_temp = 20.0
        mock_area.sleep_temp = 17.0
        mock_area.activity_temp = 22.0
        mock_area.use_global_away = True
        mock_area.use_global_eco = True
        mock_area.use_global_comfort = True
        mock_area.use_global_home = True
        mock_area.use_global_sleep = True
        mock_area.use_global_activity = True
        mock_area.use_global_presence = True
        mock_area.boost_mode_active = False
        mock_area.boost_temp = 23.0
        mock_area.boost_duration = 60
        mock_area.hvac_mode = "heat"
        mock_area.hysteresis_override = None
        mock_area.manual_override = False
        mock_area.hidden = False
        mock_area.shutdown_switches_when_idle = True
        mock_area.window_sensors = []
        mock_area.presence_sensors = []
        mock_area.night_boost_enabled = True
        mock_area.night_boost_offset = 0.5
        mock_area.night_boost_start_time = "22:00"
        mock_area.night_boost_end_time = "06:00"
        mock_area.smart_night_boost_enabled = False
        mock_area.smart_night_boost_target_time = "06:00"
        mock_area.weather_entity_id = None
        mock_area.get_effective_target_temperature.return_value = 21.0
        
        coordinator.area_manager.get_all_areas.return_value = {
            TEST_AREA_ID: mock_area
        }

        # Device state is None (unavailable)
        await coordinator.async_request_refresh()

        # Should not crash and mark device as unavailable
        assert coordinator.data is not None
        assert "areas" in coordinator.data
        devices = coordinator.data["areas"][TEST_AREA_ID]["devices"]
        assert len(devices) == 1
        assert devices[0]["state"] == "unavailable"


class TestCoordinatorAreaUpdates:
    """Test Coordinator area updates."""

    async def test_update_area_temperature(
        self, coordinator: SmartHeatingCoordinator
    ):
        """Test updating area temperature."""
        mock_area = MagicMock()
        mock_area.area_id = TEST_AREA_ID
        mock_area.name = "Living Room"
        mock_area.enabled = True
        mock_area.state = "heat"
        mock_area.target_temperature = 21.0
        mock_area.current_temperature = 20.0
        mock_area.devices = {}
        mock_area.schedules = {}
        mock_area.preset_mode = "comfort"
        mock_area.away_temp = 16.0
        mock_area.eco_temp = 18.0
        mock_area.comfort_temp = 21.0
        mock_area.home_temp = 20.0
        mock_area.sleep_temp = 17.0
        mock_area.activity_temp = 22.0
        mock_area.use_global_away = True
        mock_area.use_global_eco = True
        mock_area.use_global_comfort = True
        mock_area.use_global_home = True
        mock_area.use_global_sleep = True
        mock_area.use_global_activity = True
        mock_area.use_global_presence = True
        mock_area.boost_mode_active = False
        mock_area.boost_temp = 23.0
        mock_area.boost_duration = 60
        mock_area.hvac_mode = "heat"
        mock_area.hysteresis_override = None
        mock_area.manual_override = False
        mock_area.hidden = False
        mock_area.shutdown_switches_when_idle = True
        mock_area.window_sensors = []
        mock_area.presence_sensors = []
        mock_area.night_boost_enabled = True
        mock_area.night_boost_offset = 0.5
        mock_area.night_boost_start_time = "22:00"
        mock_area.night_boost_end_time = "06:00"
        mock_area.smart_night_boost_enabled = False
        mock_area.smart_night_boost_target_time = "06:00"
        mock_area.weather_entity_id = None
        mock_area.get_effective_target_temperature.return_value = 21.0
        
        coordinator.area_manager.get_all_areas.return_value = {
            TEST_AREA_ID: mock_area
        }

        await coordinator.async_request_refresh()

        assert coordinator.data["areas"][TEST_AREA_ID]["current_temperature"] == 20.0

    async def test_update_area_target_temperature(
        self, coordinator: SmartHeatingCoordinator
    ):
        """Test updating area target temperature."""
        mock_area = MagicMock()
        mock_area.area_id = TEST_AREA_ID
        mock_area.name = "Living Room"
        mock_area.enabled = True
        mock_area.state = "heat"
        mock_area.target_temperature = 22.0
        mock_area.current_temperature = 20.0
        mock_area.devices = {}
        mock_area.schedules = {}
        mock_area.preset_mode = "comfort"
        mock_area.away_temp = 16.0
        mock_area.eco_temp = 18.0
        mock_area.comfort_temp = 21.0
        mock_area.home_temp = 20.0
        mock_area.sleep_temp = 17.0
        mock_area.activity_temp = 22.0
        mock_area.use_global_away = True
        mock_area.use_global_eco = True
        mock_area.use_global_comfort = True
        mock_area.use_global_home = True
        mock_area.use_global_sleep = True
        mock_area.use_global_activity = True
        mock_area.use_global_presence = True
        mock_area.boost_mode_active = False
        mock_area.boost_temp = 23.0
        mock_area.boost_duration = 60
        mock_area.hvac_mode = "heat"
        mock_area.hysteresis_override = None
        mock_area.manual_override = False
        mock_area.hidden = False
        mock_area.shutdown_switches_when_idle = True
        mock_area.window_sensors = []
        mock_area.presence_sensors = []
        mock_area.night_boost_enabled = True
        mock_area.night_boost_offset = 0.5
        mock_area.night_boost_start_time = "22:00"
        mock_area.night_boost_end_time = "06:00"
        mock_area.smart_night_boost_enabled = False
        mock_area.smart_night_boost_target_time = "06:00"
        mock_area.weather_entity_id = None
        mock_area.get_effective_target_temperature.return_value = 22.0
        
        coordinator.area_manager.get_all_areas.return_value = {
            TEST_AREA_ID: mock_area
        }

        await coordinator.async_request_refresh()

        assert coordinator.data["areas"][TEST_AREA_ID]["target_temperature"] == 22.0

    async def test_update_area_enabled_state(
        self, coordinator: SmartHeatingCoordinator
    ):
        """Test updating area enabled state."""
        mock_area = MagicMock()
        mock_area.area_id = TEST_AREA_ID
        mock_area.name = "Living Room"
        mock_area.enabled = False
        mock_area.state = "heat"
        mock_area.target_temperature = 21.0
        mock_area.current_temperature = 20.0
        mock_area.devices = {}
        mock_area.schedules = {}
        mock_area.preset_mode = "comfort"
        mock_area.away_temp = 16.0
        mock_area.eco_temp = 18.0
        mock_area.comfort_temp = 21.0
        mock_area.home_temp = 20.0
        mock_area.sleep_temp = 17.0
        mock_area.activity_temp = 22.0
        mock_area.use_global_away = True
        mock_area.use_global_eco = True
        mock_area.use_global_comfort = True
        mock_area.use_global_home = True
        mock_area.use_global_sleep = True
        mock_area.use_global_activity = True
        mock_area.use_global_presence = True
        mock_area.boost_mode_active = False
        mock_area.boost_temp = 23.0
        mock_area.boost_duration = 60
        mock_area.hvac_mode = "heat"
        mock_area.hysteresis_override = None
        mock_area.manual_override = False
        mock_area.hidden = False
        mock_area.shutdown_switches_when_idle = True
        mock_area.window_sensors = []
        mock_area.presence_sensors = []
        mock_area.night_boost_enabled = True
        mock_area.night_boost_offset = 0.5
        mock_area.night_boost_start_time = "22:00"
        mock_area.night_boost_end_time = "06:00"
        mock_area.smart_night_boost_enabled = False
        mock_area.smart_night_boost_target_time = "06:00"
        mock_area.weather_entity_id = None
        mock_area.get_effective_target_temperature.return_value = 21.0
        
        coordinator.area_manager.get_all_areas.return_value = {
            TEST_AREA_ID: mock_area
        }

        await coordinator.async_request_refresh()

        assert coordinator.data["areas"][TEST_AREA_ID]["enabled"] is False


class TestDebounceTemperatureChange:
    """Test debounced temperature change handling."""

    async def test_handle_temperature_change_debounce(
        self, coordinator: SmartHeatingCoordinator, hass: HomeAssistant
    ):
        """Test temperature change creates debounce task."""
        old_state = State("climate.test", "heat", {"temperature": 20.0})
        new_state = State("climate.test", "heat", {"temperature": 21.0})
        
        with patch.object(coordinator, '_apply_manual_temperature_change') as mock_apply:
            coordinator._handle_temperature_change("climate.test", old_state, new_state)
            
            # Should create debounce task
            assert "climate.test" in coordinator._debounce_tasks

    async def test_apply_manual_temperature_change_matches_expected(
        self, coordinator: SmartHeatingCoordinator
    ):
        """Test manual temperature change when it matches expected temperature."""
        mock_area = MagicMock()
        mock_area.name = "Living Room"
        mock_area.devices = {"climate.test": {}}
        mock_area.get_effective_target_temperature.return_value = 21.0
        mock_area.target_temperature = 21.0
        mock_area.manual_override = False  # Set initial value
        
        coordinator.area_manager.get_all_areas.return_value = {
            TEST_AREA_ID: mock_area
        }
        
        # Temperature matches expected - should not set manual override
        await coordinator._apply_manual_temperature_change("climate.test", 21.0)
        
        # manual_override should remain False since temp matches
        assert mock_area.manual_override is False

    async def test_apply_manual_temperature_change_different_from_expected(
        self, coordinator: SmartHeatingCoordinator
    ):
        """Test manual temperature change when it differs from expected."""
        mock_area = MagicMock()
        mock_area.name = "Living Room"
        mock_area.devices = {"climate.test": {}}
        mock_area.get_effective_target_temperature.return_value = 21.0
        mock_area.target_temperature = 21.0
        mock_area.manual_override = False
        
        coordinator.area_manager.get_all_areas.return_value = {
            TEST_AREA_ID: mock_area
        }
        coordinator.area_manager.async_save = AsyncMock()
        
        # Temperature differs - should set manual override
        await coordinator._apply_manual_temperature_change("climate.test", 23.0)
        
        assert mock_area.target_temperature == 23.0
        assert mock_area.manual_override is True
        coordinator.area_manager.async_save.assert_called_once()


class TestTemperatureSensorConversion:
    """Test temperature sensor data extraction and conversion."""

    def test_get_temperature_from_sensor_celsius(self, coordinator: SmartHeatingCoordinator):
        """Test getting temperature from Celsius sensor."""
        state = State("sensor.temp", "20.5", {"unit_of_measurement": "°C"})
        
        result = coordinator._get_temperature_from_sensor("sensor.temp", state)
        
        assert result == 20.5

    def test_get_temperature_from_sensor_fahrenheit(self, coordinator: SmartHeatingCoordinator):
        """Test getting temperature from Fahrenheit sensor."""
        state = State("sensor.temp", "68.0", {"unit_of_measurement": "°F"})
        
        result = coordinator._get_temperature_from_sensor("sensor.temp", state)
        
        assert result is not None
        assert abs(result - 20.0) < 0.1  # 68°F ≈ 20°C

    def test_get_temperature_from_sensor_unavailable(self, coordinator: SmartHeatingCoordinator):
        """Test getting temperature from unavailable sensor."""
        state = State("sensor.temp", "unavailable", {})
        
        result = coordinator._get_temperature_from_sensor("sensor.temp", state)
        
        assert result is None

    def test_get_temperature_from_sensor_unknown(self, coordinator: SmartHeatingCoordinator):
        """Test getting temperature from unknown sensor."""
        state = State("sensor.temp", "unknown", {})
        
        result = coordinator._get_temperature_from_sensor("sensor.temp", state)
        
        assert result is None

    def test_get_temperature_from_sensor_invalid(self, coordinator: SmartHeatingCoordinator):
        """Test getting temperature from sensor with invalid value."""
        state = State("sensor.temp", "invalid", {})
        
        result = coordinator._get_temperature_from_sensor("sensor.temp", state)
        
        assert result is None


class TestValvePosition:
    """Test valve position extraction."""

    def test_get_valve_position_valid(self, coordinator: SmartHeatingCoordinator):
        """Test getting valid valve position."""
        state = State("number.valve", "50.0", {})
        
        result = coordinator._get_valve_position(state)
        
        assert result == 50.0

    def test_get_valve_position_unavailable(self, coordinator: SmartHeatingCoordinator):
        """Test getting valve position when unavailable."""
        state = State("number.valve", "unavailable", {})
        
        result = coordinator._get_valve_position(state)
        
        assert result is None

    def test_get_valve_position_unknown(self, coordinator: SmartHeatingCoordinator):
        """Test getting valve position when unknown."""
        state = State("number.valve", "unknown", {})
        
        result = coordinator._get_valve_position(state)
        
        assert result is None

    def test_get_valve_position_invalid(self, coordinator: SmartHeatingCoordinator):
        """Test getting valve position with invalid value."""
        state = State("number.valve", "invalid", {})
        
        result = coordinator._get_valve_position(state)
        
        assert result is None


class TestGetDeviceStateData:
    """Test device state data extraction."""

    def test_get_device_state_data_temperature_sensor(self, coordinator: SmartHeatingCoordinator, hass: HomeAssistant):
        """Test getting state data for temperature sensor."""
        device_id = "sensor.living_room_temp"
        device_info = {"type": "temperature_sensor"}
        
        # Set state using hass.states.async_set
        hass.states.async_set(
            device_id, "22.5",
            {"friendly_name": "Living Room Temperature", "unit_of_measurement": "°C"}
        )
        
        result = coordinator._get_device_state_data(device_id, device_info)
        
        assert result["id"] == device_id
        assert result["type"] == "temperature_sensor"
        assert result["state"] == "22.5"
        assert result["name"] == "Living Room Temperature"
        assert result["temperature"] == 22.5

    def test_get_device_state_data_valve(self, coordinator: SmartHeatingCoordinator, hass: HomeAssistant):
        """Test getting state data for valve."""
        device_id = "number.valve_position"
        device_info = {"type": "valve"}
        
        hass.states.async_set(
            device_id, "75.0",
            {"friendly_name": "Valve Position"}
        )
        
        result = coordinator._get_device_state_data(device_id, device_info)
        
        assert result["id"] == device_id
        assert result["type"] == "valve"
        assert result["state"] == "75.0"
        assert result["name"] == "Valve Position"
        assert result["position"] == 75.0

    def test_get_device_state_data_thermostat(self, coordinator: SmartHeatingCoordinator, hass: HomeAssistant):
        """Test getting state data for thermostat."""
        device_id = "climate.living_room"
        device_info = {"type": "thermostat"}
        
        hass.states.async_set(
            device_id,
            "heat",
            {
                "friendly_name": "Living Room Thermostat",
                "current_temperature": 20.0,
                "temperature": 21.0,
                "hvac_action": "heating"
            }
        )
        
        result = coordinator._get_device_state_data(device_id, device_info)
        
        assert result["id"] == device_id
        assert result["type"] == "thermostat"
        assert result["state"] == "heat"
        assert result["name"] == "Living Room Thermostat"
        assert result["current_temperature"] == 20.0
        assert result["target_temperature"] == 21.0
        assert result["hvac_action"] == "heating"

    def test_get_device_state_data_no_state(self, coordinator: SmartHeatingCoordinator, hass: HomeAssistant):
        """Test getting state data when device has no state."""
        device_id = "sensor.missing"
        device_info = {"type": "temperature_sensor"}
        
        # Don't set any state - device doesn't exist
        
        result = coordinator._get_device_state_data(device_id, device_info)
        
        assert result["id"] == device_id
        assert result["type"] == "temperature_sensor"
        assert result["state"] == "unavailable"
        assert result["name"] == device_id
        # Should not have temperature key since state is None
        assert "temperature" not in result
