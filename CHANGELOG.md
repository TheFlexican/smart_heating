# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/).

## [Unreleased]

### ⚡ Performance

**Device Discovery Optimization (v0.5.8)**
- **Implemented device discovery caching**: Eliminated redundant discovery on every API call
  - Device list now cached after initial discovery
  - Cache persists across API calls to `/api/smart_heating/devices`
  - Use `/api/smart_heating/devices/refresh` to force re-discovery
  - Reduces Home Assistant entity registry queries from ~every 30 seconds to on-demand only
- **Performance impact**: 
  - Eliminates unnecessary CPU usage from repeated entity registry scans
  - Faster API response times (cached list returned instantly)
  - Discovery only happens on startup and manual refresh
- **User control**: Users can refresh device list via zones overview when needed

### 🐛 Fixed

**Critical Switch Control Bug Fix (v0.4.3)**
- **Fixed incomplete switch control logic**: Switches now explicitly stay ON when thermostats are actively heating
  - Previous code only logged intent to keep switches on but didn't execute the action
  - Added explicit `SERVICE_TURN_ON` call when `hvac_action == "heating"` detected
  - Prevents heat pumps/circulation pumps from turning off prematurely
  - Critical for systems with decimal temperature precision (e.g., Google Nest thermostats)
  - Example: Thermostat heating to 19.2°C while area target is 19.2°C → switch now correctly stays ON
- **Root cause**: Control flow allowed switch to turn off despite thermostats still heating
  - Old flow: Log message → fall through to `elif shutdown_switches_when_idle` → switch OFF
  - New flow: Log message → explicit `SERVICE_TURN_ON` → prevent fall-through

### 🔧 Code Quality

**Frontend Code Quality Improvements (v0.4.3)**
- **App.tsx** - Fixed 5/5 SonarQube issues:
  - Consolidated Material-UI imports
  - Renamed state variable `zones` → `areas` for consistency
  - Extracted `ZonesOverview` component to reduce cognitive complexity
  - Replaced `.flatMap()` with explicit `for...of` loops for better readability
  - All issues resolved (100%)
  
- **ZoneCard.tsx** - Fixed 3/3 SonarQube issues:
  - Reduced cognitive complexity by extracting helper functions:
    - `formatTemperature()` - Temperature formatting with null safety
    - `isValidState()` - State validation
    - `getThermostatStatus()` - Thermostat-specific status logic
    - `getTemperatureSensorStatus()` - Temperature sensor status logic
    - `getValveStatus()` - Valve status logic
    - `getGenericDeviceStatus()` - Generic device status logic
  - Replaced deprecated `secondaryTypographyProps` with `slotProps.secondary`
  - All issues resolved (100%)
  
- **AreaDetail.tsx** - Fixed 32/42 SonarQube issues (76% resolution):
  - Made all component props `Readonly<>` for immutability
  - Replaced deprecated `inputProps` / `InputLabelProps` with `slotProps`
  - Added null-safe optional chaining (`area?.target_temperature`)
  - Replaced nested ternaries with IIFE for complex conditional rendering
  - Renamed conflicting `setHistoryRetention` variables for clarity
  - Used `String.replaceAll()` for cleaner string replacements
  - Replaced `paragraph` prop with `sx={{ mb: 1 }}` for consistency
  - Used `Number.parseFloat()` / `Number.parseInt()` instead of global functions
  - Remaining 10 issues: Advanced patterns requiring broader refactoring

- **TypeScript Library Upgrade**:
  - Upgraded from ES2020 to ES2021 in `tsconfig.json`
  - Enables native `String.replaceAll()` support
  - Removes need for regex-based string replacement workarounds

### ✨ Added

**Automatic Preset Mode Switching (v0.4.2)**
- **Auto Preset Mode**: Automatically switch between preset modes based on presence detection
  - Enable/disable per area in Settings tab
  - Configure which preset to use when home (Home/Comfort/Activity)
  - Configure which preset to use when away (Away/Eco)
  - Works with both area-specific and global presence sensors
- **Smart Home Automation**: System responds to your presence
  - Automatically lowers temperature to away preset when you leave
  - Automatically restores home preset when you return
  - Integrates seamlessly with existing preset mode system
- **Full Logging**: All automatic preset changes logged in area logs
  - Track when and why preset mode changed
  - Includes presence state in log entries
  - Helps troubleshoot automation behavior

### 🔧 Code Quality

**SonarQube Analysis & Code Cleanup (v0.4.1)**
- **Fixed Critical Issues**:
  - Removed unreachable code in `area_manager.py`
  - Removed unused variables across codebase
  - Fixed bare `except` clause (now catches specific `Exception`)
  - Removed duplicate conditional branches
  - Fixed Python 3.9 compatibility (Optional type hints)
- **Code Organization**:
  - Extracted constants for duplicate string literals
  - Added `ERROR_UNKNOWN_ENDPOINT`, `ERROR_HISTORY_NOT_AVAILABLE`, `ERROR_VACATION_NOT_INITIALIZED` in `api.py`
  - Added `ERROR_AREA_NOT_FOUND` in service handlers
  - Added `ENDPOINT_PREFIX_AREAS` constant for consistent endpoint handling
- **Reduced Cognitive Complexity**:
  - Refactored `validate_schedule_data()` with helper methods `_validate_time_format()` and `_validate_days_list()`
  - Extracted device detection helpers in `api.py`: `_determine_mqtt_device_type()` and `_get_ha_area_name()`
  - Improved code readability without sacrificing functionality
- **Maintainability**: All fixable SonarQube issues resolved, remaining warnings are design choices or false positives

### ✨ Added

**Enhanced Schedule UI with Date Pickers & Multi-Day Selection (v0.4.0)**
- **Modern Date/Time Selectors**: Replaced error-prone time inputs with Material-UI DatePicker
  - Calendar-based date selection like vacation mode
  - Visual date selection for date-specific schedules
  - Improved user experience with validated time inputs
- **Multi-Day Selection**: Create schedules for multiple days at once
  - Quick selection buttons: Weekdays, Weekend, All Days
  - Checkbox interface for individual day selection
  - Preview of selected days before saving
  - Reduces repetitive schedule creation
- **Card-Based Layout**: Modern, collapsible schedule organization
  - Weekly recurring schedules grouped by day
  - Date-specific schedules in separate section
  - Expandable/collapsible cards for better overview
  - Visual distinction between recurring and one-time schedules
- **Date-Specific Schedules**: One-time schedules for specific dates
  - Perfect for holidays, special events, or temporary changes
  - Separate section with calendar icon
  - Formatted dates for easy readability
  - No impact on recurring weekly schedules
- **Backend Enhancements**: Full support for new schedule types
  - `days[]` array for multi-day recurring schedules
  - `date` field (YYYY-MM-DD) for date-specific schedules
  - Backward compatible with existing single-day schedules
  - Smart day format conversion (Monday/mon)
- **Translation Support**: Full English and Dutch translations
  - All new UI elements translated
  - Schedule type selection labels
  - Multi-day selection buttons
  - Date-specific schedule section headers

**Safety Sensor (Smoke/CO Detector) - Emergency Shutdown (v0.3.19)**
- **Safety Monitoring**: Automatic emergency heating shutdown on smoke/CO detection
  - Configure any Home Assistant binary sensor (smoke, carbon_monoxide, gas)
  - Real-time monitoring of sensor state changes
  - Immediate shutdown of ALL heating areas when danger detected
  - Prevents heating during fire or carbon monoxide emergencies
  - Enabled by default when sensor configured
  - Visual alerts in UI when safety alert is active

**Backend Implementation**
- New `SafetyMonitor` module for real-time sensor monitoring
- Area manager stores safety sensor configuration and alert state
- Emergency shutdown disables all areas immediately
- Configuration persists - areas stay disabled across HA restarts
- Services: `set_safety_sensor`, `remove_safety_sensor`
- API endpoints: GET/POST/DELETE `/api/smart_heating/safety_sensor`
- WebSocket events for safety alert notifications
- Comprehensive logging of safety events

**Frontend Implementation**
- New **Safety Tab** in Global Settings with Security icon (🔒)
- Configure smoke/CO detector with simple sensor picker
- Visual status display:
  - Green success alert when sensor configured and monitoring
  - Red error banner when safety alert is active
  - Warning alert when no sensor configured
- Shows current sensor details (entity ID, attribute, status)
- One-click add/remove safety sensor
- Real-time updates when sensor state changes

**Test Environment**
- Added MOES smoke detector (`binary_sensor.smoke_detector`)
- Added TuYa CO detector (`binary_sensor.co_detector`) 
- Test sensors included in `setup.sh` for development

**Translation Support**
- Full English and Dutch translations for safety feature
- UI text: `globalSettings.safety.*` translation keys
- Help text explaining emergency shutdown behavior
- Alert messages for active safety alerts

**Area-Specific Hysteresis Override (v0.3.18)**
- **Hysteresis Customization**: Areas can now override the global hysteresis setting
  - Toggle between global hysteresis (0.5°C default) or area-specific value
  - Range: 0.1°C to 2.0°C with 0.1°C increments
  - Particularly useful for floor heating systems (can use 0.1-0.3°C)
  - Help modal with detailed explanation of hysteresis and heating system types
  - Optimistic UI updates for instant feedback
  - State persists across page refreshes

**Global Settings Redesign (v0.3.18)**
- **Tabbed Navigation**: Reorganized Global Settings page with 4 tabs
  - 🌡️ **Temperature Tab**: Global preset temperatures (6 presets)
  - 👥 **Sensors Tab**: Global presence sensor configuration
  - 🏖️ **Vacation Tab**: Vacation mode settings (moved from top)
  - ⚙️ **Advanced Tab**: Hysteresis and future advanced settings
  - Material-UI tabs with icons for better visual navigation
  - Better organization and scalability for future features
  - Mobile-friendly responsive design with less scrolling

**Backend Implementation**
- Added `hysteresis_override` field to Area model (None = use global, float = custom)
- Climate controller uses area-specific hysteresis when set
- API endpoint: `POST /api/smart_heating/areas/{area_id}/hysteresis`
- WebSocket broadcasts hysteresis changes in real-time
- Coordinator includes hysteresis_override in area data export
- Area logger logs when heating blocked due to hysteresis

**Frontend Implementation**
- New **HysteresisSettings** component in Area Settings
  - Toggle switch: "Use global hysteresis" vs "Custom hysteresis"
  - Slider with visual markers (0.1°C, 0.5°C, 1.0°C, 2.0°C)
  - Help icon opens **HysteresisHelpModal** with detailed explanation
  - Real-time status display: "Using global: X°C" or "Custom: X°C"
- Updated **GlobalSettings** with tabbed layout
  - TabPanel component for content organization
  - Accessible with ARIA labels and keyboard navigation
  - Full EN/NL translation support for all tabs
- **HysteresisHelpModal** component explains:
  - What hysteresis is and why it matters
  - How different heating systems (radiator vs floor) need different values
  - Equipment protection (prevents short cycling damage)
  - Recommendations based on heating system type

### 📚 Documentation
- Created `docs/GLOBAL_SETTINGS_REDESIGN.md` - Architecture decision document
  - Explains Home Assistant best practices: Config Flow vs Custom UI
  - Documents tabbed UI design and future enhancement plans
  - Translation support details
- Updated translation files (EN/NL) with new keys:
  - `globalSettings.tabs.*` - Tab labels
  - `globalSettings.presets.*` - Preset tab content
  - `globalSettings.sensors.*` - Sensors tab content
  - `globalSettings.hysteresis.*` - Advanced tab content
  - `hysteresisHelp.*` - Help modal content

### 🐛 Fixed
- **WebSocket Error**: Fixed vacation_manager AttributeError in WebSocket coordinator lookup
  - Added "vacation_manager" to exclusion list in `websocket.py`
  - Prevents treating VacationManager as a coordinator
- **Console Cleanup**: Removed all debug console.log statements from production
  - Cleaned up App.tsx, AreaDetail.tsx, useWebSocket.ts
  - Production-ready console output

## [0.6.0] - 2025-12-07

### ✨ Added - Vacation Mode & Internationalization

**One-Click Vacation Management**
- **Vacation Mode**: Set all areas to Away preset for extended periods with a single click
  - Configure date range (start/end dates) for vacation period
  - Choose preset mode (Away, Eco, or Sleep) to apply to all areas
  - Frost protection override with configurable minimum temperature
  - Auto-disable when someone arrives home (person entity integration)
  - Visual banner on dashboard when vacation mode is active
  - Service calls for automation integration

**Backend Implementation**
- New `VacationManager` class manages vacation mode state and area overrides
- API endpoints: `GET/POST/DELETE /api/smart_heating/vacation_mode`
- Climate controller integration: automatically overrides area presets during vacation
- WebSocket events broadcast vacation mode changes in real-time
- Persistent storage in `.storage/smart_heating/vacation_mode.json`

**Frontend Implementation**
- New **VacationModeSettings** component in Global Settings page
  - Material-UI date pickers for start/end date selection
  - Preset mode dropdown (Away, Eco, Sleep)
  - Frost protection toggle with minimum temperature slider
  - Auto-disable toggle for person entity integration
  - Enable/Disable buttons with loading states
- **VacationModeBanner** component displays active vacation mode on dashboard
  - Shows current preset mode and end date
  - Quick disable button for easy exit
  - Auto-refreshes every 30 seconds

**Service Calls**
- `smart_heating.enable_vacation_mode` - Enable vacation mode
  - Fields: start_date, end_date, preset_mode, frost_protection_override, min_temperature, auto_disable
- `smart_heating.disable_vacation_mode` - Disable vacation mode

**Use Cases**
- Set entire home to energy-saving mode for holidays
- Protect against freezing pipes during winter vacations
  - Automatically resume normal heating when arriving home
  - Schedule vacation mode via automations

**Multi-Language Support**
- **Internationalization (i18n)**: Full multi-language user interface
  - Automatic language detection from Home Assistant settings
  - Supported languages: English (🇬🇧) and Dutch (🇳🇱)
  - Manual language switching via interface (🌍 button in header)
  - Full UI translation including:
    - Dashboard and zone cards
    - All settings pages
    - Forms and error messages
    - Vacation mode interface
    - Help texts and tooltips
  - i18next framework for robust translation management
  - Custom Home Assistant language detector
  - Browser language fallback mechanism

**i18n Implementation**
- Frontend: i18next + react-i18next + i18next-browser-languagedetector
- Translation files: `src/locales/{en,nl}/translation.json`
- 200+ translation keys organized by feature domain
- Custom language detector checks Home Assistant localStorage first
- Components updated with `useTranslation` hook

### 🔧 Dependencies
- Added `@mui/x-date-pickers` v7.22.2 for date selection UI
- Added `date-fns` v2.30.0 for date handling
- Added `i18next` v23.16.11 for internationalization
- Added `react-i18next` v15.1.3 for React integration
- Added `i18next-browser-languagedetector` v8.0.2 for automatic language detection

### 📚 Documentation
- Updated README.md with Vacation Mode feature description
- Updated README.md with Internationalization feature description
- Updated CHANGELOG.md with v0.6.0 release notes
- Added vacation mode services to services.yaml
- New README.nl.md: Full Dutch translation of documentation
- New CHANGELOG.nl.md: Dutch translation of changelog
- New docs/ folder structure for language-specific documentation
- E2E tests for vacation mode (9 tests in vacation-mode.spec.ts)
- Test documentation: VACATION_MODE_TEST_GUIDE.md

### 🧪 Testing
- E2E test suite for vacation mode with 9 comprehensive tests
- Test coverage: enable/disable flows, date validation, frost protection, UI states
- Tests verify: API integration, WebSocket updates, visual components## [0.5.7] - 2025-12-06

### 🐛 Critical Fixes

**Async File I/O**
- Fixed blocking file operations in area logger
  - All file reads/writes now use `hass.async_add_executor_job()`
  - Prevents event loop blocking warnings
  - Improved performance and responsiveness

**API Rate Limiting Protection**
- Temperature change detection already in place (v0.5.6+)
  - Only sets thermostat temperature if changed by ≥0.1°C
  - Prevents hitting Google Nest API rate limits
  - Cached last set temperature per thermostat

**Disabled Area Handling**
- Fixed disabled areas attempting to control devices
  - Disabled areas now skip ALL device control
  - No more `climate.turn_off` errors on MQTT devices
  - Devices maintain their current state
  - Temperature tracking continues normally

**Scheduler Cleanup**
- Removed unnecessary climate service call for preset modes
  - Preset mode set directly on area object
  - No more "Action climate.set_preset_mode not found" warnings
  - Cleaner, more efficient schedule activation

**Learning Engine Parameter Fix**
- Fixed `async_predict_heating_time()` parameter mismatch
  - Changed `start_temp` → `current_temp` 
  - Removed unused `outdoor_temp` parameter
  - Smart night boost predictions working correctly

## [0.5.6] - 2025-12-06

### 🚀 Performance Improvements - File-Based Logging

**Efficient Log Storage**
- **File-Based Architecture**: Replaced in-memory log storage with persistent file-based system
  - Separate `.jsonl` files per event type for efficient filtering
  - Storage location: `.storage/smart_heating/logs/{area_id}/{event_type}.jsonl`
  - Automatic log rotation at 1,000 entries per file
  - Logs persist across Home Assistant restarts
  - Reduced memory footprint - logs no longer kept in RAM

**Enhanced UI/UX**
- **Chip-Based Filtering**: Replaced dropdown with clickable filter chips
  - Color-coded chips for each event type (Temperature, Heating, Schedule, etc.)
  - Visual feedback: filled variant when active, outlined when inactive
  - One-click filtering for better usability
  - Matches event type badge colors for consistency

**Event Type Files**
- `temperature.jsonl` - Target temperature calculations and changes
- `heating.jsonl` - Heating state transitions with context
- `schedule.jsonl` - Schedule activation events
- `smart_boost.jsonl` - Smart night boost predictions and starts
- `sensor.jsonl` - Window and presence sensor state changes
- `mode.jsonl` - Manual override mode entries and exits

**Developer Benefits**
- Faster log queries with direct file reads
- Better scalability for long-running systems
- Easier debugging with persistent event history
- Clean separation of concerns by event type

### 📝 Enhanced Logging Detail

**Temperature Calculation Visibility**
- Added source tracking for temperature changes
  - Shows whether temperature comes from preset, schedule, or base target
  - Logs night boost calculations with before/after values
  - Includes current time and period checks for debugging

**Night Boost Transparency**
- Detailed logging when night boost applies
  - Shows base target temperature
  - Shows boost offset being added
  - Shows effective target temperature after boost
  - Includes current time and night period validation

## [0.5.5] - 2025-12-06

### 🐛 Fixed - Temperature Tracking

**Disabled Areas Now Track Temperature**
- Fixed issue where disabled areas stopped recording temperature history
  - Moved history recording to start of area loop (before enabled check)
  - All areas now maintain continuous temperature history regardless of state
  - Critical for reviewing heating patterns when re-enabling areas

**UI Cleanup**
- Removed redundant "Device Status" section from area Overview tab
  - Information already available in dedicated Devices tab
  - Cleaner, less cluttered Overview presentation

## [0.5.4] - 2025-12-06

### ✨ New Features - Development Logging System

**Per-Area Logging**
- **Dedicated Logs Tab**: New tab in area details showing comprehensive heating strategy logs
  - Displays all heating decisions and events for development visibility
  - Color-coded event type badges for easy identification
  - Chronological order (newest first) with timestamps
  - Detailed JSON data for each event showing exact parameters

**Event Types Tracked**
- **Temperature**: Target temperature calculations and effective temperature changes
- **Heating**: Heating state changes (on/off) with current/target temperatures
- **Schedule**: Schedule activations with preset modes or temperature values
- **Smart Boost**: Smart night boost predictions, start times, and duration estimates
- **Sensor**: Window and presence sensor state changes (open/closed, detected/not detected)
- **Mode**: Manual override mode entries and exits

**Filtering & Controls**
- Filter dropdown to view specific event types or all events
- Refresh button to reload logs on demand
- Limit of 500 entries per area (memory-efficient with deque)
- API endpoint: `GET /api/smart_heating/areas/{area_id}/logs?limit=N&type=EVENT_TYPE`

**Backend Implementation**
- New `AreaLogger` class with `log_event()`, `get_logs()`, `clear_logs()` methods
- Integrated throughout climate controller and scheduler
- Logs preserved in memory (development tool, not persisted to disk)

### 🐛 Fixed
- **Coordinator Lookup**: Fixed multiple `AttributeError` issues where `area_logger` was incorrectly identified as coordinator
  - Updated exclusion lists in `api.py` (17 occurrences) and `websocket.py` (2 occurrences)
  - WebSocket connections now work correctly without "unknown_error"
  - Manual override and other API endpoints no longer fail with attribute errors

### 🧪 Tests
- **New E2E Test Suite**: `area-logs.spec.ts` with 10 comprehensive tests
  - Tab visibility and navigation
  - Log display and structure
  - Filter functionality
  - Refresh button
  - Timestamp display
  - Color-coded event chips
  - JSON details display
- **Updated Navigation Tests**: Added verification for all 7 tabs including new Logs tab

### 📚 Documentation
- Updated README.md with Development Logs feature description
- Updated CHANGELOG.md with v0.5.4 release notes

## [0.5.3] - 2025-12-06

### ✨ Improved - Smart Night Boost & Schedule Integration

**Smart Night Boost Enhancements**
- **Schedule-Aware Targeting**: Smart night boost now reads morning schedules automatically
  - Detects first morning schedule (between 00:00-12:00) as target time
  - Falls back to configured `smart_night_boost_target_time` if no schedule exists
  - Calculates optimal heating start time based on predicted heating duration
  - Uses schedule's preset mode or temperature as target

**Night Boost Schedule Coordination**
- **Schedule Precedence**: Regular night boost no longer overlaps with active schedules
  - Night boost only applies when NO schedule is active
  - Allows schedules (e.g., "sleep" preset 22:00-06:30) to take precedence
  - Night boost pre-heats BEFORE morning schedule starts, not during
  - Better coordination between manual night boost and scheduled presets

**Example Use Case**
- Schedule: Saturday 22:00 - Sunday 07:00 (sleep preset)
- Smart night boost: Detects 07:00 schedule, predicts heating time needed
- Starts heating at optimal time (e.g., 06:30) to reach target by 07:00
- Regular night boost: Only active when outside schedule periods

## [0.5.2] - 2025-12-06

### 🐛 Fixed
- **WebSocket Schedule Bug**: Fixed schedules disappearing from frontend after WebSocket updates
  - Coordinator now includes schedules in area data sent via WebSocket
  - Previously, WebSocket updates overwrote area data without schedules
  - Schedule tab now shows schedules consistently even after real-time updates

## [0.5.1] - 2025-12-06

### 📚 Documentation
- **Complete Documentation Update**: Updated all documentation for v0.5.0 features
  - CHANGELOG.md: Added comprehensive v0.5.0 release notes
  - README.md: Documented schedule presets, cross-day schedules, and global presence
  - API examples updated for new endpoints and service calls
  - Feature descriptions aligned with actual implementation

### 🔧 Fixed
- Documentation was missing for v0.5.0 release features
- Copilot instructions updated with RULE #4: Update documentation before releases

## [0.5.0] - 2025-12-06

### ✨ Added - Schedule Presets, Cross-Day Schedules & Global Presence Sensors

**Schedule Preset Mode Selection**
- **Preset-Based Schedules**: Schedules can now set preset modes instead of fixed temperatures
  - Choose between "Fixed Temperature" or "Preset Mode" when creating/editing schedules
  - All standard preset modes available: Away, Eco, Comfort, Home, Sleep, Activity
  - Combines scheduling flexibility with preset temperature management
  - Respects global/custom preset configuration per area

**Cross-Day Schedule Support**
- **Midnight Crossover**: Schedules can now span across midnight
  - Example: Saturday 22:00 - Sunday 07:00 works correctly
  - Scheduler checks both current day and previous day for active schedules
  - End time before start time automatically indicates cross-day schedule
  - Proper validation ensures schedule is active during intended hours

**Global Presence Sensor Configuration**
- **Centralized Presence Management**: Configure presence sensors globally in Settings
  - Add/remove presence sensors that apply to all areas using them
  - Person entities, device trackers, motion sensors supported
  - Configure once, apply to multiple areas

**Per-Area Presence Configuration**
- **Toggle Control**: Each area can choose global or area-specific presence sensors
  - "Use Global Presence Sensors" toggle in Area Detail → Presence Configuration
  - Override with area-specific sensors when needed
  - Real-time switching between global and area-specific detection
  - Visual indication of which sensor set is active

**Climate Controller Integration**
- Climate controller respects `use_global_presence` flag
- Automatically selects correct sensor list (global vs area-specific)
- Presence detection behavior unchanged, just more flexible configuration

**API Enhancements**
- Added `/api/smart_heating/global_presence` GET/POST endpoints
- Added `/api/smart_heating/areas/{id}/presence_config` POST endpoint
- Enhanced schedule validation: accepts both `time` and `start_time` fields
- Area responses include `use_global_presence` and all `use_global_*` flags
- Schedule entries support optional `preset_mode` field

**Frontend Improvements**
- **Global Settings Page**: New "Global Presence Sensors" section
- **Area Detail Page**: New "Presence Configuration" section with toggle
- **Schedule Editor**: Mode selector toggle between temperature and preset modes
- **Alphabetical Sorting**: Area cards in zones overview now sorted alphabetically (prevents dynamic reordering)

**Affected Files:**
- Backend: `area_manager.py`, `scheduler.py`, `api.py`, `climate_controller.py`
- Frontend: `types.ts`, `api.ts`, `ScheduleEditor.tsx`, `GlobalSettings.tsx`, `AreaDetail.tsx`, `ZoneList.tsx`
- Configuration: `manifest.json` (version bump to 0.5.0)

### 🐛 Fixed
- Schedule API validation failing on missing `time` field (now accepts `time` or `start_time`)
- Toggle switch not responding due to missing `use_global_presence` in API responses
- Climate controller not using global presence sensors even when flag was set
- Area cards dynamically reordering in zones overview due to WebSocket updates

### 🔧 Changed
- Area cards now maintain alphabetical order regardless of state updates
- Schedule data model enhanced with optional `preset_mode` field
- Area data model includes `use_global_presence` flag with persistence

### ✨ Added - Global Preset Temperatures (v0.4.3)

**Global Preset System**
- **Global Temperature Defaults**: Configure default temperatures for all preset modes in one place
  - Away, Eco, Comfort, Home, Sleep, Activity presets
  - Set once in Settings → Global Presets, apply everywhere
  - Slider controls with 0.1°C precision (5°C - 30°C range)
  - Automatic debouncing (500ms) to prevent excessive saves

**Per-Area Preset Customization**
- **Toggle Control**: Choose between global defaults or custom temperatures for each preset per area
  - Convenient toggle switches: "Use Global" ↔ "Use Custom"
  - Visual indication of which temperature is active
  - Changes apply immediately via WebSocket updates
  - Settings persist across restarts

**Presence Detection Improvements**
- **Simplified Behavior**: Presence sensors now control preset mode switching only
  - Away when nobody home → Switches to "Away" preset
  - Home when someone arrives → Switches to "Home" preset
  - No more manual temperature adjustments (+1°C / -1°C)
  - Clean, predictable behavior using your configured preset temperatures

**API & Backend**
- Added `/api/smart_heating/areas` endpoint returns `use_global_*` flags
- Added `set_area_preset_config()` endpoint for updating flags
- Global presets stored in `AreaManager` with persistence
- Coordinator includes effective temperature calculation
- Area effective temperature respects global/custom preset selection

**Frontend**
- Settings page: Global Presets configuration with debounced sliders
- Area Detail page: Preset Temperature Configuration section with toggle switches
- Presence sensor dialog: Simplified to show preset mode control explanation
- Real-time updates via WebSocket when toggling between global/custom
- Material-UI Switch components for intuitive UX

**Affected Files:**
- Backend: `area_manager.py`, `api.py`, `coordinator.py`
- Frontend: `Settings.tsx`, `AreaDetail.tsx`, `SensorConfigDialog.tsx`, `types.ts`, `api.ts`
- Documentation: `README.md`, `CHANGELOG.md`

### Planned
- 🤖 Enhanced AI-driven heating optimization with multi-factor analysis
- 📊 Advanced energy analytics dashboard
- 🌡️ Extended weather integration (forecasts, humidity)
- 🔥 PID control for OpenTherm gateways
- 📱 Mobile app notifications
- 🏡 Multi-home support

## [0.4.2] - 2025-01-06

### ✨ Added - Per-Area Switch/Pump Control

**Smart Switch Control Setting**
- **New Area Setting**: `shutdown_switches_when_idle` - Control whether switches/pumps turn off when area not heating
- **Default Behavior**: Enabled (true) - switches automatically turn off when heating stops
- **Optional Always-On Mode**: Disable setting to keep pumps running continuously regardless of heating demand
- **Use Cases**: 
  - Enable for energy efficiency (pumps off when not needed)
  - Disable for systems requiring continuous circulation
  - Perfect for zone valves that need constant pump pressure

**Implementation:**
- Added `shutdown_switches_when_idle` property to Area class
- Persistence: Saved/loaded from storage like other area settings
- Climate controller checks setting before turning off switches
- Frontend UI: Toggle switch in Area Settings → Switch/Pump Control section
- API endpoint: `POST /api/smart_heating/areas/{id}/switch_shutdown`
- Detailed logging when switches kept on vs turned off

**Frontend UI:**
- New "Switch/Pump Control" section in area detail settings
- Toggle: "Shutdown switches/pumps when not heating"
- Badge shows current state: "Auto Off" or "Always On"
- Helpful description explaining behavior

**Affected Files:**
- `smart_heating/area_manager.py`: Added property and persistence
- `smart_heating/climate_controller.py`: Conditional switch control logic
- `smart_heating/api.py`: New endpoint for updating setting
- `smart_heating/frontend/src/types.ts`: TypeScript interface update
- `smart_heating/frontend/src/api.ts`: API function
- `smart_heating/frontend/src/pages/AreaDetail.tsx`: UI controls

## [0.4.1] - 2025-01-06

### 🐛 Fixed - Manual Override Persistence

**Bug Fix**
- **Fixed**: Manual override mode now correctly persists across Home Assistant restarts
- **Issue**: While `manual_override` flag was saved to storage, it wasn't being loaded during startup
- **Solution**: Added `manual_override` to both `Area.to_dict()` and `Area.from_dict()` methods in `area_manager.py`
- **Impact**: Users' manual thermostat adjustments are now preserved even after HA restarts/updates
- **Affected Files**:
  - `smart_heating/area_manager.py`: Added persistence for `manual_override` flag

## [0.4.0] - 2025-01-06

### ✨ Added - Manual Override Mode & Real-Time Updates

**Manual Override Mode**
- **Automatic Detection**: System detects when thermostat is adjusted outside the app (e.g., directly on Google Nest)
- **State Change Listeners**: Real-time monitoring of thermostat temperature changes via Home Assistant state events
- **Debouncing**: 2-second delay to handle rapid temperature dial adjustments (prevents flood of updates)
- **Manual Override Flag**: Area enters "MANUAL" mode when external adjustment detected
  - Orange "MANUAL" badge displayed on area card
  - App stops automatic temperature control for that area
  - Target temperature updated to match external setting
  - Manual override persists across restarts (saved to storage)
- **Clear Override**: Manual mode automatically cleared when user adjusts temperature via app
- **Backend Components**:
  - `coordinator.py`: State change listeners with debounce logic
  - `area_manager.py`: Added `manual_override` property to Area class
  - `climate_controller.py`: Skips areas in manual override mode
  - `api.py`: Clears manual override on temperature API calls

**Real-Time WebSocket Updates**
- **Frontend Updates**: Area cards update within 2-3 seconds of external thermostat changes
- **WebSocket Message Format**: Fixed to properly handle `result` type messages with area data
- **Object-to-Array Conversion**: Backend sends areas as object (dict), frontend converts to array
- **State Preservation**: Hidden area state preserved during WebSocket updates
- **Forced Coordinator Refresh**: Immediate data update after debounce completes (not rate-limited)

**Data Completeness Fixes**
- **Area ID**: Added `id` property to coordinator area data (fixes navigation after WebSocket updates)
- **Device Names**: Added `name` property with `friendly_name` from Home Assistant (fixes device display)
- **Hidden Property**: Backend now includes `hidden` flag in coordinator data (persistent across updates)

### 🔧 Fixed
- Area cards not clickable after WebSocket updates (missing `id` property)
- Device names showing entity IDs instead of friendly names after updates
- Hidden areas becoming visible after WebSocket updates
- Frontend not detecting WebSocket area updates (message type mismatch)
- Temperature display not updating when thermostat changed externally
- Coordinator data missing key properties (`id`, `name`, `hidden`)

### 🧪 Testing
- Created `manual-override.spec.ts` with 5 E2E tests for manual override functionality
- Tests verify: manual mode detection, clearing, persistence, WebSocket updates
- All existing tests still pass (86/90 tests passing)

### 📚 Documentation
- Updated ARCHITECTURE.md with manual override system flow
- Updated DEVELOPER.md with state listener implementation details
- Added debounce configuration constants to documentation

## [0.3.16] - 2025-12-06

### ✨ Added - Devices Tab in Area Detail

**Devices Tab Interface**
- **Assigned Devices Section**: Shows all devices currently linked to the area
  - Remove button (🗑️) for each device
  - Real-time device status (temperature, heating state, device type)
  - Device count in section header
- **Available Devices Section**: Shows unassigned devices from the same HA area
  - Add button for each available device
  - Smart filtering by HA area ID OR device name matching
  - Supports both devices with HA area assignment and MQTT devices without area
  - Device count in section header
- **Smart Filtering Logic**:
  - Method 1: Direct HA `area_id` match (for devices assigned to HA areas)
  - Method 2: Name-based matching (e.g., "Kitchen Thermostat" for "Kitchen" area)
  - Excludes devices already assigned to the area
- **Tab Navigation**: Devices tab is 2nd tab (index 1) in area detail page
- **Backward Compatible**: Works with existing MQTT device system

**E2E Test Coverage**
- Created `device-management.spec.ts` with 15 comprehensive tests (all passing ✅)
- Tests cover:
  - Devices tab navigation and visibility
  - Assigned devices section display and remove functionality
  - Available devices section display and add functionality
  - Smart filtering (HA area + name matching)
  - Add/Remove operations and state updates
  - Drag & drop preservation on main page

### 🔧 Changed
- Extended Device interface with `entity_id`, `area_id`, and `domain` properties
- Updated tab indices: Devices (1), Schedule (2), History (3), Settings (4), Learning (5)
- Devices tab is now primary device management method (drag & drop still available)

### 📚 Documentation
- Updated `.github/copilot-instructions.md` with Devices tab feature description
- Updated E2E test documentation with device management test suite details

## [0.3.15] - 2025-12-06

### ✨ Added - Universal Device Discovery & Enhanced Device Management

**Universal Device Discovery**
- **ALL Home Assistant climate entities** now discovered (not just MQTT)
- Support for Google Nest, Ecobee, generic_thermostat, and ANY climate integration
- Discover climate, sensor, switch, and number entities from ALL platforms
- Platform-agnostic device detection with smart filtering
- Expanded device type detection:
  - Thermostats from ANY integration
  - Temperature sensors with flexible matching (device_class, unit_of_measurement, entity naming)
  - Heating-related switches (pumps, relays, floor heating)
  - Valve/TRV position controls

**Enhanced Area Device Management**
- **Location-based filtering** via dropdown in Devices tab
- Filter devices by:
  - All Locations (show all available devices)
  - No Location Assigned (unassigned devices)
  - Specific HA areas (Badkamer, Woonkamer, Slaapkamer, etc.)
- **Direct device assignment** from Area Detail page
- Add devices with single click (+ icon button)
- Remove devices with single click (- icon button)
- Real-time device count per location filter
- Visual location chips showing HA area assignment
- Improved UX: No need to return to main page for device management

**Backend Improvements**
- `api.py`: Removed MQTT-only filter (`platform == "mqtt"`)
- Device discovery now queries all entity domains: `["climate", "sensor", "number", "switch"]`
- Enhanced temperature sensor detection with multiple fallback methods
- Smart switch filtering for heating-related devices
- Maintained hidden area filtering (3-method approach)

**Frontend Enhancements**
- `AreaDetail.tsx`: New location filter dropdown with Material-UI Select
- `AddCircleOutlineIcon` for adding devices (primary color)
- `RemoveCircleOutlineIcon` for removing devices (error color)
- Device list shows HA area as Chip component
- Empty state messages for filtered device lists
- Improved device counter in filter options

### 🐛 Fixed
- Google Nest and other non-MQTT thermostats now properly discovered
- Device discovery no longer limited to single integration platform
- Temperature sensor detection more reliable across different manufacturers

### 📝 Changed
- Device discovery significantly expanded (from ~19 to potentially 100+ devices)
- Simplified device assignment workflow (direct from area page)
- Better device organization with location-based filtering

### 🔧 Technical Details
- Discovery method now platform-agnostic
- Backward compatible with existing MQTT device assignments
- No breaking changes to existing configurations
- Filtering logic preserved for hidden areas

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
