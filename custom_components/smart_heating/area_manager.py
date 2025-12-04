"""Zone Manager for Smart Heating integration."""
import logging
from typing import Any
from datetime import datetime, time

from homeassistant.core import HomeAssistant
from homeassistant.helpers.storage import Store

from .const import (
    ATTR_CURRENT_TEMPERATURE,
    ATTR_DEVICES,
    ATTR_ENABLED,
    ATTR_TARGET_TEMPERATURE,
    ATTR_AREA_ID,
    ATTR_AREA_NAME,
    DEVICE_TYPE_OPENTHERM_GATEWAY,
    DEVICE_TYPE_TEMPERATURE_SENSOR,
    DEVICE_TYPE_THERMOSTAT,
    DEVICE_TYPE_VALVE,
    STATE_HEATING,
    STATE_IDLE,
    STATE_OFF,
    STORAGE_KEY,
    STORAGE_VERSION,
)

_LOGGER = logging.getLogger(__name__)


class Schedule:
    """Representation of a temperature schedule."""

    def __init__(
        self,
        schedule_id: str,
        time: str,
        temperature: float,
        days: list[str] | None = None,
        enabled: bool = True,
    ) -> None:
        """Initialize a schedule.
        
        Args:
            schedule_id: Unique identifier
            time: Time in HH:MM format
            temperature: Target temperature
            days: Days of week (mon, tue, etc.) or None for all days
            enabled: Whether schedule is active
        """
        self.schedule_id = schedule_id
        self.time = time
        self.temperature = temperature
        self.days = days or ["mon", "tue", "wed", "thu", "fri", "sat", "sun"]
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
        
        # Check day of week
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
        return {
            "id": self.schedule_id,
            "time": self.time,
            "temperature": self.temperature,
            "days": self.days,
            "enabled": self.enabled,
        }
    
    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "Schedule":
        """Create from dictionary."""
        return cls(
            schedule_id=data["id"],
            time=data["time"],
            temperature=data["temperature"],
            days=data.get("days"),
            enabled=data.get("enabled", True),
        )


class Area:
    """Representation of a heating area."""

    def __init__(
        self,
        area_id: str,
        name: str,
        target_temperature: float = 20.0,
        enabled: bool = True,
    ) -> None:
        """Initialize a area.
        
        Args:
            area_id: Unique identifier for the area
            name: Display name of the area
            target_temperature: Target temperature for the area
            enabled: Whether the area is enabled
        """
        self.area_id = area_id
        self.name = name
        self.target_temperature = target_temperature
        self.enabled = enabled
        self.devices: dict[str, dict[str, Any]] = {}
        self.schedules: dict[str, Schedule] = {}
        self._current_temperature: float | None = None
        self.night_boost_enabled: bool = True
        self.night_boost_offset: float = 0.5  # Add 0.5°C during night hours

    def add_device(self, device_id: str, device_type: str, mqtt_topic: str | None = None) -> None:
        """Add a device to the area.
        
        Args:
            device_id: Unique identifier for the device
            device_type: Type of device (thermostat, temperature_sensor, etc.)
            mqtt_topic: MQTT topic for the device (optional)
        """
        self.devices[device_id] = {
            "type": device_type,
            "mqtt_topic": mqtt_topic,
            "entity_id": None,
        }
        _LOGGER.debug("Added device %s (type: %s) to area %s", device_id, device_type, self.area_id)

    def remove_device(self, device_id: str) -> None:
        """Remove a device from the area.
        
        Args:
            device_id: Unique identifier for the device
        """
        if device_id in self.devices:
            del self.devices[device_id]
            _LOGGER.debug("Removed device %s from area %s", device_id, self.area_id)

    def get_temperature_sensors(self) -> list[str]:
        """Get all temperature sensor device IDs in the area.
        
        Returns:
            List of temperature sensor device IDs
        """
        return [
            device_id
            for device_id, device in self.devices.items()
            if device["type"] == DEVICE_TYPE_TEMPERATURE_SENSOR
        ]

    def get_thermostats(self) -> list[str]:
        """Get all thermostat device IDs in the area.
        
        Returns:
            List of thermostat device IDs
        """
        return [
            device_id
            for device_id, device in self.devices.items()
            if device["type"] == DEVICE_TYPE_THERMOSTAT
        ]

    def get_opentherm_gateways(self) -> list[str]:
        """Get all OpenTherm gateway device IDs in the area.
        
        Returns:
            List of OpenTherm gateway device IDs
        """
        return [
            device_id
            for device_id, device in self.devices.items()
            if device["type"] == DEVICE_TYPE_OPENTHERM_GATEWAY
        ]

    def add_schedule(self, schedule: Schedule) -> None:
        """Add a schedule to the area.
        
        Args:
            schedule: Schedule instance
        """
        self.schedules[schedule.schedule_id] = schedule
        _LOGGER.debug("Added schedule %s to area %s", schedule.schedule_id, self.area_id)

    def remove_schedule(self, schedule_id: str) -> None:
        """Remove a schedule from the area.
        
        Args:
            schedule_id: Schedule identifier
        """
        if schedule_id in self.schedules:
            del self.schedules[schedule_id]
            _LOGGER.debug("Removed schedule %s from area %s", schedule_id, self.area_id)

    def get_active_schedule_temperature(self, current_time: datetime | None = None) -> float | None:
        """Get the temperature from the currently active schedule.
        
        Args:
            current_time: Current time (defaults to now)
            
        Returns:
            Temperature from active schedule or None
        """
        if current_time is None:
            current_time = datetime.now()
        
        # Find all active schedules and get the latest one
        active_schedules = [
            s for s in self.schedules.values()
            if s.is_active(current_time)
        ]
        
        if not active_schedules:
            return None
        
        # Sort by time and get the latest
        active_schedules.sort(key=lambda s: s.time, reverse=True)
        return active_schedules[0].temperature

    def get_effective_target_temperature(self, current_time: datetime | None = None) -> float:
        """Get the effective target temperature considering schedules and night boost.
        
        Args:
            current_time: Current time (defaults to now)
            
        Returns:
            Effective target temperature
        """
        if current_time is None:
            current_time = datetime.now()
        
        # Start with schedule temperature if available
        target = self.get_active_schedule_temperature(current_time)
        if target is None:
            target = self.target_temperature
        
        # Apply night boost if enabled (22:00 - 06:00)
        if self.night_boost_enabled:
            current_hour = current_time.hour
            if current_hour >= 22 or current_hour < 6:
                target += self.night_boost_offset
                _LOGGER.debug(
                    "Night boost active for area %s: %.1f°C + %.1f°C = %.1f°C",
                    self.area_id, target - self.night_boost_offset, 
                    self.night_boost_offset, target
                )
        
        return target

    @property
    def current_temperature(self) -> float | None:
        """Get the current temperature of the area.
        
        Returns:
            Current temperature or None
        """
        return self._current_temperature

    @current_temperature.setter
    def current_temperature(self, value: float | None) -> None:
        """Set the current temperature of the area.
        
        Args:
            value: New temperature value
        """
        self._current_temperature = value

    @property
    def state(self) -> str:
        """Get the current state of the area.
        
        Returns:
            Current state (heating, idle, off)
        """
        if not self.enabled:
            return STATE_OFF
        
        if self._current_temperature is not None and self.target_temperature is not None:
            if self._current_temperature < self.target_temperature - 0.5:
                return STATE_HEATING
        
        return STATE_IDLE

    def to_dict(self) -> dict[str, Any]:
        """Convert area to dictionary for storage.
        
        Returns:
            Dictionary representation of the area
        """
        return {
            ATTR_AREA_ID: self.area_id,
            ATTR_AREA_NAME: self.name,
            ATTR_TARGET_TEMPERATURE: self.target_temperature,
            ATTR_ENABLED: self.enabled,
            ATTR_DEVICES: self.devices,
            "schedules": [s.to_dict() for s in self.schedules.values()],
            "night_boost_enabled": self.night_boost_enabled,
            "night_boost_offset": self.night_boost_offset,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "Area":
        """Create a area from dictionary.
        
        Args:
            data: Dictionary with area data
            
        Returns:
            Zone instance
        """
        area = cls(
            area_id=data[ATTR_AREA_ID],
            name=data[ATTR_AREA_NAME],
            target_temperature=data.get(ATTR_TARGET_TEMPERATURE, 20.0),
            enabled=data.get(ATTR_ENABLED, True),
        )
        area.devices = data.get(ATTR_DEVICES, {})
        area.night_boost_enabled = data.get("night_boost_enabled", True)
        area.night_boost_offset = data.get("night_boost_offset", 0.5)
        
        # Load schedules
        for schedule_data in data.get("schedules", []):
            schedule = Schedule.from_dict(schedule_data)
            area.schedules[schedule.schedule_id] = schedule
        
        return area


class AreaManager:
    """Manage heating areas."""

    def __init__(self, hass: HomeAssistant) -> None:
        """Initialize the area manager.
        
        Args:
            hass: Home Assistant instance
        """
        self.hass = hass
        self.areas: dict[str, Area] = {}
        self._store = Store(hass, STORAGE_VERSION, STORAGE_KEY)
        _LOGGER.debug("AreaManager initialized")

    async def async_load(self) -> None:
        """Load areas from storage."""
        _LOGGER.debug("Loading areas from storage")
        data = await self._store.async_load()
        
        if data is not None and "areas" in data:
            for area_data in data["areas"]:
                area = Area.from_dict(area_data)
                self.areas[area.area_id] = area
            _LOGGER.info("Loaded %d areas from storage", len(self.areas))
        else:
            _LOGGER.debug("No areas found in storage")

    async def async_save(self) -> None:
        """Save areas to storage."""
        _LOGGER.debug("Saving areas to storage")
        data = {
            "areas": [area.to_dict() for area in self.areas.values()]
        }
        await self._store.async_save(data)
        _LOGGER.info("Saved %d areas to storage", len(self.areas))

    def get_area(self, area_id: str) -> Area | None:
        """Get a area by ID.
        
        Args:
            area_id: Zone identifier
            
        Returns:
            Zone or None if not found
        """
        return self.areas.get(area_id)

    def get_all_areas(self) -> dict[str, Area]:
        """Get all areas.
        
        Returns:
            Dictionary of all areas
        """
        return self.areas

    def add_device_to_area(
        self,
        area_id: str,
        device_id: str,
        device_type: str,
        mqtt_topic: str | None = None,
    ) -> None:
        """Add a device to a area.
        
        Args:
            area_id: Zone identifier
            device_id: Device identifier
            device_type: Type of device
            mqtt_topic: MQTT topic for the device
            
        Raises:
            ValueError: If area does not exist
        """
        area = self.get_area(area_id)
        if area is None:
            raise ValueError(f"Area {area_id} does not exist")
        
        area.add_device(device_id, device_type, mqtt_topic)

    def remove_device_from_area(self, area_id: str, device_id: str) -> None:
        """Remove a device from a area.
        
        Args:
            area_id: Zone identifier
            device_id: Device identifier
            
        Raises:
            ValueError: If area does not exist
        """
        area = self.get_area(area_id)
        if area is None:
            raise ValueError(f"Area {area_id} does not exist")
        
        area.remove_device(device_id)

    def update_area_temperature(self, area_id: str, temperature: float) -> None:
        """Update the current temperature of a area.
        
        Args:
            area_id: Zone identifier
            temperature: New temperature value
            
        Raises:
            ValueError: If area does not exist
        """
        area = self.get_area(area_id)
        if area is None:
            raise ValueError(f"Area {area_id} does not exist")
        
        area.current_temperature = temperature
        _LOGGER.debug("Updated area %s temperature to %.1f°C", area_id, temperature)

    def set_area_target_temperature(self, area_id: str, temperature: float) -> None:
        """Set the target temperature of a area.
        
        Args:
            area_id: Zone identifier
            temperature: Target temperature
            
        Raises:
            ValueError: If area does not exist
        """
        area = self.get_area(area_id)
        if area is None:
            raise ValueError(f"Area {area_id} does not exist")
        
        area.target_temperature = temperature
        _LOGGER.info("Set area %s target temperature to %.1f°C", area_id, temperature)

    def enable_area(self, area_id: str) -> None:
        """Enable a area.
        
        Args:
            area_id: Zone identifier
            
        Raises:
            ValueError: If area does not exist
        """
        area = self.get_area(area_id)
        if area is None:
            raise ValueError(f"Area {area_id} does not exist")
        
        area.enabled = True
        _LOGGER.info("Enabled area %s", area_id)

    def disable_area(self, area_id: str) -> None:
        """Disable a area.
        
        Args:
            area_id: Zone identifier
            
        Raises:
            ValueError: If area does not exist
        """
        area = self.get_area(area_id)
        if area is None:
            raise ValueError(f"Area {area_id} does not exist")
        
        area.enabled = False
        _LOGGER.info("Disabled area %s", area_id)

    def add_schedule_to_area(
        self, 
        area_id: str, 
        schedule_id: str,
        time: str,
        temperature: float,
        days: list[str] | None = None,
    ) -> Schedule:
        """Add a schedule to an area.
        
        Args:
            area_id: Area identifier
            schedule_id: Unique schedule identifier
            time: Time in HH:MM format
            temperature: Target temperature
            days: Days of week or None for all days
            
        Returns:
            Created schedule
            
        Raises:
            ValueError: If area does not exist
        """
        area = self.get_area(area_id)
        if area is None:
            raise ValueError(f"Area {area_id} does not exist")
        
        schedule = Schedule(schedule_id, time, temperature, days)
        area.add_schedule(schedule)
        _LOGGER.info("Added schedule %s to area %s", schedule_id, area_id)
        return schedule

    def remove_schedule_from_area(self, area_id: str, schedule_id: str) -> None:
        """Remove a schedule from an area.
        
        Args:
            area_id: Area identifier
            schedule_id: Schedule identifier
            
        Raises:
            ValueError: If area does not exist
        """
        area = self.get_area(area_id)
        if area is None:
            raise ValueError(f"Area {area_id} does not exist")
        
        area.remove_schedule(schedule_id)
        _LOGGER.info("Removed schedule %s from area %s", schedule_id, area_id)
        _LOGGER.info("Disabled area %s", area_id)
