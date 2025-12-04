# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/).

## [Unreleased]

### Planned
- 🎨 Web GUI for drag & drop area management
- 🤖 Smart heating with AI optimization
- 📊 Energy monitoring and statistics
- 🔗 MQTT auto-discovery for Zigbee2MQTT devices
- 👥 Presence-based heating
- 🌡️ Multi-sensor averaging per area
- 🔥 Direct OpenTherm boiler control
- 📱 Mobile app notifications
- 🌍 Weather-based temperature optimization

## [2.0.0] - 2025-12-04

### 🔄 BREAKING CHANGES
- **Complete Rename**: Integration renamed from "Zone Heater Manager" to "Smart Heating"
  - Domain changed from `zone_heater_manager` to `smart_heating`
  - All entities now use `smart_heating` prefix instead of `zone_heater`
  - Panel URL changed from `/zone_heater_manager/` to `/smart_heating/`
  - All service names changed from `zone_heater_manager.*` to `smart_heating.*`
  
- **Terminology Update**: Aligned with Home Assistant conventions
  - "Zones" renamed to "Areas" throughout the codebase
  - All service calls now use "area" instead of "zone" (e.g., `create_area`, `delete_area`)
  - Entity IDs changed from `climate.zone_*` to `climate.smart_heating_*`
  - API endpoints changed from `/zones` to `/areas`

### ✨ Added
- **Schedule Executor**
  - Automatic temperature control based on time schedules
  - Checks schedules every minute
  - Supports day-of-week and time-based rules
  - Handles midnight-crossing schedules correctly

### 🔧 Changed
- Updated all documentation to reflect new naming
- Frontend dependencies updated to latest versions (React 18.3, MUI v6, Vite 6)
- Improved coordinator lifecycle management
- Better separation of concerns (scheduler as separate component)

### 📝 Migration Guide
If upgrading from v0.1.0 or earlier:
1. Remove the old "Zone Heater Manager" integration
2. Delete `.storage/zone_heater_manager` file
3. Install "Smart Heating" v2.0.0
4. Reconfigure all areas
5. Update automations to use new service names (`smart_heating.*` instead of `zone_heater_manager.*`)
6. Update entity references in dashboards (e.g., `climate.zone_living_room` → `climate.smart_heating_living_room`)

## [0.1.0] - 2025-12-04

### ✨ Added
- **Zone Management System**
  - Create, delete and manage heating areas
  - Persistent storage of area configuration
  - Zone enable/disable functionality
  
- **Multi-Platform Support**
  - Climate entities per area for thermostat control
  - Switch entities for area on/off switching
  - Sensor entity for system status
  
- **Zigbee2MQTT Integration**
  - Support for thermostats
  - Support for temperature sensors
  - Support for OpenTherm gateways
  - Support for smart radiator valves
  
- **Extensive Service Calls**
  - `create_zone` - Create new zone
  - `delete_zone` - Delete zone
  - `add_device_to_zone` - Add device to zone
  - `remove_device_from_zone` - Remove device from zone
  - `set_area_temperature` - Set target temperature
  - `enable_zone` - Enable zone
  - `disable_zone` - Disable zone
  - `refresh` - Manually refresh data
  
- **Documentation**
  - Extensive README with installation instructions
  - GETTING_STARTED guide for new users
  - Example files:
    - `examples/automations.yaml` - Automation examples
    - `examples/scripts.yaml` - Script examples
    - `examples/lovelace.yaml` - Dashboard examples
    - `examples/configuration.yaml` - Helper configuration
  
- **Developer Features**
  - Extensive debug logging
  - Data coordinator with 30-second update interval
  - Type hints and docstrings
  - Clean code architecture

### 🔧 Changed
- Integration type changed from `device` to `hub`
- IoT class changed from `calculated` to `local_push`
- MQTT dependency added to manifest
- Platforms expanded from `sensor` to `sensor, climate, switch`

### 📚 Technical
- **New Files**:
  - `area_manager.py` - Core area management logic
  - `climate.py` - Climate platform implementation
  - `switch.py` - Switch platform implementation
  
- **Modified Files**:
  - `__init__.py` - Service registration and setup
  - `coordinator.py` - Zone data updates
  - `const.py` - Extended constants
  - `manifest.json` - MQTT dependency
  - `services.yaml` - Service definitions
  - `strings.json` - UI translations

### 🐛 Bugs
No known bugs in this release.

## [0.0.1] - 2025-12-04 (Initial Release)

### ✨ Added
- **Basic Integration Setup**
  - Config flow for UI installation
  - Data update coordinator
  - Status sensor entity
  - Refresh service
  
- **Documentation**
  - Basic README with installation instructions
  - License (MIT)
  - Deploy script for development
  
### 📚 Technical
- **Core Files**:
  - `__init__.py` - Integration entry point
  - `config_flow.py` - Configuration flow
  - `coordinator.py` - Data update coordinator
  - `sensor.py` - Sensor platform
  - `const.py` - Constants
  - `manifest.json` - Integration metadata
  - `services.yaml` - Service definitions
  - `strings.json` - UI strings

---

## Version Numbering

We use [SemVer](https://semver.org/) for version numbering:

- **MAJOR** version for incompatible API changes
- **MINOR** version for new functionality (backwards compatible)
- **PATCH** version for backwards compatible bug fixes

## Release Notes Template

```markdown
## [X.Y.Z] - YYYY-MM-DD

### ✨ Toegevoegd
- Nieuwe features

### 🔧 Gewijzigd
- Wijzigingen in bestaande functionaliteit

### 🐛 Opgelost
- Bug fixes

### 🗑️ Verwijderd
- Verwijderde features

### 🔒 Security
- Security patches
```

## Links

- [Repository](https://github.com/TheFlexican/smart_heating)
- [Issues](https://github.com/TheFlexican/smart_heating/issues)
- [Pull Requests](https://github.com/TheFlexican/smart_heating/pulls)
