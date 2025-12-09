"""Tests for ConfigManager - Basic smoke tests."""

import pytest
from unittest.mock import MagicMock, AsyncMock, patch
from pathlib import Path

from smart_heating.config_manager import ConfigManager
from smart_heating.const import DOMAIN


@pytest.fixture
def mock_hass():
    """Create mock Home Assistant instance."""
    hass = MagicMock()
    hass.config.config_dir = "/config"
    hass.data = {
        DOMAIN: {
            "vacation_manager": MagicMock(
                enabled=False,
                start_date=None,
                end_date=None,
                preset_mode="eco",
                frost_protection_override=False,
                min_temperature=15.0,
            )
        }
    }
    return hass


@pytest.fixture
def mock_area_manager():
    """Create mock AreaManager."""
    manager = MagicMock()
    
    # Mock area
    mock_area = MagicMock()
    mock_area.to_dict.return_value = {
        "name": "Living Room",
        "enabled": True,
        "target_temperature": 21.0,
    }
    
    manager.get_all_areas.return_value = {"living_room": mock_area}
    manager.frost_protection_enabled = True
    manager.frost_protection_min_temp = 7.0
    manager.global_away_temp = 15.0
    manager.global_eco_temp = 18.0
    manager.global_comfort_temp = 21.0
    manager.global_home_temp = 20.0
    manager.global_sleep_temp = 17.0
    manager.global_activity_temp = 22.0
    manager.trv_heating_temp = 25.0
    manager.trv_idle_temp = 5.0
    manager.trv_temp_offset = 0.0
    manager.opentherm_enabled = False
    manager.opentherm_gateway_id = None
    manager.get_safety_sensors.return_value = []
    manager.async_save = AsyncMock()
    
    return manager


@pytest.fixture
def config_manager(mock_hass, mock_area_manager):
    """Create ConfigManager instance."""
    storage_path = Path("/config/.storage/smart_heating")
    with patch("smart_heating.config_manager.Path.mkdir"):
        return ConfigManager(mock_hass, mock_area_manager, storage_path)


class TestConfigManagerBasics:
    """Basic smoke tests for ConfigManager."""

    def test_init_creates_manager(self, mock_hass, mock_area_manager):
        """Test that ConfigManager can be initialized."""
        with patch("smart_heating.config_manager.Path.mkdir"):
            manager = ConfigManager(mock_hass, mock_area_manager, "/config/.storage/smart_heating")
        
        assert manager is not None
        assert isinstance(manager.storage_path, Path)

    async def test_export_returns_data(self, config_manager):
        """Test that export returns configuration data."""
        result = await config_manager.async_export_config()
        
        assert "version" in result
        assert "export_date" in result
        assert "areas" in result
        assert "global_settings" in result

    async def test_export_includes_areas(self, config_manager):
        """Test that export includes area data."""
        result = await config_manager.async_export_config()
        
        assert "living_room" in result["areas"]
        assert result["areas"]["living_room"]["name"] == "Living Room"

    async def test_export_includes_global_settings(self, config_manager):
        """Test that export includes global settings."""
        result = await config_manager.async_export_config()
        
        settings = result["global_settings"]
        assert "frost_protection" in settings
        assert "global_presets" in settings
        assert settings["frost_protection"]["enabled"] is True
        assert settings["frost_protection"]["min_temperature"] == 7.0

    async def test_import_valid_data(self, config_manager):
        """Test importing valid configuration data."""
        data = {
            "version": "0.6.0",
            "areas": {},
            "global_settings": {
                "frost_protection": {"enabled": True, "min_temp": 7.0}
            },
            "vacation_mode": {},
        }
        
        with patch.object(config_manager, "_async_create_backup", new=AsyncMock(return_value="backup.json")):
            result = await config_manager.async_import_config(data, create_backup=True)
        
        # Should complete without error
        assert isinstance(result, dict)

    async def test_import_skips_backup_when_disabled(self, config_manager):
        """Test import without creating backup."""
        data = {
            "version": "0.6.0",
            "areas": {},
            "global_settings": {},
            "vacation_mode": {},
        }
        
        backup_mock = AsyncMock()
        with patch.object(config_manager, "_async_create_backup", backup_mock):
            await config_manager.async_import_config(data, create_backup=False)
        
        # Backup should not be called
        backup_mock.assert_not_called()
