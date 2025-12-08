# Architecture Overview

Smart Heating is a Home Assistant integration with a modern web-based interface for managing multi-area heating systems.

## Code Quality & Standards

**SonarQube Analysis** (v0.4.1+)

The codebase undergoes regular SonarQube analysis to maintain high code quality standards:

- **All critical issues resolved**: No unreachable code, unused variables, or bare except clauses
- **Constants extracted**: Duplicate string literals replaced with named constants for maintainability
- **Helper methods**: Complex functions refactored with extracted helper methods to reduce cognitive complexity
- **Type safety**: Python 3.9+ compatible type hints using `Optional[]` syntax
- **Remaining warnings**: Design choices (async interfaces) or false positives (Home Assistant imports)

**Key Code Patterns:**
- `ERROR_*` constants for consistent error messages across API endpoints
- `ENDPOINT_PREFIX_*` constants for maintainable routing
- Helper methods like `_validate_time_format()`, `_determine_mqtt_device_type()` for code reuse
- Comprehensive validation with clear error messages

## High-Level Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                     Home Assistant                          │
│  ┌────────────────────────────────────────────────────────┐ │
│  │         Smart Heating Integration                      │ │
│  │                                                        │ │
│  │  ┌──────────────┐  ┌──────────────┐  ┌─────────────┐   │ │
│  │  │ Area Manager │  │ Coordinator  │  │  Platforms  │   │ │
│  │  │   (Storage)  │  │  (30s poll)  │  │ (Entities)  │   │ │
│  │  └──────┬───────┘  └──────┬───────┘  └─────────────┘   │ │
│  │         │                 │                            │ │
│  │  ┌──────┴─────────────────┴──────-────────────────┐    │ │
│  │  │   REST API (api.py + api_handlers/)            │    │ │
│  │  │   WebSocket API (websocket.py)                 │    │ │
│  │  │   Service Handlers (ha_services/)              │    │ │
│  │  │   (/api/smart_heating/*)                       │    │ │
│  │  │                                                │    │ │
│  │  └───────────────────────┬────────────────────────┘    │ │
│  │                          │                             │ │
│  │  ┌───────────────────────┴──────────────────────────┐  │ │
│  │  │                                                  │  │ │
│  │  │         Static File Server                       │  │ │
│  │  │    (/smart_heating/* → frontend/dist)            │  │ │
│  │  │                                                  │  │ │
│  │  └─────────────────────┬─--─────────────────────────┘  │ │
│  └────────────────────────┼───--──────────────────────────┘ │
└───────────────────────────┼─────────────────────────────────┘
                            │
                            │ HTTP/WebSocket
                            ▼
             ┌──────────────────────────────┐
             │     React Frontend (SPA)     │
             │                              │
             │  - Area Management UI        │
             │  - Device Panel              │
             │  - Real-time Updates         │
             │  - Material-UI Components    │
             └──────────────────────────────┘
                            │
                            │ MQTT (via HA)
                            ▼
             ┌──────────────────────────────┐
             │       Zigbee2MQTT            │
             │                              │
             │  - Thermostats               │
             │  - Temperature Sensors       │
             │  - OpenTherm Gateways        │
             │  - Radiator Valves           │
             └──────────────────────────────┘
```

## Backend Components

### 1. Area Manager (`area_manager.py`)

Core business logic for managing heating areas.

**Responsibilities:**
- Area CRUD operations
- Device assignment to areas
- Schedule management (Schedule class)
- Night boost configuration per area
- Temperature control and effective target calculation
- Area enable/disable
- Persistent storage (via HA storage API)

**Data Model:**
```python
Area:
  - area_id: str
  - name: str
  - target_temperature: float
  - enabled: bool
  - hidden: bool
  - manual_override: bool  # v0.4.0+ - Enters manual mode when thermostat changed externally
  - devices: Dict[str, Device]
  - schedules: Dict[str, Schedule]
  - state: ZoneState (heating/idle/off/manual)
  - night_boost_enabled: bool
  - night_boost_offset: float
  - current_temperature: Optional[float]

Schedule:
  - schedule_id: str
  - time: str (HH:MM) [legacy]
  - day: str (Monday, Tuesday, etc.) [legacy - single day]
  - days: List[str] (Monday, Tuesday, etc.) [v0.4.0+ - multi-day selection]
  - date: str (YYYY-MM-DD) [v0.4.0+ - date-specific schedules]
  - start_time: str (HH:MM)
  - end_time: str (HH:MM)
  - temperature: float
  - preset_mode: str (optional - away, eco, comfort, home, sleep, activity)
  - enabled: bool

Schedule Types (v0.4.0+):
  - Weekly Recurring: Uses 'days' array for multi-day schedules
  - Date-Specific: Uses 'date' field for one-time schedules (holidays, events)
  - Legacy: Single 'day' field (backward compatible)

Device:
  - id: str
  - type: str (thermostat/temperature_sensor/switch/valve/opentherm_gateway)
  - mqtt_topic: Optional[str]
  - entity_id: Optional[str]
```

**Supported Device Types:**
- **thermostat** - Climate entities from ANY Home Assistant integration
  - Google Nest, Ecobee, generic_thermostat, MQTT/Zigbee2MQTT, Z-Wave, etc.
  - Platform-agnostic: Works with climate entities from any source
  - No integration-specific code required
- **temperature_sensor** - External sensors for area monitoring
  - Flexible detection: device_class, unit_of_measurement, or entity naming
  - Works with sensor entities from ANY platform
- **switch** - Per-area circulation pumps/relays
  - Smart filtering for heating-related switches
- **valve** - TRVs with position or temperature control
  - Dynamic capability detection at runtime
- **opentherm_gateway** - Global boiler control (shared across areas)

**Key Methods:**
- `get_effective_target_temperature()` - Calculates target with schedules + night boost
- `get_active_schedule_temperature()` - Finds current active schedule
- `add_schedule()` / `remove_schedule()` - Schedule management
- `get_switches()` - Get switch devices in area (NEW)
- `get_valves()` - Get valve devices in area (NEW)
- `set_opentherm_gateway()` - Configure global OpenTherm gateway (NEW)
- `set_trv_temperatures()` - Set TRV heating/idle temperatures (NEW)

### 2. Coordinator (`coordinator.py`)

Data update coordinator using Home Assistant's `DataUpdateCoordinator`.

**Responsibilities:**
- Fetch area data every 30 seconds
- Broadcast updates to entities
- Handle refresh requests
- **Monitor thermostat state changes in real-time** (v0.4.0+)
- **Automatic manual override detection** (v0.4.0+)

**Manual Override System** (v0.4.0+):

Detects when thermostats are adjusted outside the Smart Heating app and automatically enters manual override mode.

**Components:**
1. **State Change Listeners** (`async_setup()`):
   - Registers `async_track_state_change_event` for all climate entities
   - Monitors `temperature` and `hvac_action` attribute changes
   - Filters out app-initiated changes via `_ignore_next_state_change` flag

2. **Debouncing** (`_handle_state_change()`):
   - 2-second delay (configurable via `MANUAL_TEMP_CHANGE_DEBOUNCE`)
   - Prevents flood of updates from rapid dial adjustments (e.g., Google Nest)
   - Cancels previous pending updates when new changes detected

3. **Manual Override Activation** (`debounced_temp_update()`):
   - Sets `area.manual_override = True`
   - Updates `area.target_temperature` to match thermostat
   - Persists state via `await self.area_manager.async_save()`
   - Forces coordinator refresh for immediate UI update

4. **Persistence** (v0.4.1+):
   - `manual_override` flag saved in `Area.to_dict()`
   - Restored in `Area.from_dict()` during startup
   - Survives Home Assistant restarts

**Clearing Manual Override:**
- Automatically cleared when temperature set via app API
- API sets `area.manual_override = False` on temperature changes
- Climate controller skips areas in manual override mode

**Flow:**
```
User adjusts thermostat externally (e.g., Google Nest dial)
  ↓
State change event fired by Home Assistant
  ↓
_handle_state_change() receives event
  ↓
Wait 2 seconds (debounce)
  ↓
debounced_temp_update() executes:
  - Set manual_override = True
  - Update target_temperature
  - Save to storage
  - Force coordinator refresh
  ↓
WebSocket broadcasts update to frontend
  ↓
UI shows orange "MANUAL" badge (2-3 second delay)
  ↓
Climate controller skips automatic control
```

### 3. Climate Controller (`climate_controller.py`)

Automated heating control engine with multi-device support.

**Responsibilities:**
- Runs every 30 seconds (via async_track_time_interval)
- Updates area temperatures from sensors (with F→C conversion)
- Controls heating based on hysteresis logic
- Records temperature history every 5 minutes (10 cycles)
- Integrates with AreaManager for effective target temperature
- Updates thermostat targets even when area is idle (syncs with schedules)
- **Controls all device types in coordinated fashion (NEW)**

**Device Control Methods:**

1. **_async_control_thermostats()** - Standard thermostat control
   - Sets `climate.*` entities to target temperature
   - Works with traditional TRVs and smart thermostats

2. **_async_control_switches()** - Intelligent binary switch control
   - Monitors thermostat `hvac_action` attribute to detect actual heating state
   - Keeps switches ON when thermostats are actively heating (even when area target reached)
   - Handles edge cases: decimal temperature differences, thermostat lag
   - Respects `shutdown_switches_when_idle` setting per area
   - Perfect for circulation pumps, zone valves, relays
   - Example: Google Nest thermostat heating to 19.2°C while area target is 19.2°C → switch stays ON until hvac_action changes to "idle"

3. **_async_control_valves()** - Intelligent valve control with dynamic capability detection
   
   **Capability Detection** (`_get_valve_capability()`):
   - **100% runtime detection** - NO hardcoded device models
   - Queries entity attributes and domain to determine control mode
   - Works with ANY valve from any manufacturer (TuYa, Danfoss, Eurotronic, Sonoff, etc.)
   - Caches results to avoid repeated queries
   - Returns:
     - `supports_position`: Boolean for position control capability
     - `supports_temperature`: Boolean for temperature control capability
     - `position_min/max`: Min/max values for position entities
     - `entity_domain`: Entity type (number, climate, etc.)
   
   **Control Modes**:
   - **Position mode** (`number.*` entities or `climate.*` with position attribute):
     - Queries `min`/`max` attributes from entity
     - Sets to max when heating, min when idle
     - Example: Any valve with position control → 100% open / 0% closed
   - **Temperature mode** (fallback for `climate.*` without position):
     - For any TRV that only supports temperature control
     - Sets to `target_temp + offset` when heating (ensures valve opens)
     - Sets to `trv_idle_temp` (default 10°C) when idle (closes valve)
     - Example: Area target 21°C → TRV set to 31°C when heating, 10°C when idle
   - Works with any external temperature sensors

4. **_async_control_opentherm_gateway()** - Global boiler control
   - Aggregates heating demands across ALL areas
   - Tracks which areas are actively heating
   - Calculates maximum target temperature across all heating areas
   - Boiler control:
     - **ON**: When any area needs heat, setpoint = `max(area_targets) + 20°C`
     - **OFF**: When no areas need heat
   - Shared resource (one gateway serves all areas)

**Control Flow:**
```
Every 30 seconds:
1. Update all area temperatures from sensors
2. For each area:
   - Decide if heating needed (hysteresis logic)
   - Control thermostats → set target temperature
   - Control switches → on/off based on heating state
   - Control valves → position or temperature based on capability
   - Track if area is heating + its target temp
3. After all areas processed:
   - Aggregate heating demands
   - Control OpenTherm gateway → boiler on/off + optimal setpoint
```

**Hysteresis Logic:**
```python
# Hysteresis control (default 0.5°C)
should_heat = current_temp < (target_temp - hysteresis)
should_stop = current_temp >= target_temp

# Target includes schedules + night boost
target_temp = area.get_effective_target_temperature()
```

### 4. Schedule Executor (`scheduler.py`)

Time-based temperature control.

**Responsibilities:**
- Runs every 1 minute (via async_track_time_interval)
- Checks all active schedules for current day/time
- Applies temperature changes when schedules activate
- Handles midnight-crossing schedules
- Prevents duplicate temperature sets (tracks last applied)

**Schedule Matching:**
- Day-of-week checking (mon, tue, wed, thu, fri, sat, sun)
- Time range validation (handles 22:00-06:00 crossing midnight)
- Priority: Latest schedule time wins

### 5. History Tracker (`history.py`)

Temperature logging and retention.

**Responsibilities:**
- Records temperature every 5 minutes
- Stores: current_temp, target_temp, state, timestamp
- 7-day automatic retention
- Persistent storage in `.storage/smart_heating_history`
- Automatic cleanup of old entries
- 1000 entry limit per area

**Storage:**
```json
{
  "history": {
    "living_room": [
      {
        "timestamp": "2025-12-04T10:00:00",
        "current_temperature": 20.5,
        "target_temperature": 21.0,
        "state": "heating"
      }
    ]
  }
}
```

### 6. Safety Monitor (`safety_monitor.py`)

Emergency heating shutdown on safety sensor alerts.

**Responsibilities:**
- Monitors configured safety sensors (smoke, CO detectors)
- Triggers emergency shutdown when alert detected
- Disables all heating areas immediately
- Fires `smart_heating_safety_alert` event
- Persists disabled state (survives restarts)

**Performance:**
- **Event-driven architecture** - Zero polling overhead
- Uses `async_track_state_change_event()` for Home Assistant event bus subscription
- Callback triggered only on actual sensor state changes
- CPU usage: 0% idle, ~1-5ms per state change event
- Memory: Negligible (single event listener registration)

**Configuration:**
- Global setting configured via Area Manager
- Sensor ID: Entity to monitor (e.g., `binary_sensor.smoke_detector`)
- Attribute: Specific attribute to check (e.g., `state`)
- Alert value: Value indicating danger (e.g., `on`)
- Enabled: Default true, can be disabled for testing

**Control Flow:**
```
1. SafetyMonitor setup with configured sensor
2. async_track_state_change_event registers listener (event-driven, no polling)
3. On sensor state change (instant notification from HA event bus):
   - Check if alert value matches configured value
   - If match: trigger _emergency_shutdown()
     - Disable all areas via Area Manager
     - Fire event: smart_heating_safety_alert
     - Request coordinator refresh for UI update
     - Log error with sensor details
4. User must manually re-enable areas after resolving danger
   - Re-enabling any area clears the alert state
```

**Storage (via Area Manager):**
```json
{
  "safety_sensor_id": "binary_sensor.smoke_detector",
  "safety_sensor_attribute": "state",
  "safety_sensor_alert_value": "on",
  "safety_sensor_enabled": true
}
```

**Integration:**
- Configured via Global Settings → Safety tab in frontend
- Services: `set_safety_sensor`, `remove_safety_sensor`
- API endpoints: GET/POST/DELETE `/api/smart_heating/safety_sensor`
- WebSocket events: Real-time alert updates via coordinator refresh

### 7. Vacation Manager (`vacation_manager.py`)

Automated away-from-home heating control.

**Responsibilities:**
- Manages vacation mode schedules with start/end dates
- Automatically enables/disables vacation mode at scheduled times
- Stores all areas' enabled states before vacation starts
- Disables all areas during vacation (energy saving)
- Restores original area states when vacation ends
- Handles Home Assistant restarts during vacation periods

**Vacation Mode States:**
- **Inactive**: No vacation scheduled or vacation ended
- **Active**: Currently in vacation period (all areas disabled)
- **Scheduled**: Vacation configured for future date

**Control Flow:**
```
1. User sets vacation dates via Global Settings → Vacation tab
2. Vacation Manager checks every hour (async_track_time_interval)
3. When start time reached:
   - Save current enabled state of all areas
   - Disable all areas
   - Set vacation_mode_active = true
   - Fire event: smart_heating_vacation_started
4. When end time reached:
   - Restore all areas to original states
   - Set vacation_mode_active = false
   - Fire event: smart_heating_vacation_ended
5. On HA restart during vacation:
   - Detects active vacation period
   - Areas remain disabled (state persisted)
```

**Storage (via Area Manager):**
```json
{
  "vacation_mode_start": "2024-12-20T15:00:00",
  "vacation_mode_end": "2024-12-27T18:00:00",
  "vacation_mode_active": true,
  "vacation_original_states": {
    "living_room": true,
    "bedroom": true,
    "bathroom": false
  }
}
```

**Integration:**
- Configured via Global Settings → Vacation tab in frontend
- Services: `set_vacation_mode`, `cancel_vacation_mode`
- API endpoints: GET/POST/DELETE `/api/smart_heating/vacation`
- WebSocket events: `vacation_changed`, `smart_heating_vacation_started`, `smart_heating_vacation_ended`

### 8. Platforms

#### Climate Platform (`climate.py`)
Creates one `climate.area_<name>` entity per area.

**Features:**
- HVAC modes: HEAT, OFF
- Temperature control (5-30°C, 0.5° steps)
- Current area state
- Area attributes (devices, enabled)

#### Switch Platform (`switch.py`)
Creates one `switch.area_<name>_control` entity per area.

**Features:**
- Simple on/off control
- Tied to area.enabled property

#### Sensor Platform (`sensor.py`)
Creates `sensor.smart_heating_status` entity.

**Features:**
- Overall system status
- Area count
- Active areas count

### 9. REST API (`api.py`)

HTTP API using `HomeAssistantView` for frontend communication.

**Endpoints:**

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/smart_heating/areas` | Get all areas with night boost data |
| GET | `/api/smart_heating/areas/{id}` | Get specific area |
| POST | `/api/smart_heating/areas` | Create area |
| DELETE | `/api/smart_heating/areas/{id}` | Delete area |
| POST | `/api/smart_heating/areas/{id}/devices` | Add device to area |
| DELETE | `/api/smart_heating/areas/{id}/devices/{device_id}` | Remove device |
| POST | `/api/smart_heating/areas/{id}/schedules` | Add schedule to area |
| DELETE | `/api/smart_heating/areas/{id}/schedules/{schedule_id}` | Remove schedule |
| POST | `/api/smart_heating/areas/{id}/temperature` | Set temperature |
| POST | `/api/smart_heating/areas/{id}/enable` | Enable area |
| POST | `/api/smart_heating/areas/{id}/disable` | Disable area |
| GET | `/api/smart_heating/areas/{id}/history?hours=24` | Get temperature history |
| GET | `/api/smart_heating/devices` | Get available devices (ALL platforms) |
| GET | `/api/smart_heating/devices/refresh` | Refresh device discovery |
| GET | `/api/smart_heating/status` | Get system status |
| POST | `/api/smart_heating/call_service` | Call HA service (proxy) |
| GET | `/api/smart_heating/vacation` | Get vacation mode configuration |
| POST | `/api/smart_heating/vacation` | Set vacation mode dates |
| DELETE | `/api/smart_heating/vacation` | Cancel vacation mode |
| GET | `/api/smart_heating/safety_sensor` | Get safety sensor configuration |
| POST | `/api/smart_heating/safety_sensor` | Set safety sensor configuration |
| DELETE | `/api/smart_heating/safety_sensor` | Remove safety sensor |

**Device Discovery** (`GET /devices`):
- Discovers ALL Home Assistant climate, sensor, switch, and number entities
- Platform-agnostic: Works with ANY integration (Nest, Ecobee, MQTT, Z-Wave, etc.)
- Smart filtering:
  - Climate entities: All climate domains
  - Temperature sensors: device_class, unit_of_measurement, or entity naming
  - Switches: Heating-related only (pumps, relays, floor heating)
  - Numbers: Valve/TRV position controls
- Returns device metadata: entity_id, name, type, HA area assignment
- Filters out devices from hidden areas (3-method filtering)

### 10. WebSocket API (`websocket.py`)

Real-time communication using HA WebSocket API.

**Commands:**
- `smart_heating/subscribe_updates` - Subscribe to area updates
- `smart_heating/get_areas` - Get areas via WebSocket

### 11. Service Calls

Comprehensive service API for automation/script integration:

**Area Management:**
1. `smart_heating.enable_area` - Enable area
2. `smart_heating.disable_area` - Disable area
3. `smart_heating.set_area_temperature` - Set target temperature

**Device Management:**
4. `smart_heating.add_device_to_area` - Add device to area
5. `smart_heating.remove_device_from_area` - Remove device

**Schedule Management:**
6. `smart_heating.add_schedule` - Add time-based schedule
7. `smart_heating.remove_schedule` - Remove schedule
8. `smart_heating.enable_schedule` - Enable schedule
9. `smart_heating.disable_schedule` - Disable schedule

**Advanced Settings:**
10. `smart_heating.set_night_boost` - Configure night boost
11. `smart_heating.set_opentherm_gateway` - Configure global OpenTherm gateway
12. `smart_heating.set_trv_temperatures` - Set TRV heating/idle temperatures
13. `smart_heating.set_hysteresis` - Set global hysteresis

**Vacation Mode:**
14. `smart_heating.set_vacation_mode` - Configure vacation dates
15. `smart_heating.cancel_vacation_mode` - Cancel vacation

**Safety:**
16. `smart_heating.set_safety_sensor` - Configure safety sensor
17. `smart_heating.remove_safety_sensor` - Remove safety sensor

**System:**
18. `smart_heating.refresh` - Manual refresh

## Frontend Components

### Technology Stack

- **React 18.3** - UI library
- **TypeScript** - Type safety
- **Vite 6** - Build tool and dev server
- **Material-UI (MUI) v6** - Component library
- **react-router-dom** - Client-side routing
- **react-beautiful-dnd** - Drag and drop device assignment
- **Recharts** - Interactive temperature charts
- **WebSocket** - Real-time updates via custom hook

### Component Structure

```
src/
├── main.tsx                    # Entry point
├── App.tsx                     # Main application with routing
├── types.ts                    # TypeScript interfaces
├── api.ts                      # API client functions
├── index.css                   # Global styles
├── components/
│   ├── Header.tsx              # App header with connection status
│   ├── ZoneList.tsx            # Area grid with drag-drop context
│   ├── ZoneCard.tsx            # Individual area control card
│   ├── CreateZoneDialog.tsx    # Area creation dialog
│   ├── DevicePanel.tsx         # Draggable devices sidebar
│   ├── ScheduleEditor.tsx      # Schedule management UI
│   └── HistoryChart.tsx        # Temperature history visualization
├── pages/
│   ├── AreaDetail.tsx          # Detailed area page (5 tabs)
│   └── GlobalSettings.tsx      # Global settings page (5 tabs)
└── hooks/
    └── useWebSocket.ts         # WebSocket connection hook
```

### Key Features

**ZoneCard Component:**
- Temperature slider (5-30°C, 0.5° steps)
- Enable/disable toggle
- State indicator with color coding (heating/idle/off)
- Device list with remove buttons
- Drag-drop target for device assignment
- Click to navigate to detail page

**AreaDetail Page (5 Tabs):**
1. **Overview** - Temperature control, current state, device status with real-time heating indicators
2. **Devices** - Enhanced device management with:
   - Assigned devices list with remove buttons
   - Location-based filtering dropdown
   - Available devices with add buttons (+/- icons)
   - HA area assignment displayed as chips
   - Real-time device counts per location
3. **Schedule** - Time-based schedule editor
4. **History** - Interactive temperature charts (6h-7d ranges)
5. **Settings** - Night boost, hysteresis, advanced configuration

**GlobalSettings Page (5 Tabs):**
1. **Temperature** - Global temperature settings:
   - Default target temperature
   - Minimum and maximum temperature limits
   - Temperature step size (0.5°C default)
2. **Sensors** - Global sensor configuration:
   - Default sensor entity for new areas
   - Sensor filtering and discovery settings
3. **Vacation** - Vacation mode management:
   - Start and end date/time pickers
   - Current vacation status display
   - Cancel vacation button
   - Original area states shown during vacation
4. **Safety** - Safety sensor configuration:
   - Sensor selection dropdown (smoke/CO detectors)
   - Attribute selection (e.g., smoke, gas, co)
   - Alert value configuration (e.g., true, on)
   - Enable/disable safety monitoring
   - Current configuration display
5. **Advanced** - Advanced system settings:
   - Hysteresis configuration (±0.5°C default)
   - TRV heating/idle temperatures
   - OpenTherm gateway configuration
   - Logging and debug settings

**Device Management Features:**
- **Location Filter Dropdown** - Filter devices by HA area
  - "All Locations" - Show all available devices
  - "No Location Assigned" - Unassigned devices only
  - Specific areas (Badkamer, Woonkamer, etc.) with device counts
- **Direct Device Assignment** - Add/remove devices from area detail page
- **Add Button** (AddCircleOutlineIcon) - Single click to assign device
- **Remove Button** (RemoveCircleOutlineIcon) - Single click to unassign device
- **Location Chips** - Visual indicators showing device's HA area
- **Real-time Updates** - Device list refreshes after add/remove operations

**ScheduleEditor Component (v0.4.0 - Enhanced UI):**
- **Modern Date/Time Selection:**
  - Material-UI DatePicker for date selection (calendar view)
  - Time inputs for start/end times
  - Toggle between "Weekly Recurring" and "Specific Date" schedules
- **Multi-Day Selection:**
  - Checkbox interface for selecting multiple days
  - Quick selection buttons: Weekdays, Weekend, All Days, Clear
  - Visual preview of selected days with chips
  - Count indicator showing number of selected days
- **Card-Based Layout:**
  - Separate sections for Weekly and Date-Specific schedules
  - Collapsible cards for each day (expand/collapse for cleaner view)
  - Visual icons (🔁 Repeat for weekly, 📅 Event for date-specific)
  - Schedule count badges per day
  - Formatted dates for date-specific schedules (e.g., "Apr 29, 2024")
- **Schedule Types:**
  - Weekly Recurring: Create schedules for multiple days at once
  - Date-Specific: One-time schedules for holidays, events, temporary changes
  - Temperature or Preset Mode: Toggle between fixed temperature and preset modes
- Add/remove schedules with single click
- Edit schedules by clicking on chips
- Enable/disable individual schedules
- Visual schedule chips showing time range and temperature/preset

**HistoryChart Component:**
- Recharts line chart
- Blue line: Current temperature
- Yellow dashed: Target temperature
- Red dots: Heating active periods
- Time range selector (6h, 12h, 24h, 3d, 7d)
- Auto-refresh every 5 minutes
- Responsive design

**DevicePanel Component:**
- **Universal Device Discovery** - Shows ALL Home Assistant devices
  - Climate entities from ANY integration (Nest, Ecobee, MQTT, Z-Wave, etc.)
  - Temperature sensors from ANY platform
  - Heating-related switches (pumps, relays, floor heating)
  - Valve/TRV position controls
- Platform-agnostic device detection
- Real-time availability updates
- Device refresh button for manual discovery
- Filter by device type icons
- Shows HA area assignment for each device

**CreateZoneDialog Component:**
- Area name input
- Auto-generated area_id
- Initial temperature setting
- Form validation

### API Integration

All API calls go through `src/api.ts`:

```typescript
// Get areas
const areas = await getZones()

// Create area
await createZone('living_room', 'Living Room', 21.0)

// Set temperature
await setZoneTemperature('living_room', 22.5)

// Add device
await addDeviceToZone('living_room', 'device_id')
```

### Real-time Updates (Planned)

WebSocket connection for live updates:
- Area state changes
- Temperature updates
- Device additions/removals
- System status

## Data Flow

### Area Creation Flow

```
User clicks "Create Area"
    ↓
CreateZoneDialog collects input

### Primary Temperature Sensor Selection (v0.5.10+)

**Feature:** Allows users to select which device measures temperature for each area.

**Use Cases:**
- Air conditioner with built-in temp sensor + dedicated temperature sensor → Use dedicated sensor for accuracy
- Multiple thermostats in one area → Choose which thermostat's temperature to use
- Prefer standalone sensor over AC's sensor for consistent readings

**Behavior:**
```
Auto Mode (default):
    - primary_temperature_sensor = null
    - Averages ALL temperature sensors + thermostats in area
    
Primary Sensor Mode:
    - primary_temperature_sensor = "sensor.xyz" or "climate.abc"
    - Uses ONLY the selected device for temperature
    - If selected device unavailable → Falls back to auto mode temporarily
```

**Implementation:**
- **Storage:** `Area.primary_temperature_sensor` (str | None)
- **Temperature Collection:** `climate_handlers/temperature_sensors.py`
  - Checks if primary sensor is set
  - Returns single temperature from primary device
  - Falls back to averaging if primary unavailable
- **API Endpoint:** `POST /api/smart_heating/areas/{area_id}/primary_temp_sensor`
  - Validates sensor exists in area
  - Updates temperature immediately
  - Triggers heating control refresh
- **UI:** Area Detail → Devices tab → Primary Temperature Sensor dropdown
- **Translations:** English + Dutch

### Temperature Control Flow

```
User drags temperature slider
    ↓
ZoneCard onChange handler
    ↓
api.setZoneTemperature() calls POST /api/.../temperature
    ↓
ZoneHeaterAPIView.post() routes to set_temperature()
    ↓
area_manager.set_area_target_temperature()
    ↓
Area updated in storage
    ↓
Climate controller (30s interval) detects change
    ↓
Climate controller processes area:
    │
    ├──→ Collects temperature using primary sensor (if set) or averaging (if null)
    │
    ├──→ Thermostats: climate.set_temperature to target
    │
    ├──→ Switches: switch.turn_on if heating, switch.turn_off if idle
    │
    ├──→ Valves:
    │    ├──→ Position mode (number.*): Set to 100% if heating, 0% if idle
    │    └──→ Temperature mode (climate.*): Set to heating_temp if heating, idle_temp if idle
    │
    └──→ Tracks heating state + target for this area
    ↓
After all areas processed:
    ↓
Climate controller aggregates demands:
    - heating_areas = areas currently needing heat
    - max_target_temp = highest target across heating areas
    ↓
OpenTherm Gateway Control:
    - If any_heating: Boiler ON, setpoint = max_target_temp + 20°C
    - If no heating: Boiler OFF
    ↓
Devices respond (thermostats, switches, valves, boiler)
    ↓
Coordinator fetches updated state (30s interval)
    ↓
[F°→C° conversion applied if needed]
    ↓
WebSocket pushes update to frontend
    ↓
ZoneCard displays updated device status
```

**Multi-Device Coordination Example:**

Living Room area with target 23°C, current 20°C (needs heating):
1. **Thermostat** → Set to 23°C
2. **Pump Switch** → Turn ON
3. **TRV (position mode)** → Set to 100% open
4. **TRV (temp mode)** → Set to 25°C (heating_temp)
5. Area tracked as heating with target 23°C

Kitchen area with target 19°C, current 21°C (no heating needed):
1. **Thermostat** → Set to 19°C (stays synced)
2. **Pump Switch** → Turn OFF
3. **TRV (position mode)** → Set to 0% closed
4. **TRV (temp mode)** → Set to 10°C (idle_temp)
5. Area tracked as idle

OpenTherm Gateway (global):
- Living Room needs heat (target 23°C), Kitchen doesn't
- Boiler ON, setpoint = 23 + 20 = 43°C

**Note on Mock Devices:**
With mock MQTT devices, valve positions don't respond to commands since there's no physical hardware. Real TRVs would automatically adjust their valve position based on temperature commands and report back via MQTT.

## Storage

Zones and configuration are stored using Home Assistant's storage API:

**File:** `.storage/smart_heating_areas`

**Format:**
```json
{
  "version": 1,
  "data": {
    "areas": [
      {
        "id": "living_room",
        "name": "Living Room",
        "target_temperature": 21.0,
        "enabled": true,
        "devices": [
          {
            "id": "device_1",
            "name": "Living Room Thermostat",
            "type": "thermostat"
          }
        ]
      }
    ]
  }
}
```

## Zigbee2MQTT Integration

### Device Discovery

Devices are discovered via MQTT topics:
- `zigbee2mqtt/bridge/devices` - List of all devices
- `zigbee2mqtt/<friendly_name>` - Device state

### Device Control

Control messages sent to:
- `zigbee2mqtt/<friendly_name>/set` - Send commands

Example:
```json
{
  "temperature": 22.5,
  "system_mode": "heat"
}
```

## Security

- **Authentication**: All API endpoints require HA authentication
- **Authorization**: Uses HA's built-in user permissions
- **CORS**: Configured for same-origin only
- **Input Validation**: All inputs validated before processing

## Performance

- **Coordinator Poll**: 30-second interval (configurable)
- **API Response Time**: < 100ms for typical operations
- **Frontend Bundle**: ~500KB gzipped
- **WebSocket**: Minimal overhead for real-time updates

## Backend Module Structure

**v0.6.0+ Modular Architecture:**

The backend has been refactored into a clean modular structure following single-responsibility principles:

### Core Integration Files
- `__init__.py` (591 lines) - Integration setup, coordinator initialization
- `area_manager.py` - Area/zone management and storage
- `coordinator.py` - Data update coordinator with manual override detection
- `climate.py` - Climate platform (zone entities)
- `switch.py` - Switch platform (zone enable/disable)
- `sensor.py` - Sensor platform
- `config_flow.py` - Configuration flow

### Service Handler Modules (`ha_services/`)
Extracted from `__init__.py` - 29 Home Assistant service handlers:
- `__init__.py` - Central exports
- `schemas.py` - 22 service validation schemas
- `area_handlers.py` - Set temperature, enable/disable area
- `device_handlers.py` - Add/remove devices
- `schedule_handlers.py` - Schedule management, night boost, copy
- `hvac_handlers.py` - Preset mode, boost mode, HVAC mode
- `sensor_handlers.py` - Window/presence sensor management
- `config_handlers.py` - Global settings, frost protection, presets
- `safety_handlers.py` - Safety sensor configuration
- `vacation_handlers.py` - Vacation mode control
- `system_handlers.py` - Refresh, status

### API Handler Modules (`api_handlers/`)
Extracted from `api.py` - 49 REST API endpoint handlers:
- `__init__.py` - Central exports
- `areas.py` - 12 area management endpoints
- `devices.py` - 4 device discovery/assignment endpoints
- `schedules.py` - 5 schedule/preset/boost endpoints
- `sensors.py` - 5 sensor management endpoints
- `config.py` - 15 global configuration endpoints
- `history.py` - 4 history/learning endpoints
- `logs.py` - 1 logging endpoint
- `system.py` - 3 system status endpoints

### Manager/Controller Modules
- `climate_controller.py` - HVAC device control logic
- `scheduler.py` - Schedule execution (1-minute interval)
- `learning_engine.py` - ML-based temperature learning
- `safety_monitor.py` - Emergency shutdown on safety alerts
- `vacation_manager.py` - Vacation mode coordination
- `history.py` - Temperature logging and retention
- `area_logger.py` - Per-area event logging

### Model Modules (`models/`)
- `area.py` - Area data model
- `schedule.py` - Schedule data model

### Utility Modules (`utils/`)
- `validators.py` - Input validation functions
- `response_builders.py` - API response formatting
- `coordinator_helpers.py` - Coordinator utility functions
- `device_registry.py` - HA device registry helpers

### API & Communication
- `api.py` (446 lines) - REST API routing, static file serving
- `websocket.py` - WebSocket real-time updates

**Refactoring Impact:**
- Phase 2 (ha_services/): `__init__.py` reduced from 1,126 → 591 lines (47% reduction)
- Phase 3 (api_handlers/): `api.py` reduced from 2,518 → 446 lines (82% reduction)
- Overall: 72% code reduction with 20 focused, single-responsibility modules
- Maintainability: Significantly improved with clear separation of concerns

## Extensibility

### Adding New Device Types

1. Add device type constant in `const.py`
2. Update device handling in `area_manager.py`
3. Add icon in `DevicePanel.tsx`

### Adding New Platforms

1. Create platform file (e.g., `number.py`)
2. Add to `PLATFORMS` in `const.py`
3. Forward setup in `__init__.py`

### Adding New API Endpoints

1. Add handler function to appropriate module in `api_handlers/`
2. Import handler in `api_handlers/__init__.py`
3. Add routing in `api.py` (SmartHeatingAPIView)
4. Add client function to `frontend/src/api.ts`
5. Use in React components

### Adding New Services

1. Add schema to `ha_services/schemas.py`
2. Create handler in appropriate module in `ha_services/`
3. Import handler in `ha_services/__init__.py`
4. Register service in `__init__.py` (async_setup_services)
5. Document in `services.yaml`

## Future Enhancements

- [ ] Drag-and-drop device assignment
- [ ] Area scheduling/programs
- [ ] Analytics dashboard
- [ ] Smart heating algorithms
- [ ] Energy monitoring
- [ ] Multi-language support
- [ ] Mobile app integration
- [ ] Voice control optimization
