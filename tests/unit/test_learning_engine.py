"""Tests for learning engine.

Tests the adaptive learning engine including heating event tracking,
statistics recording, and prediction functionality.
"""

import statistics
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from smart_heating.learning_engine import HeatingEvent, LearningEngine, MIN_LEARNING_EVENTS


@pytest.fixture
def mock_hass():
    """Create a mock Home Assistant instance."""
    hass = MagicMock()
    hass.states = MagicMock()
    hass.states.async_entity_ids = MagicMock(return_value=[])
    hass.states.get = MagicMock(return_value=None)
    return hass


@pytest.fixture
def learning_engine(mock_hass):
    """Create a learning engine instance."""
    return LearningEngine(mock_hass)


class TestHeatingEvent:
    """Tests for HeatingEvent class."""

    def test_heating_event_creation(self):
        """Test creating a heating event."""
        start_time = datetime.now()
        end_time = start_time + timedelta(minutes=30)
        
        event = HeatingEvent(
            area_id="living_room",
            start_time=start_time,
            end_time=end_time,
            start_temp=18.0,
            end_temp=21.0,
            outdoor_temp=10.0,
        )
        
        assert event.area_id == "living_room"
        assert event.start_time == start_time
        assert event.end_time == end_time
        assert event.start_temp == 18.0
        assert event.end_temp == 21.0
        assert event.outdoor_temp == 10.0
        assert event.duration_minutes == 30.0
        assert event.temp_change == 3.0
        assert event.heating_rate == pytest.approx(0.1, abs=0.01)  # 3°C / 30min

    def test_heating_event_no_outdoor_temp(self):
        """Test creating event without outdoor temperature."""
        start_time = datetime.now()
        end_time = start_time + timedelta(minutes=20)
        
        event = HeatingEvent(
            area_id="bedroom",
            start_time=start_time,
            end_time=end_time,
            start_temp=19.0,
            end_temp=21.0,
        )
        
        assert event.outdoor_temp is None
        assert event.duration_minutes == 20.0
        assert event.temp_change == 2.0

    def test_heating_event_zero_duration(self):
        """Test handling zero duration."""
        now = datetime.now()
        
        event = HeatingEvent(
            area_id="test",
            start_time=now,
            end_time=now,
            start_temp=20.0,
            end_temp=20.0,
        )
        
        assert event.duration_minutes == 0.0
        assert event.heating_rate == 0.0


class TestLearningEngineSetup:
    """Tests for learning engine setup."""

    def test_initialization(self, learning_engine):
        """Test learning engine initialization."""
        assert learning_engine._active_heating_events == {}
        assert learning_engine._weather_entity is None

    @pytest.mark.asyncio
    async def test_async_setup_with_weather_entity(self, learning_engine, mock_hass):
        """Test setup with available weather entity."""
        weather_state = MagicMock()
        weather_state.state = "sunny"
        
        mock_hass.states.async_entity_ids.return_value = ["weather.home"]
        mock_hass.states.get.return_value = weather_state
        
        with patch.object(learning_engine, '_async_register_statistics_metadata', AsyncMock()):
            await learning_engine.async_setup()
        
        assert learning_engine._weather_entity == "weather.home"

    @pytest.mark.asyncio
    async def test_async_setup_no_weather_entity(self, learning_engine, mock_hass):
        """Test setup without weather entity."""
        mock_hass.states.async_entity_ids.return_value = []
        
        with patch.object(learning_engine, '_async_register_statistics_metadata', AsyncMock()):
            await learning_engine.async_setup()
        
        assert learning_engine._weather_entity is None

    @pytest.mark.asyncio
    async def test_detect_weather_entity_unavailable(self, learning_engine, mock_hass):
        """Test detection skips unavailable weather entities."""
        weather_state = MagicMock()
        weather_state.state = "unavailable"
        
        mock_hass.states.async_entity_ids.return_value = ["weather.home"]
        mock_hass.states.get.return_value = weather_state
        
        entity = await learning_engine._async_detect_weather_entity()
        assert entity is None


class TestHeatingEventTracking:
    """Tests for heating event tracking."""

    @pytest.mark.asyncio
    async def test_start_heating_event(self, learning_engine):
        """Test starting a heating event."""
        with patch.object(learning_engine, '_async_get_outdoor_temperature', AsyncMock(return_value=12.0)):
            await learning_engine.async_start_heating_event("living_room", 19.0)
        
        assert "living_room" in learning_engine._active_heating_events
        event = learning_engine._active_heating_events["living_room"]
        assert event["start_temp"] == 19.0
        assert event["outdoor_temp"] == 12.0
        assert "start_time" in event

    @pytest.mark.asyncio
    async def test_start_heating_event_no_outdoor_temp(self, learning_engine):
        """Test starting event without outdoor temperature."""
        with patch.object(learning_engine, '_async_get_outdoor_temperature', AsyncMock(return_value=None)):
            await learning_engine.async_start_heating_event("bedroom", 18.0)
        
        event = learning_engine._active_heating_events["bedroom"]
        assert event["outdoor_temp"] is None

    @pytest.mark.asyncio
    async def test_end_heating_event_no_active_event(self, learning_engine):
        """Test ending event when none active."""
        await learning_engine.async_end_heating_event("living_room", 21.0)
        
        # Should handle gracefully (no error)
        assert "living_room" not in learning_engine._active_heating_events

    @pytest.mark.asyncio
    async def test_end_heating_event_short_duration(self, learning_engine):
        """Test ending event with too short duration (< 5 minutes)."""
        # Start event
        learning_engine._active_heating_events["living_room"] = {
            "start_time": datetime.now(),  # Very recent
            "start_temp": 19.0,
            "outdoor_temp": 10.0,
        }
        
        with patch.object(learning_engine, '_async_record_heating_event', AsyncMock()) as mock_record:
            await learning_engine.async_end_heating_event("living_room", 19.5)
        
        # Should not record (too short)
        mock_record.assert_not_called()
        assert "living_room" not in learning_engine._active_heating_events

    @pytest.mark.asyncio
    async def test_end_heating_event_insignificant_change(self, learning_engine):
        """Test ending event with insignificant temperature change (< 0.1°C)."""
        learning_engine._active_heating_events["living_room"] = {
            "start_time": datetime.now() - timedelta(minutes=10),
            "start_temp": 19.0,
            "outdoor_temp": 10.0,
        }
        
        with patch.object(learning_engine, '_async_record_heating_event', AsyncMock()) as mock_record:
            await learning_engine.async_end_heating_event("living_room", 19.05)  # Only 0.05°C change
        
        # Should not record (insignificant change)
        mock_record.assert_not_called()

    @pytest.mark.asyncio
    async def test_end_heating_event_valid(self, learning_engine):
        """Test ending event with valid data."""
        learning_engine._active_heating_events["living_room"] = {
            "start_time": datetime.now() - timedelta(minutes=30),
            "start_temp": 18.0,
            "outdoor_temp": 10.0,
        }
        
        with patch.object(learning_engine, '_async_record_heating_event', AsyncMock()) as mock_record:
            await learning_engine.async_end_heating_event("living_room", 21.0)
        
        # Should record the event
        mock_record.assert_called_once()
        call_args = mock_record.call_args[0][0]
        assert isinstance(call_args, HeatingEvent)
        assert call_args.area_id == "living_room"
        assert call_args.start_temp == 18.0
        assert call_args.end_temp == 21.0
        assert "living_room" not in learning_engine._active_heating_events


class TestStatistics:
    """Tests for statistics functionality."""

    def test_get_statistic_id(self, learning_engine):
        """Test generating statistic IDs."""
        stat_id = learning_engine._get_statistic_id("heating_rate", "living_room")
        assert stat_id == "smart_heating:heating_rate_living_room"

    @pytest.mark.asyncio
    async def test_async_register_statistics_metadata(self, learning_engine):
        """Test registering statistics metadata (does nothing in current implementation)."""
        # This method currently does nothing (just passes)
        await learning_engine._async_register_statistics_metadata()
        # No error means success
        assert True


class TestOutdoorTemperature:
    """Tests for outdoor temperature functionality."""

    @pytest.mark.asyncio
    async def test_get_outdoor_temperature_no_entity(self, learning_engine):
        """Test getting outdoor temperature without entity."""
        learning_engine._weather_entity = None
        
        temp = await learning_engine._async_get_outdoor_temperature()
        assert temp is None

    @pytest.mark.asyncio
    async def test_get_outdoor_temperature_success(self, learning_engine, mock_hass):
        """Test getting outdoor temperature successfully."""
        learning_engine._weather_entity = "weather.home"
        
        state = MagicMock()
        state.attributes = {"temperature": 12.5}
        mock_hass.states.get.return_value = state
        
        temp = await learning_engine._async_get_outdoor_temperature()
        assert temp == 12.5

    @pytest.mark.asyncio
    async def test_get_outdoor_temperature_invalid(self, learning_engine, mock_hass):
        """Test handling invalid outdoor temperature."""
        learning_engine._weather_entity = "weather.home"
        
        state = MagicMock()
        state.attributes = {"temperature": "invalid"}
        mock_hass.states.get.return_value = state
        
        temp = await learning_engine._async_get_outdoor_temperature()
        assert temp is None

    @pytest.mark.asyncio
    async def test_calculate_outdoor_adjustment_warm(self, learning_engine):
        """Test outdoor adjustment when warm outside."""
        adjustment = await learning_engine._async_calculate_outdoor_adjustment(18.0)
        assert adjustment == 1.1

    @pytest.mark.asyncio
    async def test_calculate_outdoor_adjustment_moderate(self, learning_engine):
        """Test outdoor adjustment when moderate temperature."""
        adjustment = await learning_engine._async_calculate_outdoor_adjustment(10.0)
        assert adjustment == 1.0

    @pytest.mark.asyncio
    async def test_calculate_outdoor_adjustment_cold(self, learning_engine):
        """Test outdoor adjustment when cold outside."""
        adjustment = await learning_engine._async_calculate_outdoor_adjustment(2.0)
        assert adjustment == 0.9

    @pytest.mark.asyncio
    async def test_calculate_outdoor_adjustment_very_cold(self, learning_engine):
        """Test outdoor adjustment when very cold outside."""
        adjustment = await learning_engine._async_calculate_outdoor_adjustment(-5.0)
        assert adjustment == 0.8


class TestPredictions:
    """Tests for prediction functionality."""

    @pytest.mark.asyncio
    async def test_predict_heating_time_insufficient_data(self, learning_engine):
        """Test prediction with insufficient data."""
        with patch.object(learning_engine, '_async_get_recent_heating_rates', AsyncMock(return_value=[])):
            result = await learning_engine.async_predict_heating_time("living_room", 18.0, 21.0)
        
        assert result is None

    @pytest.mark.asyncio
    async def test_predict_heating_time_success(self, learning_engine):
        """Test successful heating time prediction."""
        # Mock sufficient heating rate data
        heating_rates = [0.1] * MIN_LEARNING_EVENTS  # 0.1°C/min
        
        with patch.object(learning_engine, '_async_get_recent_heating_rates', AsyncMock(return_value=heating_rates)):
            with patch.object(learning_engine, '_async_get_outdoor_temperature', AsyncMock(return_value=None)):
                result = await learning_engine.async_predict_heating_time("living_room", 18.0, 21.0)
        
        # 3°C change at 0.1°C/min = 30 minutes
        assert result == 30

    @pytest.mark.asyncio
    async def test_predict_heating_time_with_outdoor_adjustment(self, learning_engine):
        """Test prediction with outdoor temperature adjustment."""
        heating_rates = [0.1] * MIN_LEARNING_EVENTS
        
        with patch.object(learning_engine, '_async_get_recent_heating_rates', AsyncMock(return_value=heating_rates)):
            with patch.object(learning_engine, '_async_get_outdoor_temperature', AsyncMock(return_value=15.0)):
                with patch.object(learning_engine, '_async_calculate_outdoor_adjustment', AsyncMock(return_value=1.1)):
                    result = await learning_engine.async_predict_heating_time("living_room", 18.0, 21.0)
        
        # 3°C at 0.1°C/min * 1.1 adjustment = 27.3 minutes (rounds to 27)
        assert result == 27

    @pytest.mark.asyncio
    async def test_predict_heating_time_already_warm(self, learning_engine):
        """Test prediction when current temp >= target."""
        heating_rates = [0.1] * MIN_LEARNING_EVENTS
        
        with patch.object(learning_engine, '_async_get_recent_heating_rates', AsyncMock(return_value=heating_rates)):
            result = await learning_engine.async_predict_heating_time("living_room", 22.0, 21.0)
        
        assert result == 0


class TestLearningStats:
    """Tests for learning statistics."""

    @pytest.mark.asyncio
    async def test_get_learning_stats_no_data(self, learning_engine):
        """Test getting learning stats with no data."""
        with patch.object(learning_engine, '_async_get_recent_heating_rates', AsyncMock(return_value=[])):
            stats = await learning_engine.async_get_learning_stats("living_room")
        
        assert stats["data_points"] == 0
        assert stats["avg_heating_rate"] == 0
        assert stats["ready_for_predictions"] is False

    @pytest.mark.asyncio
    async def test_get_learning_stats_with_data(self, learning_engine):
        """Test getting learning stats with data."""
        heating_rates = [0.08, 0.10, 0.12, 0.09, 0.11] * 4  # 20 data points
        
        learning_engine._weather_entity = "weather.home"
        
        with patch.object(learning_engine, '_async_get_recent_heating_rates', AsyncMock(return_value=heating_rates)):
            stats = await learning_engine.async_get_learning_stats("living_room")
        
        assert stats["data_points"] == 20
        assert stats["avg_heating_rate"] == pytest.approx(0.10, abs=0.01)
        assert stats["min_heating_rate"] == 0.08
        assert stats["max_heating_rate"] == 0.12
        assert stats["ready_for_predictions"] is True
        assert stats["outdoor_temp_available"] is True

    @pytest.mark.asyncio
    async def test_calculate_smart_night_boost(self, learning_engine):
        """Test smart night boost calculation (not yet implemented)."""
        result = await learning_engine.async_calculate_smart_night_boost("living_room")
        
        # Returns None until implemented
        assert result is None
