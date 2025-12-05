# Smart Heating

A Home Assistant custom integration for managing multi-area heating systems with Zigbee2MQTT devices. Features a modern React-based web interface for easy area configuration and device management.

## ✨ Features

- 🏠 **Multi-area heating control** - Create and manage multiple heating areas
- 🌡️ **Zigbee2MQTT integration** - Support for thermostats, temperature sensors and OpenTherm gateways
- 🎛️ **Web-based GUI** - Modern React interface with drag-and-drop device management
- 📅 **Smart Scheduling** - Time-based temperature profiles with day-of-week selection
- 🌙 **Night Boost** - Configurable temperature increase during night hours (customizable start/end times)
- 🧠 **Adaptive Learning** - Machine learning system that learns heating patterns and weather correlation
  - Automatically predicts heating time based on outdoor temperature
  - Smart night boost: Starts heating at optimal time to reach target by wake-up
  - Uses Home Assistant Statistics API for efficient database storage
  - Tracks heating rates, cooldown rates, and outdoor temperature correlations
- 🎯 **Preset Modes** - Quick temperature presets (AWAY, ECO, COMFORT, HOME, SLEEP, ACTIVITY, BOOST)
- ⚡ **Boost Mode** - Temporary high-temperature boost with configurable duration
- 🪟 **Window Sensor Integration** - Configurable actions (turn off, reduce temp, or none) when windows/doors open with custom temperature drops
- 👤 **Presence Detection** - Advanced presence-based heating with separate away/home actions, supports motion sensors, Person entities, and Device Trackers
- ❄️ **Frost Protection** - Global minimum temperature to prevent freezing
- 🌡️ **HVAC Modes** - Support for heating, cooling, auto, and off modes
- 📋 **Schedule Copying** - Duplicate schedules between areas and days
- 📊 **Temperature History** - Track and visualize temperature trends with interactive charts
  - Configurable retention period (1-365 days, default 30 days)
  - Custom time range selection with date/time picker
  - Preset ranges: 6h, 12h, 24h, 3d, 7d, 30d
  - 5-minute data resolution (never aggregated)
  - Automatic cleanup every hour
- ⚙️ **Advanced Settings** - Hysteresis control, temperature limits, and fine-tuning
- 🌐 **REST API** - Full API for programmatic control
- 📡 **WebSocket support** - Real-time updates
- 🎛️ **Climate entities** - Full thermostat control per area
- 🔌 **Switch entities** - Easy area on/off control
- 📊 **Sensor entities** - System status monitoring
- 🛠️ **Service calls** - Comprehensive service API for automation
- 💾 **Persistent storage** - Configuration and history automatically saved
- 🔄 **Auto-update** - Data coordinator with 30-second interval
- 📝 **Debug logging** - Extensive logging for troubleshooting

## 📋 Supported Device Types

### Per-Area Devices
- **Thermostat** - Room thermostats for direct temperature control
- **Temperature Sensor** - External temperature measurement for area monitoring
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

Boost temperature when presence/motion is detected for enhanced comfort.

**How It Works:**
1. Add presence/motion sensors to an area
2. When motion detected → automatic temperature boost (default: +2°C)
3. When no presence → boost removed
4. Works additively with other temperature settings
5. Ideal for rooms used intermittently

**Configuration:**
```yaml
# Add presence sensor
service: smart_heating.add_presence_sensor
data:
  area_id: "home_office"
  entity_id: "binary_sensor.office_motion"

# Remove presence sensor
service: smart_heating.remove_presence_sensor
data:
  area_id: "home_office"
  entity_id: "binary_sensor.office_motion"
```

**Customization:**
Per-area setting (in `area_manager.py`):
- `presence_temp_boost`: Temperature increase in °C (default: 2.0)

**Supported Sensor Types:**
- Motion sensors (`binary_sensor` with `device_class: motion`)
- Occupancy sensors (`device_class: occupancy`)
- Presence sensors (`device_class: presence`)
- Person detection sensors

**REST API:**
```bash
# Add sensor
POST /api/smart_heating/areas/home_office/presence_sensors
{"entity_id": "binary_sensor.office_motion"}

# Remove sensor
DELETE /api/smart_heating/areas/home_office/presence_sensors/binary_sensor.office_motion
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
- `temperature` (required): Target temperature in °C

**Example:**
```yaml
service: smart_heating.add_schedule
data:
  area_id: "living_room"
  day: "Monday"
  start_time: "07:00"
  end_time: "22:00"
  temperature: 21.5
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

**Parameters:**
- `area_id` (required): Area identifier
- `night_boost_enabled` (optional): Enable/disable manual night boost
- `night_boost_offset` (optional): Temperature offset in °C (0-3°C)
- `night_boost_start_time` (optional): Start time in HH:MM format (default: 22:00)
- `night_boost_end_time` (optional): End time in HH:MM format (default: 06:00)
- `smart_night_boost_enabled` (optional): Enable/disable adaptive learning night boost
- `smart_night_boost_target_time` (optional): Desired wake-up time in HH:MM format (e.g., "06:00")
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
```

**Example (Smart Night Boost with Learning):**
```yaml
service: smart_heating.set_night_boost
data:
  area_id: "bedroom"
  smart_night_boost_enabled: true
  smart_night_boost_target_time: "06:00"  # Room ready by 6 AM
  weather_entity_id: "sensor.outdoor_temperature"  # For weather correlation
```

#### `smart_heating.set_hysteresis`
Set global temperature hysteresis for heating control.

**Parameters:**
- `hysteresis` (required): Temperature difference in °C (0.1-2.0°C)

**Example:**
```yaml
service: smart_heating.set_hysteresis
data:
  hysteresis: 0.5  # Heating turns on at target-0.5°C
```

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
