"""Tests for response builder utilities."""

from unittest.mock import MagicMock, Mock

from smart_heating.utils.response_builders import (
    build_area_response,
    build_device_info,
)


class TestBuildDeviceInfo:
    """Tests for build_device_info function."""

    def test_build_device_info_minimal(self):
        """Test building device info with minimal data."""
        device_data = {"type": "climate", "mqtt_topic": "test/topic"}

        result = build_device_info("climate.device1", device_data)

        assert result["id"] == "climate.device1"
        assert result["type"] == "climate"
        assert result["mqtt_topic"] == "test/topic"

    def test_build_device_info_with_state(self):
        """Test building device info with state object."""
        device_data = {"type": "climate", "mqtt_topic": "test/topic"}

        state_obj = Mock()
        state_obj.attributes = {"friendly_name": "Living Room Thermostat"}

        result = build_device_info("climate.device1", device_data, state_obj=state_obj)

        assert result["name"] == "Living Room Thermostat"

    def test_build_device_info_with_coordinator(self):
        """Test building device info with coordinator data."""
        device_data = {"type": "climate"}

        coordinator_device = {
            "state": "heat",
            "current_temperature": 20.5,
            "target_temperature": 21.0,
            "hvac_action": "heating",
            "temperature": 21.0,
            "position": 50,
        }

        result = build_device_info(
            "climate.device1", device_data, coordinator_device=coordinator_device
        )

        assert result["state"] == "heat"
        assert result["current_temperature"] == 20.5
        assert result["target_temperature"] == 21.0
        assert result["hvac_action"] == "heating"
        assert result["temperature"] == 21.0
        assert result["position"] == 50

    def test_build_device_info_complete(self):
        """Test building device info with all data."""
        device_data = {"type": "climate", "mqtt_topic": "test/topic"}

        state_obj = Mock()
        state_obj.attributes = {"friendly_name": "Thermostat"}

        coordinator_device = {"state": "heat", "current_temperature": 20.5}

        result = build_device_info(
            "climate.device1",
            device_data,
            state_obj=state_obj,
            coordinator_device=coordinator_device,
        )

        assert result["name"] == "Thermostat"
        assert result["state"] == "heat"
        assert result["current_temperature"] == 20.5


class TestBuildAreaResponse:
    """Tests for build_area_response function."""

    def test_build_area_response_minimal(self):
        """Test building area response with minimal data."""
        area = MagicMock()
        area.area_id = "living_room"
        area.name = "Living Room"
        area.enabled = True
        area.hidden = False
        area.state = "heating"
        area.target_temperature = 21.0
        area.get_effective_target_temperature.return_value = 21.0
        area.current_temperature = 20.5
        area.schedules = {}
        area.night_boost_enabled = False
        area.night_boost_offset = 0.0
        area.night_boost_start_time = "22:00"
        area.night_boost_end_time = "06:00"
        area.smart_night_boost_enabled = False
        area.smart_night_boost_target_time = "06:00"
        area.weather_entity_id = None
        area.preset_mode = "none"
        area.away_temp = 16.0
        area.eco_temp = 18.0
        area.comfort_temp = 22.0
        area.home_temp = 20.0
        area.sleep_temp = 18.0
        area.activity_temp = 21.0
        area.use_global_away = True
        area.use_global_eco = True
        area.use_global_comfort = True
        area.use_global_home = True
        area.use_global_sleep = True
        area.use_global_activity = True
        area.boost_mode_active = False
        area.boost_temp = 25.0
        area.boost_duration = 60
        area.hvac_mode = "heat"
        area.hysteresis_override = None
        area.manual_override = False
        area.window_sensors = []
        area.presence_sensors = []
        area.use_global_presence = True
        area.auto_preset_enabled = False
        area.auto_preset_home = "home"
        area.auto_preset_away = "away"
        area.shutdown_switches_when_idle = False
        area.shutdown_switch_entities = []

        result = build_area_response(area)

        assert result["id"] == "living_room"
        assert result["name"] == "Living Room"
        assert result["enabled"] is True
        assert result["state"] == "heating"
        assert result["target_temperature"] == 21.0
        assert result["devices"] == []

    def test_build_area_response_with_devices(self):
        """Test building area response with devices."""
        area = MagicMock()
        area.area_id = "living_room"
        area.name = "Living Room"
        area.enabled = True
        area.hidden = False
        area.state = "heating"
        area.target_temperature = 21.0
        area.get_effective_target_temperature.return_value = 21.0
        area.current_temperature = 20.5
        area.schedules = {}
        area.night_boost_enabled = False
        area.night_boost_offset = 0.0
        area.night_boost_start_time = "22:00"
        area.night_boost_end_time = "06:00"
        area.smart_night_boost_enabled = False
        area.smart_night_boost_target_time = "06:00"
        area.weather_entity_id = None
        area.preset_mode = "none"
        area.away_temp = 16.0
        area.eco_temp = 18.0
        area.comfort_temp = 22.0
        area.home_temp = 20.0
        area.sleep_temp = 18.0
        area.activity_temp = 21.0
        area.use_global_away = True
        area.use_global_eco = True
        area.use_global_comfort = True
        area.use_global_home = True
        area.use_global_sleep = True
        area.use_global_activity = True
        area.boost_mode_active = False
        area.boost_temp = 25.0
        area.boost_duration = 60
        area.hvac_mode = "heat"
        area.hysteresis_override = None
        area.manual_override = False
        area.window_sensors = []
        area.presence_sensors = []
        area.use_global_presence = True
        area.auto_preset_enabled = False
        area.auto_preset_home = "home"
        area.auto_preset_away = "away"
        area.shutdown_switches_when_idle = False
        area.shutdown_switch_entities = []

        devices = [{"id": "device1", "name": "Device 1"}, {"id": "device2", "name": "Device 2"}]

        result = build_area_response(area, devices)

        assert len(result["devices"]) == 2
        assert result["devices"][0]["id"] == "device1"

    def test_build_area_response_with_schedules(self):
        """Test building area response with schedules."""
        area = MagicMock()
        area.area_id = "living_room"
        area.name = "Living Room"
        area.enabled = True
        area.hidden = False
        area.state = "heating"
        area.target_temperature = 21.0
        area.get_effective_target_temperature.return_value = 21.0
        area.current_temperature = 20.5

        schedule = MagicMock()
        schedule.to_dict.return_value = {
            "id": "schedule1",
            "time": "08:00",
            "temperature": 21.0,
            "days": [0, 1],
        }
        area.schedules = {"schedule1": schedule}

        area.night_boost_enabled = False
        area.night_boost_offset = 0.0
        area.night_boost_start_time = "22:00"
        area.night_boost_end_time = "06:00"
        area.smart_night_boost_enabled = False
        area.smart_night_boost_target_time = "06:00"
        area.weather_entity_id = None
        area.preset_mode = "none"
        area.away_temp = 16.0
        area.eco_temp = 18.0
        area.comfort_temp = 22.0
        area.home_temp = 20.0
        area.sleep_temp = 18.0
        area.activity_temp = 21.0
        area.use_global_away = True
        area.use_global_eco = True
        area.use_global_comfort = True
        area.use_global_home = True
        area.use_global_sleep = True
        area.use_global_activity = True
        area.boost_mode_active = False
        area.boost_temp = 25.0
        area.boost_duration = 60
        area.hvac_mode = "heat"
        area.hysteresis_override = None
        area.manual_override = False
        area.window_sensors = []
        area.presence_sensors = []
        area.use_global_presence = True
        area.auto_preset_enabled = False
        area.auto_preset_home = "home"
        area.auto_preset_away = "away"
        area.shutdown_switches_when_idle = False
        area.shutdown_switch_entities = []

        result = build_area_response(area)

        assert len(result["schedules"]) == 1
        assert result["schedules"][0]["id"] == "schedule1"

    def test_build_area_response_shutdown_field_from_new_attribute(self):
        """Ensure shutdown_switches_when_idle is present when using new attribute."""
        area = MagicMock()
        area.area_id = "living_room"
        area.name = "Living Room"
        area.enabled = True
        area.hidden = False
        area.state = "heating"
        area.target_temperature = 21.0
        area.get_effective_target_temperature.return_value = 21.0
        area.current_temperature = 20.5
        area.schedules = {}
        # set the new attribute
        area.shutdown_switches_when_idle = True

        result = build_area_response(area)

        assert result["shutdown_switches_when_idle"] is True

    def test_build_area_response_shutdown_field_from_legacy_attribute(self):
        """Ensure legacy attribute is ignored and default applies when not set."""
        area = MagicMock()
        area.area_id = "living_room"
        area.name = "Living Room"
        area.enabled = True
        area.hidden = False
        area.state = "heating"
        area.target_temperature = 21.0
        area.get_effective_target_temperature.return_value = 21.0
        area.current_temperature = 20.5
        area.schedules = {}
        # set only the legacy attribute (should be ignored)
        area.switch_shutdown_enabled = False

        result = build_area_response(area)

        # Legacy attribute is ignored; default is True
        assert result["shutdown_switches_when_idle"] is True
