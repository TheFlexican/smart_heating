"""Tests for Safety Monitor.

Tests safety sensor monitoring, emergency shutdown, state changes, and alerts.
"""

from unittest.mock import AsyncMock, MagicMock, patch, call

import pytest
from homeassistant.core import HomeAssistant, Event, State

from smart_heating.safety_monitor import SafetyMonitor
from smart_heating.const import DOMAIN

from tests.unit.const import TEST_AREA_ID


@pytest.fixture
def safety_monitor(hass: HomeAssistant, mock_area_manager) -> SafetyMonitor:
    """Create a SafetyMonitor instance."""
    return SafetyMonitor(hass, mock_area_manager)


@pytest.fixture
def mock_area():
    """Create a mock area."""
    area = MagicMock()
    area.area_id = TEST_AREA_ID
    area.name = "Living Room"
    area.enabled = True
    return area


class TestInitialization:
    """Tests for initialization."""

    def test_init(self, safety_monitor: SafetyMonitor, hass: HomeAssistant, mock_area_manager):
        """Test safety monitor initialization."""
        assert safety_monitor.hass == hass
        assert safety_monitor.area_manager == mock_area_manager
        assert safety_monitor._state_unsub is None
        assert safety_monitor._emergency_shutdown_active is False

    async def test_async_setup_no_sensors(self, safety_monitor: SafetyMonitor, mock_area_manager):
        """Test setup with no safety sensors."""
        mock_area_manager.get_safety_sensors.return_value = []
        
        await safety_monitor.async_setup()
        
        assert safety_monitor._state_unsub is None

    async def test_async_setup_with_sensors(self, safety_monitor: SafetyMonitor, mock_area_manager, hass: HomeAssistant):
        """Test setup with safety sensors."""
        mock_area_manager.get_safety_sensors.return_value = [
            {"sensor_id": "binary_sensor.smoke_detector", "enabled": True}
        ]
        mock_area_manager.check_safety_sensor_status.return_value = (False, None)
        
        # Mock the sensor state
        hass.states.async_set("binary_sensor.smoke_detector", "off")
        
        with patch("smart_heating.safety_monitor.async_track_state_change_event") as mock_track:
            mock_track.return_value = MagicMock()
            await safety_monitor.async_setup()
        
        mock_track.assert_called_once()
        assert safety_monitor._state_unsub is not None

    async def test_async_setup_disabled_sensors(self, safety_monitor: SafetyMonitor, mock_area_manager):
        """Test setup with only disabled sensors."""
        mock_area_manager.get_safety_sensors.return_value = [
            {"sensor_id": "binary_sensor.smoke_detector", "enabled": False}
        ]
        
        await safety_monitor.async_setup()
        
        # Should not set up listeners for disabled sensors
        assert safety_monitor._state_unsub is None
    
    async def test_async_setup_replaces_existing_listener(self, safety_monitor: SafetyMonitor, mock_area_manager, hass: HomeAssistant):
        """Test that setup removes existing listener before creating new one."""
        mock_area_manager.get_safety_sensors.return_value = [
            {"sensor_id": "binary_sensor.smoke", "enabled": True}
        ]
        mock_area_manager.check_safety_sensor_status.return_value = (False, None)
        
        # Create mock unsubscribe function
        mock_unsub = MagicMock()
        safety_monitor._state_unsub = mock_unsub
        
        hass.states.async_set("binary_sensor.smoke", "off")
        
        with patch("smart_heating.safety_monitor.async_track_state_change_event") as mock_track:
            mock_track.return_value = MagicMock()
            await safety_monitor.async_setup()
        
        # Should call existing unsubscribe
        mock_unsub.assert_called_once()
    
    async def test_async_setup_sensor_does_not_exist(self, safety_monitor: SafetyMonitor, mock_area_manager, hass: HomeAssistant):
        """Test setup when sensor doesn't exist yet."""
        mock_area_manager.get_safety_sensors.return_value = [
            {"sensor_id": "binary_sensor.nonexistent", "enabled": True}
        ]
        mock_area_manager.check_safety_sensor_status.return_value = (False, None)
        
        # Don't create the sensor state
        # hass.states.get will return None
        
        with patch("smart_heating.safety_monitor.async_track_state_change_event") as mock_track:
            mock_track.return_value = MagicMock()
            await safety_monitor.async_setup()
        
        # Should still set up listener (sensor might come later)
        mock_track.assert_called_once()
        assert safety_monitor._state_unsub is not None


class TestStateChangeHandling:
    """Tests for state change handling."""

    async def test_handle_safety_sensor_state_change(self, safety_monitor: SafetyMonitor, hass: HomeAssistant, mock_area_manager):
        """Test handling safety sensor state change."""
        # Mock the check status
        mock_area_manager.check_safety_sensor_status.return_value = (False, None)
        
        # Create state change event
        old_state = State("binary_sensor.smoke", "off")
        new_state = State("binary_sensor.smoke", "on")
        
        event = Event(
            "state_changed",
            {
                "entity_id": "binary_sensor.smoke",
                "old_state": old_state,
                "new_state": new_state
            }
        )
        
        with patch.object(hass, 'async_create_task') as mock_task:
            safety_monitor._handle_safety_sensor_state_change(event)
        
        # Should schedule safety check
        mock_task.assert_called_once()

    async def test_handle_safety_sensor_state_change_no_new_state(self, safety_monitor: SafetyMonitor):
        """Test handling state change with no new state."""
        event = Event(
            "state_changed",
            {
                "entity_id": "binary_sensor.smoke",
                "old_state": None,
                "new_state": None
            }
        )
        
        # Should not crash
        safety_monitor._handle_safety_sensor_state_change(event)


class TestSafetyChecks:
    """Tests for safety status checking."""

    async def test_check_safety_status_no_alert(self, safety_monitor: SafetyMonitor, mock_area_manager):
        """Test checking safety status with no alert."""
        mock_area_manager.check_safety_sensor_status.return_value = (False, None)
        
        await safety_monitor._check_safety_status()
        
        # Should not trigger shutdown
        assert safety_monitor._emergency_shutdown_active is False

    async def test_check_safety_status_alert_detected(self, safety_monitor: SafetyMonitor, mock_area_manager, mock_area, hass: HomeAssistant):
        """Test checking safety status when alert is detected."""
        mock_area_manager.check_safety_sensor_status.return_value = (True, "binary_sensor.smoke")
        mock_area_manager.get_all_areas.return_value = {TEST_AREA_ID: mock_area}
        
        # Mock the emergency shutdown method to avoid complex internal calls
        with patch.object(safety_monitor, '_trigger_emergency_shutdown', new_callable=AsyncMock) as mock_shutdown:
            await safety_monitor._check_safety_status()
        
        # Should trigger emergency shutdown
        mock_shutdown.assert_called_once_with("binary_sensor.smoke")

    async def test_check_safety_status_alert_cleared(self, safety_monitor: SafetyMonitor, mock_area_manager):
        """Test checking safety status when alert is cleared."""
        # Set emergency shutdown as active
        safety_monitor._emergency_shutdown_active = True
        
        # Alert cleared
        mock_area_manager.check_safety_sensor_status.return_value = (False, None)
        
        await safety_monitor._check_safety_status()
        
        # Should keep shutdown active (manual intervention required)
        assert safety_monitor._emergency_shutdown_active is True


class TestEmergencyShutdown:
    """Tests for emergency shutdown functionality."""
    
    async def test_trigger_emergency_shutdown_disables_all_areas(
        self, safety_monitor: SafetyMonitor, mock_area_manager, hass: HomeAssistant
    ):
        """Test that emergency shutdown disables all enabled areas."""
        # Create mock areas
        area1 = MagicMock()
        area1.name = "Living Room"
        area1.enabled = True
        
        area2 = MagicMock()
        area2.name = "Bedroom"
        area2.enabled = True
        
        area3 = MagicMock()
        area3.name = "Kitchen"
        area3.enabled = False  # Already disabled
        
        mock_area_manager.get_all_areas.return_value = {
            "living_room": area1,
            "bedroom": area2,
            "kitchen": area3
        }
        
        # Initialize hass.data for DOMAIN
        hass.data[DOMAIN] = {}
        
        await safety_monitor._trigger_emergency_shutdown("binary_sensor.smoke")
        
        # Should disable enabled areas
        assert area1.enabled is False
        assert area2.enabled is False
        assert area3.enabled is False  # Remains disabled
        
        # Should save configuration
        mock_area_manager.async_save.assert_called_once()
        
        # Should set safety alert active
        mock_area_manager.set_safety_alert_active.assert_called_once_with(True)
        
        # Should mark emergency shutdown as active
        assert safety_monitor._emergency_shutdown_active is True
    
    async def test_trigger_emergency_shutdown_no_enabled_areas(
        self, safety_monitor: SafetyMonitor, mock_area_manager, hass: HomeAssistant
    ):
        """Test emergency shutdown when all areas already disabled."""
        area1 = MagicMock()
        area1.name = "Living Room"
        area1.enabled = False
        
        mock_area_manager.get_all_areas.return_value = {"living_room": area1}
        hass.data[DOMAIN] = {}
        
        await safety_monitor._trigger_emergency_shutdown("binary_sensor.co")
        
        # Should complete without errors
        assert safety_monitor._emergency_shutdown_active is True
    
    async def test_trigger_emergency_shutdown_requests_coordinator_refresh(
        self, safety_monitor: SafetyMonitor, mock_area_manager, hass: HomeAssistant
    ):
        """Test that emergency shutdown requests coordinator refresh."""
        mock_area_manager.get_all_areas.return_value = {}
        
        # Mock coordinator in hass.data
        mock_coordinator = MagicMock()
        mock_coordinator.async_request_refresh = AsyncMock()
        hass.data[DOMAIN] = {
            "test_entry_id": mock_coordinator,
            "history": MagicMock(),
            "climate_controller": MagicMock()
        }
        
        await safety_monitor._trigger_emergency_shutdown("binary_sensor.smoke")
        
        # Should request coordinator refresh
        mock_coordinator.async_request_refresh.assert_called_once()
    
    async def test_trigger_emergency_shutdown_no_coordinator(
        self, safety_monitor: SafetyMonitor, mock_area_manager, hass: HomeAssistant
    ):
        """Test emergency shutdown when no coordinator available."""
        mock_area_manager.get_all_areas.return_value = {}
        
        # Only internal services in hass.data
        hass.data[DOMAIN] = {
            "history": MagicMock(),
            "climate_controller": MagicMock(),
            "learning_engine": MagicMock()
        }
        
        # Should not crash
        await safety_monitor._trigger_emergency_shutdown("binary_sensor.smoke")


class TestReconfigure:
    """Tests for reconfiguration."""

    async def test_async_reconfigure(self, safety_monitor: SafetyMonitor, mock_area_manager, hass: HomeAssistant):
        """Test reconfiguring safety monitor."""
        mock_area_manager.get_safety_sensors.return_value = [
            {"sensor_id": "binary_sensor.co", "enabled": True}
        ]
        mock_area_manager.check_safety_sensor_status.return_value = (False, None)
        
        # Mock sensor state
        hass.states.async_set("binary_sensor.co", "off")
        
        with patch("smart_heating.safety_monitor.async_track_state_change_event") as mock_track:
            mock_track.return_value = MagicMock()
            await safety_monitor.async_reconfigure()
        
        # Should set up new listeners
        mock_track.assert_called_once()


class TestShutdown:
    """Tests for shutdown."""

    def test_async_shutdown(self, safety_monitor: SafetyMonitor):
        """Test shutting down safety monitor."""
        mock_unsub = MagicMock()
        safety_monitor._state_unsub = mock_unsub
        
        safety_monitor.async_shutdown()
        
        mock_unsub.assert_called_once()
        assert safety_monitor._state_unsub is None

    def test_async_shutdown_no_listener(self, safety_monitor: SafetyMonitor):
        """Test shutdown with no active listener."""
        safety_monitor.async_shutdown()
        # Should not crash
        assert safety_monitor._state_unsub is None


class TestReset:
    """Tests for reset functionality."""

    def test_reset_emergency_shutdown(self, safety_monitor: SafetyMonitor, mock_area_manager):
        """Test resetting emergency shutdown state."""
        safety_monitor._emergency_shutdown_active = True
        
        safety_monitor.reset_emergency_shutdown()
        
        assert safety_monitor._emergency_shutdown_active is False
        mock_area_manager.set_safety_alert_active.assert_called_once_with(False)