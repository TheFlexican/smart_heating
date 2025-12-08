"""Tests for utility modules."""
from __future__ import annotations

from unittest.mock import MagicMock

import pytest

from smart_heating.utils.validators import (
    validate_temperature,
    validate_schedule_data,
    validate_area_id,
    validate_entity_id,
)
from smart_heating.utils.response_builders import (
    build_area_response,
    build_device_info,
)
from smart_heating.models.area import Area

from tests.unit.const import TEST_TEMPERATURE


class TestValidators:
    """Test validation functions."""

    def test_validate_temperature_valid(self):
        """Test temperature validation with valid value."""
        is_valid, error = validate_temperature(TEST_TEMPERATURE)
        assert is_valid is True
        assert error is None
        
        is_valid, error = validate_temperature(5.0)
        assert is_valid is True
        
        is_valid, error = validate_temperature(35.0)
        assert is_valid is True

    def test_validate_temperature_invalid(self):
        """Test temperature validation with invalid values."""
        is_valid, error = validate_temperature(4.0)
        assert is_valid is False
        assert error is not None
        
        is_valid, error = validate_temperature(36.0)
        assert is_valid is False
        assert error is not None
        
        is_valid, error = validate_temperature("not_a_number")
        assert is_valid is False
        assert error is not None
        
        is_valid, error = validate_temperature(None)
        assert is_valid is False
        assert "required" in error.lower()

    def test_validate_area_id_valid(self):
        """Test area ID validation with valid value."""
        is_valid, error = validate_area_id("living_room")
        assert is_valid is True
        assert error is None

    def test_validate_area_id_invalid(self):
        """Test area ID validation with invalid values."""
        is_valid, error = validate_area_id("")
        assert is_valid is False
        
        is_valid, error = validate_area_id(None)
        assert is_valid is False

    def test_validate_entity_id_valid(self):
        """Test entity ID validation with valid value."""
        is_valid, error = validate_entity_id("climate.living_room")
        assert is_valid is True
        assert error is None
        
        is_valid, error = validate_entity_id("sensor.temperature")
        assert is_valid is True

    def test_validate_entity_id_invalid(self):
        """Test entity ID validation with invalid values."""
        is_valid, error = validate_entity_id("invalid")
        assert is_valid is False
        
        is_valid, error = validate_entity_id("")
        assert is_valid is False

    def test_validate_schedule_data_valid(self):
        """Test schedule data validation with valid data."""
        schedule_data = {
            "time": "07:00",
            "temperature": 21.0,
            "days": ["mon", "tue"],
            "enabled": True,
        }
        is_valid, error = validate_schedule_data(schedule_data)
        assert is_valid is True
        assert error is None

    def test_validate_schedule_data_invalid(self):
        """Test schedule data validation with invalid data."""
        # Missing required field
        schedule_data = {
            "temperature": 21.0,
            "days": ["mon"],
        }
        is_valid, error = validate_schedule_data(schedule_data)
        assert is_valid is False
        
        # Invalid time format - missing colon
        schedule_data = {
            "time": "0700",
            "temperature": 21.0,
            "days": ["mon"],
        }
        is_valid, error = validate_schedule_data(schedule_data)
        assert is_valid is False
        
        # Invalid hours
        schedule_data = {
            "time": "25:00",
            "temperature": 21.0,
            "days": ["mon"],
        }
        is_valid, error = validate_schedule_data(schedule_data)
        assert is_valid is False
        
        # Invalid minutes
        schedule_data = {
            "time": "12:60",
            "temperature": 21.0,
            "days": ["mon"],
        }
        is_valid, error = validate_schedule_data(schedule_data)
        assert is_valid is False
        
        # Invalid day
        schedule_data = {
            "time": "07:00",
            "temperature": 21.0,
            "days": ["monday"],  # Should be "mon"
        }
        is_valid, error = validate_schedule_data(schedule_data)
        assert is_valid is False
        
        # Invalid time - non-numeric hours/minutes (triggers ValueError in int())
        schedule_data = {
            "time": "ab:cd",
            "temperature": 21.0,
            "days": ["mon"],
        }
        is_valid, error = validate_schedule_data(schedule_data)
        assert is_valid is False
        assert "invalid time format" in error.lower()
        
        # Invalid temperature in schedule data
        schedule_data = {
            "time": "07:00",
            "temperature": None,
            "days": ["mon"],
        }
        is_valid, error = validate_schedule_data(schedule_data)
        assert is_valid is False
        assert "temperature" in error.lower()


class TestResponseBuilders:
    """Test response builder functions."""

    def test_build_area_response(self):
        """Test building area response."""
        area = Area(
            area_id="living_room",
            name="Living Room",
            target_temperature=21.0,
        )
        
        response = build_area_response(area)
        
        assert response is not None
        assert isinstance(response, dict)

    def test_build_device_info(self):
        """Test building device info."""
        device_data = {
            "type": "thermostat",
            "mqtt_topic": None,
            "entity_id": "climate.living_room",
        }
        
        info = build_device_info("climate.living_room", device_data)
        
        assert info is not None
        assert isinstance(info, dict)
