"""Tests for api_handlers/system module."""
from __future__ import annotations

from datetime import datetime
from unittest.mock import AsyncMock, MagicMock
import pytest
from aiohttp import web

from smart_heating.api_handlers.system import (
    handle_get_status,
    handle_get_entity_state,
    handle_call_service,
)


@pytest.fixture
def mock_area_manager():
    """Create mock area manager with areas."""
    manager = MagicMock()
    
    # Create mock areas
    area1 = MagicMock()
    area1.enabled = True
    area1.devices = {"device1": MagicMock(), "device2": MagicMock()}
    
    area2 = MagicMock()
    area2.enabled = False
    area2.devices = {"device3": MagicMock()}
    
    manager.get_all_areas.return_value = {
        "area1": area1,
        "area2": area2,
    }
    
    return manager


@pytest.fixture
def mock_hass():
    """Create mock Home Assistant instance."""
    hass = MagicMock()
    return hass


class TestSystemHandlers:
    """Test system API handlers."""

    @pytest.mark.asyncio
    async def test_handle_get_status(self, mock_area_manager):
        """Test getting system status."""
        response = await handle_get_status(mock_area_manager)
        
        assert response.status == 200
        # Parse response body
        import json
        body = json.loads(response.body.decode())
        
        assert body["area_count"] == 2
        assert body["active_areas"] == 1  # Only area1 is enabled
        assert body["total_devices"] == 3  # 2 in area1, 1 in area2

    @pytest.mark.asyncio
    async def test_handle_get_entity_state_success(self, mock_hass):
        """Test getting entity state successfully."""
        # Create mock state object
        mock_state = MagicMock()
        mock_state.state = "20.5"
        mock_state.attributes = {"unit_of_measurement": "°C", "friendly_name": "Temperature"}
        mock_state.last_changed = datetime(2024, 1, 1, 12, 0, 0)
        mock_state.last_updated = datetime(2024, 1, 1, 12, 5, 0)
        
        mock_hass.states.get.return_value = mock_state
        
        response = await handle_get_entity_state(mock_hass, "sensor.temperature")
        
        assert response.status == 200
        import json
        body = json.loads(response.body.decode())
        
        assert body["state"] == "20.5"
        assert body["attributes"]["unit_of_measurement"] == "°C"
        assert body["attributes"]["friendly_name"] == "Temperature"
        assert "last_changed" in body
        assert "last_updated" in body

    @pytest.mark.asyncio
    async def test_handle_get_entity_state_not_found(self, mock_hass):
        """Test getting entity state when entity not found."""
        mock_hass.states.get.return_value = None
        
        response = await handle_get_entity_state(mock_hass, "sensor.unknown")
        
        assert response.status == 404
        import json
        body = json.loads(response.body.decode())
        
        assert "error" in body
        assert "not found" in body["error"].lower()

    @pytest.mark.asyncio
    async def test_handle_call_service_success(self, mock_hass):
        """Test calling service successfully."""
        mock_hass.services.async_call = AsyncMock()
        
        data = {
            "service": "set_temperature",
            "area_id": "living_room",
            "temperature": 21.5,
        }
        
        response = await handle_call_service(mock_hass, data)
        
        assert response.status == 200
        import json
        body = json.loads(response.body.decode())
        
        assert body["success"] is True
        assert "successfully" in body["message"].lower()
        
        # Verify service was called correctly
        mock_hass.services.async_call.assert_called_once_with(
            "smart_heating",
            "set_temperature",
            {"area_id": "living_room", "temperature": 21.5},
            blocking=True,
        )

    @pytest.mark.asyncio
    async def test_handle_call_service_no_service_name(self, mock_hass):
        """Test calling service without service name."""
        data = {"area_id": "living_room"}
        
        response = await handle_call_service(mock_hass, data)
        
        assert response.status == 400
        import json
        body = json.loads(response.body.decode())
        
        assert "error" in body
        assert "required" in body["error"].lower()

    @pytest.mark.asyncio
    async def test_handle_call_service_error(self, mock_hass):
        """Test calling service when error occurs."""
        mock_hass.services.async_call = AsyncMock(side_effect=Exception("Service error"))
        
        data = {"service": "set_temperature"}
        
        response = await handle_call_service(mock_hass, data)
        
        assert response.status == 500
        import json
        body = json.loads(response.body.decode())
        
        assert "error" in body
        assert "Service error" in body["error"]
