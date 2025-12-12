"""User Profile Manager for Multi-User Presence Tracking."""

import json
import logging
from pathlib import Path
from typing import Any

from homeassistant.core import HomeAssistant
from homeassistant.helpers.event import async_track_state_change_event

_LOGGER = logging.getLogger(__name__)


class UserManager:
    """Manage user profiles and multi-user presence tracking."""

    def __init__(self, hass: HomeAssistant, storage_path: str) -> None:
        """Initialize user manager.

        Args:
            hass: Home Assistant instance
            storage_path: Path to store user profile data
        """
        self.hass = hass
        self._storage_file = Path(storage_path) / "user_profiles.json"
        self._data = {
            "users": {},
            "presence_state": {
                "users_home": [],
                "active_user": None,
                "combined_mode": "none",  # "single", "multiple", "none"
            },
            "settings": {
                "multi_user_strategy": "priority",  # "priority" or "average"
                "enabled": True,
            },
        }
        self._unsub_person_listeners = []

    async def async_load(self) -> None:
        """Load user profile data from storage."""
        if not self._storage_file.exists():
            await self.async_save()
            return

        try:
            # Use executor to avoid blocking
            def _read():
                with open(self._storage_file, "r", encoding="utf-8") as f:
                    return json.load(f)

            data = await self.hass.async_add_executor_job(_read)
            self._data.update(data)
            _LOGGER.info("Loaded user profiles from %s", self._storage_file)

            # Start tracking person entities
            await self._setup_person_listeners()

        except Exception as e:
            _LOGGER.error("Failed to load user profiles: %s", e)

    async def async_save(self) -> None:
        """Save user profile data to storage."""
        try:
            # Ensure directory exists
            self._storage_file.parent.mkdir(parents=True, exist_ok=True)

            # Use executor to avoid blocking
            def _write():
                with open(self._storage_file, "w", encoding="utf-8") as f:
                    json.dump(self._data, f, indent=2)

            await self.hass.async_add_executor_job(_write)
            _LOGGER.debug("Saved user profiles to %s", self._storage_file)

        except Exception as e:
            _LOGGER.error("Failed to save user profiles: %s", e)

    async def _setup_person_listeners(self) -> None:
        """Set up listeners for person entity state changes."""
        # Remove existing listeners
        for unsub in self._unsub_person_listeners:
            unsub()
        self._unsub_person_listeners.clear()

        # Get all person entity IDs from user profiles
        person_entities = set()
        for user_data in self._data["users"].values():
            if user_data.get("user_id"):
                person_entities.add(user_data["user_id"])

        if not person_entities:
            _LOGGER.debug("No person entities to track")
            return

        # Track each person entity
        for entity_id in person_entities:
            unsub = async_track_state_change_event(
                self.hass, [entity_id], self._person_state_changed
            )
            self._unsub_person_listeners.append(unsub)

        _LOGGER.info("Tracking %d person entities", len(person_entities))

        # Initial presence update
        await self._update_presence_state()

    async def _person_state_changed(self, event) -> None:
        """Handle person entity state change."""
        entity_id = event.data.get("entity_id")
        old_state = event.data.get("old_state")
        new_state = event.data.get("new_state")

        if not new_state:
            return

        _LOGGER.debug(
            "Person %s changed from %s to %s",
            entity_id,
            old_state.state if old_state else "unknown",
            new_state.state,
        )

        await self._update_presence_state()

        # Fire custom event for WebSocket
        self.hass.bus.async_fire(
            "smart_heating_user_presence_changed",
            {
                "entity_id": entity_id,
                "old_state": old_state.state if old_state else None,
                "new_state": new_state.state,
                "users_home": self._data["presence_state"]["users_home"],
                "active_user": self._data["presence_state"]["active_user"],
            },
        )

    async def _update_presence_state(self) -> None:
        """Update presence state based on current person entity states."""
        users_home = []

        for user_id, user_data in self._data["users"].items():
            person_entity = user_data.get("user_id")
            if not person_entity:
                continue

            state = self.hass.states.get(person_entity)
            if state and state.state == "home":
                users_home.append(user_id)

        # Update presence state
        self._data["presence_state"]["users_home"] = users_home

        if len(users_home) == 0:
            self._data["presence_state"]["combined_mode"] = "none"
            self._data["presence_state"]["active_user"] = None
        elif len(users_home) == 1:
            self._data["presence_state"]["combined_mode"] = "single"
            self._data["presence_state"]["active_user"] = users_home[0]
        else:
            self._data["presence_state"]["combined_mode"] = "multiple"
            # Select highest priority user
            highest_priority_user = self._get_highest_priority_user(users_home)
            self._data["presence_state"]["active_user"] = highest_priority_user

        await self.async_save()

    def _get_highest_priority_user(self, user_ids: list[str]) -> str | None:
        """Get the highest priority user from a list of user IDs.

        Args:
            user_ids: List of user IDs to compare

        Returns:
            User ID with highest priority, or None if no users
        """
        if not user_ids:
            return None

        highest_priority = -1
        highest_user = None

        for user_id in user_ids:
            user_data = self._data["users"].get(user_id)
            if not user_data:
                continue

            priority = user_data.get("priority", 5)
            if priority > highest_priority:
                highest_priority = priority
                highest_user = user_id

        return highest_user

    async def create_user_profile(
        self,
        user_id: str,
        name: str,
        person_entity: str,
        preset_preferences: dict[str, float] | None = None,
        priority: int = 5,
        areas: list[str] | None = None,
    ) -> dict[str, Any]:
        """Create a new user profile.

        Args:
            user_id: Unique user ID
            name: User's display name
            person_entity: Home Assistant person entity ID
            preset_preferences: Temperature preferences per preset
            priority: User priority (1-10, higher = more important)
            areas: List of area IDs this user cares about (empty = all)

        Returns:
            Created user profile data

        Raises:
            ValueError: If user_id already exists or invalid data
        """
        if user_id in self._data["users"]:
            raise ValueError(f"User {user_id} already exists")

        if priority < 1 or priority > 10:
            raise ValueError("Priority must be between 1 and 10")

        # Verify person entity exists
        if not self.hass.states.get(person_entity):
            _LOGGER.warning("Person entity %s not found", person_entity)

        user_data = {
            "user_id": person_entity,
            "name": name,
            "preset_preferences": preset_preferences or {},
            "priority": priority,
            "areas": areas or [],
        }

        self._data["users"][user_id] = user_data
        await self.async_save()

        # Re-setup person listeners
        await self._setup_person_listeners()

        _LOGGER.info("Created user profile: %s", user_id)
        return user_data

    async def update_user_profile(
        self, user_id: str, updates: dict[str, Any]
    ) -> dict[str, Any]:
        """Update an existing user profile.

        Args:
            user_id: User ID to update
            updates: Dictionary of fields to update

        Returns:
            Updated user profile data

        Raises:
            ValueError: If user_id doesn't exist
        """
        if user_id not in self._data["users"]:
            raise ValueError(f"User {user_id} not found")

        user_data = self._data["users"][user_id]

        # Update allowed fields
        for key in ["name", "preset_preferences", "priority", "areas"]:
            if key in updates:
                user_data[key] = updates[key]

        # If person entity changed, re-setup listeners
        if "user_id" in updates:
            user_data["user_id"] = updates["user_id"]
            await self._setup_person_listeners()

        await self.async_save()
        await self._update_presence_state()

        _LOGGER.info("Updated user profile: %s", user_id)
        return user_data

    async def delete_user_profile(self, user_id: str) -> None:
        """Delete a user profile.

        Args:
            user_id: User ID to delete

        Raises:
            ValueError: If user_id doesn't exist
        """
        if user_id not in self._data["users"]:
            raise ValueError(f"User {user_id} not found")

        del self._data["users"][user_id]
        await self.async_save()

        # Re-setup person listeners
        await self._setup_person_listeners()
        await self._update_presence_state()

        _LOGGER.info("Deleted user profile: %s", user_id)

    def get_user_profile(self, user_id: str) -> dict[str, Any] | None:
        """Get a user profile by ID.

        Args:
            user_id: User ID to retrieve

        Returns:
            User profile data or None if not found
        """
        return self._data["users"].get(user_id)

    def get_all_users(self) -> dict[str, Any]:
        """Get all user profiles.

        Returns:
            Dictionary of all user profiles
        """
        return self._data["users"].copy()

    def get_presence_state(self) -> dict[str, Any]:
        """Get current presence state.

        Returns:
            Current presence state including users home and active user
        """
        return self._data["presence_state"].copy()

    def get_settings(self) -> dict[str, Any]:
        """Get multi-user settings.

        Returns:
            Multi-user settings
        """
        return self._data["settings"].copy()

    async def update_settings(self, settings: dict[str, Any]) -> dict[str, Any]:
        """Update multi-user settings.

        Args:
            settings: Settings to update

        Returns:
            Updated settings
        """
        self._data["settings"].update(settings)
        await self.async_save()
        _LOGGER.info("Updated multi-user settings: %s", settings)
        return self._data["settings"].copy()

    def get_active_user_preferences(
        self, area_id: str | None = None
    ) -> dict[str, float] | None:
        """Get temperature preferences for the currently active user.

        Args:
            area_id: Optional area ID to filter by user's areas

        Returns:
            Active user's preset preferences, or None if no user home
        """
        if not self._data["settings"]["enabled"]:
            return None

        active_user_id = self._data["presence_state"].get("active_user")
        if not active_user_id:
            return None

        user_data = self._data["users"].get(active_user_id)
        if not user_data:
            return None

        # Check if user cares about this area
        if area_id and user_data.get("areas"):
            if area_id not in user_data["areas"]:
                return None

        return user_data.get("preset_preferences", {})

    def get_combined_preferences(
        self, area_id: str | None = None
    ) -> dict[str, float] | None:
        """Get combined temperature preferences when multiple users are home.

        Uses the configured strategy (priority or average).

        Args:
            area_id: Optional area ID to filter by user's areas

        Returns:
            Combined preset preferences, or None if no users home
        """
        if not self._data["settings"]["enabled"]:
            return None

        users_home = self._data["presence_state"]["users_home"]
        if not users_home:
            return None

        strategy = self._data["settings"]["multi_user_strategy"]

        if strategy == "priority" or len(users_home) == 1:
            # Use highest priority user
            return self.get_active_user_preferences(area_id)

        # Average strategy - collect relevant user IDs
        filtered_users = self._get_users_for_area(users_home, area_id)
        if not filtered_users:
            return None

        return self._average_user_preferences(filtered_users)

    def _get_users_for_area(
        self, user_ids: list[str], area_id: str | None
    ) -> list[str]:
        """Filter users that are relevant for given area (if area_id provided)."""
        users = []
        for user_id in user_ids:
            user_data = self._data["users"].get(user_id)
            if not user_data:
                continue
            if area_id and user_data.get("areas") and area_id not in user_data["areas"]:
                continue
            users.append(user_id)
        return users

    def _average_user_preferences(self, user_ids: list[str]) -> dict[str, float] | None:
        """Average preferences for the provided user IDs."""
        if not user_ids:
            return None
        all_preferences = {}
        for user_id in user_ids:
            user_data = self._data["users"].get(user_id)
            if not user_data:
                continue
            prefs = user_data.get("preset_preferences", {})
            for preset, temp in prefs.items():
                all_preferences.setdefault(preset, []).append(temp)

        if not all_preferences:
            return None

        return {
            preset: sum(temps) / len(temps) for preset, temps in all_preferences.items()
        }

    async def cleanup(self) -> None:
        """Clean up resources."""
        for unsub in self._unsub_person_listeners:
            unsub()
        self._unsub_person_listeners.clear()
