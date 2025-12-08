"""Tests for Area Logger.

Tests logging functionality, file operations, log rotation, and querying.
"""

import json
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch, mock_open

import pytest
from homeassistant.core import HomeAssistant

from smart_heating.area_logger import AreaLogger, EVENT_TYPES, MAX_LOG_ENTRIES_PER_FILE

from tests.unit.const import TEST_AREA_ID


@pytest.fixture
def area_logger(hass: HomeAssistant, tmp_path) -> AreaLogger:
    """Create an AreaLogger instance."""
    return AreaLogger(str(tmp_path), hass)


class TestInitialization:
    """Tests for initialization."""

    def test_init(self, area_logger: AreaLogger, tmp_path):
        """Test area logger initialization."""
        assert area_logger._base_path == Path(tmp_path) / "logs"
        assert area_logger._base_path.exists()
        assert area_logger._hass is not None

    def test_get_log_file_path(self, area_logger: AreaLogger):
        """Test getting log file path."""
        path = area_logger._get_log_file_path(TEST_AREA_ID, "temperature")
        
        assert path.name == "temperature.jsonl"
        assert TEST_AREA_ID in str(path)


class TestLogging:
    """Tests for logging events."""

    def test_log_event(self, area_logger: AreaLogger):
        """Test logging an event."""
        with patch.object(area_logger._hass, 'async_create_task') as mock_task:
            area_logger.log_event(
                TEST_AREA_ID,
                "temperature",
                "Temperature changed to 20.5°C",
                {"temperature": 20.5}
            )
        
        # Should schedule async write
        mock_task.assert_called_once()

    def test_log_event_unknown_type(self, area_logger: AreaLogger):
        """Test logging event with unknown type defaults to 'mode'."""
        with patch.object(area_logger._hass, 'async_create_task') as mock_task:
            area_logger.log_event(
                TEST_AREA_ID,
                "unknown_type",
                "Test message"
            )
        
        # Should still schedule write with type changed to 'mode'
        mock_task.assert_called_once()

    @pytest.mark.asyncio
    async def test_async_write_log(self, area_logger: AreaLogger, hass: HomeAssistant):
        """Test async writing of log entry."""
        entry = {
            "timestamp": "2024-01-01T12:00:00",
            "type": "temperature",
            "message": "Test message",
            "details": {}
        }
        
        with patch.object(area_logger, '_async_rotate_if_needed', new_callable=AsyncMock):
            await area_logger._async_write_log(TEST_AREA_ID, "temperature", entry)
        
        # Verify file was created and written
        log_file = area_logger._get_log_file_path(TEST_AREA_ID, "temperature")
        assert log_file.exists()
        
        # Verify content
        with open(log_file, 'r') as f:
            logged_entry = json.loads(f.readline())
        
        assert logged_entry["message"] == "Test message"

    @pytest.mark.asyncio
    async def test_async_write_log_error_handling(self, area_logger: AreaLogger, hass: HomeAssistant):
        """Test async write handles file errors gracefully."""
        entry = {"timestamp": "2024-01-01T12:00:00", "type": "test", "message": "Test"}
        
        # Use a path that will fail to write
        with patch.object(area_logger, '_get_log_file_path', return_value=Path("/nonexistent/invalid/path.jsonl")):
            with patch.object(area_logger, '_async_rotate_if_needed', new_callable=AsyncMock):
                # Should not raise exception despite the invalid path
                await area_logger._async_write_log(TEST_AREA_ID, "temperature", entry)


class TestRotation:
    """Tests for log rotation."""

    @pytest.mark.asyncio
    async def test_rotate_if_needed_small_file(self, area_logger: AreaLogger):
        """Test rotation skips file below threshold."""
        log_file = area_logger._get_log_file_path(TEST_AREA_ID, "temperature")
        
        # Write a few entries
        with open(log_file, 'w') as f:
            for i in range(10):
                f.write(json.dumps({"entry": i}) + '\n')
        
        await area_logger._async_rotate_if_needed(log_file)
        
        # Should still have 10 lines
        with open(log_file, 'r') as f:
            lines = f.readlines()
        assert len(lines) == 10

    @pytest.mark.asyncio
    async def test_rotate_if_needed_large_file(self, area_logger: AreaLogger):
        """Test rotation trims file exceeding threshold."""
        log_file = area_logger._get_log_file_path(TEST_AREA_ID, "temperature")
        
        # Write more than MAX_LOG_ENTRIES_PER_FILE entries
        num_entries = MAX_LOG_ENTRIES_PER_FILE + 100
        with open(log_file, 'w') as f:
            for i in range(num_entries):
                f.write(json.dumps({"entry": i}) + '\n')
        
        await area_logger._async_rotate_if_needed(log_file)
        
        # Should be trimmed to MAX_LOG_ENTRIES_PER_FILE
        with open(log_file, 'r') as f:
            lines = f.readlines()
        assert len(lines) == MAX_LOG_ENTRIES_PER_FILE

    @pytest.mark.asyncio
    async def test_rotate_if_needed_error_handling(self, area_logger: AreaLogger):
        """Test rotation handles errors gracefully."""
        log_file = Path("/nonexistent/path/file.jsonl")
        
        # Should not raise exception
        try:
            await area_logger._async_rotate_if_needed(log_file)
        except Exception:
            pytest.fail("_async_rotate_if_needed should handle errors gracefully")


class TestReading:
    """Tests for reading logs."""

    @pytest.mark.asyncio
    async def test_async_get_logs_single_type(self, area_logger: AreaLogger):
        """Test getting logs for single event type."""
        # Write some logs
        log_file = area_logger._get_log_file_path(TEST_AREA_ID, "temperature")
        with open(log_file, 'w') as f:
            f.write(json.dumps({"timestamp": "2024-01-01T12:00:00", "message": "Entry 1"}) + '\n')
            f.write(json.dumps({"timestamp": "2024-01-01T12:01:00", "message": "Entry 2"}) + '\n')
        
        logs = await area_logger.async_get_logs(TEST_AREA_ID, event_type="temperature")
        
        assert len(logs) == 2
        # Should be sorted newest first
        assert logs[0]["message"] == "Entry 2"

    @pytest.mark.asyncio
    async def test_async_get_logs_all_types(self, area_logger: AreaLogger):
        """Test getting logs from all event types."""
        # Write logs to multiple files
        temp_file = area_logger._get_log_file_path(TEST_AREA_ID, "temperature")
        with open(temp_file, 'w') as f:
            f.write(json.dumps({"timestamp": "2024-01-01T12:00:00", "message": "Temp 1"}) + '\n')
        
        heating_file = area_logger._get_log_file_path(TEST_AREA_ID, "heating")
        with open(heating_file, 'w') as f:
            f.write(json.dumps({"timestamp": "2024-01-01T12:01:00", "message": "Heat 1"}) + '\n')
        
        logs = await area_logger.async_get_logs(TEST_AREA_ID)
        
        assert len(logs) == 2
        # Should be sorted newest first (heating before temp)
        assert logs[0]["message"] == "Heat 1"

    @pytest.mark.asyncio
    async def test_async_get_logs_with_limit(self, area_logger: AreaLogger):
        """Test getting logs with limit."""
        # Write 5 logs
        log_file = area_logger._get_log_file_path(TEST_AREA_ID, "temperature")
        with open(log_file, 'w') as f:
            for i in range(5):
                f.write(json.dumps({"timestamp": f"2024-01-01T12:0{i}:00", "message": f"Entry {i}"}) + '\n')
        
        logs = await area_logger.async_get_logs(TEST_AREA_ID, limit=2)
        
        assert len(logs) == 2

    @pytest.mark.asyncio
    async def test_async_get_logs_nonexistent_area(self, area_logger: AreaLogger):
        """Test getting logs for nonexistent area."""
        logs = await area_logger.async_get_logs("nonexistent_area")
        
        assert logs == []

    @pytest.mark.asyncio
    async def test_async_read_log_file(self, area_logger: AreaLogger):
        """Test reading individual log file."""
        log_file = area_logger._get_log_file_path(TEST_AREA_ID, "temperature")
        with open(log_file, 'w') as f:
            f.write(json.dumps({"message": "Entry 1"}) + '\n')
            f.write(json.dumps({"message": "Entry 2"}) + '\n')
        
        logs = await area_logger._async_read_log_file(log_file)
        
        assert len(logs) == 2

    @pytest.mark.asyncio
    async def test_async_read_log_file_corrupted(self, area_logger: AreaLogger):
        """Test reading file with corrupted JSON."""
        log_file = area_logger._get_log_file_path(TEST_AREA_ID, "temperature")
        with open(log_file, 'w') as f:
            f.write(json.dumps({"message": "Entry 1"}) + '\n')
            f.write("invalid json{" + '\n')
            f.write(json.dumps({"message": "Entry 2"}) + '\n')
        
        logs = await area_logger._async_read_log_file(log_file)
        
        # Should skip corrupted entry
        assert len(logs) == 2


class TestClearLogs:
    """Tests for clearing logs."""

    def test_clear_logs_specific_type(self, area_logger: AreaLogger):
        """Test clearing specific event type."""
        # Create log files
        temp_file = area_logger._get_log_file_path(TEST_AREA_ID, "temperature")
        heating_file = area_logger._get_log_file_path(TEST_AREA_ID, "heating")
        
        temp_file.write_text("test")
        heating_file.write_text("test")
        
        # Clear only temperature logs
        area_logger.clear_logs(TEST_AREA_ID, event_type="temperature")
        
        assert not temp_file.exists()
        assert heating_file.exists()

    def test_clear_logs_all_types(self, area_logger: AreaLogger):
        """Test clearing all event types."""
        # Create log files
        temp_file = area_logger._get_log_file_path(TEST_AREA_ID, "temperature")
        heating_file = area_logger._get_log_file_path(TEST_AREA_ID, "heating")
        
        temp_file.write_text("test")
        heating_file.write_text("test")
        
        # Clear all logs
        area_logger.clear_logs(TEST_AREA_ID)
        
        assert not temp_file.exists()
        assert not heating_file.exists()

    def test_clear_logs_nonexistent_area(self, area_logger: AreaLogger):
        """Test clearing logs for nonexistent area."""
        # Should not crash
        area_logger.clear_logs("nonexistent_area")


class TestHelpers:
    """Tests for helper methods."""

    def test_get_all_area_ids(self, area_logger: AreaLogger):
        """Test getting all area IDs."""
        # Create log files for multiple areas
        area1_file = area_logger._get_log_file_path("area1", "temperature")
        area2_file = area_logger._get_log_file_path("area2", "temperature")
        
        area1_file.write_text("test")
        area2_file.write_text("test")
        
        area_ids = area_logger.get_all_area_ids()
        
        assert len(area_ids) == 2
        assert "area1" in area_ids
        assert "area2" in area_ids

    def test_get_all_area_ids_empty(self, area_logger: AreaLogger):
        """Test getting area IDs when none exist."""
        # Remove the logs directory
        area_logger._base_path.rmdir()
        
        area_ids = area_logger.get_all_area_ids()
        
        assert area_ids == []

    def test_get_event_types(self, area_logger: AreaLogger):
        """Test getting event types for an area."""
        # Create log files for different event types
        temp_file = area_logger._get_log_file_path(TEST_AREA_ID, "temperature")
        heating_file = area_logger._get_log_file_path(TEST_AREA_ID, "heating")
        
        temp_file.write_text("test")
        heating_file.write_text("test")
        
        event_types = area_logger.get_event_types(TEST_AREA_ID)
        
        assert len(event_types) == 2
        assert "temperature" in event_types
        assert "heating" in event_types

    def test_get_event_types_nonexistent_area(self, area_logger: AreaLogger):
        """Test getting event types for nonexistent area."""
        event_types = area_logger.get_event_types("nonexistent_area")
        
        assert event_types == []
