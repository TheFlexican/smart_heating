"""Tests for import/export API handlers - Basic smoke tests."""

import json
import pytest
from unittest.mock import MagicMock, AsyncMock, patch, mock_open

from smart_heating.api_handlers.import_export import (
    handle_export_config,
    handle_import_config,
    handle_validate_config,
    handle_list_backups,
    handle_restore_backup,
)


@pytest.fixture
def mock_hass():
    """Create mock Home Assistant instance."""
    hass = MagicMock()
    hass.data = {"smart_heating": {"vacation_manager": MagicMock()}}
    return hass


@pytest.fixture
def mock_config_manager():
    """Create mock ConfigManager."""
    from pathlib import Path
    from unittest.mock import PropertyMock
    
    manager = MagicMock()
    
    # Mock export - returns valid data
    manager.async_export_config = AsyncMock(
        return_value={
            "version": "0.6.0",
            "export_date": "2024-01-15T10:30:00",
            "areas": {},
            "global_settings": {},
            "vacation_mode": {},
        }
    )
    
    # Mock import - returns changes dict
    manager.async_import_config = AsyncMock(
        return_value={
            "areas_created": 0,
            "areas_updated": 0,
            "global_settings_updated": False,
        }
    )
    
    # Mock validate - internal method
    manager._validate_import_data = MagicMock()
    
    # Mock area_manager for validate handler
    manager.area_manager.get_all_areas.return_value = {}
    
    # Mock backup_dir for list/restore handlers
    backup_dir = MagicMock(spec=Path)
    backup_dir.exists.return_value = False
    type(manager).backup_dir = PropertyMock(return_value=backup_dir)
    
    return manager


class TestExportHandler:
    """Basic tests for export handler."""

    async def test_export_returns_json_response(self, mock_hass, mock_config_manager):
        """Test that export returns a response with JSON content."""
        response = await handle_export_config(mock_hass, mock_config_manager)
        
        assert response.status == 200
        assert "application/json" in response.headers["Content-Type"]
        assert "attachment" in response.headers["Content-Disposition"]


class TestImportHandler:
    """Basic tests for import handler."""

    async def test_import_accepts_valid_data(self, mock_hass, mock_config_manager):
        """Test that import handler accepts valid configuration data."""
        data = {
            "version": "0.6.0",
            "areas": {},
            "global_settings": {},
        }
        
        response = await handle_import_config(mock_hass, mock_config_manager, data)
        
        assert response.status == 200
        # Verify async_import_config was called with create_backup=True
        mock_config_manager.async_import_config.assert_called_once_with(data, create_backup=True)

    async def test_import_validation_error(self, mock_hass, mock_config_manager):
        """Test import with validation error."""
        # Mock to raise ValueError
        mock_config_manager.async_import_config = AsyncMock(
            side_effect=ValueError("Invalid version")
        )
        
        data = {"version": "99.99.99"}
        response = await handle_import_config(mock_hass, mock_config_manager, data)
        
        assert response.status == 400
        data = json.loads(response.body)
        assert "error" in data

    async def test_import_with_changes(self, mock_hass, mock_config_manager):
        """Test import returns changes information."""
        mock_config_manager.async_import_config = AsyncMock(
            return_value={
                "areas_created": 2,
                "areas_updated": 1,
                "global_settings_updated": True,
            }
        )
        
        data = {"version": "0.6.0", "areas": {}}
        response = await handle_import_config(mock_hass, mock_config_manager, data)
        
        assert response.status == 200
        result = json.loads(response.body)
        assert result["success"] is True
        assert "changes" in result


class TestValidateHandler:
    """Basic tests for validate handler."""

    async def test_validate_returns_response(self, mock_hass, mock_config_manager):
        """Test that validate handler returns a response."""
        data = {"version": "0.6.0", "areas": {}}
        
        # Just check it returns something
        response = await handle_validate_config(mock_hass, mock_config_manager, data)
        
        assert response.status == 200

    async def test_validate_with_preview(self, mock_hass, mock_config_manager):
        """Test validate returns preview information."""
        mock_config_manager.area_manager.get_all_areas.return_value = {
            "living_room": MagicMock()
        }
        
        data = {
            "version": "0.6.0",
            "export_date": "2024-01-15T10:30:00",
            "areas": {
                "living_room": {"name": "Living Room"},
                "bedroom": {"name": "Bedroom"}
            },
            "global_settings": {},
            "vacation_mode": {},
        }
        
        response = await handle_validate_config(mock_hass, mock_config_manager, data)
        
        assert response.status == 200
        result = json.loads(response.body)
        assert result["valid"] is True
        assert result["areas_to_create"] == 1  # bedroom
        assert result["areas_to_update"] == 1  # living_room

    async def test_validate_invalid_data(self, mock_hass, mock_config_manager):
        """Test validation with invalid data."""
        mock_config_manager._validate_import_data = MagicMock(
            side_effect=ValueError("Missing required field")
        )
        
        data = {"version": "0.6.0"}
        response = await handle_validate_config(mock_hass, mock_config_manager, data)
        
        assert response.status == 400
        result = json.loads(response.body)
        assert result["valid"] is False
        assert "error" in result


class TestBackupHandlers:
    """Basic tests for backup handlers."""

    async def test_list_backups_returns_response(self, mock_hass, mock_config_manager):
        """Test that list backups returns a response."""
        response = await handle_list_backups(mock_hass, mock_config_manager)
        
        assert response.status == 200

    async def test_list_backups_with_files(self, mock_hass, mock_config_manager):
        """Test listing backups when files exist."""
        from pathlib import Path
        from unittest.mock import PropertyMock
        
        # Mock backup directory with files
        backup_dir = MagicMock(spec=Path)
        backup_dir.exists.return_value = True
        
        # Mock backup file
        mock_file = MagicMock(spec=Path)
        mock_file.name = "backup_20240115_120000.json"
        mock_stat = MagicMock()
        mock_stat.st_size = 1024
        mock_stat.st_mtime = 1705320000.0
        mock_file.stat.return_value = mock_stat
        
        backup_dir.glob.return_value = [mock_file]
        type(mock_config_manager).backup_dir = PropertyMock(return_value=backup_dir)
        
        response = await handle_list_backups(mock_hass, mock_config_manager)
        
        assert response.status == 200
        data = json.loads(response.body)
        assert "backups" in data
        assert len(data["backups"]) == 1
        assert data["backups"][0]["filename"] == "backup_20240115_120000.json"

    async def test_restore_backup_not_found(self, mock_hass, mock_config_manager):
        """Test restoring non-existent backup."""
        from pathlib import Path
        from unittest.mock import PropertyMock
        
        # Mock backup directory
        backup_dir = MagicMock(spec=Path)
        backup_file = MagicMock(spec=Path)
        backup_file.exists.return_value = False
        backup_dir.__truediv__.return_value = backup_file
        type(mock_config_manager).backup_dir = PropertyMock(return_value=backup_dir)
        
        response = await handle_restore_backup(
            mock_hass, mock_config_manager, "nonexistent.json"
        )
        
        assert response.status == 404

    async def test_restore_backup_success(self, mock_hass, mock_config_manager):
        """Test successful backup restore."""
        from pathlib import Path
        from unittest.mock import PropertyMock
        
        # Mock backup directory and file
        backup_dir = MagicMock(spec=Path)
        backup_file = MagicMock(spec=Path)
        backup_file.exists.return_value = True
        backup_file.__str__.return_value = "/path/to/backup.json"
        backup_dir.__truediv__.return_value = backup_file
        type(mock_config_manager).backup_dir = PropertyMock(return_value=backup_dir)
        
        # Mock file content
        backup_content = json.dumps({
            "version": "0.6.0",
            "areas": {},
            "global_settings": {},
        })
        
        with patch("builtins.open", mock_open(read_data=backup_content)):
            response = await handle_restore_backup(
                mock_hass, mock_config_manager, "backup.json"
            )
        
        assert response.status == 200
        data = json.loads(response.body)
        assert data["success"] is True
        response = await handle_restore_backup(
            mock_hass, mock_config_manager, "backup.json"
        )
        
        # Any response is fine for smoke test
        assert response is not None
