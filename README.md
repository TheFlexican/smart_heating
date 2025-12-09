# Smart Heating

[![Version](https://img.shields.io/badge/version-0.5.12-blue.svg)](https://github.com/TheFlexican/smart_heating/releases)
[![HACS](https://img.shields.io/badge/HACS-Custom-orange.svg)](https://github.com/hacs/integration)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)

A Home Assistant custom integration for intelligent multi-zone heating control with adaptive learning. Features a modern React-based web interface for easy configuration and real-time monitoring.

[🇳🇱 Nederlandse versie](README.nl.md) | [📚 Full Documentation](docs/en/)

## Features

### 🏠 Smart Zone Control
- **Multi-zone heating management** - Create and manage unlimited heating zones
- **Universal device support** - Works with ANY Home Assistant climate integration (Nest, Ecobee, Zigbee2MQTT, etc.)
- **Real-time status updates** - WebSocket-based live monitoring with <3s response time
- **Manual override detection** - Automatically detects and respects external thermostat changes

### 📅 Intelligent Scheduling
- **Flexible schedules** - Time-based temperature profiles with multi-day support
- **Preset mode scheduling** - Use preset modes (Away, Eco, Comfort) instead of fixed temperatures
- **Date-specific schedules** - One-time schedules for holidays and special events
- **Cross-day support** - Schedules can span midnight (e.g., Saturday 22:00 - Sunday 07:00)

### 🧠 Adaptive Learning
- **Machine learning** - Learns heating patterns and outdoor temperature correlation
- **Smart night boost** - Predicts optimal heating start time for morning schedules
- **Weather-aware** - Uses outdoor temperature to optimize heating efficiency
- **Persistent learning** - Stores data using Home Assistant Statistics API

### 🎯 Preset Modes & Automation
- **6 preset modes** - Away, Eco, Comfort, Home, Sleep, Activity (+ Boost)
- **Global presets** - Configure default temperatures once, apply to all zones
- **Presence detection** - Automatic mode switching based on occupancy
- **Window sensors** - Auto-adjust or pause heating when windows/doors open

### 🔒 Safety & Control
- **Frost protection** - Global minimum temperature to prevent freezing
- **Emergency shutdown** - Smoke/CO detector integration for safety
- **HVAC mode support** - Heating, cooling, auto, and off modes
- **Smart switch control** - Auto-shutdown circulation pumps when not heating

### 📊 Monitoring & Debugging
- **Temperature history** - Track and visualize trends (5-min resolution, 1-365 days retention)
- **Development logs** - Per-zone logging with detailed strategy decisions
- **Interactive charts** - Customizable time ranges with preset filters
- **Event filtering** - Color-coded event types with one-click filtering

### 🎨 Modern Web Interface
- **React-based GUI** - Fast, responsive, and intuitive
- **Material-UI design** - Clean, modern interface with dark mode support
- **Drag-and-drop** - Easy device assignment and schedule management
- **Real-time updates** - Live status via WebSocket, no page refresh needed
- **Internationalization** - Full support for English and Dutch (Nederlands)

### 🔄 Backup & Restore
- **Configuration export** - Download complete settings as JSON
- **Import with preview** - Review changes before applying
- **Automatic backups** - Created before each import for safety
- **Version compatibility** - Smart detection of configuration versions

## Quick Start

### Installation

1. **HACS (Recommended)**
   - Add custom repository: `https://github.com/TheFlexican/smart_heating`
   - Search for "Smart Heating" in HACS
   - Install and restart Home Assistant

2. **Manual Installation**
   ```bash
   cd /config/custom_components
   git clone https://github.com/TheFlexican/smart_heating.git
   ```

3. **Configuration**
   - Go to Settings → Devices & Services → Add Integration
   - Search for "Smart Heating"
   - Configure initial settings

### Access Web Interface

Navigate to: `http://your-home-assistant:8123/api/smart_heating/`

## Key Settings

### Global Settings
- **Preset Temperatures** - Default temps for Away, Eco, Comfort, Home, Sleep, Activity
- **Presence Sensors** - Configure once, apply to all zones
- **Frost Protection** - Minimum temperature (default: 7°C)
- **Hysteresis** - Temperature buffer to prevent rapid cycling (0.1-2.0°C)
- **Safety Sensors** - Smoke/CO detectors for emergency shutdown

### Zone Settings
- **Target Temperature** - Base temperature for the zone
- **Devices** - Assign thermostats, sensors, valves, switches
- **Schedules** - Time-based temperature or preset profiles
- **Night Boost** - Pre-heating during configurable night hours
- **Boost Mode** - Temporary high-temperature boost (configurable duration)
- **Window Sensors** - Auto-adjust when windows/doors open
- **Presence Detection** - Choose global or zone-specific sensors
- **Switch Control** - Auto-shutdown pumps when not heating

### Advanced Features
- **Adaptive Learning** - Enable smart night boost with weather prediction
- **Manual Override** - System respects external thermostat adjustments
- **Vacation Mode** - Set start/end dates with away temperature
- **Hysteresis Override** - Per-zone custom values (useful for floor heating)
- **Import/Export** - Backup and restore complete configuration with one click

## Supported Devices

### Climate Entities
- ✅ **All HA climate integrations** - Google Nest, Ecobee, generic_thermostat, Z-Wave, Zigbee2MQTT
- ✅ **Thermostats** - Any climate.* entity with temperature control
- ✅ **AC units** - Supports heating, cooling, and auto modes

### Sensors
- ✅ **Temperature sensors** - sensor.* entities with device_class: temperature
- ✅ **Window/door sensors** - binary_sensor.* for open/close detection
- ✅ **Presence sensors** - Person, device_tracker, motion sensors
- ✅ **Safety sensors** - Smoke detectors, CO detectors (binary_sensor.*)

### Other Devices
- ✅ **Valves** - number.* or climate.* entities with position control
- ✅ **Switches** - switch.* for pumps, relays, etc.
- ✅ **Weather** - For outdoor temperature in adaptive learning

## Documentation

### User Guides
- 📖 [Full Documentation](docs/en/) - Complete feature guide
- 🏗️ [Architecture](docs/en/ARCHITECTURE.md) - Technical design and components
- 💻 [Developer Guide](DEVELOPER.md) - Development setup and workflow
- 📝 [Changelog](CHANGELOG.md) - Version history and release notes

### Quick References
- ⚡ [Testing Guide](TESTING_QUICKSTART.md) - Run tests and verify coverage
- 🔧 [API Reference](docs/en/ARCHITECTURE.md#api-endpoints) - REST API endpoints
- 🐛 [Troubleshooting](docs/en/#troubleshooting) - Common issues and solutions

## REST API

Full REST API for programmatic control:

```bash
# Get all zones
GET /api/smart_heating/areas

# Update zone temperature
POST /api/smart_heating/areas/{area_id}/temperature
{"temperature": 21.5}

# Enable boost mode
POST /api/smart_heating/areas/{area_id}/boost
{"duration": 60, "temperature": 24}

# Add schedule
POST /api/smart_heating/areas/{area_id}/schedule
{
  "days": ["monday", "tuesday"],
  "start_time": "07:00",
  "end_time": "09:00",
  "preset_mode": "comfort"
}
```

See [API Documentation](docs/en/ARCHITECTURE.md#api-endpoints) for complete endpoint list.

## Contributing

Contributions are welcome! Please see [DEVELOPER.md](DEVELOPER.md) for development setup.

### Development Workflow
```bash
# Clone repository
git clone https://github.com/TheFlexican/smart_heating.git

# Install dependencies
cd smart_heating/frontend
npm install

# Run tests
cd ../..
./run_tests.sh  # Python unit tests
cd tests/e2e && npm test  # E2E tests

# Format and lint (pre-commit hooks)
git commit -m "Your changes"  # Auto-runs black + ruff
```

## License

MIT License - see [LICENSE](LICENSE) file for details.

## Support

- 🐛 [Report bugs](https://github.com/TheFlexican/smart_heating/issues)
- 💡 [Request features](https://github.com/TheFlexican/smart_heating/issues)
- 📖 [Full documentation](docs/en/)
- 🇳🇱 [Nederlandse documentatie](docs/nl/)

## Links

- [GitHub Repository](https://github.com/TheFlexican/smart_heating)
- [HACS Integration](https://hacs.xyz/)
- [Home Assistant](https://www.home-assistant.io/)
- [Releases](https://github.com/TheFlexican/smart_heating/releases)
