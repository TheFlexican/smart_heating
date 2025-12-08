"""Tests for climate controller.

This module is complex (420 statements). Tests focus on core heating logic,
device control, sensor handling, and temperature management.
"""

import json
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, patch, call

import pytest

from smart_heating.climate_controller import ClimateController


@pytest.fixture
def mock_hass():
    """Create a mock Home Assistant instance."""
    hass = MagicMock()
    hass.data = {
        "smart_heating": {
            "history": MagicMock(
                async_record_temperature=AsyncMock(),
                async_save=AsyncMock()
            ),
            "vacation_manager": None,
        }
    }
    hass.states = MagicMock()
    hass.services = MagicMock()
    hass.services.async_call = AsyncMock()
    return hass


@pytest.fixture
def mock_area_manager():
    """Create a mock area manager."""
    manager = MagicMock()
    manager.async_save = AsyncMock()
    manager.frost_protection_enabled = False
    manager.frost_protection_temp = 7.0
    manager.opentherm_enabled = False
    manager.opentherm_gateway_id = None
    manager.trv_temp_offset = 2.0
    manager.trv_heating_temp = 25.0
    manager.trv_idle_temp = 10.0
    manager.global_presence_sensors = []
    manager.get_all_areas = MagicMock(return_value={})
    return manager


@pytest.fixture
def mock_area_logger():
    """Create mock area logger."""
    logger = MagicMock()
    logger.log_event = MagicMock()
    return logger


@pytest.fixture
def mock_area():
    """Create a mock area."""
    area = MagicMock()
    area.area_id = "living_room"
    area.enabled = True
    area.manual_override = False
    area.target_temperature = 21.0
    area.current_temperature = 19.0
    area.preset_mode = "home"
    area.boost_mode_active = False
    area.hysteresis_override = None
    area.window_sensors = []
    area.presence_sensors = []
    area.use_global_presence = False
    area.auto_preset_enabled = False
    area.auto_preset_home = "home"
    area.auto_preset_away = "away"
    area.window_is_open = False
    area.presence_detected = False
    area.state = "idle"
    area.shutdown_switches_when_idle = True
    area.weather_entity_id = None
    area.devices = {}
    area.get_thermostats = MagicMock(return_value=[])
    area.get_switches = MagicMock(return_value=[])
    area.get_valves = MagicMock(return_value=[])
    area.get_temperature_sensors = MagicMock(return_value=[])
    area.get_effective_target_temperature = MagicMock(return_value=21.0)
    area.check_boost_expiry = MagicMock()
    return area


@pytest.fixture
def controller(mock_hass, mock_area_manager, mock_area_logger):
    """Create a climate controller instance."""
    ctrl = ClimateController(mock_hass, mock_area_manager, learning_engine=None)
    # Initialize handlers via set_area_logger
    ctrl.set_area_logger(mock_area_logger)
    return ctrl


class TestTemperatureMethods:
    """Tests for temperature conversion and reading methods."""

    def test_convert_fahrenheit_to_celsius(self, controller):
        """Test Fahrenheit to Celsius conversion."""
        # 32°F = 0°C
        assert controller._convert_fahrenheit_to_celsius(32.0) == pytest.approx(0.0, abs=0.1)
        # 212°F = 100°C
        assert controller._convert_fahrenheit_to_celsius(212.0) == pytest.approx(100.0, abs=0.1)
        # 68°F = 20°C
        assert controller._convert_fahrenheit_to_celsius(68.0) == pytest.approx(20.0, abs=0.1)

    def test_get_temperature_from_sensor_celsius(self, controller, mock_hass):
        """Test getting temperature from sensor in Celsius."""
        state = MagicMock()
        state.state = "21.5"
        state.attributes = {"unit_of_measurement": "°C"}
        mock_hass.states.get.return_value = state
        
        temp = controller._get_temperature_from_sensor("sensor.temp")
        assert temp == 21.5

    def test_get_temperature_from_sensor_fahrenheit(self, controller, mock_hass):
        """Test getting temperature from sensor in Fahrenheit."""
        state = MagicMock()
        state.state = "68"  # 68°F = 20°C
        state.attributes = {"unit_of_measurement": "°F"}
        mock_hass.states.get.return_value = state
        
        temp = controller._get_temperature_from_sensor("sensor.temp")
        assert temp == pytest.approx(20.0, abs=0.1)

    def test_get_temperature_from_sensor_unavailable(self, controller, mock_hass):
        """Test handling unavailable sensor."""
        state = MagicMock()
        state.state = "unavailable"
        mock_hass.states.get.return_value = state
        
        temp = controller._get_temperature_from_sensor("sensor.temp")
        assert temp is None

    def test_get_temperature_from_sensor_invalid(self, controller, mock_hass):
        """Test handling invalid sensor value."""
        state = MagicMock()
        state.state = "not_a_number"
        state.attributes = {"unit_of_measurement": "°C"}
        mock_hass.states.get.return_value = state
        
        temp = controller._get_temperature_from_sensor("sensor.temp")
        assert temp is None

    def test_get_temperature_from_thermostat_success(self, controller, mock_hass):
        """Test getting temperature from thermostat."""
        state = MagicMock()
        state.state = "idle"
        state.attributes = {
            "current_temperature": 21.5,
            "unit_of_measurement": "°C"
        }
        mock_hass.states.get.return_value = state
        
        temp = controller._get_temperature_from_thermostat("climate.thermostat")
        assert temp == 21.5

    def test_get_temperature_from_thermostat_fahrenheit(self, controller, mock_hass):
        """Test getting temperature from thermostat in Fahrenheit."""
        state = MagicMock()
        state.state = "heating"
        state.attributes = {
            "current_temperature": 68.0,  # 68°F = 20°C
            "unit_of_measurement": "°F"
        }
        mock_hass.states.get.return_value = state
        
        temp = controller._get_temperature_from_thermostat("climate.thermostat")
        assert temp == pytest.approx(20.0, abs=0.1)

    def test_collect_area_temperatures(self, controller, mock_hass, mock_area):
        """Test collecting temperatures from multiple sources."""
        # Mock temperature sensor
        sensor_state = MagicMock()
        sensor_state.state = "20.5"
        sensor_state.attributes = {"unit_of_measurement": "°C"}
        
        # Mock thermostat
        thermostat_state = MagicMock()
        thermostat_state.state = "heating"
        thermostat_state.attributes = {
            "current_temperature": 21.0,
            "unit_of_measurement": "°C"
        }
        
        mock_hass.states.get.side_effect = lambda entity_id: {
            "sensor.temp": sensor_state,
            "climate.thermostat": thermostat_state,
        }.get(entity_id)
        
        mock_area.get_temperature_sensors.return_value = ["sensor.temp"]
        mock_area.get_thermostats.return_value = ["climate.thermostat"]
        
        temps = controller._collect_area_temperatures(mock_area)
        assert len(temps) == 2
        assert 20.5 in temps
        assert 21.0 in temps

    @pytest.mark.asyncio
    async def test_async_update_area_temperatures(self, controller, mock_hass, mock_area_manager, mock_area):
        """Test updating temperatures for all areas."""
        sensor_state = MagicMock()
        sensor_state.state = "21.0"
        sensor_state.attributes = {"unit_of_measurement": "°C"}
        mock_hass.states.get.return_value = sensor_state
        
        mock_area.get_temperature_sensors.return_value = ["sensor.temp"]
        mock_area.get_thermostats.return_value = []
        mock_area_manager.get_all_areas.return_value = {"living_room": mock_area}
        
        await controller.async_update_area_temperatures()
        
        assert mock_area.current_temperature == 21.0


class TestWindowSensors:
    """Tests for window sensor handling."""

    def test_check_window_sensors_no_sensors(self, controller, mock_area):
        """Test checking windows when no sensors configured."""
        mock_area.window_sensors = []
        
        is_open = controller._check_window_sensors("living_room", mock_area)
        assert is_open is False

    def test_check_window_sensors_all_closed(self, controller, mock_hass, mock_area):
        """Test checking windows when all are closed."""
        state = MagicMock()
        state.state = "off"
        mock_hass.states.get.return_value = state
        
        mock_area.window_sensors = [{"entity_id": "binary_sensor.window"}]
        
        is_open = controller._check_window_sensors("living_room", mock_area)
        assert is_open is False

    def test_check_window_sensors_one_open(self, controller, mock_hass, mock_area):
        """Test checking windows when one is open."""
        state = MagicMock()
        state.state = "on"
        mock_hass.states.get.return_value = state
        
        mock_area.window_sensors = [{"entity_id": "binary_sensor.window"}]
        
        is_open = controller._check_window_sensors("living_room", mock_area)
        assert is_open is True

    def test_log_window_state_change_to_open(self, controller, mock_area):
        """Test logging window opening."""
        mock_area.window_is_open = False
        
        controller._log_window_state_change("living_room", mock_area, True)
        
        assert mock_area.window_is_open is True

    def test_log_window_state_change_to_closed(self, controller, mock_area):
        """Test logging window closing."""
        mock_area.window_is_open = True
        
        controller._log_window_state_change("living_room", mock_area, False)
        
        assert mock_area.window_is_open is False


class TestPresenceSensors:
    """Tests for presence sensor handling."""

    def test_get_presence_sensors_area_specific(self, controller, mock_area):
        """Test getting area-specific presence sensors."""
        mock_area.use_global_presence = False
        mock_area.presence_sensors = [{"entity_id": "person.john"}]
        
        sensors = controller._get_presence_sensors_for_area(mock_area)
        assert sensors == [{"entity_id": "person.john"}]

    def test_get_presence_sensors_global(self, controller, mock_area_manager, mock_area):
        """Test getting global presence sensors."""
        mock_area.use_global_presence = True
        mock_area_manager.global_presence_sensors = [{"entity_id": "person.jane"}]
        
        sensors = controller._get_presence_sensors_for_area(mock_area)
        assert sensors == [{"entity_id": "person.jane"}]

    def test_check_presence_sensors_no_sensors(self, controller):
        """Test checking presence when no sensors configured."""
        is_present = controller._check_presence_sensors("living_room", [])
        assert is_present is False

    def test_check_presence_sensors_nobody_home(self, controller, mock_hass):
        """Test checking presence when nobody is home."""
        state = MagicMock()
        state.state = "not_home"
        mock_hass.states.get.return_value = state
        
        is_present = controller._check_presence_sensors("living_room", [{"entity_id": "person.john"}])
        assert is_present is False

    def test_check_presence_sensors_someone_home(self, controller, mock_hass):
        """Test checking presence when someone is home."""
        state = MagicMock()
        state.state = "home"
        mock_hass.states.get.return_value = state
        
        is_present = controller._check_presence_sensors("living_room", [{"entity_id": "person.john"}])
        assert is_present is True

    @pytest.mark.asyncio
    async def test_handle_auto_preset_change_disabled(self, controller, mock_area, mock_area_manager):
        """Test auto preset change when disabled."""
        mock_area.auto_preset_enabled = False
        
        await controller._handle_auto_preset_change("living_room", mock_area, True)
        
        # Preset should not change
        assert mock_area.preset_mode == "home"
        mock_area_manager.async_save.assert_not_called()

    @pytest.mark.asyncio
    async def test_handle_auto_preset_change_to_away(self, controller, mock_area, mock_area_manager):
        """Test auto preset change to away when no presence."""
        mock_area.auto_preset_enabled = True
        mock_area.auto_preset_home = "home"
        mock_area.auto_preset_away = "away"
        mock_area.preset_mode = "home"
        
        await controller._handle_auto_preset_change("living_room", mock_area, False)
        
        assert mock_area.preset_mode == "away"
        mock_area_manager.async_save.assert_called_once()

    @pytest.mark.asyncio
    async def test_handle_auto_preset_change_to_home(self, controller, mock_area, mock_area_manager):
        """Test auto preset change to home when presence detected."""
        mock_area.auto_preset_enabled = True
        mock_area.auto_preset_home = "home"
        mock_area.auto_preset_away = "away"
        mock_area.preset_mode = "away"
        
        await controller._handle_auto_preset_change("living_room", mock_area, True)
        
        assert mock_area.preset_mode == "home"
        mock_area_manager.async_save.assert_called_once()


class TestFrostProtection:
    """Tests for frost protection."""

    def test_apply_frost_protection_disabled(self, controller, mock_area_manager):
        """Test frost protection when disabled."""
        mock_area_manager.frost_protection_enabled = False
        
        result = controller._apply_frost_protection("living_room", 10.0)
        assert result == 10.0

    def test_apply_frost_protection_above_minimum(self, controller, mock_area_manager):
        """Test frost protection when temperature is above minimum."""
        mock_area_manager.frost_protection_enabled = True
        mock_area_manager.frost_protection_temp = 7.0
        
        result = controller._apply_frost_protection("living_room", 15.0)
        assert result == 15.0

    def test_apply_frost_protection_below_minimum(self, controller, mock_area_manager):
        """Test frost protection when temperature is below minimum."""
        mock_area_manager.frost_protection_enabled = True
        mock_area_manager.frost_protection_temp = 7.0
        
        result = controller._apply_frost_protection("living_room", 5.0)
        assert result == 7.0

    def test_apply_frost_protection_vacation_mode(self, controller, mock_hass, mock_area_manager):
        """Test frost protection with vacation mode override."""
        mock_area_manager.frost_protection_enabled = False
        
        vacation_manager = MagicMock()
        vacation_manager.is_active.return_value = True
        vacation_manager.get_min_temperature.return_value = 10.0
        mock_hass.data["smart_heating"]["vacation_manager"] = vacation_manager
        
        result = controller._apply_frost_protection("living_room", 8.0)
        assert result == 10.0


class TestVacationMode:
    """Tests for vacation mode handling."""

    def test_apply_vacation_mode_not_active(self, controller, mock_hass, mock_area):
        """Test vacation mode when not active."""
        vacation_manager = MagicMock()
        vacation_manager.is_active.return_value = False
        mock_hass.data["smart_heating"]["vacation_manager"] = vacation_manager
        
        mock_area.preset_mode = "home"
        controller._apply_vacation_mode("living_room", mock_area)
        
        assert mock_area.preset_mode == "home"

    def test_apply_vacation_mode_active(self, controller, mock_hass, mock_area):
        """Test vacation mode when active."""
        vacation_manager = MagicMock()
        vacation_manager.is_active.return_value = True
        vacation_manager.get_preset_mode.return_value = "away"
        mock_hass.data["smart_heating"]["vacation_manager"] = vacation_manager
        
        mock_area.preset_mode = "home"
        controller._apply_vacation_mode("living_room", mock_area)
        
        assert mock_area.preset_mode == "away"


class TestDeviceControl:
    """Tests for device control methods."""

    def test_is_any_thermostat_actively_heating_true(self, controller, mock_hass, mock_area):
        """Test detecting active heating."""
        state = MagicMock()
        state.attributes = {"hvac_action": "heating"}
        mock_hass.states.get.return_value = state
        
        mock_area.get_thermostats.return_value = ["climate.thermostat"]
        
        is_heating = controller._is_any_thermostat_actively_heating(mock_area)
        assert is_heating is True

    def test_is_any_thermostat_actively_heating_false(self, controller, mock_hass, mock_area):
        """Test detecting no active heating."""
        state = MagicMock()
        state.attributes = {"hvac_action": "idle"}
        mock_hass.states.get.return_value = state
        
        mock_area.get_thermostats.return_value = ["climate.thermostat"]
        
        is_heating = controller._is_any_thermostat_actively_heating(mock_area)
        assert is_heating is False

    @pytest.mark.asyncio
    async def test_async_control_thermostats_heating(self, controller, mock_hass, mock_area):
        """Test controlling thermostats to heat."""
        mock_area.get_thermostats.return_value = ["climate.living_room"]
        
        await controller._async_control_thermostats(mock_area, True, 21.0)
        
        mock_hass.services.async_call.assert_called_once_with(
            "climate",
            "set_temperature",
            {
                "entity_id": "climate.living_room",
                "temperature": 21.0,
            },
            blocking=False,
        )

    @pytest.mark.asyncio
    async def test_async_control_thermostats_no_duplicate_call(self, controller, mock_hass, mock_area):
        """Test avoiding duplicate thermostat calls."""
        mock_area.get_thermostats.return_value = ["climate.living_room"]
        
        # First call
        await controller._async_control_thermostats(mock_area, True, 21.0)
        assert mock_hass.services.async_call.call_count == 1
        
        # Second call with same temperature
        await controller._async_control_thermostats(mock_area, True, 21.0)
        # Should not call again (cached)
        assert mock_hass.services.async_call.call_count == 1

    @pytest.mark.asyncio
    async def test_async_control_thermostats_temperature_change(self, controller, mock_hass, mock_area):
        """Test thermostat update when temperature changes."""
        mock_area.get_thermostats.return_value = ["climate.living_room"]
        
        # First call
        await controller._async_control_thermostats(mock_area, True, 21.0)
        assert mock_hass.services.async_call.call_count == 1
        
        # Second call with different temperature
        await controller._async_control_thermostats(mock_area, True, 22.0)
        # Should call again (temperature changed)
        assert mock_hass.services.async_call.call_count == 2

    @pytest.mark.asyncio
    async def test_async_control_switches_turn_on(self, controller, mock_hass, mock_area):
        """Test turning on switches."""
        mock_area.get_switches.return_value = ["switch.pump"]
        
        await controller._async_control_switches(mock_area, True)
        
        mock_hass.services.async_call.assert_called_once_with(
            "switch",
            "turn_on",
            {"entity_id": "switch.pump"},
            blocking=False,
        )

    @pytest.mark.asyncio
    async def test_async_control_switches_turn_off(self, controller, mock_hass, mock_area):
        """Test turning off switches when shutdown allowed."""
        state = MagicMock()
        state.attributes = {"hvac_action": "idle"}
        mock_hass.states.get.return_value = state
        
        mock_area.get_switches.return_value = ["switch.pump"]
        mock_area.get_thermostats.return_value = ["climate.thermostat"]
        mock_area.shutdown_switches_when_idle = True
        
        await controller._async_control_switches(mock_area, False)
        
        mock_hass.services.async_call.assert_called_once_with(
            "switch",
            "turn_off",
            {"entity_id": "switch.pump"},
            blocking=False,
        )

    @pytest.mark.asyncio
    async def test_async_control_switches_keep_on_when_thermostat_heating(self, controller, mock_hass, mock_area):
        """Test keeping switches on when thermostat still heating."""
        state = MagicMock()
        state.attributes = {"hvac_action": "heating"}
        mock_hass.states.get.return_value = state
        
        mock_area.get_switches.return_value = ["switch.pump"]
        mock_area.get_thermostats.return_value = ["climate.thermostat"]
        
        await controller._async_control_switches(mock_area, False)
        
        # Should turn ON (keep switch on because thermostat still heating)
        mock_hass.services.async_call.assert_called_once_with(
            "switch",
            "turn_on",
            {"entity_id": "switch.pump"},
            blocking=False,
        )

    @pytest.mark.asyncio
    async def test_async_control_valves_number_entity_open(self, controller, mock_hass, mock_area):
        """Test opening valve via number entity."""
        state = MagicMock()
        state.attributes = {"min": 0, "max": 100}
        mock_hass.states.get.return_value = state
        
        mock_area.get_valves.return_value = ["number.valve_position"]
        
        await controller._async_control_valves(mock_area, True, 21.0)
        
        mock_hass.services.async_call.assert_called_once_with(
            "number",
            "set_value",
            {
                "entity_id": "number.valve_position",
                "value": 100,
            },
            blocking=False,
        )

    @pytest.mark.asyncio
    async def test_async_control_valves_number_entity_close(self, controller, mock_hass, mock_area):
        """Test closing valve via number entity."""
        state = MagicMock()
        state.attributes = {"min": 0, "max": 100}
        mock_hass.states.get.return_value = state
        
        mock_area.get_valves.return_value = ["number.valve_position"]
        
        await controller._async_control_valves(mock_area, False, 21.0)
        
        mock_hass.services.async_call.assert_called_once_with(
            "number",
            "set_value",
            {
                "entity_id": "number.valve_position",
                "value": 0,
            },
            blocking=False,
        )

    @pytest.mark.asyncio
    async def test_async_get_outdoor_temperature_success(self, controller, mock_hass, mock_area):
        """Test getting outdoor temperature."""
        state = MagicMock()
        state.state = "15.0"
        state.attributes = {"unit_of_measurement": "°C"}
        mock_hass.states.get.return_value = state
        
        mock_area.weather_entity_id = "weather.home"
        
        temp = await controller._async_get_outdoor_temperature(mock_area)
        assert temp == 15.0

    @pytest.mark.asyncio
    async def test_async_get_outdoor_temperature_no_entity(self, controller, mock_area):
        """Test getting outdoor temperature when no entity configured."""
        mock_area.weather_entity_id = None
        
        temp = await controller._async_get_outdoor_temperature(mock_area)
        assert temp is None

    @pytest.mark.asyncio
    async def test_async_control_opentherm_gateway_heating(self, controller, mock_hass, mock_area_manager):
        """Test controlling OpenTherm gateway when heating."""
        mock_area_manager.opentherm_enabled = True
        mock_area_manager.opentherm_gateway_id = "climate.boiler"
        
        await controller._async_control_opentherm_gateway(True, 21.0)
        
        # Should set to target + 20°C overhead
        mock_hass.services.async_call.assert_called_once_with(
            "climate",
            "set_temperature",
            {
                "entity_id": "climate.boiler",
                "temperature": 41.0,  # 21 + 20
            },
            blocking=False,
        )

    @pytest.mark.asyncio
    async def test_async_control_opentherm_gateway_off(self, controller, mock_hass, mock_area_manager):
        """Test turning off OpenTherm gateway when no heating."""
        mock_area_manager.opentherm_enabled = True
        mock_area_manager.opentherm_gateway_id = "climate.boiler"
        
        await controller._async_control_opentherm_gateway(False, 0.0)
        
        mock_hass.services.async_call.assert_called_once_with(
            "climate",
            "turn_off",
            {"entity_id": "climate.boiler"},
            blocking=False,
        )

    @pytest.mark.asyncio
    async def test_async_control_opentherm_gateway_disabled(self, controller, mock_hass, mock_area_manager):
        """Test OpenTherm gateway when disabled."""
        mock_area_manager.opentherm_enabled = False
        
        await controller._async_control_opentherm_gateway(True, 21.0)
        
        mock_hass.services.async_call.assert_not_called()


class TestValveCapabilities:
    """Tests for valve capability detection."""

    def test_get_valve_capability_number_entity(self, controller, mock_hass):
        """Test detecting number entity valve capabilities."""
        state = MagicMock()
        state.attributes = {"min": 0, "max": 100}
        mock_hass.states.get.return_value = state
        
        caps = controller._get_valve_capability("number.valve_position")
        
        assert caps["supports_position"] is True
        assert caps["position_min"] == 0
        assert caps["position_max"] == 100
        assert caps["entity_domain"] == "number"

    def test_get_valve_capability_climate_with_position(self, controller, mock_hass):
        """Test detecting climate entity with position attribute."""
        state = MagicMock()
        state.attributes = {"position": 50, "temperature": 21.0}
        mock_hass.states.get.return_value = state
        
        caps = controller._get_valve_capability("climate.trv")
        
        assert caps["supports_position"] is True
        assert caps["supports_temperature"] is True
        assert caps["entity_domain"] == "climate"

    def test_get_valve_capability_climate_temp_only(self, controller, mock_hass):
        """Test detecting climate entity with temperature control only."""
        state = MagicMock()
        state.attributes = {"temperature": 21.0}
        mock_hass.states.get.return_value = state
        
        caps = controller._get_valve_capability("climate.trv")
        
        assert caps["supports_position"] is False
        assert caps["supports_temperature"] is True

    def test_get_valve_capability_cached(self, controller, mock_hass):
        """Test that capabilities are cached."""
        state = MagicMock()
        state.attributes = {"min": 0, "max": 100}
        mock_hass.states.get.return_value = state
        
        # First call
        caps1 = controller._get_valve_capability("number.valve")
        # Second call
        caps2 = controller._get_valve_capability("number.valve")
        
        assert caps1 == caps2
        # Should only query HA once (cached)
        assert mock_hass.states.get.call_count == 1


class TestHeatingCycle:
    """Tests for heating control cycle."""

    @pytest.mark.asyncio
    async def test_async_prepare_heating_cycle(self, controller, mock_hass, mock_area_manager):
        """Test preparing for heating cycle."""
        mock_area_manager.get_all_areas.return_value = {}
        
        should_record, history = await controller._async_prepare_heating_cycle()
        
        # First call: counter = 1, should not record
        assert should_record is False
        assert history is not None

    @pytest.mark.asyncio
    async def test_async_handle_disabled_area(self, controller, mock_hass, mock_area):
        """Test handling disabled area."""
        history = mock_hass.data["smart_heating"]["history"]
        mock_area.current_temperature = 20.0
        mock_area.state = "idle"  # Initial state
        
        await controller._async_handle_disabled_area("living_room", mock_area, history, True)
        
        assert mock_area.state == "off"
        # History is recorded BEFORE state is changed to "off", so it uses the current state
        history.async_record_temperature.assert_called_once_with(
            "living_room", 20.0, 21.0, "idle"
        )

    @pytest.mark.asyncio
    async def test_async_handle_manual_override(self, controller, mock_hass, mock_area):
        """Test handling manual override mode."""
        state = MagicMock()
        state.attributes = {"hvac_action": "idle"}
        mock_hass.states.get.return_value = state
        
        mock_area.devices = {"climate.thermostat": {"type": "thermostat"}}
        mock_area.get_switches.return_value = []
        
        await controller._async_handle_manual_override("living_room", mock_area)
        
        assert mock_area.state == "manual"
