"""Area-specific logging for Smart Heating development."""

import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Any

from homeassistant.core import HomeAssistant

_LOGGER = logging.getLogger(__name__)

# Maximum log entries per file (rotated when exceeded)
MAX_LOG_ENTRIES_PER_FILE = 1000

# Valid event types
EVENT_TYPES = ["temperature", "heating", "schedule", "smart_boost", "sensor", "mode"]


class AreaLogger:
    """Logger for tracking heating strategy decisions per area.

    Logs are stored in separate files per event type for efficient filtering:
    .storage/smart_heating/logs/{area_id}/{event_type}.jsonl
    """

    def __init__(self, storage_path: str, hass: HomeAssistant) -> None:
        """Initialize the area logger.

        Args:
            storage_path: Base path to store logs (e.g., .storage/smart_heating)
            hass: Home Assistant instance for async operations
        """
        self._base_path = Path(storage_path) / "logs"
        self._base_path.mkdir(parents=True, exist_ok=True)
        self._hass = hass
        _LOGGER.info("Area logger initialized at %s", self._base_path)

    def _get_log_file_path(self, area_id: str, event_type: str) -> Path:
        """Get the log file path for an area and event type.

        Args:
            area_id: Area identifier
            event_type: Type of event

        Returns:
            Path to the log file
        """
        area_path = self._base_path / area_id
        area_path.mkdir(parents=True, exist_ok=True)
        return area_path / f"{event_type}.jsonl"

    def log_event(
        self, area_id: str, event_type: str, message: str, details: dict[str, Any] | None = None
    ) -> None:
        """Log an event for a specific area (schedules async file write).

        Args:
            area_id: Area identifier
            event_type: Type of event (temperature, heating, schedule, smart_boost, sensor, mode)
            message: Human-readable message
            details: Additional event details
        """
        if event_type not in EVENT_TYPES:
            _LOGGER.warning("Unknown event type '%s', using 'mode'", event_type)
            event_type = "mode"

        entry = {
            "timestamp": datetime.now().isoformat(),
            "type": event_type,
            "message": message,
            "details": details or {},
        }

        # Schedule async write (non-blocking)
        self._hass.async_create_task(self._async_write_log(area_id, event_type, entry))

        # Also log to standard logger for debugging
        _LOGGER.debug(
            "[%s] %s: %s %s",
            area_id,
            event_type.upper(),
            message,
            f"({details})" if details else "",
        )

    async def _async_write_log(self, area_id: str, event_type: str, entry: dict) -> None:
        """Asynchronously write log entry to file.

        Args:
            area_id: Area identifier
            event_type: Event type
            entry: Log entry to write
        """
        log_file = self._get_log_file_path(area_id, event_type)

        def _write():
            try:
                with open(log_file, "a", encoding="utf-8") as f:
                    f.write(json.dumps(entry) + "\n")
            except Exception as err:
                _LOGGER.error("Failed to write log for area %s: %s", area_id, err)

        # Run file I/O in executor to avoid blocking
        await self._hass.async_add_executor_job(_write)

        # Check if rotation needed (also async)
        await self._async_rotate_if_needed(log_file)

    async def _async_rotate_if_needed(self, log_file: Path) -> None:
        """Rotate log file if it exceeds the maximum entries.

        Args:
            log_file: Path to the log file
        """

        def _rotate():
            try:
                # Count lines in file
                with open(log_file, "r", encoding="utf-8") as f:
                    line_count = sum(1 for _ in f)

                if line_count > MAX_LOG_ENTRIES_PER_FILE:
                    # Keep only the last MAX_LOG_ENTRIES_PER_FILE entries
                    with open(log_file, "r", encoding="utf-8") as f:
                        lines = f.readlines()

                    # Write back only the newest entries
                    with open(log_file, "w", encoding="utf-8") as f:
                        f.writelines(lines[-MAX_LOG_ENTRIES_PER_FILE:])

                    _LOGGER.debug("Rotated log file %s", log_file)

            except Exception as err:
                _LOGGER.error("Failed to rotate log file %s: %s", log_file, err)

        # Run rotation in executor to avoid blocking
        await self._hass.async_add_executor_job(_rotate)

    async def async_get_logs(
        self, area_id: str, limit: int | None = None, event_type: str | None = None
    ) -> list[dict[str, Any]]:
        """Get logs for a specific area (async).

        Args:
            area_id: Area identifier
            limit: Maximum number of entries to return
            event_type: Filter by event type (or None for all types)

        Returns:
            List of log entries (newest first)
        """
        logs = []

        if event_type:
            # Read from specific event type file
            log_file = self._get_log_file_path(area_id, event_type)
            if log_file.exists():
                logs = await self._async_read_log_file(log_file)
        else:
            # Read from all event type files and merge
            area_path = self._base_path / area_id
            if area_path.exists():
                for event_type_file in EVENT_TYPES:
                    log_file = area_path / f"{event_type_file}.jsonl"
                    if log_file.exists():
                        file_logs = await self._async_read_log_file(log_file)
                        logs.extend(file_logs)

        # Sort by timestamp (newest first)
        logs.sort(key=lambda x: x["timestamp"], reverse=True)

        # Apply limit
        if limit:
            logs = logs[:limit]

        return logs

    async def _async_read_log_file(self, log_file: Path) -> list[dict[str, Any]]:
        """Read all entries from a log file (async).

        Args:
            log_file: Path to the log file

        Returns:
            List of log entries
        """

        def _read():
            logs = []
            try:
                with open(log_file, "r", encoding="utf-8") as f:
                    for line in f:
                        try:
                            logs.append(json.loads(line.strip()))
                        except json.JSONDecodeError:
                            continue
            except Exception as err:
                _LOGGER.error("Failed to read log file %s: %s", log_file, err)
            return logs

        # Run file read in executor to avoid blocking
        return await self._hass.async_add_executor_job(_read)

    def clear_logs(self, area_id: str, event_type: str | None = None) -> None:
        """Clear logs for an area.

        Args:
            area_id: Area identifier
            event_type: Clear specific event type (or None for all)
        """
        area_path = self._base_path / area_id

        if event_type:
            # Clear specific event type
            log_file = area_path / f"{event_type}.jsonl"
            if log_file.exists():
                log_file.unlink()
                _LOGGER.info("Cleared %s logs for area %s", event_type, area_id)
        else:
            # Clear all event types
            if area_path.exists():
                for log_file in area_path.glob("*.jsonl"):
                    log_file.unlink()
                _LOGGER.info("Cleared all logs for area %s", area_id)

    def get_all_area_ids(self) -> list[str]:
        """Get all area IDs that have logs.

        Returns:
            List of area IDs
        """
        if not self._base_path.exists():
            return []

        return [d.name for d in self._base_path.iterdir() if d.is_dir()]

    def get_event_types(self, area_id: str) -> list[str]:
        """Get all event types that have logs for an area.

        Args:
            area_id: Area identifier

        Returns:
            List of event types
        """
        area_path = self._base_path / area_id
        if not area_path.exists():
            return []

        return [f.stem for f in area_path.glob("*.jsonl")]
