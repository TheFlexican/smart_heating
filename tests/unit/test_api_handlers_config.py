"""Tests for configuration API handlers."""

import pytest
from unittest.mock import MagicMock, AsyncMock, patch
from aiohttp import web
import json

from smart_heating.api_handlers.config import (
    handle_get_config,
    handle_get_global_presets,
    handle_set_global_presets,
    handle_get_hysteresis,
    handle_set_hysteresis_value,
    handle_get_global_presence,
    handle_set_global_presence,
    handle_set_frost_protection,
    handle_get_vacation_mode,
    handle_enable_vacation_mode,
    handle_disable_vacation_mode,
    handle_get_safety_sensor,
    handle_set_safety_sensor,
    handle_remove_safety_sensor,
    handle_set_hvac_mode,
)
from smart_heating.const import DOMAIN


@pytest.fixture
def mock_hass():
    """Create mock Home Assistant instance."""
    hass = MagicMock()
    hass.data = {DOMAIN: {}}
    hass.bus = MagicMock()
    hass.bus.async_fire = MagicMock()
    return hass


@pytest.fixture
def mock_area_manager():
    """Create mock area manager."""
    manager = MagicMock()
    manager.opentherm_gateway_id = "climate.gateway"
    manager.opentherm_enabled = True
    manager.trv_heating_temp = 22.0
    manager.trv_idle_temp = 18.0
    manager.trv_temp_offset = 1.0
    manager.hysteresis = 0.5
    manager.global_away_temp = 15.0
    manager.global_eco_temp = 18.0
    manager.global_comfort_temp = 22.0
    manager.global_home_temp = 20.0
    manager.global_sleep_temp = 17.0
    manager.global_activity_temp = 21.0
    manager.global_presence_sensors = ["binary_sensor.motion"]
    manager.frost_protection_enabled = False
    manager.frost_protection_temp = 5.0
    manager.get_safety_sensors.return_value = []
    manager.is_safety_alert_active.return_value = False
    manager.async_save = AsyncMock()
    
    # Mock area
    mock_area = MagicMock()
    mock_area.id = "living_room"
    mock_area.hvac_mode = "heat"
    manager.get_area.return_value = mock_area
    manager.areas = {"living_room": mock_area}
    
    return manager


@pytest.fixture
def mock_coordinator():
    """Create mock coordinator."""
    coordinator = AsyncMock()
    return coordinator


class TestConfigHandlers:
    """Test configuration API handlers."""

    @pytest.mark.asyncio
    async def test_handle_get_config(self, mock_hass, mock_area_manager):
        """Test getting system configuration."""
        response = await handle_get_config(mock_hass, mock_area_manager)
        
        assert response.status == 200
        body = json.loads(response.body.decode())
        assert body["opentherm_gateway_id"] == "climate.gateway"
        assert body["opentherm_enabled"] == True
        assert body["trv_heating_temp"] == 22.0
        assert body["safety_alert_active"] == False

    @pytest.mark.asyncio
    async def test_handle_get_global_presets(self, mock_area_manager):
        """Test getting global preset temperatures."""
        response = await handle_get_global_presets(mock_area_manager)
        
        assert response.status == 200
        body = json.loads(response.body.decode())
        assert body["away_temp"] == 15.0
        assert body["eco_temp"] == 18.0
        assert body["comfort_temp"] == 22.0
        assert body["home_temp"] == 20.0
        assert body["sleep_temp"] == 17.0
        assert body["activity_temp"] == 21.0

    @pytest.mark.asyncio
    async def test_handle_set_global_presets_all(self, mock_area_manager):
        """Test setting all global preset temperatures."""
        data = {
            "away_temp": 14.0,
            "eco_temp": 17.0,
            "comfort_temp": 23.0,
            "home_temp": 19.0,
            "sleep_temp": 16.0,
            "activity_temp": 22.0
        }
        
        response = await handle_set_global_presets(mock_area_manager, data)
        
        assert response.status == 200
        body = json.loads(response.body.decode())
        assert body["success"] == True
        
        assert mock_area_manager.global_away_temp == 14.0
        assert mock_area_manager.global_eco_temp == 17.0
        assert mock_area_manager.global_comfort_temp == 23.0
        assert mock_area_manager.global_home_temp == 19.0
        assert mock_area_manager.global_sleep_temp == 16.0
        assert mock_area_manager.global_activity_temp == 22.0
        mock_area_manager.async_save.assert_called_once()

    @pytest.mark.asyncio
    async def test_handle_set_global_presets_partial(self, mock_area_manager):
        """Test setting only some preset temperatures."""
        data = {"eco_temp": 17.5, "comfort_temp": 21.5}
        
        response = await handle_set_global_presets(mock_area_manager, data)
        
        assert response.status == 200
        assert mock_area_manager.global_eco_temp == 17.5
        assert mock_area_manager.global_comfort_temp == 21.5
        # Others should remain unchanged
        assert mock_area_manager.global_away_temp == 15.0

    @pytest.mark.asyncio
    async def test_handle_get_hysteresis(self, mock_area_manager):
        """Test getting hysteresis value."""
        response = await handle_get_hysteresis(mock_area_manager)
        
        assert response.status == 200
        body = json.loads(response.body.decode())
        assert body["hysteresis"] == 0.5

    @pytest.mark.asyncio
    async def test_handle_set_hysteresis_value_success(self, mock_hass, mock_area_manager, mock_coordinator):
        """Test setting hysteresis value."""
        data = {"hysteresis": 0.8}
        
        response = await handle_set_hysteresis_value(
            mock_hass, mock_area_manager, mock_coordinator, data
        )
        
        assert response.status == 200
        body = json.loads(response.body.decode())
        assert body["success"] == True
        
        assert mock_area_manager.hysteresis == 0.8
        mock_area_manager.async_save.assert_called_once()
        mock_coordinator.async_request_refresh.assert_called_once()

    @pytest.mark.asyncio
    async def test_handle_set_hysteresis_value_out_of_range_low(
        self, mock_hass, mock_area_manager, mock_coordinator
    ):
        """Test setting hysteresis below minimum."""
        data = {"hysteresis": 0.05}
        
        response = await handle_set_hysteresis_value(
            mock_hass, mock_area_manager, mock_coordinator, data
        )
        
        assert response.status == 400
        body = json.loads(response.body.decode())
        assert "error" in body

    @pytest.mark.asyncio
    async def test_handle_set_hysteresis_value_out_of_range_high(
        self, mock_hass, mock_area_manager, mock_coordinator
    ):
        """Test setting hysteresis above maximum."""
        data = {"hysteresis": 5.0}
        
        response = await handle_set_hysteresis_value(
            mock_hass, mock_area_manager, mock_coordinator, data
        )
        
        assert response.status == 400
        body = json.loads(response.body.decode())
        assert "error" in body

    @pytest.mark.asyncio
    async def test_handle_set_hysteresis_value_missing(
        self, mock_hass, mock_area_manager, mock_coordinator
    ):
        """Test setting hysteresis without value."""
        data = {}
        
        response = await handle_set_hysteresis_value(
            mock_hass, mock_area_manager, mock_coordinator, data
        )
        
        assert response.status == 400
        body = json.loads(response.body.decode())
        assert "error" in body

    @pytest.mark.asyncio
    async def test_handle_get_global_presence(self, mock_area_manager):
        """Test getting global presence sensors."""
        response = await handle_get_global_presence(mock_area_manager)
        
        assert response.status == 200
        body = json.loads(response.body.decode())
        assert body["sensors"] == ["binary_sensor.motion"]

    @pytest.mark.asyncio
    async def test_handle_set_global_presence(self, mock_area_manager):
        """Test setting global presence sensors."""
        data = {"sensors": ["binary_sensor.motion1", "binary_sensor.motion2"]}
        
        response = await handle_set_global_presence(mock_area_manager, data)
        
        assert response.status == 200
        body = json.loads(response.body.decode())
        assert body["success"] == True
        
        assert len(mock_area_manager.global_presence_sensors) == 2
        mock_area_manager.async_save.assert_called_once()

    @pytest.mark.asyncio
    async def test_handle_set_frost_protection_both(self, mock_area_manager):
        """Test setting frost protection with both enabled and temperature."""
        data = {"enabled": True, "temperature": 7.0}
        
        response = await handle_set_frost_protection(mock_area_manager, data)
        
        assert response.status == 200
        body = json.loads(response.body.decode())
        assert body["success"] == True
        assert body["enabled"] == True
        assert body["temperature"] == 7.0
        
        assert mock_area_manager.frost_protection_enabled == True
        assert mock_area_manager.frost_protection_temp == 7.0
        mock_area_manager.async_save.assert_called_once()

    @pytest.mark.asyncio
    async def test_handle_set_frost_protection_enabled_only(self, mock_area_manager):
        """Test setting only frost protection enabled flag."""
        data = {"enabled": True}
        
        response = await handle_set_frost_protection(mock_area_manager, data)
        
        assert response.status == 200
        assert mock_area_manager.frost_protection_enabled == True
        # Temperature should remain unchanged
        assert mock_area_manager.frost_protection_temp == 5.0

    @pytest.mark.asyncio
    async def test_handle_set_frost_protection_temp_only(self, mock_area_manager):
        """Test setting only frost protection temperature."""
        data = {"temperature": 6.0}
        
        response = await handle_set_frost_protection(mock_area_manager, data)
        
        assert response.status == 200
        assert mock_area_manager.frost_protection_temp == 6.0
        # Enabled should remain unchanged
        assert mock_area_manager.frost_protection_enabled == False

    @pytest.mark.asyncio
    async def test_handle_set_frost_protection_error(self, mock_area_manager):
        """Test frost protection with ValueError."""
        mock_area_manager.async_save.side_effect = ValueError("Invalid value")
        
        data = {"enabled": True}
        response = await handle_set_frost_protection(mock_area_manager, data)
        
        assert response.status == 400
        body = json.loads(response.body.decode())
        assert "error" in body

    @pytest.mark.asyncio
    async def test_handle_get_vacation_mode_success(self, mock_hass):
        """Test getting vacation mode status."""
        mock_vacation = MagicMock()
        mock_vacation.get_data.return_value = {
            "enabled": True,
            "start_date": "2024-01-01",
            "end_date": "2024-01-07"
        }
        mock_hass.data[DOMAIN]["vacation_manager"] = mock_vacation
        
        response = await handle_get_vacation_mode(mock_hass)
        
        assert response.status == 200
        body = json.loads(response.body.decode())
        assert body["enabled"] == True
        assert body["start_date"] == "2024-01-01"

    @pytest.mark.asyncio
    async def test_handle_get_vacation_mode_no_manager(self, mock_hass):
        """Test getting vacation mode when manager not initialized."""
        response = await handle_get_vacation_mode(mock_hass)
        
        assert response.status == 500
        body = json.loads(response.body.decode())
        assert "error" in body

    @pytest.mark.asyncio
    async def test_handle_enable_vacation_mode_success(self, mock_hass):
        """Test enabling vacation mode."""
        mock_vacation = MagicMock()
        mock_vacation.async_enable = AsyncMock()
        mock_vacation.get_data.return_value = {"enabled": True}
        mock_hass.data[DOMAIN]["vacation_manager"] = mock_vacation
        
        data = {
            "start_date": "2024-01-01",
            "end_date": "2024-01-07",
            "temperature": 15.0
        }
        response = await handle_enable_vacation_mode(mock_hass, data)
        
        assert response.status == 200
        body = json.loads(response.body.decode())
        assert body["enabled"] == True
        
        mock_vacation.async_enable.assert_called_once_with(
            start_date="2024-01-01",
            end_date="2024-01-07",
            temperature=15.0
        )

    @pytest.mark.asyncio
    async def test_handle_enable_vacation_mode_missing_dates(self, mock_hass):
        """Test enabling vacation mode without dates."""
        mock_vacation = MagicMock()
        mock_hass.data[DOMAIN]["vacation_manager"] = mock_vacation
        
        data = {"temperature": 15.0}  # Missing dates
        response = await handle_enable_vacation_mode(mock_hass, data)
        
        assert response.status == 400
        body = json.loads(response.body.decode())
        assert "error" in body

    @pytest.mark.asyncio
    async def test_handle_enable_vacation_mode_no_manager(self, mock_hass):
        """Test enabling vacation mode when manager not initialized."""
        data = {
            "start_date": "2024-01-01",
            "end_date": "2024-01-07"
        }
        response = await handle_enable_vacation_mode(mock_hass, data)
        
        assert response.status == 500
        body = json.loads(response.body.decode())
        assert "error" in body

    @pytest.mark.asyncio
    async def test_handle_enable_vacation_mode_value_error(self, mock_hass):
        """Test enabling vacation mode with invalid data."""
        mock_vacation = MagicMock()
        mock_vacation.async_enable = AsyncMock(side_effect=ValueError("Invalid dates"))
        mock_hass.data[DOMAIN]["vacation_manager"] = mock_vacation
        
        data = {
            "start_date": "2024-01-07",
            "end_date": "2024-01-01"  # End before start
        }
        response = await handle_enable_vacation_mode(mock_hass, data)
        
        assert response.status == 400
        body = json.loads(response.body.decode())
        assert "error" in body

    @pytest.mark.asyncio
    async def test_handle_disable_vacation_mode_success(self, mock_hass):
        """Test disabling vacation mode."""
        mock_vacation = MagicMock()
        mock_vacation.async_disable = AsyncMock()
        mock_hass.data[DOMAIN]["vacation_manager"] = mock_vacation
        
        response = await handle_disable_vacation_mode(mock_hass)
        
        assert response.status == 200
        body = json.loads(response.body.decode())
        assert body["success"] == True
        
        mock_vacation.async_disable.assert_called_once()

    @pytest.mark.asyncio
    async def test_handle_disable_vacation_mode_no_manager(self, mock_hass):
        """Test disabling vacation mode when manager not initialized."""
        response = await handle_disable_vacation_mode(mock_hass)
        
        assert response.status == 500
        body = json.loads(response.body.decode())
        assert "error" in body

    @pytest.mark.asyncio
    async def test_handle_get_safety_sensor_with_sensor(self, mock_area_manager):
        """Test getting safety sensor when one is configured."""
        mock_area_manager.get_safety_sensors.return_value = [
            {"entity_id": "binary_sensor.smoke"}
        ]
        
        response = await handle_get_safety_sensor(mock_area_manager)
        
        assert response.status == 200
        body = json.loads(response.body.decode())
        assert body["sensor_id"] == "binary_sensor.smoke"
        assert body["enabled"] == True
        assert body["alert_active"] == False

    @pytest.mark.asyncio
    async def test_handle_get_safety_sensor_without_sensor(self, mock_area_manager):
        """Test getting safety sensor when none configured."""
        mock_area_manager.get_safety_sensors.return_value = []
        
        response = await handle_get_safety_sensor(mock_area_manager)
        
        assert response.status == 200
        body = json.loads(response.body.decode())
        assert body["sensor_id"] is None
        assert body["enabled"] == False
        assert body["alert_active"] == False

    @pytest.mark.asyncio
    async def test_handle_set_safety_sensor_success(self, mock_hass, mock_area_manager):
        """Test setting safety sensor."""
        mock_safety = MagicMock()
        mock_safety.async_reconfigure = AsyncMock()
        mock_hass.data[DOMAIN]["safety_monitor"] = mock_safety
        
        data = {"sensor_id": "binary_sensor.smoke"}
        response = await handle_set_safety_sensor(mock_hass, mock_area_manager, data)
        
        assert response.status == 200
        body = json.loads(response.body.decode())
        assert body["success"] == True
        assert body["sensor_id"] == "binary_sensor.smoke"
        
        mock_area_manager.clear_safety_sensors.assert_called_once()
        mock_area_manager.add_safety_sensor.assert_called_once_with("binary_sensor.smoke")
        mock_area_manager.async_save.assert_called_once()
        mock_safety.async_reconfigure.assert_called_once()
        mock_hass.bus.async_fire.assert_called_once()

    @pytest.mark.asyncio
    async def test_handle_set_safety_sensor_missing_id(self, mock_hass, mock_area_manager):
        """Test setting safety sensor without sensor_id."""
        data = {}
        response = await handle_set_safety_sensor(mock_hass, mock_area_manager, data)
        
        assert response.status == 400
        body = json.loads(response.body.decode())
        assert "error" in body

    @pytest.mark.asyncio
    async def test_handle_remove_safety_sensor(self, mock_hass, mock_area_manager):
        """Test removing safety sensor."""
        mock_safety = MagicMock()
        mock_safety.async_reconfigure = AsyncMock()
        mock_hass.data[DOMAIN]["safety_monitor"] = mock_safety
        
        response = await handle_remove_safety_sensor(mock_hass, mock_area_manager)
        
        assert response.status == 200
        body = json.loads(response.body.decode())
        assert body["success"] == True
        
        mock_area_manager.clear_safety_sensors.assert_called_once()
        mock_area_manager.async_save.assert_called_once()
        mock_safety.async_reconfigure.assert_called_once()
        mock_hass.bus.async_fire.assert_called_once()

    @pytest.mark.asyncio
    async def test_handle_set_hvac_mode_success(self, mock_hass, mock_area_manager):
        """Test setting HVAC mode."""
        mock_coordinator = AsyncMock()
        mock_hass.data[DOMAIN]["test_coordinator"] = mock_coordinator
        
        data = {"hvac_mode": "cool"}
        response = await handle_set_hvac_mode(mock_hass, mock_area_manager, "living_room", data)
        
        assert response.status == 200
        body = json.loads(response.body.decode())
        assert body["success"] == True
        assert body["hvac_mode"] == "cool"
        
        assert mock_area_manager.get_area.return_value.hvac_mode == "cool"
        mock_area_manager.async_save.assert_called_once()
        mock_coordinator.async_request_refresh.assert_called_once()

    @pytest.mark.asyncio
    async def test_handle_set_hvac_mode_missing_mode(self, mock_hass, mock_area_manager):
        """Test setting HVAC mode without mode parameter."""
        data = {}
        response = await handle_set_hvac_mode(mock_hass, mock_area_manager, "living_room", data)
        
        assert response.status == 400
        body = json.loads(response.body.decode())
        assert "error" in body

    @pytest.mark.asyncio
    async def test_handle_set_hvac_mode_area_not_found(self, mock_hass, mock_area_manager):
        """Test setting HVAC mode for non-existent area."""
        mock_area_manager.get_area.return_value = None
        
        data = {"hvac_mode": "cool"}
        response = await handle_set_hvac_mode(mock_hass, mock_area_manager, "nonexistent", data)
        
        assert response.status == 400
        body = json.loads(response.body.decode())
        assert "error" in body
