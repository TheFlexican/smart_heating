"""Common fixtures for Smart Heating tests."""

from __future__ import annotations

from collections.abc import Generator
from typing import Any
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from homeassistant.const import CONF_NAME
from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator
from pytest_homeassistant_custom_component.common import MockConfigEntry
from smart_heating.const import DOMAIN


@pytest.fixture(autouse=True)
def disable_time_interval(monkeypatch):
    """Patch async_track_time_interval used by the integration to avoid starting recurring tasks in tests.

    Several integration components schedule periodic tasks using async_track_time_interval.
    For unit tests we replace it with a no-op that returns a dummy unsub function so no real tasks run.
    """
    try:
        import smart_heating as init_mod
        import smart_heating.advanced_metrics_collector as amc_mod
        import smart_heating.history as history_mod
        import smart_heating.scheduler as scheduler_mod

        def dummy_unsub():
            return None

        monkeypatch.setattr(
            scheduler_mod, "async_track_time_interval", lambda hass, func, interval: dummy_unsub
        )
        monkeypatch.setattr(
            amc_mod, "async_track_time_interval", lambda hass, func, interval: dummy_unsub
        )
        monkeypatch.setattr(
            init_mod, "async_track_time_interval", lambda hass, func, interval: dummy_unsub
        )
        monkeypatch.setattr(
            history_mod, "async_track_time_interval", lambda hass, func, interval: dummy_unsub
        )
    except Exception:
        # If modules are not importable in certain test contexts, ignore
        pass
    yield


@pytest.fixture(autouse=True)
async def cleanup_background_tasks(hass: HomeAssistant):
    """Autouse fixture cleaning up background tasks started by integration setup.

    Some tests call integration setup or create components that schedule recurring
    tasks (via async_track_time_interval or hass.async_create_task). These tasks
    may survive a test and keep the event loop alive, causing hangs. Ensure
    known components are stopped after each test.
    """
    yield
    # Cancel any test-scoped tasks stored by fixtures or autouse monkeypatch
    domain_data = hass.data.get(DOMAIN, {}) if hass and hasattr(hass, "data") else {}
    try:
        tasks = domain_data.get("test_tasks", [])
        for t in tasks:
            try:
                if not t.done():
                    t.cancel()
            except Exception:
                pass

        # Actually await the cancelled tasks to consume CancelledError
        import asyncio

        if tasks:
            await asyncio.gather(*tasks, return_exceptions=True)

        domain_data["test_tasks"] = []
        await hass.async_block_till_done()
    except Exception:
        pass


def pytest_sessionfinish(session, exitstatus):
    """Pytest hook debugging lingering asyncio tasks at session end."""
    try:
        import asyncio

        tasks = asyncio.all_tasks()
        if tasks:
            print(f"SESSION DEBUG: total asyncio tasks: {len(tasks)}")
            for t in tasks:
                print(f"SESSION TASK: {t!r}, done={t.done()}, cancelled={t.cancelled()}")
                try:
                    stack = t.get_stack()
                    if stack:
                        print("  STACK:")
                        for f in stack:
                            print("    ", f)
                except Exception:
                    pass
    except Exception:
        pass


pytest_plugins = "pytest_homeassistant_custom_component"


@pytest.fixture(autouse=True)
def auto_enable_custom_integrations(enable_custom_integrations):
    """Enable custom integrations defined in the test dir."""
    yield


@pytest.fixture(autouse=True)
def capture_hass_async_create_task(monkeypatch, hass: HomeAssistant):
    """Monkeypatch hass.async_create_task to record tasks for cleanup.

    This keeps a reference to created tasks in hass.data[DOMAIN]["test_tasks"]
    so the test cleanup fixture can safely cancel them.
    """
    orig = hass.async_create_task

    def _wrap_async_create_task(coro):
        try:
            task = orig(coro)
            hass.data.setdefault(DOMAIN, {}).setdefault("test_tasks", []).append(task)
            try:

                def _remove_done(fut):
                    try:
                        hass.data[DOMAIN]["test_tasks"].remove(fut)
                    except Exception:
                        pass

                try:
                    task.add_done_callback(_remove_done)
                except Exception:
                    pass
            except Exception:
                pass
            return task
        except Exception:
            # If original fails (some tests patch hass), fallback to returning a dummy object
            return None

    monkeypatch.setattr(hass, "async_create_task", _wrap_async_create_task)
    yield


@pytest.fixture(autouse=True)
def capture_asyncio_create_task(monkeypatch, hass: HomeAssistant):
    """Monkeypatch asyncio.create_task to record tasks for cleanup.

    Coordinator uses asyncio.create_task directly; capture those tasks as well.
    """
    import asyncio as _asyncio

    orig = _asyncio.create_task

    def _wrap_create_task(coro):
        try:
            task = orig(coro)
            hass.data.setdefault(DOMAIN, {}).setdefault("test_tasks", []).append(task)

            def _remove_done(fut):
                try:
                    hass.data[DOMAIN]["test_tasks"].remove(fut)
                except Exception:
                    pass

            try:
                task.add_done_callback(_remove_done)
            except Exception:
                pass
            return task
        except Exception:
            return orig(coro)

    monkeypatch.setattr(_asyncio, "create_task", _wrap_create_task)
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
    with patch("smart_heating.async_setup_entry", return_value=True) as mock_setup_entry:
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
        "days": [0, 1, 2, 3, 4],
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
    hass = MagicMock(spec=HomeAssistant)
    # Provide a minimal .data dict used across tests and event bus default
    default_coordinator = MagicMock(spec=DataUpdateCoordinator)
    default_coordinator.data = {"areas": {}}
    default_coordinator.async_request_refresh = AsyncMock()
    hass.data = {DOMAIN: {"test_entry_id": default_coordinator}}
    hass.bus = MagicMock()
    hass.config = MagicMock()
    hass.config.components = set()
    return hass
