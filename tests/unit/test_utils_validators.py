"""Tests for validators utility functions."""

from smart_heating.utils.validators import (
    _validate_days_list,
    _validate_time_format,
    validate_area_id,
    validate_entity_id,
    validate_schedule_data,
    validate_temperature,
)


class TestValidateTemperature:
    """Tests for temperature validation."""

    def test_validate_temperature_valid(self):
        """Test validating valid temperature."""
        is_valid, error = validate_temperature(20.5)
        assert is_valid is True
        assert error is None

    def test_validate_temperature_none(self):
        """Test validating None temperature."""
        is_valid, error = validate_temperature(None)
        assert is_valid is False
        assert "required" in error

    def test_validate_temperature_too_low(self):
        """Test validating temperature too low."""
        is_valid, error = validate_temperature(0.0)
        assert is_valid is False
        assert "between" in error

    def test_validate_temperature_too_high(self):
        """Test validating temperature too high."""
        is_valid, error = validate_temperature(40.0)
        assert is_valid is False
        assert "between" in error

    def test_validate_temperature_not_number(self):
        """Test validating non-number temperature."""
        is_valid, error = validate_temperature("invalid")
        assert is_valid is False
        assert "number" in error

    def test_validate_temperature_edge_min(self):
        """Test validating minimum temperature."""
        is_valid, error = validate_temperature(5.0)
        assert is_valid is True
        assert error is None

    def test_validate_temperature_edge_max(self):
        """Test validating maximum temperature."""
        is_valid, error = validate_temperature(35.0)
        assert is_valid is True
        assert error is None


class TestValidateAreaId:
    """Tests for area ID validation."""

    def test_validate_area_id_valid(self):
        """Test validating valid area ID."""
        is_valid, error = validate_area_id("living_room")
        assert is_valid is True
        assert error is None

    def test_validate_area_id_empty(self):
        """Test validating empty area ID."""
        is_valid, error = validate_area_id("")
        assert is_valid is False
        assert "required" in error

    def test_validate_area_id_not_string(self):
        """Test validating non-string area ID."""
        is_valid, error = validate_area_id(123)
        assert is_valid is False
        assert "string" in error


class TestValidateTimeFormat:
    """Tests for time format validation."""

    def test_validate_time_format_valid(self):
        """Test validating valid time."""
        is_valid, error = _validate_time_format("08:30")
        assert is_valid is True
        assert error is None

    def test_validate_time_format_no_colon(self):
        """Test validating time without colon."""
        is_valid, error = _validate_time_format("0830")
        assert is_valid is False
        assert "HH:MM" in error

    def test_validate_time_format_invalid_hour(self):
        """Test validating invalid hour."""
        is_valid, error = _validate_time_format("25:00")
        assert is_valid is False
        assert "hours" in error

    def test_validate_time_format_invalid_minute(self):
        """Test validating invalid minute."""
        is_valid, error = _validate_time_format("08:60")
        assert is_valid is False
        assert "minutes" in error

    def test_validate_time_format_edge_cases(self):
        """Test validating edge case times."""
        assert _validate_time_format("00:00")[0] is True
        assert _validate_time_format("23:59")[0] is True


class TestValidateDaysList:
    """Tests for days list validation."""

    def test_validate_days_list_valid(self):
        """Test validating valid days list."""
        is_valid, error = _validate_days_list([0, 1, 2])
        assert is_valid is True
        assert error is None

    def test_validate_days_list_empty(self):
        """Test validating empty days list."""
        is_valid, error = _validate_days_list([])
        assert is_valid is False
        assert "non-empty" in error

    def test_validate_days_list_not_list(self):
        """Test validating non-list."""
        is_valid, error = _validate_days_list("monday")
        assert is_valid is False
        assert "list" in error

    def test_validate_days_list_invalid_day(self):
        """Test validating invalid day."""
        is_valid, error = _validate_days_list([0, "invalid"])
        assert is_valid is False
        assert "invalid day" in error


class TestValidateScheduleData:
    """Tests for schedule data validation."""

    def test_validate_schedule_data_valid(self):
        """Test validating valid schedule data."""
        data = {"time": "08:00", "temperature": 21.0, "days": [0, 1, 2]}
        is_valid, error = validate_schedule_data(data)
        assert is_valid is True
        assert error is None

    def test_validate_schedule_data_missing_time(self):
        """Test validating schedule data without time."""
        data = {"temperature": 21.0, "days": [0]}
        is_valid, error = validate_schedule_data(data)
        assert is_valid is False
        assert "time" in error

    def test_validate_schedule_data_missing_temperature(self):
        """Test validating schedule data without temperature."""
        data = {"time": "08:00", "days": [0]}
        is_valid, error = validate_schedule_data(data)
        assert is_valid is False
        assert "temperature" in error

    def test_validate_schedule_data_missing_days(self):
        """Test validating schedule data without days."""
        data = {"time": "08:00", "temperature": 21.0}
        is_valid, error = validate_schedule_data(data)
        assert is_valid is False
        assert "days" in error


class TestValidateEntityId:
    """Tests for entity ID validation."""

    def test_validate_entity_id_valid(self):
        """Test validating valid entity ID."""
        is_valid, error = validate_entity_id("climate.living_room")
        assert is_valid is True
        assert error is None

    def test_validate_entity_id_empty(self):
        """Test validating empty entity ID."""
        is_valid, error = validate_entity_id("")
        assert is_valid is False
        assert "required" in error

    def test_validate_entity_id_not_string(self):
        """Test validating non-string entity ID."""
        is_valid, error = validate_entity_id(123)
        assert is_valid is False
        assert "string" in error

    def test_validate_entity_id_no_domain(self):
        """Test validating entity ID without domain."""
        is_valid, error = validate_entity_id("livingroom")
        assert is_valid is False
        assert "domain.object_id" in error


class TestValidatorsEdgeCases:
    """Test edge cases in validators."""

    def test_validate_time_format_exception_handling(self):
        """Test time format validation with invalid types."""
        # This should trigger the except (ValueError, AttributeError) block
        is_valid, error = _validate_time_format(None)
        assert is_valid is False
        assert "HH:MM format" in error or "invalid time format" in error

    def test_validate_schedule_data_missing_time(self):
        """Test schedule validation missing time field."""
        data = {"temperature": 20.0, "days": [0]}
        is_valid, error = validate_schedule_data(data)
        assert is_valid is False
        assert "time is required" in error

    def test_validate_schedule_data_missing_temperature(self):
        """Test schedule validation missing temperature field."""
        data = {"time": "08:00", "days": [0]}
        is_valid, error = validate_schedule_data(data)
        assert is_valid is False
        assert "temperature is required" in error

    def test_validate_schedule_data_missing_days(self):
        """Test schedule validation missing days field."""
        data = {"time": "08:00", "temperature": 20.0}
        is_valid, error = validate_schedule_data(data)
        assert is_valid is False
        assert "days is required" in error
