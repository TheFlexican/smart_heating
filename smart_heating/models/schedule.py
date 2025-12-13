"""Schedule model for Smart Heating integration."""

import logging
from datetime import datetime
from typing import Any

_LOGGER = logging.getLogger(__name__)


class Schedule:
    """Representation of a temperature schedule."""

    def __init__(
        self,
        schedule_id: str,
        time: str = "",
        temperature: float | None = None,
        days: list[int] | None = None,
        enabled: bool = True,
        day: int | None = None,
        start_time: str | None = None,
        end_time: str | None = None,
        preset_mode: str | None = None,
        date: str | None = None,
    ) -> None:
        """Initialize a schedule.

        Args:
            schedule_id: Unique identifier
            time: Time in HH:MM format (legacy)
            temperature: Target temperature (optional if preset_mode is used)
            days: Days of week (mon, tue, etc.) or None for all days (legacy)
            enabled: Whether schedule is active
            day: Day name (Monday, Tuesday, etc.) - new format (single day, legacy)
            start_time: Start time in HH:MM format - new format
            end_time: End time in HH:MM format - new format
            preset_mode: Preset mode name (away, eco, comfort, home, sleep, activity)
            date: Specific date for one-time schedules (YYYY-MM-DD format)
        """
        self.schedule_id = schedule_id
        # Support both old and new formats
        self.time = start_time or time
        self.start_time = start_time or time
        self.end_time = end_time or "23:59"  # Default end time
        self.temperature = temperature
        self.preset_mode = preset_mode
        self.date = date  # Specific date for one-time schedules

        # Use numeric indices internally: 0=Monday .. 6=Sunday

        # If date is specified, this is a date-specific schedule (not recurring weekly)
        if date:
            self.day = None
            self.days = None
        elif day is not None:
            # Normalize localized day to English full name if possible
            if isinstance(day, int):
                normalized_day = int(day % 7)
            elif isinstance(day, str):
                day_key = day.strip().lower()
                short_codes = {"mon", "tue", "wed", "thu", "fri", "sat", "sun"}
                if day_key in short_codes:
                    short_to_index = {
                        "mon": 0,
                        "tue": 1,
                        "wed": 2,
                        "thu": 3,
                        "fri": 4,
                        "sat": 5,
                        "sun": 6,
                    }
                    normalized_day = short_to_index[day_key]
                else:
                    raise ValueError(
                        "Invalid 'day' string format: use numeric index (0=Monday) or short code 'mon'"
                    )
            else:
                normalized_day = day
            self.day = int(normalized_day)
            self.days = [int(normalized_day)]
        elif days:
            # Accept days as list of short codes ("mon") or numeric indices (0=Monday)
            def normalize_day_item(d):
                if isinstance(d, int):
                    return int(d % 7)
                if isinstance(d, str):
                    key = d.strip().lower()
                    if key in {"mon", "tue", "wed", "thu", "fri", "sat", "sun"}:
                        short_to_index = {
                            "mon": 0,
                            "tue": 1,
                            "wed": 2,
                            "thu": 3,
                            "fri": 4,
                            "sat": 5,
                            "sun": 6,
                        }
                        return short_to_index.get(key)
                    # Reject full English or localized day names to enforce indices/short codes
                    raise ValueError(
                        "Invalid 'days' string format: use numeric indices (0=Monday) or short codes (mon)"
                    )
                return d

            self.days = [normalize_day_item(x) for x in days]
            # Use first day for display (as index)
            self.day = int(self.days[0]) if self.days else 0
        else:
            self.days = [0, 1, 2, 3, 4, 5, 6]
            self.day = 0

        self.enabled = enabled

    def is_active(self, current_time: datetime) -> bool:
        """Check if schedule is active at given time.

        Args:
            current_time: Current datetime

        Returns:
            True if schedule should be active
        """
        if not self.enabled:
            return False

        # Check if this is a date-specific schedule
        if self.date:
            current_date_str = current_time.strftime("%Y-%m-%d")
            if current_date_str != self.date:
                return False
            # Date matches, check time range
            schedule_start = datetime.strptime(self.start_time, "%H:%M").time()
            schedule_end = datetime.strptime(self.end_time, "%H:%M").time()
            current_time_only = current_time.time()
            return schedule_start <= current_time_only < schedule_end

        # Otherwise, check day of week for recurring schedules
        if not self.days:
            return False

        current_day_idx = current_time.weekday()
        if current_day_idx not in self.days:
            return False

        # Check time (within 30 minutes)
        schedule_time = datetime.strptime(self.time, "%H:%M").time()
        current_time_only = current_time.time()

        # Simple time comparison - schedule is active from its time until next schedule
        return current_time_only >= schedule_time

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        result = {
            "id": self.schedule_id,
            "start_time": self.start_time,
            "end_time": self.end_time,
            "enabled": self.enabled,
        }

        # Add date for date-specific schedules
        if self.date:
            result["date"] = self.date
        # Add days for recurring weekly schedules
        elif self.days:
            # Already stored as indices
            result["days"] = [int(d) for d in self.days]
            if self.day is not None:
                result["day"] = int(self.day)

        if self.temperature is not None:
            result["temperature"] = self.temperature
        if self.preset_mode is not None:
            result["preset_mode"] = self.preset_mode
        return result

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "Schedule":
        """Create from dictionary."""
        # Convert frontend days format to internal format if needed
        days_data = data.get("days")
        if days_data and isinstance(days_data, list) and days_data:
            # Filter out None before mapping
            days_data = [d for d in days_data if d is not None]

            # Expect numeric day indices (0=Monday) or short 3-letter codes (mon, tue, ...)
            def map_day_any_to_index(d: Any) -> int:
                if isinstance(d, int):
                    return int(d % 7)
                if not isinstance(d, str):
                    raise ValueError(
                        "Invalid 'days' entry: must be integer index or short code"
                    )
                key = d.strip().lower()
                short_to_idx = {
                    "mon": 0,
                    "tue": 1,
                    "wed": 2,
                    "thu": 3,
                    "fri": 4,
                    "sat": 5,
                    "sun": 6,
                }
                if key in short_to_idx:
                    return short_to_idx[key]
                raise ValueError(
                    "Invalid 'days' string format: use numeric indices (0=Monday) or short codes (mon)"
                )

            days_data = [map_day_any_to_index(d) for d in days_data]

        # Filter out None values to match type hint list[str] | None
        filtered_days = (
            [int(d) for d in days_data if d is not None] if days_data else None
        )

        # Normalize input 'day' to index if provided as string short code
        day_val = data.get("day")
        if isinstance(day_val, str):
            short_to_idx = {
                "mon": 0,
                "tue": 1,
                "wed": 2,
                "thu": 3,
                "fri": 4,
                "sat": 5,
                "sun": 6,
            }
            key = day_val.strip().lower()
            day_val = short_to_idx.get(key)

        return cls(
            schedule_id=data["id"],
            time=data.get("time", ""),
            temperature=data.get("temperature"),
            days=filtered_days,
            enabled=data.get("enabled", True),
            day=day_val,
            start_time=data.get("start_time"),
            end_time=data.get("end_time"),
            preset_mode=data.get("preset_mode"),
            date=data.get("date"),
        )
