# Installation Guide - Zone Heater Manager

Complete installation guide for the Zone Heater Manager Home Assistant integration.

## Prerequisites

- Home Assistant OS or Supervised installation
- SSH access to your Home Assistant instance
- MQTT integration configured (for Zigbee2MQTT)
- Node.js 18+ (for building the frontend)

## Quick Install

### Step 1: Install the Integration

**Option A: Via SSH (Recommended)**

```bash
# SSH into Home Assistant
ssh -p 22222 root@homeassistant.local

# Navigate to custom_components
cd /config/custom_components

# Clone the repository
git clone https://github.com/TheFlexican/zone_heater_manager.git temp
mv temp/custom_components/zone_heater_manager .
rm -rf temp
```

**Option B: Manual Download**

1. Download the latest release from GitHub
2. Extract the `custom_components/zone_heater_manager` folder
3. Copy it to your Home Assistant `config/custom_components/` directory

### Step 2: Build the Frontend

The React frontend needs to be built before it can be used:

```bash
# Navigate to the integration directory
cd /config/custom_components/zone_heater_manager

# Run the build script
./build_frontend.sh
```

Or manually:

```bash
cd /config/custom_components/zone_heater_manager/frontend
npm install
npm run build
```

### Step 3: Restart Home Assistant

```bash
ha core restart
```

Or restart via the UI: **Settings** → **System** → **Restart**

### Step 4: Add the Integration

1. Go to **Settings** → **Devices & Services**
2. Click **+ ADD INTEGRATION**
3. Search for **Zone Heater Manager**
4. Click on it to add (no configuration needed)

### Step 5: Access the Web Interface

The **Zone Heater Manager** panel will automatically appear in your Home Assistant sidebar with a radiator icon.

Alternatively, navigate directly to: `http://your-ha-instance:8123/zone_heater_manager/`

## Post-Installation

### Create Your First Zone

Via the Web Interface:
1. Open the Zone Heater Manager panel
2. Click **+ Create Zone**
3. Enter zone name (e.g., "Living Room")
4. Set initial temperature
5. Click **Create**

Via Service Call:
```yaml
service: zone_heater_manager.create_zone
data:
  zone_id: "living_room"
  zone_name: "Living Room"
  temperature: 21.0
```

### Add Devices to Zones

1. Make sure Zigbee2MQTT is running and devices are paired
2. In the web interface, drag devices from the right panel to zone cards
3. Or use service calls:

```yaml
service: zone_heater_manager.add_device_to_zone
data:
  zone_id: "living_room"
  device_id: "zigbee2mqtt/0x00158d0001a2b3c4"
```

### Configure Automations

Use the climate and switch entities in your automations:

```yaml
automation:
  - alias: "Living Room Morning Heat"
    trigger:
      - platform: time
        at: "06:00:00"
    action:
      - service: climate.set_temperature
        target:
          entity_id: climate.zone_living_room
        data:
          temperature: 22
      - service: switch.turn_on
        target:
          entity_id: switch.zone_living_room_control
```

## Troubleshooting

### Frontend Not Loading

**Problem**: Blank page or 404 error when accessing the web interface.

**Solution**:
1. Ensure frontend was built: `ls /config/custom_components/zone_heater_manager/frontend/dist`
2. Rebuild if necessary: `./build_frontend.sh`
3. Restart Home Assistant
4. Clear browser cache

### Integration Not Showing Up

**Problem**: Can't find "Zone Heater Manager" in integrations list.

**Solution**:
1. Verify installation path: `/config/custom_components/zone_heater_manager/manifest.json` should exist
2. Check Home Assistant logs for errors: **Settings** → **System** → **Logs**
3. Restart Home Assistant
4. Force refresh browser (Ctrl+F5 or Cmd+Shift+R)

### No Zigbee Devices Found

**Problem**: Device panel is empty.

**Solution**:
1. Verify MQTT integration is installed and running
2. Verify Zigbee2MQTT is running and publishing to MQTT
3. Check MQTT topic configuration matches your Zigbee2MQTT setup
4. Look for devices in MQTT Explorer or similar tool

### Service Calls Not Working

**Problem**: Service calls return errors or don't execute.

**Solution**:
1. Enable debug logging in `configuration.yaml`:
   ```yaml
   logger:
     default: info
     logs:
       custom_components.zone_heater_manager: debug
   ```
2. Check logs for detailed error messages
3. Verify zone_id and device_id values are correct
4. Ensure zone exists before adding devices

### Build Script Fails

**Problem**: `./build_frontend.sh` fails with errors.

**Solution**:
1. Ensure Node.js 18+ is installed: `node -v`
2. Install Node.js if missing: https://nodejs.org/
3. Clear npm cache: `cd frontend && rm -rf node_modules package-lock.json && npm install`
4. Check for specific error messages in build output

## Updating

To update to the latest version:

```bash
cd /config/custom_components
rm -rf zone_heater_manager
git clone https://github.com/TheFlexican/zone_heater_manager.git temp
mv temp/custom_components/zone_heater_manager .
rm -rf temp

cd zone_heater_manager
./build_frontend.sh

ha core restart
```

## Uninstalling

1. Remove the integration via UI: **Settings** → **Devices & Services** → **Zone Heater Manager** → **Delete**
2. Delete files:
   ```bash
   rm -rf /config/custom_components/zone_heater_manager
   ```
3. Restart Home Assistant

## Development Setup

For developers who want to work on the integration:

### Python Development

```bash
# Clone the repository
git clone https://github.com/TheFlexican/zone_heater_manager.git
cd zone_heater_manager

# Install development dependencies (optional)
pip install -r requirements_dev.txt  # if exists
```

### Frontend Development

```bash
cd custom_components/zone_heater_manager/frontend

# Install dependencies
npm install

# Start dev server with hot reload
npm run dev

# Build for production
npm run build
```

The dev server runs on `http://localhost:5173` and proxies API requests to your Home Assistant instance.

### Deploy Script

Use the included deploy script to quickly push changes to your HA instance:

```bash
# Edit deploy.sh to set your HA host
vim deploy.sh

# Deploy
./deploy.sh
```

## Support

- **Issues**: https://github.com/TheFlexican/zone_heater_manager/issues
- **Discussions**: https://github.com/TheFlexican/zone_heater_manager/discussions
- **Documentation**: See README.md and other docs in the repository

## Next Steps

- Configure zones and add devices
- Create automations using the climate entities
- Explore the REST API for advanced integrations
- Check out example configurations in `examples/`
