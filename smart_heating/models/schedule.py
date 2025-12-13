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
        days: list[str] | None = None,
        enabled: bool = True,
        day: str | None = None,
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

        # Convert between day formats
        # Map day names to short codes; accept localized names (English/Dutch) and short names
        day_map = {
            "Monday": "mon",
            "Tuesday": "tue",
            "Wednesday": "wed",
            "Thursday": "thu",
            "Friday": "fri",
            "Saturday": "sat",
            "Sunday": "sun",
        }
        # Only support numeric indices (0=Monday) or short codes (mon, tue, ...).
        reverse_day_map = {v: k for k, v in day_map.items()}

        # If date is specified, this is a date-specific schedule (not recurring weekly)
        if date:
            self.day = None
            self.days = None
        elif day is not None:
            # Normalize localized day to English full name if possible
            if isinstance(day, int):
                index_map_full = {0: "Monday", 1: "Tuesday", 2: "Wednesday", 3: "Thursday", 4: "Friday", 5: "Saturday", 6: "Sunday"}
                normalized_day = index_map_full.get(day % 7, day)
            elif isinstance(day, str):
                day_key = day.strip().lower()
                short_codes = {"mon", "tue", "wed", "thu", "fri", "sat", "sun"}
                if day_key in short_codes:
                    normalized_day = reverse_day_map.get(day_key, "Monday")
                else:
                    raise ValueError(
                        "Invalid 'day' string format: use numeric index (0=Monday) or short code 'mon'"
                    )
            else:
                normalized_day = day
            self.day = normalized_day
            # Map normalized full name to short day code where possible
            self.days = [day_map.get(self.day, "mon")]
        elif days:
            # Accept days as list of short codes ("mon") or numeric indices (0=Monday)
            def normalize_day_item(d):
                if isinstance(d, int):
                    idx_map = {0: "mon", 1: "tue", 2: "wed", 3: "thu", 4: "fri", 5: "sat", 6: "sun"}
                    return idx_map.get(d % 7, d)
                if isinstance(d, str):
                    key = d.strip().lower()
                    if key in {"mon", "tue", "wed", "thu", "fri", "sat", "sun"}:
                        return key
                    # Reject full English or localized day names to enforce indices/short codes
                    raise ValueError(
                        "Invalid 'days' string format: use numeric indices (0=Monday) or short codes (mon)"
                    )
                return d

            self.days = [normalize_day_item(x) for x in days]
            # Use first day for display
            self.day = reverse_day_map.get(days[0], "Monday") if days else "Monday"
        else:
            self.days = ["mon", "tue", "wed", "thu", "fri", "sat", "sun"]
            self.day = "Monday"

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

        day_names = ["mon", "tue", "wed", "thu", "fri", "sat", "sun"]
        current_day = day_names[current_time.weekday()]
        if current_day not in self.days:
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
            # Convert internal short codes to numeric indices for frontend
            short_to_index = {"mon": 0, "tue": 1, "wed": 2, "thu": 3, "fri": 4, "sat": 5, "sun": 6}
            result["days"] = [short_to_index.get(d, d) for d in self.days]
            # Keep single day for backwards compatibility
            if self.day is not None:
                # Provide single day as index if possible
                full_to_index = {"Monday": 0, "Tuesday": 1, "Wednesday": 2, "Thursday": 3, "Friday": 4, "Saturday": 5, "Sunday": 6}
                if isinstance(self.day, str) and self.day in full_to_index:
                    result["day"] = full_to_index[self.day]
                else:
                    result["day"] = self.day

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
            # Expect numeric day indices (0=Monday) or short 3-letter codes (mon, tue, ...)
            day_map = {"mon": "mon", "tue": "tue", "wed": "wed", "thu": "thu", "fri": "fri", "sat": "sat", "sun": "sun"}

            def map_day_any(d: Any) -> str:
                # Accept integers as day indices
                if isinstance(d, int):
                    idx_map = {0: "mon", 1: "tue", 2: "wed", 3: "thu", 4: "fri", 5: "sat", 6: "sun"}
                    return idx_map.get(d % 7, str(d))
                if not isinstance(d, str):
                    return d
                key = d.strip().lower()
                return day_map.get(key, d)

            days_data = [map_day_any(d) for d in days_data]

        # Filter out None values to match type hint list[str] | None
        filtered_days = [d for d in days_data if d is not None] if days_data else None

        return cls(
            schedule_id=data["id"],
            time=data.get("time", ""),
            temperature=data.get("temperature"),
            days=filtered_days,
            enabled=data.get("enabled", True),
            day=data.get("day"),
            start_time=data.get("start_time"),
            end_time=data.get("end_time"),
            preset_mode=data.get("preset_mode"),
            date=data.get("date"),
        )
