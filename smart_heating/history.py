"""History tracking for Smart Heating."""

import logging
from datetime import datetime, timedelta
from typing import Any

from homeassistant.core import HomeAssistant
from homeassistant.helpers.event import async_track_time_interval
from homeassistant.helpers.storage import Store

from .const import DEFAULT_HISTORY_RETENTION_DAYS

_LOGGER = logging.getLogger(__name__)

STORAGE_VERSION = 1
STORAGE_KEY = "smart_heating_history"
CLEANUP_INTERVAL = timedelta(hours=1)  # Run cleanup every hour


class HistoryTracker:
    """Track temperature history for areas."""

    def __init__(self, hass: HomeAssistant) -> None:
        """Initialize the history tracker.

        Args:
            hass: Home Assistant instance
        """
        self.hass = hass
        self._store = Store(hass, STORAGE_VERSION, STORAGE_KEY)
        self._history: dict[str, list[dict[str, Any]]] = {}
        self._retention_days: int = DEFAULT_HISTORY_RETENTION_DAYS
        self._cleanup_unsub = None

    async def async_load(self) -> None:
        """Load history from storage."""
        _LOGGER.debug("Loading history from storage")
        data = await self._store.async_load()

        if data is not None:
            if "history" in data:
                self._history = data["history"]
            if "retention_days" in data:
                self._retention_days = data["retention_days"]

            # Clean up old entries
            await self._async_cleanup_old_entries()
            _LOGGER.info(
                "Loaded history for %d areas (retention: %d days)",
                len(self._history),
                self._retention_days,
            )
        else:
            _LOGGER.debug("No history found in storage")

        # Schedule periodic cleanup
        self._cleanup_unsub = async_track_time_interval(
            self.hass, self._async_periodic_cleanup, CLEANUP_INTERVAL
        )
        _LOGGER.info("History cleanup scheduled every %s", CLEANUP_INTERVAL)

    async def async_save(self) -> None:
        """Save history to storage."""
        _LOGGER.debug("Saving history to storage")
        data = {"history": self._history, "retention_days": self._retention_days}
        await self._store.async_save(data)

    async def async_unload(self) -> None:
        """Unload and cleanup."""
        if self._cleanup_unsub:
            self._cleanup_unsub()
            self._cleanup_unsub = None
        _LOGGER.debug("History tracker unloaded")

    async def _async_cleanup_old_entries(self) -> None:
        """Remove entries older than retention period."""
        cutoff = datetime.now() - timedelta(days=self._retention_days)
        cutoff_iso = cutoff.isoformat()

        total_removed = 0
        for area_id in list(self._history.keys()):
            original_count = len(self._history[area_id])
            self._history[area_id] = [
                entry for entry in self._history[area_id] if entry["timestamp"] > cutoff_iso
            ]
            removed = original_count - len(self._history[area_id])
            total_removed += removed
            if removed > 0:
                _LOGGER.debug(
                    "Removed %d old entries for area %s (retention: %d days)",
                    removed,
                    area_id,
                    self._retention_days,
                )

        if total_removed > 0:
            _LOGGER.info(
                "History cleanup: removed %d entries older than %d days",
                total_removed,
                self._retention_days,
            )
            await self.async_save()

    async def _async_periodic_cleanup(self, now=None) -> None:
        """Periodic cleanup task."""
        _LOGGER.debug("Running periodic history cleanup")
        await self._async_cleanup_old_entries()

    async def async_record_temperature(
        self,
        area_id: str,
        current_temp: float,
        target_temp: float,
        state: str,
    ) -> None:
        """Record a temperature reading.

        Args:
            area_id: Area identifier
            current_temp: Current temperature
            target_temp: Target temperature
            state: Area state (heating/idle/off)
        """
        if area_id not in self._history:
            self._history[area_id] = []

        entry = {
            "timestamp": datetime.now().isoformat(),
            "current_temperature": current_temp,
            "target_temperature": target_temp,
            "state": state,
        }

        self._history[area_id].append(entry)

        # Limit to last 1000 entries per area
        if len(self._history[area_id]) > 1000:
            self._history[area_id] = self._history[area_id][-1000:]

        _LOGGER.debug(
            "Recorded temperature for %s: %.1f°C (target: %.1f°C, state: %s)",
            area_id,
            current_temp,
            target_temp,
            state,
        )

    def get_history(
        self,
        area_id: str,
        hours: int | None = None,
        start_time: datetime | None = None,
        end_time: datetime | None = None,
    ) -> list[dict[str, Any]]:
        """Get temperature history for an area.

        Args:
            area_id: Area identifier
            hours: Number of hours to retrieve (default: None, returns all within retention)
            start_time: Custom start time (optional)
            end_time: Custom end time (optional, defaults to now)

        Returns:
            List of history entries
        """
        if area_id not in self._history:
            return []

        # Determine time range
        if start_time and end_time:
            # Custom time range
            start_iso = start_time.isoformat()
            end_iso = end_time.isoformat()
            return [
                entry
                for entry in self._history[area_id]
                if start_iso <= entry["timestamp"] <= end_iso
            ]
        elif hours:
            # Hours-based query
            cutoff = datetime.now() - timedelta(hours=hours)
            cutoff_iso = cutoff.isoformat()
            return [entry for entry in self._history[area_id] if entry["timestamp"] > cutoff_iso]
        else:
            # Return all available history (within retention period)
            return self._history[area_id]

    def get_all_history(self) -> dict[str, list[dict[str, Any]]]:
        """Get all history.

        Returns:
            Dictionary of area_id -> history entries
        """
        return self._history

    def set_retention_days(self, days: int) -> None:
        """Set the history retention period.

        Args:
            days: Number of days to retain history
        """
        if days < 1:
            raise ValueError("Retention period must be at least 1 day")

        old_retention = self._retention_days
        self._retention_days = days
        _LOGGER.info("History retention changed from %d to %d days", old_retention, days)

    def get_retention_days(self) -> int:
        """Get the current retention period.

        Returns:
            Number of days history is retained
        """
        return self._retention_days
