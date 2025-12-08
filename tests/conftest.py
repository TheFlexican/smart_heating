"""Common fixtures for Smart Heating tests."""
from __future__ import annotations

from collections.abc import Generator
from typing import Any
from unittest.mock import AsyncMock, MagicMock, Mock, patch

import pytest

from homeassistant.const import CONF_NAME
from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator
from homeassistant.setup import async_setup_component

from pytest_homeassistant_custom_component.common import MockConfigEntry

from smart_heating.const import DOMAIN


pytest_plugins = "pytest_homeassistant_custom_component"


@pytest.fixture(autouse=True)
def auto_enable_custom_integrations(enable_custom_integrations):
    """Enable custom integrations defined in the test dir."""
    yield


@pytest.fixture
def mock_config_entry() -> MockConfigEntry:
    """Return a mock config entry."""
    return MockConfigEntry(
        domain=DOMAIN,
        data={CONF_NAME: "Smart Heating"},
        entry_id="test_entry_id",
        title="Smart Heating",
    )


@pytest.fixture
def mock_setup_entry() -> Generator[AsyncMock]:
    """Override async_setup_entry."""
    with patch(
        "smart_heating.async_setup_entry", return_value=True
    ) as mock_setup_entry:
        yield mock_setup_entry


@pytest.fixture
async def init_integration(
    hass: HomeAssistant, mock_config_entry: MockConfigEntry
) -> MockConfigEntry:
    """Set up the Smart Heating integration for testing."""
    mock_config_entry.add_to_hass(hass)
    
    # Initialize the domain data structure
    hass.data[DOMAIN] = {}
    
    await hass.config_entries.async_setup(mock_config_entry.entry_id)
    await hass.async_block_till_done()
    
    return mock_config_entry


@pytest.fixture
def mock_config_entry() -> MockConfigEntry:
    """Return the default mocked config entry."""
    return MockConfigEntry(
        domain=DOMAIN,
        title="Smart Heating",
        data={"name": "Smart Heating"},
        entry_id="test_entry_id",
        version=1,
    )


@pytest.fixture
async def init_integration(
    hass: MockHomeAssistant, mock_config_entry: MockConfigEntry
) -> MockConfigEntry:
    """Set up the Smart Heating integration for testing."""
    mock_config_entry.add_to_hass(hass)
    # Mock the setup
    return mock_config_entry


@pytest.fixture
def mock_area_manager() -> MagicMock:
    """Return a mocked AreaManager."""
    manager = MagicMock()
    manager.areas = {}
    manager.get_area = MagicMock(return_value=None)
    manager.create_area = AsyncMock(return_value=True)
    manager.update_area = AsyncMock(return_value=True)
    manager.delete_area = AsyncMock(return_value=True)
    manager.get_all_areas = MagicMock(return_value={})  # Return dict, not list
    manager.enable_area = MagicMock()
    manager.disable_area = MagicMock()
    manager.set_area_target_temperature = MagicMock()
    manager.async_save = AsyncMock()
    return manager


@pytest.fixture
def mock_coordinator(mock_area_manager) -> MagicMock:
    """Return a mocked DataUpdateCoordinator."""
    coordinator = MagicMock(spec=DataUpdateCoordinator)
    coordinator.hass = None
    coordinator.area_manager = mock_area_manager
    coordinator.data = {
        "areas": {},
        "devices": {},
        "global_settings": {
            "eco_temperature": 18.0,
            "comfort_temperature": 21.0,
            "away_temperature": 15.0,
            "home_temperature": 20.0,
            "sleep_temperature": 17.0,
            "activity_temperature": 22.0,
            "boost_temperature": 24.0,
        },
    }
    coordinator.async_request_refresh = AsyncMock()
    coordinator.async_update_listeners = MagicMock()
    return coordinator


@pytest.fixture
def mock_area_data() -> dict[str, Any]:
    """Return mock area data."""
    return {
        "area_id": "living_room",
        "area_name": "Living Room",
        "target_temperature": 21.0,
        "current_temperature": 20.0,
        "enabled": True,
        "preset_mode": "comfort",
        "hvac_mode": "heat",
        "devices": {},  # Dict, not list
        "window_sensors": [],
        "presence_sensors": [],
        "schedule": [],
        "boost_mode": {
            "enabled": False,
            "end_time": None,
            "duration": 60,
        },
        "manual_override": False,
        "vacation_mode": False,
    }


@pytest.fixture
def mock_climate_device() -> dict[str, Any]:
    """Return mock climate device state."""
    return {
        "entity_id": "climate.living_room_thermostat",
        "state": "heat",
        "attributes": {
            "friendly_name": "Living Room Thermostat",
            "temperature": 21.0,
            "current_temperature": 20.0,
            "hvac_action": "heating",
            "hvac_modes": ["heat", "cool", "auto", "off"],
            "preset_modes": ["eco", "comfort", "away", "home", "sleep", "activity", "boost"],
            "preset_mode": "comfort",
            "min_temp": 5.0,
            "max_temp": 35.0,
            "target_temp_step": 0.5,
        },
    }


@pytest.fixture
def mock_sensor_state() -> dict[str, Any]:
    """Return mock sensor state."""
    return {
        "entity_id": "binary_sensor.living_room_window",
        "state": "off",
        "attributes": {
            "friendly_name": "Living Room Window",
            "device_class": "window",
        },
    }


@pytest.fixture
def mock_schedule_entry() -> dict[str, Any]:
    """Return mock schedule entry."""
    return {
        "id": "schedule_1",
        "time": "07:00",
        "temperature": 21.0,
        "days": ["monday", "tuesday", "wednesday", "thursday", "friday"],
        "enabled": True,
    }


@pytest.fixture
def mock_learning_data() -> dict[str, Any]:
    """Return mock learning engine data."""
    return {
        "patterns": {
            "living_room": {
                "weekday_morning": {"target": 21.0, "time": "07:00"},
                "weekday_evening": {"target": 22.0, "time": "18:00"},
                "weekend_morning": {"target": 20.0, "time": "09:00"},
            }
        },
        "predictions": {},
        "statistics": {
            "learning_count": 10,
            "accuracy": 0.85,
        },
    }


@pytest.fixture
def mock_hass() -> MagicMock:
    """Return a mocked HomeAssistant instance."""
    return MockHomeAssistant()

