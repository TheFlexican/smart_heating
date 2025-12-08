"""Tests for device registry utilities."""

from unittest.mock import MagicMock, Mock, patch
import pytest

from homeassistant.helpers import entity_registry as er

from smart_heating.utils.device_registry import DeviceRegistry, build_device_dict


class TestDeviceRegistry:
    """Tests for DeviceRegistry class."""

    @pytest.fixture
    def mock_hass(self):
        """Create mock Home Assistant instance."""
        hass = MagicMock()
        return hass

    @pytest.fixture
    def device_registry(self, mock_hass):
        """Create DeviceRegistry instance."""
        with patch("smart_heating.utils.device_registry.er.async_get"), \
             patch("smart_heating.utils.device_registry.dr.async_get"), \
             patch("smart_heating.utils.device_registry.ar.async_get"):
            return DeviceRegistry(mock_hass)

    def test_init(self, mock_hass):
        """Test initialization."""
        with patch("smart_heating.utils.device_registry.er.async_get") as mock_er, \
             patch("smart_heating.utils.device_registry.dr.async_get") as mock_dr, \
             patch("smart_heating.utils.device_registry.ar.async_get") as mock_ar:
            
            registry = DeviceRegistry(mock_hass)
            
            assert registry.hass == mock_hass
            mock_er.assert_called_once_with(mock_hass)
            mock_dr.assert_called_once_with(mock_hass)
            mock_ar.assert_called_once_with(mock_hass)

    def test_get_device_type_climate(self, device_registry):
        """Test getting device type for climate entity."""
        entity = MagicMock(spec=er.RegistryEntry)
        entity.domain = "climate"
        
        state = Mock()
        state.attributes = {}
        
        result = device_registry.get_device_type(entity, state)
        assert result == ("thermostat", "climate")

    def test_get_device_type_switch(self, device_registry):
        """Test getting device type for switch entity."""
        entity = MagicMock(spec=er.RegistryEntry)
        entity.domain = "switch"
        
        state = Mock()
        state.attributes = {}
        
        result = device_registry.get_device_type(entity, state)
        assert result == ("switch", "switch")

    def test_get_device_type_number(self, device_registry):
        """Test getting device type for number entity."""
        entity = MagicMock(spec=er.RegistryEntry)
        entity.domain = "number"
        
        state = Mock()
        state.attributes = {}
        
        result = device_registry.get_device_type(entity, state)
        assert result == ("number", "number")

    def test_get_device_type_temperature_sensor_by_class(self, device_registry):
        """Test getting device type for temperature sensor by device class."""
        entity = MagicMock(spec=er.RegistryEntry)
        entity.domain = "sensor"
        
        state = Mock()
        state.attributes = {"device_class": "temperature"}
        
        result = device_registry.get_device_type(entity, state)
        assert result == ("sensor", "temperature")

    def test_get_device_type_temperature_sensor_by_unit(self, device_registry):
        """Test getting device type for temperature sensor by unit."""
        entity = MagicMock(spec=er.RegistryEntry)
        entity.domain = "sensor"
        
        state = Mock()
        state.attributes = {"unit_of_measurement": "°C"}
        
        result = device_registry.get_device_type(entity, state)
        assert result == ("sensor", "temperature")

    def test_get_device_type_non_temperature_sensor(self, device_registry):
        """Test getting device type for non-temperature sensor."""
        entity = MagicMock(spec=er.RegistryEntry)
        entity.domain = "sensor"
        
        state = Mock()
        state.attributes = {"device_class": "humidity"}
        
        result = device_registry.get_device_type(entity, state)
        assert result is None

    def test_get_device_type_unsupported_domain(self, device_registry):
        """Test getting device type for unsupported domain."""
        entity = MagicMock(spec=er.RegistryEntry)
        entity.domain = "light"
        
        state = Mock()
        state.attributes = {}
        
        result = device_registry.get_device_type(entity, state)
        assert result is None

    def test_get_ha_area_with_area(self, device_registry):
        """Test getting HA area when entity has area."""
        entity = MagicMock(spec=er.RegistryEntry)
        entity.device_id = "device123"
        
        # Mock device entry with area
        device_entry = Mock()
        device_entry.area_id = "area123"
        device_registry._device_registry.async_get.return_value = device_entry
        
        # Mock area entry
        area_entry = Mock()
        area_entry.id = "area123"
        area_entry.name = "Living Room"
        device_registry._area_registry.async_get_area.return_value = area_entry
        
        result = device_registry.get_ha_area(entity)
        assert result == ("area123", "Living Room")

    def test_get_ha_area_no_device_id(self, device_registry):
        """Test getting HA area when entity has no device ID."""
        entity = MagicMock(spec=er.RegistryEntry)
        entity.device_id = None
        
        result = device_registry.get_ha_area(entity)
        assert result is None

    def test_get_ha_area_no_device_entry(self, device_registry):
        """Test getting HA area when device not found."""
        entity = MagicMock(spec=er.RegistryEntry)
        entity.device_id = "device123"
        
        device_registry._device_registry.async_get.return_value = None
        
        result = device_registry.get_ha_area(entity)
        assert result is None

    def test_get_ha_area_no_area_id(self, device_registry):
        """Test getting HA area when device has no area ID."""
        entity = MagicMock(spec=er.RegistryEntry)
        entity.device_id = "device123"
        
        device_entry = Mock()
        device_entry.area_id = None
        device_registry._device_registry.async_get.return_value = device_entry
        
        result = device_registry.get_ha_area(entity)
        assert result is None

    def test_get_ha_area_no_area_entry(self, device_registry):
        """Test getting HA area when area not found."""
        entity = MagicMock(spec=er.RegistryEntry)
        entity.device_id = "device123"
        
        device_entry = Mock()
        device_entry.area_id = "area123"
        device_registry._device_registry.async_get.return_value = device_entry
        
        device_registry._area_registry.async_get_area.return_value = None
        
        result = device_registry.get_ha_area(entity)
        assert result is None

    def test_should_filter_device_entity_id_match(self, device_registry):
        """Test filtering device by entity ID match."""
        hidden_areas = [{"id": "hidden", "name": "Garage"}]
        
        result = device_registry.should_filter_device(
            "climate.garage_thermostat",
            "Garage Thermostat",
            None,
            hidden_areas
        )
        assert result is True

    def test_should_filter_device_friendly_name_match(self, device_registry):
        """Test filtering device by friendly name match."""
        hidden_areas = [{"id": "hidden", "name": "Garage"}]
        
        result = device_registry.should_filter_device(
            "climate.device1",
            "My Garage Heater",
            None,
            hidden_areas
        )
        assert result is True

    def test_should_filter_device_ha_area_match(self, device_registry):
        """Test filtering device by HA area match."""
        hidden_areas = [{"id": "hidden", "name": "Garage"}]
        
        result = device_registry.should_filter_device(
            "climate.device1",
            "Thermostat",
            "Garage",
            hidden_areas
        )
        assert result is True

    def test_should_filter_device_no_match(self, device_registry):
        """Test not filtering device when no match."""
        hidden_areas = [{"id": "hidden", "name": "Garage"}]
        
        result = device_registry.should_filter_device(
            "climate.living_room",
            "Living Room Thermostat",
            "Living Room",
            hidden_areas
        )
        assert result is False

    def test_should_filter_device_case_insensitive(self, device_registry):
        """Test filtering is case insensitive."""
        hidden_areas = [{"id": "hidden", "name": "Garage"}]
        
        result = device_registry.should_filter_device(
            "climate.GARAGE_device",
            "My Thermostat",
            None,
            hidden_areas
        )
        assert result is True


class TestBuildDeviceDict:
    """Tests for build_device_dict function."""

    def test_build_device_dict_with_area(self):
        """Test building device dict with HA area."""
        entity = MagicMock(spec=er.RegistryEntry)
        entity.entity_id = "climate.living_room"
        entity.domain = "climate"
        
        state = Mock()
        state.state = "heat"
        state.attributes = {
            "friendly_name": "Living Room Thermostat",
            "temperature": 21.0,
            "current_temperature": 20.5,
            "unit_of_measurement": "°C"
        }
        
        result = build_device_dict(
            entity,
            state,
            "thermostat",
            "climate",
            ("area123", "Living Room"),
            ["zone1"]
        )
        
        assert result["id"] == "climate.living_room"
        assert result["name"] == "Living Room Thermostat"
        assert result["type"] == "thermostat"
        assert result["subtype"] == "climate"
        assert result["entity_id"] == "climate.living_room"
        assert result["domain"] == "climate"
        assert result["assigned_areas"] == ["zone1"]
        assert result["ha_area_id"] == "area123"
        assert result["ha_area_name"] == "Living Room"
        assert result["state"] == "heat"
        assert result["attributes"]["temperature"] == 21.0
        assert result["attributes"]["current_temperature"] == 20.5
        assert result["attributes"]["unit_of_measurement"] == "°C"

    def test_build_device_dict_no_area(self):
        """Test building device dict without HA area."""
        entity = MagicMock(spec=er.RegistryEntry)
        entity.entity_id = "climate.portable"
        entity.domain = "climate"
        
        state = Mock()
        state.state = "off"
        state.attributes = {"friendly_name": "Portable Heater"}
        
        result = build_device_dict(
            entity,
            state,
            "thermostat",
            "climate",
            None,
            []
        )
        
        assert result["ha_area_id"] is None
        assert result["ha_area_name"] is None
        assert result["assigned_areas"] == []

    def test_build_device_dict_fallback_name(self):
        """Test building device dict with fallback name."""
        entity = MagicMock(spec=er.RegistryEntry)
        entity.entity_id = "climate.device1"
        entity.domain = "climate"
        
        state = Mock()
        state.state = "off"
        state.attributes = {}  # No friendly_name
        
        result = build_device_dict(
            entity,
            state,
            "thermostat",
            "climate",
            None,
            []
        )
        
        assert result["name"] == "climate.device1"
