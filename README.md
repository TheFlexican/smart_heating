# Smart Heating

A Home Assistant custom integration for managing multi-area heating systems with Zigbee2MQTT devices. Features a modern React-based web interface for easy area configuration and device management.

## ✨ Features

- 🏠 **Multi-area heating control** - Create and manage multiple heating areas
- 🌡️ **Universal Device Support** - Works with ALL Home Assistant climate integrations
  - Google Nest, Ecobee, generic_thermostat, MQTT/Zigbee2MQTT, and ANY climate entity
  - Platform-agnostic device discovery
  - No integration-specific code required
- 🎛️ **Web-based GUI** - Modern React interface with intelligent device management
  - Location-based device filtering
  - Direct device assignment from area pages
  - Real-time device status updates
- 🔄 **Manual Override Mode** - Automatic detection of external thermostat changes (NEW in v0.4.0)
  - System detects when thermostat adjusted outside app (e.g., Google Nest dial)
  - Enters "MANUAL" mode - app stops controlling, preserves user's setting
  - Real-time updates within 2-3 seconds via WebSocket
  - Automatically clears when temperature adjusted via app
  - Persists across restarts
- 📅 **Smart Scheduling** - Time-based temperature profiles with day-of-week selection
  - **Preset Mode Schedules** - Set preset modes (Away, Eco, Comfort, etc.) instead of fixed temperatures (v0.5.0+)
  - **Cross-Day Support** - Schedules can span midnight (e.g., Saturday 22:00 - Sunday 07:00) (v0.5.0+)
  - Toggle between temperature-based and preset-based scheduling
  - Combine with global preset temperatures for maximum flexibility
- 🌙 **Night Boost** - Configurable temperature increase during night hours (customizable start/end times)
  - **Schedule-Aware** - Automatically coordinates with active schedules (v0.5.3+)
  - Only applies when NO schedule is active (schedules take precedence)
  - Works as pre-heating mechanism before morning schedules
- 🧠 **Adaptive Learning** - Machine learning system that learns heating patterns and weather correlation
  - Automatically predicts heating time based on outdoor temperature
  - **Smart night boost** - Detects morning schedules and heats towards them (v0.5.3+)
  - Reads first morning schedule (00:00-12:00) as target time
  - Uses schedule's preset temperature as heating target
  - Starts heating at optimal predicted time before schedule
  - Uses Home Assistant Statistics API for efficient database storage
  - Tracks heating rates, cooldown rates, and outdoor temperature correlations
- 🎯 **Preset Modes** - Quick temperature presets (AWAY, ECO, COMFORT, HOME, SLEEP, ACTIVITY, BOOST)
  - **Global Preset Temperatures** - Configure default temperatures for all areas (v0.4.3+)
  - **Per-Area Customization** - Choose between global defaults or custom temperatures per area
  - Seamless switching between global and custom settings with toggle controls
- ⚡ **Boost Mode** - Temporary high-temperature boost with configurable duration
- 🪟 **Window Sensor Integration** - Configurable actions (turn off, reduce temp, or none) when windows/doors open with custom temperature drops
- 👤 **Presence Detection** - Automatic preset mode switching based on occupancy (v0.4.3+)
  - Switches to "Away" preset when nobody is home
  - Returns to "Home" preset when someone arrives
  - Works with Person entities, Device Trackers, and motion sensors
  - No manual temperature adjustments - uses your configured preset temperatures
  - **Global Presence Sensors** - Configure sensors once, apply to all areas (v0.5.0+)
  - **Per-Area Toggle** - Choose global or area-specific presence detection per area (v0.5.0+)
- 🔌 **Smart Switch Control** - Per-area control to turn off switches/pumps when not heating (v0.4.2+)
  - Energy efficient: Automatically shuts down circulation pumps when heating stops
  - Always-on mode: Keep pumps running continuously for systems requiring constant circulation
  - Works in manual override mode: Switches controlled based on actual thermostat heating state
- ❄️ **Frost Protection** - Global minimum temperature to prevent freezing
- 🌡️ **HVAC Modes** - Support for heating, cooling, auto, and off modes
- 📋 **Schedule Copying** - Duplicate schedules between areas and days
- 📊 **Temperature History** - Track and visualize temperature trends with interactive charts
  - Configurable retention period (1-365 days, default 30 days)
  - Custom time range selection with date/time picker
  - Preset ranges: 6h, 12h, 24h, 3d, 7d, 30d
  - 5-minute data resolution (never aggregated)
  - Automatic cleanup every hour
- 📝 **Development Logs** - Per-area logging system for debugging and visibility (v0.5.4+)
  - Dedicated Logs tab in area details showing all heating strategy decisions
  - Color-coded event types: Temperature, Heating, Schedule, Smart Boost, Sensors, Mode Changes
  - Detailed JSON data for each log entry showing exact parameters
  - **Chip-Based Filtering** - One-click event type filters with visual feedback (v0.5.6+)
  - **File-Based Storage** - Persistent logs stored in separate `.jsonl` files per event type (v0.5.6+)
    - Storage: `.storage/smart_heating/logs/{area_id}/{event_type}.jsonl`
    - Automatic rotation at 1,000 entries per file
    - Logs persist across Home Assistant restarts
  - Tracks: temperature changes, heating state changes, schedule activations, smart night boost predictions, sensor triggers, manual override mode
  - **Enhanced Detail** - Temperature source tracking (preset/schedule/base), night boost calculations with values (v0.5.6+)
- ⚙️ **Advanced Settings** - Hysteresis control, temperature limits, and fine-tuning
  - **Global Hysteresis** - Set default temperature buffer to prevent rapid on/off cycling (0.1-2.0°C)
  - **Area-Specific Hysteresis Override** - Customize hysteresis per area (NEW in v0.3.18)
    - Useful for floor heating systems (can use 0.1-0.3°C)
    - Help modal explains hysteresis and system-specific recommendations
    - Toggle between global setting or custom value
  - **Tabbed Global Settings** - Organized interface with 4 categories (NEW in v0.3.18)
    - 🌡️ Temperature: Global preset temperatures
    - 👥 Sensors: Global presence sensor configuration
    - 🏖️ Vacation: Vacation mode settings
    - ⚙️ Advanced: Hysteresis and future advanced features
- 🌐 **REST API** - Full API for programmatic control
- 📡 **WebSocket support** - Real-time updates and state synchronization
- 🎛️ **Climate entities** - Full thermostat control per area
- 🔌 **Switch entities** - Easy area on/off control
- 📊 **Sensor entities** - System status monitoring
- 🛠️ **Service calls** - Comprehensive service API for automation
- 💾 **Persistent storage** - Configuration and history automatically saved
- 🔄 **Auto-update** - Data coordinator with 30-second interval
- 📝 **Debug logging** - Extensive logging for troubleshooting
- 🏖️ **Vacation Mode** - One-click mode to set all areas to Away preset (NEW in v0.6.0)
  - Set date range for extended absences
  - Auto-disable when someone arrives home
  - Frost protection with minimum temperature override
  - Visual banner and quick disable
- 🌍 **Internationalization** - Multi-language support (NEW in v0.6.0)
  - Automatic language detection from Home Assistant settings
  - Supported languages: English (🇬🇧) and Dutch (🇳🇱)
  - Manual language switching via interface
  - Full UI translation including all features

## 🚀 Coming in v0.6.0+

**Status**: Vacation Mode & Internationalization Released! Additional features in development.

The following features are released or planned for future releases:

### 🏖️ Vacation Mode ✅ RELEASED in v0.6.0
One-click mode to set all areas to Away preset for extended periods
- ✅ Set date range for vacation (start/end dates)
- ✅ Auto-disable when someone arrives home
- ✅ Frost protection override with minimum temperature
- ✅ Visual banner on dashboard when active
- ✅ Service calls for automation integration

**Usage:**
1. Navigate to **Settings** (gear icon in header)
2. Find the **Vacation Mode** section at the top
3. Set your vacation dates and preferred preset mode
4. Enable frost protection if needed (recommended for winter)
5. Click **Enable Vacation Mode**

All areas will automatically switch to your chosen preset. A banner will appear on the dashboard. When you return, simply click **Disable** in the banner or settings.

### 🌍 Internationalization (i18n) ✅ RELEASED in v0.6.0
Multi-language support for global deployment
- ✅ Automatic language detection from Home Assistant settings
- ✅ Supported languages: English (🇬🇧) and Dutch (🇳🇱)
- ✅ Manual language switching via header menu (🌍 icon)
- ✅ Complete UI translation
- ✅ Dutch documentation (README.nl.md, CHANGELOG.nl.md)

**Usage:**
1. Language is automatically detected from your Home Assistant settings
2. To change manually, click the 🌍 icon in the header
3. Select your preferred language (English or Nederlands)
4. All UI elements will update immediately

**Documentation:**
- 🇬🇧 English: `README.md`, `CHANGELOG.md`
- 🇳🇱 Dutch: `README.nl.md`, `CHANGELOG.nl.md`

### 💾 Import/Export Configuration (Planned)
Backup and restore all Smart Heating settings
- Export complete configuration to JSON
- Import with validation and preview
- Selective restore (choose what to import)
- Automatic backup before import

### 👥 Multi-User Presence (Planned)
Track which family members are home and adjust per-person preferences
- User profiles with temperature preferences
- Priority system for multiple users
- Per-user preset overrides

### 📊 Heating Efficiency Reports (Planned)
Analyze which areas are heating efficiently
- Efficiency score per area (0-100)
- Daily/weekly/monthly reports
- Recommendations for improvement

### 📈 Historical Comparisons (Planned)
Compare heating performance across time periods
- Week-to-week, month-to-month comparisons
- Year-over-year analysis
- Energy savings tracking

**Implementation Strategy**: Features will be released incrementally with thorough testing. See [V0.6.0_ARCHITECTURE.md](V0.6.0_ARCHITECTURE.md) for technical details.

---

## 📋 Supported Device Types

### Per-Area Devices
- **Thermostat** - Room thermostats for direct temperature control
  - **ALL Home Assistant climate integrations supported**:
    - Google Nest (`nest` integration)
    - Ecobee (`ecobee` integration)
    - Generic Thermostat (`generic_thermostat` integration)
    - MQTT/Zigbee2MQTT (`mqtt` platform)
    - Z-Wave thermostats (`zwave_js` integration)
    - And ANY other climate entity from ANY integration
  - Platform-agnostic: Works with climate entities from any source
  - No device-specific code required
- **Temperature Sensor** - External temperature measurement for area monitoring
  - Flexible detection: device_class, unit_of_measurement, or entity naming
  - Works with sensor entities from ANY platform (MQTT, Z-Wave, Zigbee, etc.)
- **Window/Door Sensor** - Binary sensors for automatic heating adjustment when open
- **Presence/Motion Sensor** - Binary sensors for occupancy-based temperature boosting
- **Valve/TRV** - Smart radiator valves with **dynamic capability detection**
  - **No device-specific code** - System queries Home Assistant entity attributes at runtime
  - **Works with ANY valve model** from any manufacturer
  - Control mode determined by entity capabilities:
    - **Position control**: Entity has `number.*` domain OR `climate.*` with `position` attribute
    - **Temperature control**: Entity has `climate.*` domain with `temperature` attribute
  - Examples (for reference only, not hardcoded):
    - TuYa, Danfoss, Eurotronic, Sonoff, or any other TRV brand
    - Position-controlled valves: Opens to max when heating, min when idle
    - Temperature-controlled valves: Sets to `target+offset` when heating, `idle_temp` when idle
  - Works with any external sensor brand
- **Switch** - Circulation pumps, relays, or zone valves (any brand)
  - Automatically turns ON when area needs heating
  - Automatically turns OFF when area is idle
  - Smart filtering: Only heating-related switches detected (pumps, relays, floor heating)

### Global Devices
- **OpenTherm Gateway** - Single gateway for boiler control (shared across all areas)
  - Aggregates heating demands from all areas
  - Controls boiler on/off based on any area needing heat
  - Sets optimal boiler temperature (highest requested + 20°C overhead)

## 🏗️ Heating Architecture

Smart Heating uses an intelligent multi-device control strategy:

### Device Assignment by Area
Each area can contain multiple device types that work together:

```
Living Room Area:
├── climate.living_room_thermostat (optional - direct control)
├── sensor.living_room_temperature (required - for monitoring)
├── climate.living_room_trv_1 (valve with temp control)
├── climate.living_room_trv_2 (valve with temp control)
└── switch.living_room_pump (floor heating pump)

Bedroom Area:
├── sensor.bedroom_temperature (required)
├── number.bedroom_valve (valve with position control)
└── switch.bedroom_pump

Global Configuration:
└── climate.opentherm_gateway (boiler control - shared)
```

### Heating Control Flow

1. **Temperature Monitoring**: External sensors measure area temperature
2. **Heating Decision**: Compare current vs target (with hysteresis)
3. **Per-Area Actions** (when heating needed):
   - **Thermostats**: Set to target temperature
   - **Switches**: Turn ON (pumps, relays)
   - **Valves**: Dynamic control based on capabilities
     - **Position control** (if supported): Open to 100%
     - **Temperature control** (fallback): Set to `target + 10°C` to ensure valve opens
       - Example: For TS0601 TRV at 21°C target → Set TRV to 31°C (opens valve fully)
4. **Global Boiler Control**:
   - If ANY area needs heating → Boiler ON
   - Set boiler to: `max(all_area_targets) + 20°C`
   - If NO areas need heating → Boiler OFF

### Why This Design?

- **Shared Boiler**: One OpenTherm gateway serves all areas efficiently
- **Independent Zones**: Each area controls its own circulation and valves
- **Smart TRV Fallback**: Works with TRVs that don't support direct position control
- **External Sensors**: Accurate temperature measurement independent of TRV location
- **Energy Efficient**: Boiler only runs when needed, optimal temperature setting

## 🧠 Adaptive Learning System

Smart Heating includes a machine learning engine that learns your home's heating characteristics and optimizes heating schedules automatically.

### How It Works

1. **Automatic Learning**: Every heating cycle is recorded with:
   - Start and end temperatures
   - Time taken to reach target
   - Outdoor temperature (if weather sensor configured)
   - Calculated heating rate (°C per minute)

2. **Data Storage**: Uses Home Assistant's Statistics API
   - Efficient database storage (SQLite or MariaDB)
   - No file-based storage overhead
   - Statistics tracked per area:
     - `heating_rate`: How fast the area heats up
     - `cooldown_rate`: How fast it cools down
     - `outdoor_correlation`: Impact of outdoor temperature
     - `prediction_accuracy`: How accurate predictions are

3. **Predictive Scheduling**: Smart Night Boost feature
   - Configure desired wake-up time (e.g., 06:00)
   - System predicts heating time based on:
     - Current temperature
     - Target temperature
     - Current outdoor temperature
     - Historical learning data
   - Automatically starts heating at optimal time
   - Includes safety margin to ensure target is reached

### Configuration

**Per Area:**
- `smart_night_boost_enabled`: Enable/disable adaptive learning for this area
- `smart_night_boost_target_time`: Desired time to reach target temperature (e.g., "06:00")
- `weather_entity_id`: Outdoor temperature sensor for weather correlation (optional)

**Example:**
```yaml
# Via service call
service: smart_heating.set_night_boost
data:
  area_id: living_room
  smart_night_boost_enabled: true
  smart_night_boost_target_time: "06:00"
  weather_entity_id: sensor.outdoor_temperature
```

### Learning Statistics API

Access learning data via REST API:
```bash
GET /api/smart_heating/areas/{area_id}/learning
```

Returns:
```json
{
  "area_id": "living_room",
  "stats": {
    "total_events": 45,
    "avg_heating_rate": 0.15,
    "avg_outdoor_correlation": -0.65,
    "prediction_accuracy": 0.92,
    "last_updated": "2024-12-04T10:30:00"
  }
}
```

## 🎯 Advanced Heating Features

Smart Heating includes advanced features for enhanced comfort and energy efficiency.

### Manual Override Mode (v0.4.0+)

Automatic detection of external thermostat adjustments with intelligent manual override.

**How It Works:**

When you adjust a thermostat directly (e.g., turning the Google Nest dial, pressing buttons on a physical thermostat, or using the thermostat's own app), Smart Heating automatically detects this change and enters "Manual Override Mode" for that area.

**Features:**
- 🔍 **Real-Time Detection** - Monitors all thermostats for external temperature changes
- ⏱️ **Smart Debouncing** - 2-second delay prevents flood of updates from rapid dial adjustments
- 🟠 **Visual Indication** - Orange "MANUAL" badge displayed on area card
- 🔒 **Automatic Control Pause** - App stops sending temperature commands to that area
- 💾 **Persistence** - Manual mode survives Home Assistant restarts
- 🔄 **Easy Exit** - Automatically cleared when temperature adjusted via Smart Heating app

**User Experience:**

1. **External Adjustment:**
   - You adjust your Google Nest from 20°C to 22°C
   - System detects change within 2 seconds
   - Area enters MANUAL mode
   - Frontend shows orange "MANUAL" badge (2-3 second delay)

2. **During Manual Mode:**
   - Climate controller skips this area
   - Your manual setting is preserved
   - No automatic temperature changes
   - Schedules don't apply
   - Night boost disabled

3. **Resuming Automatic Control:**
   - Adjust temperature via Smart Heating app
   - Manual mode automatically cleared
   - Normal operation resumes (schedules, night boost, etc.)

**Technical Details:**

**State Change Monitoring:**
```python
# Backend monitors all climate entities in real-time
async_track_state_change_event(hass, entity_id, handler)
# Triggered on temperature or hvac_action changes
```

**Debouncing Logic:**
```python
MANUAL_TEMP_CHANGE_DEBOUNCE = 2.0  # seconds
# Prevents multiple updates from rapid dial turns
# Cancels previous pending updates when new changes detected
```

**Persistence:**
```json
{
  "area_id": "living_room",
  "manual_override": true,  // v0.4.1+ persists across restarts
  "target_temperature": 22.0
}
```

**API Integration:**
```bash
# Check manual override status
GET /api/smart_heating/areas/living_room
# Response: {"manual_override": true, ...}

# Clear manual mode by setting temperature
POST /api/smart_heating/areas/living_room/temperature
{"temperature": 21.0}
# Automatically sets manual_override: false
```

**Why Manual Override?**

Smart Heating is designed to be non-intrusive. If you manually adjust a thermostat, the system respects your decision and gets out of the way. This prevents frustrating "fights" where the app keeps overriding your manual adjustments.

**Use Cases:**
- 🏠 Quick comfort adjustment without opening app
- 🌡️ Guest preferences in specific rooms  
- 🛋️ Temporary changes for specific activities
- 🔧 Testing thermostat functionality
- 👶 Nursery temperature fine-tuning

**Logging:**
```bash
# Monitor manual override events
2025-01-06 10:30:15 DEBUG Thermostat temperature change detected: living_room 20.0°C → 22.0°C
2025-01-06 10:30:17 DEBUG Applying debounced temperature update: living_room = 22.0°C
2025-01-06 10:30:17 DEBUG Setting manual override mode for living_room
2025-01-06 10:30:17 DEBUG Area living_room entered MANUAL mode
```

**Compatibility:**
Works with **ALL** Home Assistant climate integrations:
- Google Nest thermostats
- Ecobee thermostats
- Generic Thermostat
- MQTT/Zigbee2MQTT devices
- Z-Wave thermostats
- Any climate entity from any integration

### Preset Modes

Quick temperature presets for common scenarios. Each preset has a default temperature that can be customized per area.

**Available Presets:**
- **NONE** - Use manual temperature or schedule
- **AWAY** (16°C) - Energy-saving when nobody's home
- **ECO** (18°C) - Economical heating
- **COMFORT** (22°C) - Maximum comfort
- **HOME** (20°C) - Standard home temperature
- **SLEEP** (19°C) - Optimal sleeping temperature
- **ACTIVITY** (21°C) - Active room usage
- **BOOST** (24°C) - Quick heat-up

**Usage:**
```yaml
service: smart_heating.set_preset_mode
data:
  area_id: "living_room"
  preset_mode: "comfort"
```

**Temperature Priority:**
Preset modes override schedules. Priority order:
1. Boost mode (highest)
2. Window open (reduces temp)
3. Preset mode
4. Schedule temperature
5. Manual target temperature
6. Night boost (additive)

### Smart Switch/Pump Control (v0.4.2+)

Automatically manage circulation pumps, relays, and zone valves to save energy when heating is not needed.

**How It Works:**

By default, switches and pumps assigned to an area are automatically turned **OFF** when the area is not actively heating and turned **ON** when heating is needed. This saves energy and reduces wear on equipment.

**Configuration:**

Each area has a configurable switch control mode in **Settings → Switch/Pump Control**:

- **Auto Off (Default)** - Switches/pumps automatically turn off when not heating
  - Badge: `Auto Off`
  - Energy efficient: Pumps only run when needed
  - Extends equipment lifespan
  
- **Always On** - Switches/pumps stay on continuously
  - Badge: `Always On`
  - For systems requiring constant circulation
  - Useful for balanced heating systems

**Intelligent Control:**

The switch control system is intelligent and works even in manual override mode:

```
Manual Override Mode:
- Thermostat heating? → Switches ON
- Thermostat idle? → Switches OFF (if Auto Off enabled)
```

This means switches are controlled based on the **actual heating state** of your thermostat, not the app's schedule. If you manually adjust your Google Nest thermostat and it starts heating, the circulation pump will automatically turn on.

**API Control:**

```bash
# Enable auto-shutdown
POST /api/smart_heating/areas/living_room/switch_shutdown
{"enabled": true}

# Keep switches always on
POST /api/smart_heating/areas/living_room/switch_shutdown
{"enabled": false}
```

**Use Cases:**

✅ **Auto Off Mode:**
- Floor heating circulation pumps
- Zone valve relays
- Auxiliary heating switches
- Areas with on-demand heating

❌ **Always On Mode:**
- Balanced heating systems
- Systems requiring constant flow
- Pumps with anti-seizing requirements
- Complex multi-zone systems

**Device Types:**

Works with all switch entities:
- `switch.floor_heating_pump`
- `switch.zone_valve_relay`
- `switch.circulation_pump`
- Any switch assigned to an area

**Visual Feedback:**

- Badge displays current mode in Settings accordion
- Orange "MANUAL" badge when thermostat manually adjusted
- Switches controlled based on thermostat hvac_action
7. Presence boost (additive)

### Boost Mode

Temporary high-temperature override for quick heating. Perfect for rapid warm-up when coming home.

**Features:**
- Configurable duration (5-180 minutes)
- Optional custom boost temperature (default: 24°C)
- Automatic expiry and return to normal operation
- Visual indication in frontend

**Usage:**
```yaml
# Boost for 30 minutes at default temp
service: smart_heating.set_boost_mode
data:
  area_id: "living_room"
  duration: 30

# Boost for 60 minutes at custom temp
service: smart_heating.set_boost_mode
data:
  area_id: "bedroom"
  duration: 60
  temperature: 25.0
```

**Cancel Boost:**
```yaml
service: smart_heating.cancel_boost
data:
  area_id: "living_room"
```

**REST API:**
```bash
# Activate boost
POST /api/smart_heating/areas/living_room/boost
{"duration": 30, "temperature": 24}

# Cancel boost
POST /api/smart_heating/areas/living_room/cancel_boost
```

### Window Sensor Integration

Automatically adjusts heating when windows/doors open to save energy.

**How It Works:**
1. Add window/door sensors to an area
2. When any sensor detects "open" state
3. Target temperature is automatically reduced by configured amount (default: 5°C)
4. Heating returns to normal when all windows closed
5. Status logged for monitoring

**Configuration:**
```yaml
# Add window sensor
service: smart_heating.add_window_sensor
data:
  area_id: "living_room"
  entity_id: "binary_sensor.living_room_window"

# Remove window sensor
service: smart_heating.remove_window_sensor
data:
  area_id: "living_room"
  entity_id: "binary_sensor.living_room_window"
```

**Customization:**
Per-area settings (in `area_manager.py`):
- `window_open_action_enabled`: Enable/disable feature (default: true)
- `window_open_temp_drop`: Temperature reduction in °C (default: 5.0)

**REST API:**
```bash
# Add sensor
POST /api/smart_heating/areas/living_room/window_sensors
{"entity_id": "binary_sensor.living_room_window"}

# Remove sensor
DELETE /api/smart_heating/areas/living_room/window_sensors/binary_sensor.living_room_window
```

### History Data Management

Full control over temperature history storage and retention with automatic cleanup.

**Features:**
- **Configurable Retention**: Store history from 1 day to 1 year (default: 30 days)
- **5-Minute Resolution**: Data recorded every 5 minutes, never aggregated
- **Automatic Cleanup**: Hourly background task removes expired data
- **Flexible Querying**: View preset ranges or custom date/time periods
- **No Data Loss**: Raw data points preserved at full resolution

**Recording:**
- Interval: Every 5 minutes (300 seconds)
- Data points: Current temperature, target temperature, heating state, timestamp
- Storage: Home Assistant's internal storage (`.storage/smart_heating_history`)

**Configuration:**
```yaml
# Set retention period (1-365 days)
service: smart_heating.set_history_retention
data:
  history_retention_days: 90  # Keep 90 days of history
```

**Frontend UI:**
- Settings tab → History Data Management section
- Slider to adjust retention period (1-365 days)
- Visual markers for common periods (1d, 7d, 30d, 90d, 180d, 365d)
- Save button to apply changes
- Automatic cleanup triggered when reducing retention

**History Tab:**
- Preset time ranges: 6h, 12h, 24h, 3d, 7d, 30d
- Custom date/time range picker for specific analysis
- Auto-refresh every 5 minutes
- Interactive charts with heating indicators

**REST API:**
```bash
# Get history configuration
GET /api/smart_heating/history/config
# Returns: {"retention_days": 30, "record_interval_seconds": 300, "record_interval_minutes": 5}

# Update retention period
POST /api/smart_heating/history/config
{"retention_days": 90}

# Query history with preset range
GET /api/smart_heating/areas/living_room/history?hours=24

# Query history with custom range
GET /api/smart_heating/areas/living_room/history?start_time=2025-12-01T00:00:00&end_time=2025-12-05T23:59:59

# Get all available history (within retention)
GET /api/smart_heating/areas/living_room/history
```

**Storage Management:**
- Old data automatically deleted after retention period expires
- Cleanup runs every hour in the background
- Immediate cleanup when retention period is reduced
- No manual intervention required
- Storage space scales with retention period and number of areas

**Best Practices:**
- **Short-term analysis (1-7 days)**: Quick troubleshooting and pattern identification
- **Medium-term (30-90 days)**: Seasonal adjustments and efficiency monitoring
- **Long-term (180-365 days)**: Year-over-year comparisons and annual optimization
- Balance storage space vs historical data needs
- Longer retention enables better machine learning predictions

### Presence Detection

Automatically switch between preset modes based on occupancy for enhanced comfort and energy savings.

**How It Works (v0.4.3+):**
1. Add presence sensors to an area (or use global sensors)
2. When nobody home → switches to "Away" preset
3. When someone arrives → switches to "Home" preset
4. Uses your configured preset temperatures (global or custom per area)
5. No manual temperature adjustments - clean preset mode switching

**Global Presence Configuration (v0.5.0+):**
Configure presence sensors once in Settings → Global Presence Sensors, then toggle per area:

```yaml
# Configure global presence sensors (Settings page)
# Add person entities, device trackers, or motion sensors
# Examples: person.john, device_tracker.phone, binary_sensor.home_motion

# Each area can then choose:
# - Use Global Presence Sensors (toggle ON)
# - Use Area-Specific Sensors (toggle OFF)
```

**Per-Area Configuration:**
```yaml
# Add area-specific presence sensor
service: smart_heating.add_presence_sensor
data:
  area_id: "home_office"
  entity_id: "binary_sensor.office_motion"

# Remove presence sensor
service: smart_heating.remove_presence_sensor
data:
  area_id: "home_office"
  entity_id: "binary_sensor.office_motion"

# Toggle between global and area-specific (v0.5.0+)
# Use the frontend toggle in Area Detail → Presence Configuration
# Or via API:
POST /api/smart_heating/areas/home_office/presence_config
{"use_global": true}
```

**Supported Sensor Types:**
- Person entities (`person.john`, `person.jane`)
- Device trackers (`device_tracker.phone_john`)
- Motion sensors (`binary_sensor` with `device_class: motion`)
- Occupancy sensors (`device_class: occupancy`)
- Presence sensors (`device_class: presence`)

**Benefits:**
- ✅ Centralized configuration with global sensors
- ✅ Per-area override when needed
- ✅ Clean preset mode switching (Away ↔ Home)
- ✅ Works with your configured preset temperatures
- ✅ Energy savings when nobody home

**REST API:**
```bash
# Configure global presence sensors (v0.5.0+)
GET /api/smart_heating/global_presence
POST /api/smart_heating/global_presence
{"sensors": [{"entity_id": "person.john"}, {"entity_id": "person.jane"}]}

# Add area-specific sensor
POST /api/smart_heating/areas/home_office/presence_sensors
{"entity_id": "binary_sensor.office_motion"}

# Remove area-specific sensor
DELETE /api/smart_heating/areas/home_office/presence_sensors/binary_sensor.office_motion

# Toggle global/area presence (v0.5.0+)
POST /api/smart_heating/areas/home_office/presence_config
{"use_global": true}
```

### Frost Protection

Global minimum temperature setting to prevent freezing in all areas.

**How It Works:**
1. Enable frost protection globally
2. Set minimum temperature (default: 7°C)
3. If any area's target falls below minimum → automatically raised to frost protection temperature
4. Applies even when areas are disabled
5. Safety feature for winter vacations

**Configuration:**
```yaml
service: smart_heating.set_frost_protection
data:
  enabled: true
  temperature: 7.0
```

**Use Cases:**
- Winter holidays (prevent pipe freezing)
- Empty properties
- Seasonal properties
- Backup safety measure

**REST API:**
```bash
POST /api/smart_heating/frost_protection
{"enabled": true, "temperature": 7.0}
```

### HVAC Modes

Support for different HVAC operation modes per area.

**Available Modes:**
- **HEAT** - Heating mode (default)
- **COOL** - Cooling mode (for AC-equipped areas)
- **AUTO** - Automatic heating/cooling
- **OFF** - System off (overrides all settings)

**Usage:**
```yaml
service: smart_heating.set_hvac_mode
data:
  area_id: "bedroom"
  hvac_mode: "heat"
```

**Behavior:**
- **OFF mode**: Area completely disabled, no heating commands sent
- **HEAT mode**: Normal heating operation
- **COOL/AUTO modes**: Framework ready for future AC support

**REST API:**
```bash
POST /api/smart_heating/areas/bedroom/hvac_mode
{"hvac_mode": "heat"}
```

### Schedule Copying

Duplicate schedules between areas or days to save time.

**Features:**
- Copy from one area to another
- Copy to specific days of week
- Copy all schedules at once
- Unique IDs automatically generated

**Usage:**
```yaml
# Copy Monday schedule to Tuesday-Friday
service: smart_heating.copy_schedule
data:
  source_area_id: "living_room"
  source_schedule_id: "monday_morning"
  target_area_id: "living_room"
  target_days:
    - "tue"
    - "wed"
    - "thu"
    - "fri"

# Copy entire area schedule to another area
service: smart_heating.copy_schedule
data:
  source_area_id: "living_room"
  target_area_id: "bedroom"
```

**Use Cases:**
- Weekday schedule replication
- Duplicate successful schedules to other rooms
- Quick setup of similar areas
- Seasonal schedule templates

## 🔧 Advanced Configuration

### Temperature Calculation Priority

Smart Heating uses a sophisticated 7-level priority system to determine the final target temperature:

1. **Boost Mode** (Highest Priority)
   - Temporary override
   - Time-limited
   - Typically 24-26°C

2. **Window Open Detection**
   - Reduces target by configured amount
   - Default: -5°C
   - Immediate response

3. **Preset Mode Temperature**
   - Away: 16°C, Eco: 18°C, Comfort: 22°C, etc.
   - Overrides schedule

4. **Schedule Temperature**
   - Time-based temperature profiles
   - Different temps for different times

5. **Base Target Temperature**
   - Manual setting
   - Fallback value

6. **Night Boost** (Additive)
   - Adds to current target
   - Default: +0.5°C during night hours

7. **Presence Boost** (Additive)
   - Adds to current target
   - Default: +2°C when presence detected

**Example Calculation:**
```
Base schedule: 20°C
+ Preset mode (COMFORT): → 22°C
+ Presence detected: +2°C → 24°C
- Window open: -5°C → 19°C
= Final target: 19°C
```

### Sensor State Monitoring

The climate controller automatically monitors all configured sensors every 30 seconds:

**Window Sensors:**
- State values considered "open": `on`, `open`, `true`, `True`
- All other states considered "closed"
- Multiple sensors per area supported (any open triggers action)

**Presence Sensors:**
- State values considered "detected": `on`, `home`, `detected`, `true`, `True`
- All other states considered "no presence"
- Multiple sensors per area supported (any detection triggers boost)

**State Caching:**
Sensor states are cached in area objects:
- `area.window_is_open` - Boolean
- `area.presence_detected` - Boolean
- Updates logged for monitoring

## 🚀 Installation

### Method 1: HACS (Coming Soon)

This integration will be available via HACS in the future.

### Method 2: Manual Installation via SSH

1. **SSH into your Home Assistant OS:****
   ```bash
   ssh -p 22222 root@homeassistant.local
   ```

2. **Navigate to custom_components:**
   ```bash
   cd /config/custom_components
   ```

3. **Clone this repository:**
   ```bash
   git clone https://github.com/TheFlexican/smart_heating.git temp
   mv temp/custom_components/smart_heating .
   rm -rf temp
   ```

4. **Restart Home Assistant:**
   ```bash
   ha core restart
   ```

### Method 3: Deploy Script (Development)

For development, use the included deploy script:

```bash
./deploy.sh
```

Configure your Home Assistant host in the script first.

### Method 4: Development with Docker (Recommended)

For local development and testing:

```bash
# Initial setup - creates Docker containers with HA + MQTT
./setup.sh

# After making code changes - syncs backend + frontend
./sync.sh
```

The `sync.sh` script:
- Builds the React frontend
- Copies Python backend files to the container
- Syncs frontend dist to the container
- Restarts Home Assistant automatically
- Takes ~30 seconds total

## 💻 Development Setup

For developers who want to contribute or customize the integration:

### Quick Setup (macOS)

```bash
# Run automated setup script
./setup_dev_environment.sh

# Open in VS Code and reopen in DevContainer
code .
# Press Cmd+Shift+P → "Remote-Containers: Reopen in Container"
```

The setup script installs:
- Homebrew (if not installed)
- Docker Desktop
- VS Code and required extensions
- DevContainer environment

See [.devcontainer/README.md](.devcontainer/README.md) for detailed development instructions.

## ⚙️ Setup

### 1. Add the Integration

1. Go to **Settings** → **Devices & Services**
2. Click **+ ADD INTEGRATION**
3. Search for **Smart Heating**
4. Click on it to add (no configuration needed)

### 2. Configure OpenTherm Gateway (Optional)

If you have an OpenTherm gateway for boiler control:

1. Go to **Settings** → **Devices & Services**
2. Find the **Smart Heating** integration card
3. Click the **gear icon (⚙️)** to open configuration
4. Select your OpenTherm gateway from the dropdown
5. Enable **OpenTherm Control**
6. Click **Submit**

**Note**: The OpenTherm dropdown only shows devices identified as OpenTherm gateways (entities containing "opentherm" or "otgw" in their name/ID, or with OpenTherm-specific attributes like `control_setpoint`).

The system works perfectly without OpenTherm - this is only needed if you want centralized boiler control across all areas.

## 🎨 Web Interface

Once installed, the Smart Heating panel will automatically appear in your Home Assistant sidebar with a radiator icon (🔥).

You can also access it directly via:
- **Direct URL**: `http://your-ha-instance:8123/smart_heating/`

### Overview Page Features

The main overview page includes:

- **OpenTherm Gateway Status** (top card, if configured)
  - Real-time heating status with pulsing indicator when active
  - Boiler water temperature
  - Target setpoint temperature
  - Current HVAC status (heating/idle)
  - Flame status indicator
  - Updates every 5 seconds
  - Red border when actively heating

- **Area Management** (main section)
  - Create and delete areas
  - Set target temperatures with visual sliders (5-30°C)
  - Enable/disable areas with toggle switches
  - Monitor area states in real-time (heating/idle/off)
  - View current temperature and device count per area

- **Device Panel** (right sidebar)
  - View available Zigbee2MQTT devices
  - Drag and drop devices into areas
  - Real-time device discovery

### Area Detail Page Features

Click on any area to access:
- **Manage Schedules** - Create time-based temperature profiles
- **View History** - Interactive temperature charts with multiple time ranges
- **Configure Settings** - Night boost, hysteresis, and advanced options
- **Real-time Updates** - WebSocket connection for instant feedback

### Building the Frontend

The frontend is a React application that needs to be built before use:

```bash
cd custom_components/smart_heating/frontend
npm install
npm run build
```

For development with hot reload:
```bash
npm run dev
```

See `custom_components/smart_heating/frontend/README.md` for more details.

## 📦 Entities

After installation, the following entities will be created:

### Per Area:
- `climate.area_<area_name>` - Climate entity for temperature control
- `switch.area_<area_name>_control` - Switch to turn area on/off
- `sensor.smart_heating_status` - General status sensor

## 🛠️ Services

### Area Management

#### `smart_heating.enable_area`
Enable heating for a area.

**Parameters:**
- `area_id` (required): Area identifier

**Example:**
```yaml
service: smart_heating.enable_area
data:
  area_id: "living_room"
```

#### `smart_heating.disable_area`
Disable heating for a area.

**Parameters:**
- `area_id` (required): Area identifier

**Example:**
```yaml
service: smart_heating.disable_area
data:
  area_id: "living_room"
```

### Device Management

#### `smart_heating.add_device_to_area`
Add a Zigbee2MQTT device to a area.

**Parameters:**
- `area_id` (required): Area identifier
- `device_id` (required): Zigbee2MQTT device ID (e.g. "0x00158d0001a2b3c4")
- `device_type` (required): Device type (`thermostat`, `temperature_sensor`, `opentherm_gateway`, `valve`)

**Example:**
```yaml
service: smart_heating.add_device_to_area
data:
  area_id: "living_room"
  device_id: "0x00158d0001a2b3c4"
  device_type: "thermostat"
```

#### `smart_heating.remove_device_from_area`
Remove a device from a area.

**Parameters:**
- `area_id` (required): Area identifier
- `device_id` (required): Device identifier

**Example:**
```yaml
service: smart_heating.remove_device_from_area
data:
  area_id: "living_room"
  device_id: "0x00158d0001a2b3c4"
```

### Temperature Control

#### `smart_heating.set_area_temperature`
Set the target temperature for a area.

**Parameters:**
- `area_id` (required): Area identifier
- `temperature` (required): Target temperature in °C (5-30°C)

**Example:**
```yaml
service: smart_heating.set_area_temperature
data:
  area_id: "living_room"
  temperature: 22.0
```

#### `smart_heating.refresh`
Manually refresh Smart Heating data.

**Example:**
```yaml
service: smart_heating.refresh
```

### Schedule Management

#### `smart_heating.add_schedule`
Add a temperature schedule to an area.

**Parameters:**
- `area_id` (required): Area identifier
- `schedule_id` (optional): Unique schedule identifier (auto-generated if not provided)
- `day` (required): Day name (Monday, Tuesday, Wednesday, Thursday, Friday, Saturday, Sunday)
- `start_time` (required): Start time in HH:MM format (24-hour)
- `end_time` (required): End time in HH:MM format (24-hour)
- `temperature` (optional): Target temperature in °C (use either temperature OR preset_mode)
- `preset_mode` (optional): Preset mode to activate (away, eco, comfort, home, sleep, activity) (v0.5.0+)

**Features:**
- **Temperature-Based**: Set fixed temperature for the schedule period
- **Preset-Based**: Activate a preset mode (uses global or custom preset temperature) (v0.5.0+)
- **Cross-Day Support**: End time before start time indicates schedule spans midnight (v0.5.0+)
  - Example: Saturday 22:00 to Sunday 07:00 works correctly

**Examples:**
```yaml
# Temperature-based schedule
service: smart_heating.add_schedule
data:
  area_id: "living_room"
  day: "Monday"
  start_time: "07:00"
  end_time: "22:00"
  temperature: 21.5

# Preset-based schedule (v0.5.0+)
service: smart_heating.add_schedule
data:
  area_id: "bedroom"
  day: "Saturday"
  start_time: "22:00"
  end_time: "07:00"
  preset_mode: "sleep"
```

#### `smart_heating.remove_schedule`
Remove a schedule from an area.

**Parameters:**
- `area_id` (required): Area identifier
- `schedule_id` (required): Schedule identifier

**Example:**
```yaml
service: smart_heating.remove_schedule
data:
  area_id: "living_room"
  schedule_id: "morning_warmup"
```

#### `smart_heating.enable_schedule` / `smart_heating.disable_schedule`
Enable or disable a specific schedule.

**Parameters:**
- `area_id` (required): Area identifier
- `schedule_id` (required): Schedule identifier

### Advanced Settings

#### `smart_heating.set_night_boost`
Configure night boost for an area (gradually increase temperature during configurable night hours).

**Features (v0.5.3+):**
- **Schedule-Aware**: Night boost only applies when NO schedule is active
- **Smart Targeting**: Smart night boost automatically detects first morning schedule (00:00-12:00)
- **Preset Integration**: Uses schedule's preset mode temperature as target
- **Optimal Timing**: Predicts and starts heating at optimal time before schedule

**Parameters:**
- `area_id` (required): Area identifier
- `night_boost_enabled` (optional): Enable/disable manual night boost
- `night_boost_offset` (optional): Temperature offset in °C (0-3°C)
- `night_boost_start_time` (optional): Start time in HH:MM format (default: 22:00)
- `night_boost_end_time` (optional): End time in HH:MM format (default: 06:00)
- `smart_night_boost_enabled` (optional): Enable/disable adaptive learning night boost
- `smart_night_boost_target_time` (optional): Fallback wake-up time (used if no morning schedule) in HH:MM format (e.g., "06:00")
- `weather_entity_id` (optional): Outdoor temperature sensor entity for weather correlation

**Example (Manual Night Boost):**
```yaml
service: smart_heating.set_night_boost
data:
  area_id: "bedroom"
  night_boost_enabled: true
  night_boost_offset: 0.5  # Add 0.5°C during night hours
  night_boost_start_time: "23:00"  # Start at 11 PM
  night_boost_end_time: "07:00"    # End at 7 AM
  # Note: Only applies when NO schedule is active
```

**Example (Smart Night Boost with Schedule Integration):**
```yaml
service: smart_heating.set_night_boost
data:
  area_id: "bedroom"
  smart_night_boost_enabled: true
  smart_night_boost_target_time: "06:00"  # Fallback if no morning schedule
  weather_entity_id: "sensor.outdoor_temperature"
  # Smart boost will:
  # 1. Detect first morning schedule (e.g., 07:00 home preset)
  # 2. Use schedule's preset temperature as target
  # 3. Predict heating time needed
  # 4. Start heating at optimal time to reach target by 07:00
```

#### `smart_heating.set_hysteresis`
Set global temperature hysteresis for heating control. This is the default value used by all areas unless they have a custom override set.

**What is Hysteresis?**
Hysteresis is a temperature buffer that prevents your heating system from constantly turning on and off (short cycling). This protects equipment like boilers, relays, and thermostatic valves from damage.

**How it works:**
- Heating turns ON when temperature falls below `(target - hysteresis)`
- Heating turns OFF when temperature reaches the target
- Example: Target 19.2°C, hysteresis 0.5°C → heating starts at 18.7°C, stops at 19.2°C

**Recommendations:**
- **0.5°C** - Balanced (default, recommended for most radiator systems)
- **1.0°C** - Energy efficient, maximum equipment protection
- **0.1-0.3°C** - Floor heating systems (thermal mass provides natural protection)

**Parameters:**
- `hysteresis` (required): Temperature difference in °C (0.1-2.0°C)

**Example:**
```yaml
service: smart_heating.set_hysteresis
data:
  hysteresis: 0.5  # Heating turns on at target-0.5°C
```

**Area-Specific Override:**
Each area can override the global hysteresis setting in its Settings tab under "Heating Control Settings". This is useful for:
- Floor heating systems that can use lower values (0.1-0.3°C)
- Rooms with specific requirements
- Testing different values per room

#### `smart_heating.set_opentherm_gateway`
Configure the global OpenTherm gateway for boiler control. **This is completely optional** - only use if you have an OpenTherm gateway device.

**Parameters:**
- `gateway_id` (optional): Entity ID of the OpenTherm gateway climate entity (e.g., `climate.opentherm_gateway`)
- `enabled` (optional): Enable/disable OpenTherm control (default: true)

**Example:**
```yaml
service: smart_heating.set_opentherm_gateway
data:
  gateway_id: "climate.opentherm_gateway"  # Select YOUR gateway
  enabled: true
```

**Note**: The system works without OpenTherm. You only need this if you want centralized boiler control across all areas.

#### `smart_heating.set_trv_temperatures`
Configure global settings for temperature-controlled TRVs. **System dynamically detects device capabilities** - no need to configure per-device.

**Parameters:**
- `heating_temp` (optional): Fallback temperature for heating (default: 25.0°C)
- `idle_temp` (optional): Temperature when idle/closed (default: 10.0°C)
- `temp_offset` (optional): Offset above target temp to ensure valve opens (default: 10.0°C)

**Example:**
```yaml
service: smart_heating.set_trv_temperatures
data:
  heating_temp: 25.0   # Fallback if target+offset is lower
  idle_temp: 10.0      # Closes valve when area idle
  temp_offset: 10.0    # Add 10°C to target (21°C target → 31°C TRV)
```

**How it works**:
- For area target 21°C: TRV set to `max(21+10, 25)` = 31°C when heating
- When idle: TRV set to 10°C (closes valve)
- System queries each valve's capabilities automatically

**Note**: Only applies to TRVs without position control (e.g., TS0601 _TZE200_b6wax7g0). Position-controlled valves (number.* entities) use direct 0-100% control.

## 📖 Usage

### Basic Setup Workflow

1. **Install the integration** via the Home Assistant UI
2. **Add areas** in Home Assistant (Settings → Areas & Zones)
3. **Add devices** to areas using the web interface or service calls
4. **Configure temperatures** via climate entities or service calls
5. **Manage areas** via switches or service calls

### Example Configuration

```yaml
# Complete setup example for floor heating with boiler
automation:
  - alias: "Configure Smart Heating System"
    trigger:
      - platform: homeassistant
        event: start
    action:
      # Configure global OpenTherm gateway
      - service: smart_heating.set_opentherm_gateway
        data:
          gateway_id: "climate.opentherm_gateway"
          enabled: true
      
      # Configure TRV settings (automatically applies to temp-controlled valves)
      - service: smart_heating.set_trv_temperatures
        data:
          heating_temp: 25.0   # Fallback temperature
          idle_temp: 10.0      # Close valve when idle
          temp_offset: 10.0    # Add to target for heating (dynamic)
      
      # Setup Living Room area
      - service: smart_heating.add_device_to_area
        data:
          area_id: "living_room"
          device_id: "sensor.living_room_temperature"
          device_type: "temperature_sensor"
      
      - service: smart_heating.add_device_to_area
        data:
          area_id: "living_room"
          device_id: "switch.living_room_pump"
          device_type: "switch"
      
      - service: smart_heating.add_device_to_area
        data:
          area_id: "living_room"
          device_id: "climate.living_room_trv_1"
          device_type: "valve"
      
      # Setup Bedroom area
      - service: smart_heating.add_device_to_area
        data:
          area_id: "bedroom"
          device_id: "sensor.bedroom_temperature"
          device_type: "temperature_sensor"
      
      - service: smart_heating.add_device_to_area
        data:
          area_id: "bedroom"
          device_id: "number.bedroom_valve_position"
          device_type: "valve"
```

### Dashboard Integration

Add climate cards to your dashboard:

```yaml
type: thermostat
entity: climate.area_living_room
```

Or use switch cards:

```yaml
type: entities
entities:
  - entity: switch.area_living_room_control
  - entity: climate.area_living_room
    type: custom:simple-thermostat
```

## 🏗️ Architecture

### Backend Components

- **Area Manager** - Manages heating areas, devices, and schedules
- **Climate Controller** - Controls thermostats based on temperature and schedules (updates every 30 seconds)
- **Schedule Executor** - Applies time-based temperature schedules (checks every minute)
- **Coordinator** - Fetches device states from Home Assistant (30-second interval)
- **History Tracker** - Records temperature data for visualization
  - 5-minute recording interval (300 seconds)
  - Configurable retention period (1-365 days, default: 30 days)
  - Automatic hourly cleanup of expired data
  - No data aggregation - raw data points preserved
  - Flexible querying: preset ranges, custom dates, or all available data
- **REST API** - HTTP endpoints for frontend and external integrations
  - `/api/smart_heating/areas` - Area management
  - `/api/smart_heating/devices` - Device listing
  - `/api/smart_heating/config` - System configuration (OpenTherm, TRV settings)
  - `/api/smart_heating/status` - System status
- **WebSocket** - Real-time updates for frontend
- **Config Flow** - Integration setup with options flow for OpenTherm configuration

### Frontend (React + TypeScript + MUI)

- **ZoneCard** - Area overview with device status and temperature control
- **AreaDetail** - Detailed area view with tabs for overview, schedules, and history
- **OpenThermStatus** - Real-time OpenTherm gateway monitoring with visual status indicators
- **ScheduleManager** - Create and manage time-based temperature profiles
- **TemperatureChart** - Interactive temperature history visualization
- **DeviceList** - Drag-and-drop device assignment

### Device Control Flow

1. **Temperature Monitoring**: Coordinator fetches sensor data → Climate Controller calculates average per area
2. **Heating Decision**: Climate Controller compares current vs target (with hysteresis) → Sends commands to thermostats
3. **Schedule Application**: Schedule Executor checks active schedules → Updates area target temperature
4. **Thermostat Control**: Climate Controller sends `climate.set_temperature` to TRVs
5. **TRV Response**: Physical TRV adjusts valve position → Reports back via MQTT
6. **Display Update**: Coordinator fetches updated states → WebSocket pushes to frontend

**Note**: With mock devices, the valve position doesn't respond to commands since there's no physical hardware. Real TRVs would automatically adjust valve position based on temperature commands.

### Debug Logging

Add this to your `configuration.yaml`:

```yaml
logger:
  default: info
  logs:
    custom_components.smart_heating: debug
```

### File Structure

```
custom_components/smart_heating/
├── __init__.py          # Integration setup and services
├── api.py               # REST API endpoints
├── climate.py           # Climate platform for areas
├── config_flow.py       # UI configuration flow with OpenTherm options
├── const.py             # Constants and configuration
├── coordinator.py       # Data update coordinator
├── manifest.json        # Integration metadata
├── sensor.py            # Sensor platform
├── services.yaml        # Service definitions
├── strings.json         # UI translations
├── switch.py            # Switch platform for area control
├── area_manager.py      # Area management logic
├── websocket.py         # WebSocket handlers
└── frontend/            # React frontend application
    ├── src/
    │   ├── components/
    │   │   ├── OpenThermStatus.tsx  # OpenTherm gateway status card
    │   │   ├── ZoneCard.tsx
    │   │   ├── DevicePanel.tsx
    │   │   └── ...
    │   ├── pages/
    │   │   └── AreaDetail.tsx
    │   └── api.ts       # API client with config endpoint
    └── dist/            # Built frontend assets
```

### Future Features (Roadmap)

- 🤖 **AI-Driven Optimization** - Machine learning for heating patterns
- 📊 **Energy Analytics** - Detailed energy monitoring and cost tracking
- 🔗 **MQTT Auto-discovery** - Automatic detection of Zigbee2MQTT devices
- 👥 **Presence Detection** - Occupancy-based heating control
- 🌡️ **Weather Integration** - Weather-based temperature optimization
- 🔥 **Advanced Boiler Control** - PID control for OpenTherm gateways
- 📱 **Mobile Notifications** - Push notifications for heating events
- 🏡 **Multi-home Support** - Manage multiple locations

## 📝 Version

Current version: **0.3.3**

### Changelog

#### v0.3.19 (2025-12-06)
**Fixed External Temperature Changes Sync**

- 🔄 **Real-time Temperature Sync**
  - Fixed: Area cards now update immediately when thermostat temperature is changed externally
  - Added useEffect hook to sync local temperature state with WebSocket updates
  - Temperature changes made on the device itself now reflect instantly in the UI
  - Works for both main overview zone cards and area detail pages

- ✅ **Testing**
  - Added E2E test: "should sync temperature when changed externally via WebSocket"
  - Verifies temperature display updates correctly after external changes
  - All 86 temperature control tests passing

#### v0.3.18 (2025-12-06)
**Enhanced Presence Sensor Display**

- 👤 **Improved Presence Sensor UI**
  - Presence sensors now show friendly names instead of entity IDs
  - Added status indicators (AWAY/HOME badges) in area detail Settings tab
  - Main overview zone cards display presence status next to heating state
  - Green "HOME" badge or gray "AWAY" badge with person icon
  - Real-time presence state updates via entity state API

- ✅ **Testing Improvements**
  - Added E2E tests for presence status display on main overview
  - Enhanced presence sensor status detection tests
  - All 85 E2E tests passing (4 skipped)

#### v0.3.17 (2025-12-06)
**Universal Device Support & Enhanced Search**

- 🌍 **Language-Independent Device Discovery**
  - Removed all hardcoded keyword filtering (no more "pump", "pomp", "heating", etc.)
  - Truly universal device support - all climate, switch, number, and sensor entities
  - Domain-based device type mapping (climate→thermostat, switch→switch, etc.)
  - Added `subtype` field for better categorization (climate, switch, number, temperature)

- 🔍 **Smart Device Filtering**
  - New filter toggle: "Show only climate & temperature sensors"
  - Default shows climate entities and temperature sensors only
  - Toggle off to see ALL devices (switches, numbers, etc.)
  - Works on both main overview and area detail pages

- 🔎 **Advanced Device Search**
  - Search bar in Available Devices panel (main overview sidebar)
  - Search bar in Area Detail Available Devices section
  - Search by device name, entity ID, or Home Assistant area
  - Real-time filtering with dynamic device count
  - Works together with climate/temperature filter

- 🐛 **Bug Fixes**
  - Fixed TypeScript type safety in Schedule creation (proper null checks)
  - Fixed area.add_schedule null reference issue
  - Improved error handling for missing schedule data

#### v0.3.14 (2025-12-05)
**Improved Device Discovery**

- 🔍 **Enhanced Temperature Sensor Detection**
  - More inclusive temperature sensor discovery
  - Now detects sensors with "temp" or "thermostat" in entity_id
  - Better compatibility with Zigbee2MQTT temperature sensors
  - Improved fallback detection for devices without proper device_class

- 📊 **Better Discovery Logging**
  - Added comprehensive logging for device discovery process
  - Logs each discovered device with type, domain, and HA area
  - Shows which devices are filtered and why
  - Helps troubleshoot missing device issues
  - INFO level summary of total devices found

#### v0.3.13 (2025-12-05)
**Enhanced Hidden Area Device Filtering**

- 🎯 **Comprehensive Device Filtering**
  - Devices now filtered from Available Devices list in multiple ways:
    - Devices directly assigned to hidden Smart Heating areas
    - Devices whose Home Assistant area matches a hidden Smart Heating area
    - Devices whose entity_id or friendly_name contains a hidden area name
  - Catches all bedroom/hidden area devices regardless of HA area assignment
  - Perfect for MQTT devices without explicit HA area configuration
  - Keeps Available Devices panel completely clean of hidden area devices

- 🔄 **Device Refresh Fix**
  - Fixed 500 error when clicking refresh button
  - Removed invalid coordinator reference from API view
  - Refresh now works properly to sync devices from Home Assistant

- 📍 **Device Location Display (v0.3.10)**
  - Available devices show their Home Assistant area assignment
  - Location displayed with 📍 icon below device type
  - Helps identify device physical locations when dragging to areas

#### v0.3.12 (2025-12-05)
**Filter Hidden Area Devices**

- 🔍 **Smart Device Filtering**
  - Available Devices panel no longer shows devices assigned to hidden areas
  - Keeps device list clean and focused on active areas only
  - When area is hidden, its devices are automatically hidden from overview
  - When area is unhidden, its devices reappear in available devices list
  - Prevents clutter in device management interface

#### v0.3.11 (2025-12-05)
**Device Refresh & Sync Feature**

- 🔄 **Device Refresh Button**
  - Added refresh button to Available Devices panel (top-right corner)
  - Re-discovers all MQTT devices from Home Assistant
  - Overwrites existing device configurations with current HA settings
  - Updates device types, names, and area assignments from HA
  - Useful after adding/removing devices or changing HA configurations
  - Shows spinner during refresh operation
  - Automatically reloads device list after refresh completes
  - Backend logs refresh activity (devices updated, available for assignment)

- 🎯 **Improved Device Management**
  - Tooltip explains refresh function: "Refresh devices from Home Assistant"
  - Smooth UX with loading indicator during sync
  - Backend endpoint: `GET /api/smart_heating/devices/refresh`
  - Returns count of updated and available devices

#### v0.3.10 (2025-12-05)
**Show Device Home Assistant Area Locations**

- 📍 **Device Area Location Display**
  - Available devices now show their Home Assistant area assignment
  - Location displayed below device type chip with 📍 icon
  - Helps users quickly identify where devices are physically located
  - Makes it easier to drag devices to the correct Smart Heating areas
  - Uses existing `ha_area_name` data from backend device discovery

#### v0.3.9 (2025-12-05)
**Hide/Show Areas, Thermostat History, Switch Support**

- 👁️ **Hide/Show Areas Feature**
  - Hide non-heating areas from main view to declutter interface
  - Toggle button appears when hidden areas exist
  - "X hidden" badge shows count of hidden areas
  - Menu option on each area card to hide/unhide individual areas
  - Hidden state persisted across restarts
  - Areas can be created on-demand when hiding (no need to pre-configure)

- 📊 **Fixed Thermostat Temperature History**
  - Temperature history now records for areas with thermostats (not just external sensors)
  - Climate controller reads `current_temperature` attribute from thermostats
  - Averages temperature from all sources (sensors + thermostats) for accurate monitoring
  - Fixes "missing data" issue when only thermostats are assigned to an area

- 🔌 **Enhanced Switch Device Support**
  - Switches now properly categorized as "switch" device type (was incorrectly "thermostat")
  - Added detection keywords: "pump", "floor", "relay" for automatic discovery
  - Switches automatically turn ON when area needs heating
  - Switches automatically turn OFF when area reaches target temperature
  - Perfect for floor heating pumps, circulation pumps, and zone relays

- 🎨 **UI Improvements**
  - Removed redundant Devices tab from area detail view
  - Simplified tab structure: Overview (0), Schedule (1), History (2), Settings (3)
  - Fixed "Show Hidden Areas" button to appear when areas are hidden
  - Areas list properly filters hidden areas based on toggle state

- 🐛 **Bug Fixes**
  - Fixed hidden field not being serialized/deserialized in storage
  - Fixed Area creation to use correct constructor parameters
  - Fixed event propagation when clicking hide/unhide menu item

#### v0.3.3 (2025-12-05)
**User-Controlled History Data Management**

- 📊 **Configurable History Retention**
  - User-configurable retention period (1-365 days, default: 30 days)
  - Service: `smart_heating.set_history_retention` with days parameter
  - Automatic hourly cleanup of expired data
  - Immediate cleanup when retention is reduced
  - Settings UI in area detail Settings tab with slider and save button

- 📈 **Enhanced History Querying**
  - Preset time ranges: 6h, 12h, 24h, 3d, 7d, 30d
  - Custom date/time range picker for specific analysis periods
  - Query all available history within retention period
  - REST API endpoints for config and flexible queries
  - No data aggregation - maintains 5-minute resolution

- 🔧 **Backend Improvements**
  - `HistoryTracker` class with configurable retention and scheduled cleanup
  - New API endpoints: `GET/POST /api/smart_heating/history/config`
  - Enhanced history query with hours, start_time, end_time parameters
  - Proper cleanup on integration unload
  - Persistent storage of retention settings

- 🎨 **Frontend Features**
  - History Data Management panel in Settings tab
  - Retention slider with visual markers (1d, 7d, 30d, 90d, 180d, 365d)
  - Custom date/time range picker in History Chart
  - Display of recording interval and current retention
  - API functions: `getHistoryConfig()`, `setHistoryRetention()`, `getHistory()`

#### v0.3.2 (2025-12-05)
**Frontend UI for v0.3.0 Features**

- 🎨 **Complete v0.3.0 Feature UI Implementation**
  - Added Preset Modes dropdown in Settings tab (away, eco, comfort, home, sleep, activity, boost, none)
  - Added Boost Mode controls with temperature and duration inputs
  - Added HVAC Mode selector (heat, cool, auto, off)
  - Added Window Sensors management with add/remove functionality
  - Added Presence Sensors management with add/remove functionality
  - All features now accessible via Settings tab in area detail page

- 🏗️ **Project Restructure**
  - Moved integration folder to root following Home Assistant standard structure
  - Renamed project from `zone_heater_manager` to `smart_heating`
  - Updated all deployment scripts and documentation
  - Updated GitHub repository URL

- 📝 **Documentation**
  - Added comprehensive `.copilot-instructions.md` for development guidance
  - Updated all references to match new project name



#### v0.3.1 (2025-12-05)
**UI/UX Improvements and Real-time Updates**

- 🎨 **UI Enhancements**
  - Moved area enable/disable toggle from area cards to area detail page header
  - Added descriptive labels ("Heating Active" / "Heating Disabled") next to toggle
  - Cleaner area card layout with focus on temperature and status
- 🔄 **Real-time Device Status Updates**
  - Fixed device status to use area target temperature instead of stale device attributes
  - Device heating indicators now update instantly via WebSocket
  - Removed dependency on slow-updating `hvac_action` attribute from thermostats
  - All views (Area Detail, Zone Cards, Device Overview) now show accurate heating status
- 🐛 **Bug Fixes**
  - Fixed 500 errors on `/enable`, `/disable`, and `/temperature` endpoints
  - Added "learning_engine" to coordinator exclusion lists
  - Fixed JSON parsing error when calling endpoints without request body
  - Reorganized API endpoint handling to parse JSON only when needed
- ⚡ **Performance**
  - Device status changes reflect immediately without waiting for entity state sync
  - Improved WebSocket update handling across all components
- 📚 **Technical Details**
  - Device heating status now calculated from: `area.target_temperature > device.current_temperature`
  - Frontend components use area target temperature for all heating decisions
  - Mock/test devices will show static temperatures (expected behavior in test environments)

#### v0.3.0 (2025-12-05)
**Advanced Heating Features Release**
- ✨ **Preset Modes** - 8 quick temperature presets (AWAY, ECO, COMFORT, HOME, SLEEP, ACTIVITY, BOOST, NONE)
  - Per-area preset temperatures with customizable defaults
  - Service: `smart_heating.set_preset_mode`
  - REST API: `POST /areas/{id}/preset_mode`
- ⚡ **Boost Mode** - Temporary high-temperature override
  - Configurable duration (5-180 minutes) and optional custom temperature
  - Automatic expiry with time tracking
  - Services: `set_boost_mode`, `cancel_boost`
  - REST API: `POST /areas/{id}/boost`, `POST /areas/{id}/cancel_boost`
- 🪟 **Window Sensor Integration** - Automatic heating adjustment when windows open
  - Binary sensor support for windows/doors
  - Configurable temperature drop (default: -5°C)
  - Services: `add_window_sensor`, `remove_window_sensor`
  - REST API: `POST/DELETE /areas/{id}/window_sensors`
- 👤 **Presence Detection** - Temperature boost when motion/presence detected
  - Binary sensor support for motion/occupancy/presence
  - Configurable temperature boost (default: +2°C)
  - Services: `add_presence_sensor`, `remove_presence_sensor`
  - REST API: `POST/DELETE /areas/{id}/presence_sensors`
- ❄️ **Frost Protection** - Global minimum temperature to prevent freezing
  - Applies to all areas automatically
  - Default: 7°C minimum
  - Service: `set_frost_protection`
  - REST API: `POST /frost_protection`
- 🌡️ **HVAC Modes** - Support for heat/cool/auto/off modes per area
  - OFF mode completely disables area
  - Service: `set_hvac_mode`
  - REST API: `POST /areas/{id}/hvac_mode`
- 📋 **Schedule Copying** - Duplicate schedules between areas and days
  - Copy to specific days or entire areas
  - Automatic unique ID generation
  - Service: `copy_schedule`
- 🔧 **7-Level Temperature Priority System**
  1. Boost mode (highest)
  2. Window open (reduces temp)
  3. Preset mode
  4. Schedule
  5. Base target
  6. Night boost (additive)
  7. Presence boost (additive)
- 🔄 **Climate Controller Enhancements**
  - Automatic sensor state monitoring every 30 seconds
  - Boost mode expiry checking
  - Frost protection enforcement
  - HVAC mode support
- 📚 **Comprehensive Documentation**
  - Complete service reference with examples
  - REST API endpoint documentation
  - Temperature calculation priority explanation
  - Sensor integration guides
  - Use case examples
- 🐛 Bug fixes and performance improvements

#### v0.2.0 (2025-12-04)
- ✨ **Adaptive Learning System** - Machine learning for optimal heating start times
  - Automatic tracking of every heating cycle with weather correlation
  - Smart night boost: Predicts when to start heating to reach target by wake-up time
  - Home Assistant Statistics API integration for efficient data storage
  - Learning statistics: heating rate, cooldown rate, outdoor correlation, accuracy
  - Frontend UI: Smart Night Boost section in Settings + new Learning tab
  - API endpoint: `/api/smart_heating/areas/{area_id}/learning`
  - Service parameters: `smart_night_boost_enabled`, `smart_night_boost_target_time`, `weather_entity_id`
- 🐛 Fixed service schema validation errors for smart boost parameters
- 🐛 Fixed method signature mismatches in learning engine calls
- 🐛 Fixed WebSocket coordinator lookup errors
- 📚 Comprehensive documentation for adaptive learning system
- 🏆 Minimal performance impact with efficient database storage

#### v0.1.0 (2025-12-04)
- ✨ Area management system with Home Assistant areas integration
- ✨ Climate entities per area with full thermostat control
- ✨ Switch entities for area enable/disable
- ✨ Modern React-based web interface with drag-and-drop
- ✨ **OpenTherm Gateway integration** with visual status monitoring
  - Configuration UI in integration options (gear icon)
  - Real-time status card on overview page
  - Automatic filtering of OpenTherm-compatible devices
- ✨ **Configurable Night Boost** with customizable time periods
  - Set custom start and end times (default: 22:00-06:00)
  - Supports periods crossing midnight (e.g., 23:00-07:00)
  - Time picker UI in area settings
  - Adjustable temperature offset (0-3°C)
- ✨ Schedule management (time-based temperature profiles)
- ✨ Temperature history tracking with interactive charts
- ✨ Real-time device status display in area cards
- ✨ Fahrenheit to Celsius temperature conversion
- ✨ Climate controller with hysteresis control
- ✨ Schedule executor for automatic temperature changes
- ✨ WebSocket support for real-time updates
- ✨ REST API for full programmatic control
- ✨ Zigbee2MQTT device support (thermostats, sensors, valves)
- ✨ **Config flow with options** for OpenTherm gateway selection
- 💾 Persistent storage of configuration and history
- 🔧 MQTT dependency added
- 🐛 Fixed schedule format compatibility between frontend and backend
- 🐛 Fixed device status display (shows actual temperatures instead of type names)
- 🐛 Fixed thermostat target sync when area is idle
- 🐛 Fixed config flow panel registration errors
- 🐛 Fixed "already_configured" issue with proper config entry cleanup

#### v0.0.1 (Initial)
- 🎉 Basic integration setup

## 📄 License

MIT License

## 🤝 Contributing

Contributions are welcome! Feel free to submit a Pull Request.

### Development Setup

1. Clone the repository
2. Make changes in `custom_components/smart_heating/`
3. Test with `./deploy.sh` to your development Home Assistant instance
4. Check logs for errors
5. Submit PR with description of changes

## ❓ Troubleshooting

### Area not being created
- Check if `area_id` is unique
- Check debug logs: add `logger` configuration
- Verify that the integration is loaded correctly

### Device not appearing in area
- Check if `device_id` is correct (Zigbee2MQTT friendly name or IEEE address)
- Verify that `device_type` is set correctly
- Check if Zigbee2MQTT is active and devices are visible

### Temperature not updating
- Check MQTT broker connection
- Verify Zigbee2MQTT configuration
- Check if sensors are publishing data to MQTT

## 🔗 Links

- [Home Assistant Documentation](https://www.home-assistant.io/)
- [Zigbee2MQTT Documentation](https://www.zigbee2mqtt.io/)
- [OpenTherm Gateway](http://otgw.tclcode.com/)
