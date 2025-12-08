"""Tests for Scheduler helper methods."""
from __future__ import annotations

from datetime import datetime, time
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from homeassistant.core import HomeAssistant, State

from smart_heating.scheduler import ScheduleExecutor
from smart_heating.models.schedule import Schedule
from smart_heating.const import (
    PRESET_AWAY,
    PRESET_COMFORT,
    PRESET_ECO,
    PRESET_HOME,
    PRESET_SLEEP,
)


@pytest.fixture
def mock_learning_engine():
    """Create mock learning engine."""
    engine = MagicMock()
    engine.async_predict_heating_time = AsyncMock(return_value=30)
    return engine


@pytest.fixture
def scheduler(hass, mock_area_manager, mock_learning_engine):
    """Create a ScheduleExecutor instance."""
    executor = ScheduleExecutor(hass, mock_area_manager, mock_learning_engine)
    executor.area_logger = None
    return executor


@pytest.fixture
def mock_area():
    """Create mock area."""
    area = MagicMock()
    area.area_id = "living_room"
    area.name = "Living Room"
    area.target_temperature = 20.0
    area.current_temperature = 18.0
    area.preset_mode = "none"
    area.manual_override = False
    area.schedules = {}
    area.weather_entity_id = None
    area.smart_night_boost_target_time = None
    # Preset temperatures
    area.away_temp = 16.0
    area.eco_temp = 18.0
    area.comfort_temp = 22.0
    area.home_temp = 20.0
    area.sleep_temp = 17.0
    area.activity_temp = 23.0
    # Use global flags
    area.use_global_away = False
    area.use_global_eco = False
    area.use_global_comfort = False
    area.use_global_home = False
    area.use_global_sleep = False
    area.use_global_activity = False
    return area


class TestGetPreviousDay:
    """Test _get_previous_day helper."""

    def test_get_previous_day_monday(self, scheduler):
        """Test getting previous day for Monday."""
        assert scheduler._get_previous_day("Monday") == "Sunday"

    def test_get_previous_day_tuesday(self, scheduler):
        """Test getting previous day for Tuesday."""
        assert scheduler._get_previous_day("Tuesday") == "Monday"

    def test_get_previous_day_sunday(self, scheduler):
        """Test getting previous day for Sunday."""
        assert scheduler._get_previous_day("Sunday") == "Saturday"


class TestScheduleTimeMatching:
    """Test schedule time matching helpers."""

    def test_is_time_in_midnight_crossing_schedule_from_previous_day(self, scheduler):
        """Test checking if time is in midnight-crossing schedule from previous day."""
        # Create schedule from 22:00 to 07:00
        schedule = Schedule(
            schedule_id="1",
            time="22:00",
            day="Saturday",
            start_time="22:00",
            end_time="07:00",
            temperature=18.0,
            enabled=True
        )
        
        # Test time at 02:00 (early morning, should match)
        current_time = time(2, 0)
        assert scheduler._is_time_in_midnight_crossing_schedule_from_previous_day(
            schedule, current_time
        ) is True
        
        # Test time at 08:00 (after end time, should not match)
        current_time = time(8, 0)
        assert scheduler._is_time_in_midnight_crossing_schedule_from_previous_day(
            schedule, current_time
        ) is False

    def test_is_time_in_midnight_crossing_schedule_today(self, scheduler):
        """Test checking if time is in midnight-crossing schedule that starts today."""
        # Create schedule from 22:00 to 07:00
        schedule = Schedule(
            schedule_id="1",
            time="22:00",
            day="Saturday",
            start_time="22:00",
            end_time="07:00",
            temperature=18.0,
            enabled=True
        )
        
        # Test time at 23:00 (evening, should match)
        current_time = time(23, 0)
        assert scheduler._is_time_in_midnight_crossing_schedule_today(
            schedule, current_time
        ) is True
        
        # Test time at 02:00 (early morning, should not match - that's from previous day)
        current_time = time(2, 0)
        assert scheduler._is_time_in_midnight_crossing_schedule_today(
            schedule, current_time
        ) is False

    def test_is_time_in_normal_schedule(self, scheduler):
        """Test checking if time is in normal (non-midnight-crossing) schedule."""
        # Create normal schedule from 08:00 to 22:00
        schedule = Schedule(
            schedule_id="1",
            time="08:00",
            day="Monday",
            start_time="08:00",
            end_time="22:00",
            temperature=21.0,
            enabled=True
        )
        
        # Test time at 10:00 (should match)
        current_time = time(10, 0)
        assert scheduler._is_time_in_normal_schedule(schedule, current_time) is True
        
        # Test time at 07:00 (before start, should not match)
        current_time = time(7, 0)
        assert scheduler._is_time_in_normal_schedule(schedule, current_time) is False
        
        # Test time at 23:00 (after end, should not match)
        current_time = time(23, 0)
        assert scheduler._is_time_in_normal_schedule(schedule, current_time) is False


class TestFindActiveSchedule:
    """Test _find_active_schedule method."""

    def test_find_active_schedule_normal(self, scheduler):
        """Test finding active normal schedule."""
        schedules = {
            "1": Schedule(
                schedule_id="1",
                time="08:00",
                day="Monday",
                start_time="08:00",
                end_time="17:00",
                temperature=20.0,
                enabled=True
            ),
            "2": Schedule(
                schedule_id="2",
                time="17:00",
                day="Monday",
                start_time="17:00",
                end_time="22:00",
                temperature=21.0,
                enabled=True
            )
        }
        
        # Test at 10:00 Monday
        schedule = scheduler._find_active_schedule(schedules, "Monday", time(10, 0))
        assert schedule is not None
        assert schedule.schedule_id == "1"
        
        # Test at 20:00 Monday
        schedule = scheduler._find_active_schedule(schedules, "Monday", time(20, 0))
        assert schedule is not None
        assert schedule.schedule_id == "2"

    def test_find_active_schedule_midnight_crossing(self, scheduler):
        """Test finding active schedule that crosses midnight."""
        schedules = {
            "1": Schedule(
                schedule_id="1",
                time="22:00",
                day="Sunday",
                start_time="22:00",
                end_time="07:00",
                temperature=18.0,
                enabled=True
            )
        }
        
        # Test at 23:00 Sunday (start of schedule)
        schedule = scheduler._find_active_schedule(schedules, "Sunday", time(23, 0))
        assert schedule is not None
        assert schedule.schedule_id == "1"
        
        # Test at 02:00 Monday (continuation from Sunday)
        schedule = scheduler._find_active_schedule(schedules, "Monday", time(2, 0))
        assert schedule is not None
        assert schedule.schedule_id == "1"

    def test_find_active_schedule_no_match(self, scheduler):
        """Test finding schedule when none match."""
        schedules = {
            "1": Schedule(
                schedule_id="1",
                time="08:00",
                day="Monday",
                start_time="08:00",
                end_time="17:00",
                temperature=20.0,
                enabled=True
            )
        }
        
        # Test at 07:00 Monday (before any schedule)
        schedule = scheduler._find_active_schedule(schedules, "Monday", time(7, 0))
        assert schedule is None


class TestGetPresetTemperature:
    """Test _get_preset_temperature method."""

    def test_get_preset_temperature_area_specific(self, scheduler, mock_area):
        """Test getting preset temperature from area-specific settings."""
        temp = scheduler._get_preset_temperature(mock_area, PRESET_COMFORT)
        assert temp == 22.0

    def test_get_preset_temperature_global(self, scheduler, mock_area, mock_area_manager):
        """Test getting preset temperature from global settings."""
        # Set up area manager with global temps
        mock_area_manager.global_comfort_temp = 21.5
        mock_area.use_global_comfort = True
        
        temp = scheduler._get_preset_temperature(mock_area, PRESET_COMFORT)
        # Should use global temp
        assert temp == 21.5

    def test_get_preset_temperature_all_presets(self, scheduler, mock_area):
        """Test getting all preset temperatures."""
        assert scheduler._get_preset_temperature(mock_area, PRESET_AWAY) == 16.0
        assert scheduler._get_preset_temperature(mock_area, PRESET_ECO) == 18.0
        assert scheduler._get_preset_temperature(mock_area, PRESET_COMFORT) == 22.0
        assert scheduler._get_preset_temperature(mock_area, PRESET_HOME) == 20.0
        assert scheduler._get_preset_temperature(mock_area, PRESET_SLEEP) == 17.0
        assert scheduler._get_preset_temperature(mock_area, "activity") == 23.0

    def test_get_preset_temperature_unknown_preset(self, scheduler, mock_area):
        """Test getting temperature for unknown preset falls back to target."""
        temp = scheduler._get_preset_temperature(mock_area, "unknown_preset")
        assert temp == mock_area.target_temperature


class TestOutdoorTemperature:
    """Test _get_outdoor_temperature method."""

    def test_get_outdoor_temperature_no_entity(self, scheduler, mock_area):
        """Test getting outdoor temperature when no weather entity configured."""
        mock_area.weather_entity_id = None
        
        temp = scheduler._get_outdoor_temperature(mock_area)
        assert temp is None

    def test_get_outdoor_temperature_celsius(self, scheduler, mock_area, hass):
        """Test getting outdoor temperature in Celsius."""
        mock_area.weather_entity_id = "weather.home"
        
        # Create a state for the weather entity
        hass.states.async_set(
            "weather.home",
            "12.5",
            {"unit_of_measurement": "°C"}
        )
        
        temp = scheduler._get_outdoor_temperature(mock_area)
        assert temp == 12.5

    def test_get_outdoor_temperature_fahrenheit(self, scheduler, mock_area, hass):
        """Test getting outdoor temperature in Fahrenheit."""
        mock_area.weather_entity_id = "weather.home"
        
        # Create a state for the weather entity
        hass.states.async_set(
            "weather.home",
            "55.0",
            {"unit_of_measurement": "°F"}
        )
        
        temp = scheduler._get_outdoor_temperature(mock_area)
        assert temp == pytest.approx(12.78, abs=0.01)

    def test_get_outdoor_temperature_unavailable(self, scheduler, mock_area, hass):
        """Test getting outdoor temperature when unavailable."""
        mock_area.weather_entity_id = "weather.home"
        
        # Create unavailable state
        hass.states.async_set("weather.home", "unavailable")
        
        temp = scheduler._get_outdoor_temperature(mock_area)
        assert temp is None


class TestTargetTimeFromConfig:
    """Test _get_target_time_from_config method."""

    def test_get_target_time_from_config_valid(self, scheduler, mock_area):
        """Test getting target time from area configuration."""
        mock_area.smart_night_boost_target_time = "06:30"
        now = datetime(2024, 1, 1, 22, 0)  # 10 PM
        
        target_time = scheduler._get_target_time_from_config(mock_area, now)
        
        assert target_time is not None
        assert target_time.hour == 6
        assert target_time.minute == 30

    def test_get_target_time_from_config_none(self, scheduler, mock_area):
        """Test getting target time when not configured."""
        mock_area.smart_night_boost_target_time = None
        now = datetime(2024, 1, 1, 22, 0)
        
        target_time = scheduler._get_target_time_from_config(mock_area, now)
        
        assert target_time is None


class TestApplyScheduleMethods:
    """Test _apply_preset_schedule and _apply_temperature_schedule methods."""

    @pytest.mark.asyncio
    async def test_apply_preset_schedule(self, scheduler, mock_area, mock_area_manager, hass):
        """Test applying a schedule with preset mode."""
        schedule = Schedule(
            schedule_id="1",
            time="08:00",
            day="Monday",
            start_time="08:00",
            end_time="17:00",
            preset_mode=PRESET_COMFORT,
            enabled=True
        )
        
        await scheduler._apply_preset_schedule(mock_area, schedule, "climate.smart_heating_living_room")
        
        # Should set preset mode
        assert mock_area.preset_mode == PRESET_COMFORT
        # Should update target temperature to match preset
        assert mock_area.target_temperature == 22.0
        # Should save
        mock_area_manager.async_save.assert_called_once()

    @pytest.mark.asyncio
    async def test_apply_preset_schedule_clears_manual_override(self, scheduler, mock_area, mock_area_manager, hass):
        """Test that applying schedule clears manual override."""
        mock_area.manual_override = True
        schedule = Schedule(
            schedule_id="1",
            time="08:00",
            day="Monday",
            start_time="08:00",
            end_time="17:00",
            preset_mode=PRESET_COMFORT,
            enabled=True
        )
        
        await scheduler._apply_preset_schedule(mock_area, schedule, "climate.smart_heating_living_room")
        
        # Should clear manual override
        assert mock_area.manual_override is False

    @pytest.mark.asyncio
    async def test_apply_temperature_schedule(self, scheduler, mock_area, mock_area_manager, hass):
        """Test applying a schedule with direct temperature."""
        schedule = Schedule(
            schedule_id="1",
            time="08:00",
            day="Monday",
            start_time="08:00",
            end_time="17:00",
            temperature=21.5,
            enabled=True
        )
        
        await scheduler._apply_temperature_schedule(mock_area, schedule, "climate.smart_heating_living_room")
        
        # Should set target temperature
        assert mock_area.target_temperature == 21.5
        # Should save
        mock_area_manager.async_save.assert_called_once()
        # Note: hass.services.async_call is called but will fail with service_not_found
        # in test environment - that's expected and logged as a warning

    @pytest.mark.asyncio
    async def test_apply_temperature_schedule_clears_manual_override(self, scheduler, mock_area, mock_area_manager, hass):
        """Test that applying temperature schedule clears manual override."""
        mock_area.manual_override = True
        schedule = Schedule(
            schedule_id="1",
            time="08:00",
            day="Monday",
            start_time="08:00",
            end_time="17:00",
            temperature=21.0,
            enabled=True
        )
        
        await scheduler._apply_temperature_schedule(mock_area, schedule, "climate.smart_heating_living_room")
        
        # Should clear manual override
        assert mock_area.manual_override is False
