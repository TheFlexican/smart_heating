"""History tracking for Smart Heating."""

import logging
from datetime import datetime, timedelta
from typing import Any

from homeassistant.components.recorder import get_instance
from homeassistant.core import HomeAssistant
from homeassistant.helpers.event import async_track_time_interval
from homeassistant.helpers.storage import Store
from sqlalchemy import Column, DateTime, Float, Integer, String, Table, MetaData, select, delete
from sqlalchemy.exc import SQLAlchemyError

from .const import (
    DEFAULT_HISTORY_RETENTION_DAYS,
    MAX_HISTORY_RETENTION_DAYS,
    HISTORY_STORAGE_JSON,
    HISTORY_STORAGE_DATABASE,
)

_LOGGER = logging.getLogger(__name__)

STORAGE_VERSION = 1
STORAGE_KEY = "smart_heating_history"
CLEANUP_INTERVAL = timedelta(hours=1)  # Run cleanup every hour

# Database table name
DB_TABLE_NAME = "smart_heating_history"


class HistoryTracker:
    """Track temperature history for areas with optional database storage."""

    def __init__(self, hass: HomeAssistant, storage_backend: str = HISTORY_STORAGE_JSON) -> None:
        """Initialize the history tracker.

        Args:
            hass: Home Assistant instance
            storage_backend: Storage backend to use (json or database)
        """
        self.hass = hass
        self._storage_backend = storage_backend
        self._store = Store(hass, STORAGE_VERSION, STORAGE_KEY)
        self._history: dict[str, list[dict[str, Any]]] = {}
        self._retention_days: int = DEFAULT_HISTORY_RETENTION_DAYS
        self._cleanup_unsub = None
        self._db_table = None
        self._db_engine = None
        self._db_validated = False
        
    async def _async_validate_database_support(self) -> None:
        """Validate that database storage is supported."""
        if self._db_validated:
            return
            
        try:
            recorder = get_instance(self.hass)
            if not recorder:
                _LOGGER.warning("Recorder not available, falling back to JSON storage")
                self._storage_backend = HISTORY_STORAGE_JSON
                self._db_validated = True
                return
                
            db_url = str(recorder.db_url)
            
            # Check if it's SQLite (not supported for database storage)
            if "sqlite" in db_url.lower():
                _LOGGER.warning(
                    "SQLite database detected. Database storage not supported, "
                    "falling back to JSON storage"
                )
                self._storage_backend = HISTORY_STORAGE_JSON
                self._db_validated = True
                return
            
            # Supported: MariaDB, MySQL, PostgreSQL
            if any(db in db_url.lower() for db in ["mysql", "mariadb", "postgresql", "postgres"]):
                db_type = "MariaDB/MySQL" if "mysql" in db_url.lower() or "mariadb" in db_url.lower() else "PostgreSQL"
                _LOGGER.info("Database storage enabled with %s", db_type)
                self._init_database_table()
                self._db_validated = True
            else:
                _LOGGER.warning(
                    "Unsupported database type for history storage, falling back to JSON"
                )
                self._storage_backend = HISTORY_STORAGE_JSON
                self._db_validated = True
            
        except Exception as e:  # pylint: disable=broad-except
            _LOGGER.error("Error validating database support: %s, falling back to JSON", e, exc_info=True)
            self._storage_backend = HISTORY_STORAGE_JSON
            self._db_validated = True

    def _init_database_table(self) -> None:
        """Initialize the database table for history storage."""
        try:
            recorder = get_instance(self.hass)
            self._db_engine = recorder.engine
            
            metadata = MetaData()
            self._db_table = Table(
                DB_TABLE_NAME,
                metadata,
                Column("id", Integer, primary_key=True, autoincrement=True),
                Column("area_id", String(255), nullable=False, index=True),
                Column("timestamp", DateTime, nullable=False, index=True),
                Column("current_temperature", Float, nullable=False),
                Column("target_temperature", Float, nullable=False),
                Column("state", String(50), nullable=False),
            )
            
            # Create table if it doesn't exist
            metadata.create_all(self._db_engine)
            _LOGGER.info("Database table '%s' ready for history storage", DB_TABLE_NAME)
            
        except Exception as e:
            _LOGGER.error("Failed to initialize database table: %s, falling back to JSON", e)
            self._storage_backend = HISTORY_STORAGE_JSON
            self._db_table = None
            self._db_engine = None

    async def async_load(self) -> None:
        """Load history from storage."""
        # First, check if there's a stored backend preference in JSON
        data = await self._store.async_load()
        if data and "storage_backend" in data:
            self._storage_backend = data["storage_backend"]
        
        # Validate database support if backend is set to database
        if self._storage_backend == HISTORY_STORAGE_DATABASE:
            await self._async_validate_database_support()
        
        # Now load the actual data
        if self._storage_backend == HISTORY_STORAGE_DATABASE and self._db_table is not None:
            await self._async_load_from_database()
        else:
            await self._async_load_from_json()
        
        # Schedule periodic cleanup
        self._cleanup_unsub = async_track_time_interval(
            self.hass, self._async_periodic_cleanup, CLEANUP_INTERVAL
        )
        _LOGGER.info("History cleanup scheduled every %s", CLEANUP_INTERVAL)

    async def _async_load_from_json(self) -> None:
        """Load history from JSON storage."""
        data = await self._store.async_load()

        if data is not None:
            if "history" in data:
                self._history = data["history"]
            if "retention_days" in data:
                self._retention_days = data["retention_days"]
            if "storage_backend" in data:
                # Preserve storage backend preference
                self._storage_backend = data.get("storage_backend", HISTORY_STORAGE_JSON)

            # Clean up old entries
            await self._async_cleanup_old_entries()
            _LOGGER.info(
                "Loaded history for %d areas (retention: %d days, storage: JSON)",
                len(self._history),
                self._retention_days,
            )
        else:
            _LOGGER.debug("No history found in JSON storage")

    async def _async_load_from_database(self) -> None:
        """Load history from database."""
        try:
            recorder = get_instance(self.hass)
            
            def _load():
                with recorder.engine.connect() as conn:
                    # Load retention setting from JSON config
                    stmt = select(self._db_table).order_by(self._db_table.c.timestamp.desc())
                    result = conn.execute(stmt)
                    
                    history_dict = {}
                    for row in result:
                        area_id = row.area_id
                        if area_id not in history_dict:
                            history_dict[area_id] = []
                        
                        history_dict[area_id].append({
                            "timestamp": row.timestamp.isoformat(),
                            "current_temperature": row.current_temperature,
                            "target_temperature": row.target_temperature,
                            "state": row.state,
                        })
                    
                    return history_dict
            
            self._history = await recorder.async_add_executor_job(_load)
            
            # Load retention setting from JSON store
            data = await self._store.async_load()
            if data and "retention_days" in data:
                self._retention_days = data["retention_days"]
            
            # Clean up old entries
            await self._async_cleanup_old_entries()
            _LOGGER.info(
                "Loaded history for %d areas (retention: %d days, storage: Database)",
                len(self._history),
                self._retention_days,
            )
        except Exception as e:
            _LOGGER.error("Failed to load from database: %s, falling back to JSON", e)
            self._storage_backend = HISTORY_STORAGE_JSON
            await self._async_load_from_json()

    async def async_save(self) -> None:
        """Save history to storage."""
        _LOGGER.debug("Saving history to %s storage", self._storage_backend)
        
        if self._storage_backend == HISTORY_STORAGE_DATABASE and self._db_table is not None:
            await self._async_save_to_database()
        else:
            await self._async_save_to_json()

    async def _async_save_to_json(self) -> None:
        """Save history to JSON storage."""
        data = {
            "history": self._history,
            "retention_days": self._retention_days,
            "storage_backend": self._storage_backend,
        }
        await self._store.async_save(data)

    async def _async_save_to_database(self) -> None:
        """Save history to database."""
        # Database records are inserted individually on async_record_temperature
        # Just save retention settings to JSON
        data = {
            "retention_days": self._retention_days,
            "storage_backend": self._storage_backend,
        }
        await self._store.async_save(data)

    async def async_unload(self) -> None:
        """Unload and cleanup."""
        if self._cleanup_unsub:
            self._cleanup_unsub()
            self._cleanup_unsub = None
        _LOGGER.debug("History tracker unloaded")

    async def _async_cleanup_old_entries(self) -> None:
        """Remove entries older than retention period."""
        if self._storage_backend == HISTORY_STORAGE_DATABASE and self._db_table is not None:
            await self._async_cleanup_database()
        else:
            await self._async_cleanup_json()

    async def _async_cleanup_json(self) -> None:
        """Clean up old entries in JSON storage."""
        cutoff = datetime.now() - timedelta(days=self._retention_days)
        cutoff_iso = cutoff.isoformat()

        total_removed = 0
        for area_id in list(self._history.keys()):
            original_count = len(self._history[area_id])
            self._history[area_id] = [
                entry
                for entry in self._history[area_id]
                if entry["timestamp"] > cutoff_iso
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
                "History cleanup: removed %d entries older than %d days (JSON)",
                total_removed,
                self._retention_days,
            )
            await self.async_save()

    async def _async_cleanup_database(self) -> None:
        """Clean up old entries in database storage."""
        try:
            recorder = get_instance(self.hass)
            cutoff = datetime.now() - timedelta(days=self._retention_days)
            
            def _cleanup():
                with recorder.engine.connect() as conn:
                    stmt = delete(self._db_table).where(
                        self._db_table.c.timestamp < cutoff
                    )
                    result = conn.execute(stmt)
                    conn.commit()
                    return result.rowcount
            
            removed = await recorder.async_add_executor_job(_cleanup)
            
            if removed > 0:
                _LOGGER.info(
                    "History cleanup: removed %d entries older than %d days (Database)",
                    removed,
                    self._retention_days,
                )
                # Reload in-memory cache
                await self._async_load_from_database()
                
        except Exception as e:
            _LOGGER.error("Failed to cleanup database: %s", e)

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
        timestamp = datetime.now()
        entry = {
            "timestamp": timestamp.isoformat(),
            "current_temperature": current_temp,
            "target_temperature": target_temp,
            "state": state,
        }

        # Always maintain in-memory cache
        if area_id not in self._history:
            self._history[area_id] = []

        self._history[area_id].append(entry)

        # Limit to last 1000 entries per area in memory
        if len(self._history[area_id]) > 1000:
            self._history[area_id] = self._history[area_id][-1000:]

        # Persist to storage backend
        if self._storage_backend == HISTORY_STORAGE_DATABASE and self._db_table is not None:
            await self._async_save_to_database_entry(area_id, timestamp, current_temp, target_temp, state)

        _LOGGER.debug(
            "Recorded temperature for %s: %.1f°C (target: %.1f°C, state: %s) [%s]",
            area_id,
            current_temp,
            target_temp,
            state,
            self._storage_backend,
        )

    async def _async_save_to_database_entry(
        self,
        area_id: str,
        timestamp: datetime,
        current_temp: float,
        target_temp: float,
        state: str,
    ) -> None:
        """Save a single entry to the database."""
        try:
            recorder = get_instance(self.hass)
            
            def _insert():
                with recorder.engine.connect() as conn:
                    stmt = self._db_table.insert().values(
                        area_id=area_id,
                        timestamp=timestamp,
                        current_temperature=current_temp,
                        target_temperature=target_temp,
                        state=state,
                    )
                    conn.execute(stmt)
                    conn.commit()
            
            await recorder.async_add_executor_job(_insert)
            
        except Exception as e:
            _LOGGER.error("Failed to save entry to database: %s", e)

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
            return [
                entry
                for entry in self._history[area_id]
                if entry["timestamp"] > cutoff_iso
            ]
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
        if days > MAX_HISTORY_RETENTION_DAYS:
            raise ValueError(f"Retention period cannot exceed {MAX_HISTORY_RETENTION_DAYS} days")

        old_retention = self._retention_days
        self._retention_days = days
        _LOGGER.info(
            "History retention changed from %d to %d days", old_retention, days
        )

    def get_retention_days(self) -> int:
        """Get the current retention period.

        Returns:
            Number of days history is retained
        """
        return self._retention_days

    def get_storage_backend(self) -> str:
        """Get the current storage backend.

        Returns:
            Current storage backend (json or database)
        """
        return self._storage_backend

    async def async_migrate_storage(self, target_backend: str) -> dict[str, Any]:
        """Migrate history data between storage backends.

        Args:
            target_backend: Target storage backend (json or database)

        Returns:
            Migration result with status and details
        """
        if target_backend == self._storage_backend:
            return {
                "success": False,
                "message": f"Already using {target_backend} storage",
                "migrated_entries": 0,
            }

        # Validate target backend
        if target_backend not in [HISTORY_STORAGE_JSON, HISTORY_STORAGE_DATABASE]:
            return {
                "success": False,
                "message": f"Invalid storage backend: {target_backend}",
                "migrated_entries": 0,
            }

        # Capture source backend BEFORE any changes
        source_backend = self._storage_backend

        # Check database support if migrating to database
        if target_backend == HISTORY_STORAGE_DATABASE:
            self._storage_backend = target_backend
            self._db_validated = False  # Reset validation flag
            await self._async_validate_database_support()
            
            if self._storage_backend != HISTORY_STORAGE_DATABASE:
                # Validation failed, backend was reset to JSON
                self._storage_backend = source_backend
                return {
                    "success": False,
                    "message": "Database storage not supported (SQLite or validation failed)",
                    "migrated_entries": 0,
                }

        _LOGGER.info(
            "Starting migration from %s to %s storage",
            source_backend,
            target_backend,
        )

        try:
            # Count total entries
            total_entries = sum(len(entries) for entries in self._history.values())

            # Perform migration
            if target_backend == HISTORY_STORAGE_DATABASE:
                await self._migrate_to_database()
            else:
                await self._migrate_to_json()

            # Update backend
            self._storage_backend = target_backend
            await self.async_save()

            _LOGGER.info(
                "Migration complete: %s → %s (%d entries)",
                source_backend,
                target_backend,
                total_entries,
            )

            return {
                "success": True,
                "message": f"Successfully migrated from {source_backend} to {target_backend}",
                "migrated_entries": total_entries,
                "source_backend": source_backend,
                "target_backend": target_backend,
            }

        except Exception as e:
            _LOGGER.error("Migration failed: %s", e)
            return {
                "success": False,
                "message": f"Migration failed: {str(e)}",
                "migrated_entries": 0,
            }

    async def _migrate_to_database(self) -> None:
        """Migrate all in-memory history to database."""
        if self._db_table is None:
            self._init_database_table()

        recorder = get_instance(self.hass)
        
        def _batch_insert():
            with recorder.engine.connect() as conn:
                for area_id, entries in self._history.items():
                    for entry in entries:
                        timestamp = datetime.fromisoformat(entry["timestamp"])
                        stmt = self._db_table.insert().values(
                            area_id=area_id,
                            timestamp=timestamp,
                            current_temperature=entry["current_temperature"],
                            target_temperature=entry["target_temperature"],
                            state=entry["state"],
                        )
                        conn.execute(stmt)
                conn.commit()
        
        await recorder.async_add_executor_job(_batch_insert)
        _LOGGER.info("Migrated all entries to database")

    async def _migrate_to_json(self) -> None:
        """Migrate all database history to JSON."""
        # History is already in memory, just save to JSON
        await self._async_save_to_json()
        _LOGGER.info("Migrated all entries to JSON")

    async def async_get_database_stats(self) -> dict[str, Any]:
        """Get database statistics.

        Returns:
            Dictionary with database statistics
        """
        if self._storage_backend != HISTORY_STORAGE_DATABASE or self._db_table is None:
            return {
                "enabled": False,
                "message": "Database storage not enabled",
            }

        try:
            recorder = get_instance(self.hass)
            
            def _get_stats():
                with recorder.engine.connect() as conn:
                    # Count total entries
                    stmt = select(self._db_table.c.id)
                    total = conn.execute(stmt).rowcount
                    
                    # Count by area
                    from sqlalchemy import func
                    stmt = select(
                        self._db_table.c.area_id,
                        func.count(self._db_table.c.id).label('count')
                    ).group_by(self._db_table.c.area_id)
                    area_counts = {row.area_id: row.count for row in conn.execute(stmt)}
                    
                    # Get oldest and newest timestamps
                    stmt = select(
                        func.min(self._db_table.c.timestamp).label('oldest'),
                        func.max(self._db_table.c.timestamp).label('newest')
                    )
                    result = conn.execute(stmt).first()
                    
                    return {
                        "total_entries": total,
                        "entries_by_area": area_counts,
                        "oldest_entry": result.oldest.isoformat() if result.oldest else None,
                        "newest_entry": result.newest.isoformat() if result.newest else None,
                    }
            
            stats = await recorder.async_add_executor_job(_get_stats)
            stats["enabled"] = True
            stats["table_name"] = DB_TABLE_NAME
            stats["backend"] = self._storage_backend
            
            return stats
            
        except Exception as e:
            _LOGGER.error("Failed to get database stats: %s", e)
            return {
                "enabled": True,
                "error": str(e),
            }
