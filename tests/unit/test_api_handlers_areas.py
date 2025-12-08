"""Tests for area API handlers."""

import pytest
from unittest.mock import MagicMock, AsyncMock, patch
from aiohttp import web
import json

from smart_heating.api_handlers.areas import (
    handle_get_areas,
    handle_get_area,
    handle_set_temperature,
    handle_enable_area,
    handle_disable_area,
    handle_hide_area,
    handle_unhide_area,
    handle_set_switch_shutdown,
    handle_set_area_hysteresis,
    handle_set_auto_preset,
    handle_set_area_preset_config,
    handle_set_manual_override,
)
from smart_heating.const import DOMAIN


@pytest.fixture
def mock_hass():
    """Create mock Home Assistant instance."""
    hass = MagicMock()
    hass.data = {DOMAIN: {"test_coordinator": MagicMock()}}
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
    mock_area.enabled = True
    mock_area.hidden = False
    mock_area.target_temperature = 21.0
    mock_area.current_temperature = 20.5
    mock_area.devices = {"climate.heater": {"type": "climate"}}
    mock_area.schedules = []
    mock_area.manual_override = False
    mock_area.preset_mode = "none"
    mock_area.shutdown_switches_when_idle = True
    mock_area.hysteresis_override = None
    mock_area.auto_preset_enabled = False
    mock_area.use_global_away = True
    mock_area.use_global_eco = True
    mock_area.use_global_comfort = True
    mock_area.use_global_home = True
    mock_area.use_global_sleep = True
    mock_area.use_global_activity = True
    mock_area.use_global_presence = True
    mock_area.get_effective_target_temperature.return_value = 21.0
    
    manager.get_area.return_value = mock_area
    manager.areas = {"living_room": mock_area}
    manager.is_safety_alert_active.return_value = False
    manager.async_save = AsyncMock()
    
    return manager


@pytest.fixture
def mock_area_registry():
    """Create mock area registry."""
    registry = MagicMock()
    
    mock_ha_area = MagicMock()
    mock_ha_area.id = "living_room"
    mock_ha_area.name = "Living Room"
    
    registry.areas = {"living_room": mock_ha_area}
    registry.async_get_area.return_value = mock_ha_area
    
    return registry


class TestAreaHandlers:
    """Test area API handlers."""

    @pytest.mark.asyncio
    async def test_handle_get_areas(self, mock_hass, mock_area_manager, mock_area_registry):
        """Test getting all areas."""
        with patch("smart_heating.api_handlers.areas.ar.async_get", return_value=mock_area_registry), \
             patch("smart_heating.api_handlers.areas.get_coordinator_devices", return_value={}), \
             patch("smart_heating.api_handlers.areas.build_device_info", return_value={"id": "climate.heater"}), \
             patch("smart_heating.api_handlers.areas.build_area_response", return_value={
                 "id": "living_room",
                 "name": "Living Room",
                 "enabled": True,
                 "devices": [{"id": "climate.heater"}]
             }):
            
            response = await handle_get_areas(mock_hass, mock_area_manager)
            
            assert response.status == 200
            body = json.loads(response.body.decode())
            assert "areas" in body
            assert len(body["areas"]) == 1
            assert body["areas"][0]["id"] == "living_room"
            assert body["areas"][0]["name"] == "Living Room"

    @pytest.mark.asyncio
    async def test_handle_get_areas_no_stored_data(self, mock_hass, mock_area_registry):
        """Test getting areas with no stored data."""
        area_manager = MagicMock()
        area_manager.get_area.return_value = None  # No stored data
        
        with patch("smart_heating.api_handlers.areas.ar.async_get", return_value=mock_area_registry):
            response = await handle_get_areas(mock_hass, area_manager)
            
            assert response.status == 200
            body = json.loads(response.body.decode())
            assert "areas" in body
            assert len(body["areas"]) == 1
            # Should have default values
            assert body["areas"][0]["enabled"] == True
            assert body["areas"][0]["target_temperature"] == 20.0

    @pytest.mark.asyncio
    async def test_handle_get_area_success(self, mock_hass, mock_area_manager):
        """Test getting a specific area."""
        with patch("smart_heating.api_handlers.areas.build_device_info", return_value={"id": "climate.heater"}), \
             patch("smart_heating.api_handlers.areas.build_area_response", return_value={
                 "id": "living_room",
                 "name": "Living Room"
             }):
            
            response = await handle_get_area(mock_hass, mock_area_manager, "living_room")
            
            assert response.status == 200
            body = json.loads(response.body.decode())
            assert body["id"] == "living_room"

    @pytest.mark.asyncio
    async def test_handle_get_area_not_found(self, mock_hass):
        """Test getting non-existent area."""
        area_manager = MagicMock()
        area_manager.get_area.return_value = None
        
        response = await handle_get_area(mock_hass, area_manager, "nonexistent")
        
        assert response.status == 404
        body = json.loads(response.body.decode())
        assert "error" in body

    @pytest.mark.asyncio
    async def test_handle_set_temperature_success(self, mock_hass, mock_area_manager):
        """Test setting area temperature."""
        mock_coordinator = AsyncMock()
        mock_hass.data[DOMAIN]["test_coordinator"] = mock_coordinator
        
        mock_climate = AsyncMock()
        mock_hass.data[DOMAIN]["climate_controller"] = mock_climate
        
        data = {"temperature": 22.5}
        
        with patch("smart_heating.utils.validators.validate_area_id", return_value=(True, None)), \
             patch("smart_heating.utils.validators.validate_temperature", return_value=(True, None)):
            
            response = await handle_set_temperature(mock_hass, mock_area_manager, "living_room", data)
            
            assert response.status == 200
            body = json.loads(response.body.decode())
            assert body["success"] == True
            
            mock_area_manager.set_area_target_temperature.assert_called_once_with("living_room", 22.5)
            mock_area_manager.async_save.assert_called_once()
            mock_climate.async_control_heating.assert_called_once()

    @pytest.mark.asyncio
    async def test_handle_set_temperature_invalid_area_id(self, mock_hass, mock_area_manager):
        """Test setting temperature with invalid area ID."""
        data = {"temperature": 22.5}
        
        with patch("smart_heating.utils.validators.validate_area_id", return_value=(False, "Invalid area ID")):
            response = await handle_set_temperature(mock_hass, mock_area_manager, "", data)
            
            assert response.status == 400
            body = json.loads(response.body.decode())
            assert "error" in body

    @pytest.mark.asyncio
    async def test_handle_set_temperature_invalid_temperature(self, mock_hass, mock_area_manager):
        """Test setting invalid temperature."""
        data = {"temperature": 100}
        
        with patch("smart_heating.utils.validators.validate_area_id", return_value=(True, None)), \
             patch("smart_heating.utils.validators.validate_temperature", return_value=(False, "Temperature out of range")):
            
            response = await handle_set_temperature(mock_hass, mock_area_manager, "living_room", data)
            
            assert response.status == 400
            body = json.loads(response.body.decode())
            assert "error" in body

    @pytest.mark.asyncio
    async def test_handle_set_temperature_area_not_found(self, mock_hass):
        """Test setting temperature for non-existent area."""
        area_manager = MagicMock()
        area_manager.get_area.return_value = None
        
        data = {"temperature": 22.5}
        
        with patch("smart_heating.utils.validators.validate_area_id", return_value=(True, None)), \
             patch("smart_heating.utils.validators.validate_temperature", return_value=(True, None)):
            
            response = await handle_set_temperature(mock_hass, area_manager, "nonexistent", data)
            
            assert response.status == 404
            body = json.loads(response.body.decode())
            assert "error" in body

    @pytest.mark.asyncio
    async def test_handle_set_temperature_clears_manual_override(self, mock_hass, mock_area_manager):
        """Test that setting temperature clears manual override."""
        mock_area_manager.get_area.return_value.manual_override = True
        
        mock_coordinator = AsyncMock()
        mock_hass.data[DOMAIN]["test_coordinator"] = mock_coordinator
        mock_climate = AsyncMock()
        mock_hass.data[DOMAIN]["climate_controller"] = mock_climate
        
        data = {"temperature": 22.5}
        
        with patch("smart_heating.utils.validators.validate_area_id", return_value=(True, None)), \
             patch("smart_heating.utils.validators.validate_temperature", return_value=(True, None)):
            
            response = await handle_set_temperature(mock_hass, mock_area_manager, "living_room", data)
            
            assert response.status == 200
            assert mock_area_manager.get_area.return_value.manual_override == False

    @pytest.mark.asyncio
    async def test_handle_enable_area_success(self, mock_hass, mock_area_manager):
        """Test enabling an area."""
        mock_coordinator = AsyncMock()
        mock_hass.data[DOMAIN]["test_coordinator"] = mock_coordinator
        mock_climate = AsyncMock()
        mock_hass.data[DOMAIN]["climate_controller"] = mock_climate
        
        response = await handle_enable_area(mock_hass, mock_area_manager, "living_room")
        
        assert response.status == 200
        body = json.loads(response.body.decode())
        assert body["success"] == True
        
        mock_area_manager.enable_area.assert_called_once_with("living_room")
        mock_area_manager.async_save.assert_called_once()
        mock_climate.async_control_heating.assert_called_once()

    @pytest.mark.asyncio
    async def test_handle_enable_area_clears_safety_alert(self, mock_hass, mock_area_manager):
        """Test enabling area clears safety alert."""
        mock_area_manager.is_safety_alert_active.return_value = True
        mock_safety = MagicMock()
        mock_hass.data[DOMAIN]["safety_monitor"] = mock_safety
        
        mock_coordinator = AsyncMock()
        mock_hass.data[DOMAIN]["test_coordinator"] = mock_coordinator
        mock_climate = AsyncMock()
        mock_hass.data[DOMAIN]["climate_controller"] = mock_climate
        
        response = await handle_enable_area(mock_hass, mock_area_manager, "living_room")
        
        assert response.status == 200
        mock_area_manager.set_safety_alert_active.assert_called_once_with(False)

    @pytest.mark.asyncio
    async def test_handle_enable_area_error(self, mock_hass, mock_area_manager):
        """Test enable area with error."""
        mock_area_manager.enable_area.side_effect = ValueError("Area not found")
        
        response = await handle_enable_area(mock_hass, mock_area_manager, "nonexistent")
        
        assert response.status == 404
        body = json.loads(response.body.decode())
        assert "error" in body

    @pytest.mark.asyncio
    async def test_handle_disable_area_success(self, mock_hass, mock_area_manager):
        """Test disabling an area."""
        mock_coordinator = AsyncMock()
        mock_hass.data[DOMAIN]["test_coordinator"] = mock_coordinator
        mock_climate = AsyncMock()
        mock_hass.data[DOMAIN]["climate_controller"] = mock_climate
        
        response = await handle_disable_area(mock_hass, mock_area_manager, "living_room")
        
        assert response.status == 200
        body = json.loads(response.body.decode())
        assert body["success"] == True
        
        mock_area_manager.disable_area.assert_called_once_with("living_room")
        mock_area_manager.async_save.assert_called_once()
        mock_climate.async_control_heating.assert_called_once()

    @pytest.mark.asyncio
    async def test_handle_disable_area_error(self, mock_hass, mock_area_manager):
        """Test disable area with error."""
        mock_area_manager.disable_area.side_effect = ValueError("Area not found")
        
        response = await handle_disable_area(mock_hass, mock_area_manager, "nonexistent")
        
        assert response.status == 404
        body = json.loads(response.body.decode())
        assert "error" in body

    @pytest.mark.asyncio
    async def test_handle_hide_area_existing(self, mock_hass, mock_area_manager):
        """Test hiding an existing area."""
        mock_coordinator = AsyncMock()
        mock_hass.data[DOMAIN]["test_coordinator"] = mock_coordinator
        
        response = await handle_hide_area(mock_hass, mock_area_manager, "living_room")
        
        assert response.status == 200
        body = json.loads(response.body.decode())
        assert body["success"] == True
        
        assert mock_area_manager.get_area.return_value.hidden == True
        mock_area_manager.async_save.assert_called_once()

    @pytest.mark.asyncio
    async def test_handle_hide_area_new(self, mock_hass, mock_area_registry):
        """Test hiding a new area (creates it first)."""
        area_manager = MagicMock()
        area_manager.get_area.return_value = None  # Area doesn't exist
        area_manager.areas = {}
        area_manager.async_save = AsyncMock()
        
        mock_coordinator = AsyncMock()
        mock_hass.data[DOMAIN]["test_coordinator"] = mock_coordinator
        
        with patch("smart_heating.api_handlers.areas.ar.async_get", return_value=mock_area_registry), \
             patch("smart_heating.api_handlers.areas.Area") as mock_area_class:
            
            mock_new_area = MagicMock()
            mock_area_class.return_value = mock_new_area
            
            response = await handle_hide_area(mock_hass, area_manager, "living_room")
            
            assert response.status == 200
            assert mock_new_area.hidden == True
            assert "living_room" in area_manager.areas

    @pytest.mark.asyncio
    async def test_handle_hide_area_not_in_ha(self, mock_hass):
        """Test hiding area not in Home Assistant."""
        area_manager = MagicMock()
        area_manager.get_area.return_value = None
        
        registry = MagicMock()
        registry.async_get_area.return_value = None  # Not in HA
        
        with patch("smart_heating.api_handlers.areas.ar.async_get", return_value=registry):
            response = await handle_hide_area(mock_hass, area_manager, "nonexistent")
            
            assert response.status == 404
            body = json.loads(response.body.decode())
            assert "error" in body

    @pytest.mark.asyncio
    async def test_handle_unhide_area_existing(self, mock_hass, mock_area_manager):
        """Test unhiding an existing area."""
        mock_area_manager.get_area.return_value.hidden = True
        
        mock_coordinator = AsyncMock()
        mock_hass.data[DOMAIN]["test_coordinator"] = mock_coordinator
        
        response = await handle_unhide_area(mock_hass, mock_area_manager, "living_room")
        
        assert response.status == 200
        body = json.loads(response.body.decode())
        assert body["success"] == True
        
        assert mock_area_manager.get_area.return_value.hidden == False
        mock_area_manager.async_save.assert_called_once()

    @pytest.mark.asyncio
    async def test_handle_unhide_area_new(self, mock_hass, mock_area_registry):
        """Test unhiding a new area (creates it first)."""
        area_manager = MagicMock()
        area_manager.get_area.return_value = None
        area_manager.areas = {}
        area_manager.async_save = AsyncMock()
        
        mock_coordinator = AsyncMock()
        mock_hass.data[DOMAIN]["test_coordinator"] = mock_coordinator
        
        with patch("smart_heating.api_handlers.areas.ar.async_get", return_value=mock_area_registry), \
             patch("smart_heating.api_handlers.areas.Area") as mock_area_class:
            
            mock_new_area = MagicMock()
            mock_area_class.return_value = mock_new_area
            
            response = await handle_unhide_area(mock_hass, area_manager, "living_room")
            
            assert response.status == 200
            assert mock_new_area.hidden == False

    @pytest.mark.asyncio
    async def test_handle_set_switch_shutdown_success(self, mock_hass, mock_area_manager):
        """Test setting switch shutdown setting."""
        mock_coordinator = AsyncMock()
        mock_hass.data[DOMAIN]["test_coordinator"] = mock_coordinator
        
        data = {"shutdown": False}
        response = await handle_set_switch_shutdown(mock_hass, mock_area_manager, "living_room", data)
        
        assert response.status == 200
        body = json.loads(response.body.decode())
        assert body["success"] == True
        
        assert mock_area_manager.get_area.return_value.shutdown_switches_when_idle == False
        mock_area_manager.async_save.assert_called_once()

    @pytest.mark.asyncio
    async def test_handle_set_switch_shutdown_default(self, mock_hass, mock_area_manager):
        """Test setting switch shutdown with default value."""
        mock_coordinator = AsyncMock()
        mock_hass.data[DOMAIN]["test_coordinator"] = mock_coordinator
        
        data = {}  # No shutdown key
        response = await handle_set_switch_shutdown(mock_hass, mock_area_manager, "living_room", data)
        
        assert response.status == 200
        # Default is True
        assert mock_area_manager.get_area.return_value.shutdown_switches_when_idle == True

    @pytest.mark.asyncio
    async def test_handle_set_switch_shutdown_not_found(self, mock_hass):
        """Test setting switch shutdown for non-existent area."""
        area_manager = MagicMock()
        area_manager.get_area.return_value = None
        
        data = {"shutdown": False}
        response = await handle_set_switch_shutdown(mock_hass, area_manager, "nonexistent", data)
        
        assert response.status == 404
        body = json.loads(response.body.decode())
        assert "error" in body

    @pytest.mark.asyncio
    async def test_handle_set_area_hysteresis_use_global(self, mock_hass, mock_area_manager):
        """Test setting area to use global hysteresis."""
        mock_coordinator = AsyncMock()
        mock_hass.data[DOMAIN]["test_coordinator"] = mock_coordinator
        
        data = {"use_global": True}
        response = await handle_set_area_hysteresis(mock_hass, mock_area_manager, "living_room", data)
        
        assert response.status == 200
        body = json.loads(response.body.decode())
        assert body["success"] == True
        
        assert mock_area_manager.get_area.return_value.hysteresis_override is None
        mock_area_manager.async_save.assert_called_once()

    @pytest.mark.asyncio
    async def test_handle_set_area_hysteresis_custom(self, mock_hass, mock_area_manager):
        """Test setting custom area hysteresis."""
        mock_coordinator = AsyncMock()
        mock_hass.data[DOMAIN]["test_coordinator"] = mock_coordinator
        
        data = {"use_global": False, "hysteresis": 0.5}
        response = await handle_set_area_hysteresis(mock_hass, mock_area_manager, "living_room", data)
        
        assert response.status == 200
        body = json.loads(response.body.decode())
        assert body["success"] == True
        
        assert mock_area_manager.get_area.return_value.hysteresis_override == 0.5
        mock_area_manager.async_save.assert_called_once()

    @pytest.mark.asyncio
    async def test_handle_set_area_hysteresis_missing_value(self, mock_hass, mock_area_manager):
        """Test setting hysteresis without value."""
        data = {"use_global": False}  # Missing hysteresis
        response = await handle_set_area_hysteresis(mock_hass, mock_area_manager, "living_room", data)
        
        assert response.status == 400
        body = json.loads(response.body.decode())
        assert "error" in body

    @pytest.mark.asyncio
    async def test_handle_set_area_hysteresis_out_of_range(self, mock_hass, mock_area_manager):
        """Test setting hysteresis with out-of-range value."""
        data = {"use_global": False, "hysteresis": 5.0}  # Too high
        response = await handle_set_area_hysteresis(mock_hass, mock_area_manager, "living_room", data)
        
        assert response.status == 400
        body = json.loads(response.body.decode())
        assert "error" in body

    @pytest.mark.asyncio
    async def test_handle_set_area_hysteresis_not_found(self, mock_hass):
        """Test setting hysteresis for non-existent area."""
        area_manager = MagicMock()
        area_manager.get_area.return_value = None
        
        data = {"use_global": True}
        response = await handle_set_area_hysteresis(mock_hass, area_manager, "nonexistent", data)
        
        assert response.status == 404
        body = json.loads(response.body.decode())
        assert "error" in body

    @pytest.mark.asyncio
    async def test_handle_set_auto_preset_success(self, mock_hass, mock_area_manager):
        """Test setting auto preset configuration."""
        mock_coordinator = AsyncMock()
        mock_hass.data[DOMAIN]["test_coordinator"] = mock_coordinator
        
        data = {"auto_preset_enabled": True}
        response = await handle_set_auto_preset(mock_hass, mock_area_manager, "living_room", data)
        
        assert response.status == 200
        body = json.loads(response.body.decode())
        assert body["success"] == True
        
        assert mock_area_manager.get_area.return_value.auto_preset_enabled == True
        mock_area_manager.async_save.assert_called_once()

    @pytest.mark.asyncio
    async def test_handle_set_auto_preset_not_found(self, mock_hass):
        """Test setting auto preset for non-existent area."""
        area_manager = MagicMock()
        area_manager.get_area.return_value = None
        
        data = {"auto_preset_enabled": True}
        response = await handle_set_auto_preset(mock_hass, area_manager, "nonexistent", data)
        
        assert response.status == 404
        body = json.loads(response.body.decode())
        assert "error" in body

    @pytest.mark.asyncio
    async def test_handle_set_area_preset_config_success(self, mock_hass, mock_area_manager):
        """Test setting area preset configuration."""
        mock_coordinator = AsyncMock()
        mock_hass.data[DOMAIN]["test_coordinator"] = mock_coordinator
        
        data = {
            "use_global_away": False,
            "use_global_eco": True,
            "use_global_comfort": False
        }
        response = await handle_set_area_preset_config(mock_hass, mock_area_manager, "living_room", data)
        
        assert response.status == 200
        body = json.loads(response.body.decode())
        assert body["success"] == True
        
        area = mock_area_manager.get_area.return_value
        assert area.use_global_away == False
        assert area.use_global_eco == True
        assert area.use_global_comfort == False
        mock_area_manager.async_save.assert_called_once()

    @pytest.mark.asyncio
    async def test_handle_set_area_preset_config_all_flags(self, mock_hass, mock_area_manager):
        """Test setting all preset config flags."""
        mock_coordinator = AsyncMock()
        mock_hass.data[DOMAIN]["test_coordinator"] = mock_coordinator
        
        data = {
            "use_global_away": True,
            "use_global_eco": False,
            "use_global_comfort": True,
            "use_global_home": False,
            "use_global_sleep": True,
            "use_global_activity": False,
            "use_global_presence": True
        }
        response = await handle_set_area_preset_config(mock_hass, mock_area_manager, "living_room", data)
        
        assert response.status == 200
        area = mock_area_manager.get_area.return_value
        assert area.use_global_away == True
        assert area.use_global_eco == False
        assert area.use_global_comfort == True
        assert area.use_global_home == False
        assert area.use_global_sleep == True
        assert area.use_global_activity == False
        assert area.use_global_presence == True

    @pytest.mark.asyncio
    async def test_handle_set_area_preset_config_not_found(self, mock_hass):
        """Test setting preset config for non-existent area."""
        area_manager = MagicMock()
        area_manager.get_area.return_value = None
        
        data = {"use_global_away": False}
        response = await handle_set_area_preset_config(mock_hass, area_manager, "nonexistent", data)
        
        assert response.status == 404
        body = json.loads(response.body.decode())
        assert "error" in body

    @pytest.mark.asyncio
    async def test_handle_set_manual_override_enable(self, mock_hass, mock_area_manager):
        """Test enabling manual override."""
        mock_coordinator = AsyncMock()
        mock_hass.data[DOMAIN]["test_coordinator"] = mock_coordinator
        mock_climate = AsyncMock()
        mock_hass.data[DOMAIN]["climate_controller"] = mock_climate
        
        data = {"enabled": True}
        response = await handle_set_manual_override(mock_hass, mock_area_manager, "living_room", data)
        
        assert response.status == 200
        body = json.loads(response.body.decode())
        assert body["success"] == True
        
        assert mock_area_manager.get_area.return_value.manual_override == True
        mock_area_manager.async_save.assert_called_once()
        mock_climate.async_control_heating.assert_called_once()

    @pytest.mark.asyncio
    async def test_handle_set_manual_override_disable_with_preset(self, mock_hass, mock_area_manager):
        """Test disabling manual override updates target temp with preset."""
        mock_area = mock_area_manager.get_area.return_value
        mock_area.manual_override = True
        mock_area.preset_mode = "eco"
        mock_area.target_temperature = 21.0
        mock_area.get_effective_target_temperature.return_value = 18.0
        
        mock_coordinator = AsyncMock()
        mock_hass.data[DOMAIN]["test_coordinator"] = mock_coordinator
        mock_climate = AsyncMock()
        mock_hass.data[DOMAIN]["climate_controller"] = mock_climate
        
        data = {"enabled": False}
        response = await handle_set_manual_override(mock_hass, mock_area_manager, "living_room", data)
        
        assert response.status == 200
        assert mock_area.manual_override == False
        assert mock_area.target_temperature == 18.0  # Updated to preset temp

    @pytest.mark.asyncio
    async def test_handle_set_manual_override_missing_enabled(self, mock_hass, mock_area_manager):
        """Test setting manual override without enabled field."""
        data = {}  # Missing enabled
        response = await handle_set_manual_override(mock_hass, mock_area_manager, "living_room", data)
        
        assert response.status == 400
        body = json.loads(response.body.decode())
        assert "error" in body

    @pytest.mark.asyncio
    async def test_handle_set_manual_override_not_found(self, mock_hass):
        """Test setting manual override for non-existent area."""
        area_manager = MagicMock()
        area_manager.get_area.return_value = None
        
        data = {"enabled": True}
        response = await handle_set_manual_override(mock_hass, area_manager, "nonexistent", data)
        
        assert response.status == 404
        body = json.loads(response.body.decode())
        assert "error" in body


class TestHandleSetPrimaryTemperatureSensor:
    """Test handle_set_primary_temperature_sensor function."""
    
    @pytest.mark.asyncio
    async def test_set_primary_sensor_success(self, mock_hass, mock_area_manager):
        """Test setting primary temperature sensor successfully."""
        from smart_heating.api_handlers.areas import handle_set_primary_temperature_sensor
        
        area = MagicMock()
        area.id = "area1"
        area.name = "Living Room"
        area.primary_temperature_sensor = None
        area.get_temperature_sensors.return_value = ["sensor.temp1", "sensor.temp2"]
        area.get_thermostats.return_value = ["climate.thermo1"]
        
        mock_area_manager.get_area.return_value = area
        
        # Mock climate controller
        climate_controller = MagicMock()
        climate_controller.async_update_area_temperatures = AsyncMock()
        climate_controller.async_control_heating = AsyncMock()
        
        # Mock coordinator with AsyncMock for refresh
        coordinator = MagicMock()
        coordinator.async_request_refresh = AsyncMock()
        
        mock_hass.data = {
            "smart_heating": {
                "climate_controller": climate_controller,
                "test_entry_id": coordinator
            }
        }
        
        data = {"sensor_id": "sensor.temp1"}
        response = await handle_set_primary_temperature_sensor(mock_hass, mock_area_manager, "area1", data)
        
        assert response.status == 200
        assert area.primary_temperature_sensor == "sensor.temp1"
        mock_area_manager.async_save.assert_called_once()
        climate_controller.async_update_area_temperatures.assert_called_once()
        climate_controller.async_control_heating.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_set_primary_thermostat_success(self, mock_hass, mock_area_manager):
        """Test setting primary thermostat successfully."""
        from smart_heating.api_handlers.areas import handle_set_primary_temperature_sensor
        
        area = MagicMock()
        area.id = "area1"
        area.name = "Living Room"
        area.primary_temperature_sensor = None
        area.get_temperature_sensors.return_value = ["sensor.temp1"]
        area.get_thermostats.return_value = ["climate.thermo1", "climate.thermo2"]
        
        mock_area_manager.get_area.return_value = area
        
        # Mock climate controller
        climate_controller = MagicMock()
        climate_controller.async_update_area_temperatures = AsyncMock()
        climate_controller.async_control_heating = AsyncMock()
        
        # Mock coordinator with AsyncMock for refresh
        coordinator = MagicMock()
        coordinator.async_request_refresh = AsyncMock()
        
        mock_hass.data = {
            "smart_heating": {
                "climate_controller": climate_controller,
                "test_entry_id": coordinator
            }
        }
        
        data = {"sensor_id": "climate.thermo1"}
        response = await handle_set_primary_temperature_sensor(mock_hass, mock_area_manager, "area1", data)
        
        assert response.status == 200
        assert area.primary_temperature_sensor == "climate.thermo1"
    
    @pytest.mark.asyncio
    async def test_reset_to_auto_mode(self, mock_hass, mock_area_manager):
        """Test resetting to auto mode (None)."""
        from smart_heating.api_handlers.areas import handle_set_primary_temperature_sensor
        
        area = MagicMock()
        area.id = "area1"
        area.name = "Living Room"
        area.primary_temperature_sensor = "sensor.temp1"
        area.get_temperature_sensors.return_value = ["sensor.temp1"]
        area.get_thermostats.return_value = []
        
        mock_area_manager.get_area.return_value = area
        
        # Mock climate controller
        climate_controller = MagicMock()
        climate_controller.async_update_area_temperatures = AsyncMock()
        climate_controller.async_control_heating = AsyncMock()
        
        # Mock coordinator with AsyncMock for refresh
        coordinator = MagicMock()
        coordinator.async_request_refresh = AsyncMock()
        
        mock_hass.data = {
            "smart_heating": {
                "climate_controller": climate_controller,
                "test_entry_id": coordinator
            }
        }
        
        data = {"sensor_id": None}
        response = await handle_set_primary_temperature_sensor(mock_hass, mock_area_manager, "area1", data)
        
        assert response.status == 200
        assert area.primary_temperature_sensor is None
    
    @pytest.mark.asyncio
    async def test_sensor_not_in_area(self, mock_hass, mock_area_manager):
        """Test setting sensor that doesn't exist in area."""
        from smart_heating.api_handlers.areas import handle_set_primary_temperature_sensor
        
        area = MagicMock()
        area.id = "area1"
        area.name = "Living Room"
        area.get_temperature_sensors.return_value = ["sensor.temp1"]
        area.get_thermostats.return_value = ["climate.thermo1"]
        
        mock_area_manager.get_area.return_value = area
        
        data = {"sensor_id": "sensor.nonexistent"}
        response = await handle_set_primary_temperature_sensor(mock_hass, mock_area_manager, "area1", data)
        
        assert response.status == 400
        body = json.loads(response.body.decode())
        assert "error" in body
        assert "not found" in body["error"]
    
    @pytest.mark.asyncio
    async def test_area_not_found(self, mock_hass):
        """Test setting primary sensor for non-existent area."""
        from smart_heating.api_handlers.areas import handle_set_primary_temperature_sensor
        
        area_manager = MagicMock()
        area_manager.get_area.return_value = None
        
        data = {"sensor_id": "sensor.temp1"}
        response = await handle_set_primary_temperature_sensor(mock_hass, area_manager, "nonexistent", data)
        
        assert response.status == 404
        body = json.loads(response.body.decode())
        assert "error" in body

