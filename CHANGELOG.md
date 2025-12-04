# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/).

## [Unreleased]

### Planned
- 🤖 AI-driven heating optimization
- 📊 Advanced energy analytics and cost tracking
- 🔗 MQTT auto-discovery for Zigbee2MQTT devices
- 👥 Presence-based heating control
- 🌡️ Weather-based temperature optimization
- 🔥 PID control for OpenTherm gateways
- 📱 Mobile app notifications
- 🏡 Multi-home support

## [Unreleased]

### ✨ Added
- **Device Status Display in Area Cards**: Area overview now shows real-time device information
  - **Thermostats**: Display HVAC action (heating/idle), current temperature, and target temperature
    - Red flame icon when actively heating
    - Blue thermostat icon when idle
    - Status text shows "heating · 19.5°C → 21°C"
  - **Temperature Sensors**: Show current temperature reading with green sensor icon
  - **Valves**: Display position percentage and open/closed state
    - Orange icon when valve is open (position > 0)
    - Status text shows "75% · open"
  - **Switches**: Show on/off state with color-coded power icons
  - Color-coded icons provide instant visual feedback of device states
  - All device states update automatically every 30 seconds via coordinator

- **Real-time Device State Updates**: Area overview now shows immediate feedback when temperature changes
  - Device states (heating/idle/off) update instantly when temperature is adjusted
  - Thermostat HVAC action (heating/idle) reflected in real-time
  - Valve positions and switch states update immediately
  - WebSocket pushes device state changes to frontend within 1-2 seconds
  - Coordinator includes full device state information with type-specific attributes
  - Temperature changes trigger immediate climate control execution

### 🐛 Fixed
- **Device Display Names**: Area cards now show human-readable device names (e.g., "Living Room Thermostat") instead of entity IDs (e.g., "climate.living_room")
  - API endpoints `/api/smart_heating/areas` and `/api/smart_heating/areas/{id}` now include `name` field in device objects
  - Device names are extracted from Home Assistant entity state's `friendly_name` attribute
  - Improves UX when assigning devices to areas via drag-and-drop

## [2.1.0] - 2025-12-04

### ✨ Added - Major Feature Release

**Smart Scheduling System**
- Time-based temperature schedules with HH:MM format
- Day-of-week selection (individual or all days)
- Schedule executor running every minute
- Automatic temperature changes based on active schedules
- Multiple schedules per area with priority handling
- Enable/disable individual schedules
- Schedule persistence across restarts

**Night Boost Feature**
- Automatic temperature boost during night hours (22:00-06:00)
- Configurable temperature offset (0-3°C, default: 0.5°C)
- Per-area enable/disable control
- Helps maintain comfort in early morning
- Integrated with schedule system
- Service: `smart_heating.set_night_boost`

**Temperature History Tracking**
- Records temperature every 5 minutes
- Stores current temperature, target temperature, and heating state
- 7-day automatic retention period
- Persistent storage in `.storage/smart_heating_history`
- Automatic cleanup of old data
- API endpoint: `GET /api/smart_heating/areas/{area_id}/history?hours=24`

**Interactive History Charts**
- Beautiful Recharts-based visualization
- Multiple time ranges: 6h, 12h, 24h, 3d, 7d
- Color-coded lines:
  - Blue: Current temperature
  - Yellow dashed: Target temperature
  - Red dots: Heating active periods
- Auto-refresh every 5 minutes
- Responsive design matching HA theme

**Advanced Settings UI**
- Complete Settings tab in area detail page
- Night boost controls:
  - Enable/disable toggle
  - Temperature offset slider (0-3°C)
  - Real-time updates
- Hysteresis configuration:
  - Global setting (0.1-2.0°C)
  - Prevents rapid on/off cycling
  - Visual slider with markers
- Temperature limits display (5-30°C)
- Professional UI with helpful descriptions

**New Services**
- `smart_heating.add_schedule` - Add time-based temperature schedule
- `smart_heating.remove_schedule` - Remove schedule from area
- `smart_heating.enable_schedule` - Enable specific schedule
- `smart_heating.disable_schedule` - Disable specific schedule
- `smart_heating.set_night_boost` - Configure night boost settings
- `smart_heating.set_hysteresis` - Set global hysteresis value

**API Enhancements**
- `/api/smart_heating/call_service` - Generic service call endpoint
- `/api/smart_heating/areas/{area_id}/history` - Get temperature history
- Night boost fields in area responses
- Service call integration from frontend

### 🔧 Changed
- Climate controller now records history every 5 minutes (10 cycles)
- Area data includes `night_boost_enabled` and `night_boost_offset`
- Effective target temperature calculation includes night boost
- Frontend AreaDetail page reorganized with 5 tabs
- Enhanced service descriptions in `services.yaml`

### 🐛 Fixed
- Scheduler variable naming (area → area consistency)
- Area entity ID generation in scheduler
- Method calls in ScheduleExecutor

### 📚 Technical
- **New Files**:
  - `history.py` - HistoryTracker class for temperature logging
  - `scheduler.py` - ScheduleExecutor for time-based control
  - `frontend/src/components/HistoryChart.tsx` - Interactive chart component
- **Enhanced Files**:
  - `__init__.py` - Integrated scheduler and history tracker
  - `api.py` - Added history and service call endpoints
  - `climate_controller.py` - History recording integration
  - `area_manager.py` - Night boost and schedule support
  - `const.py` - New service and attribute constants
  - `services.yaml` - Complete service definitions
- **Storage**:
  - `.storage/smart_heating_storage` - Areas and schedules
  - `.storage/smart_heating_history` - Temperature history

### 🏆 Performance
- History stored efficiently with 1000 entry limit per area
- Automatic cleanup prevents storage bloat
- History recording optimized (every 5 min vs every 30 sec)
- Schedule checks only once per minute

## [2.0.0] - 2025-12-04

### 🔄 BREAKING CHANGES
- **Complete Rename**: Integration renamed from "Area Heater Manager" to "Smart Heating"
  - Domain changed from `area_heater_manager` to `smart_heating`
  - All entities now use `smart_heating` prefix instead of `area_heater`
  - Panel URL changed from `/area_heater_manager/` to `/smart_heating/`
  - All service names changed from `area_heater_manager.*` to `smart_heating.*`
  
- **Terminology Update**: Aligned with Home Assistant conventions
  - "Zones" renamed to "Areas" throughout the codebase
  - All service calls now use "area" instead of "zone" terminology
  - Entity IDs changed from `climate.area_*` to `climate.smart_heating_*`
  - API endpoints updated to use "areas" terminology
  - Areas are now based on Home Assistant areas (created in Settings → Areas & Zones)
  - Removed manual area creation/deletion - areas sync with HA's area registry

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
1. Remove the old "Area Heater Manager" integration
2. Delete `.storage/area_heater_manager` file
3. Install "Smart Heating" v2.0.0
4. Reconfigure all areas
5. Update automations to use new service names (`smart_heating.*` instead of `area_heater_manager.*`)
6. Update entity references in dashboards (e.g., `climate.area_living_room` → `climate.smart_heating_living_room`)

## [0.1.0] - 2025-12-04

### ✨ Added
- **Area Management System**
  - Create, delete and manage heating areas
  - Persistent storage of area configuration
  - Area enable/disable functionality
  
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
  - `add_device_to_area` - Add device to area
  - `remove_device_from_area` - Remove device from area
  - `set_area_temperature` - Set target temperature
  - `enable_area` - Enable area
  - `disable_area` - Disable area
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
  - `coordinator.py` - Area data updates
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
