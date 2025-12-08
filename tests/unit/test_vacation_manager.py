"""Tests for vacation manager.

Tests vacation mode enable/disable, expiration, person entity tracking,
and storage functionality.
"""

import json
from datetime import date, timedelta
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from homeassistant.core import HomeAssistant

from smart_heating.vacation_manager import VacationManager


@pytest.fixture
def vacation_manager(hass: HomeAssistant, tmp_path) -> VacationManager:
    """Create a VacationManager instance."""
    return VacationManager(hass, str(tmp_path))


class TestInitialization:
    """Tests for initialization."""

    def test_init(self, vacation_manager: VacationManager, hass: HomeAssistant):
        """Test vacation manager initialization."""
        assert vacation_manager.hass == hass
        assert vacation_manager._data is not None
        assert vacation_manager._data["enabled"] is False
        assert vacation_manager._data["preset_mode"] == "away"
        assert vacation_manager._data["frost_protection_override"] is True
        assert vacation_manager._data["min_temperature"] == 10.0
        assert vacation_manager._data["auto_disable"] is True
        assert vacation_manager._data["person_entities"] == []


class TestStorage:
    """Tests for storage functionality."""

    @pytest.mark.asyncio
    async def test_async_save_creates_file(self, vacation_manager: VacationManager):
        """Test that saving creates the storage file."""
        await vacation_manager.async_save()
        
        assert vacation_manager._storage_file.exists()
        
        with open(vacation_manager._storage_file, 'r') as f:
            data = json.load(f)
        
        assert data["enabled"] is False
        assert data["preset_mode"] == "away"

    @pytest.mark.asyncio
    async def test_async_load_nonexistent_file(self, vacation_manager: VacationManager):
        """Test loading when file doesn't exist creates default."""
        await vacation_manager.async_load()
        
        # Should create file with defaults
        assert vacation_manager._storage_file.exists()
        assert vacation_manager._data["enabled"] is False

    @pytest.mark.asyncio
    async def test_async_load_existing_file(self, vacation_manager: VacationManager, hass: HomeAssistant, tmp_path):
        """Test loading existing vacation mode data."""
        # First save some data
        vacation_manager._data["enabled"] = True
        vacation_manager._data["preset_mode"] = "eco"
        await vacation_manager.async_save()
        
        # Create new manager and load
        new_manager = VacationManager(hass, str(tmp_path))
        await new_manager.async_load()
        
        assert new_manager._data["enabled"] is True
        assert new_manager._data["preset_mode"] == "eco"

    @pytest.mark.asyncio
    async def test_async_load_corrupted_file(self, vacation_manager: VacationManager):
        """Test loading corrupted file handles error gracefully."""
        # Write corrupted JSON
        vacation_manager._storage_file.parent.mkdir(parents=True, exist_ok=True)
        with open(vacation_manager._storage_file, 'w') as f:
            f.write("invalid json{")
        
        # Should handle error gracefully
        await vacation_manager.async_load()
        # Data should still be default
        assert vacation_manager._data["enabled"] is False


class TestEnable:
    """Tests for enabling vacation mode."""

    @pytest.mark.asyncio
    async def test_enable_basic(self, vacation_manager: VacationManager):
        """Test enabling vacation mode with basic parameters."""
        result = await vacation_manager.async_enable(
            start_date="2024-01-01",
            end_date="2024-01-15",
        )
        
        assert result["enabled"] is True
        assert result["start_date"] == "2024-01-01"
        assert result["end_date"] == "2024-01-15"
        assert result["preset_mode"] == "away"

    @pytest.mark.asyncio
    async def test_enable_with_custom_preset(self, vacation_manager: VacationManager):
        """Test enabling with custom preset mode."""
        result = await vacation_manager.async_enable(
            preset_mode="eco",
        )
        
        assert result["preset_mode"] == "eco"

    @pytest.mark.asyncio
    async def test_enable_with_frost_protection(self, vacation_manager: VacationManager):
        """Test enabling with custom frost protection."""
        result = await vacation_manager.async_enable(
            frost_protection_override=True,
            min_temperature=12.0,
        )
        
        assert result["frost_protection_override"] is True
        assert result["min_temperature"] == 12.0

    @pytest.mark.asyncio
    async def test_enable_default_start_date(self, vacation_manager: VacationManager):
        """Test enabling without start date uses today."""
        result = await vacation_manager.async_enable()
        
        assert result["start_date"] == date.today().isoformat()

    @pytest.mark.asyncio
    async def test_enable_with_person_entities(self, vacation_manager: VacationManager):
        """Test enabling with person entity tracking."""
        with patch.object(vacation_manager, '_setup_person_listeners') as mock_setup:
            result = await vacation_manager.async_enable(
                auto_disable=True,
                person_entities=["person.john", "person.jane"]
            )
        
        assert result["person_entities"] == ["person.john", "person.jane"]
        mock_setup.assert_called_once()

    @pytest.mark.asyncio
    async def test_enable_invalid_start_date(self, vacation_manager: VacationManager):
        """Test enabling with invalid start date format."""
        with pytest.raises(ValueError, match="Invalid start_date format"):
            await vacation_manager.async_enable(start_date="invalid-date")

    @pytest.mark.asyncio
    async def test_enable_invalid_end_date(self, vacation_manager: VacationManager):
        """Test enabling with invalid end date format."""
        with pytest.raises(ValueError, match="Invalid end_date format"):
            await vacation_manager.async_enable(end_date="2024-99-99")


class TestDisable:
    """Tests for disabling vacation mode."""

    @pytest.mark.asyncio
    async def test_disable(self, vacation_manager: VacationManager):
        """Test disabling vacation mode."""
        # First enable
        await vacation_manager.async_enable()
        assert vacation_manager._data["enabled"] is True
        
        # Then disable
        result = await vacation_manager.async_disable()
        
        assert result["enabled"] is False
        assert vacation_manager._data["enabled"] is False

    @pytest.mark.asyncio
    async def test_disable_cleans_up_listeners(self, vacation_manager: VacationManager):
        """Test disabling cleans up person listeners."""
        # Create mock listeners
        mock_unsub_1 = MagicMock()
        mock_unsub_2 = MagicMock()
        vacation_manager._unsub_person_listeners = [mock_unsub_1, mock_unsub_2]
        
        await vacation_manager.async_disable()
        
        mock_unsub_1.assert_called_once()
        mock_unsub_2.assert_called_once()
        assert len(vacation_manager._unsub_person_listeners) == 0


class TestExpiration:
    """Tests for expiration checking."""

    @pytest.mark.asyncio
    async def test_check_expiration_not_expired(self, vacation_manager: VacationManager):
        """Test expiration check when not expired."""
        future_date = (date.today() + timedelta(days=7)).isoformat()
        await vacation_manager.async_enable(end_date=future_date)
        
        await vacation_manager._check_expiration()
        
        assert vacation_manager._data["enabled"] is True

    @pytest.mark.asyncio
    async def test_check_expiration_expired(self, vacation_manager: VacationManager):
        """Test expiration check when expired."""
        past_date = (date.today() - timedelta(days=1)).isoformat()
        await vacation_manager.async_enable(end_date=past_date)
        
        await vacation_manager._check_expiration()
        
        assert vacation_manager._data["enabled"] is False

    @pytest.mark.asyncio
    async def test_check_expiration_no_end_date(self, vacation_manager: VacationManager):
        """Test expiration check with no end date set."""
        await vacation_manager.async_enable(end_date=None)
        
        await vacation_manager._check_expiration()
        
        # Should still be enabled (no end date = no expiration)
        assert vacation_manager._data["enabled"] is True

    @pytest.mark.asyncio
    async def test_check_expiration_not_enabled(self, vacation_manager: VacationManager):
        """Test expiration check when not enabled."""
        vacation_manager._data["enabled"] = False
        vacation_manager._data["end_date"] = (date.today() - timedelta(days=1)).isoformat()
        
        await vacation_manager._check_expiration()
        
        # Should still be disabled
        assert vacation_manager._data["enabled"] is False

    @pytest.mark.asyncio
    async def test_check_expiration_invalid_date(self, vacation_manager: VacationManager):
        """Test expiration check with invalid date format."""
        await vacation_manager.async_enable()
        vacation_manager._data["end_date"] = "invalid-date"
        
        # Should handle error gracefully
        await vacation_manager._check_expiration()


class TestActiveStatus:
    """Tests for is_active checks."""

    def test_is_active_when_enabled(self, vacation_manager: VacationManager):
        """Test is_active returns True when enabled."""
        vacation_manager._data["enabled"] = True
        vacation_manager._data["end_date"] = (date.today() + timedelta(days=7)).isoformat()
        
        assert vacation_manager.is_active() is True

    def test_is_active_when_disabled(self, vacation_manager: VacationManager):
        """Test is_active returns False when disabled."""
        vacation_manager._data["enabled"] = False
        
        assert vacation_manager.is_active() is False

    def test_is_active_when_expired(self, vacation_manager: VacationManager):
        """Test is_active returns False when expired."""
        vacation_manager._data["enabled"] = True
        vacation_manager._data["end_date"] = (date.today() - timedelta(days=1)).isoformat()
        
        assert vacation_manager.is_active() is False

    def test_is_active_no_end_date(self, vacation_manager: VacationManager):
        """Test is_active when no end date is set."""
        vacation_manager._data["enabled"] = True
        vacation_manager._data["end_date"] = None
        
        assert vacation_manager.is_active() is True

    def test_is_active_invalid_end_date(self, vacation_manager: VacationManager):
        """Test is_active with invalid end date format."""
        vacation_manager._data["enabled"] = True
        vacation_manager._data["end_date"] = "invalid-date"
        
        # Should still return True (invalid date ignored)
        assert vacation_manager.is_active() is True


class TestGetters:
    """Tests for getter methods."""

    def test_get_preset_mode_active(self, vacation_manager: VacationManager):
        """Test getting preset mode when active."""
        vacation_manager._data["enabled"] = True
        vacation_manager._data["preset_mode"] = "eco"
        
        assert vacation_manager.get_preset_mode() == "eco"

    def test_get_preset_mode_inactive(self, vacation_manager: VacationManager):
        """Test getting preset mode when inactive."""
        vacation_manager._data["enabled"] = False
        
        assert vacation_manager.get_preset_mode() is None

    def test_get_min_temperature_active(self, vacation_manager: VacationManager):
        """Test getting min temperature when active."""
        vacation_manager._data["enabled"] = True
        vacation_manager._data["frost_protection_override"] = True
        vacation_manager._data["min_temperature"] = 12.0
        
        assert vacation_manager.get_min_temperature() == 12.0

    def test_get_min_temperature_inactive(self, vacation_manager: VacationManager):
        """Test getting min temperature when inactive."""
        vacation_manager._data["enabled"] = False
        
        assert vacation_manager.get_min_temperature() is None

    def test_get_min_temperature_frost_disabled(self, vacation_manager: VacationManager):
        """Test getting min temperature when frost protection disabled."""
        vacation_manager._data["enabled"] = True
        vacation_manager._data["frost_protection_override"] = False
        
        assert vacation_manager.get_min_temperature() is None

    def test_get_data(self, vacation_manager: VacationManager):
        """Test getting vacation mode data."""
        vacation_manager._data["enabled"] = True
        vacation_manager._data["preset_mode"] = "away"
        
        data = vacation_manager.get_data()
        
        assert data["enabled"] is True
        assert data["preset_mode"] == "away"
        # Should be a copy, not the original
        assert data is not vacation_manager._data


class TestPersonListeners:
    """Tests for person entity listeners."""

    def test_setup_person_listeners_no_entities(self, vacation_manager: VacationManager):
        """Test setting up listeners with no entities."""
        vacation_manager._data["person_entities"] = []
        
        vacation_manager._setup_person_listeners()
        
        assert len(vacation_manager._unsub_person_listeners) == 0

    def test_setup_person_listeners_with_entities(self, vacation_manager: VacationManager):
        """Test setting up listeners with entities."""
        vacation_manager._data["person_entities"] = ["person.john", "person.jane"]
        
        with patch('smart_heating.vacation_manager.async_track_state_change_event') as mock_track:
            mock_track.return_value = MagicMock()
            vacation_manager._setup_person_listeners()
        
        assert mock_track.call_count == 2
        assert len(vacation_manager._unsub_person_listeners) == 2

    def test_setup_person_listeners_cleans_existing(self, vacation_manager: VacationManager):
        """Test setting up listeners cleans up existing ones."""
        # Create mock existing listeners
        mock_unsub = MagicMock()
        vacation_manager._unsub_person_listeners = [mock_unsub]
        vacation_manager._data["person_entities"] = []
        
        vacation_manager._setup_person_listeners()
        
        mock_unsub.assert_called_once()
        assert len(vacation_manager._unsub_person_listeners) == 0

    @pytest.mark.asyncio
    async def test_load_with_enabled_sets_up_listeners(self, vacation_manager: VacationManager, hass: HomeAssistant, tmp_path):
        """Test loading enabled vacation mode sets up listeners."""
        # Save enabled vacation mode with person entities
        vacation_manager._data["enabled"] = True
        vacation_manager._data["auto_disable"] = True
        vacation_manager._data["person_entities"] = ["person.john"]
        vacation_manager._data["end_date"] = (date.today() + timedelta(days=7)).isoformat()
        await vacation_manager.async_save()
        
        # Create new manager and load
        new_manager = VacationManager(hass, str(tmp_path))
        
        with patch('smart_heating.vacation_manager.async_track_state_change_event') as mock_track:
            mock_track.return_value = MagicMock()
            await new_manager.async_load()
        
        # Should have set up listeners
        assert mock_track.call_count == 1


class TestLoadEdgeCases:
    """Test edge cases in loading."""

    @pytest.mark.asyncio
    async def test_load_with_error(self, vacation_manager: VacationManager, tmp_path):
        """Test loading with file read error."""
        # Create corrupted file
        corrupt_file = tmp_path / "vacation_mode.json"
        corrupt_file.write_text("{invalid json", encoding='utf-8')
        
        # Should handle error gracefully
        await vacation_manager.async_load()
        
        # Should have default values
        assert vacation_manager._data["enabled"] is False

    @pytest.mark.asyncio
    async def test_save_with_error(self, vacation_manager: VacationManager):
        """Test saving with write error."""
        # Make storage file read-only
        vacation_manager._storage_file.parent.mkdir(parents=True, exist_ok=True)
        vacation_manager._storage_file.touch()
        vacation_manager._storage_file.chmod(0o444)
        
        try:
            # Should handle error gracefully
            await vacation_manager.async_save()
        finally:
            # Clean up
            vacation_manager._storage_file.chmod(0o644)
