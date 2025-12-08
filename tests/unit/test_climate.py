"""Tests for Climate platform."""
from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from homeassistant.components.climate import (
    HVACMode,
    ClimateEntityFeature,
    ATTR_TEMPERATURE,
    ATTR_PRESET_MODE,
)
from homeassistant.const import ATTR_ENTITY_ID
from homeassistant.core import HomeAssistant

from smart_heating.climate import (
    AreaClimate,
    async_setup_entry,
)
from smart_heating.const import (
    PRESET_COMFORT,
    PRESET_ECO,
    PRESET_AWAY,
)

from tests.unit.const import TEST_AREA_ID, TEST_AREA_NAME, TEST_TEMPERATURE


@pytest.fixture
def climate_entity(hass: HomeAssistant, mock_coordinator, mock_config_entry) -> AreaClimate:
    """Create a climate entity."""
    # Create a mock Area object
    mock_area = MagicMock()
    mock_area.area_id = TEST_AREA_ID
    mock_area.name = TEST_AREA_NAME
    mock_area.current_temperature = 20.0
    mock_area.target_temperature = 21.0
    mock_area.enabled = True
    mock_area.state = "heat"
    mock_area.preset_mode = PRESET_COMFORT
    mock_area.hvac_mode = "heat"
    mock_area.boost_mode_active = False
    
    return AreaClimate(mock_coordinator, mock_config_entry, mock_area)


class TestClimateEntitySetup:
    """Test climate entity setup."""

    async def test_async_setup_entry(
        self, hass: HomeAssistant, mock_config_entry, mock_coordinator
    ):
        """Test setting up climate entities."""
        # Create mock area
        mock_area = MagicMock()
        mock_area.area_id = TEST_AREA_ID
        mock_area.name = TEST_AREA_NAME
        
        # Set up coordinator with area
        mock_coordinator.area_manager.get_all_areas.return_value = {
            TEST_AREA_ID: mock_area
        }
        
        # Store coordinator in hass.data as async_setup_entry expects
        from smart_heating.const import DOMAIN
        hass.data[DOMAIN] = {mock_config_entry.entry_id: mock_coordinator}

        async_add_entities = AsyncMock()
        
        await async_setup_entry(
            hass, mock_config_entry, async_add_entities
        )
        
        # Should have created climate entities
        assert async_add_entities.called
        call_args = async_add_entities.call_args
        entities = call_args[0][0]
        assert len(entities) == 1
        assert isinstance(entities[0], AreaClimate)


class TestClimateEntityProperties:
    """Test climate entity properties."""

    def test_name(self, climate_entity: AreaClimate):
        """Test entity name."""
        # Name is "Zone {area.name}"
        assert climate_entity.name == f"Zone {TEST_AREA_NAME}"

    def test_unique_id(self, climate_entity: AreaClimate, mock_config_entry):
        """Test unique ID."""
        # Unique ID is "{entry_id}_climate_{area_id}"
        assert climate_entity.unique_id == f"{mock_config_entry.entry_id}_climate_{TEST_AREA_ID}"

    def test_supported_features(self, climate_entity: AreaClimate):
        """Test supported features."""
        features = climate_entity.supported_features
        assert features & ClimateEntityFeature.TARGET_TEMPERATURE
        assert features & ClimateEntityFeature.TURN_OFF
        assert features & ClimateEntityFeature.TURN_ON

    def test_hvac_modes(self, climate_entity: AreaClimate):
        """Test HVAC modes."""
        modes = climate_entity.hvac_modes
        assert HVACMode.HEAT in modes
        assert HVACMode.OFF in modes

    def test_temperature_unit(self, climate_entity: AreaClimate):
        """Test temperature unit."""
        from homeassistant.const import UnitOfTemperature
        assert climate_entity.temperature_unit == UnitOfTemperature.CELSIUS

    def test_min_temp(self, climate_entity: AreaClimate):
        """Test minimum temperature."""
        assert climate_entity.min_temp == 5.0

    def test_max_temp(self, climate_entity: AreaClimate):
        """Test maximum temperature."""
        assert climate_entity.max_temp == 30.0

    def test_target_temperature_step(self, climate_entity: AreaClimate):
        """Test temperature step."""
        assert climate_entity.target_temperature_step == 0.5


class TestClimateEntityState:
    """Test climate entity state."""

    def test_current_temperature(self, climate_entity: AreaClimate):
        """Test current temperature property."""
        # AreaClimate reads from self._area.current_temperature
        assert climate_entity.current_temperature == 20.0

    def test_target_temperature(self, climate_entity: AreaClimate):
        """Test target temperature property."""
        # AreaClimate reads from self._area.target_temperature
        assert climate_entity.target_temperature == 21.0

    def test_hvac_mode_enabled(self, climate_entity: AreaClimate):
        """Test HVAC mode when enabled."""
        # Area is enabled in fixture
        assert climate_entity.hvac_mode == HVACMode.HEAT

    def test_hvac_mode_disabled(self, climate_entity: AreaClimate):
        """Test HVAC mode when disabled."""
        # Disable the area
        climate_entity._area.enabled = False
        assert climate_entity.hvac_mode == HVACMode.OFF


class TestClimateEntityActions:
    """Test climate entity actions."""

    async def test_async_set_temperature(
        self, hass: HomeAssistant, climate_entity: AreaClimate, mock_coordinator
    ):
        """Test setting temperature."""
        climate_entity.hass = hass
        mock_coordinator.area_manager.set_area_target_temperature = MagicMock()
        mock_coordinator.area_manager.async_save = AsyncMock()
        mock_coordinator.async_request_refresh = AsyncMock()

        await climate_entity.async_set_temperature(**{ATTR_TEMPERATURE: 22.0})

        # Should call area_manager to set temperature
        mock_coordinator.area_manager.set_area_target_temperature.assert_called_once_with(
            TEST_AREA_ID, 22.0
        )
        mock_coordinator.area_manager.async_save.assert_called_once()
        mock_coordinator.async_request_refresh.assert_called_once()

    async def test_async_set_hvac_mode_heat(
        self, hass: HomeAssistant, climate_entity: AreaClimate, mock_coordinator
    ):
        """Test setting HVAC mode to heat."""
        climate_entity.hass = hass
        mock_coordinator.area_manager.enable_area = MagicMock()
        mock_coordinator.area_manager.async_save = AsyncMock()
        mock_coordinator.async_request_refresh = AsyncMock()

        await climate_entity.async_set_hvac_mode(HVACMode.HEAT)

        # Should enable the area
        mock_coordinator.area_manager.enable_area.assert_called_once_with(TEST_AREA_ID)

    async def test_async_set_hvac_mode_off(
        self, hass: HomeAssistant, climate_entity: AreaClimate, mock_coordinator
    ):
        """Test setting HVAC mode to off."""
        climate_entity.hass = hass
        mock_coordinator.area_manager.disable_area = MagicMock()
        mock_coordinator.area_manager.async_save = AsyncMock()
        mock_coordinator.async_request_refresh = AsyncMock()

        await climate_entity.async_set_hvac_mode(HVACMode.OFF)

        # Should disable the area
        mock_coordinator.area_manager.disable_area.assert_called_once_with(TEST_AREA_ID)

    async def test_async_set_temperature_no_temperature(
        self, hass: HomeAssistant, climate_entity: AreaClimate, mock_coordinator
    ):
        """Test setting temperature when no temperature provided."""
        climate_entity.hass = hass
        mock_coordinator.area_manager.set_area_target_temperature = MagicMock()
        
        # Call without temperature
        await climate_entity.async_set_temperature()
        
        # Should not call set_area_target_temperature
        mock_coordinator.area_manager.set_area_target_temperature.assert_not_called()


class TestClimateEntityAttributes:
    """Test climate entity extra attributes."""

    def test_extra_state_attributes(self, climate_entity: AreaClimate):
        """Test extra state attributes."""
        # Mock device methods
        climate_entity._area.devices = {"device1": MagicMock(), "device2": MagicMock()}
        climate_entity._area.get_thermostats = MagicMock(return_value=["thermostat1"])
        climate_entity._area.get_temperature_sensors = MagicMock(return_value=["sensor1"])
        climate_entity._area.get_opentherm_gateways = MagicMock(return_value=["gateway1"])
        
        attrs = climate_entity.extra_state_attributes
        
        # Check basic attributes
        assert attrs["area_id"] == TEST_AREA_ID
        assert attrs["area_name"] == TEST_AREA_NAME
        assert attrs["area_state"] == "heat"
        assert attrs["device_count"] == 2
        assert attrs["devices"] == ["device1", "device2"]
        
        # Check device type attributes
        assert attrs["thermostats"] == ["thermostat1"]
        assert attrs["temperature_sensors"] == ["sensor1"]
        assert attrs["opentherm_gateways"] == ["gateway1"]

    def test_extra_state_attributes_no_devices(self, climate_entity: AreaClimate):
        """Test extra state attributes when no devices of specific types."""
        # Mock empty device lists
        climate_entity._area.devices = {}
        climate_entity._area.get_thermostats = MagicMock(return_value=[])
        climate_entity._area.get_temperature_sensors = MagicMock(return_value=[])
        climate_entity._area.get_opentherm_gateways = MagicMock(return_value=[])
        
        attrs = climate_entity.extra_state_attributes
        
        # Check basic attributes
        assert attrs["area_id"] == TEST_AREA_ID
        assert attrs["device_count"] == 0
        
        # Device type attributes should not be present when empty
        assert "thermostats" not in attrs
        assert "temperature_sensors" not in attrs
        assert "opentherm_gateways" not in attrs

    def test_available_true(self, climate_entity: AreaClimate, mock_coordinator):
        """Test available property when coordinator successful."""
        mock_coordinator.last_update_success = True
        
        assert climate_entity.available is True

    def test_available_false(self, climate_entity: AreaClimate, mock_coordinator):
        """Test available property when coordinator failed."""
        mock_coordinator.last_update_success = False
        
        assert climate_entity.available is False
