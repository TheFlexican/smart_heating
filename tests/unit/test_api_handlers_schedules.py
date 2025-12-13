"""Tests for schedule API handlers."""

import json
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from homeassistant.core import HomeAssistant
from smart_heating.api_handlers.schedules import (
    handle_add_schedule,
    handle_cancel_boost,
    handle_remove_schedule,
    handle_set_boost_mode,
    handle_set_preset_mode,
    handle_update_schedule,
)
from smart_heating.const import DOMAIN


@pytest.fixture
def mock_hass():
    """Create mock Home Assistant instance."""
    hass = MagicMock(spec=HomeAssistant)
    hass.data = {DOMAIN: {}}
    return hass


@pytest.fixture
def mock_area_manager():
    """Create mock area manager."""
    manager = MagicMock()

    # Mock area
    mock_area = MagicMock()
    mock_area.id = "living_room"
    mock_area.name = "Living Room"
    mock_area.preset_mode = "none"
    mock_area.target_temperature = 21.0
    mock_area.manual_override = False
    mock_area.get_effective_target_temperature.return_value = 21.0
    mock_area.boost_temp = 25.0

    manager.get_area.return_value = mock_area
    manager.areas = {"living_room": mock_area}
    manager.async_save = AsyncMock()

    return manager


@pytest.fixture
def mock_area_registry():
    """Create mock area registry."""
    registry = MagicMock()

    mock_ha_area = MagicMock()
    mock_ha_area.id = "living_room"
    mock_ha_area.name = "Living Room"

    registry.async_get_area.return_value = mock_ha_area

    return registry


class TestScheduleHandlers:
    """Test schedule API handlers."""

    @pytest.mark.asyncio
    async def test_handle_add_schedule_with_temperature(self, mock_hass, mock_area_manager):
        """Test adding schedule with temperature."""
        data = {
            "id": "sched_123",
            "time": "08:00",
            "temperature": 22.0,
            "days": ["monday", "tuesday"],
            "enabled": True,
        }

        with (
            patch(
                "smart_heating.api_handlers.schedules.validate_area_id", return_value=(True, None)
            ),
            patch(
                "smart_heating.api_handlers.schedules.validate_temperature",
                return_value=(True, None),
            ),
            patch("smart_heating.api_handlers.schedules.Schedule") as mock_schedule_class,
        ):
            mock_schedule = MagicMock()
            mock_schedule.to_dict.return_value = {"id": "sched_123", "time": "08:00"}
            mock_schedule_class.return_value = mock_schedule

            response = await handle_add_schedule(mock_hass, mock_area_manager, "living_room", data)

            assert response.status == 200
            body = json.loads(response.body.decode())
            assert body["success"]
            assert "schedule" in body

            mock_area_manager.get_area.return_value.add_schedule.assert_called_once()
            mock_area_manager.async_save.assert_called_once()

    @pytest.mark.asyncio
    async def test_handle_add_schedule_with_preset_mode(self, mock_hass, mock_area_manager):
        """Test adding schedule with preset mode."""
        data = {
            "start_time": "07:00",
            "end_time": "09:00",
            "preset_mode": "comfort",
            "days": ["weekday"],
        }

        with (
            patch(
                "smart_heating.api_handlers.schedules.validate_area_id", return_value=(True, None)
            ),
            patch("smart_heating.api_handlers.schedules.Schedule") as mock_schedule_class,
        ):
            mock_schedule = MagicMock()
            mock_schedule.to_dict.return_value = {"preset_mode": "comfort"}
            mock_schedule_class.return_value = mock_schedule

            response = await handle_add_schedule(mock_hass, mock_area_manager, "living_room", data)

            assert response.status == 200
            body = json.loads(response.body.decode())
            assert body["success"]

    @pytest.mark.asyncio
    async def test_handle_add_schedule_invalid_area_id(self, mock_hass, mock_area_manager):
        """Test adding schedule with invalid area ID."""
        data = {"temperature": 22.0, "time": "08:00"}

        with patch(
            "smart_heating.api_handlers.schedules.validate_area_id",
            return_value=(False, "Invalid area ID"),
        ):
            response = await handle_add_schedule(mock_hass, mock_area_manager, "", data)

            assert response.status == 400
            body = json.loads(response.body.decode())
            assert "error" in body

    @pytest.mark.asyncio
    async def test_handle_add_schedule_missing_temperature_and_preset(
        self, mock_hass, mock_area_manager
    ):
        """Test adding schedule without temperature or preset_mode."""
        data = {"time": "08:00", "days": ["monday"]}

        with patch(
            "smart_heating.api_handlers.schedules.validate_area_id", return_value=(True, None)
        ):
            response = await handle_add_schedule(mock_hass, mock_area_manager, "living_room", data)

            assert response.status == 400
            body = json.loads(response.body.decode())
            assert "error" in body

    @pytest.mark.asyncio
    async def test_handle_add_schedule_invalid_temperature(self, mock_hass, mock_area_manager):
        """Test adding schedule with invalid temperature."""
        data = {"time": "08:00", "temperature": 100}

        with (
            patch(
                "smart_heating.api_handlers.schedules.validate_area_id", return_value=(True, None)
            ),
            patch(
                "smart_heating.api_handlers.schedules.validate_temperature",
                return_value=(False, "Temperature out of range"),
            ),
        ):
            response = await handle_add_schedule(mock_hass, mock_area_manager, "living_room", data)

            assert response.status == 400
            body = json.loads(response.body.decode())
            assert "error" in body

    @pytest.mark.asyncio
    async def test_handle_add_schedule_creates_area(self, mock_hass, mock_area_registry):
        """Test adding schedule auto-creates area if needed."""
        area_manager = MagicMock()
        area_manager.get_area.return_value = None  # Area doesn't exist
        area_manager.areas = {}
        area_manager.async_save = AsyncMock()

        data = {"temperature": 22.0, "time": "08:00"}

        with (
            patch(
                "smart_heating.api_handlers.schedules.validate_area_id", return_value=(True, None)
            ),
            patch(
                "smart_heating.api_handlers.schedules.validate_temperature",
                return_value=(True, None),
            ),
            patch(
                "smart_heating.api_handlers.schedules.ar.async_get", return_value=mock_area_registry
            ),
            patch("smart_heating.api_handlers.schedules.Area") as mock_area_class,
            patch("smart_heating.api_handlers.schedules.Schedule") as mock_schedule_class,
        ):
            mock_new_area = MagicMock()
            mock_area_class.return_value = mock_new_area

            mock_schedule = MagicMock()
            mock_schedule.to_dict.return_value = {}
            mock_schedule_class.return_value = mock_schedule

            # After creating area, make it available
            def side_effect(area_id):
                if area_id in area_manager.areas:
                    return area_manager.areas[area_id]
                return None

            area_manager.get_area.side_effect = side_effect

            response = await handle_add_schedule(mock_hass, area_manager, "living_room", data)

            assert response.status == 200
            assert "living_room" in area_manager.areas

    @pytest.mark.asyncio
    async def test_handle_add_schedule_area_not_in_ha(self, mock_hass):
        """Test adding schedule when area doesn't exist in HA."""
        area_manager = MagicMock()
        area_manager.get_area.return_value = None

        registry = MagicMock()
        registry.async_get_area.return_value = None  # Not in HA

        data = {"temperature": 22.0, "time": "08:00"}

        with (
            patch(
                "smart_heating.api_handlers.schedules.validate_area_id", return_value=(True, None)
            ),
            patch(
                "smart_heating.api_handlers.schedules.validate_temperature",
                return_value=(True, None),
            ),
            patch("smart_heating.api_handlers.schedules.ar.async_get", return_value=registry),
        ):
            response = await handle_add_schedule(mock_hass, area_manager, "nonexistent", data)

            assert response.status == 404
            body = json.loads(response.body.decode())
            assert "error" in body

    @pytest.mark.asyncio
    async def test_handle_add_schedule_missing_time(self, mock_hass, mock_area_manager):
        """Test adding schedule without time field."""
        data = {"temperature": 22.0}  # Missing time

        with (
            patch(
                "smart_heating.api_handlers.schedules.validate_area_id", return_value=(True, None)
            ),
            patch(
                "smart_heating.api_handlers.schedules.validate_temperature",
                return_value=(True, None),
            ),
        ):
            response = await handle_add_schedule(mock_hass, mock_area_manager, "living_room", data)

            assert response.status == 400
            body = json.loads(response.body.decode())
            assert "error" in body

    @pytest.mark.asyncio
    async def test_handle_add_schedule_value_error(self, mock_hass, mock_area_manager):
        """Test adding schedule with ValueError."""
        data = {"temperature": 22.0, "time": "08:00"}

        with (
            patch(
                "smart_heating.api_handlers.schedules.validate_area_id", return_value=(True, None)
            ),
            patch(
                "smart_heating.api_handlers.schedules.validate_temperature",
                return_value=(True, None),
            ),
            patch(
                "smart_heating.api_handlers.schedules.Schedule",
                side_effect=ValueError("Invalid schedule"),
            ),
        ):
            response = await handle_add_schedule(mock_hass, mock_area_manager, "living_room", data)

            assert response.status == 400
            body = json.loads(response.body.decode())
            assert "error" in body

    @pytest.mark.asyncio
    async def test_handle_remove_schedule_success(self, mock_hass, mock_area_manager):
        """Test removing a schedule."""
        mock_executor = MagicMock()
        mock_hass.data[DOMAIN]["schedule_executor"] = mock_executor

        response = await handle_remove_schedule(
            mock_hass, mock_area_manager, "living_room", "sched_123"
        )

        assert response.status == 200
        body = json.loads(response.body.decode())
        assert body["success"]

        mock_area_manager.remove_schedule_from_area.assert_called_once_with(
            "living_room", "sched_123"
        )
        mock_area_manager.async_save.assert_called_once()
        mock_executor.clear_schedule_cache.assert_called_once_with("living_room")

    @pytest.mark.asyncio
    async def test_handle_remove_schedule_no_executor(self, mock_hass, mock_area_manager):
        """Test removing schedule when executor not available."""
        response = await handle_remove_schedule(
            mock_hass, mock_area_manager, "living_room", "sched_123"
        )

        assert response.status == 200
        body = json.loads(response.body.decode())
        assert body["success"]

    @pytest.mark.asyncio
    async def test_handle_remove_schedule_error(self, mock_hass, mock_area_manager):
        """Test removing schedule with error."""
        mock_area_manager.remove_schedule_from_area.side_effect = ValueError("Schedule not found")

        response = await handle_remove_schedule(
            mock_hass, mock_area_manager, "living_room", "nonexistent"
        )

        assert response.status == 404
        body = json.loads(response.body.decode())
        assert "error" in body

    @pytest.mark.asyncio
    async def test_handle_update_schedule_remove_single_day(self, mock_hass, mock_area_manager):
        """Test updating a schedule by removing a single day from its days list."""
        from smart_heating.models.schedule import Schedule

        # Create a real schedule in area with multiple days
        schedule = Schedule(
            "sched_123", "08:00", temperature=21.0, days=["Monday", "Tuesday", "Wednesday"]
        )
        mock_area_manager.get_area.return_value.schedules = {"sched_123": schedule}

        # Update to remove Monday
        response = await handle_update_schedule(
            mock_hass,
            mock_area_manager,
            "living_room",
            "sched_123",
            {"days": ["Tuesday", "Wednesday"]},
        )

        assert response.status == 200
        body = json.loads(response.body.decode())
        assert body["success"] is True
        assert body["schedule"]["days"] == ["Tuesday", "Wednesday"]

    @pytest.mark.asyncio
    async def test_handle_update_schedule_delete_if_empty_days(self, mock_hass, mock_area_manager):
        """If the updated days list is empty, treat as delete and remove schedule."""
        from smart_heating.models.schedule import Schedule

        schedule = Schedule(
            "sched_del", "08:00", temperature=21.0, days=["Monday"]
        )  # 1-day schedule
        mock_area_manager.get_area.return_value.schedules = {"sched_del": schedule}

        response = await handle_update_schedule(
            mock_hass, mock_area_manager, "living_room", "sched_del", {"days": []}
        )

        assert response.status == 200
        body = json.loads(response.body.decode())
        assert body["success"] is True
        assert body.get("deleted") is True

    @pytest.mark.asyncio
    async def test_handle_set_preset_mode_success(self, mock_hass, mock_area_manager):
        """Test setting preset mode."""
        mock_coordinator = MagicMock()
        mock_coordinator.data = {}
        mock_coordinator.async_request_refresh = AsyncMock()
        mock_hass.data[DOMAIN]["test_coordinator"] = mock_coordinator
        mock_climate = AsyncMock()
        mock_hass.data[DOMAIN]["climate_controller"] = mock_climate

        data = {"preset_mode": "eco"}
        response = await handle_set_preset_mode(mock_hass, mock_area_manager, "living_room", data)

        assert response.status == 200
        body = json.loads(response.body.decode())
        assert body["success"]
        assert body["preset_mode"] == "eco"

        mock_area_manager.get_area.return_value.set_preset_mode.assert_called_once_with("eco")
        mock_area_manager.async_save.assert_called_once()
        mock_climate.async_control_heating.assert_called_once()

    @pytest.mark.asyncio
    async def test_handle_set_preset_mode_clears_manual_override(
        self, mock_hass, mock_area_manager
    ):
        """Test setting preset mode clears manual override."""
        mock_area_manager.get_area.return_value.manual_override = True

        mock_coordinator = MagicMock()
        mock_coordinator.data = {}
        mock_coordinator.async_request_refresh = AsyncMock()
        mock_hass.data[DOMAIN]["test_coordinator"] = mock_coordinator
        mock_climate = AsyncMock()
        mock_hass.data[DOMAIN]["climate_controller"] = mock_climate

        data = {"preset_mode": "comfort"}
        response = await handle_set_preset_mode(mock_hass, mock_area_manager, "living_room", data)

        assert response.status == 200
        assert not mock_area_manager.get_area.return_value.manual_override

    @pytest.mark.asyncio
    async def test_handle_set_preset_mode_missing_mode(self, mock_hass, mock_area_manager):
        """Test setting preset mode without mode parameter."""
        data = {}
        response = await handle_set_preset_mode(mock_hass, mock_area_manager, "living_room", data)

        assert response.status == 400
        body = json.loads(response.body.decode())
        assert "error" in body

    @pytest.mark.asyncio
    async def test_handle_set_preset_mode_area_not_found(self, mock_hass, mock_area_manager):
        """Test setting preset mode for non-existent area."""
        mock_area_manager.get_area.return_value = None

        data = {"preset_mode": "eco"}
        response = await handle_set_preset_mode(mock_hass, mock_area_manager, "nonexistent", data)

        assert response.status == 400
        body = json.loads(response.body.decode())
        assert "error" in body

    @pytest.mark.asyncio
    async def test_handle_set_boost_mode_success(self, mock_hass, mock_area_manager):
        """Test setting boost mode."""
        mock_coordinator = MagicMock()
        mock_coordinator.data = {}
        mock_coordinator.async_request_refresh = AsyncMock()
        mock_hass.data[DOMAIN]["test_coordinator"] = mock_coordinator

        data = {"duration": 120, "temperature": 25.0}
        response = await handle_set_boost_mode(mock_hass, mock_area_manager, "living_room", data)

        assert response.status == 200
        body = json.loads(response.body.decode())
        assert body["success"]
        assert body["boost_active"]
        assert body["duration"] == 120

        mock_area_manager.get_area.return_value.set_boost_mode.assert_called_once_with(120, 25.0)
        mock_area_manager.async_save.assert_called_once()

    @pytest.mark.asyncio
    async def test_handle_set_boost_mode_default_duration(self, mock_hass, mock_area_manager):
        """Test setting boost mode with default duration."""
        mock_coordinator = MagicMock()
        mock_coordinator.data = {}
        mock_coordinator.async_request_refresh = AsyncMock()
        mock_hass.data[DOMAIN]["test_coordinator"] = mock_coordinator

        data = {}  # No duration specified
        response = await handle_set_boost_mode(mock_hass, mock_area_manager, "living_room", data)

        assert response.status == 200
        body = json.loads(response.body.decode())
        assert body["duration"] == 60  # Default

    @pytest.mark.asyncio
    async def test_handle_set_boost_mode_area_not_found(self, mock_hass, mock_area_manager):
        """Test setting boost mode for non-existent area."""
        mock_area_manager.get_area.return_value = None

        data = {"duration": 60}
        response = await handle_set_boost_mode(mock_hass, mock_area_manager, "nonexistent", data)

        assert response.status == 400
        body = json.loads(response.body.decode())
        assert "error" in body

    @pytest.mark.asyncio
    async def test_handle_cancel_boost_success(self, mock_hass, mock_area_manager):
        """Test canceling boost mode."""
        mock_coordinator = MagicMock()
        mock_coordinator.data = {}
        mock_coordinator.async_request_refresh = AsyncMock()
        mock_hass.data[DOMAIN]["test_coordinator"] = mock_coordinator

        response = await handle_cancel_boost(mock_hass, mock_area_manager, "living_room")

        assert response.status == 200
        body = json.loads(response.body.decode())
        assert body["success"]
        assert not body["boost_active"]

        mock_area_manager.get_area.return_value.cancel_boost_mode.assert_called_once()
        mock_area_manager.async_save.assert_called_once()

    @pytest.mark.asyncio
    async def test_handle_cancel_boost_area_not_found(self, mock_hass, mock_area_manager):
        """Test canceling boost for non-existent area."""
        mock_area_manager.get_area.return_value = None

        response = await handle_cancel_boost(mock_hass, mock_area_manager, "nonexistent")

        assert response.status == 400
        body = json.loads(response.body.decode())
        assert "error" in body
