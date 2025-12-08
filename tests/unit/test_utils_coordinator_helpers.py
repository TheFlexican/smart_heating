"""Tests for coordinator helpers utilities."""

from unittest.mock import MagicMock, Mock
import pytest

from smart_heating.utils.coordinator_helpers import (
    get_coordinator,
    get_coordinator_devices,
    safe_coordinator_data,
)


class TestGetCoordinator:
    """Tests for get_coordinator function."""

    def test_get_coordinator_found(self):
        """Test getting coordinator when it exists."""
        hass = MagicMock()
        
        # Create mock coordinator
        coordinator = Mock()
        coordinator.data = {}
        coordinator.async_request_refresh = Mock()
        
        # Add to hass.data
        hass.data = {"smart_heating": {"config_entry_id": coordinator}}
        
        result = get_coordinator(hass)
        assert result == coordinator

    def test_get_coordinator_not_found(self):
        """Test getting coordinator when it doesn't exist."""
        hass = MagicMock()
        hass.data = {"smart_heating": {}}
        
        result = get_coordinator(hass)
        assert result is None

    def test_get_coordinator_empty_domain_data(self):
        """Test getting coordinator with empty domain data."""
        hass = MagicMock()
        hass.data = {}
        
        result = get_coordinator(hass)
        assert result is None

    def test_get_coordinator_wrong_type(self):
        """Test getting coordinator with wrong type object."""
        hass = MagicMock()
        
        # Object without coordinator attributes
        wrong_obj = {"key": "value"}
        hass.data = {"smart_heating": {"config_entry_id": wrong_obj}}
        
        result = get_coordinator(hass)
        assert result is None


class TestGetCoordinatorDevices:
    """Tests for get_coordinator_devices function."""

    def test_get_coordinator_devices_success(self):
        """Test getting devices for an area."""
        hass = MagicMock()
        
        # Create mock coordinator with data
        coordinator = Mock()
        coordinator.data = {
            "areas": {
                "living_room": {
                    "devices": [
                        {"id": "device1", "name": "Device 1"},
                        {"id": "device2", "name": "Device 2"}
                    ]
                }
            }
        }
        coordinator.async_request_refresh = Mock()
        
        hass.data = {"smart_heating": {"config_entry_id": coordinator}}
        
        result = get_coordinator_devices(hass, "living_room")
        
        assert len(result) == 2
        assert result["device1"]["name"] == "Device 1"
        assert result["device2"]["name"] == "Device 2"

    def test_get_coordinator_devices_no_coordinator(self):
        """Test getting devices when coordinator not found."""
        hass = MagicMock()
        hass.data = {}
        
        result = get_coordinator_devices(hass, "living_room")
        assert result == {}

    def test_get_coordinator_devices_no_data(self):
        """Test getting devices when coordinator has no data."""
        hass = MagicMock()
        
        coordinator = Mock()
        coordinator.data = None
        coordinator.async_request_refresh = Mock()
        
        hass.data = {"smart_heating": {"config_entry_id": coordinator}}
        
        result = get_coordinator_devices(hass, "living_room")
        assert result == {}

    def test_get_coordinator_devices_area_not_found(self):
        """Test getting devices for non-existent area."""
        hass = MagicMock()
        
        coordinator = Mock()
        coordinator.data = {
            "areas": {
                "living_room": {
                    "devices": [{"id": "device1"}]
                }
            }
        }
        coordinator.async_request_refresh = Mock()
        
        hass.data = {"smart_heating": {"config_entry_id": coordinator}}
        
        result = get_coordinator_devices(hass, "bedroom")
        assert result == {}

    def test_get_coordinator_devices_no_devices(self):
        """Test getting devices when area has no devices."""
        hass = MagicMock()
        
        coordinator = Mock()
        coordinator.data = {
            "areas": {
                "living_room": {}
            }
        }
        coordinator.async_request_refresh = Mock()
        
        hass.data = {"smart_heating": {"config_entry_id": coordinator}}
        
        result = get_coordinator_devices(hass, "living_room")
        assert result == {}


class TestSafeCoordinatorData:
    """Tests for safe_coordinator_data function."""

    def test_safe_coordinator_data_removes_learning_engine(self):
        """Test that learning_engine is removed."""
        data = {
            "areas": {},
            "global_settings": {},
            "learning_engine": {"some": "data"}
        }
        
        result = safe_coordinator_data(data)
        
        assert "areas" in result
        assert "global_settings" in result
        assert "learning_engine" not in result

    def test_safe_coordinator_data_no_learning_engine(self):
        """Test with data that has no learning_engine."""
        data = {
            "areas": {},
            "global_settings": {}
        }
        
        result = safe_coordinator_data(data)
        
        assert "areas" in result
        assert "global_settings" in result
        assert len(result) == 2

    def test_safe_coordinator_data_empty(self):
        """Test with empty data."""
        data = {}
        
        result = safe_coordinator_data(data)
        
        assert result == {}
