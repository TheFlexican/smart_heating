"""Tests for sensor platform."""
from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from pytest_homeassistant_custom_component.common import MockConfigEntry

from smart_heating.sensor import async_setup_entry, SmartHeatingStatusSensor
from smart_heating.const import DOMAIN, STATE_INITIALIZED


@pytest.fixture
def mock_coordinator():
    """Create mock coordinator."""
    coordinator = MagicMock()
    coordinator.data = {
        "status": "ready",
        "area_count": 3,
    }
    coordinator.last_update_success = True
    return coordinator


@pytest.fixture
def mock_config_entry():
    """Create mock config entry."""
    return MockConfigEntry(
        domain=DOMAIN,
        data={"name": "Smart Heating"},
        entry_id="test_entry_id",
    )


@pytest.fixture
def sensor(mock_coordinator, mock_config_entry):
    """Create a SmartHeatingStatusSensor instance."""
    return SmartHeatingStatusSensor(mock_coordinator, mock_config_entry)


class TestSensorSetup:
    """Test sensor platform setup."""

    @pytest.mark.asyncio
    async def test_async_setup_entry(self, hass, mock_config_entry, mock_coordinator):
        """Test sensor platform setup."""
        # Add coordinator to hass.data
        hass.data[DOMAIN] = {mock_config_entry.entry_id: mock_coordinator}
        
        # Mock async_add_entities
        async_add_entities = AsyncMock()
        
        # Call setup
        await async_setup_entry(hass, mock_config_entry, async_add_entities)
        
        # Verify entities were added
        async_add_entities.assert_called_once()
        entities = async_add_entities.call_args[0][0]
        assert len(entities) == 1
        assert isinstance(entities[0], SmartHeatingStatusSensor)


class TestSmartHeatingStatusSensor:
    """Test SmartHeatingStatusSensor class."""

    def test_sensor_initialization(self, sensor, mock_config_entry):
        """Test sensor initialization."""
        assert sensor._attr_name == "Smart Heating Status"
        assert sensor._attr_unique_id == f"{mock_config_entry.entry_id}_status"
        assert sensor._attr_icon == "mdi:radiator"

    def test_native_value_with_data(self, sensor, mock_coordinator):
        """Test native_value property with coordinator data."""
        assert sensor.native_value == "ready"

    def test_native_value_custom_status(self, sensor, mock_coordinator):
        """Test native_value with custom status."""
        mock_coordinator.data = {"status": "initializing"}
        assert sensor.native_value == "initializing"

    def test_native_value_no_status(self, sensor, mock_coordinator):
        """Test native_value when status not in data."""
        mock_coordinator.data = {}
        assert sensor.native_value == STATE_INITIALIZED

    def test_native_value_no_data(self, sensor, mock_coordinator):
        """Test native_value when coordinator has no data."""
        mock_coordinator.data = None
        assert sensor.native_value == STATE_INITIALIZED

    def test_extra_state_attributes_with_data(self, sensor, mock_coordinator):
        """Test extra_state_attributes with coordinator data."""
        attributes = sensor.extra_state_attributes
        
        assert attributes["integration"] == "smart_heating"
        assert attributes["version"] == "2.0.0"
        assert attributes["area_count"] == 3

    def test_extra_state_attributes_no_area_count(self, sensor, mock_coordinator):
        """Test extra_state_attributes when area_count not in data."""
        mock_coordinator.data = {"status": "ready"}
        attributes = sensor.extra_state_attributes
        
        assert attributes["integration"] == "smart_heating"
        assert attributes["version"] == "2.0.0"
        assert attributes["area_count"] == 0

    def test_extra_state_attributes_no_data(self, sensor, mock_coordinator):
        """Test extra_state_attributes when coordinator has no data."""
        mock_coordinator.data = None
        attributes = sensor.extra_state_attributes
        
        assert attributes["integration"] == "smart_heating"
        assert attributes["version"] == "2.0.0"
        assert "area_count" not in attributes

    def test_available_true(self, sensor, mock_coordinator):
        """Test available property when coordinator update succeeded."""
        mock_coordinator.last_update_success = True
        assert sensor.available is True

    def test_available_false(self, sensor, mock_coordinator):
        """Test available property when coordinator update failed."""
        mock_coordinator.last_update_success = False
        assert sensor.available is False
