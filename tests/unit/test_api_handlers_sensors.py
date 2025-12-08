"""Tests for sensor API handlers."""

import json
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from aiohttp import web

from smart_heating.api_handlers.sensors import (
    handle_add_presence_sensor,
    handle_add_window_sensor,
    handle_get_binary_sensor_entities,
    handle_remove_presence_sensor,
    handle_remove_window_sensor,
)


@pytest.fixture
def mock_hass():
    """Create a mock Home Assistant instance."""
    hass = MagicMock()
    hass.data = {
        "smart_heating": {
            "entry_id_123": MagicMock(async_request_refresh=AsyncMock()),
            "history": MagicMock(),
            "climate_controller": MagicMock(),
            "schedule_executor": MagicMock(),
        }
    }
    return hass


@pytest.fixture
def mock_area_manager():
    """Create a mock area manager."""
    manager = MagicMock()
    manager.async_save = AsyncMock()
    return manager


@pytest.fixture
def mock_area():
    """Create a mock area."""
    area = MagicMock()
    area.area_id = "living_room"
    area.add_window_sensor = MagicMock()
    area.remove_window_sensor = MagicMock()
    area.add_presence_sensor = MagicMock()
    area.remove_presence_sensor = MagicMock()
    return area


class TestAddWindowSensor:
    """Tests for handle_add_window_sensor."""

    @pytest.mark.asyncio
    async def test_add_window_sensor_success(self, mock_hass, mock_area_manager, mock_area):
        """Test successfully adding a window sensor."""
        mock_area_manager.get_area.return_value = mock_area
        
        data = {
            "entity_id": "binary_sensor.living_room_window",
            "action_when_open": "turn_off",
            "temp_drop": 2.0,
        }
        
        response = await handle_add_window_sensor(mock_hass, mock_area_manager, "living_room", data)
        
        assert response.status == 200
        body = json.loads(response.body.decode())
        assert body["success"] is True
        assert body["entity_id"] == "binary_sensor.living_room_window"
        
        mock_area.add_window_sensor.assert_called_once_with(
            "binary_sensor.living_room_window",
            "turn_off",
            2.0
        )
        mock_area_manager.async_save.assert_called_once()
        mock_hass.data["smart_heating"]["entry_id_123"].async_request_refresh.assert_called_once()

    @pytest.mark.asyncio
    async def test_add_window_sensor_default_action(self, mock_hass, mock_area_manager, mock_area):
        """Test adding window sensor with default action."""
        mock_area_manager.get_area.return_value = mock_area
        
        data = {"entity_id": "binary_sensor.bedroom_window"}
        
        response = await handle_add_window_sensor(mock_hass, mock_area_manager, "bedroom", data)
        
        assert response.status == 200
        body = json.loads(response.body.decode())
        assert body["success"] is True
        
        # Should use default "reduce_temperature" action
        mock_area.add_window_sensor.assert_called_once_with(
            "binary_sensor.bedroom_window",
            "reduce_temperature",
            None
        )

    @pytest.mark.asyncio
    async def test_add_window_sensor_missing_entity_id(self, mock_hass, mock_area_manager):
        """Test error when entity_id is missing."""
        data = {"action_when_open": "turn_off"}
        
        response = await handle_add_window_sensor(mock_hass, mock_area_manager, "living_room", data)
        
        assert response.status == 400
        body = json.loads(response.body.decode())
        assert "entity_id required" in body["error"]

    @pytest.mark.asyncio
    async def test_add_window_sensor_area_not_found(self, mock_hass, mock_area_manager):
        """Test error when area is not found."""
        mock_area_manager.get_area.return_value = None
        
        data = {"entity_id": "binary_sensor.window"}
        
        response = await handle_add_window_sensor(mock_hass, mock_area_manager, "nonexistent", data)
        
        assert response.status == 400
        body = json.loads(response.body.decode())
        assert "Area nonexistent not found" in body["error"]

    @pytest.mark.asyncio
    async def test_add_window_sensor_value_error(self, mock_hass, mock_area_manager, mock_area):
        """Test handling ValueError from area."""
        mock_area_manager.get_area.return_value = mock_area
        mock_area.add_window_sensor.side_effect = ValueError("Invalid sensor")
        
        data = {"entity_id": "binary_sensor.invalid"}
        
        response = await handle_add_window_sensor(mock_hass, mock_area_manager, "living_room", data)
        
        assert response.status == 400
        body = json.loads(response.body.decode())
        assert "Invalid sensor" in body["error"]


class TestRemoveWindowSensor:
    """Tests for handle_remove_window_sensor."""

    @pytest.mark.asyncio
    async def test_remove_window_sensor_success(self, mock_hass, mock_area_manager, mock_area):
        """Test successfully removing a window sensor."""
        mock_area_manager.get_area.return_value = mock_area
        
        response = await handle_remove_window_sensor(
            mock_hass, 
            mock_area_manager, 
            "living_room", 
            "binary_sensor.living_room_window"
        )
        
        assert response.status == 200
        body = json.loads(response.body.decode())
        assert body["success"] is True
        
        mock_area.remove_window_sensor.assert_called_once_with("binary_sensor.living_room_window")
        mock_area_manager.async_save.assert_called_once()
        mock_hass.data["smart_heating"]["entry_id_123"].async_request_refresh.assert_called_once()

    @pytest.mark.asyncio
    async def test_remove_window_sensor_area_not_found(self, mock_hass, mock_area_manager):
        """Test error when area is not found."""
        mock_area_manager.get_area.return_value = None
        
        response = await handle_remove_window_sensor(
            mock_hass,
            mock_area_manager,
            "nonexistent",
            "binary_sensor.window"
        )
        
        assert response.status == 404
        body = json.loads(response.body.decode())
        assert "Area nonexistent not found" in body["error"]

    @pytest.mark.asyncio
    async def test_remove_window_sensor_value_error(self, mock_hass, mock_area_manager, mock_area):
        """Test handling ValueError from area."""
        mock_area_manager.get_area.return_value = mock_area
        mock_area.remove_window_sensor.side_effect = ValueError("Sensor not found")
        
        response = await handle_remove_window_sensor(
            mock_hass,
            mock_area_manager,
            "living_room",
            "binary_sensor.nonexistent"
        )
        
        assert response.status == 404
        body = json.loads(response.body.decode())
        assert "Sensor not found" in body["error"]


class TestAddPresenceSensor:
    """Tests for handle_add_presence_sensor."""

    @pytest.mark.asyncio
    async def test_add_presence_sensor_success(self, mock_hass, mock_area_manager, mock_area):
        """Test successfully adding a presence sensor."""
        mock_area_manager.get_area.return_value = mock_area
        
        data = {"entity_id": "person.john"}
        
        response = await handle_add_presence_sensor(mock_hass, mock_area_manager, "living_room", data)
        
        assert response.status == 200
        body = json.loads(response.body.decode())
        assert body["success"] is True
        assert body["entity_id"] == "person.john"
        
        mock_area.add_presence_sensor.assert_called_once_with("person.john")
        mock_area_manager.async_save.assert_called_once()
        mock_hass.data["smart_heating"]["entry_id_123"].async_request_refresh.assert_called_once()

    @pytest.mark.asyncio
    async def test_add_presence_sensor_missing_entity_id(self, mock_hass, mock_area_manager):
        """Test error when entity_id is missing."""
        data = {}
        
        response = await handle_add_presence_sensor(mock_hass, mock_area_manager, "living_room", data)
        
        assert response.status == 400
        body = json.loads(response.body.decode())
        assert "entity_id required" in body["error"]

    @pytest.mark.asyncio
    async def test_add_presence_sensor_area_not_found(self, mock_hass, mock_area_manager):
        """Test error when area is not found."""
        mock_area_manager.get_area.return_value = None
        
        data = {"entity_id": "person.jane"}
        
        response = await handle_add_presence_sensor(mock_hass, mock_area_manager, "nonexistent", data)
        
        assert response.status == 400
        body = json.loads(response.body.decode())
        assert "Area nonexistent not found" in body["error"]

    @pytest.mark.asyncio
    async def test_add_presence_sensor_value_error(self, mock_hass, mock_area_manager, mock_area):
        """Test handling ValueError from area."""
        mock_area_manager.get_area.return_value = mock_area
        mock_area.add_presence_sensor.side_effect = ValueError("Invalid presence sensor")
        
        data = {"entity_id": "person.invalid"}
        
        response = await handle_add_presence_sensor(mock_hass, mock_area_manager, "living_room", data)
        
        assert response.status == 400
        body = json.loads(response.body.decode())
        assert "Invalid presence sensor" in body["error"]


class TestRemovePresenceSensor:
    """Tests for handle_remove_presence_sensor."""

    @pytest.mark.asyncio
    async def test_remove_presence_sensor_success(self, mock_hass, mock_area_manager, mock_area):
        """Test successfully removing a presence sensor."""
        mock_area_manager.get_area.return_value = mock_area
        
        response = await handle_remove_presence_sensor(
            mock_hass,
            mock_area_manager,
            "living_room",
            "person.john"
        )
        
        assert response.status == 200
        body = json.loads(response.body.decode())
        assert body["success"] is True
        
        mock_area.remove_presence_sensor.assert_called_once_with("person.john")
        mock_area_manager.async_save.assert_called_once()
        mock_hass.data["smart_heating"]["entry_id_123"].async_request_refresh.assert_called_once()

    @pytest.mark.asyncio
    async def test_remove_presence_sensor_area_not_found(self, mock_hass, mock_area_manager):
        """Test error when area is not found."""
        mock_area_manager.get_area.return_value = None
        
        response = await handle_remove_presence_sensor(
            mock_hass,
            mock_area_manager,
            "nonexistent",
            "person.john"
        )
        
        assert response.status == 404
        body = json.loads(response.body.decode())
        assert "Area nonexistent not found" in body["error"]

    @pytest.mark.asyncio
    async def test_remove_presence_sensor_value_error(self, mock_hass, mock_area_manager, mock_area):
        """Test handling ValueError from area."""
        mock_area_manager.get_area.return_value = mock_area
        mock_area.remove_presence_sensor.side_effect = ValueError("Sensor not found")
        
        response = await handle_remove_presence_sensor(
            mock_hass,
            mock_area_manager,
            "living_room",
            "person.nonexistent"
        )
        
        assert response.status == 404
        body = json.loads(response.body.decode())
        assert "Sensor not found" in body["error"]


class TestGetBinarySensorEntities:
    """Tests for handle_get_binary_sensor_entities."""

    @pytest.mark.asyncio
    async def test_get_binary_sensor_entities_success(self, mock_hass):
        """Test successfully getting binary sensor entities."""
        # Mock binary sensor
        binary_state = MagicMock()
        binary_state.state = "on"
        binary_state.attributes = {
            "friendly_name": "Living Room Window",
            "device_class": "window",
        }
        
        # Mock person
        person_state = MagicMock()
        person_state.state = "home"
        person_state.attributes = {"friendly_name": "John"}
        
        # Mock device tracker
        tracker_state = MagicMock()
        tracker_state.state = "home"
        tracker_state.attributes = {"friendly_name": "John's Phone"}
        
        mock_hass.states.async_entity_ids = MagicMock(side_effect=lambda domain: {
            "binary_sensor": ["binary_sensor.living_room_window"],
            "person": ["person.john"],
            "device_tracker": ["device_tracker.john_phone"],
        }.get(domain, []))
        
        mock_hass.states.get = MagicMock(side_effect=lambda entity_id: {
            "binary_sensor.living_room_window": binary_state,
            "person.john": person_state,
            "device_tracker.john_phone": tracker_state,
        }.get(entity_id))
        
        response = await handle_get_binary_sensor_entities(mock_hass)
        
        assert response.status == 200
        body = json.loads(response.body.decode())
        assert "entities" in body
        assert len(body["entities"]) == 3
        
        # Check binary sensor
        binary_entity = next(e for e in body["entities"] if e["entity_id"] == "binary_sensor.living_room_window")
        assert binary_entity["state"] == "on"
        assert binary_entity["attributes"]["friendly_name"] == "Living Room Window"
        assert binary_entity["attributes"]["device_class"] == "window"
        
        # Check person
        person_entity = next(e for e in body["entities"] if e["entity_id"] == "person.john")
        assert person_entity["state"] == "home"
        assert person_entity["attributes"]["friendly_name"] == "John"
        assert person_entity["attributes"]["device_class"] == "presence"
        
        # Check device tracker
        tracker_entity = next(e for e in body["entities"] if e["entity_id"] == "device_tracker.john_phone")
        assert tracker_entity["state"] == "home"
        assert tracker_entity["attributes"]["friendly_name"] == "John's Phone"
        assert tracker_entity["attributes"]["device_class"] == "presence"

    @pytest.mark.asyncio
    async def test_get_binary_sensor_entities_empty(self, mock_hass):
        """Test getting entities when none exist."""
        mock_hass.states.async_entity_ids = MagicMock(return_value=[])
        
        response = await handle_get_binary_sensor_entities(mock_hass)
        
        assert response.status == 200
        body = json.loads(response.body.decode())
        assert "entities" in body
        assert len(body["entities"]) == 0

    @pytest.mark.asyncio
    async def test_get_binary_sensor_entities_none_state(self, mock_hass):
        """Test handling when entity state is None."""
        mock_hass.states.async_entity_ids = MagicMock(side_effect=lambda domain: {
            "binary_sensor": ["binary_sensor.test"],
        }.get(domain, []))
        
        mock_hass.states.get = MagicMock(return_value=None)
        
        response = await handle_get_binary_sensor_entities(mock_hass)
        
        assert response.status == 200
        body = json.loads(response.body.decode())
        assert "entities" in body
        assert len(body["entities"]) == 0

    @pytest.mark.asyncio
    async def test_get_binary_sensor_entities_missing_attributes(self, mock_hass):
        """Test handling entities with missing attributes."""
        state = MagicMock()
        state.state = "on"
        state.attributes = {}  # No friendly_name or device_class
        
        mock_hass.states.async_entity_ids = MagicMock(side_effect=lambda domain: {
            "binary_sensor": ["binary_sensor.minimal"],
        }.get(domain, []))
        
        mock_hass.states.get = MagicMock(return_value=state)
        
        response = await handle_get_binary_sensor_entities(mock_hass)
        
        assert response.status == 200
        body = json.loads(response.body.decode())
        assert len(body["entities"]) == 1
        entity = body["entities"][0]
        assert entity["entity_id"] == "binary_sensor.minimal"
        assert entity["attributes"]["friendly_name"] == "binary_sensor.minimal"  # Falls back to entity_id
        assert entity["attributes"]["device_class"] is None

    @pytest.mark.asyncio
    async def test_get_binary_sensor_entities_multiple_types(self, mock_hass):
        """Test getting entities with multiple device classes."""
        window_state = MagicMock()
        window_state.state = "off"
        window_state.attributes = {
            "friendly_name": "Window Sensor",
            "device_class": "window",
        }
        
        motion_state = MagicMock()
        motion_state.state = "on"
        motion_state.attributes = {
            "friendly_name": "Motion Sensor",
            "device_class": "motion",
        }
        
        door_state = MagicMock()
        door_state.state = "off"
        door_state.attributes = {
            "friendly_name": "Door Sensor",
            "device_class": "door",
        }
        
        mock_hass.states.async_entity_ids = MagicMock(side_effect=lambda domain: {
            "binary_sensor": ["binary_sensor.window", "binary_sensor.motion", "binary_sensor.door"],
        }.get(domain, []))
        
        mock_hass.states.get = MagicMock(side_effect=lambda entity_id: {
            "binary_sensor.window": window_state,
            "binary_sensor.motion": motion_state,
            "binary_sensor.door": door_state,
        }.get(entity_id))
        
        response = await handle_get_binary_sensor_entities(mock_hass)
        
        assert response.status == 200
        body = json.loads(response.body.decode())
        assert len(body["entities"]) == 3
        
        # Verify all device classes are preserved
        device_classes = [e["attributes"]["device_class"] for e in body["entities"]]
        assert "window" in device_classes
        assert "motion" in device_classes
        assert "door" in device_classes
