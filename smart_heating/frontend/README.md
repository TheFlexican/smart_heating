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
- **AreaDetail** - Detailed area page with 6 tabs (Overview, Devices, Schedule, History, Settings, Learning)

**Components:**
- **Header** - Top app bar with WebSocket connection status
- **ZoneList** - Grid display of all areas with drag-drop
- **ZoneCard** - Individual area control (droppable target)
- **CreateZoneDialog** - Modal dialog for creating new areas
- **DevicePanel** - Sidebar with draggable Zigbee2MQTT devices
- **ScheduleEditor** - Time-based temperature schedule management
- **HistoryChart** - Interactive Recharts visualization with configurable time ranges
  - Preset buttons: 6h, 12h, 24h, 3d, 7d, 30d, Custom
  - Custom date/time range picker with start/end inputs
  - Auto-refresh every 5 minutes
  - Visual indicators for heating periods

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
- `getLearningStats()` - Get adaptive learning statistics for an area
- `getHistoryConfig()` - Fetch history retention settings
- `setHistoryRetention(days)` - Update retention period (1-365 days)
- `getHistory(areaId, options)` - Flexible history queries with hours, startTime, endTime
- Plus schedule, preset modes, boost mode, window/presence sensors, and HVAC mode endpoints

### TypeScript Types

See `src/types.ts` for all interface definitions:
- `Zone` - Area configuration, state, schedules, night boost, smart learning
- `Device` - Zigbee2MQTT device information
- `ScheduleEntry` - Time-based schedule data
- `HistoryEntry` - Temperature history record
- `LearningStats` - Adaptive learning statistics

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

### Smart Night Boost (Adaptive Learning)
- Machine learning system that predicts optimal heating start times
- Learns heating patterns from historical data
- Weather correlation with outdoor temperature sensors
- Configurable target wake-up time
- Automatic prediction improvement over time
- Real-time learning statistics and progress tracking
- Dedicated Learning tab showing:
  - Learning status and configuration
  - Learning process explanation
  - API endpoint information

### Temperature History
- **Configurable Retention**: 1-365 days (default: 30 days)
- **Recording Interval**: Every 5 minutes (fixed)
- **No Aggregation**: Raw data points preserved at full resolution
- **Preset Time Ranges**: 6h, 12h, 24h, 3d, 7d, 30d
- **Custom Date/Time Picker**: Select specific analysis periods
- **Automatic Cleanup**: Hourly background task removes expired data
- **Interactive Charts**: Color-coded visualization
  - Current temperature (blue line)
  - Target temperature (yellow dashed line)
  - Heating active (red dots)
  - Average target (green dashed line)
- **History Management UI**:
  - Settings tab panel for retention configuration
  - Slider with visual markers (1d, 7d, 30d, 90d, 180d, 365d)
  - Save button with immediate cleanup
  - Display of recording interval and current settings
- **Flexible Querying**:
  - Toggle buttons for preset ranges
  - Custom mode with start/end datetime inputs
  - Apply button for custom queries
  - Auto-refresh every 5 minutes

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
