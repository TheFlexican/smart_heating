"""Tests for Switch platform."""
from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock

import pytest
from homeassistant.components.switch import SwitchEntity
from homeassistant.core import HomeAssistant

from smart_heating.switch import AreaSwitch, async_setup_entry

from tests.unit.const import TEST_AREA_ID, TEST_AREA_NAME


@pytest.fixture
def switch_entity(mock_coordinator, mock_config_entry) -> AreaSwitch:
    """Create a switch entity."""
    # Create a mock Area object
    mock_area = MagicMock()
    mock_area.area_id = TEST_AREA_ID
    mock_area.name = TEST_AREA_NAME
    mock_area.enabled = True
    
    return AreaSwitch(mock_coordinator, mock_config_entry, mock_area)


class TestSwitchEntitySetup:
    """Test switch entity setup."""

    async def test_async_setup_entry(
        self, hass: HomeAssistant, mock_config_entry, mock_coordinator
    ):
        """Test setting up switch entities."""
        # Create mock area
        mock_area = MagicMock()
        mock_area.area_id = TEST_AREA_ID
        mock_area.name = TEST_AREA_NAME
        
        # Set up coordinator with area
        mock_coordinator.area_manager.get_all_areas.return_value = {
            TEST_AREA_ID: mock_area
        }
        
        # Store coordinator in hass.data
        from smart_heating.const import DOMAIN
        hass.data[DOMAIN] = {mock_config_entry.entry_id: mock_coordinator}

        async_add_entities = AsyncMock()

        await async_setup_entry(hass, mock_config_entry, async_add_entities)

        # Should create switch entities
        assert async_add_entities.called
        call_args = async_add_entities.call_args
        entities = call_args[0][0]
        assert len(entities) == 1
        assert isinstance(entities[0], AreaSwitch)


class TestSwitchEntityProperties:
    """Test switch entity properties."""

    def test_name(self, switch_entity: AreaSwitch):
        """Test entity name."""
        # Name is "Zone {area.name} Control"
        assert switch_entity.name == f"Zone {TEST_AREA_NAME} Control"

    def test_unique_id(self, switch_entity: AreaSwitch, mock_config_entry):
        """Test unique ID."""
        # Unique ID is "{entry_id}_switch_{area_id}"
        assert switch_entity.unique_id == f"{mock_config_entry.entry_id}_switch_{TEST_AREA_ID}"

    def test_is_on_enabled(self, switch_entity: AreaSwitch):
        """Test is_on when area is enabled."""
        # Switch reads from self._area.enabled
        assert switch_entity.is_on is True

    def test_is_on_disabled(self, switch_entity: AreaSwitch):
        """Test is_on when area is disabled."""
        # Disable the area
        switch_entity._area.enabled = False
        assert switch_entity.is_on is False


class TestSwitchEntityActions:
    """Test switch entity actions."""

    async def test_async_turn_on(
        self, hass: HomeAssistant, switch_entity: AreaSwitch, mock_coordinator
    ):
        """Test turning on the switch."""
        switch_entity.hass = hass
        mock_coordinator.area_manager.enable_area = MagicMock()
        mock_coordinator.area_manager.async_save = AsyncMock()
        mock_coordinator.async_request_refresh = AsyncMock()

        await switch_entity.async_turn_on()

        # Should call area_manager.enable_area
        mock_coordinator.area_manager.enable_area.assert_called_once_with(TEST_AREA_ID)
        mock_coordinator.area_manager.async_save.assert_called_once()
        mock_coordinator.async_request_refresh.assert_called_once()

    async def test_async_turn_off(
        self, hass: HomeAssistant, switch_entity: AreaSwitch, mock_coordinator
    ):
        """Test turning off the switch."""
        switch_entity.hass = hass
        mock_coordinator.area_manager.disable_area = MagicMock()
        mock_coordinator.area_manager.async_save = AsyncMock()
        mock_coordinator.async_request_refresh = AsyncMock()

        await switch_entity.async_turn_off()

        # Should call area_manager.disable_area
        mock_coordinator.area_manager.disable_area.assert_called_once_with(TEST_AREA_ID)
        mock_coordinator.area_manager.async_save.assert_called_once()
        mock_coordinator.async_request_refresh.assert_called_once()

    async def test_async_toggle(
        self, hass: HomeAssistant, switch_entity: AreaSwitch, mock_coordinator
    ):
        """Test toggling the switch."""
        switch_entity.hass = hass
        mock_coordinator.area_manager.disable_area = MagicMock()
        mock_coordinator.area_manager.async_save = AsyncMock()
        mock_coordinator.async_request_refresh = AsyncMock()

        # Test toggle when on (should turn off)
        switch_entity._area.enabled = True

        await switch_entity.async_toggle()

        # Should call disable_area since it was on
        mock_coordinator.area_manager.disable_area.assert_called_once_with(TEST_AREA_ID)


class TestSwitchEntityAttributes:
    """Test switch entity extra attributes."""

    def test_extra_state_attributes(self, switch_entity: AreaSwitch):
        """Test extra state attributes."""
        # Mock area properties
        switch_entity._area.state = "heat"
        switch_entity._area.target_temperature = 21.5
        switch_entity._area.current_temperature = 20.0
        switch_entity._area.devices = {"device1": MagicMock(), "device2": MagicMock()}
        
        attrs = switch_entity.extra_state_attributes
        
        # Check attributes
        assert attrs["area_id"] == TEST_AREA_ID
        assert attrs["area_name"] == TEST_AREA_NAME
        assert attrs["area_state"] == "heat"
        assert attrs["target_temperature"] == 21.5
        assert attrs["current_temperature"] == 20.0
        assert attrs["device_count"] == 2

    def test_available_true(self, switch_entity: AreaSwitch, mock_coordinator):
        """Test available property when coordinator successful."""
        mock_coordinator.last_update_success = True
        
        assert switch_entity.available is True

    def test_available_false(self, switch_entity: AreaSwitch, mock_coordinator):
        """Test available property when coordinator failed."""
        mock_coordinator.last_update_success = False
        
        assert switch_entity.available is False
