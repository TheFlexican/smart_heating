"""Tests for Area model."""

from __future__ import annotations

from datetime import datetime
from unittest.mock import Mock

import pytest
from smart_heating.models.area import Area
from smart_heating.models.schedule import Schedule

from tests.unit.const import (
    PRESET_COMFORT,
    PRESET_ECO,
    TEST_AREA_ID,
    TEST_AREA_NAME,
    TEST_CURRENT_TEMP,
    TEST_ENTITY_ID,
    TEST_TEMPERATURE,
)


class TestAreaModel:
    """Test Area model."""

    def test_area_init(self):
        """Test Area initialization."""
        area = Area(
            area_id=TEST_AREA_ID,
            name=TEST_AREA_NAME,
            target_temperature=TEST_TEMPERATURE,
        )

        assert area.area_id == TEST_AREA_ID
        assert area.name == TEST_AREA_NAME
        assert area.target_temperature == TEST_TEMPERATURE
        assert area.current_temperature is None
        assert area.enabled is True
        assert area.preset_mode == "none"
        assert area.hvac_mode == "heat"
        assert area.devices == {}  # Dict, not list
        assert area.window_sensors == []
        assert area.presence_sensors == []

    def test_area_to_dict(self):
        """Test converting Area to dictionary."""
        area = Area(
            area_id=TEST_AREA_ID,
            name=TEST_AREA_NAME,
            target_temperature=TEST_TEMPERATURE,
        )
        area_dict = area.to_dict()

        assert area_dict["area_id"] == TEST_AREA_ID
        assert area_dict["area_name"] == TEST_AREA_NAME
        assert area_dict["target_temperature"] == TEST_TEMPERATURE
        assert area_dict["enabled"] is True

    def test_from_dict_legacy_switch_shutdown(self):
        """Test that legacy `switch_shutdown_enabled` key is ignored when loading area data."""
        data = {
            "area_id": TEST_AREA_ID,
            "area_name": TEST_AREA_NAME,
            "target_temperature": TEST_TEMPERATURE,
            "enabled": True,
            "switch_shutdown_enabled": False,
        }

        area = Area.from_dict(data)
        # Legacy key should be ignored; default remains True
        assert area.shutdown_switches_when_idle is True

    def test_area_device_management(self):
        """Test adding and removing devices."""
        area = Area(
            area_id=TEST_AREA_ID,
            name=TEST_AREA_NAME,
            target_temperature=TEST_TEMPERATURE,
        )

        # Add device
        area.add_device(TEST_ENTITY_ID, "thermostat")
        assert TEST_ENTITY_ID in area.devices
        assert len(area.devices) == 1
        assert area.devices[TEST_ENTITY_ID]["type"] == "thermostat"

        # Remove device
        area.remove_device(TEST_ENTITY_ID)
        assert TEST_ENTITY_ID not in area.devices
        assert len(area.devices) == 0

    def test_area_get_thermostats(self):
        """Test getting thermostat devices."""
        area = Area(
            area_id=TEST_AREA_ID,
            name=TEST_AREA_NAME,
            target_temperature=TEST_TEMPERATURE,
        )

        area.add_device("climate.thermostat1", "thermostat")
        area.add_device("climate.thermostat2", "thermostat")
        area.add_device("sensor.temp", "temperature_sensor")

        thermostats = area.get_thermostats()
        assert len(thermostats) == 2
        assert "climate.thermostat1" in thermostats
        assert "climate.thermostat2" in thermostats

        assert "climate.thermostat2" in thermostats

    def test_area_window_sensor_management(self):
        """Test window sensor management."""
        area = Area(
            area_id=TEST_AREA_ID,
            name=TEST_AREA_NAME,
            target_temperature=TEST_TEMPERATURE,
        )

        # Add window sensor
        area.add_window_sensor(
            "binary_sensor.window", action_when_open="reduce_temperature", temp_drop=2.0
        )
        assert len(area.window_sensors) == 1
        assert area.window_sensors[0]["entity_id"] == "binary_sensor.window"
        assert area.window_sensors[0]["action_when_open"] == "reduce_temperature"
        assert area.window_sensors[0]["temp_drop"] == pytest.approx(2.0)

        # Remove window sensor
        area.remove_window_sensor("binary_sensor.window")
        assert len(area.window_sensors) == 0

    def test_area_presence_sensor_management(self):
        """Test presence sensor management."""
        area = Area(
            area_id=TEST_AREA_ID,
            name=TEST_AREA_NAME,
            target_temperature=TEST_TEMPERATURE,
        )

        # Add presence sensor
        area.add_presence_sensor("binary_sensor.presence")
        assert len(area.presence_sensors) == 1
        assert area.presence_sensors[0]["entity_id"] == "binary_sensor.presence"

        # Remove presence sensor
        area.remove_presence_sensor("binary_sensor.presence")
        assert len(area.presence_sensors) == 0

    def test_area_schedule_management(self):
        """Test schedule management."""
        area = Area(
            area_id=TEST_AREA_ID,
            name=TEST_AREA_NAME,
            target_temperature=TEST_TEMPERATURE,
        )

        # Create a schedule
        schedule = Schedule(
            schedule_id="schedule_1",
            time="07:00",
            temperature=21.0,
                days=[0, "tuesday"],
        )

        # Add schedule
        area.add_schedule(schedule)
        assert len(area.schedules) == 1
        assert "schedule_1" in area.schedules

        # Remove schedule
        area.remove_schedule("schedule_1")
        assert len(area.schedules) == 0

    def test_area_boost_mode(self):
        """Test boost mode functionality."""
        area = Area(
            area_id=TEST_AREA_ID,
            name=TEST_AREA_NAME,
            target_temperature=TEST_TEMPERATURE,
        )

        # Set boost mode
        area.set_boost_mode(duration=60, temp=25.0)

        assert area.boost_mode_active is True
        assert area.boost_duration == 60
        assert area.boost_temp == pytest.approx(25.0)
        assert area.boost_end_time is not None
        assert area.preset_mode == "boost"

        # Cancel boost mode
        area.cancel_boost_mode()
        assert area.boost_mode_active is False
        assert area.boost_end_time is None
        assert area.preset_mode == "none"

    def test_area_preset_mode_change(self):
        """Test changing preset mode."""
        area = Area(
            area_id=TEST_AREA_ID,
            name=TEST_AREA_NAME,
            target_temperature=TEST_TEMPERATURE,
        )

        area.set_preset_mode(PRESET_ECO)
        assert area.preset_mode == PRESET_ECO

        area.set_preset_mode(PRESET_COMFORT)
        assert area.preset_mode == PRESET_COMFORT

    def test_area_current_temperature_property(self):
        """Test current temperature property."""
        area = Area(
            area_id=TEST_AREA_ID,
            name=TEST_AREA_NAME,
            target_temperature=TEST_TEMPERATURE,
        )

        # Set via property
        area.current_temperature = TEST_CURRENT_TEMP
        assert area.current_temperature == pytest.approx(TEST_CURRENT_TEMP)

        area.current_temperature = 19.5
        assert area.current_temperature == pytest.approx(19.5)

    def test_area_get_preset_temperature(self):
        """Test getting preset temperature."""
        area = Area(
            area_id=TEST_AREA_ID,
            name=TEST_AREA_NAME,
            target_temperature=TEST_TEMPERATURE,
        )

        # Set preset mode and check temperature
        area.preset_mode = "eco"
        temp = area.get_preset_temperature()
        assert temp == area.eco_temp

        area.preset_mode = "comfort"
        temp = area.get_preset_temperature()
        assert temp == area.comfort_temp

    def test_area_global_preset_flags(self):
        """Test global preset usage flags."""
        area = Area(
            area_id=TEST_AREA_ID,
            name=TEST_AREA_NAME,
            target_temperature=TEST_TEMPERATURE,
        )

        # Default should use global presets
        assert area.use_global_eco is True
        assert area.use_global_comfort is True
        assert area.use_global_home is True

        # Change to custom presets
        area.use_global_eco = False
        assert area.use_global_eco is False


class TestAreaDeviceTypes:
    """Test area device type getter methods."""

    def test_get_temperature_sensors(self):
        """Test getting temperature sensor devices."""
        area = Area(TEST_AREA_ID, TEST_AREA_NAME)

        area.add_device("sensor.temp1", "temperature_sensor")
        area.add_device("sensor.temp2", "temperature_sensor")
        area.add_device("climate.thermostat", "thermostat")

        sensors = area.get_temperature_sensors()

        assert len(sensors) == 2
        assert "sensor.temp1" in sensors
        assert "sensor.temp2" in sensors

    def test_get_opentherm_gateways(self):
        """Test getting OpenTherm gateway devices."""
        area = Area(TEST_AREA_ID, TEST_AREA_NAME)

        area.add_device("climate.otgw1", "opentherm_gateway")
        area.add_device("climate.otgw2", "opentherm_gateway")
        area.add_device("climate.thermostat", "thermostat")

        gateways = area.get_opentherm_gateways()

        assert len(gateways) == 2
        assert "climate.otgw1" in gateways
        assert "climate.otgw2" in gateways

    def test_get_switches(self):
        """Test getting switch devices."""
        area = Area(TEST_AREA_ID, TEST_AREA_NAME)

        area.add_device("switch.pump1", "switch")
        area.add_device("switch.relay1", "switch")
        area.add_device("climate.thermostat", "thermostat")

        switches = area.get_switches()

        assert len(switches) == 2
        assert "switch.pump1" in switches
        assert "switch.relay1" in switches

    def test_get_valves(self):
        """Test getting valve devices."""
        area = Area(TEST_AREA_ID, TEST_AREA_NAME)

        area.add_device("number.valve1", "valve")
        area.add_device("number.valve2", "valve")
        area.add_device("climate.thermostat", "thermostat")

        valves = area.get_valves()

        assert len(valves) == 2
        assert "number.valve1" in valves
        assert "number.valve2" in valves


class TestAreaWindowSensors:
    """Test window sensor functionality."""

    def test_add_window_sensor_with_reduce_temperature(self):
        """Test adding window sensor with reduce_temperature action."""
        area = Area(TEST_AREA_ID, TEST_AREA_NAME)

        area.add_window_sensor("binary_sensor.window1", "reduce_temperature", 2.5)

        assert len(area.window_sensors) == 1
        assert area.window_sensors[0]["entity_id"] == "binary_sensor.window1"
        assert area.window_sensors[0]["action_when_open"] == "reduce_temperature"
        assert area.window_sensors[0]["temp_drop"] == pytest.approx(2.5)

    def test_add_window_sensor_with_turn_off(self):
        """Test adding window sensor with turn_off action."""
        area = Area(TEST_AREA_ID, TEST_AREA_NAME)

        area.add_window_sensor("binary_sensor.window1", "turn_off")

        assert len(area.window_sensors) == 1
        assert area.window_sensors[0]["entity_id"] == "binary_sensor.window1"
        assert area.window_sensors[0]["action_when_open"] == "turn_off"
        assert "temp_drop" not in area.window_sensors[0]

    def test_add_duplicate_window_sensor(self):
        """Test adding duplicate window sensor is prevented."""
        area = Area(TEST_AREA_ID, TEST_AREA_NAME)

        area.add_window_sensor("binary_sensor.window1", "reduce_temperature", 2.0)
        area.add_window_sensor("binary_sensor.window1", "reduce_temperature", 3.0)  # Duplicate

        # Should still only have one sensor
        assert len(area.window_sensors) == 1

    def test_remove_window_sensor(self):
        """Test removing window sensor."""
        area = Area(TEST_AREA_ID, TEST_AREA_NAME)

        area.add_window_sensor("binary_sensor.window1", "reduce_temperature", 2.0)
        area.add_window_sensor("binary_sensor.window2", "turn_off")

        area.remove_window_sensor("binary_sensor.window1")

        assert len(area.window_sensors) == 1
        assert area.window_sensors[0]["entity_id"] == "binary_sensor.window2"


class TestAreaPresetTemperatures:
    """Test preset temperature handling."""

    def test_get_preset_temperature_with_area_manager(self):
        """Test getting preset temperature with area manager."""

        # Create a mock area manager with global temperatures
        area_manager = Mock()
        area_manager.global_home_temp = 20.0
        area_manager.global_away_temp = 15.0
        area_manager.global_comfort_temp = 22.0
        area_manager.global_eco_temp = 18.0
        area_manager.global_sleep_temp = 17.0
        area_manager.global_activity_temp = 23.0

        area = Area(TEST_AREA_ID, TEST_AREA_NAME)
        area.area_manager = area_manager
        area.use_global_home = True
        area.preset_mode = "home"

        # Should use global temperatures
        temp = area.get_preset_temperature()
        assert temp == pytest.approx(20.0)

    def test_get_preset_temperature_without_area_manager(self):
        """Test getting preset temperature without area manager."""
        area = Area(TEST_AREA_ID, TEST_AREA_NAME)
        area.home_temp = 20.0
        area.preset_mode = "home"
        area.area_manager = None  # No area manager

        # Should use area-specific temperatures
        temp = area.get_preset_temperature()
        assert temp == pytest.approx(20.0)

    def test_get_active_schedule_temperature(self):
        """Test getting temperature from active schedule."""
        area = Area(TEST_AREA_ID, TEST_AREA_NAME)

        # Add schedule
        schedule = Schedule(
            schedule_id="test_schedule",
            time="08:00",  # Use 'time' instead of 'start_time'
            temperature=21.0,
            days=["mon", "tue", "wed", "thu", "fri"],  # Use strings instead of numbers
        )
        area.schedules["test_schedule"] = schedule

        # Monday at 8:30 AM
        current_time = datetime(2024, 1, 1, 8, 30)  # Monday

        temp = area.get_active_schedule_temperature(current_time)
        assert temp == pytest.approx(21.0)

    def test_get_active_schedule_temperature_no_schedule(self):
        """Test getting temperature when no schedule active."""
        area = Area(TEST_AREA_ID, TEST_AREA_NAME)

        # No schedules
        current_time = datetime(2024, 1, 1, 8, 30)

        temp = area.get_active_schedule_temperature(current_time)
        assert temp is None

    def test_get_window_open_temperature_turn_off(self):
        """Test getting temperature when window open with turn_off action."""
        area = Area(TEST_AREA_ID, TEST_AREA_NAME)
        area.target_temperature = 20.0

        area.add_window_sensor("binary_sensor.window1", "turn_off")
        area.window_is_open = True

        temp = area._get_window_open_temperature()
        assert temp == pytest.approx(5.0)  # Frost protection

    def test_get_window_open_temperature_reduce(self):
        """Test getting temperature when window open with reduce action."""
        area = Area(TEST_AREA_ID, TEST_AREA_NAME)
        area.target_temperature = 20.0

        area.add_window_sensor("binary_sensor.window1", "reduce_temperature", 3.0)
        area.window_is_open = True

        temp = area._get_window_open_temperature()
        assert temp == pytest.approx(17.0)  # 20.0 - 3.0

    def test_get_window_open_temperature_no_action(self):
        """Test getting temperature when window closed."""
        area = Area(TEST_AREA_ID, TEST_AREA_NAME)
        area.target_temperature = 20.0

        area.add_window_sensor("binary_sensor.window1", "reduce_temperature", 3.0)
        area.window_is_open = False  # Window closed

        temp = area._get_window_open_temperature()
        assert temp is None


class TestAreaNightBoost:
    """Test night boost functionality."""

    def test_night_boost_with_area_logger(self):
        """Test night boost logging when area logger available."""

        # Create mock hass with data
        hass = Mock()
        hass.data = {"smart_heating": {"area_logger": Mock()}}

        # Create mock area manager
        area_manager = Mock()
        area_manager.hass = hass

        area = Area(TEST_AREA_ID, TEST_AREA_NAME)
        area.area_manager = area_manager
        area.target_temperature = 20.0
        area.night_boost_enabled = True
        area.night_boost_offset = 2.0
        area.night_boost_start_time = "22:00"
        area.night_boost_end_time = "06:00"

        # Test at a time within the boost period
        current_time = datetime(2024, 1, 1, 23, 0)  # 11 PM

        # Should log to area logger
        target = area._apply_night_boost(20.0, current_time)
        assert target == pytest.approx(22.0)

    def test_night_boost_active_during_period(self):
        """Test night boost applies offset during configured period."""
        area = Area(TEST_AREA_ID, TEST_AREA_NAME)
        area.night_boost_enabled = True
        area.night_boost_offset = 0.5
        area.night_boost_start_time = "03:00"
        area.night_boost_end_time = "07:00"

        # Test during boost period
        current_time = datetime(2024, 1, 1, 5, 30)  # 5:30 AM
        target = area._apply_night_boost(18.5, current_time)
        assert target == pytest.approx(19.0)  # 18.5 + 0.5

    def test_night_boost_inactive_outside_period(self):
        """Test night boost doesn't apply outside configured period."""
        area = Area(TEST_AREA_ID, TEST_AREA_NAME)
        area.night_boost_enabled = True
        area.night_boost_offset = 0.5
        area.night_boost_start_time = "03:00"
        area.night_boost_end_time = "07:00"

        # Test outside boost period
        current_time = datetime(2024, 1, 1, 10, 0)  # 10 AM
        target = area._apply_night_boost(18.5, current_time)
        assert target == pytest.approx(18.5)  # No change

    def test_night_boost_works_with_schedule(self):
        """Test night boost works additively on top of active schedule."""
        area = Area(TEST_AREA_ID, TEST_AREA_NAME)
        area.night_boost_enabled = True
        area.night_boost_offset = 0.2
        area.night_boost_start_time = "03:00"
        area.night_boost_end_time = "07:00"
        area.target_temperature = 20.0

        # Add a sleep schedule that overlaps with night boost
        schedule = Schedule(
            schedule_id="sleep1",
            start_time="22:00",
            end_time="06:30",
            day="Monday",
            preset_mode="sleep",
        )
        area.add_schedule(schedule)
        area.sleep_temp = 18.5

        # Test at 5 AM - during both sleep schedule AND night boost
        current_time = datetime(2024, 1, 1, 5, 0)  # Monday 5 AM

        # Night boost should work on top of sleep temperature
        # Sleep schedule gives 18.5°C, night boost adds 0.2°C = 18.7°C
        target = area._apply_night_boost(18.5, current_time)
        assert target == pytest.approx(18.7)

    def test_night_boost_disabled(self):
        """Test night boost doesn't apply when disabled."""
        area = Area(TEST_AREA_ID, TEST_AREA_NAME)
        area.night_boost_enabled = False
        area.night_boost_offset = 2.0
        area.night_boost_start_time = "03:00"
        area.night_boost_end_time = "07:00"

        # Test during what would be boost period
        current_time = datetime(2024, 1, 1, 5, 0)
        target = area._apply_night_boost(20.0, current_time)
        assert target == pytest.approx(20.0)  # No change when disabled

    def test_night_boost_crosses_midnight(self):
        """Test night boost works correctly when period crosses midnight."""
        area = Area(TEST_AREA_ID, TEST_AREA_NAME)
        area.night_boost_enabled = True
        area.night_boost_offset = 0.3
        area.night_boost_start_time = "22:00"
        area.night_boost_end_time = "06:00"

        # Test late night (before midnight)
        current_time = datetime(2024, 1, 1, 23, 30)  # 11:30 PM
        target = area._apply_night_boost(18.0, current_time)
        assert target == pytest.approx(18.3)

        # Test early morning (after midnight)
        current_time = datetime(2024, 1, 2, 4, 0)  # 4 AM
        target = area._apply_night_boost(18.0, current_time)
        assert target == pytest.approx(18.3)


class TestAreaState:
    """Test area state property."""

    def test_state_when_disabled(self):
        """Test state returns off when area disabled."""
        area = Area(TEST_AREA_ID, TEST_AREA_NAME)
        area.enabled = False

        assert area.state == "off"

    def test_state_with_explicit_state(self):
        """Test state returns explicit _state when set."""
        area = Area(TEST_AREA_ID, TEST_AREA_NAME)
        area._state = "heating"

        assert area.state == "heating"

    def test_state_based_on_temperature(self):
        """Test state determined by temperature when no explicit state."""
        area = Area(TEST_AREA_ID, TEST_AREA_NAME)
        area.current_temperature = 18.0
        area.target_temperature = 21.0

        # Should be heating (current < target - 0.5)
        assert area.state == "heating"

    def test_state_idle_when_at_temperature(self):
        """Test state idle when at target temperature."""
        area = Area(TEST_AREA_ID, TEST_AREA_NAME)
        area.current_temperature = 20.0
        area.target_temperature = 20.0

        # Should be idle (current >= target - 0.5)
        assert area.state == "idle"


class TestAreaFromDict:
    """Test Area.from_dict() functionality."""

    def test_from_dict_with_boost_end_time(self):
        """Test loading area with boost_end_time."""
        data = {
            "area_id": TEST_AREA_ID,
            "area_name": TEST_AREA_NAME,
            "target_temperature": 20.0,
            "boost_end_time": "2024-01-01T12:00:00",
        }

        area = Area.from_dict(data)

        assert area.boost_end_time is not None
        assert area.boost_end_time.year == 2024

    def test_from_dict_with_hysteresis_override(self):
        """Test loading area with hysteresis_override."""
        data = {
            "area_id": TEST_AREA_ID,
            "area_name": TEST_AREA_NAME,
            "target_temperature": 20.0,
            "hysteresis_override": 1.5,
        }

        area = Area.from_dict(data)

        assert area.hysteresis_override == pytest.approx(1.5)

    def test_from_dict_legacy_window_sensors(self):
        """Test loading area with legacy window sensor format."""
        data = {
            "area_id": TEST_AREA_ID,
            "area_name": TEST_AREA_NAME,
            "target_temperature": 20.0,
            "window_sensors": ["binary_sensor.window1", "binary_sensor.window2"],
            "window_open_temp_drop": 2.5,
        }

        area = Area.from_dict(data)

        assert len(area.window_sensors) == 2
        assert area.window_sensors[0]["entity_id"] == "binary_sensor.window1"
        assert area.window_sensors[0]["action_when_open"] == "reduce_temperature"
        assert area.window_sensors[0]["temp_drop"] == pytest.approx(2.5)

    def test_from_dict_legacy_presence_sensors(self):
        """Test loading area with legacy presence sensor format."""
        data = {
            "area_id": TEST_AREA_ID,
            "area_name": TEST_AREA_NAME,
            "target_temperature": 20.0,
            "presence_sensors": ["binary_sensor.motion1", "binary_sensor.motion2"],
            "presence_temp_boost": 1.5,
        }

        area = Area.from_dict(data)

        assert len(area.presence_sensors) == 2
        assert area.presence_sensors[0]["entity_id"] == "binary_sensor.motion1"
        assert area.presence_sensors[0]["temp_boost_when_home"] == pytest.approx(1.5)

    def test_from_dict_with_auto_preset(self):
        """Test loading area with auto preset settings."""
        data = {
            "area_id": TEST_AREA_ID,
            "area_name": TEST_AREA_NAME,
            "target_temperature": 20.0,
            "auto_preset_enabled": True,
            "auto_preset_home": "comfort",
            "auto_preset_away": "eco",
        }

        area = Area.from_dict(data)

        assert area.auto_preset_enabled is True
        assert area.auto_preset_home == "comfort"
        assert area.auto_preset_away == "eco"
