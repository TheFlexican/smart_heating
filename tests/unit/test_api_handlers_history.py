"""Tests for api_handlers/history module."""
from __future__ import annotations

from datetime import datetime
from unittest.mock import AsyncMock, MagicMock
import pytest
from aiohttp import web

from smart_heating.api_handlers.history import (
    handle_get_history,
    handle_get_learning_stats,
    handle_get_history_config,
    handle_set_history_config,
)
from smart_heating.const import DOMAIN


@pytest.fixture
def mock_history_tracker():
    """Create mock history tracker."""
    tracker = MagicMock()
    tracker.get_history = MagicMock(return_value=[
        {
            "timestamp": "2024-01-01T12:00:00",
            "current_temperature": 20.0,
            "target_temperature": 21.0,
            "state": "heating",
        }
    ])
    tracker.get_retention_days = MagicMock(return_value=30)
    tracker.set_retention_days = MagicMock()
    tracker.async_save = AsyncMock()
    tracker._async_cleanup_old_entries = AsyncMock()
    return tracker


@pytest.fixture
def mock_learning_engine():
    """Create mock learning engine."""
    engine = MagicMock()
    engine.async_get_learning_stats = AsyncMock(return_value={
        "total_patterns": 10,
        "confidence": 0.85,
    })
    return engine


@pytest.fixture
def mock_hass(mock_history_tracker, mock_learning_engine):
    """Create mock Home Assistant instance."""
    hass = MagicMock()
    hass.data = {
        DOMAIN: {
            "history": mock_history_tracker,
            "learning_engine": mock_learning_engine,
        }
    }
    return hass


@pytest.fixture
def mock_request():
    """Create mock request."""
    request = MagicMock()
    request.query = {}
    return request


class TestHistoryHandlers:
    """Test history API handlers."""

    @pytest.mark.asyncio
    async def test_handle_get_history_default(
        self, mock_hass, mock_history_tracker, mock_request
    ):
        """Test getting history with default parameters (24 hours)."""
        response = await handle_get_history(mock_hass, "living_room", mock_request)
        
        assert response.status == 200
        import json
        body = json.loads(response.body.decode())
        
        assert body["area_id"] == "living_room"
        assert body["hours"] == 24
        assert body["count"] == 1
        assert len(body["entries"]) == 1
        
        # Verify history tracker was called with 24 hours
        mock_history_tracker.get_history.assert_called_once_with("living_room", hours=24)

    @pytest.mark.asyncio
    async def test_handle_get_history_custom_hours(
        self, mock_hass, mock_history_tracker, mock_request
    ):
        """Test getting history with custom hours."""
        mock_request.query = {"hours": "48"}
        
        response = await handle_get_history(mock_hass, "living_room", mock_request)
        
        assert response.status == 200
        import json
        body = json.loads(response.body.decode())
        
        assert body["hours"] == 48
        
        # Verify history tracker was called with 48 hours
        mock_history_tracker.get_history.assert_called_once_with("living_room", hours=48)

    @pytest.mark.asyncio
    async def test_handle_get_history_custom_time_range(
        self, mock_hass, mock_history_tracker, mock_request
    ):
        """Test getting history with custom time range."""
        start = "2024-01-01T00:00:00"
        end = "2024-01-02T00:00:00"
        mock_request.query = {"start_time": start, "end_time": end}
        
        response = await handle_get_history(mock_hass, "living_room", mock_request)
        
        assert response.status == 200
        import json
        body = json.loads(response.body.decode())
        
        assert body["start_time"] == start
        assert body["end_time"] == end
        
        # Verify history tracker was called with datetime objects
        call_args = mock_history_tracker.get_history.call_args
        assert call_args[0][0] == "living_room"
        assert "start_time" in call_args[1]
        assert "end_time" in call_args[1]

    @pytest.mark.asyncio
    async def test_handle_get_history_invalid_time(
        self, mock_hass, mock_history_tracker, mock_request
    ):
        """Test getting history with invalid time format."""
        mock_request.query = {"start_time": "invalid", "end_time": "2024-01-02T00:00:00"}
        
        response = await handle_get_history(mock_hass, "living_room", mock_request)
        
        assert response.status == 400
        import json
        body = json.loads(response.body.decode())
        
        assert "error" in body
        assert "Invalid time parameter" in body["error"]

    @pytest.mark.asyncio
    async def test_handle_get_history_no_tracker(self, mock_hass, mock_request):
        """Test getting history when tracker not available."""
        # Remove history tracker
        mock_hass.data[DOMAIN] = {}
        
        response = await handle_get_history(mock_hass, "living_room", mock_request)
        
        assert response.status == 503
        import json
        body = json.loads(response.body.decode())
        
        assert "error" in body
        assert "not available" in body["error"].lower()

    @pytest.mark.asyncio
    async def test_handle_get_learning_stats(
        self, mock_hass, mock_learning_engine
    ):
        """Test getting learning statistics."""
        response = await handle_get_learning_stats(mock_hass, "living_room")
        
        assert response.status == 200
        import json
        body = json.loads(response.body.decode())
        
        assert body["area_id"] == "living_room"
        assert body["stats"]["total_patterns"] == 10
        assert body["stats"]["confidence"] == 0.85
        
        # Verify learning engine was called
        mock_learning_engine.async_get_learning_stats.assert_called_once_with("living_room")

    @pytest.mark.asyncio
    async def test_handle_get_learning_stats_no_engine(self, mock_hass):
        """Test getting learning stats when engine not available."""
        # Remove learning engine
        mock_hass.data[DOMAIN] = {}
        
        response = await handle_get_learning_stats(mock_hass, "living_room")
        
        assert response.status == 503
        import json
        body = json.loads(response.body.decode())
        
        assert "error" in body
        assert "not available" in body["error"].lower()

    @pytest.mark.asyncio
    async def test_handle_get_history_config(
        self, mock_hass, mock_history_tracker
    ):
        """Test getting history configuration."""
        response = await handle_get_history_config(mock_hass)
        
        assert response.status == 200
        import json
        body = json.loads(response.body.decode())
        
        assert body["retention_days"] == 30
        assert "record_interval_seconds" in body
        assert "record_interval_minutes" in body

    @pytest.mark.asyncio
    async def test_handle_get_history_config_no_tracker(self, mock_hass):
        """Test getting history config when tracker not available."""
        # Remove history tracker
        mock_hass.data[DOMAIN] = {}
        
        response = await handle_get_history_config(mock_hass)
        
        assert response.status == 503
        import json
        body = json.loads(response.body.decode())
        
        assert "error" in body

    @pytest.mark.asyncio
    async def test_handle_set_history_config_success(
        self, mock_hass, mock_history_tracker
    ):
        """Test setting history configuration successfully."""
        data = {"retention_days": 60}
        
        response = await handle_set_history_config(mock_hass, data)
        
        assert response.status == 200
        import json
        body = json.loads(response.body.decode())
        
        assert body["success"] is True
        assert body["retention_days"] == 30
        
        # Verify tracker methods were called
        mock_history_tracker.set_retention_days.assert_called_once_with(60)
        mock_history_tracker.async_save.assert_called_once()
        mock_history_tracker._async_cleanup_old_entries.assert_called_once()

    @pytest.mark.asyncio
    async def test_handle_set_history_config_no_retention_days(self, mock_hass):
        """Test setting history config without retention_days."""
        data = {}
        
        response = await handle_set_history_config(mock_hass, data)
        
        assert response.status == 400
        import json
        body = json.loads(response.body.decode())
        
        assert "error" in body
        assert "required" in body["error"].lower()

    @pytest.mark.asyncio
    async def test_handle_set_history_config_no_tracker(self, mock_hass):
        """Test setting history config when tracker not available."""
        # Remove history tracker
        mock_hass.data[DOMAIN] = {}
        
        data = {"retention_days": 60}
        response = await handle_set_history_config(mock_hass, data)
        
        assert response.status == 503
        import json
        body = json.loads(response.body.decode())
        
        assert "error" in body

    @pytest.mark.asyncio
    async def test_handle_set_history_config_invalid_value(
        self, mock_hass, mock_history_tracker
    ):
        """Test setting history config with invalid value."""
        # Make set_retention_days raise ValueError
        mock_history_tracker.set_retention_days.side_effect = ValueError("Invalid retention")

        data = {"retention_days": -5}
        response = await handle_set_history_config(mock_hass, data)

        assert response.status == 400
        import json
        body = json.loads(response.body.decode())

        assert "error" in body
        assert "Invalid retention" in body["error"]