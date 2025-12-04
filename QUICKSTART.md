# Quick Start Guide

Get Smart Heating running in 5 minutes!

## Prerequisites

- Home Assistant OS/Supervised
- SSH access
- Node.js 18+ installed

## Installation (3 steps)

### 1. Install Integration

```bash
# SSH to Home Assistant
ssh -p 22222 root@homeassistant.local

# Clone repository
cd /config/custom_components
git clone https://github.com/TheFlexican/smart_heating.git temp
mv temp/custom_components/smart_heating .
rm -rf temp
```

### 2. Build Frontend

```bash
cd /config/custom_components/smart_heating
./build_frontend.sh
```

### 3. Restart & Add Integration

```bash
ha core restart
```

Then:
1. Go to **Settings** → **Devices & Services**
2. Click **+ ADD INTEGRATION**
3. Search for **Smart Heating**
4. Click to add

## Access the Interface

The **Smart Heating** panel appears automatically in your Home Assistant sidebar with a radiator icon 🔥

Or navigate to: `http://your-ha-instance:8123/smart_heating/`

## Create Your First Zone

1. Click **+ Create Zone** in the web interface
2. Enter zone name (e.g., "Living Room")
3. Set initial temperature
4. Click **Create**

## Next Steps

- Configure MQTT/Zigbee2MQTT for device discovery
- Add devices to your areas
- Create automations using the climate entities
- Explore the REST API for advanced integrations

## Need Help?

- Read [INSTALL.md](INSTALL.md) for detailed installation
- Check [ARCHITECTURE.md](ARCHITECTURE.md) to understand the system
- See [DEVELOPER.md](DEVELOPER.md) for development info
- Visit [GitHub Issues](https://github.com/TheFlexican/smart_heating/issues)

## Key Features

✅ **Automatic Sidebar Panel** - No manual configuration needed
✅ **Modern Web UI** - React-based interface with Material Design
✅ **Real-time Updates** - See changes instantly
✅ **Temperature Sliders** - Visual control (5-30°C)
✅ **Zone Management** - Create, delete, enable/disable areas
✅ **Climate Entities** - Full Home Assistant integration
✅ **Service Calls** - Automation-ready

Happy heating! 🔥
