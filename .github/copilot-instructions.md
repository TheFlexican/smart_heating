# Copilot Instructions - Smart Heating

## Project Overview
Smart Heating is a custom Home Assistant integration for intelligent zone-based heating control with learning capabilities, presence detection, and advanced scheduling.

**Tech Stack:**
- Backend: Python 3.13, Home Assistant Custom Integration
- Frontend: React + TypeScript + Material-UI v5 + Vite 6.4.1
- Communication: REST API + WebSocket for real-time updates
- Development: Docker container (homeassistant-test) for testing

## Repository Structure
```
smart_heating/
├── smart_heating/               # Main integration directory (HA standard)
│   ├── __init__.py              # Integration setup & panel registration
│   ├── api.py                   # REST API endpoints
│   ├── area_manager.py          # Zone/area management logic
│   ├── climate.py               # Climate entity
│   ├── climate_controller.py   # Device control logic
│   ├── coordinator.py           # Data coordinator for real-time updates
│   ├── learning_engine.py      # ML-based temperature learning
│   ├── scheduler.py             # Schedule management
│   ├── websocket.py             # WebSocket API
│   ├── manifest.json            # Integration metadata & version
│   ├── services.yaml            # HA service definitions
│   ├── strings.json             # i18n strings
│   └── frontend/                # React frontend
│       ├── src/
│       │   ├── pages/           # Main UI pages
│       │   ├── components/      # Reusable components
│       │   ├── types.ts         # TypeScript definitions
│       │   └── api.ts           # Frontend API client
│       └── dist/                # Built frontend (served by HA)
├── sync.sh                      # Quick sync to test container
├── setup.sh                     # Full redeploy with container restart
├── deploy.sh                    # Deploy to production HA via Samba
└── README.md                    # Project documentation
```

**Note:** The integration folder is at the root level following [Home Assistant's standard development structure](https://developers.home-assistant.io/docs/creating_integration_file_structure). Deployment scripts copy `smart_heating/` to the container's `custom_components/smart_heating/` directory.

## Critical Scripts

### Development Workflow Scripts

1. **`sync.sh`** - **Primary development script**
   - Quick sync for iterative development
   - Builds frontend automatically
   - Copies all files to test container at `/config/custom_components/smart_heating/`
   - Restarts Home Assistant (fast reload)
   - **Use this 95% of the time during development**
   - Usage: `./sync.sh`

2. **`setup.sh`** - Full redeploy script
   - Complete container restart
   - Use when you need clean slate
   - Slower than sync.sh
   - **Use only when sync.sh isn't enough**
   - Usage: `./setup.sh`

### Development Cycle
```bash
# Normal development workflow:
1. Edit code (backend .py or frontend .tsx/.ts)
2. Run: ./sync.sh
3. Clear browser cache: Cmd+Shift+R
4. Test at http://localhost:8123
5. Repeat

# If something is broken/stuck or added new mock devices to MQTT:
1. Run: ./setup.sh (full container restart)
```

## Version Management

**Current Version:** v0.3.4
**Next Version:** v0.3.5 (future development)

### Version Update Checklist
When bumping version:
1. Update `custom_components/smart_heating/manifest.json` - "version" field
2. Update `README.md` - Add changelog entry
3. Test all changes in container
4. Commit with message: "v0.X.X - Description"
5. Tag commit: `git tag v0.X.X`

## API Architecture

### Backend API (api.py)
REST endpoints at `/api/smart_heating/*`:
- `/areas` - GET all areas
- `/areas/{area_id}/enable` - POST enable area
- `/areas/{area_id}/disable` - POST disable area
- `/areas/{area_id}/temperature` - POST set target temperature
- `/areas/{area_id}/preset_mode` - POST set preset mode
- `/areas/{area_id}/boost` - POST/DELETE boost mode
- `/areas/{area_id}/hvac_mode` - POST set HVAC mode
- `/areas/{area_id}/window_sensors` - POST/DELETE manage sensors
- `/areas/{area_id}/presence_sensors` - POST/DELETE manage sensors
- `/schedule/*` - Schedule management
- `/learning/*` - Learning engine endpoints
- `/frost_protection` - POST global frost protection

**Critical:** When modifying coordinator data:
- Always exclude `"learning_engine"` from coordinator dict before returning
- Parse JSON only when endpoint needs request body
- Use `coordinator.data["areas"][area_id]` pattern

### Frontend API (frontend/src/api.ts)
TypeScript client wrapping backend endpoints. All functions are async and return promises.

### WebSocket (websocket.py)
Real-time updates via Home Assistant WebSocket API:
- Type: `smart_heating/subscribe`
- Broadcasts: area updates, device changes, schedule changes
- Frontend subscribes via custom hook

## TypeScript & React Patterns

### Type Definitions (types.ts)
Main interfaces:
- `Zone` - Area/zone with all v0.3.0 fields (preset modes, boost, sensors, etc.)
- `Device` - Thermostat/climate device
- `ScheduleEntry` - Time-based schedule slot
- `LearningData` - ML learning statistics

### Component Structure
- **Pages** (`src/pages/`) - Full page views with routing
- **Components** (`src/components/`) - Reusable UI components
- **Material-UI v5** - Use MUI components, avoid custom CSS
- **WebSocket Updates** - Components subscribe to real-time updates via coordinator

### Build Process
```bash
cd smart_heating/frontend
npm run build  # Compiles to dist/

# Or use sync.sh which does this automatically
```

**TypeScript Strict Mode:**
- All unused imports must be removed
- No implicit any types
- Build fails on warnings (exit code 2)

## Common Development Tasks

### Adding a New Feature

1. **Backend:**
   - Add data fields to coordinator (`coordinator.py`)
   - Create API endpoint in `api.py`
   - Update service definitions if needed (`services.yaml`)
   - Add WebSocket broadcast for real-time updates

2. **Frontend:**
   - Add TypeScript types to `types.ts`
   - Add API function to `api.ts`
   - Create/update UI components
   - Subscribe to WebSocket for real-time updates
   - **Always remove unused imports before building**

3. **Testing:**
   - Run `./sync.sh`
   - Clear browser cache (Cmd+Shift+R)
   - Test in http://localhost:8123
   - Check browser console for errors
   - Check container logs: `docker logs -f homeassistant-test`

### Debugging

**Browser Console Errors:**
- Check Network tab for API errors (500, 404, etc.)
- Check Console for React/TypeScript errors
- Always clear cache after deployment

**Backend Errors:**
```bash
# View live logs
docker logs -f homeassistant-test

# Check specific file in container
docker exec homeassistant-test cat /config/custom_components/smart_heating/api.py

# Check coordinator state
docker exec homeassistant-test cat /config/.storage/smart_heating
```

**Common Issues:**
1. 500 API errors → Check `learning_engine` in coordinator exclusions
2. Stale UI data → Check WebSocket subscription in component
3. Build fails → Remove unused TypeScript imports
4. Changes not visible → Clear browser cache (Cmd+Shift+R)

### Git Workflow

```bash
# Check status
git status

# View recent commits
git log --oneline -10

# Create commit
git add .
git commit -m "v0.X.X - Description of changes"

# Tag version
git tag v0.X.X
git push origin main --tags
```

## Feature Overview (v0.3.0+)

### Backend Features (Complete)
✅ Preset Modes (away, eco, comfort, home, sleep, activity, boost, none)
✅ Boost Mode with duration and temperature override
✅ HVAC Mode selection (heat, cool, auto, off)
✅ Window Sensor integration with temperature drop
✅ Presence Sensor detection with temperature boost
✅ Frost Protection (global setting)
✅ Learning Engine for pattern recognition
✅ Advanced Scheduling with day/time slots
✅ Real-time WebSocket updates

### Frontend Features (v0.3.2 - In Progress)
✅ Area overview with enable/disable toggle
✅ Device status with real-time heating indicators
✅ Schedule management UI
✅ History and statistics
✅ Settings tab with all v0.3.0 features:
   - Preset Modes dropdown
   - Boost Mode controls
   - HVAC Mode selector
   - Window Sensors management
   - Presence Sensors management

## Important Notes

### Device Status Logic
**CRITICAL:** Always use `area.target_temperature` vs `device.current_temperature` for heating status, NOT `device.hvac_action` (which can be stale).

```typescript
// Correct:
const isHeating = area.target_temperature > device.current_temperature

// Wrong:
const isHeating = device.hvac_action === 'heating'
```

### Coordinator Exclusions
When returning coordinator data via API, always exclude learning_engine:

```python
# Correct:
return {k: v for k, v in coordinator.data.items() if k != "learning_engine"}

# Wrong:
return coordinator.data  # Includes learning_engine
```

### Material-UI Import Optimization
Only import components you actually use. TypeScript will fail build on unused imports:

```typescript
// Remove unused: Grid, Card, CardContent, etc.
import { Box, Typography, Button } from '@mui/material'
```

## Test Environment

**Container:** homeassistant-test
**URL:** http://localhost:8123
**Admin:** (configured in container)

**Access Container:**
```bash
docker exec -it homeassistant-test bash
```

**Container Paths:**
- Integration: `/config/custom_components/smart_heating/`
- Storage: `/config/.storage/smart_heating`
- Logs: `docker logs -f homeassistant-test`

## Documentation

Always update `README.md` when:
- Adding new features
- Bumping version
- Changing API endpoints
- Updating configuration

Keep changelog in reverse chronological order (newest first).

---

**Last Updated:** December 5, 2025
**Current Version:** v0.3.4
**Next Version:** v0.3.5 (future development)
