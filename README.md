# Smart Heating

A Home Assistant custom integration for managing multi-area heating systems with Zigbee2MQTT devices. Features a modern React-based web interface for easy area configuration and device management.

## ✨ Features

- 🏠 **Multi-zone heating control** - Create and manage multiple heating areas
- 🌡️ **Zigbee2MQTT integration** - Support for thermostats, temperature sensors and OpenTherm gateways
- 🎛️ **Web-based GUI** - Modern React interface with drag-and-drop device management
- 🌐 **REST API** - Full API for programmatic control
- 📡 **WebSocket support** - Real-time updates
- 🎛️ **Climate entities** - Full thermostat control per area
- 🔌 **Switch entities** - Easy area on/off control
- 📊 **Sensor entities** - System status monitoring
- 🛠️ **Service calls** - Manage areas and devices via Home Assistant services
- 💾 **Persistent storage** - Configuration automatically saved
- 🔄 **Auto-update** - Data coordinator with 30-second interval
- 📝 **Debug logging** - Extensive logging for troubleshooting

## 📋 Supported Device Types

- **Thermostat** - Zigbee thermostats for temperature control
- **Temperature Sensor** - Temperature sensors for zone monitoring
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
- Drag and drop devices into areas (coming soon)
- Monitor zone states in real-time (heating/idle/off)

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

### Per Zone:
- `climate.area_<area_name>` - Climate entity for temperature control
- `switch.area_<area_name>_control` - Switch to turn area on/off
- `sensor.smart_heating_status` - General status sensor

## 🛠️ Services

### Zone Management

#### `smart_heating.create_zone`
Create a new heating area.

**Parameters:**
- `area_id` (required): Unique identifier (e.g. "living_room")
- `area_name` (required): Display name (e.g. "Living Room")
- `temperature` (optional): Initial target temperature in °C (default: 20.0)

**Example:**
```yaml
service: smart_heating.create_zone
data:
  area_id: "living_room"
  area_name: "Living Room"
  temperature: 21.5
```

#### `smart_heating.delete_zone`
Delete an existing area.

**Parameters:**
- `area_id` (required): Zone identifier

**Example:**
```yaml
service: smart_heating.delete_zone
data:
  area_id: "living_room"
```

#### `smart_heating.enable_zone`
Enable heating for a area.

**Parameters:**
- `area_id` (required): Zone identifier

**Example:**
```yaml
service: smart_heating.enable_zone
data:
  area_id: "living_room"
```

#### `smart_heating.disable_zone`
Disable heating for a area.

**Parameters:**
- `area_id` (required): Zone identifier

**Example:**
```yaml
service: smart_heating.disable_zone
data:
  area_id: "living_room"
```

### Device Management

#### `smart_heating.add_device_to_zone`
Add a Zigbee2MQTT device to a area.

**Parameters:**
- `area_id` (required): Zone identifier
- `device_id` (required): Zigbee2MQTT device ID (e.g. "0x00158d0001a2b3c4")
- `device_type` (required): Device type (`thermostat`, `temperature_sensor`, `opentherm_gateway`, `valve`)

**Example:**
```yaml
service: smart_heating.add_device_to_zone
data:
  area_id: "living_room"
  device_id: "0x00158d0001a2b3c4"
  device_type: "thermostat"
```

#### `smart_heating.remove_device_from_zone`
Remove a device from a area.

**Parameters:**
- `area_id` (required): Zone identifier
- `device_id` (required): Device identifier

**Example:**
```yaml
service: smart_heating.remove_device_from_zone
data:
  area_id: "living_room"
  device_id: "0x00158d0001a2b3c4"
```

### Temperature Control

#### `smart_heating.set_area_temperature`
Set the target temperature for a area.

**Parameters:**
- `area_id` (required): Zone identifier
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

## 📖 Usage

### Basic Setup Workflow

1. **Install the integration** via the Home Assistant UI
2. **Create areas** using the `create_zone` service
3. **Add devices** using the `add_device_to_zone` service
4. **Configure temperatures** via climate entities or service calls
5. **Manage areas** via switches or service calls

### Example Configuration

```yaml
# Automation to create areas at startup
automation:
  - alias: "Setup Heating Zones"
    trigger:
      - platform: homeassistant
        event: start
    action:
      # Create living room zone
      - service: smart_heating.create_zone
        data:
          area_id: "living_room"
          area_name: "Living Room"
          temperature: 21.0
      
      # Add thermostat
      - service: smart_heating.add_device_to_zone
        data:
          area_id: "living_room"
          device_id: "0x00158d0001a2b3c4"
          device_type: "thermostat"
      
      # Add temperature sensor
      - service: smart_heating.add_device_to_zone
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

## 🔧 Development

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
├── switch.py            # Switch platform for zone control
└── area_manager.py      # Zone management logic
```

### Future Features (Roadmap)

- 🎨 **Web GUI** - Drag & drop interface for zone and device management
- 🤖 **Smart Heating** - AI-driven heating optimization
- 📊 **Analytics** - Energy monitoring and statistics
- 🔗 **MQTT Auto-discovery** - Automatic detection of Zigbee2MQTT devices
- ⏱️ **Schedules** - Time-based temperature profiles per area
- 👥 **Presence Detection** - Presence-based heating
- 🌡️ **Multi-sensor averaging** - Multiple sensors per area
- 🔥 **Boiler Control** - Direct OpenTherm boiler control

## 📝 Version

Current version: **0.1.0**

### Changelog

#### v0.1.0 (2025-12-04)
- ✨ Zone management system
- ✨ Climate entities per area
- ✨ Switch entities for zone control
- ✨ Extensive service calls
- ✨ Zigbee2MQTT device support
- ✨ Persistent storage of configuration
- 🔧 MQTT dependency added

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

### Zone not being created
- Check if `area_id` is unique
- Check debug logs: add `logger` configuration
- Verify that the integration is loaded correctly

### Device not appearing in zone
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
