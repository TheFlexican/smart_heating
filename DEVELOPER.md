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

### Coordinator (`coordinator.py`)

```python
class ZoneHeaterManagerCoordinator(DataUpdateCoordinator):
    area_manager: ZoneManager
    
    async def _async_update_data() -> Dict[str, Any]
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
