"""Vacation Mode Manager for Smart Heating."""
import logging
import json
from datetime import datetime, date
from pathlib import Path
from typing import Any

from homeassistant.core import HomeAssistant
from homeassistant.helpers.event import async_track_state_change_event

_LOGGER = logging.getLogger(__name__)


class VacationManager:
    """Manage vacation mode for all areas."""
    
    def __init__(self, hass: HomeAssistant, storage_path: str) -> None:
        """Initialize vacation manager.
        
        Args:
            hass: Home Assistant instance
            storage_path: Path to store vacation mode data
        """
        self.hass = hass
        self._storage_file = Path(storage_path) / "vacation_mode.json"
        self._data = {
            "enabled": False,
            "start_date": None,
            "end_date": None,
            "preset_mode": "away",
            "frost_protection_override": True,
            "min_temperature": 10.0,
            "auto_disable": True,
            "person_entities": []  # List of person entities to watch
        }
        self._unsub_person_listeners = []
    
    async def async_load(self) -> None:
        """Load vacation mode data from storage."""
        if not self._storage_file.exists():
            await self.async_save()
            return
        
        try:
            # Use executor to avoid blocking
            def _read():
                with open(self._storage_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            
            data = await self.hass.async_add_executor_job(_read)
            self._data.update(data)
            
            # Check if vacation mode should auto-expire
            if self._data["enabled"]:
                await self._check_expiration()
            
            # Set up person entity listeners if auto-disable is enabled
            if self._data["enabled"] and self._data["auto_disable"]:
                await self._setup_person_listeners()
                
            _LOGGER.info("Loaded vacation mode data: %s", self._data)
        except Exception as err:
            _LOGGER.error("Failed to load vacation mode data: %s", err)
    
    async def async_save(self) -> None:
        """Save vacation mode data to storage."""
        try:
            # Ensure directory exists
            self._storage_file.parent.mkdir(parents=True, exist_ok=True)
            
            # Write to executor to avoid blocking
            def _write():
                with open(self._storage_file, 'w', encoding='utf-8') as f:
                    json.dump(self._data, f, indent=2)
            
            await self.hass.async_add_executor_job(_write)
            _LOGGER.debug("Saved vacation mode data")
        except Exception as err:
            _LOGGER.error("Failed to save vacation mode data: %s", err)
    
    async def _check_expiration(self) -> None:
        """Check if vacation mode has expired and disable if needed."""
        if not self._data["enabled"]:
            return
        
        if not self._data["end_date"]:
            return
        
        try:
            end_date = date.fromisoformat(self._data["end_date"])
            today = date.today()
            
            if today > end_date:
                _LOGGER.info("Vacation mode expired - disabling")
                await self.async_disable()
        except ValueError as err:
            _LOGGER.error("Invalid end_date format: %s", err)
    
    async def _setup_person_listeners(self) -> None:
        """Set up listeners for person entities to auto-disable when someone comes home."""
        # Clean up existing listeners
        for unsub in self._unsub_person_listeners:
            unsub()
        self._unsub_person_listeners.clear()
        
        if not self._data["person_entities"]:
            return
        
        async def person_state_changed(event):
            """Handle person state change."""
            new_state = event.data.get("new_state")
            old_state = event.data.get("old_state")
            
            if not new_state or not old_state:
                return
            
            # Check if person came home
            if old_state.state == "not_home" and new_state.state == "home":
                _LOGGER.info(
                    "Person %s came home - disabling vacation mode",
                    event.data.get("entity_id")
                )
                await self.async_disable()
        
        # Set up listener for each person entity
        for entity_id in self._data["person_entities"]:
            unsub = async_track_state_change_event(
                self.hass,
                [entity_id],
                person_state_changed
            )
            self._unsub_person_listeners.append(unsub)
        
        _LOGGER.debug("Set up %d person listeners", len(self._unsub_person_listeners))
    
    async def async_enable(
        self,
        start_date: str | None = None,
        end_date: str | None = None,
        preset_mode: str = "away",
        frost_protection_override: bool = True,
        min_temperature: float = 10.0,
        auto_disable: bool = True,
        person_entities: list[str] | None = None
    ) -> dict[str, Any]:
        """Enable vacation mode.
        
        Args:
            start_date: Start date (ISO format YYYY-MM-DD)
            end_date: End date (ISO format YYYY-MM-DD)
            preset_mode: Preset mode to use for all areas
            frost_protection_override: Enable frost protection override
            min_temperature: Minimum temperature for frost protection
            auto_disable: Auto-disable when person comes home
            person_entities: List of person entities to watch
            
        Returns:
            Updated vacation mode data
        """
        # Validate dates
        if start_date:
            try:
                date.fromisoformat(start_date)
            except ValueError:
                raise ValueError(f"Invalid start_date format: {start_date}")
        
        if end_date:
            try:
                date.fromisoformat(end_date)
            except ValueError:
                raise ValueError(f"Invalid end_date format: {end_date}")
        
        # Update data
        self._data.update({
            "enabled": True,
            "start_date": start_date or date.today().isoformat(),
            "end_date": end_date,
            "preset_mode": preset_mode,
            "frost_protection_override": frost_protection_override,
            "min_temperature": min_temperature,
            "auto_disable": auto_disable,
            "person_entities": person_entities or []
        })
        
        await self.async_save()
        
        # Set up person listeners if auto-disable is enabled
        if auto_disable and person_entities:
            await self._setup_person_listeners()
        
        _LOGGER.info("Vacation mode enabled: %s to %s", start_date, end_date)
        return self._data.copy()
    
    async def async_disable(self) -> dict[str, Any]:
        """Disable vacation mode.
        
        Returns:
            Updated vacation mode data
        """
        # Clean up person listeners
        for unsub in self._unsub_person_listeners:
            unsub()
        self._unsub_person_listeners.clear()
        
        self._data["enabled"] = False
        await self.async_save()
        
        _LOGGER.info("Vacation mode disabled")
        return self._data.copy()
    
    def is_active(self) -> bool:
        """Check if vacation mode is currently active.
        
        Returns:
            True if vacation mode is enabled and not expired
        """
        if not self._data["enabled"]:
            return False
        
        # Check if expired
        if self._data["end_date"]:
            try:
                end_date = date.fromisoformat(self._data["end_date"])
                if date.today() > end_date:
                    return False
            except ValueError:
                pass
        
        return True
    
    def get_preset_mode(self) -> str | None:
        """Get the preset mode for vacation mode.
        
        Returns:
            Preset mode if vacation mode is active, None otherwise
        """
        if self.is_active():
            return self._data["preset_mode"]
        return None
    
    def get_min_temperature(self) -> float | None:
        """Get minimum temperature override if frost protection is enabled.
        
        Returns:
            Minimum temperature if active and frost protection enabled, None otherwise
        """
        if self.is_active() and self._data["frost_protection_override"]:
            return self._data["min_temperature"]
        return None
    
    def get_data(self) -> dict[str, Any]:
        """Get current vacation mode data.
        
        Returns:
            Copy of vacation mode data
        """
        return self._data.copy()
