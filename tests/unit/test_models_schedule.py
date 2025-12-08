"""Tests for Schedule model."""

from datetime import datetime
import pytest

from smart_heating.models.schedule import Schedule


class TestScheduleInitialization:
    """Test Schedule initialization."""

    def test_init_minimal(self):
        """Test minimal initialization."""
        schedule = Schedule("schedule1", "08:00")
        
        assert schedule.schedule_id == "schedule1"
        assert schedule.time == "08:00"
        assert schedule.start_time == "08:00"
        assert schedule.end_time == "23:59"
        assert schedule.enabled is True
        assert schedule.days == ["mon", "tue", "wed", "thu", "fri", "sat", "sun"]

    def test_init_with_temperature(self):
        """Test initialization with temperature."""
        schedule = Schedule("schedule1", "08:00", temperature=21.0)
        
        assert schedule.temperature == 21.0
        assert schedule.preset_mode is None

    def test_init_with_preset_mode(self):
        """Test initialization with preset mode."""
        schedule = Schedule("schedule1", "08:00", preset_mode="comfort")
        
        assert schedule.preset_mode == "comfort"
        assert schedule.temperature is None

    def test_init_with_days(self):
        """Test initialization with specific days."""
        schedule = Schedule("schedule1", "08:00", days=["mon", "wed", "fri"])
        
        assert schedule.days == ["mon", "wed", "fri"]
        assert schedule.day == "Monday"

    def test_init_with_day_name(self):
        """Test initialization with day name."""
        schedule = Schedule("schedule1", "08:00", day="Tuesday")
        
        assert schedule.day == "Tuesday"
        assert schedule.days == ["tue"]

    def test_init_with_start_end_time(self):
        """Test initialization with start and end time."""
        schedule = Schedule("schedule1", None, start_time="08:00", end_time="12:00")
        
        assert schedule.start_time == "08:00"
        assert schedule.end_time == "12:00"

    def test_init_with_date(self):
        """Test initialization with specific date."""
        schedule = Schedule("schedule1", "08:00", date="2024-12-25")
        
        assert schedule.date == "2024-12-25"
        assert schedule.day is None
        assert schedule.days is None

    def test_init_disabled(self):
        """Test initialization disabled."""
        schedule = Schedule("schedule1", "08:00", enabled=False)
        
        assert schedule.enabled is False


class TestIsActive:
    """Test schedule active checking."""

    def test_is_active_disabled(self):
        """Test disabled schedule is not active."""
        schedule = Schedule("schedule1", "08:00", enabled=False)
        current_time = datetime(2024, 1, 15, 9, 0)  # Monday 09:00
        
        assert schedule.is_active(current_time) is False

    def test_is_active_recurring_correct_day_before_time(self):
        """Test recurring schedule before start time."""
        schedule = Schedule("schedule1", "08:00", days=["mon"])
        current_time = datetime(2024, 1, 15, 7, 30)  # Monday 07:30
        
        assert schedule.is_active(current_time) is False

    def test_is_active_recurring_correct_day_at_time(self):
        """Test recurring schedule at start time."""
        schedule = Schedule("schedule1", "08:00", days=["mon"])
        current_time = datetime(2024, 1, 15, 8, 0)  # Monday 08:00
        
        assert schedule.is_active(current_time) is True

    def test_is_active_recurring_correct_day_after_time(self):
        """Test recurring schedule after start time."""
        schedule = Schedule("schedule1", "08:00", days=["mon"])
        current_time = datetime(2024, 1, 15, 10, 0)  # Monday 10:00
        
        assert schedule.is_active(current_time) is True

    def test_is_active_recurring_wrong_day(self):
        """Test recurring schedule on wrong day."""
        schedule = Schedule("schedule1", "08:00", days=["mon"])
        current_time = datetime(2024, 1, 16, 8, 0)  # Tuesday 08:00
        
        assert schedule.is_active(current_time) is False

    def test_is_active_recurring_no_days(self):
        """Test recurring schedule with no days defaults to all days."""
        schedule = Schedule("schedule1", "08:00", days=[])
        current_time = datetime(2024, 1, 15, 8, 0)  # Monday 08:00
        
        # Empty days list defaults to all days, so schedule is active
        assert schedule.is_active(current_time) is True
        assert schedule.days == ["mon", "tue", "wed", "thu", "fri", "sat", "sun"]

    def test_is_active_date_specific_correct_date_in_range(self):
        """Test date-specific schedule on correct date and time."""
        schedule = Schedule("schedule1", "08:00", date="2024-01-15", start_time="08:00", end_time="12:00")
        current_time = datetime(2024, 1, 15, 10, 0)  # 2024-01-15 10:00
        
        assert schedule.is_active(current_time) is True

    def test_is_active_date_specific_correct_date_before_range(self):
        """Test date-specific schedule on correct date but before time range."""
        schedule = Schedule("schedule1", "08:00", date="2024-01-15", start_time="08:00", end_time="12:00")
        current_time = datetime(2024, 1, 15, 7, 0)  # 2024-01-15 07:00
        
        assert schedule.is_active(current_time) is False

    def test_is_active_date_specific_correct_date_after_range(self):
        """Test date-specific schedule on correct date but after time range."""
        schedule = Schedule("schedule1", "08:00", date="2024-01-15", start_time="08:00", end_time="12:00")
        current_time = datetime(2024, 1, 15, 13, 0)  # 2024-01-15 13:00
        
        assert schedule.is_active(current_time) is False

    def test_is_active_date_specific_wrong_date(self):
        """Test date-specific schedule on wrong date."""
        schedule = Schedule("schedule1", "08:00", date="2024-01-15", start_time="08:00", end_time="12:00")
        current_time = datetime(2024, 1, 16, 10, 0)  # 2024-01-16 10:00
        
        assert schedule.is_active(current_time) is False


class TestToDict:
    """Test schedule to_dict conversion."""

    def test_to_dict_basic(self):
        """Test basic to_dict."""
        schedule = Schedule("schedule1", "08:00", temperature=21.0, days=["mon", "wed"])
        
        result = schedule.to_dict()
        
        assert result["id"] == "schedule1"
        assert result["start_time"] == "08:00"
        assert result["end_time"] == "23:59"
        assert result["temperature"] == 21.0
        assert result["enabled"] is True
        assert result["days"] == ["Monday", "Wednesday"]

    def test_to_dict_with_preset_mode(self):
        """Test to_dict with preset mode."""
        schedule = Schedule("schedule1", "08:00", preset_mode="comfort", days=["mon"])
        
        result = schedule.to_dict()
        
        assert result["preset_mode"] == "comfort"
        assert "temperature" not in result

    def test_to_dict_date_specific(self):
        """Test to_dict for date-specific schedule."""
        schedule = Schedule("schedule1", "08:00", date="2024-12-25", start_time="08:00", end_time="12:00")
        
        result = schedule.to_dict()
        
        assert result["date"] == "2024-12-25"
        assert "days" not in result

    def test_to_dict_with_day_name(self):
        """Test to_dict preserves day name for backwards compatibility."""
        schedule = Schedule("schedule1", "08:00", day="Tuesday")
        
        result = schedule.to_dict()
        
        assert result["day"] == "Tuesday"
        assert result["days"] == ["Tuesday"]


class TestFromDict:
    """Test schedule from_dict creation."""

    def test_from_dict_basic(self):
        """Test basic from_dict."""
        data = {
            "id": "schedule1",
            "start_time": "08:00",
            "end_time": "12:00",
            "temperature": 21.0,
            "days": ["Monday", "Wednesday"],
            "enabled": True
        }
        
        schedule = Schedule.from_dict(data)
        
        assert schedule.schedule_id == "schedule1"
        assert schedule.start_time == "08:00"
        assert schedule.end_time == "12:00"
        assert schedule.temperature == 21.0
        assert schedule.days == ["mon", "wed"]
        assert schedule.enabled is True

    def test_from_dict_with_preset_mode(self):
        """Test from_dict with preset mode."""
        data = {
            "id": "schedule1",
            "start_time": "08:00",
            "preset_mode": "comfort",
            "days": ["Monday"]
        }
        
        schedule = Schedule.from_dict(data)
        
        assert schedule.preset_mode == "comfort"
        assert schedule.temperature is None

    def test_from_dict_date_specific(self):
        """Test from_dict for date-specific schedule."""
        data = {
            "id": "schedule1",
            "start_time": "08:00",
            "end_time": "12:00",
            "date": "2024-12-25",
            "temperature": 21.0
        }
        
        schedule = Schedule.from_dict(data)
        
        assert schedule.date == "2024-12-25"
        assert schedule.temperature == 21.0

    def test_from_dict_legacy_format(self):
        """Test from_dict with legacy time field."""
        data = {
            "id": "schedule1",
            "time": "08:00",
            "temperature": 21.0,
            "days": ["mon", "wed"]
        }
        
        schedule = Schedule.from_dict(data)
        
        assert schedule.time == "08:00"
        assert schedule.days == ["mon", "wed"]

    def test_from_dict_with_day_name(self):
        """Test from_dict with single day name."""
        data = {
            "id": "schedule1",
            "start_time": "08:00",
            "day": "Tuesday",
            "temperature": 21.0
        }
        
        schedule = Schedule.from_dict(data)
        
        assert schedule.day == "Tuesday"

    def test_from_dict_filters_none_days(self):
        """Test from_dict filters out None values from days."""
        data = {
            "id": "schedule1",
            "start_time": "08:00",
            "days": ["Monday", None, "Wednesday"],
            "temperature": 21.0
        }
        
        schedule = Schedule.from_dict(data)
        
        # Should filter out None and convert to internal format
        assert schedule.days == ["mon", "wed"]
