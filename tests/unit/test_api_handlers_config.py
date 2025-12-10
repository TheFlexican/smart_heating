"""Unit tests for config API handlers."""

from __future__ import annotations

import json
from unittest.mock import AsyncMock, MagicMock

import pytest
from homeassistant.core import HomeAssistant
from smart_heating.api_handlers.config import (
    handle_disable_vacation_mode,
    handle_enable_vacation_mode,
    handle_get_config,
    handle_get_global_presence,
    handle_get_global_presets,
    handle_get_hysteresis,
    handle_get_safety_sensor,
    handle_get_vacation_mode,
    handle_remove_safety_sensor,
    handle_set_advanced_control_config,
    handle_set_frost_protection,
    handle_set_global_presence,
    handle_set_global_presets,
    handle_set_hvac_mode,
    handle_set_hysteresis_value,
    handle_set_opentherm_gateway,
    handle_set_safety_sensor,
)
from smart_heating.area_manager import AreaManager
from smart_heating.const import DOMAIN

## The handler test moved down below fixtures to comply with import order linting


"""Tests for configuration API handlers."""


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
    manager.hide_devices_panel = False
    manager.advanced_control_enabled = False
    manager.heating_curve_enabled = False
    manager.pwm_enabled = False
    manager.pid_enabled = False
    manager.overshoot_protection_enabled = False
    manager.default_heating_curve_coefficient = 1.0
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


@pytest.mark.asyncio
async def test_handle_set_opentherm_gateway_updates_config_entry(hass: HomeAssistant):
    """Verify API handler updates the HA config entry options when a coordinator exists."""
    # Prepare area manager and coordinator
    area_manager = MagicMock(spec=AreaManager)
    area_manager.set_opentherm_gateway = AsyncMock()
    area_manager.async_save = AsyncMock()

    coordinator = MagicMock()
    # Mock coordinator.config_entry and coordinator.hass
    coordinator.config_entry = MagicMock()
    coordinator.config_entry.options = {}
    coordinator.hass = hass

    # Mock hass.config_entries.async_update_entry
    hass.config_entries.async_update_entry = AsyncMock()

    await handle_set_opentherm_gateway(area_manager, coordinator, {"gateway_id": "gateway1"})

    # Verify area_manager.set_opentherm_gateway was called
    area_manager.set_opentherm_gateway.assert_called_once_with("gateway1")

    # Verify HA config_entry async_update_entry was called
    hass.config_entries.async_update_entry.assert_called()


class TestConfigHandlers:
    """Test configuration API handlers."""

    @pytest.mark.asyncio
    async def test_handle_get_config(self, mock_hass, mock_area_manager):
        """Test getting system configuration."""
        response = await handle_get_config(mock_hass, mock_area_manager)

        assert response.status == 200
        body = json.loads(response.body.decode())
        assert body["opentherm_gateway_id"] == "climate.gateway"
        # Enablement is determined by gateway presence - ensure id present
        assert body["opentherm_gateway_id"] == "climate.gateway"
        assert body["trv_heating_temp"] == pytest.approx(22.0)
        assert body["safety_alert_active"] is False
        assert body["hide_devices_panel"] is False

    @pytest.mark.asyncio
    async def test_handle_get_global_presets(self, mock_area_manager):
        """Test getting global preset temperatures."""
        response = await handle_get_global_presets(mock_area_manager)

        assert response.status == 200
        body = json.loads(response.body.decode())
        assert body["away_temp"] == pytest.approx(15.0)
        assert body["eco_temp"] == pytest.approx(18.0)
        assert body["comfort_temp"] == pytest.approx(22.0)
        assert body["home_temp"] == pytest.approx(20.0)
        assert body["sleep_temp"] == pytest.approx(17.0)
        assert body["activity_temp"] == pytest.approx(21.0)

    @pytest.mark.asyncio
    async def test_handle_set_global_presets_all(self, mock_area_manager):
        """Test setting all global preset temperatures."""
        data = {
            "away_temp": 14.0,
            "eco_temp": 17.0,
            "comfort_temp": 23.0,
            "home_temp": 19.0,
            "sleep_temp": 16.0,
            "activity_temp": 22.0,
        }

        response = await handle_set_global_presets(mock_area_manager, data)

        assert response.status == 200
        body = json.loads(response.body.decode())
        assert body["success"] is True

        assert mock_area_manager.global_away_temp == pytest.approx(14.0)
        assert mock_area_manager.global_eco_temp == pytest.approx(17.0)
        assert mock_area_manager.global_comfort_temp == pytest.approx(23.0)
        assert mock_area_manager.global_home_temp == pytest.approx(19.0)
        assert mock_area_manager.global_sleep_temp == pytest.approx(16.0)
        assert mock_area_manager.global_activity_temp == pytest.approx(22.0)
        mock_area_manager.async_save.assert_called_once()

    @pytest.mark.asyncio
    async def test_handle_set_global_presets_partial(self, mock_area_manager):
        """Test setting only some preset temperatures."""
        data = {"eco_temp": 17.5, "comfort_temp": 21.5}

        response = await handle_set_global_presets(mock_area_manager, data)

        assert response.status == 200
        assert mock_area_manager.global_eco_temp == pytest.approx(17.5)
        assert mock_area_manager.global_comfort_temp == pytest.approx(21.5)
        # Others should remain unchanged
        assert mock_area_manager.global_away_temp == pytest.approx(15.0)

    @pytest.mark.asyncio
    async def test_handle_get_hysteresis(self, mock_area_manager):
        """Test getting hysteresis value."""
        response = await handle_get_hysteresis(mock_area_manager)

        assert response.status == 200
        body = json.loads(response.body.decode())
        assert body["hysteresis"] == pytest.approx(0.5)

    @pytest.mark.asyncio
    async def test_handle_set_hysteresis_value_success(
        self, mock_hass, mock_area_manager, mock_coordinator
    ):
        """Test setting hysteresis value."""
        data = {"hysteresis": 0.8}

        response = await handle_set_hysteresis_value(
            mock_hass, mock_area_manager, mock_coordinator, data
        )

        assert response.status == 200
        body = json.loads(response.body.decode())
        assert body["success"] is True

        assert mock_area_manager.hysteresis == pytest.approx(0.8)
        mock_area_manager.async_save.assert_called_once()
        mock_coordinator.async_request_refresh.assert_called_once()

    @pytest.mark.asyncio
    async def test_handle_set_hide_devices_panel_true(self, mock_area_manager):
        """Test setting hide_devices_panel to true."""
        from smart_heating.api_handlers.config import handle_set_hide_devices_panel

        data = {"hide_devices_panel": True}

        response = await handle_set_hide_devices_panel(mock_area_manager, data)

        assert response.status == 200
        body = json.loads(response.body.decode())
        assert body["success"] is True

        assert mock_area_manager.hide_devices_panel is True
        mock_area_manager.async_save.assert_called_once()

    @pytest.mark.asyncio
    async def test_handle_set_hide_devices_panel_false(self, mock_area_manager):
        """Test setting hide_devices_panel to false."""
        from smart_heating.api_handlers.config import handle_set_hide_devices_panel

        data = {"hide_devices_panel": False}

        response = await handle_set_hide_devices_panel(mock_area_manager, data)

        assert response.status == 200
        body = json.loads(response.body.decode())
        assert body["success"] is True

        assert mock_area_manager.hide_devices_panel is False
        mock_area_manager.async_save.assert_called_once()

    @pytest.mark.asyncio
    async def test_handle_set_hide_devices_panel_missing_value(self, mock_area_manager):
        """Test setting hide_devices_panel with missing value."""
        from smart_heating.api_handlers.config import handle_set_hide_devices_panel

        data = {}

        response = await handle_set_hide_devices_panel(mock_area_manager, data)

        assert response.status == 400
        body = json.loads(response.body.decode())
        assert "error" in body
        assert "Missing hide_devices_panel value" in body["error"]

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
    async def test_handle_set_advanced_control_config(self, mock_area_manager):
        data = {
            "advanced_control_enabled": True,
            "heating_curve_enabled": True,
            "pwm_enabled": True,
            "pid_enabled": True,
            "overshoot_protection_enabled": True,
            "default_heating_curve_coefficient": 1.25,
        }

        response = await handle_set_advanced_control_config(mock_area_manager, data)
        assert response.status == 200
        body = json.loads(response.body.decode())
        assert body["success"] is True
        assert mock_area_manager.advanced_control_enabled
        assert mock_area_manager.heating_curve_enabled
        assert mock_area_manager.pwm_enabled
        assert mock_area_manager.pid_enabled
        assert mock_area_manager.overshoot_protection_enabled
        assert mock_area_manager.default_heating_curve_coefficient == pytest.approx(1.25)
        mock_area_manager.async_save.assert_called_once()

    @pytest.mark.asyncio
    async def test_handle_set_advanced_control_config_invalid_coefficient(self, mock_area_manager):
        data = {"default_heating_curve_coefficient": "not-a-number"}
        response = await handle_set_advanced_control_config(mock_area_manager, data)
        assert response.status == 400

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
        assert body["success"] is True

        assert len(mock_area_manager.global_presence_sensors) == 2
        mock_area_manager.async_save.assert_called_once()

    @pytest.mark.asyncio
    async def test_handle_set_frost_protection_both(self, mock_area_manager):
        """Test setting frost protection with both enabled and temperature."""
        data = {"enabled": True, "temperature": 7.0}

        response = await handle_set_frost_protection(mock_area_manager, data)

        assert response.status == 200
        body = json.loads(response.body.decode())
        assert body["success"] is True
        assert body["enabled"] is True
        assert body["temperature"] == pytest.approx(7.0)

        assert mock_area_manager.frost_protection_enabled is True
        assert mock_area_manager.frost_protection_temp == pytest.approx(7.0)
        mock_area_manager.async_save.assert_called_once()

    @pytest.mark.asyncio
    async def test_handle_set_frost_protection_enabled_only(self, mock_area_manager):
        """Test setting only frost protection enabled flag."""
        data = {"enabled": True}

        response = await handle_set_frost_protection(mock_area_manager, data)

        assert response.status == 200
        assert mock_area_manager.frost_protection_enabled is True
        # Temperature should remain unchanged
        assert mock_area_manager.frost_protection_temp == pytest.approx(5.0)

    @pytest.mark.asyncio
    async def test_handle_set_frost_protection_temp_only(self, mock_area_manager):
        """Test setting only frost protection temperature."""
        data = {"temperature": 6.0}

        response = await handle_set_frost_protection(mock_area_manager, data)

        assert response.status == 200
        assert mock_area_manager.frost_protection_temp == pytest.approx(6.0)
        # Enabled should remain unchanged
        assert mock_area_manager.frost_protection_enabled is False

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
            "end_date": "2024-01-07",
        }
        mock_hass.data[DOMAIN]["vacation_manager"] = mock_vacation

        response = await handle_get_vacation_mode(mock_hass)

        assert response.status == 200
        body = json.loads(response.body.decode())
        assert body["enabled"] is True
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

        data = {"start_date": "2024-01-01", "end_date": "2024-01-07", "temperature": 15.0}
        response = await handle_enable_vacation_mode(mock_hass, data)

        assert response.status == 200
        body = json.loads(response.body.decode())
        assert body["enabled"] is True

        mock_vacation.async_enable.assert_called_once_with(
            start_date="2024-01-01", end_date="2024-01-07", temperature=15.0
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
        data = {"start_date": "2024-01-01", "end_date": "2024-01-07"}
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
            "end_date": "2024-01-01",  # End before start
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
        assert body["success"] is True

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
            {"sensor_id": "binary_sensor.smoke", "enabled": True}
        ]
        mock_area_manager.is_safety_alert_active.return_value = False

        response = await handle_get_safety_sensor(mock_area_manager)

        assert response.status == 200
        body = json.loads(response.body.decode())
        assert body["sensor_id"] == "binary_sensor.smoke"
        assert body["enabled"] is True
        assert body["alert_active"] is False

    @pytest.mark.asyncio
    async def test_handle_get_safety_sensor_without_sensor(self, mock_area_manager):
        """Test getting safety sensor when none configured."""
        mock_area_manager.get_safety_sensors.return_value = []

        response = await handle_get_safety_sensor(mock_area_manager)

        assert response.status == 200
        body = json.loads(response.body.decode())
        assert body["sensor_id"] is None
        assert body["enabled"] is False
        assert body["alert_active"] is False

    @pytest.mark.asyncio
    async def test_handle_set_safety_sensor_success(self, mock_hass, mock_area_manager):
        """Test setting safety sensor."""
        mock_safety = MagicMock()
        mock_safety.async_reconfigure = AsyncMock()
        mock_hass.data[DOMAIN]["safety_monitor"] = mock_safety

        data = {"sensor_id": "binary_sensor.smoke", "alert_value": "on"}
        response = await handle_set_safety_sensor(mock_hass, mock_area_manager, data)

        assert response.status == 200
        body = json.loads(response.body.decode())
        assert body["success"] is True
        assert body["sensor_id"] == "binary_sensor.smoke"

        mock_area_manager.clear_safety_sensors.assert_called_once()
        mock_area_manager.add_safety_sensor.assert_called_once_with(
            sensor_id="binary_sensor.smoke",
            attribute="state",
            alert_value="on",
            enabled=True,
        )
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
        assert body["success"] is True

        mock_area_manager.clear_safety_sensors.assert_called_once()
        mock_area_manager.async_save.assert_called_once()
        mock_safety.async_reconfigure.assert_called_once()
        mock_hass.bus.async_fire.assert_called_once()

    @pytest.mark.asyncio
    async def test_handle_set_hvac_mode_success(self, mock_hass, mock_area_manager):
        """Test setting HVAC mode."""
        mock_coordinator = MagicMock()
        mock_coordinator.data = {}
        mock_coordinator.async_request_refresh = AsyncMock()
        mock_hass.data[DOMAIN]["test_coordinator"] = mock_coordinator

        data = {"hvac_mode": "cool"}
        response = await handle_set_hvac_mode(mock_hass, mock_area_manager, "living_room", data)

        assert response.status == 200
        body = json.loads(response.body.decode())
        assert body["success"] is True
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
