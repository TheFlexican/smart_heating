# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/).

## [Unreleased]

### Planned
- 🎨 Web GUI for drag & drop zone management
- 🤖 Smart heating with AI optimization
- 📊 Energy monitoring and statistics
- 🔗 MQTT auto-discovery for Zigbee2MQTT devices
- ⏱️ Time schedules per zone
- 👥 Presence-based heating
- 🌡️ Multi-sensor averaging per zone
- 🔥 Direct OpenTherm boiler control
- 📱 Mobile app notifications
- 🌍 Weather-based temperature optimization

## [0.1.0] - 2025-12-04

### ✨ Added
- **Zone Management System**
  - Create, delete and manage heating zones
  - Persistent storage of zone configuration
  - Zone enable/disable functionality
  
- **Multi-Platform Support**
  - Climate entities per zone for thermostat control
  - Switch entities for zone on/off switching
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
  - `set_zone_temperature` - Set target temperature
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
  - `zone_manager.py` - Core zone management logic
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

- [Repository](https://github.com/TheFlexican/zone_heater_manager)
- [Issues](https://github.com/TheFlexican/zone_heater_manager/issues)
- [Pull Requests](https://github.com/TheFlexican/zone_heater_manager/pulls)
