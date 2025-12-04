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
│  │  │ Zone Manager │  │ Coordinator  │  │  Platforms  │ │ │
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
             │  - Zone Management UI        │
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

### 1. Zone Manager (`area_manager.py`)

Core business logic for managing heating areas.

**Responsibilities:**
- Zone CRUD operations
- Device assignment to areas
- Temperature control
- Zone enable/disable
- Persistent storage (via HA storage API)

**Data Model:**
```python
Zone:
  - id: str
  - name: str
  - target_temperature: float
  - enabled: bool
  - devices: List[Device]
  - state: ZoneState (heating/idle/off)

Device:
  - id: str
  - name: str
  - type: str (thermostat/sensor/gateway/valve)
  - area_id: Optional[str]
```

### 2. Coordinator (`coordinator.py`)

Data update coordinator using Home Assistant's `DataUpdateCoordinator`.

**Responsibilities:**
- Fetch zone data every 30 seconds
- Broadcast updates to entities
- Handle refresh requests

### 3. Platforms

#### Climate Platform (`climate.py`)
Creates one `climate.area_<name>` entity per area.

**Features:**
- HVAC modes: HEAT, OFF
- Temperature control (5-30°C, 0.5° steps)
- Current zone state
- Zone attributes (devices, enabled)

#### Switch Platform (`switch.py`)
Creates one `switch.area_<name>_control` entity per area.

**Features:**
- Simple on/off control
- Tied to area.enabled property

#### Sensor Platform (`sensor.py`)
Creates `sensor.smart_heating_status` entity.

**Features:**
- Overall system status
- Zone count
- Active areas count

### 4. REST API (`api.py`)

HTTP API using `HomeAssistantView` for frontend communication.

**Endpoints:**

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/smart_heating/zones` | Get all areas |
| GET | `/api/smart_heating/zones/{id}` | Get specific zone |
| POST | `/api/smart_heating/zones` | Create zone |
| DELETE | `/api/smart_heating/zones/{id}` | Delete zone |
| POST | `/api/smart_heating/zones/{id}/devices` | Add device to zone |
| DELETE | `/api/smart_heating/zones/{id}/devices/{device_id}` | Remove device |
| POST | `/api/smart_heating/zones/{id}/temperature` | Set temperature |
| POST | `/api/smart_heating/zones/{id}/enable` | Enable zone |
| POST | `/api/smart_heating/zones/{id}/disable` | Disable zone |
| GET | `/api/smart_heating/devices` | Get available devices |
| GET | `/api/smart_heating/status` | Get system status |

### 5. WebSocket API (`websocket.py`)

Real-time communication using HA WebSocket API.

**Commands:**
- `smart_heating/subscribe_updates` - Subscribe to zone updates
- `smart_heating/get_zones` - Get areas via WebSocket
- `smart_heating/create_zone` - Create zone via WebSocket

### 6. Service Calls

Eight service calls for automation/script integration:

1. `smart_heating.create_zone`
2. `smart_heating.delete_zone`
3. `smart_heating.add_device_to_zone`
4. `smart_heating.remove_device_from_zone`
5. `smart_heating.set_area_temperature`
6. `smart_heating.enable_zone`
7. `smart_heating.disable_zone`
8. `smart_heating.refresh`

## Frontend Components

### Technology Stack

- **React 18.2** - UI library
- **TypeScript** - Type safety
- **Vite** - Build tool
- **Material-UI (MUI) v5** - Component library
- **Axios** - HTTP client
- **react-beautiful-dnd** - Drag and drop (planned)
- **Recharts** - Analytics charts (planned)

### Component Structure

```
src/
├── main.tsx              # Entry point
├── App.tsx               # Main application
├── types.ts              # TypeScript interfaces
├── api.ts                # API client functions
├── index.css             # Global styles
└── components/
    ├── Header.tsx        # App header with branding
    ├── ZoneList.tsx      # Zone grid display
    ├── ZoneCard.tsx      # Individual zone control
    ├── CreateZoneDialog.tsx  # Zone creation dialog
    └── DevicePanel.tsx   # Available devices sidebar
```

### Key Features

**ZoneCard Component:**
- Temperature slider (5-30°C)
- Enable/disable toggle
- State indicator (heating/idle/off)
- Delete zone action
- Device list

**DevicePanel Component:**
- Lists available Zigbee2MQTT devices
- Filters out devices already in areas
- Drag source for device assignment (planned)
- Device type icons

**CreateZoneDialog Component:**
- Zone name input
- Auto-generated area_id
- Initial temperature setting
- Form validation

### API Integration

All API calls go through `src/api.ts`:

```typescript
// Get areas
const areas = await getZones()

// Create zone
await createZone('living_room', 'Living Room', 21.0)

// Set temperature
await setZoneTemperature('living_room', 22.5)

// Add device
await addDeviceToZone('living_room', 'device_id')
```

### Real-time Updates (Planned)

WebSocket connection for live updates:
- Zone state changes
- Temperature updates
- Device additions/removals
- System status

## Data Flow

### Zone Creation Flow

```
User clicks "Create Zone"
    ↓
CreateZoneDialog collects input
    ↓
api.createZone() calls POST /api/smart_heating/zones
    ↓
ZoneHeaterAPIView.post() in api.py
    ↓
area_manager.async_create_zone()
    ↓
Zone saved to storage
    ↓
Coordinator refresh triggered
    ↓
Climate/Switch entities created
    ↓
Frontend refreshes zone list
```

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
Zone updated in storage
    ↓
Climate entity receives update
    ↓
MQTT commands sent to devices (via climate entity)
    ↓
Physical devices adjust
```

## Storage

Zones and configuration are stored using Home Assistant's storage API:

**File:** `.storage/smart_heating_zones`

**Format:**
```json
{
  "version": 1,
  "data": {
    "zones": [
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
- [ ] Zone scheduling/programs
- [ ] Analytics dashboard
- [ ] Smart heating algorithms
- [ ] Energy monitoring
- [ ] Multi-language support
- [ ] Mobile app integration
- [ ] Voice control optimization
