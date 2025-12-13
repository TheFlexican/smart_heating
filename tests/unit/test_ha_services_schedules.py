"""Tests for ha_services/schedule_handlers module."""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock

import pytest
from homeassistant.core import ServiceCall
from smart_heating.const import (
    ATTR_AREA_ID,
    ATTR_DAYS,
    ATTR_SCHEDULE_ID,
    ATTR_TEMPERATURE,
    ATTR_TIME,
)
from smart_heating.ha_services.schedule_handlers import (
    async_handle_add_schedule,
    async_handle_copy_schedule,
    async_handle_disable_schedule,
    async_handle_enable_schedule,
    async_handle_remove_schedule,
    async_handle_set_night_boost,
)
from smart_heating.models import Schedule


@pytest.fixture
def mock_schedule():
    """Create mock schedule."""
    schedule = MagicMock(spec=Schedule)
    schedule.schedule_id = "schedule_1"
    schedule.start_time = "08:00"
    schedule.end_time = "22:00"
    schedule.temperature = 21.0
    schedule.enabled = True
    schedule.day = 0
    return schedule


@pytest.fixture
def mock_area(mock_schedule):
    """Create mock area."""
    area = MagicMock()
    area.schedules = {"schedule_1": mock_schedule}
    area.add_schedule = MagicMock()
    area.night_boost_enabled = False
    area.night_boost_offset = 0.5
    area.night_boost_start_time = "22:00"
    area.night_boost_end_time = "06:00"
    area.smart_night_boost_enabled = False
    area.smart_night_boost_target_time = "06:00"
    area.weather_entity_id = None
    return area


@pytest.fixture
def mock_area_manager(mock_area):
    """Create mock area manager."""
    manager = MagicMock()
    manager.get_area = MagicMock(return_value=mock_area)
    manager.add_schedule_to_area = MagicMock()
    manager.remove_schedule_from_area = MagicMock()
    manager.async_save = AsyncMock()
    return manager


@pytest.fixture
def mock_coordinator():
    """Create mock coordinator."""
    coordinator = MagicMock()
    coordinator.async_request_refresh = AsyncMock()
    return coordinator


class TestScheduleHandlers:
    """Test schedule service handlers."""

    @pytest.mark.asyncio
    async def test_async_handle_add_schedule_success(self, mock_area_manager, mock_coordinator):
        """Test adding schedule successfully."""
        call = MagicMock(spec=ServiceCall)
        call.data = {
            ATTR_AREA_ID: "living_room",
            ATTR_SCHEDULE_ID: "morning",
            ATTR_TIME: "08:00",
            ATTR_TEMPERATURE: 21.5,
            ATTR_DAYS: [0, 1],
        }

        await async_handle_add_schedule(call, mock_area_manager, mock_coordinator)

        # Verify schedule was added
        mock_area_manager.add_schedule_to_area.assert_called_once_with(
            "living_room", "morning", "08:00", 21.5, [0, 1]
        )
        # Verify data was saved
        mock_area_manager.async_save.assert_called_once()
        # Verify coordinator refresh
        mock_coordinator.async_request_refresh.assert_called_once()

    @pytest.mark.asyncio
    async def test_async_handle_add_schedule_no_days(self, mock_area_manager, mock_coordinator):
        """Test adding schedule without days parameter."""
        call = MagicMock(spec=ServiceCall)
        call.data = {
            ATTR_AREA_ID: "living_room",
            ATTR_SCHEDULE_ID: "morning",
            ATTR_TIME: "08:00",
            ATTR_TEMPERATURE: 21.5,
        }

        await async_handle_add_schedule(call, mock_area_manager, mock_coordinator)

        # Verify schedule was added with None for days
        mock_area_manager.add_schedule_to_area.assert_called_once_with(
            "living_room", "morning", "08:00", 21.5, None
        )

    @pytest.mark.asyncio
    async def test_async_handle_add_schedule_error(self, mock_area_manager, mock_coordinator):
        """Test adding schedule when add_schedule_to_area raises error."""
        call = MagicMock(spec=ServiceCall)
        call.data = {
            ATTR_AREA_ID: "living_room",
            ATTR_SCHEDULE_ID: "morning",
            ATTR_TIME: "08:00",
            ATTR_TEMPERATURE: 21.5,
        }

        # Make add_schedule_to_area raise ValueError
        mock_area_manager.add_schedule_to_area.side_effect = ValueError("Schedule exists")

        # Should not raise, just log error
        await async_handle_add_schedule(call, mock_area_manager, mock_coordinator)

        # Should not save or refresh on error
        mock_area_manager.async_save.assert_not_called()
        mock_coordinator.async_request_refresh.assert_not_called()

    @pytest.mark.asyncio
    async def test_async_handle_remove_schedule_success(self, mock_area_manager, mock_coordinator):
        """Test removing schedule successfully."""
        call = MagicMock(spec=ServiceCall)
        call.data = {
            ATTR_AREA_ID: "living_room",
            ATTR_SCHEDULE_ID: "morning",
        }

        await async_handle_remove_schedule(call, mock_area_manager, mock_coordinator)

        # Verify schedule was removed
        mock_area_manager.remove_schedule_from_area.assert_called_once_with(
            "living_room", "morning"
        )
        # Verify data was saved
        mock_area_manager.async_save.assert_called_once()
        # Verify coordinator refresh
        mock_coordinator.async_request_refresh.assert_called_once()

    @pytest.mark.asyncio
    async def test_async_handle_remove_schedule_error(self, mock_area_manager, mock_coordinator):
        """Test removing schedule when remove_schedule_from_area raises error."""
        call = MagicMock(spec=ServiceCall)
        call.data = {
            ATTR_AREA_ID: "living_room",
            ATTR_SCHEDULE_ID: "morning",
        }

        # Make remove_schedule_from_area raise ValueError
        mock_area_manager.remove_schedule_from_area.side_effect = ValueError("Schedule not found")

        # Should not raise, just log error
        await async_handle_remove_schedule(call, mock_area_manager, mock_coordinator)

        # Should not save or refresh on error
        mock_area_manager.async_save.assert_not_called()
        mock_coordinator.async_request_refresh.assert_not_called()

    @pytest.mark.asyncio
    async def test_async_handle_enable_schedule_success(
        self, mock_area_manager, mock_coordinator, mock_area, mock_schedule
    ):
        """Test enabling schedule successfully."""
        call = MagicMock(spec=ServiceCall)
        call.data = {
            ATTR_AREA_ID: "living_room",
            ATTR_SCHEDULE_ID: "schedule_1",
        }

        mock_schedule.enabled = False  # Start disabled

        await async_handle_enable_schedule(call, mock_area_manager, mock_coordinator)

        # Verify schedule was enabled
        assert mock_schedule.enabled is True
        # Verify data was saved
        mock_area_manager.async_save.assert_called_once()
        # Verify coordinator refresh
        mock_coordinator.async_request_refresh.assert_called_once()

    @pytest.mark.asyncio
    async def test_async_handle_enable_schedule_area_not_found(
        self, mock_area_manager, mock_coordinator
    ):
        """Test enabling schedule when area not found."""
        call = MagicMock(spec=ServiceCall)
        call.data = {
            ATTR_AREA_ID: "unknown_area",
            ATTR_SCHEDULE_ID: "schedule_1",
        }

        # Make get_area return None
        mock_area_manager.get_area.return_value = None

        # Should not raise, just log error
        await async_handle_enable_schedule(call, mock_area_manager, mock_coordinator)

        # Should not save or refresh on error
        mock_area_manager.async_save.assert_not_called()
        mock_coordinator.async_request_refresh.assert_not_called()

    @pytest.mark.asyncio
    async def test_async_handle_enable_schedule_not_found(
        self, mock_area_manager, mock_coordinator, mock_area
    ):
        """Test enabling schedule when schedule not found."""
        call = MagicMock(spec=ServiceCall)
        call.data = {
            ATTR_AREA_ID: "living_room",
            ATTR_SCHEDULE_ID: "unknown_schedule",
        }

        # Schedule not in area.schedules
        await async_handle_enable_schedule(call, mock_area_manager, mock_coordinator)

        # Should not save or refresh on error
        mock_area_manager.async_save.assert_not_called()
        mock_coordinator.async_request_refresh.assert_not_called()

    @pytest.mark.asyncio
    async def test_async_handle_disable_schedule_success(
        self, mock_area_manager, mock_coordinator, mock_area, mock_schedule
    ):
        """Test disabling schedule successfully."""
        call = MagicMock(spec=ServiceCall)
        call.data = {
            ATTR_AREA_ID: "living_room",
            ATTR_SCHEDULE_ID: "schedule_1",
        }

        mock_schedule.enabled = True  # Start enabled

        await async_handle_disable_schedule(call, mock_area_manager, mock_coordinator)

        # Verify schedule was disabled
        assert mock_schedule.enabled is False
        # Verify data was saved
        mock_area_manager.async_save.assert_called_once()
        # Verify coordinator refresh
        mock_coordinator.async_request_refresh.assert_called_once()

    @pytest.mark.asyncio
    async def test_async_handle_disable_schedule_not_found(
        self, mock_area_manager, mock_coordinator, mock_area
    ):
        """Test disabling schedule when schedule not found."""
        call = MagicMock(spec=ServiceCall)
        call.data = {
            ATTR_AREA_ID: "living_room",
            ATTR_SCHEDULE_ID: "unknown_schedule",
        }

        # Schedule not in area.schedules
        await async_handle_disable_schedule(call, mock_area_manager, mock_coordinator)

        # Should not save or refresh on error
        mock_area_manager.async_save.assert_not_called()
        mock_coordinator.async_request_refresh.assert_not_called()

    @pytest.mark.asyncio
    async def test_async_handle_set_night_boost_all_settings(
        self, mock_area_manager, mock_coordinator, mock_area
    ):
        """Test setting all night boost settings."""
        call = MagicMock(spec=ServiceCall)
        call.data = {
            ATTR_AREA_ID: "living_room",
            "night_boost_enabled": True,
            "night_boost_offset": 1.0,
            "night_boost_start_time": "23:00",
            "night_boost_end_time": "07:00",
            "smart_night_boost_enabled": True,
            "smart_night_boost_target_time": "07:00",
            "weather_entity_id": "weather.home",
        }

        await async_handle_set_night_boost(call, mock_area_manager, mock_coordinator)

        # Verify all settings were updated
        assert mock_area.night_boost_enabled is True
        assert mock_area.night_boost_offset == 1.0
        assert mock_area.night_boost_start_time == "23:00"
        assert mock_area.night_boost_end_time == "07:00"
        assert mock_area.smart_night_boost_enabled is True
        assert mock_area.smart_night_boost_target_time == "07:00"
        assert mock_area.weather_entity_id == "weather.home"
        # Verify data was saved
        mock_area_manager.async_save.assert_called_once()
        # Verify coordinator refresh
        mock_coordinator.async_request_refresh.assert_called_once()

    @pytest.mark.asyncio
    async def test_async_handle_set_night_boost_partial_settings(
        self, mock_area_manager, mock_coordinator, mock_area
    ):
        """Test setting only some night boost settings."""
        call = MagicMock(spec=ServiceCall)
        call.data = {
            ATTR_AREA_ID: "living_room",
            "night_boost_enabled": True,
            "night_boost_offset": 1.5,
        }

        original_start = mock_area.night_boost_start_time

        await async_handle_set_night_boost(call, mock_area_manager, mock_coordinator)

        # Verify only specified settings were updated
        assert mock_area.night_boost_enabled is True
        assert mock_area.night_boost_offset == 1.5
        # Verify unspecified settings were not changed
        assert mock_area.night_boost_start_time == original_start

    @pytest.mark.asyncio
    async def test_async_handle_set_night_boost_area_not_found(
        self, mock_area_manager, mock_coordinator
    ):
        """Test setting night boost when area not found."""
        call = MagicMock(spec=ServiceCall)
        call.data = {
            ATTR_AREA_ID: "unknown_area",
            "night_boost_enabled": True,
        }

        # Make get_area return None
        mock_area_manager.get_area.return_value = None

        # Should not raise, just log error
        await async_handle_set_night_boost(call, mock_area_manager, mock_coordinator)

        # Should not save or refresh on error
        mock_area_manager.async_save.assert_not_called()
        mock_coordinator.async_request_refresh.assert_not_called()

    @pytest.mark.asyncio
    async def test_async_handle_copy_schedule_success(
        self, mock_area_manager, mock_coordinator, mock_schedule
    ):
        """Test copying schedule successfully."""
        source_area = MagicMock()
        source_area.schedules = {"schedule_1": mock_schedule}
        target_area = MagicMock()
        target_area.add_schedule = MagicMock()

        # Mock get_area to return different areas
        def get_area(area_id):
            if area_id == "source_area":
                return source_area
            elif area_id == "target_area":
                return target_area
            return None

        mock_area_manager.get_area.side_effect = get_area

        call = MagicMock(spec=ServiceCall)
        call.data = {
            "source_area_id": "source_area",
            "source_schedule_id": "schedule_1",
            "target_area_id": "target_area",
        }

        await async_handle_copy_schedule(call, mock_area_manager, mock_coordinator)

        # Verify schedule was added to target area
        target_area.add_schedule.assert_called_once()
        # Verify data was saved
        mock_area_manager.async_save.assert_called_once()
        # Verify coordinator refresh
        mock_coordinator.async_request_refresh.assert_called_once()

    @pytest.mark.asyncio
    async def test_async_handle_copy_schedule_with_target_days(
        self, mock_area_manager, mock_coordinator, mock_schedule
    ):
        """Test copying schedule with target days."""
        source_area = MagicMock()
        source_area.schedules = {"schedule_1": mock_schedule}
        target_area = MagicMock()
        target_area.add_schedule = MagicMock()

        def get_area(area_id):
            if area_id == "source_area":
                return source_area
            elif area_id == "target_area":
                return target_area
            return None

        mock_area_manager.get_area.side_effect = get_area

        call = MagicMock(spec=ServiceCall)
        call.data = {
            "source_area_id": "source_area",
            "source_schedule_id": "schedule_1",
            "target_area_id": "target_area",
            "target_days": [0, 1, 2],
        }

        await async_handle_copy_schedule(call, mock_area_manager, mock_coordinator)

        # Verify schedule was added 3 times (one for each day)
        assert target_area.add_schedule.call_count == 3

    @pytest.mark.asyncio
    async def test_async_handle_copy_schedule_source_area_not_found(
        self, mock_area_manager, mock_coordinator
    ):
        """Test copying schedule when source area not found."""
        mock_area_manager.get_area.return_value = None

        call = MagicMock(spec=ServiceCall)
        call.data = {
            "source_area_id": "unknown_area",
            "source_schedule_id": "schedule_1",
            "target_area_id": "target_area",
        }

        await async_handle_copy_schedule(call, mock_area_manager, mock_coordinator)

        # Should not save or refresh on error
        mock_area_manager.async_save.assert_not_called()
        mock_coordinator.async_request_refresh.assert_not_called()

    @pytest.mark.asyncio
    async def test_async_handle_copy_schedule_target_area_not_found(
        self, mock_area_manager, mock_coordinator, mock_schedule
    ):
        """Test copying schedule when target area not found."""
        source_area = MagicMock()
        source_area.schedules = {"schedule_1": mock_schedule}

        def get_area(area_id):
            if area_id == "source_area":
                return source_area
            return None

        mock_area_manager.get_area.side_effect = get_area

        call = MagicMock(spec=ServiceCall)
        call.data = {
            "source_area_id": "source_area",
            "source_schedule_id": "schedule_1",
            "target_area_id": "unknown_area",
        }

        await async_handle_copy_schedule(call, mock_area_manager, mock_coordinator)

        # Should not save or refresh on error
        mock_area_manager.async_save.assert_not_called()
        mock_coordinator.async_request_refresh.assert_not_called()

    @pytest.mark.asyncio
    async def test_async_handle_copy_schedule_schedule_not_found(
        self, mock_area_manager, mock_coordinator
    ):
        """Test copying schedule when source schedule not found."""
        source_area = MagicMock()
        source_area.schedules = {}  # No schedules
        target_area = MagicMock()

        def get_area(area_id):
            if area_id == "source_area":
                return source_area
            elif area_id == "target_area":
                return target_area
            return None

        mock_area_manager.get_area.side_effect = get_area

        call = MagicMock(spec=ServiceCall)
        call.data = {
            "source_area_id": "source_area",
            "source_schedule_id": "unknown_schedule",
            "target_area_id": "target_area",
        }

        await async_handle_copy_schedule(call, mock_area_manager, mock_coordinator)

        # Should not save or refresh on error
        mock_area_manager.async_save.assert_not_called()
        mock_coordinator.async_request_refresh.assert_not_called()
