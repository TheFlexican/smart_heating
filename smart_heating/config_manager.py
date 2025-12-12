"""Configuration import/export manager for Smart Heating."""

import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Any

from homeassistant.core import HomeAssistant

from .area_manager import AreaManager
from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)

CURRENT_VERSION = "0.6.0"


class ConfigManager:
    """Manages configuration import/export for Smart Heating."""

    def __init__(
        self, hass: HomeAssistant, area_manager: AreaManager, storage_path: Path
    ):
        """Initialize the config manager.

        Args:
            hass: Home Assistant instance
            area_manager: Area manager instance
            storage_path: Path to storage directory
        """
        self.hass = hass
        self.area_manager = area_manager
        self.storage_path = (
            Path(storage_path) if isinstance(storage_path, str) else storage_path
        )
        self.backup_dir = self.storage_path / "backups"
        self.backup_dir.mkdir(exist_ok=True)

    async def async_export_config(self) -> dict[str, Any]:
        """Export all Smart Heating configuration.

        Returns:
            Dictionary with all configuration data
        """
        _LOGGER.info("Exporting Smart Heating configuration")

        # Get all areas with their full configuration
        areas_data = {}
        for area_id, area in self.area_manager.get_all_areas().items():
            areas_data[area_id] = area.to_dict()

        # Get global settings
        global_settings = {
            "frost_protection": {
                "enabled": self.area_manager.frost_protection_enabled,
                "min_temperature": self.area_manager.frost_protection_min_temp,
            },
            "global_presets": {
                "away_temp": self.area_manager.global_away_temp,
                "eco_temp": self.area_manager.global_eco_temp,
                "comfort_temp": self.area_manager.global_comfort_temp,
                "home_temp": self.area_manager.global_home_temp,
                "sleep_temp": self.area_manager.global_sleep_temp,
                "activity_temp": self.area_manager.global_activity_temp,
            },
            "trv_settings": {
                "heating_temp": self.area_manager.trv_heating_temp,
                "idle_temp": self.area_manager.trv_idle_temp,
                "temp_offset": self.area_manager.trv_temp_offset,
            },
            "opentherm": {
                "gateway_id": self.area_manager.opentherm_gateway_id,
            },
            "safety_sensors": self.area_manager.get_safety_sensors(),
        }

        # Get vacation mode if available
        vacation_data = None
        if "vacation_manager" in self.hass.data[DOMAIN]:
            vacation_manager = self.hass.data[DOMAIN]["vacation_manager"]
            vacation_data = {
                "enabled": vacation_manager.enabled,
                "start_date": (
                    vacation_manager.start_date.isoformat()
                    if vacation_manager.start_date
                    else None
                ),
                "end_date": (
                    vacation_manager.end_date.isoformat()
                    if vacation_manager.end_date
                    else None
                ),
                "preset_mode": vacation_manager.preset_mode,
                "frost_protection_override": vacation_manager.frost_protection_override,
                "min_temperature": vacation_manager.min_temperature,
            }

        export_data = {
            "version": CURRENT_VERSION,
            "export_date": datetime.now().isoformat(),
            "areas": areas_data,
            "global_settings": global_settings,
            "vacation_mode": vacation_data,
        }

        _LOGGER.info("Configuration export complete (%d areas)", len(areas_data))
        return export_data

    async def async_import_config(
        self, config_data: dict[str, Any], create_backup: bool = True
    ) -> dict[str, Any]:
        """Import Smart Heating configuration.

        Args:
            config_data: Configuration data to import
            create_backup: Whether to create a backup before importing

        Returns:
            Dictionary with import results

        Raises:
            ValueError: If configuration is invalid
        """
        _LOGGER.info("Importing Smart Heating configuration")

        # Validate structure
        self._validate_import_data(config_data)

        # Create backup if requested
        if create_backup:
            await self._async_create_backup()

        # Track changes
        changes = {
            "areas_created": 0,
            "areas_updated": 0,
            "areas_deleted": 0,
            "global_settings_updated": False,
            "vacation_mode_updated": False,
        }

        # Import global settings
        if "global_settings" in config_data:
            await self._async_import_global_settings(config_data["global_settings"])
            changes["global_settings_updated"] = True

        # Import areas
        if "areas" in config_data:
            area_changes = await self._async_import_areas(config_data["areas"])
            changes.update(area_changes)

        # Import vacation mode
        if "vacation_mode" in config_data and config_data["vacation_mode"]:
            await self._async_import_vacation_mode(config_data["vacation_mode"])
            changes["vacation_mode_updated"] = True

        _LOGGER.info("Configuration import complete: %s", changes)
        return changes

    def _validate_import_data(self, config_data: dict[str, Any]) -> None:
        """Validate imported configuration data.

        Args:
            config_data: Configuration data to validate

        Raises:
            ValueError: If configuration is invalid
        """
        # Check version
        if "version" not in config_data:
            raise ValueError("Missing version in configuration data")

        # Version compatibility check
        import_version = config_data["version"]
        if import_version != CURRENT_VERSION:
            _LOGGER.warning(
                "Import version (%s) differs from current version (%s)",
                import_version,
                CURRENT_VERSION,
            )

        # Check required fields
        if "areas" not in config_data and "global_settings" not in config_data:
            raise ValueError(
                "Configuration must contain either areas or global_settings"
            )

    async def _async_create_backup(self) -> str:
        """Create automatic backup before import.

        Returns:
            Path to backup file
        """
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_file = self.backup_dir / f"backup_{timestamp}.json"

        export_data = await self.async_export_config()

        with open(backup_file, "w", encoding="utf-8") as f:
            json.dump(export_data, f, indent=2)

        _LOGGER.info("Created backup at %s", backup_file)
        return str(backup_file)

    async def _async_import_global_settings(self, settings: dict[str, Any]) -> None:
        """Import global settings.

        Args:
            settings: Global settings data
        """
        # Frost protection
        if "frost_protection" in settings:
            fp = settings["frost_protection"]
            self.area_manager.frost_protection_enabled = fp.get("enabled", True)
            self.area_manager.frost_protection_min_temp = fp.get(
                "min_temperature", 10.0
            )

        # Global presets
        if "global_presets" in settings:
            presets = settings["global_presets"]
            self.area_manager.global_away_temp = presets.get("away_temp", 16.0)
            self.area_manager.global_eco_temp = presets.get("eco_temp", 18.0)
            self.area_manager.global_comfort_temp = presets.get("comfort_temp", 22.0)
            self.area_manager.global_home_temp = presets.get("home_temp", 20.0)
            self.area_manager.global_sleep_temp = presets.get("sleep_temp", 17.0)
            self.area_manager.global_activity_temp = presets.get("activity_temp", 21.0)

        # TRV settings
        if "trv_settings" in settings:
            trv = settings["trv_settings"]
            self.area_manager.trv_heating_temp = trv.get("heating_temp", 25.0)
            self.area_manager.trv_idle_temp = trv.get("idle_temp", 9.0)
            self.area_manager.trv_temp_offset = trv.get("temp_offset", 0.0)

        # OpenTherm
        if "opentherm" in settings:
            ot = settings["opentherm"]
            # Enablement is determined automatically by whether a gateway ID is present
            self.area_manager.opentherm_gateway_id = ot.get("gateway_id")

        # Safety sensors
        if "safety_sensors" in settings:
            self.area_manager.set_safety_sensors(settings["safety_sensors"])

        # Save to storage
        await self.area_manager.async_save()

        _LOGGER.info("Global settings imported")

    async def _async_import_areas(self, areas_data: dict[str, Any]) -> dict[str, int]:
        """Import areas configuration.

        Args:
            areas_data: Areas data to import

        Returns:
            Dictionary with counts of created/updated/deleted areas
        """
        changes = {"areas_created": 0, "areas_updated": 0, "areas_deleted": 0}

        existing_areas = set(self.area_manager.get_all_areas().keys())

        # Create or update areas
        for area_id, area_data in areas_data.items():
            if area_id in existing_areas:
                area = self.area_manager.get_area(area_id)
                if area:
                    self._apply_update_to_area(area, area_data)
                    changes["areas_updated"] += 1
            else:
                # Create new area and apply configuration
                self.area_manager.create_area(area_id, area_data.get("name", area_id))
                area = self.area_manager.get_area(area_id)
                if area:
                    self._apply_update_to_area(area, area_data)
                    changes["areas_created"] += 1

        # Note: We don't automatically delete areas that aren't in the import
        # This is a safety feature - user must manually delete if desired

        # Save to storage
        await self.area_manager.async_save()

        _LOGGER.info(
            "Areas imported: %d created, %d updated",
            changes["areas_created"],
            changes["areas_updated"],
        )
        return changes

    def _apply_update_to_area(self, area: Any, area_data: dict[str, Any]) -> None:
        """Apply area_data onto the passed area object (in-place)."""
        area.name = area_data.get("name", area.name)
        area.enabled = area_data.get("enabled", True)
        area.target_temperature = area_data.get("target_temperature", 20.0)
        area.preset_mode = area_data.get("preset_mode", "home")
        area.night_boost_enabled = area_data.get("night_boost_enabled", False)
        area.night_boost_offset = area_data.get("night_boost_offset", 0.5)
        area.night_boost_start_time = area_data.get("night_boost_start_time")
        area.night_boost_end_time = area_data.get("night_boost_end_time")
        area.smart_night_boost_enabled = area_data.get(
            "smart_night_boost_enabled", False
        )
        area.weather_entity_id = area_data.get("weather_entity_id")

        if "devices" in area_data:
            area.heating_devices = area_data["devices"]
        if "temperature_sensors" in area_data:
            area.temperature_sensors = area_data["temperature_sensors"]
        if "schedules" in area_data:
            area.schedules = area_data["schedules"]

    async def _async_import_vacation_mode(self, vacation_data: dict[str, Any]) -> None:
        """Import vacation mode configuration.

        Args:
            vacation_data: Vacation mode data
        """
        if "vacation_manager" not in self.hass.data[DOMAIN]:
            _LOGGER.warning(
                "Vacation manager not available, skipping vacation mode import"
            )
            return

        vacation_manager = self.hass.data[DOMAIN]["vacation_manager"]

        # Parse dates if present
        start_date = None
        end_date = None
        if vacation_data.get("start_date"):
            start_date = datetime.fromisoformat(vacation_data["start_date"])
        if vacation_data.get("end_date"):
            end_date = datetime.fromisoformat(vacation_data["end_date"])

        # Update vacation manager
        vacation_manager.enabled = vacation_data.get("enabled", False)
        vacation_manager.start_date = start_date
        vacation_manager.end_date = end_date
        vacation_manager.preset_mode = vacation_data.get("preset_mode", "away")
        vacation_manager.frost_protection_override = vacation_data.get(
            "frost_protection_override", True
        )
        vacation_manager.min_temperature = vacation_data.get("min_temperature", 10.0)

        # Save vacation mode
        await vacation_manager.async_save()

        _LOGGER.info("Vacation mode imported (enabled: %s)", vacation_manager.enabled)
