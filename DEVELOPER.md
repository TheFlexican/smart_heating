# Developer Quick Reference

Quick reference for developing and extending Smart Heating.

## Project Structure

```
smart_heating/
├── custom_components/smart_heating/
│   ├── __init__.py           # Integration setup, service registration
│   ├── manifest.json         # Integration metadata
│   ├── const.py              # Constants and configuration
│   ├── config_flow.py        # Config flow (empty init)
│   ├── strings.json          # UI strings
│   ├── services.yaml         # Service definitions
│   │
│   ├── area_manager.py       # Core area management logic
│   ├── coordinator.py        # Data update coordinator
│   ├── api.py                # REST API endpoints
│   ├── websocket.py          # WebSocket handlers
│   │
│   ├── climate.py            # Climate platform
│   ├── switch.py             # Switch platform
│   ├── sensor.py             # Sensor platform
│   │
│   └── frontend/             # React frontend
│       ├── package.json
│       ├── vite.config.ts
│       ├── tsconfig.json
│       ├── index.html
│       └── src/
│           ├── main.tsx
│           ├── App.tsx
│           ├── types.ts
│           ├── api.ts
│           └── components/
│
├── README.md                 # User documentation
├── INSTALL.md                # Installation guide
├── ARCHITECTURE.md           # Architecture overview
├── DEVELOPER.md              # Developer quick reference (this file)
├── CHANGELOG.md              # Version history
├── deploy.sh                 # Development deploy script
├── build_frontend.sh         # Frontend build script
└── .gitignore                # Git ignore rules
```

## Common Tasks

### Adding a New Service

1. **Define constant** in `const.py`:
   ```python
   SERVICE_MY_NEW_SERVICE = "my_new_service"
   ```

2. **Add schema** in `__init__.py`:
   ```python
   MY_SERVICE_SCHEMA = vol.Schema({
       vol.Required("param"): cv.string,
   })
   ```

3. **Create handler** in `async_setup_services()`:
   ```python
   async def handle_my_service(call: ServiceCall) -> None:
       param = call.data["param"]
       # Do something
       await coordinator.async_refresh()
   ```

4. **Register service**:
   ```python
   hass.services.async_register(
       DOMAIN, SERVICE_MY_NEW_SERVICE, handle_my_service, schema=MY_SERVICE_SCHEMA
   )
   ```

5. **Document** in `services.yaml`:
   ```yaml
   my_new_service:
     description: "Description of service"
     fields:
       param:
         description: "Parameter description"
         example: "example_value"
   ```

### Area Manager Data Model

**Area Properties** (v0.4.1+):
```python
class Area:
    area_id: str
    name: str
    target_temperature: float
    enabled: bool
    hidden: bool  # v0.4.0+ - Hide area from UI
    manual_override: bool  # v0.4.0+ - Manual mode when thermostat changed externally
    devices: dict
    schedules: dict
    # ... other properties
```

**Persistence Methods:**
```python
# Serialization (save to storage)
def to_dict(self) -> dict:
    return {
        "manual_override": self.manual_override,  # v0.4.1+
        "hidden": self.hidden,
        # ... all other fields
    }

# Deserialization (load from storage)
@classmethod
def from_dict(cls, data: dict) -> "Area":
    area = cls(...)
    area.manual_override = data.get("manual_override", False)  # v0.4.1+
    area.hidden = data.get("hidden", False)
    return area
```

### Adding a New API Endpoint

1. **Add method** to `ZoneHeaterAPIView` in `api.py`:
   ```python
   async def my_endpoint(self, request: web.Request) -> web.Response:
       """Handle my endpoint."""
       data = await request.json()
       result = await self.area_manager.do_something(data)
       return self.json(result)
   ```

2. **Add route** in `post()` or `get()`:
   ```python
   if len(parts) == 2 and parts[1] == "my_endpoint":
       return await self.my_endpoint(request)
   ```

3. **Add client function** in `frontend/src/api.ts`:
   ```typescript
   export const myEndpoint = async (data: MyData): Promise<Result> => {
     const response = await client.post('/my_endpoint', data)
     return response.data
   }
   ```

4. **Use in component**:
   ```typescript
   import { myEndpoint } from '../api'
   
   const handleAction = async () => {
     await myEndpoint({ param: 'value' })
   }
   ```

### Adding a New React Component

1. **Create file** in `frontend/src/components/MyComponent.tsx`:
   ```typescript
   import { Box, Typography } from '@mui/material'
   
   interface MyComponentProps {
     data: string
   }
   
   const MyComponent = ({ data }: MyComponentProps) => {
     return (
       <Box>
         <Typography>{data}</Typography>
       </Box>
     )
   }
   
   export default MyComponent
   ```

2. **Import and use**:
   ```typescript
   import MyComponent from './components/MyComponent'
   
   <MyComponent data="Hello" />
   ```

### Adding Area Manager Methods

1. **Add method** to `ZoneManager` class in `area_manager.py`:
   ```python
   async def async_my_method(self, area_id: str, param: str) -> bool:
       """My method description."""
       area = self.get_area(area_id)
       if not area:
           return False
       
       # Do something
       area.custom_property = param
       
       await self.async_save()
       return True
   ```

2. **Call from API**:
   ```python
   result = await self.area_manager.async_my_method(area_id, param)
   ```

## Key Classes

### Area Class (`area_manager.py`)

```python
class Area:
    id: str
    name: str
    target_temperature: float
    enabled: bool
    devices: List[Device]
    
    def add_device(device: Device) -> None
    def remove_device(device_id: str) -> bool
    def get_state() -> ZoneState
    def to_dict() -> dict
```

### Schedule Class (`area_manager.py`)

```python
class Schedule:
    schedule_id: str
    time: str  # HH:MM (legacy)
    day: str  # Monday, Tuesday, etc. (new)
    start_time: str  # HH:MM (new)
    end_time: str  # HH:MM (new)
    temperature: float
    days: List[str]  # ["mon", "tue"] (legacy)
    enabled: bool
    
    # Note: __init__ accepts both formats and converts between them
    # to_dict() returns new format (day, start_time, end_time)
    # from_dict() accepts both formats
```

### ZoneManager Class (`area_manager.py`)

```python
class ZoneManager:
    async def async_load() -> None
    async def async_save() -> None
    
    def get_area(area_id: str) -> Optional[Area]
    def get_all_areas() -> List[Area]
    
    async def async_add_device_to_area(...) -> bool
    async def async_remove_device_from_area(...) -> bool
    async def async_set_area_temperature(...) -> bool
    async def async_enable_area(area_id: str) -> bool
    async def async_disable_area(area_id: str) -> bool
```

### HistoryTracker Class (`history.py`)

```python
class HistoryTracker:
    """Track temperature history for areas."""
    
    async def async_load() -> None  # Load from storage
    async def async_save() -> None  # Save to storage
    async def async_unload() -> None  # Cleanup on shutdown
    
    async def async_record_temperature(
        area_id: str,
        current_temp: float,
        target_temp: float,
        state: str
    ) -> None
    
    def get_history(
        area_id: str,
        hours: int | None = None,
        start_time: datetime | None = None,
        end_time: datetime | None = None
    ) -> list[dict[str, Any]]
    
    def get_all_history() -> dict[str, list[dict[str, Any]]]
    
    def set_retention_days(days: int) -> None
    def get_retention_days() -> int
    
    # Internal methods
    async def _async_cleanup_old_entries() -> None
    async def _async_periodic_cleanup(now=None) -> None
```

**Recording:**
- Interval: Every 5 minutes (10 cycles × 30 seconds)
- Counter tracked in `ClimateController._record_counter`
- Data points: timestamp (ISO8601), current_temperature, target_temperature, state
- Storage: `.storage/smart_heating_history`

**Retention:**
- Configurable: 1-365 days (default: 30 days)
- Cleanup: Hourly background task via `async_track_time_interval`
- Immediate cleanup when retention is reduced
- Persistent across restarts

**Querying:**
- By hours: `get_history(area_id, hours=24)`
- By date range: `get_history(area_id, start_time=dt1, end_time=dt2)`
- All data: `get_history(area_id)` (within retention period)

### Coordinator (`coordinator.py`)

```python
class ZoneHeaterManagerCoordinator(DataUpdateCoordinator):
    area_manager: ZoneManager
    
    async def _async_update_data() -> Dict[str, Any]
    
    # Manual Override System (v0.4.0+)
    async def async_setup() -> None
    async def _handle_state_change(event: Event) -> None
    async def debounced_temp_update(area_id: str, new_temp: float) -> None
```

**Manual Override System** (v0.4.0+):

Real-time detection of external thermostat changes with automatic manual override mode.

**Key Constants:**
```python
MANUAL_TEMP_CHANGE_DEBOUNCE = 2.0  # seconds
```

**Implementation Details:**

1. **State Listener Setup** (`async_setup()`):
   ```python
   # Register listeners for all climate entities in all areas
   for area in self.area_manager.areas.values():
       for device in area.devices.values():
           if device.get("type") == "thermostat":
               entity_id = device.get("entity_id")
               async_track_state_change_event(
                   self.hass, entity_id, self._handle_state_change
               )
   ```

2. **Debounced State Change Handler**:
   ```python
   async def _handle_state_change(self, event: Event) -> None:
       """Handle thermostat state changes with debouncing."""
       # Skip if change was initiated by app
       if self._ignore_next_state_change.get(area_id):
           self._ignore_next_state_change[area_id] = False
           return
       
       # Cancel previous pending update
       if area_id in self._pending_manual_updates:
           self._pending_manual_updates[area_id].cancel()
       
       # Schedule debounced update (2 seconds)
       handle = self.hass.async_create_task(
           self._delayed_manual_update(area_id, new_temp)
       )
       self._pending_manual_updates[area_id] = handle
   ```

3. **Manual Override Activation**:
   ```python
   async def debounced_temp_update(self, area_id: str, new_temp: float):
       """Apply manual override after debounce delay."""
       area = self.area_manager.areas.get(area_id)
       if not area:
           return
       
       # Enter manual mode
       area.manual_override = True
       area.target_temperature = new_temp
       
       # Persist to storage (v0.4.1+ includes manual_override)
       await self.area_manager.async_save()
       
       # Force UI update
       await self.async_refresh()
   ```

4. **Clearing Manual Override** (in `api.py`):
   ```python
   async def set_temperature(self, request: web.Request) -> web.Response:
       """Set area temperature via app."""
       area.target_temperature = temperature
       area.manual_override = False  # Clear manual mode
       await self.area_manager.async_save()
   ```

**Persistence** (v0.4.1+):
```python
# Area.to_dict() - Serialization
def to_dict(self) -> dict:
    return {
        "area_id": self.area_id,
        "manual_override": self.manual_override,  # Added v0.4.1
        # ... other fields
    }

# Area.from_dict() - Deserialization
@classmethod
def from_dict(cls, data: dict) -> "Area":
    area = cls(...)
    area.manual_override = data.get("manual_override", False)  # Added v0.4.1
    return area
```

**Testing Manual Override:**
```bash
# 1. Adjust thermostat externally (e.g., Google Nest)
# 2. Check backend logs
ssh root@192.168.2.2 -p 22222 "ha core logs" | grep "Thermostat temperature change detected"

# 3. Verify manual_override flag set
curl -H "Authorization: Bearer TOKEN" \
  http://homeassistant.local:8123/api/smart_heating/areas/AREA_ID

# 4. Check persistence after restart
ssh root@192.168.2.2 -p 22222 "ha core restart"
sleep 30
curl -H "Authorization: Bearer TOKEN" \
  http://homeassistant.local:8123/api/smart_heating/areas/AREA_ID
# Should still show manual_override: true
```

## Testing

### Manual Testing

1. **Start HA dev container**:
   ```bash
   docker run -d --name homeassistant \
     -p 8123:8123 \
     -v /path/to/config:/config \
     homeassistant/home-assistant:dev
   ```

2. **Deploy integration**:
   ```bash
   ./deploy.sh
   ```

3. **Watch logs**:
   ```bash
   docker logs -f homeassistant
   ```

### Frontend Testing

1. **Start dev server**:
   ```bash
   cd custom_components/smart_heating/frontend
   npm run dev
   ```

2. **Open browser**: http://localhost:5173

3. **Make changes** - Hot reload active

### API Testing

Use curl or Postman:

```bash
# Get areas
curl -H "Authorization: Bearer YOUR_TOKEN" \
  http://localhost:8123/api/smart_heating/areas

# Create area
curl -X POST \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"area_id":"test","area_name":"Test","temperature":20}' \
  http://localhost:8123/api/smart_heating/areas
```

## Debugging

### Python Debugging

Enable debug logging in `configuration.yaml`:

```yaml
logger:
  default: info
  logs:
    custom_components.smart_heating: debug
```

Add logging in code:

```python
_LOGGER.debug("Debug message: %s", variable)
_LOGGER.info("Info message")
_LOGGER.warning("Warning message")
_LOGGER.error("Error message", exc_info=True)
```

### Frontend Debugging

Open browser DevTools:
- Console: See logs and errors
- Network: Monitor API calls
- React DevTools: Inspect component state

Add console logs:

```typescript
console.log('Debug:', data)
console.error('Error:', error)
```

## Code Style

### Python

Follow PEP 8:
- 4 spaces indentation
- Max line length: 88 (Black formatter)
- Type hints where possible
- Docstrings for all functions

```python
async def my_function(param: str, option: bool = False) -> Optional[str]:
    """Brief description.
    
    Args:
        param: Parameter description
        option: Option description
        
    Returns:
        Return value description
    """
    ...
```

### TypeScript

Follow standard TypeScript conventions:
- 2 spaces indentation
- Use `const` over `let`
- Prefer arrow functions
- Define interfaces for all props

```typescript
interface MyProps {
  data: string
  optional?: number
}

const MyComponent = ({ data, optional = 0 }: MyProps) => {
  const [state, setState] = useState(0)
  
  const handleClick = () => {
    // Handler logic
  }
  
  return <Box>...</Box>
}
```

## Git Workflow

1. **Create branch**:
   ```bash
   git checkout -b feature/my-feature
   ```

2. **Make changes** and commit:
   ```bash
   git add .
   git commit -m "feat: add my feature"
   ```

3. **Push and create PR**:
   ```bash
   git push origin feature/my-feature
   ```

### Commit Message Format

- `feat:` - New feature
- `fix:` - Bug fix
- `docs:` - Documentation
- `style:` - Code style changes
- `refactor:` - Code refactoring
- `test:` - Tests
- `chore:` - Maintenance

## Building for Release

1. **Update version** in `manifest.json`

2. **Update CHANGELOG.md**

3. **Build frontend**:
   ```bash
   ./build_frontend.sh
   ```

4. **Test thoroughly**

5. **Create tag**:
   ```bash
   git tag v0.2.0
   git push origin v0.2.0
   ```

6. **Create GitHub release**

## Common Patterns

### History Data Management

**Adding history recording to a new feature:**

1. **Record data** in climate controller:
   ```python
   if should_record_history and history_tracker:
       await history_tracker.async_record_temperature(
           area_id, current_temp, target_temp, area.state
       )
   ```

2. **Query history** from API or service:
   ```python
   # Get last 24 hours
   history = history_tracker.get_history(area_id, hours=24)
   
   # Get custom range
   from datetime import datetime
   start = datetime.fromisoformat("2025-12-01T00:00:00")
   end = datetime.fromisoformat("2025-12-05T23:59:59")
   history = history_tracker.get_history(area_id, start_time=start, end_time=end)
   ```

3. **Update retention** via service:
   ```python
   history_tracker.set_retention_days(90)
   await history_tracker.async_save()
   await history_tracker._async_cleanup_old_entries()  # Immediate cleanup
   ```

**Frontend integration:**

```typescript
// Get history config
const config = await getHistoryConfig()
// {retention_days: 30, record_interval_seconds: 300, record_interval_minutes: 5}

// Update retention
await setHistoryRetention(90)

// Query history
const history = await getHistory(areaId, { hours: 24 })
const custom = await getHistory(areaId, {
  startTime: "2025-12-01T00:00:00",
  endTime: "2025-12-05T23:59:59"
})
```

### Async Operations in Python

```python
# Always use async for I/O
async def my_async_function():
    await some_io_operation()
    
# Use async_add_executor_job for sync code in async context
result = await hass.async_add_executor_job(sync_function)
```

### Error Handling

```python
try:
    result = await risky_operation()
except ValueError as err:
    _LOGGER.error("Invalid value: %s", err)
    return False
except Exception as err:
    _LOGGER.error("Unexpected error", exc_info=True)
    return False
```

### React State Management

```typescript
// Local state
const [count, setCount] = useState(0)

// Effect for data loading
useEffect(() => {
  loadData()
}, []) // Empty deps = run once

// Effect with dependencies
useEffect(() => {
  updateSomething()
}, [dependency])
```

### Material-UI Styling

```typescript
// sx prop for inline styles
<Box sx={{ 
  p: 2,              // padding: theme.spacing(2)
  mt: 1,             // marginTop: theme.spacing(1)
  bgcolor: 'primary.main',
  color: 'white',
}}>
  Content
</Box>
```

## Resources

- [Home Assistant Developer Docs](https://developers.home-assistant.io/)
- [React Documentation](https://react.dev/)
- [Material-UI Docs](https://mui.com/)
- [TypeScript Handbook](https://www.typescriptlang.org/docs/)
- [Vite Guide](https://vitejs.dev/guide/)

## Getting Help

- Check existing issues on GitHub
- Read the documentation
- Enable debug logging
- Ask in GitHub Discussions
