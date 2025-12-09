"""Tests for user_manager module."""

import json
from datetime import datetime
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, Mock, patch

import pytest
from homeassistant.core import HomeAssistant
from pytest_homeassistant_custom_component.common import MockConfigEntry

from smart_heating.user_manager import UserManager


@pytest.fixture
def mock_hass():
    """Create a mock Home Assistant instance."""
    hass = MagicMock(spec=HomeAssistant)
    hass.async_add_executor_job = AsyncMock(side_effect=lambda func, *args: func(*args))
    hass.states = MagicMock()
    hass.bus = MagicMock()
    hass.bus.async_fire = MagicMock()
    return hass


@pytest.fixture
def temp_storage_path(tmp_path):
    """Create temporary storage path."""
    return str(tmp_path)


@pytest.fixture
async def user_manager(mock_hass, temp_storage_path):
    """Create a UserManager instance."""
    manager = UserManager(mock_hass, temp_storage_path)
    await manager.async_load()
    return manager


@pytest.mark.asyncio
async def test_user_manager_initialization(mock_hass, temp_storage_path):
    """Test UserManager initialization."""
    manager = UserManager(mock_hass, temp_storage_path)
    
    assert manager.hass == mock_hass
    assert manager._storage_file == Path(temp_storage_path) / "user_profiles.json"
    assert "users" in manager._data
    assert "presence_state" in manager._data
    assert "settings" in manager._data


@pytest.mark.asyncio
async def test_async_load_creates_file_if_not_exists(mock_hass, temp_storage_path):
    """Test that async_load creates file if it doesn't exist."""
    manager = UserManager(mock_hass, temp_storage_path)
    await manager.async_load()
    
    assert manager._storage_file.exists()
    
    # Verify file contents
    with open(manager._storage_file, "r") as f:
        data = json.load(f)
    
    assert "users" in data
    assert "presence_state" in data
    assert "settings" in data


@pytest.mark.asyncio
async def test_async_load_reads_existing_file(mock_hass, temp_storage_path):
    """Test that async_load reads existing file."""
    storage_file = Path(temp_storage_path) / "user_profiles.json"
    storage_file.parent.mkdir(parents=True, exist_ok=True)
    
    test_data = {
        "users": {
            "test_user": {
                "user_id": "person.test",
                "name": "Test User",
                "preset_preferences": {"home": 21.0},
                "priority": 5,
                "areas": [],
            }
        },
        "presence_state": {"users_home": [], "active_user": None, "combined_mode": "none"},
        "settings": {"multi_user_strategy": "priority", "enabled": True},
    }
    
    with open(storage_file, "w") as f:
        json.dump(test_data, f)
    
    manager = UserManager(mock_hass, temp_storage_path)
    await manager.async_load()
    
    assert "test_user" in manager._data["users"]
    assert manager._data["users"]["test_user"]["name"] == "Test User"


@pytest.mark.asyncio
async def test_create_user_profile(user_manager):
    """Test creating a user profile."""
    user = await user_manager.create_user_profile(
        user_id="user1",
        name="John Doe",
        person_entity="person.john",
        preset_preferences={"home": 21.0, "away": 16.0},
        priority=8,
        areas=["living_room"],
    )
    
    assert user["user_id"] == "person.john"
    assert user["name"] == "John Doe"
    assert user["preset_preferences"]["home"] == 21.0
    assert user["priority"] == 8
    assert user["areas"] == ["living_room"]
    
    # Verify it was saved
    assert "user1" in user_manager._data["users"]


@pytest.mark.asyncio
async def test_create_user_profile_duplicate_raises_error(user_manager):
    """Test creating duplicate user raises error."""
    await user_manager.create_user_profile(
        user_id="user1",
        name="John Doe",
        person_entity="person.john",
        preset_preferences={},
        priority=5,
    )
    
    with pytest.raises(ValueError, match="already exists"):
        await user_manager.create_user_profile(
            user_id="user1",
            name="Jane Doe",
            person_entity="person.jane",
            preset_preferences={},
            priority=5,
        )


@pytest.mark.asyncio
async def test_create_user_profile_invalid_priority(user_manager):
    """Test creating user with invalid priority raises error."""
    with pytest.raises(ValueError, match="Priority must be between"):
        await user_manager.create_user_profile(
            user_id="user1",
            name="John Doe",
            person_entity="person.john",
            preset_preferences={},
            priority=15,
        )


@pytest.mark.asyncio
async def test_update_user_profile(user_manager):
    """Test updating a user profile."""
    await user_manager.create_user_profile(
        user_id="user1",
        name="John Doe",
        person_entity="person.john",
        preset_preferences={"home": 21.0},
        priority=5,
    )
    
    updated = await user_manager.update_user_profile(
        "user1",
        {"name": "John Smith", "priority": 8},
    )
    
    assert updated["name"] == "John Smith"
    assert updated["priority"] == 8
    assert updated["preset_preferences"]["home"] == 21.0  # Unchanged


@pytest.mark.asyncio
async def test_update_user_profile_not_found(user_manager):
    """Test updating non-existent user raises error."""
    with pytest.raises(ValueError, match="not found"):
        await user_manager.update_user_profile("nonexistent", {"name": "Test"})


@pytest.mark.asyncio
async def test_delete_user_profile(user_manager):
    """Test deleting a user profile."""
    await user_manager.create_user_profile(
        user_id="user1",
        name="John Doe",
        person_entity="person.john",
        preset_preferences={},
        priority=5,
    )
    
    assert "user1" in user_manager._data["users"]
    
    await user_manager.delete_user_profile("user1")
    
    assert "user1" not in user_manager._data["users"]


@pytest.mark.asyncio
async def test_delete_user_profile_not_found(user_manager):
    """Test deleting non-existent user raises error."""
    with pytest.raises(ValueError, match="not found"):
        await user_manager.delete_user_profile("nonexistent")


@pytest.mark.asyncio
async def test_get_user_profile(user_manager):
    """Test retrieving a user profile."""
    await user_manager.create_user_profile(
        user_id="user1",
        name="John Doe",
        person_entity="person.john",
        preset_preferences={"home": 21.0},
        priority=5,
    )
    
    user = user_manager.get_user_profile("user1")
    
    assert user is not None
    assert user["name"] == "John Doe"


@pytest.mark.asyncio
async def test_get_user_profile_not_found(user_manager):
    """Test retrieving non-existent user returns None."""
    user = user_manager.get_user_profile("nonexistent")
    assert user is None


@pytest.mark.asyncio
async def test_get_all_users(user_manager):
    """Test getting all user profiles."""
    await user_manager.create_user_profile(
        user_id="user1",
        name="John Doe",
        person_entity="person.john",
        preset_preferences={},
        priority=5,
    )
    await user_manager.create_user_profile(
        user_id="user2",
        name="Jane Doe",
        person_entity="person.jane",
        preset_preferences={},
        priority=8,
    )
    
    users = user_manager.get_all_users()
    
    assert len(users) == 2
    assert "user1" in users
    assert "user2" in users


@pytest.mark.asyncio
async def test_get_presence_state(user_manager):
    """Test getting presence state."""
    state = user_manager.get_presence_state()
    
    assert "users_home" in state
    assert "active_user" in state
    assert "combined_mode" in state
    assert state["combined_mode"] == "none"


@pytest.mark.asyncio
async def test_update_settings(user_manager):
    """Test updating multi-user settings."""
    settings = await user_manager.update_settings(
        {"multi_user_strategy": "average", "enabled": False}
    )
    
    assert settings["multi_user_strategy"] == "average"
    assert settings["enabled"] is False


@pytest.mark.asyncio
async def test_get_highest_priority_user(user_manager):
    """Test getting highest priority user."""
    await user_manager.create_user_profile(
        user_id="user1", name="User 1", person_entity="person.user1", priority=5
    )
    await user_manager.create_user_profile(
        user_id="user2", name="User 2", person_entity="person.user2", priority=8
    )
    await user_manager.create_user_profile(
        user_id="user3", name="User 3", person_entity="person.user3", priority=3
    )
    
    highest = user_manager._get_highest_priority_user(["user1", "user2", "user3"])
    
    assert highest == "user2"


@pytest.mark.asyncio
async def test_get_active_user_preferences(user_manager, mock_hass):
    """Test getting active user preferences."""
    await user_manager.create_user_profile(
        user_id="user1",
        name="User 1",
        person_entity="person.user1",
        preset_preferences={"home": 21.0, "away": 16.0},
        priority=8,
    )
    
    # Simulate user being home
    user_manager._data["presence_state"]["users_home"] = ["user1"]
    user_manager._data["presence_state"]["active_user"] = "user1"
    
    prefs = user_manager.get_active_user_preferences()
    
    assert prefs is not None
    assert prefs["home"] == 21.0
    assert prefs["away"] == 16.0


@pytest.mark.asyncio
async def test_get_active_user_preferences_no_user_home(user_manager):
    """Test getting preferences when no user is home."""
    prefs = user_manager.get_active_user_preferences()
    assert prefs is None


@pytest.mark.asyncio
async def test_get_active_user_preferences_disabled(user_manager):
    """Test getting preferences when feature is disabled."""
    await user_manager.update_settings({"enabled": False})
    
    prefs = user_manager.get_active_user_preferences()
    assert prefs is None


@pytest.mark.asyncio
async def test_get_combined_preferences_priority_strategy(user_manager):
    """Test getting combined preferences with priority strategy."""
    await user_manager.create_user_profile(
        user_id="user1",
        name="User 1",
        person_entity="person.user1",
        preset_preferences={"home": 21.0},
        priority=5,
    )
    await user_manager.create_user_profile(
        user_id="user2",
        name="User 2",
        person_entity="person.user2",
        preset_preferences={"home": 22.0},
        priority=8,
    )
    
    user_manager._data["presence_state"]["users_home"] = ["user1", "user2"]
    user_manager._data["presence_state"]["active_user"] = "user2"
    user_manager._data["settings"]["multi_user_strategy"] = "priority"
    
    prefs = user_manager.get_combined_preferences()
    
    # Should use user2's preferences (higher priority)
    assert prefs["home"] == 22.0


@pytest.mark.asyncio
async def test_get_combined_preferences_average_strategy(user_manager):
    """Test getting combined preferences with average strategy."""
    await user_manager.create_user_profile(
        user_id="user1",
        name="User 1",
        person_entity="person.user1",
        preset_preferences={"home": 20.0, "away": 16.0},
        priority=5,
    )
    await user_manager.create_user_profile(
        user_id="user2",
        name="User 2",
        person_entity="person.user2",
        preset_preferences={"home": 22.0, "away": 18.0},
        priority=8,
    )
    
    user_manager._data["presence_state"]["users_home"] = ["user1", "user2"]
    user_manager._data["settings"]["multi_user_strategy"] = "average"
    
    prefs = user_manager.get_combined_preferences()
    
    # Should average: (20+22)/2 = 21, (16+18)/2 = 17
    assert prefs["home"] == 21.0
    assert prefs["away"] == 17.0


@pytest.mark.asyncio
async def test_area_filtering_in_preferences(user_manager):
    """Test that area filtering works in preferences."""
    await user_manager.create_user_profile(
        user_id="user1",
        name="User 1",
        person_entity="person.user1",
        preset_preferences={"home": 21.0},
        priority=5,
        areas=["living_room"],  # Only cares about living room
    )
    
    user_manager._data["presence_state"]["users_home"] = ["user1"]
    user_manager._data["presence_state"]["active_user"] = "user1"
    
    # Should return preferences for living room
    prefs = user_manager.get_active_user_preferences("living_room")
    assert prefs is not None
    assert prefs["home"] == 21.0
    
    # Should return None for bedroom
    prefs = user_manager.get_active_user_preferences("bedroom")
    assert prefs is None


@pytest.mark.asyncio
async def test_cleanup(user_manager):
    """Test cleanup removes listeners."""
    user_manager._unsub_person_listeners = [Mock(), Mock()]
    
    await user_manager.cleanup()
    
    for unsub in user_manager._unsub_person_listeners:
        unsub.assert_called_once()
    
    assert len(user_manager._unsub_person_listeners) == 0
