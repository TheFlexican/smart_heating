"""Tests for device API handlers."""

import pytest
from unittest.mock import MagicMock, AsyncMock, patch
from aiohttp import web
import json

from smart_heating.api_handlers.devices import (
    handle_get_devices,
    handle_refresh_devices,
    handle_add_device,
    handle_remove_device,
    _discover_devices,
)
from smart_heating.api_handlers import devices as devices_module


@pytest.fixture
def mock_hass():
    """Create mock Home Assistant instance."""
    hass = MagicMock()
    hass.states = MagicMock()
    return hass


@pytest.fixture
def mock_area_manager():
    """Create mock area manager."""
    manager = MagicMock()
    
    # Mock area
    mock_area = MagicMock()
    mock_area.id = "living_room"
    mock_area.name = "Living Room"
    mock_area.devices = {
        "climate.heater": {"type": "climate"},
        "switch.pump": {"type": "switch"}
    }
    
    manager.get_area.return_value = mock_area
    manager.get_all_areas.return_value = {"living_room": mock_area}
    manager.areas = {"living_room": mock_area}
    manager.async_save = AsyncMock()
    
    return manager


@pytest.fixture
def mock_entity_registry():
    """Create mock entity registry."""
    registry = MagicMock()
    
    # Mock climate entity
    climate_entry = MagicMock()
    climate_entry.entity_id = "climate.heater"
    climate_entry.domain = "climate"
    climate_entry.device_id = "device_123"
    climate_entry.original_name = "Heater"
    
    # Mock switch entity
    switch_entry = MagicMock()
    switch_entry.entity_id = "switch.pump"
    switch_entry.domain = "switch"
    switch_entry.device_id = "device_456"
    switch_entry.original_name = "Pump"
    
    registry.entities = MagicMock()
    registry.entities.values.return_value = [climate_entry, switch_entry]
    
    return registry


@pytest.fixture
def mock_device_registry():
    """Create mock device registry."""
    registry = MagicMock()
    
    # Mock device for climate
    climate_device = MagicMock()
    climate_device.name_by_user = None
    climate_device.name = "Smart Heater"
    climate_device.area_id = "living_room"
    
    # Mock device for switch
    switch_device = MagicMock()
    switch_device.name_by_user = None
    switch_device.name = "Circulation Pump"
    switch_device.area_id = "living_room"
    
    def async_get_device(device_id):
        if device_id == "device_123":
            return climate_device
        elif device_id == "device_456":
            return switch_device
        return None
    
    registry.async_get.side_effect = async_get_device
    
    return registry


@pytest.fixture
def mock_area_registry():
    """Create mock area registry."""
    registry = MagicMock()
    
    mock_ha_area = MagicMock()
    mock_ha_area.id = "living_room"
    mock_ha_area.name = "Living Room"
    
    registry.async_get_area.return_value = mock_ha_area
    
    return registry


@pytest.fixture(autouse=True)
def clear_device_cache():
    """Clear device cache before each test."""
    devices_module._devices_cache = None
    devices_module._cache_timestamp = None
    yield
    devices_module._devices_cache = None
    devices_module._cache_timestamp = None


class TestDeviceHandlers:
    """Test device API handlers."""

    @pytest.mark.asyncio
    async def test_handle_get_devices_with_cache(self, mock_hass, mock_area_manager):
        """Test getting devices when cache exists."""
        # Set up cache
        devices_module._devices_cache = [
            {"id": "climate.heater", "name": "Heater", "type": "climate"}
        ]
        
        response = await handle_get_devices(mock_hass, mock_area_manager)
        
        assert response.status == 200
        body = json.loads(response.body.decode())
        assert "devices" in body
        assert len(body["devices"]) == 1
        assert body["devices"][0]["id"] == "climate.heater"

    @pytest.mark.asyncio
    async def test_handle_get_devices_without_cache(
        self, mock_hass, mock_area_manager, mock_entity_registry,
        mock_device_registry, mock_area_registry
    ):
        """Test getting devices performs discovery when no cache."""
        # Mock states
        climate_state = MagicMock()
        climate_state.state = "heating"
        climate_state.attributes = {"current_temperature": 20.5}
        
        switch_state = MagicMock()
        switch_state.state = "on"
        
        def get_state(entity_id):
            if entity_id == "climate.heater":
                return climate_state
            elif entity_id == "switch.pump":
                return switch_state
            return None
        
        mock_hass.states.get.side_effect = get_state
        
        with patch("smart_heating.api_handlers.devices.er.async_get", return_value=mock_entity_registry), \
             patch("smart_heating.api_handlers.devices.dr.async_get", return_value=mock_device_registry), \
             patch("smart_heating.api_handlers.devices.ar.async_get", return_value=mock_area_registry):
            
            response = await handle_get_devices(mock_hass, mock_area_manager)
            
            assert response.status == 200
            body = json.loads(response.body.decode())
            assert "devices" in body
            assert len(body["devices"]) == 2
            
            # Check climate device
            climate_dev = next(d for d in body["devices"] if d["id"] == "climate.heater")
            assert climate_dev["type"] == "climate"
            assert climate_dev["name"] == "Smart Heater"
            assert climate_dev["current_temperature"] == 20.5
            
            # Check switch device
            switch_dev = next(d for d in body["devices"] if d["id"] == "switch.pump")
            assert switch_dev["type"] == "switch"
            assert switch_dev["state"] == "on"

    @pytest.mark.asyncio
    async def test_discover_devices(
        self, mock_hass, mock_area_manager, mock_entity_registry,
        mock_device_registry, mock_area_registry
    ):
        """Test device discovery."""
        # Mock states
        climate_state = MagicMock()
        climate_state.state = "idle"
        climate_state.attributes = {"current_temperature": 21.0}
        
        mock_hass.states.get.return_value = climate_state
        
        with patch("smart_heating.api_handlers.devices.er.async_get", return_value=mock_entity_registry), \
             patch("smart_heating.api_handlers.devices.dr.async_get", return_value=mock_device_registry), \
             patch("smart_heating.api_handlers.devices.ar.async_get", return_value=mock_area_registry):
            
            response = await _discover_devices(mock_hass, mock_area_manager)
            
            assert response.status == 200
            body = json.loads(response.body.decode())
            assert len(body["devices"]) == 2
            
            # Verify cache was set
            assert devices_module._devices_cache is not None
            assert len(devices_module._devices_cache) == 2

    @pytest.mark.asyncio
    async def test_handle_refresh_devices(
        self, mock_hass, mock_area_manager, mock_entity_registry,
        mock_device_registry, mock_area_registry
    ):
        """Test refreshing device list."""
        # Set up initial cache
        devices_module._devices_cache = [{"id": "old_device"}]
        
        # Mock states
        mock_state = MagicMock()
        mock_state.state = "on"
        mock_state.attributes = {}
        mock_hass.states.get.return_value = mock_state
        
        with patch("smart_heating.api_handlers.devices.er.async_get", return_value=mock_entity_registry), \
             patch("smart_heating.api_handlers.devices.dr.async_get", return_value=mock_device_registry), \
             patch("smart_heating.api_handlers.devices.ar.async_get", return_value=mock_area_registry):
            
            response = await handle_refresh_devices(mock_hass, mock_area_manager)
            
            assert response.status == 200
            body = json.loads(response.body.decode())
            assert body["success"] == True
            assert "available" in body
            assert body["available"] == 2  # Two devices discovered

    @pytest.mark.asyncio
    async def test_handle_refresh_devices_error(self, mock_hass, mock_area_manager):
        """Test refreshing devices with error."""
        with patch("smart_heating.api_handlers.devices._discover_devices", side_effect=Exception("Discovery failed")):
            response = await handle_refresh_devices(mock_hass, mock_area_manager)
            
            assert response.status == 500
            body = json.loads(response.body.decode())
            assert "error" in body

    @pytest.mark.asyncio
    async def test_handle_add_device_success(self, mock_hass, mock_area_manager):
        """Test adding a device to area."""
        data = {
            "device_id": "climate.new_heater",
            "device_type": "climate"
        }
        
        response = await handle_add_device(mock_hass, mock_area_manager, "living_room", data)
        
        assert response.status == 200
        body = json.loads(response.body.decode())
        assert body["success"] == True
        
        mock_area_manager.add_device_to_area.assert_called_once_with(
            "living_room", "climate.new_heater", "climate", None
        )
        mock_area_manager.async_save.assert_called_once()

    @pytest.mark.asyncio
    async def test_handle_add_device_with_mqtt(self, mock_hass, mock_area_manager):
        """Test adding device with MQTT topic."""
        data = {
            "device_id": "climate.mqtt_heater",
            "device_type": "climate",
            "mqtt_topic": "heating/control"
        }
        
        response = await handle_add_device(mock_hass, mock_area_manager, "living_room", data)
        
        assert response.status == 200
        mock_area_manager.add_device_to_area.assert_called_once_with(
            "living_room", "climate.mqtt_heater", "climate", "heating/control"
        )

    @pytest.mark.asyncio
    async def test_handle_add_device_missing_params(self, mock_hass, mock_area_manager):
        """Test adding device without required parameters."""
        data = {"device_id": "climate.heater"}  # Missing device_type
        
        response = await handle_add_device(mock_hass, mock_area_manager, "living_room", data)
        
        assert response.status == 400
        body = json.loads(response.body.decode())
        assert "error" in body

    @pytest.mark.asyncio
    async def test_handle_add_device_area_not_found(self, mock_hass, mock_area_registry):
        """Test adding device to non-existent area that's not in HA."""
        area_manager = MagicMock()
        area_manager.get_area.return_value = None
        
        # Mock area registry to return None (area doesn't exist in HA)
        mock_area_registry.async_get_area.return_value = None
        
        data = {
            "device_id": "climate.heater",
            "device_type": "climate"
        }
        
        with patch("smart_heating.api_handlers.devices.ar.async_get", return_value=mock_area_registry):
            response = await handle_add_device(mock_hass, area_manager, "nonexistent", data)
            
            assert response.status == 404
            body = json.loads(response.body.decode())
            assert "error" in body

    @pytest.mark.asyncio
    async def test_handle_add_device_creates_area(self, mock_hass, mock_area_registry):
        """Test adding device auto-creates area if it exists in HA."""
        area_manager = MagicMock()
        area_manager.get_area.return_value = None  # Area doesn't exist in storage
        area_manager.areas = {}
        area_manager.async_save = AsyncMock()
        
        data = {
            "device_id": "climate.heater",
            "device_type": "climate"
        }
        
        with patch("smart_heating.api_handlers.devices.ar.async_get", return_value=mock_area_registry), \
             patch("smart_heating.api_handlers.devices.Area") as mock_area_class:
            
            mock_new_area = MagicMock()
            mock_area_class.return_value = mock_new_area
            
            response = await handle_add_device(mock_hass, area_manager, "living_room", data)
            
            assert response.status == 200
            # Verify area was created
            mock_area_class.assert_called_once_with("living_room", "Living Room")
            assert "living_room" in area_manager.areas

    @pytest.mark.asyncio
    async def test_handle_add_device_value_error(self, mock_hass, mock_area_manager):
        """Test adding device with ValueError."""
        mock_area_manager.add_device_to_area.side_effect = ValueError("Device already exists")
        
        data = {
            "device_id": "climate.heater",
            "device_type": "climate"
        }
        
        response = await handle_add_device(mock_hass, mock_area_manager, "living_room", data)
        
        assert response.status == 400
        body = json.loads(response.body.decode())
        assert "error" in body

    @pytest.mark.asyncio
    async def test_handle_remove_device_success(self, mock_area_manager):
        """Test removing a device from area."""
        response = await handle_remove_device(mock_area_manager, "living_room", "climate.heater")
        
        assert response.status == 200
        body = json.loads(response.body.decode())
        assert body["success"] == True
        
        mock_area_manager.remove_device_from_area.assert_called_once_with("living_room", "climate.heater")
        mock_area_manager.async_save.assert_called_once()

    @pytest.mark.asyncio
    async def test_handle_remove_device_error(self, mock_area_manager):
        """Test removing device with error."""
        mock_area_manager.remove_device_from_area.side_effect = ValueError("Device not found")
        
        response = await handle_remove_device(mock_area_manager, "living_room", "nonexistent")
        
        assert response.status == 404
        body = json.loads(response.body.decode())
        assert "error" in body
