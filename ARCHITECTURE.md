# Architecture Overview

Smart Heating is a Home Assistant integration with a modern web-based interface for managing multi-area heating systems.

## High-Level Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                     Home Assistant                           │
│  ┌────────────────────────────────────────────────────────┐ │
│  │         Smart Heating Integration               │ │
│  │                                                         │ │
│  │  ┌──────────────┐  ┌──────────────┐  ┌─────────────┐ │ │
│  │  │ Area Manager │  │ Coordinator  │  │  Platforms  │ │ │
│  │  │   (Storage)  │  │  (30s poll)  │  │ (Entities)  │ │ │
│  │  └──────┬───────┘  └──────┬───────┘  └─────────────┘ │ │
│  │         │                  │                           │ │
│  │  ┌──────┴──────────────────┴──────────────────────┐   │ │
│  │  │                                                  │   │ │
│  │  │        REST API + WebSocket API                │   │ │
│  │  │   (/api/smart_heating/*)                 │   │ │
│  │  │                                                  │   │ │
│  │  └───────────────────────┬──────────────────────────┘   │ │
│  │                          │                              │ │
│  │  ┌───────────────────────┴──────────────────────────┐  │ │
│  │  │                                                    │  │ │
│  │  │         Static File Server                        │  │ │
│  │  │    (/smart_heating/* → frontend/dist)      │  │ │
│  │  │                                                    │  │ │
│  │  └───────────────────────┬──────────────────────────┘  │ │
│  └──────────────────────────┼─────────────────────────────┘ │
└───────────────────────────┼─────────────────────────────────┘
                            │
                            │ HTTP/WebSocket
                            ▼
             ┌──────────────────────────────┐
             │     React Frontend (SPA)     │
             │                              │
             │  - Area Management UI        │
             │  - Device Panel              │
             │  - Real-time Updates         │
             │  - Material-UI Components    │
             └──────────────────────────────┘
                            │
                            │ MQTT (via HA)
                            ▼
             ┌──────────────────────────────┐
             │       Zigbee2MQTT            │
             │                              │
             │  - Thermostats               │
             │  - Temperature Sensors       │
             │  - OpenTherm Gateways        │
             │  - Radiator Valves           │
             └──────────────────────────────┘
```

## Backend Components

### 1. Area Manager (`area_manager.py`)

Core business logic for managing heating areas.

**Responsibilities:**
- Area CRUD operations
- Device assignment to areas
- Schedule management (Schedule class)
- Night boost configuration per area
- Temperature control and effective target calculation
- Area enable/disable
- Persistent storage (via HA storage API)

**Data Model:**
```python
Area:
  - area_id: str
  - name: str
  - target_temperature: float
  - enabled: bool
  - devices: Dict[str, Device]
  - schedules: Dict[str, Schedule]
  - state: ZoneState (heating/idle/off)
  - night_boost_enabled: bool
  - night_boost_offset: float
  - current_temperature: Optional[float]

Schedule:
  - schedule_id: str
  - time: str (HH:MM)
  - temperature: float
  - days: List[str] (mon, tue, etc.)
  - enabled: bool

Device:
  - id: str
  - type: str (thermostat/temperature_sensor/opentherm_gateway/valve)
  - mqtt_topic: Optional[str]
  - entity_id: Optional[str]
```

**Key Methods:**
- `get_effective_target_temperature()` - Calculates target with schedules + night boost
- `get_active_schedule_temperature()` - Finds current active schedule
- `add_schedule()` / `remove_schedule()` - Schedule management

### 2. Coordinator (`coordinator.py`)

Data update coordinator using Home Assistant's `DataUpdateCoordinator`.

**Responsibilities:**
- Fetch area data every 30 seconds
- Broadcast updates to entities
- Handle refresh requests

### 3. Climate Controller (`climate_controller.py`)

Automated heating control engine.

**Responsibilities:**
- Runs every 30 seconds (via async_track_time_interval)
- Updates area temperatures from sensors
- Controls heating based on hysteresis logic
- Records temperature history every 5 minutes (10 cycles)
- Integrates with AreaManager for effective target temperature

**Logic:**
```python
# Hysteresis control (default 0.5°C)
should_heat = current_temp < (target_temp - hysteresis)
should_stop = current_temp >= target_temp

# Target includes schedules + night boost
target_temp = area.get_effective_target_temperature()
```

### 4. Schedule Executor (`scheduler.py`)

Time-based temperature control.

**Responsibilities:**
- Runs every 1 minute (via async_track_time_interval)
- Checks all active schedules for current day/time
- Applies temperature changes when schedules activate
- Handles midnight-crossing schedules
- Prevents duplicate temperature sets (tracks last applied)

**Schedule Matching:**
- Day-of-week checking (mon, tue, wed, thu, fri, sat, sun)
- Time range validation (handles 22:00-06:00 crossing midnight)
- Priority: Latest schedule time wins

### 5. History Tracker (`history.py`)

Temperature logging and retention.

**Responsibilities:**
- Records temperature every 5 minutes
- Stores: current_temp, target_temp, state, timestamp
- 7-day automatic retention
- Persistent storage in `.storage/smart_heating_history`
- Automatic cleanup of old entries
- 1000 entry limit per area

**Storage:**
```json
{
  "history": {
    "living_room": [
      {
        "timestamp": "2025-12-04T10:00:00",
        "current_temperature": 20.5,
        "target_temperature": 21.0,
        "state": "heating"
      }
    ]
  }
}
```

### 6. Platforms

#### Climate Platform (`climate.py`)
Creates one `climate.area_<name>` entity per area.

**Features:**
- HVAC modes: HEAT, OFF
- Temperature control (5-30°C, 0.5° steps)
- Current area state
- Area attributes (devices, enabled)

#### Switch Platform (`switch.py`)
Creates one `switch.area_<name>_control` entity per area.

**Features:**
- Simple on/off control
- Tied to area.enabled property

#### Sensor Platform (`sensor.py`)
Creates `sensor.smart_heating_status` entity.

**Features:**
- Overall system status
- Area count
- Active areas count

### 7. REST API (`api.py`)

HTTP API using `HomeAssistantView` for frontend communication.

**Endpoints:**

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/smart_heating/areas` | Get all areas with night boost data |
| GET | `/api/smart_heating/areas/{id}` | Get specific area |
| POST | `/api/smart_heating/areas` | Create area |
| DELETE | `/api/smart_heating/areas/{id}` | Delete area |
| POST | `/api/smart_heating/areas/{id}/devices` | Add device to area |
| DELETE | `/api/smart_heating/areas/{id}/devices/{device_id}` | Remove device |
| POST | `/api/smart_heating/areas/{id}/schedules` | Add schedule to area |
| DELETE | `/api/smart_heating/areas/{id}/schedules/{schedule_id}` | Remove schedule |
| POST | `/api/smart_heating/areas/{id}/temperature` | Set temperature |
| POST | `/api/smart_heating/areas/{id}/enable` | Enable area |
| POST | `/api/smart_heating/areas/{id}/disable` | Disable area |
| GET | `/api/smart_heating/areas/{id}/history?hours=24` | Get temperature history |
| GET | `/api/smart_heating/devices` | Get available devices |
| GET | `/api/smart_heating/status` | Get system status |
| POST | `/api/smart_heating/call_service` | Call HA service (proxy) |

### 8. WebSocket API (`websocket.py`)

Real-time communication using HA WebSocket API.

**Commands:**
- `smart_heating/subscribe_updates` - Subscribe to area updates
- `smart_heating/get_areas` - Get areas via WebSocket

### 9. Service Calls

Comprehensive service API for automation/script integration:

**Area Management:**
1. `smart_heating.enable_area` - Enable area
2. `smart_heating.disable_area` - Disable area
3. `smart_heating.set_area_temperature` - Set target temperature

**Device Management:**
4. `smart_heating.add_device_to_area` - Add device to area
5. `smart_heating.remove_device_from_area` - Remove device

**Schedule Management:**
6. `smart_heating.add_schedule` - Add time-based schedule
7. `smart_heating.remove_schedule` - Remove schedule
8. `smart_heating.enable_schedule` - Enable schedule
9. `smart_heating.disable_schedule` - Disable schedule

**Advanced Settings:**
10. `smart_heating.set_night_boost` - Configure night boost
13. `smart_heating.set_hysteresis` - Set global hysteresis

**System:**
14. `smart_heating.refresh` - Manual refresh

## Frontend Components

### Technology Stack

- **React 18.3** - UI library
- **TypeScript** - Type safety
- **Vite 6** - Build tool and dev server
- **Material-UI (MUI) v6** - Component library
- **react-router-dom** - Client-side routing
- **react-beautiful-dnd** - Drag and drop device assignment
- **Recharts** - Interactive temperature charts
- **WebSocket** - Real-time updates via custom hook

### Component Structure

```
src/
├── main.tsx                    # Entry point
├── App.tsx                     # Main application with routing
├── types.ts                    # TypeScript interfaces
├── api.ts                      # API client functions
├── index.css                   # Global styles
├── components/
│   ├── Header.tsx              # App header with connection status
│   ├── ZoneList.tsx            # Area grid with drag-drop context
│   ├── ZoneCard.tsx            # Individual area control card
│   ├── CreateZoneDialog.tsx    # Area creation dialog
│   ├── DevicePanel.tsx         # Draggable devices sidebar
│   ├── ScheduleEditor.tsx      # Schedule management UI
│   └── HistoryChart.tsx        # Temperature history visualization
├── pages/
│   └── AreaDetail.tsx          # Detailed area page (5 tabs)
└── hooks/
    └── useWebSocket.ts         # WebSocket connection hook
```

### Key Features

**ZoneCard Component:**
- Temperature slider (5-30°C, 0.5° steps)
- Enable/disable toggle
- State indicator with color coding (heating/idle/off)
- Device list with remove buttons
- Drag-drop target for device assignment
- Click to navigate to detail page

**AreaDetail Page (5 Tabs):**
1. **Overview** - Temperature control, current state, device management
2. **Devices** - Detailed device list and assignment
3. **Schedule** - Time-based schedule editor
4. **History** - Interactive temperature charts (6h-7d ranges)
5. **Settings** - Night boost, hysteresis, advanced configuration

**ScheduleEditor Component:**
- Time picker for schedule start
- Temperature input
- Day-of-week multi-select
- Add/remove schedules
- Enable/disable individual schedules
- Visual schedule list with current status

**HistoryChart Component:**
- Recharts line chart
- Blue line: Current temperature
- Yellow dashed: Target temperature
- Red dots: Heating active periods
- Time range selector (6h, 12h, 24h, 3d, 7d)
- Auto-refresh every 5 minutes
- Responsive design

**DevicePanel Component:**
- List of available Zigbee2MQTT devices
- Draggable device cards
- Filter by device type
- Real-time availability updates

**DevicePanel Component:**
- Lists available Zigbee2MQTT devices
- Filters out devices already in areas
- Drag source for device assignment (planned)
- Device type icons

**CreateZoneDialog Component:**
- Area name input
- Auto-generated area_id
- Initial temperature setting
- Form validation

### API Integration

All API calls go through `src/api.ts`:

```typescript
// Get areas
const areas = await getZones()

// Create area
await createZone('living_room', 'Living Room', 21.0)

// Set temperature
await setZoneTemperature('living_room', 22.5)

// Add device
await addDeviceToZone('living_room', 'device_id')
```

### Real-time Updates (Planned)

WebSocket connection for live updates:
- Area state changes
- Temperature updates
- Device additions/removals
- System status

## Data Flow

### Area Creation Flow

```
User clicks "Create Area"
    ↓
CreateZoneDialog collects input
### Temperature Control Flow

```
User drags temperature slider
    ↓
ZoneCard onChange handler
    ↓
api.setZoneTemperature() calls POST /api/.../temperature
    ↓
ZoneHeaterAPIView.post() routes to set_temperature()
    ↓
area_manager.async_set_area_temperature()
    ↓
Area updated in storage
    ↓
Climate entity receives update
    ↓
MQTT commands sent to devices (via climate entity)
    ↓
Physical devices adjust
```

## Storage

Zones and configuration are stored using Home Assistant's storage API:

**File:** `.storage/smart_heating_areas`

**Format:**
```json
{
  "version": 1,
  "data": {
    "areas": [
      {
        "id": "living_room",
        "name": "Living Room",
        "target_temperature": 21.0,
        "enabled": true,
        "devices": [
          {
            "id": "device_1",
            "name": "Living Room Thermostat",
            "type": "thermostat"
          }
        ]
      }
    ]
  }
}
```

## Zigbee2MQTT Integration

### Device Discovery

Devices are discovered via MQTT topics:
- `zigbee2mqtt/bridge/devices` - List of all devices
- `zigbee2mqtt/<friendly_name>` - Device state

### Device Control

Control messages sent to:
- `zigbee2mqtt/<friendly_name>/set` - Send commands

Example:
```json
{
  "temperature": 22.5,
  "system_mode": "heat"
}
```

## Security

- **Authentication**: All API endpoints require HA authentication
- **Authorization**: Uses HA's built-in user permissions
- **CORS**: Configured for same-origin only
- **Input Validation**: All inputs validated before processing

## Performance

- **Coordinator Poll**: 30-second interval (configurable)
- **API Response Time**: < 100ms for typical operations
- **Frontend Bundle**: ~500KB gzipped
- **WebSocket**: Minimal overhead for real-time updates

## Extensibility

### Adding New Device Types

1. Add device type constant in `const.py`
2. Update device handling in `area_manager.py`
3. Add icon in `DevicePanel.tsx`

### Adding New Platforms

1. Create platform file (e.g., `number.py`)
2. Add to `PLATFORMS` in `const.py`
3. Forward setup in `__init__.py`

### Adding New API Endpoints

1. Add method to `ZoneHeaterAPIView` in `api.py`
2. Add client function to `frontend/src/api.ts`
3. Use in React components

## Future Enhancements

- [ ] Drag-and-drop device assignment
- [ ] Area scheduling/programs
- [ ] Analytics dashboard
- [ ] Smart heating algorithms
- [ ] Energy monitoring
- [ ] Multi-language support
- [ ] Mobile app integration
- [ ] Voice control optimization
