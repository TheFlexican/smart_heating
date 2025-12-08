"""Tests for history module."""
from __future__ import annotations

from datetime import datetime, timedelta
from unittest.mock import AsyncMock, MagicMock, patch
import pytest

from smart_heating.history import HistoryTracker, CLEANUP_INTERVAL


@pytest.fixture
def mock_hass():
    """Create mock Home Assistant instance."""
    hass = MagicMock()
    return hass


@pytest.fixture
def mock_store():
    """Create mock storage."""
    store = MagicMock()
    store.async_load = AsyncMock(return_value=None)
    store.async_save = AsyncMock()
    return store


@pytest.fixture
async def history_tracker(mock_hass, mock_store):
    """Create history tracker instance."""
    with patch('smart_heating.history.Store', return_value=mock_store):
        tracker = HistoryTracker(mock_hass)
        return tracker


class TestHistoryTrackerInit:
    """Test history tracker initialization."""

    def test_init(self, mock_hass):
        """Test initialization."""
        with patch('smart_heating.history.Store') as mock_store_class:
            tracker = HistoryTracker(mock_hass)
            
            assert tracker.hass == mock_hass
            assert tracker._history == {}
            assert tracker._retention_days == 30  # DEFAULT_HISTORY_RETENTION_DAYS
            assert tracker._cleanup_unsub is None
            
            # Verify store was created
            mock_store_class.assert_called_once()


class TestHistoryTrackerLoad:
    """Test loading history."""

    @pytest.mark.asyncio
    async def test_async_load_no_data(self, history_tracker, mock_store):
        """Test loading when no data in storage."""
        mock_store.async_load.return_value = None
        
        with patch('smart_heating.history.async_track_time_interval') as mock_track:
            await history_tracker.async_load()
            
            # Should have empty history
            assert history_tracker._history == {}
            assert history_tracker._retention_days == 30
            
            # Should schedule cleanup
            mock_track.assert_called_once_with(
                history_tracker.hass,
                history_tracker._async_periodic_cleanup,
                CLEANUP_INTERVAL
            )

    @pytest.mark.asyncio
    async def test_async_load_with_data(self, history_tracker, mock_store):
        """Test loading with existing data."""
        mock_data = {
            "history": {
                "living_room": [
                    {
                        "timestamp": datetime.now().isoformat(),
                        "current_temperature": 20.0,
                        "target_temperature": 21.0,
                        "state": "heating",
                    }
                ]
            },
            "retention_days": 30
        }
        mock_store.async_load.return_value = mock_data
        
        with patch('smart_heating.history.async_track_time_interval'):
            await history_tracker.async_load()
            
            # Should load history and retention
            assert history_tracker._history == mock_data["history"]
            assert history_tracker._retention_days == 30


class TestHistoryTrackerSave:
    """Test saving history."""

    @pytest.mark.asyncio
    async def test_async_save(self, history_tracker, mock_store):
        """Test saving history."""
        history_tracker._history = {
            "living_room": [
                {
                    "timestamp": datetime.now().isoformat(),
                    "current_temperature": 20.0,
                    "target_temperature": 21.0,
                    "state": "heating",
                }
            ]
        }
        history_tracker._retention_days = 30
        
        await history_tracker.async_save()
        
        # Verify save was called with correct data
        mock_store.async_save.assert_called_once()
        call_args = mock_store.async_save.call_args[0][0]
        assert call_args["history"] == history_tracker._history
        assert call_args["retention_days"] == 30


class TestHistoryTrackerUnload:
    """Test unloading history tracker."""

    @pytest.mark.asyncio
    async def test_async_unload(self, history_tracker):
        """Test unloading."""
        # Setup cleanup subscription
        mock_unsub = MagicMock()
        history_tracker._cleanup_unsub = mock_unsub
        
        await history_tracker.async_unload()
        
        # Should call unsub and clear it
        mock_unsub.assert_called_once()
        assert history_tracker._cleanup_unsub is None


class TestHistoryTrackerCleanup:
    """Test history cleanup."""

    @pytest.mark.asyncio
    async def test_cleanup_old_entries(self, history_tracker, mock_store):
        """Test cleaning up old entries."""
        # Create entries: some old, some new
        now = datetime.now()
        old_entry = {
            "timestamp": (now - timedelta(days=100)).isoformat(),
            "current_temperature": 19.0,
            "target_temperature": 20.0,
            "state": "heating",
        }
        new_entry = {
            "timestamp": now.isoformat(),
            "current_temperature": 20.0,
            "target_temperature": 21.0,
            "state": "heating",
        }
        
        history_tracker._history = {
            "living_room": [old_entry, new_entry]
        }
        history_tracker._retention_days = 30
        
        await history_tracker._async_cleanup_old_entries()
        
        # Old entry should be removed
        assert len(history_tracker._history["living_room"]) == 1
        assert history_tracker._history["living_room"][0] == new_entry
        
        # Should save after cleanup
        mock_store.async_save.assert_called_once()

    @pytest.mark.asyncio
    async def test_cleanup_no_old_entries(self, history_tracker, mock_store):
        """Test cleanup when no old entries."""
        now = datetime.now()
        new_entry = {
            "timestamp": now.isoformat(),
            "current_temperature": 20.0,
            "target_temperature": 21.0,
            "state": "heating",
        }
        
        history_tracker._history = {
            "living_room": [new_entry]
        }
        
        await history_tracker._async_cleanup_old_entries()
        
        # All entries should remain
        assert len(history_tracker._history["living_room"]) == 1
        
        # Should not save when nothing removed
        mock_store.async_save.assert_not_called()

    @pytest.mark.asyncio
    async def test_periodic_cleanup(self, history_tracker):
        """Test periodic cleanup task."""
        history_tracker._async_cleanup_old_entries = AsyncMock()
        
        await history_tracker._async_periodic_cleanup()
        
        # Should call cleanup
        history_tracker._async_cleanup_old_entries.assert_called_once()


class TestHistoryTrackerRecord:
    """Test recording temperature."""

    @pytest.mark.asyncio
    async def test_record_temperature_new_area(self, history_tracker):
        """Test recording temperature for new area."""
        await history_tracker.async_record_temperature(
            "living_room", 20.0, 21.0, "heating"
        )
        
        # Should create history for area
        assert "living_room" in history_tracker._history
        assert len(history_tracker._history["living_room"]) == 1
        
        entry = history_tracker._history["living_room"][0]
        assert entry["current_temperature"] == 20.0
        assert entry["target_temperature"] == 21.0
        assert entry["state"] == "heating"
        assert "timestamp" in entry

    @pytest.mark.asyncio
    async def test_record_temperature_existing_area(self, history_tracker):
        """Test recording temperature for existing area."""
        # Add existing entry
        history_tracker._history["living_room"] = [
            {
                "timestamp": datetime.now().isoformat(),
                "current_temperature": 19.0,
                "target_temperature": 20.0,
                "state": "heating",
            }
        ]
        
        await history_tracker.async_record_temperature(
            "living_room", 20.5, 21.0, "heating"
        )
        
        # Should append new entry
        assert len(history_tracker._history["living_room"]) == 2
        assert history_tracker._history["living_room"][1]["current_temperature"] == 20.5

    @pytest.mark.asyncio
    async def test_record_temperature_limit(self, history_tracker):
        """Test that history is limited to 1000 entries."""
        # Create 1001 entries
        history_tracker._history["living_room"] = [
            {
                "timestamp": datetime.now().isoformat(),
                "current_temperature": 20.0,
                "target_temperature": 21.0,
                "state": "heating",
            }
            for _ in range(1001)
        ]
        
        await history_tracker.async_record_temperature(
            "living_room", 20.5, 21.0, "heating"
        )
        
        # Should limit to 1000 entries
        assert len(history_tracker._history["living_room"]) == 1000


class TestHistoryTrackerGet:
    """Test getting history."""

    def test_get_history_no_data(self, history_tracker):
        """Test getting history for area with no data."""
        result = history_tracker.get_history("unknown_area")
        
        assert result == []

    def test_get_history_all(self, history_tracker):
        """Test getting all history."""
        history_tracker._history["living_room"] = [
            {
                "timestamp": datetime.now().isoformat(),
                "current_temperature": 20.0,
                "target_temperature": 21.0,
                "state": "heating",
            }
        ]
        
        result = history_tracker.get_history("living_room")
        
        assert len(result) == 1
        assert result == history_tracker._history["living_room"]

    def test_get_history_hours(self, history_tracker):
        """Test getting history for specific hours."""
        now = datetime.now()
        old_entry = {
            "timestamp": (now - timedelta(hours=25)).isoformat(),
            "current_temperature": 19.0,
            "target_temperature": 20.0,
            "state": "heating",
        }
        recent_entry = {
            "timestamp": (now - timedelta(hours=1)).isoformat(),
            "current_temperature": 20.0,
            "target_temperature": 21.0,
            "state": "heating",
        }
        
        history_tracker._history["living_room"] = [old_entry, recent_entry]
        
        result = history_tracker.get_history("living_room", hours=24)
        
        # Should only return entry from last 24 hours
        assert len(result) == 1
        assert result[0] == recent_entry

    def test_get_history_custom_range(self, history_tracker):
        """Test getting history for custom time range."""
        now = datetime.now()
        entries = [
            {
                "timestamp": (now - timedelta(days=5)).isoformat(),
                "current_temperature": 18.0,
                "target_temperature": 19.0,
                "state": "heating",
            },
            {
                "timestamp": (now - timedelta(days=3)).isoformat(),
                "current_temperature": 19.0,
                "target_temperature": 20.0,
                "state": "heating",
            },
            {
                "timestamp": (now - timedelta(days=1)).isoformat(),
                "current_temperature": 20.0,
                "target_temperature": 21.0,
                "state": "heating",
            },
        ]
        
        history_tracker._history["living_room"] = entries
        
        start = now - timedelta(days=4)
        end = now - timedelta(days=2)
        
        result = history_tracker.get_history("living_room", start_time=start, end_time=end)
        
        # Should only return entry within custom range
        assert len(result) == 1
        assert result[0] == entries[1]

    def test_get_all_history(self, history_tracker):
        """Test getting all history for all areas."""
        history_tracker._history = {
            "living_room": [{"timestamp": datetime.now().isoformat()}],
            "bedroom": [{"timestamp": datetime.now().isoformat()}],
        }
        
        result = history_tracker.get_all_history()
        
        assert result == history_tracker._history
        assert len(result) == 2


class TestHistoryTrackerRetention:
    """Test retention settings."""

    def test_set_retention_days(self, history_tracker):
        """Test setting retention days."""
        history_tracker.set_retention_days(30)
        
        assert history_tracker._retention_days == 30

    def test_set_retention_days_invalid(self, history_tracker):
        """Test setting invalid retention days."""
        with pytest.raises(ValueError, match="at least 1 day"):
            history_tracker.set_retention_days(0)

    def test_get_retention_days(self, history_tracker):
        """Test getting retention days."""
        history_tracker._retention_days = 45
        
        assert history_tracker.get_retention_days() == 45
