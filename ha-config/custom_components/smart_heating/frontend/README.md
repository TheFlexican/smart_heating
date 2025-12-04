# Zone Heater Manager Frontend

This is the React-based frontend for the Zone Heater Manager Home Assistant integration.

## Development

### Prerequisites

- Node.js 18 or higher
- npm or yarn

### Setup

```bash
cd custom_components/zone_heater_manager/frontend
npm install
```

### Development Server

```bash
npm run dev
```

This will start a development server at `http://localhost:5173` with hot reloading enabled.

The Vite dev server is configured to proxy API requests to your Home Assistant instance.

### Building for Production

```bash
npm run build
```

This creates an optimized production build in the `dist/` directory, which will be served by Home Assistant.

### Type Checking

```bash
npm run type-check
```

## Architecture

### Components

- **Header** - Top app bar with branding and version info
- **ZoneList** - Grid display of all configured zones
- **ZoneCard** - Individual zone control with temperature slider and toggle
- **CreateZoneDialog** - Modal dialog for creating new zones
- **DevicePanel** - Sidebar showing available Zigbee2MQTT devices

### API Client

The `src/api.ts` file contains all API interaction functions:
- `getZones()` - Fetch all zones
- `createZone()` - Create a new zone
- `deleteZone()` - Delete a zone
- `setZoneTemperature()` - Update zone target temperature
- `enableZone()` / `disableZone()` - Control zone state
- `addDeviceToZone()` / `removeDeviceFromZone()` - Manage zone devices
- `getDevices()` - Fetch available Zigbee2MQTT devices

### TypeScript Types

See `src/types.ts` for all interface definitions:
- `Zone` - Zone configuration and state
- `Device` - Zigbee2MQTT device information

## Future Features

- [ ] Drag-and-drop device assignment with react-beautiful-dnd
- [ ] Real-time WebSocket updates
- [ ] Zone scheduling
- [ ] Analytics dashboard with Recharts
- [ ] Smart heating optimization
- [ ] Multi-language support

## Accessing the Frontend

Once built and deployed, access the frontend through:

1. **Home Assistant Panel**: Navigate to the "Zone Heater Manager" panel in the sidebar
2. **Direct URL**: `http://your-ha-instance:8123/zone_heater_manager/`

## Troubleshooting

### API Calls Failing

Make sure your Home Assistant instance is running and the Zone Heater Manager integration is installed and configured.

### Build Errors

Clear node_modules and reinstall:
```bash
rm -rf node_modules package-lock.json
npm install
```

### Hot Reload Not Working

Make sure you're accessing the dev server directly at `localhost:5173`, not through Home Assistant.
