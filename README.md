# Smart Heating

A Home Assistant custom integration for managing multi-area heating systems with Zigbee2MQTT devices. Features a modern React-based web interface for easy area configuration and device management.

## ✨ Features

- 🏠 **Multi-area heating control** - Create and manage multiple heating areas
- 🌡️ **Zigbee2MQTT integration** - Support for thermostats, temperature sensors and OpenTherm gateways
- 🎛️ **Web-based GUI** - Modern React interface with drag-and-drop device management
- 📅 **Smart Scheduling** - Time-based temperature profiles with day-of-week selection
- 🌙 **Night Boost** - Gradual temperature increase during night hours (22:00-06:00)
- 📊 **Temperature History** - Track and visualize temperature trends with interactive charts
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

- **Thermostat** - Zigbee thermostats for temperature control
- **Temperature Sensor** - Temperature sensors for area monitoring
- **OpenTherm Gateway** - Zigbee-to-OpenTherm gateways for boiler control
- **Valve** - Smart radiator valves/thermostatic radiator valves (TRVs)

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

1. Go to **Settings** → **Devices & Services**
2. Click **+ ADD INTEGRATION**
3. Search for **Smart Heating**
4. Click on it to add (no configuration needed)

## 🎨 Web Interface

Once installed, the Smart Heating panel will automatically appear in your Home Assistant sidebar with a radiator icon (🔥).

You can also access it directly via:
- **Direct URL**: `http://your-ha-instance:8123/smart_heating/`

The web interface allows you to:
- Create and delete areas
- Set target temperatures with visual sliders (5-30°C)
- Enable/disable areas with toggle switches
- View available Zigbee2MQTT devices in the right panel
- Drag and drop devices into areas
- Monitor area states in real-time (heating/idle/off)
- **Manage Schedules** - Create time-based temperature profiles
- **View History** - Interactive temperature charts with multiple time ranges
- **Configure Settings** - Night boost, hysteresis, and advanced options
- Real-time WebSocket updates for instant feedback

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
Configure night boost for an area (gradually increase temperature during night hours).

**Parameters:**
- `area_id` (required): Area identifier
- `night_boost_enabled` (optional): Enable/disable night boost
- `night_boost_offset` (optional): Temperature offset in °C (0-3°C)

**Example:**
```yaml
service: smart_heating.set_night_boost
data:
  area_id: "bedroom"
  night_boost_enabled: true
  night_boost_offset: 0.5  # Add 0.5°C during night hours
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

## 📖 Usage

### Basic Setup Workflow

1. **Install the integration** via the Home Assistant UI
2. **Add areas** in Home Assistant (Settings → Areas & Zones)
3. **Add devices** to areas using the web interface or service calls
4. **Configure temperatures** via climate entities or service calls
5. **Manage areas** via switches or service calls

### Example Configuration

```yaml
# Automation to add devices to area
automation:
  - alias: "Setup Living Room Devices"
    trigger:
      - platform: homeassistant
        event: start
    action:
      # Add thermostat
      - service: smart_heating.add_device_to_area
        data:
          area_id: "living_room"
          device_id: "0x00158d0001a2b3c4"
          device_type: "thermostat"
      
      # Add temperature sensor
      - service: smart_heating.add_device_to_area
        data:
          area_id: "living_room"
          device_id: "0x00158d0001a2b3c5"
          device_type: "temperature_sensor"
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
- **History Tracker** - Records temperature data for visualization (5-minute intervals)
- **REST API** - HTTP endpoints for frontend and external integrations
- **WebSocket** - Real-time updates for frontend

### Frontend (React + TypeScript + MUI)

- **ZoneCard** - Area overview with device status and temperature control
- **AreaDetail** - Detailed area view with tabs for overview, schedules, and history
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
├── climate.py           # Climate platform for areas
├── config_flow.py       # UI configuration flow
├── const.py             # Constants and configuration
├── coordinator.py       # Data update coordinator
├── manifest.json        # Integration metadata
├── sensor.py            # Sensor platform
├── services.yaml        # Service definitions
├── strings.json         # UI translations
├── switch.py            # Switch platform for area control
└── area_manager.py      # Area management logic
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

Current version: **0.1.0**

### Changelog

#### v0.1.0 (2025-12-04)
- ✨ Area management system with Home Assistant areas integration
- ✨ Climate entities per area with full thermostat control
- ✨ Switch entities for area enable/disable
- ✨ Modern React-based web interface with drag-and-drop
- ✨ Schedule management (time-based temperature profiles)
- ✨ Temperature history tracking with interactive charts
- ✨ Real-time device status display in area cards
- ✨ Fahrenheit to Celsius temperature conversion
- ✨ Climate controller with hysteresis control
- ✨ Schedule executor for automatic temperature changes
- ✨ WebSocket support for real-time updates
- ✨ REST API for full programmatic control
- ✨ Zigbee2MQTT device support (thermostats, sensors, valves)
- 💾 Persistent storage of configuration and history
- 🔧 MQTT dependency added
- 🐛 Fixed schedule format compatibility between frontend and backend
- 🐛 Fixed device status display (shows actual temperatures instead of type names)
- 🐛 Fixed thermostat target sync when area is idle

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
