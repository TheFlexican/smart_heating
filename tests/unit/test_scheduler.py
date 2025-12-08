"""Tests for Schedule Executor.

Tests schedule checking, application, midnight crossing, smart night boost,
and preset/temperature handling.
"""

from datetime import datetime, time, timedelta
from unittest.mock import AsyncMock, MagicMock, patch, call

import pytest
from homeassistant.core import HomeAssistant, State

from smart_heating.scheduler import ScheduleExecutor, DAYS_OF_WEEK

from tests.unit.const import TEST_AREA_ID, TEST_TEMPERATURE


@pytest.fixture
def scheduler(hass: HomeAssistant, mock_area_manager) -> ScheduleExecutor:
    """Create a ScheduleExecutor instance."""
    return ScheduleExecutor(hass, mock_area_manager)


@pytest.fixture
def scheduler_with_learning(hass: HomeAssistant, mock_area_manager) -> ScheduleExecutor:
    """Create a ScheduleExecutor with learning engine."""
    mock_learning = MagicMock()
    mock_learning.async_predict_heating_time = AsyncMock(return_value=30)
    return ScheduleExecutor(hass, mock_area_manager, learning_engine=mock_learning)


@pytest.fixture
def mock_schedule():
    """Create a mock schedule entry."""
    schedule = MagicMock()
    schedule.schedule_id = "test_schedule"
    schedule.day = "Monday"
    schedule.start_time = "07:00"
    schedule.end_time = "09:00"
    schedule.temperature = TEST_TEMPERATURE
    schedule.preset_mode = None
    schedule.enabled = True
    return schedule


@pytest.fixture
def mock_area_with_schedule(mock_area_data):
    """Create a mock area with schedule."""
    area = MagicMock()
    area.area_id = TEST_AREA_ID
    area.name = "Test Area"
    area.enabled = True
    area.target_temperature = 20.0
    area.current_temperature = 18.0
    area.manual_override = False
    area.schedules = {}
    area.smart_night_boost_enabled = False
    area.weather_entity_id = None
    return area


class TestInitialization:
    """Tests for initialization."""

    def test_init(self, scheduler: ScheduleExecutor, hass: HomeAssistant, mock_area_manager):
        """Test scheduler initialization."""
        assert scheduler.hass == hass
        assert scheduler.area_manager == mock_area_manager
        assert scheduler.learning_engine is None
        assert scheduler._unsub_interval is None
        assert scheduler._last_applied_schedule == {}

    def test_init_with_learning_engine(self, scheduler_with_learning: ScheduleExecutor):
        """Test initialization with learning engine."""
        assert scheduler_with_learning.learning_engine is not None

    async def test_async_start(self, scheduler: ScheduleExecutor):
        """Test starting the scheduler."""
        with patch.object(scheduler, '_async_check_schedules', new_callable=AsyncMock) as mock_check:
            with patch("smart_heating.scheduler.async_track_time_interval") as mock_track:
                mock_track.return_value = MagicMock()
                
                await scheduler.async_start()
                
                # Should check schedules immediately
                mock_check.assert_called_once()
                # Should set up interval tracking
                mock_track.assert_called_once()
                assert scheduler._unsub_interval is not None
            
    async def test_async_stop(self, scheduler: ScheduleExecutor):
        """Test stopping the scheduler."""
        # Create mock unsubscribe function
        mock_unsub = MagicMock()
        scheduler._unsub_interval = mock_unsub
        
        scheduler.async_stop()
        
        mock_unsub.assert_called_once()
        assert scheduler._unsub_interval is None

    async def test_async_stop_when_not_started(self, scheduler: ScheduleExecutor):
        """Test stopping when never started."""
        scheduler.async_stop()
        # Should not crash
        assert scheduler._unsub_interval is None


class TestCacheManagement:
    """Tests for schedule cache management."""

    def test_clear_schedule_cache(self, scheduler: ScheduleExecutor):
        """Test clearing schedule cache for an area."""
        # Set up cache
        scheduler._last_applied_schedule[TEST_AREA_ID] = "test_schedule"
        scheduler._last_applied_schedule["other_area"] = "other_schedule"
        
        # Clear one area
        scheduler.clear_schedule_cache(TEST_AREA_ID)
        
        assert TEST_AREA_ID not in scheduler._last_applied_schedule
        assert "other_area" in scheduler._last_applied_schedule

    def test_clear_schedule_cache_nonexistent(self, scheduler: ScheduleExecutor):
        """Test clearing cache for area that doesn't exist."""
        # Should not crash
        scheduler.clear_schedule_cache("nonexistent_area")


class TestDayHelpers:
    """Tests for day helper methods."""

    def test_get_previous_day_monday(self, scheduler: ScheduleExecutor):
        """Test getting previous day from Monday."""
        assert scheduler._get_previous_day("Monday") == "Sunday"

    def test_get_previous_day_sunday(self, scheduler: ScheduleExecutor):
        """Test getting previous day from Sunday."""
        assert scheduler._get_previous_day("Sunday") == "Saturday"

    def test_get_previous_day_tuesday(self, scheduler: ScheduleExecutor):
        """Test getting previous day from Tuesday."""
        assert scheduler._get_previous_day("Tuesday") == "Monday"


class TestTimeMatching:
    """Tests for time matching methods."""

    def test_is_time_in_normal_schedule(self, scheduler: ScheduleExecutor, mock_schedule):
        """Test matching time in normal schedule."""
        # Schedule is 07:00-09:00, test 08:00
        current_time = time(8, 0)
        
        assert scheduler._is_time_in_normal_schedule(mock_schedule, current_time) is True

    def test_is_time_in_normal_schedule_outside(self, scheduler: ScheduleExecutor, mock_schedule):
        """Test time outside normal schedule."""
        current_time = time(10, 0)
        
        assert scheduler._is_time_in_normal_schedule(mock_schedule, current_time) is False

    def test_is_time_in_midnight_crossing_schedule_today(self, scheduler: ScheduleExecutor, mock_schedule):
        """Test matching midnight-crossing schedule (late period)."""
        # Change schedule to cross midnight: 22:00-06:00
        mock_schedule.start_time = "22:00"
        mock_schedule.end_time = "06:00"
        
        # Test 23:00 (in late period)
        current_time = time(23, 0)
        
        assert scheduler._is_time_in_midnight_crossing_schedule_today(mock_schedule, current_time) is True

    def test_is_time_in_midnight_crossing_schedule_from_previous_day(self, scheduler: ScheduleExecutor, mock_schedule):
        """Test matching midnight-crossing schedule (early period)."""
        # Schedule crosses midnight: 22:00-06:00
        mock_schedule.start_time = "22:00"
        mock_schedule.end_time = "06:00"
        
        # Test 05:00 (in early period, from previous day)
        current_time = time(5, 0)
        
        assert scheduler._is_time_in_midnight_crossing_schedule_from_previous_day(mock_schedule, current_time) is True


class TestFindActiveSchedule:
    """Tests for finding active schedules."""

    def test_find_active_schedule_normal(self, scheduler: ScheduleExecutor, mock_schedule):
        """Test finding active normal schedule."""
        schedules = {"test_id": mock_schedule}
        current_time = time(8, 0)
        
        result = scheduler._find_active_schedule(schedules, "Monday", current_time)
        
        assert result == mock_schedule

    def test_find_active_schedule_none(self, scheduler: ScheduleExecutor, mock_schedule):
        """Test finding no active schedule."""
        schedules = {"test_id": mock_schedule}
        current_time = time(10, 0)  # Outside schedule
        
        result = scheduler._find_active_schedule(schedules, "Monday", current_time)
        
        assert result is None

    def test_find_active_schedule_midnight_crossing(self, scheduler: ScheduleExecutor):
        """Test finding midnight-crossing schedule has priority."""
        # Create two schedules: one normal, one midnight-crossing
        normal_schedule = MagicMock()
        normal_schedule.day = "Monday"
        normal_schedule.start_time = "08:00"
        normal_schedule.end_time = "10:00"
        
        midnight_schedule = MagicMock()
        midnight_schedule.day = "Monday"
        midnight_schedule.start_time = "22:00"
        midnight_schedule.end_time = "06:00"
        
        schedules = {"normal": normal_schedule, "midnight": midnight_schedule}
        current_time = time(23, 0)  # Matches midnight schedule
        
        result = scheduler._find_active_schedule(schedules, "Monday", current_time)
        
        assert result == midnight_schedule


class TestPresetTemperature:
    """Tests for preset temperature handling."""

    def test_get_preset_temperature_away(self, scheduler: ScheduleExecutor, mock_area_with_schedule):
        """Test getting away preset temperature."""
        mock_area_with_schedule.away_temp = 15.0
        mock_area_with_schedule.use_global_away = False
        
        temp = scheduler._get_preset_temperature(mock_area_with_schedule, "away")
        
        assert temp == 15.0

    def test_get_preset_temperature_global(self, scheduler: ScheduleExecutor, mock_area_with_schedule, mock_area_manager):
        """Test getting global preset temperature."""
        mock_area_with_schedule.eco_temp = 18.0
        mock_area_with_schedule.use_global_eco = True
        scheduler.area_manager.global_eco_temp = 17.0
        
        temp = scheduler._get_preset_temperature(mock_area_with_schedule, "eco")
        
        assert temp == 17.0

    def test_get_preset_temperature_unknown(self, scheduler: ScheduleExecutor, mock_area_with_schedule):
        """Test getting unknown preset falls back to target temperature."""
        mock_area_with_schedule.target_temperature = 20.0
        
        temp = scheduler._get_preset_temperature(mock_area_with_schedule, "unknown_preset")
        
        assert temp == 20.0


class TestApplySchedule:
    """Tests for applying schedules."""

    async def test_apply_temperature_schedule(self, scheduler: ScheduleExecutor, mock_area_with_schedule, mock_schedule):
        """Test applying schedule with temperature."""
        mock_schedule.temperature = 22.0
        mock_schedule.preset_mode = None
        
        with patch.object(scheduler, '_apply_temperature_schedule', new_callable=AsyncMock) as mock_apply:
            await scheduler._apply_schedule(mock_area_with_schedule, mock_schedule)
        
        mock_apply.assert_called_once_with(mock_area_with_schedule, mock_schedule, f"climate.smart_heating_{TEST_AREA_ID}")

    async def test_apply_preset_schedule(self, scheduler: ScheduleExecutor, mock_area_with_schedule, mock_schedule):
        """Test applying schedule with preset mode."""
        mock_schedule.preset_mode = "eco"
        mock_schedule.temperature = None
        mock_area_with_schedule.eco_temp = 18.0
        mock_area_with_schedule.use_global_eco = False
        
        with patch.object(scheduler, '_apply_preset_schedule', new_callable=AsyncMock) as mock_apply:
            await scheduler._apply_schedule(mock_area_with_schedule, mock_schedule)
        
        mock_apply.assert_called_once_with(mock_area_with_schedule, mock_schedule, f"climate.smart_heating_{TEST_AREA_ID}")

    async def test_apply_temperature_schedule_updates_area(self, scheduler: ScheduleExecutor, mock_area_with_schedule, mock_schedule):
        """Test that applying temperature schedule updates area."""
        mock_schedule.temperature = 22.0
        mock_schedule.preset_mode = None
        mock_schedule.schedule_id = "test_id"
        mock_schedule.start_time = "07:00"
        mock_schedule.end_time = "09:00"
        
        with patch.object(scheduler.area_manager, 'async_save', new_callable=AsyncMock):
            # Call the actual implementation
            await scheduler._apply_temperature_schedule(mock_area_with_schedule, mock_schedule, "climate.test")
        
        assert mock_area_with_schedule.target_temperature == 22.0
        assert mock_area_with_schedule.manual_override is False


class TestScheduleChecking:
    """Tests for schedule checking logic."""

    async def test_check_schedules_disabled_area(self, scheduler: ScheduleExecutor, mock_area_with_schedule, mock_area_manager):
        """Test that disabled areas are skipped."""
        mock_area_with_schedule.enabled = False
        mock_area_manager.get_all_areas.return_value = {TEST_AREA_ID: mock_area_with_schedule}
        
        now = datetime(2024, 1, 1, 8, 0)  # Monday 08:00
        
        await scheduler._async_check_schedules(now)
        
        # Should not apply any schedule
        assert TEST_AREA_ID not in scheduler._last_applied_schedule

    async def test_check_schedules_applies_active(self, scheduler: ScheduleExecutor, mock_area_with_schedule, mock_schedule, mock_area_manager):
        """Test that active schedules are applied."""
        mock_schedule.day = "Monday"
        mock_schedule.start_time = "07:00"
        mock_schedule.end_time = "09:00"
        mock_area_with_schedule.schedules = {"test_id": mock_schedule}
        mock_area_manager.get_all_areas.return_value = {TEST_AREA_ID: mock_area_with_schedule}
        
        now = datetime(2024, 1, 1, 8, 0)  # Monday 08:00
        
        with patch.object(scheduler.hass.config, 'time_zone', 'UTC'):
            with patch.object(scheduler, '_apply_schedule', new_callable=AsyncMock) as mock_apply:
                await scheduler._async_check_schedules(now)
        
        mock_apply.assert_called_once_with(mock_area_with_schedule, mock_schedule)

    async def test_check_schedules_cache_prevents_reapply(self, scheduler: ScheduleExecutor, mock_area_with_schedule, mock_schedule, mock_area_manager):
        """Test that schedule cache prevents reapplying same schedule."""
        mock_schedule.day = "Monday"
        mock_area_with_schedule.schedules = {"test_id": mock_schedule}
        mock_area_manager.get_all_areas.return_value = {TEST_AREA_ID: mock_area_with_schedule}
        
        # Set cache to indicate schedule already applied
        scheduler._last_applied_schedule[TEST_AREA_ID] = f"{TEST_AREA_ID}_{mock_schedule.schedule_id}"
        
        now = datetime(2024, 1, 1, 8, 0)
        
        with patch.object(scheduler.hass.config, 'time_zone', 'UTC'):
            with patch.object(scheduler, '_apply_schedule', new_callable=AsyncMock) as mock_apply:
                await scheduler._async_check_schedules(now)
        
        # Should not reapply
        mock_apply.assert_not_called()


class TestSmartNightBoost:
    """Tests for smart night boost functionality."""

    async def test_find_first_morning_schedule(self, scheduler_with_learning: ScheduleExecutor):
        """Test finding first morning schedule."""
        morning_schedule = MagicMock()
        morning_schedule.day = "Monday"
        morning_schedule.start_time = "07:00"
        morning_schedule.enabled = True
        
        afternoon_schedule = MagicMock()
        afternoon_schedule.day = "Monday"
        afternoon_schedule.start_time = "14:00"
        afternoon_schedule.enabled = True
        
        schedules = {"morning": morning_schedule, "afternoon": afternoon_schedule}
        now = datetime(2024, 1, 1, 6, 0)  # Monday 06:00
        
        result = scheduler_with_learning._find_first_morning_schedule(schedules, now)
        
        assert result == morning_schedule

    async def test_find_first_morning_schedule_none(self, scheduler_with_learning: ScheduleExecutor):
        """Test finding morning schedule when none exist."""
        afternoon_schedule = MagicMock()
        afternoon_schedule.day = "Monday"
        afternoon_schedule.start_time = "14:00"
        afternoon_schedule.enabled = True
        
        schedules = {"afternoon": afternoon_schedule}
        now = datetime(2024, 1, 1, 6, 0)
        
        result = scheduler_with_learning._find_first_morning_schedule(schedules, now)
        
        assert result is None

    async def test_get_outdoor_temperature(self, scheduler: ScheduleExecutor, mock_area_with_schedule, hass: HomeAssistant):
        """Test getting outdoor temperature from weather entity."""
        mock_area_with_schedule.weather_entity_id = "weather.home"
        
        # Mock weather state
        hass.states.async_set("weather.home", "20.5", {"unit_of_measurement": "°C"})
        
        temp = scheduler._get_outdoor_temperature(mock_area_with_schedule)
        
        assert temp == 20.5

    async def test_get_outdoor_temperature_fahrenheit(self, scheduler: ScheduleExecutor, mock_area_with_schedule, hass: HomeAssistant):
        """Test converting Fahrenheit to Celsius."""
        mock_area_with_schedule.weather_entity_id = "weather.home"
        
        # 68°F = 20°C
        hass.states.async_set("weather.home", "68", {"unit_of_measurement": "°F"})
        
        temp = scheduler._get_outdoor_temperature(mock_area_with_schedule)
        
        assert abs(temp - 20.0) < 0.1  # Allow small floating point difference

    async def test_handle_smart_night_boost_no_config(self, scheduler_with_learning: ScheduleExecutor, mock_area_with_schedule):
        """Test smart night boost with no config returns early."""
        mock_area_with_schedule.smart_night_boost_enabled = True
        mock_area_with_schedule.smart_night_boost_target_time = None
        mock_area_with_schedule.schedules = {}
        
        now = datetime(2024, 1, 1, 6, 0)
        
        # Should return early without errors
        await scheduler_with_learning._handle_smart_night_boost(mock_area_with_schedule, now)


class TestAreaLogger:
    """Tests for area logger integration."""

    async def test_apply_schedule_logs_when_logger_available(self, scheduler: ScheduleExecutor, mock_area_with_schedule, mock_schedule):
        """Test that schedule application logs when area_logger is available."""
        mock_logger = MagicMock()
        scheduler.area_logger = mock_logger
        
        mock_schedule.temperature = 21.0
        mock_schedule.preset_mode = None
        
        with patch.object(scheduler.area_manager, 'async_save', new_callable=AsyncMock):
            # Call the internal method directly
            await scheduler._apply_temperature_schedule(mock_area_with_schedule, mock_schedule, "climate.test")
        
        mock_logger.log_event.assert_called_once()
        # Clear it
        scheduler.clear_schedule_cache(TEST_AREA_ID)
        
        # Should be removed
        assert TEST_AREA_ID not in scheduler._last_applied_schedule


class TestSmartNightBoostEdgeCases:
    """Test smart night boost edge cases."""

    async def test_handle_smart_night_boost_no_current_temp(self, scheduler_with_learning: ScheduleExecutor, mock_area_with_schedule):
        """Test smart night boost when area has no current temperature."""
        mock_area_with_schedule.smart_night_boost_enabled = True
        mock_area_with_schedule.smart_night_boost_target_time = "07:00"
        mock_area_with_schedule.current_temperature = None
        mock_area_with_schedule.schedules = {}
        
        now = datetime(2024, 1, 1, 6, 0)
        
        # Should return early due to no temperature data
        await scheduler_with_learning._handle_smart_night_boost(mock_area_with_schedule, now)

    async def test_handle_smart_night_boost_target_passed_today(self, scheduler_with_learning: ScheduleExecutor, mock_area_with_schedule):
        """Test smart night boost when target time has already passed today."""
        mock_area_with_schedule.smart_night_boost_enabled = True
        mock_area_with_schedule.smart_night_boost_target_time = "07:00"
        mock_area_with_schedule.current_temperature = 18.0
        mock_area_with_schedule.target_temperature = 21.0
        mock_area_with_schedule.schedules = {}
        mock_area_with_schedule.weather_entity_id = None
        
        # Current time is after target (8 AM > 7 AM)
        now = datetime(2024, 1, 1, 8, 0)
        
        # Should use tomorrow's target
        await scheduler_with_learning._handle_smart_night_boost(mock_area_with_schedule, now)
        
        # Verify prediction was called
        scheduler_with_learning.learning_engine.async_predict_heating_time.assert_called()

    async def test_handle_smart_night_boost_no_prediction(self, scheduler_with_learning: ScheduleExecutor, mock_area_with_schedule):
        """Test smart night boost when learning engine returns None."""
        mock_area_with_schedule.smart_night_boost_enabled = True
        mock_area_with_schedule.smart_night_boost_target_time = "07:00"
        mock_area_with_schedule.current_temperature = 18.0
        mock_area_with_schedule.target_temperature = 21.0
        mock_area_with_schedule.schedules = {}
        mock_area_with_schedule.weather_entity_id = None
        
        # Learning engine returns None (no prediction available)
        scheduler_with_learning.learning_engine.async_predict_heating_time = AsyncMock(return_value=None)
        
        now = datetime(2024, 1, 1, 6, 0)
        
        # Should return early when no prediction
        await scheduler_with_learning._handle_smart_night_boost(mock_area_with_schedule, now)

    async def test_handle_smart_night_boost_in_heating_window(self, scheduler_with_learning: ScheduleExecutor, mock_area_with_schedule):
        """Test smart night boost when current time is in optimal heating window."""
        mock_area_with_schedule.smart_night_boost_enabled = True
        mock_area_with_schedule.smart_night_boost_target_time = "07:00"
        mock_area_with_schedule.current_temperature = 18.0
        mock_area_with_schedule.target_temperature = 21.0
        mock_area_with_schedule.schedules = {}
        mock_area_with_schedule.weather_entity_id = None
        
        # Learning engine predicts 30 minutes heating time
        scheduler_with_learning.learning_engine.async_predict_heating_time = AsyncMock(return_value=30)
        
        # Current time is 06:15 (optimal start would be ~06:20 with 30 min + 10 min margin)
        now = datetime(2024, 1, 1, 6, 15)
        
        # Should activate smart night boost
        await scheduler_with_learning._handle_smart_night_boost(mock_area_with_schedule, now)

    async def test_handle_smart_night_boost_before_heating_window(self, scheduler_with_learning: ScheduleExecutor, mock_area_with_schedule):
        """Test smart night boost when current time is before optimal heating window."""
        mock_area_with_schedule.smart_night_boost_enabled = True
        mock_area_with_schedule.smart_night_boost_target_time = "07:00"
        mock_area_with_schedule.current_temperature = 18.0
        mock_area_with_schedule.target_temperature = 21.0
        mock_area_with_schedule.schedules = {}
        mock_area_with_schedule.weather_entity_id = None
        
        # Learning engine predicts 30 minutes heating time
        scheduler_with_learning.learning_engine.async_predict_heating_time = AsyncMock(return_value=30)
        
        # Current time is 05:00 (well before optimal start time)
        now = datetime(2024, 1, 1, 5, 0)
        
        # Should log that it will start later
        await scheduler_with_learning._handle_smart_night_boost(mock_area_with_schedule, now)

    async def test_get_target_time_and_temp_from_schedule_with_preset(self, scheduler: ScheduleExecutor, mock_area_with_schedule):
        """Test getting target time and temp from schedule with preset mode."""
        mock_schedule = MagicMock()
        mock_schedule.start_time = "07:00"
        mock_schedule.preset_mode = "comfort"
        mock_schedule.temperature = None
        
        mock_area_with_schedule.comfort_temp = 22.0
        mock_area_with_schedule.use_global_comfort = False
        
        now = datetime(2024, 1, 1, 6, 0)
        
        target_time, target_temp = scheduler._get_target_time_and_temp_from_schedule(
            mock_area_with_schedule, mock_schedule, now
        )
        
        assert target_time.hour == 7
        assert target_time.minute == 0
        assert target_temp == 22.0

    async def test_get_target_time_and_temp_from_schedule_with_temperature(self, scheduler: ScheduleExecutor, mock_area_with_schedule):
        """Test getting target time and temp from schedule with explicit temperature."""
        mock_schedule = MagicMock()
        mock_schedule.start_time = "07:00"
        mock_schedule.preset_mode = None
        mock_schedule.temperature = 21.5
        
        now = datetime(2024, 1, 1, 6, 0)
        
        target_time, target_temp = scheduler._get_target_time_and_temp_from_schedule(
            mock_area_with_schedule, mock_schedule, now
        )
        
        assert target_time.hour == 7
        assert target_time.minute == 0
        assert target_temp == 21.5

    async def test_get_target_time_and_temp_fallback_to_area_target(self, scheduler: ScheduleExecutor, mock_area_with_schedule):
        """Test getting target time and temp falls back to area target temperature."""
        mock_schedule = MagicMock()
        mock_schedule.start_time = "07:00"
        mock_schedule.preset_mode = None
        mock_schedule.temperature = None
        
        mock_area_with_schedule.target_temperature = 20.0
        
        now = datetime(2024, 1, 1, 6, 0)
        
        target_time, target_temp = scheduler._get_target_time_and_temp_from_schedule(
            mock_area_with_schedule, mock_schedule, now
        )
        
        assert target_temp == 20.0

    async def test_get_target_time_and_temp_with_logger(self, scheduler: ScheduleExecutor, mock_area_with_schedule):
        """Test that target time/temp logging works when area_logger available."""
        mock_schedule = MagicMock()
        mock_schedule.start_time = "07:00"
        mock_schedule.preset_mode = "comfort"
        mock_schedule.temperature = None
        
        mock_area_with_schedule.comfort_temp = 22.0
        mock_area_with_schedule.use_global_comfort = False
        
        # Add area logger
        mock_logger = MagicMock()
        scheduler.area_logger = mock_logger
        
        now = datetime(2024, 1, 1, 6, 0)
        
        scheduler._get_target_time_and_temp_from_schedule(
            mock_area_with_schedule, mock_schedule, now
        )
        
        # Verify logger was called
        mock_logger.log_event.assert_called_once()

    async def test_get_target_time_from_config_returns_none_when_not_configured(self, scheduler: ScheduleExecutor, mock_area_with_schedule):
        """Test getting target time from config returns None when not configured."""
        mock_area_with_schedule.smart_night_boost_target_time = None
        
        now = datetime(2024, 1, 1, 6, 0)
        
        result = scheduler._get_target_time_from_config(mock_area_with_schedule, now)
        
        assert result is None

    async def test_get_target_time_from_config_returns_datetime(self, scheduler: ScheduleExecutor, mock_area_with_schedule):
        """Test getting target time from config returns proper datetime."""
        mock_area_with_schedule.smart_night_boost_target_time = "07:30"
        
        now = datetime(2024, 1, 1, 6, 0)
        
        result = scheduler._get_target_time_from_config(mock_area_with_schedule, now)
        
        assert result is not None
        assert result.hour == 7
        assert result.minute == 30


class TestGetOutdoorTemperatureEdgeCases:
    """Test outdoor temperature retrieval edge cases."""

    def test_get_outdoor_temperature_no_weather_entity(self, scheduler: ScheduleExecutor, hass: HomeAssistant, mock_area_with_schedule):
        """Test getting outdoor temp when no weather entity configured."""
        mock_area_with_schedule.weather_entity_id = None
        
        temp = scheduler._get_outdoor_temperature(mock_area_with_schedule)
        
        assert temp is None

    def test_get_outdoor_temperature_unknown_state(self, scheduler: ScheduleExecutor, hass: HomeAssistant, mock_area_with_schedule):
        """Test getting outdoor temp when weather entity is unknown."""
        mock_area_with_schedule.weather_entity_id = "weather.home"
        hass.states.async_set("weather.home", "unknown", {})
        
        temp = scheduler._get_outdoor_temperature(mock_area_with_schedule)
        
        assert temp is None

    def test_get_outdoor_temperature_unavailable_state(self, scheduler: ScheduleExecutor, hass: HomeAssistant, mock_area_with_schedule):
        """Test getting outdoor temp when weather entity is unavailable."""
        mock_area_with_schedule.weather_entity_id = "weather.home"
        hass.states.async_set("weather.home", "unavailable", {})
        
        temp = scheduler._get_outdoor_temperature(mock_area_with_schedule)
        
        assert temp is None

    def test_get_outdoor_temperature_invalid_value(self, scheduler: ScheduleExecutor, hass: HomeAssistant, mock_area_with_schedule):
        """Test getting outdoor temp when weather entity has invalid value."""
        mock_area_with_schedule.weather_entity_id = "weather.home"
        hass.states.async_set("weather.home", "not_a_number", {})
        
        temp = scheduler._get_outdoor_temperature(mock_area_with_schedule)
        
        assert temp is None
