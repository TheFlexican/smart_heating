# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/).

## [Unreleased]

### Planned
- 🤖 Enhanced AI-driven heating optimization with multi-factor analysis
- 📊 Advanced energy analytics dashboard
- 🔗 MQTT auto-discovery for Zigbee2MQTT devices
- 🌡️ Extended weather integration (forecasts, humidity)
- 🔥 PID control for OpenTherm gateways
- 📱 Mobile app notifications
- 🏡 Multi-home support

## [0.3.4] - 2025-12-05

### ✨ Added - Enhanced Sensor Configuration

**Entity Selector UI**
- New `SensorConfigDialog` modal component for sensor configuration
- Dropdown populated from Home Assistant entities (auto-discovery)
- Filter entities by device_class for better UX
- Manual entity ID input fallback when no entities found
- Real-time entity state loading from HA

**Window Sensor Actions**
- Action configuration: Turn Off / Reduce Temperature / No Action
- Configurable temperature drop (1-10°C, 0.5°C steps)
- Action descriptions displayed in sensor list
- Dict-based storage with backward compatibility from string format

**Presence Sensor Actions**
- Separate away/home action configuration:
  - Away: Turn Off / Reduce Temperature / Set Eco Mode / No Action
  - Home: Increase Temperature / Set Comfort Mode / No Action
- Configurable temperature adjustments (away drop, home boost)
- Support for motion, occupancy sensors
- **Person/Device Tracker support** for HA presence detection

**Backend Enhancements**
- `area_manager.py`: Sensor storage migrated from `list[str]` to `list[dict]`
- Enhanced temperature calculation logic processing different sensor actions
- New API endpoint: `GET /api/smart_heating/entities/binary_sensor`
- Returns binary_sensor + person + device_tracker entities
- Person/device_tracker marked with virtual `device_class: presence`
- Action constants in `const.py`:
  - `WINDOW_ACTION_*`: TURN_OFF, REDUCE_TEMP, NONE
  - `PRESENCE_ACTION_*`: TURN_OFF, REDUCE_TEMP, SET_ECO, INCREASE_TEMP, SET_COMFORT, NONE

**Development Environment**
- Updated `setup.sh`: Added 7 new mock devices (24 total)
  - 3x TS0203 window/door sensors (Living Room, Kitchen, Bedroom)
  - 2x motion sensors (Living Room, Bedroom)
- Optimized setup flow: MQTT devices published before user action prompt
- Improved UX: All devices auto-discovered during MQTT integration setup

**Frontend Improvements**
- `AreaDetail.tsx`: Integrated sensor configuration dialog
- Enhanced sensor display with human-readable action descriptions
- TypeScript types: `WindowSensorConfig`, `PresenceSensorConfig`, `HassEntity`
- Material-UI v6 components for consistent UI

### 🐛 Fixed
- Backward compatibility: Old string-based sensor configs auto-migrated to dict format
- TypeScript unused imports removed for clean builds

### 📝 Changed
- `ha-config/configuration.yaml`: Removed debug logging (cleaner default config)
- `.github/copilot-instructions.md`: Updated development workflow notes

## [0.3.3] - 2025-12-05

### ✨ Added - User-Controlled History Data Management

**Configurable History Retention**
- User-configurable retention period (1-365 days, default: 30 days)
- Automatic hourly cleanup of expired data
- Immediate cleanup when retention period is reduced
- Persistent storage of retention settings
- Service: `smart_heating.set_history_retention`
- Configuration validation (1-365 days range)

**Enhanced History Querying**
- Preset time ranges: 6h, 12h, 24h, 3d, 7d, 30d
- Custom date/time range selection
- Query all available history within retention period
- Server-side filtering for efficiency
- No data aggregation - raw 5-minute resolution maintained

**Backend Improvements**
- `HistoryTracker` class enhancements:
  - Configurable retention via `set_retention_days()`/`get_retention_days()`
  - Scheduled cleanup task (runs every hour)
  - Flexible `get_history()` method supporting hours, custom ranges, or all data
  - Proper cleanup on integration unload
- New constants:
  - `DEFAULT_HISTORY_RETENTION_DAYS = 30`
  - `HISTORY_RECORD_INTERVAL_SECONDS = 300` (5 minutes)
- API endpoints:
  - `GET /api/smart_heating/history/config` - Get retention settings
  - `POST /api/smart_heating/history/config` - Update retention period
  - Enhanced `GET /api/smart_heating/areas/{id}/history` with query parameters

**Frontend Features**
- History Data Management panel in Settings tab:
  - Retention period slider (1-365 days)
  - Visual markers for common periods (1d, 7d, 30d, 90d, 180d, 365d)
  - Save button with confirmation
  - Info alert explaining automatic cleanup
  - Display of current recording interval (5 minutes)
- Enhanced HistoryChart component:
  - Added 30-day preset range
  - Custom date/time range picker
  - Start and end datetime inputs
  - Apply button for custom ranges
  - Improved time range selection UI
- API client functions:
  - `getHistoryConfig()` - Fetch retention settings
  - `setHistoryRetention(days)` - Update retention
  - `getHistory(areaId, options)` - Flexible history queries

**Service Definition**
- `set_history_retention` service in `services.yaml`:
  - Clear description and field labels
  - Number selector with validation (1-365 range)
  - Default value of 30 days
  - Unit of measurement display

**Technical Details**
- Recording interval: 5 minutes (300 seconds) - fixed, not configurable
- Data points stored: timestamp, current_temperature, target_temperature, state
- Storage location: `.storage/smart_heating_history`
- Cleanup frequency: Every 1 hour
- No data aggregation - all points kept at original resolution
- Automatic validation and error handling

**Benefits**
- User control over storage space vs historical data
- Flexible analysis periods for different needs
- Automatic maintenance - no manual cleanup required
- Better machine learning with longer retention
- Transparent operation with visible settings

## [0.2.0] - 2025-12-04

### ✨ Added - Adaptive Learning System

**Smart Night Boost with Machine Learning**
- Adaptive learning engine that predicts optimal heating start times based on your home's unique characteristics
- Automatic tracking of every heating cycle with timestamps, temperatures, and outdoor conditions
- Weather correlation using outdoor temperature sensors to learn how weather affects heating time
- Predictive scheduling based on historical data and current conditions
- Home Assistant Statistics API integration for efficient database storage (SQLite/MariaDB)
- Learning statistics tracked per area:
  - Heating rate (°C per minute) - how quickly your room warms up
  - Cooldown rate - how quickly it cools down
  - Outdoor temperature correlation - impact of weather on heating performance
  - Prediction accuracy metrics - continuous improvement tracking
- Configurable target wake-up time per area (e.g., "have bedroom at 21°C by 06:00")
- 10-minute safety margin for predictions to ensure target is reached on time
- Continuous learning improves accuracy over time with more data
- Minimal performance impact - predictions calculated once per minute

**Frontend UI for Adaptive Learning**
- New "Smart Night Boost" section in Settings tab:
  - Enable/disable toggle for adaptive learning per area
  - Time picker for target wake-up time with 24-hour format
  - Weather sensor entity selector (optional but recommended)
  - Informational panel explaining the learning system
  - Real-time configuration updates via service calls
- New "Learning" tab (6th tab in AreaDetail page):
  - Current learning status and configuration display
  - Step-by-step explanation of the learning process
  - API endpoint reference for developers
  - Helpful placeholder when feature is disabled
- User-friendly Material-UI components matching Home Assistant theme
- Instant feedback on configuration changes

**API Enhancements**
- New endpoint: `GET /api/smart_heating/areas/{area_id}/learning`
  - Returns comprehensive learning statistics for the specified area
  - Includes total heating events, average rates, correlations, and accuracy
  - JSON response format for easy integration
- Extended `set_night_boost` service with smart learning parameters:
  - `smart_night_boost_enabled` (boolean) - Enable/disable adaptive learning
  - `smart_night_boost_target_time` (string) - Desired wake-up time in HH:MM format
  - `weather_entity_id` (string) - Entity ID of outdoor temperature sensor
- Backward compatible with existing manual night boost configuration

**Technical Implementation**
- New `learning_engine.py` module (450+ lines of production code):
  - `HeatingEvent` dataclass for tracking individual heating cycles
  - `LearningEngine` class with full HA Statistics API integration
  - Methods: `async_start_heating_event()`, `async_end_heating_event()`, `async_predict_heating_time()`
  - Automatic event recording on heating start/end with all relevant data
  - Predictive algorithms using weighted historical averages
  - Weather correlation calculations with outdoor temperature
  - Statistics storage using HA's native recorder/statistics infrastructure
- Climate controller integration:
  - Tracks active heating events per area in `_area_heating_events` dict
  - Records outdoor temperature with each event via `_async_get_outdoor_temperature()` helper
  - Automatic event lifecycle management (start when heating begins, end when target reached)
  - Calls learning engine methods at appropriate times
- Scheduler integration:
  - New `_handle_smart_night_boost()` method for predictive scheduling
  - Calculates optimal heating start time based on learning data
  - 10-minute safety margin implementation
  - Falls back to default schedule if insufficient learning data
- Area model extensions:
  - Added `smart_night_boost_enabled: bool` field
  - Added `smart_night_boost_target_time: str` field (HH:MM format)
  - Added `weather_entity_id: str` field for outdoor sensor
  - All fields stored persistently in `.storage/smart_heating_storage`
- WebSocket coordinator updates:
  - Added "learning_engine" to coordinator filter list
  - Prevents learning engine from being mistaken for data coordinator
  - Ensures proper real-time updates

### 🐛 Fixed
- **Service Schema Validation**: Fixed "extra keys not allowed" error when enabling smart night boost
  - Extended `NIGHT_BOOST_SCHEMA` with `smart_night_boost_enabled`, `smart_night_boost_target_time`, `weather_entity_id`
  - Added optional `ATTR_NIGHT_BOOST_START_TIME` and `ATTR_NIGHT_BOOST_END_TIME` to schema
- **Method Signature Errors**: Fixed parameter name mismatches in learning engine calls
  - Changed climate controller to use correct parameter names (current_temp not start_temp/target_temp)
  - Fixed `async_start_heating_event()` and `async_end_heating_event()` signatures
- **WebSocket Coordinator Lookup**: Fixed "'LearningEngine' object has no attribute 'async_add_listener'" error
  - Added "learning_engine" to both coordinator filter lists in `websocket.py`
  - Now properly excludes: history, climate_controller, schedule_executor, learning_engine

### 🔧 Changed
- Extended `Area` class with 3 new fields for smart learning configuration
- Enhanced `async_handle_set_night_boost()` service handler to accept and process learning parameters
- Updated all API responses to include smart night boost configuration when enabled
- Climate controller constructor now accepts optional `learning_engine` parameter
- Scheduler constructor now accepts optional `learning_engine` parameter
- AreaDetail component structure expanded from 5 tabs to 6 tabs
- Service call payload extended with smart boost fields

### 📚 Documentation
- Updated README.md with comprehensive "Adaptive Learning System" section:
  - Detailed "How It Works" explanation with 3-step process
  - Configuration examples for both service calls and YAML
  - Learning statistics API documentation with sample responses
  - Integration with existing night boost feature
- Updated service documentation in services.yaml:
  - Added smart boost parameter descriptions
  - Included usage examples for both manual and smart modes
- Updated frontend README with Learning tab component details
- Added TypeScript type definitions:
  - `LearningStats` interface with all statistics fields
  - Extended `Area` interface with smart boost fields
- Added `getLearningStats()` API method to frontend client

### 🏆 Performance
- Efficient database storage via Home Assistant's Statistics API
  - Leverages HA's native SQLite or MariaDB backend
  - No additional file I/O overhead
  - Automatic cleanup of old statistics via HA's built-in retention policies
- Minimal performance impact:
  - Predictions calculated only once per minute (not every 30-second cycle)
  - Database queries optimized for historical data retrieval
  - Statistics aggregation handled by HA's recorder component
- Memory efficient:
  - Heating events tracked in-memory only during active heating
  - No long-term in-memory caching of historical data
  - Statistics API provides on-demand data access

### 🎯 User Experience
- Fully automatic after initial configuration - no manual intervention needed
- Progressive learning - works immediately with defaults, improves over time
- Transparent operation - users can see learning statistics via API or future UI
- Safe fallbacks - uses default schedule if learning data insufficient
- Compatible with existing features - works alongside manual night boost and schedules

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
- **Unified Schedule Format**: Schedule model now supports both legacy and new formats
  - Frontend format (day, start_time, end_time) matches backend storage
  - Automatic conversion between day names (Monday) and abbreviations (mon)
  - Backward compatible with old format (time, days)
  - Schedule creation from frontend now works seamlessly

### 🐛 Fixed
- **Device Status Display**: Fixed device status text in area cards
  - Thermostats now show "20.0°C → 22.0°C" only when heating (target > current)
  - Temperature sensors show "19.5°C" from temperature attribute
  - Valves show "45%" without redundant state value
  - All devices show "unavailable" instead of type name when no data
- **Scheduler Object Access**: Fixed scheduler to work with Schedule objects instead of dicts
  - Changed from `schedule["day"]` to `schedule.day`
  - Changed from `schedules` list to `schedules.values()` dict iteration
- **Thermostat Target Sync**: Climate controller now updates thermostat targets even when area is idle
  - Ensures TRV displays match scheduled temperatures
  - Passes target_temp to `_async_set_area_heating` in both heating and idle states

### 🔧 Changed
- **Temperature Conversion**: Added Fahrenheit to Celsius conversion in coordinator
  - Mock temperature sensors reporting 67.1°F now display as 19.5°C
  - Conversion applied before display and climate control logic

### 📚 Documentation
- Updated README with current v0.1.0 changelog and architecture section
- Added device control flow diagram explaining TRV behavior
- Updated schedule API documentation with new format
- Added note about mock devices vs real TRVs

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
