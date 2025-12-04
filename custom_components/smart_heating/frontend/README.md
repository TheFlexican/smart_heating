# Smart Heating Frontend

This is the React-based frontend for the Smart Heating Home Assistant integration.

## Features

- 🎨 **Material-UI v6** - Beautiful, responsive design matching Home Assistant theme
- ⚡ **Vite 6** - Lightning-fast development and build
- 🔄 **Real-time Updates** - WebSocket integration for instant feedback
- 🖱️ **Drag & Drop** - Easy device assignment with react-beautiful-dnd
- 📊 **Interactive Charts** - Temperature history visualization with Recharts
- 📱 **Responsive** - Works on desktop, tablet, and mobile
- 🌙 **Dark Theme** - Matches Home Assistant's native dark theme
- 🔒 **TypeScript** - Type-safe development

## Development

### Prerequisites

- Node.js 18 or higher
- npm or yarn

### Setup

```bash
cd custom_components/smart_heating/frontend
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

**Main Pages:**
- **App** - Main application with routing and drag-drop context
- **AreaDetail** - Detailed area page with 5 tabs (Overview, Devices, Schedule, History, Settings)

**Components:**
- **Header** - Top app bar with WebSocket connection status
- **ZoneList** - Grid display of all areas with drag-drop
- **ZoneCard** - Individual area control (droppable target)
- **CreateZoneDialog** - Modal dialog for creating new areas
- **DevicePanel** - Sidebar with draggable Zigbee2MQTT devices
- **ScheduleEditor** - Time-based temperature schedule management
- **HistoryChart** - Interactive Recharts visualization (6h-7d)

### Hooks

- **useWebSocket** - Custom hook for real-time WebSocket communication

### API Client

The `src/api.ts` file contains all API interaction functions:
- `getZones()` - Fetch all areas
- `createZone()` - Create a new area
- `deleteZone()` - Delete a area
- `setZoneTemperature()` - Update area target temperature
- `enableZone()` / `disableZone()` - Control area state
- `addDeviceToZone()` / `removeDeviceFromZone()` - Manage area devices
- `getDevices()` - Fetch available Zigbee2MQTT devices
- Plus schedule, history, and service endpoints

### TypeScript Types

See `src/types.ts` for all interface definitions:
- `Zone` - Area configuration, state, schedules, night boost
- `Device` - Zigbee2MQTT device information
- `ScheduleEntry` - Time-based schedule data
- `HistoryEntry` - Temperature history record

## Key Features

### Smart Scheduling
- Time-based temperature profiles
- Day-of-week selection
- Multiple schedules per area
- Enable/disable individual schedules

### Night Boost
- Configurable temperature increase during night hours
- Customizable start and end times (default: 22:00-06:00)
- Adjustable offset (0-3°C)
- Per-area enable/disable
- Supports periods crossing midnight (e.g., 23:00-07:00)

### Temperature History
- Records every 5 minutes
- 7-day retention
- Interactive charts with multiple time ranges
- Color-coded: current (blue), target (yellow), heating (red dots)

### Advanced Settings
- Global hysteresis control (0.1-2.0°C)
- Temperature limits display
- Real-time service calls

### Device Status Display
- **Thermostats**: Show "20.0°C → 22.0°C" when heating (target > current)
- **Temperature Sensors**: Show "19.5°C" from temperature attribute
- **Valves**: Show "45%" position without redundant state
- **Fallback**: Shows "unavailable" when no data available
- Color-coded icons for instant visual feedback
- Real-time updates via WebSocket and coordinator (30s)

### Drag & Drop
- Drag devices from panel to area cards
- Visual feedback on drop targets
- Automatic refresh after assignment

## Accessing the Frontend

Once built and deployed, access the frontend through:

1. **Home Assistant Panel**: Navigate to the "Smart Heating" panel in the sidebar (🔥 icon)
2. **Direct URL**: `http://your-ha-instance:8123/smart_heating/`

## Troubleshooting

### API Calls Failing

Make sure your Home Assistant instance is running and the Smart Heating integration is installed and configured.

### Build Errors

Clear node_modules and reinstall:
```bash
rm -rf node_modules package-lock.json
npm install
```

### Hot Reload Not Working

Make sure you're accessing the dev server directly at `localhost:5173`, not through Home Assistant.

### WebSocket Not Connecting

Check that Home Assistant is running and the integration is loaded. Check browser console for connection errors.

## Performance

- Code splitting with lazy loading (planned)
- Optimized re-renders with React.memo
- Debounced slider updates
- Efficient WebSocket updates
- Responsive chart rendering

## Browser Support

- Chrome/Edge 90+
- Firefox 88+
- Safari 14+
