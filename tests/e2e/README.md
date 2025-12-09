# Smart Heating E2E Tests

End-to-end tests for the Smart Heating Home Assistant integration using Playwright.

## Test Coverage

### Automated Tests (Playwright)
- ✅ **Navigation** - Menu, area navigation, tab switching
- ✅ **Temperature Control** - Slider adjustments, input changes
- ✅ **Boost Mode** - Activation, duration selection, cancellation
- ✅ **Comprehensive Features** - Preset modes, manual override, WebSocket updates
- ✅ **Sensor Management** - Window sensors, presence sensors (basic operations)
- ✅ **Backend Logging** - API error handling
- ✅ **History Storage** - Database migration, storage backend switching (see unit tests for database logic)

### Database Migration Testing

**Unit Tests** (`tests/unit/test_history.py`):
- JSON ↔ Database migration workflows
- Database detection and validation
- Storage backend persistence
- SQLAlchemy 2.0 compatibility

**Integration Testing** (Manual):
1. Configure MariaDB/PostgreSQL in `configuration.yaml`:
   ```yaml
   recorder:
     db_url: mysql://user:pass@host/database
   ```
2. Use API endpoints to test migration:
   - `GET /api/smart_heating/history/storage/info`
   - `POST /api/smart_heating/history/storage/migrate`
   - `GET /api/smart_heating/history/storage/database/stats`
3. Verify data persists across HA restarts

**E2E Testing**:
- History chart displays data from both backends
- Storage backend changes reflected in UI (future enhancement)

### Manual Testing Required
- ⚠️ **Global Presets** - See `GLOBAL_PRESETS_TEST_GUIDE.md`
  - Global preset temperature configuration
  - Per-area preset toggle (global vs custom)
  - Manual override integration
  - Simplified presence sensor configuration

**Note:** Global presets tests (`global-presets.spec.ts`) exist but are currently non-functional due to UI selector issues. Use the manual testing guide until these are resolved.

## Prerequisites

1. **Home Assistant must be running** on `http://localhost:8123`
2. **Smart Heating integration must be installed** and configured
3. **At least one area** (Living Room) must be set up with devices

## Installation

```bash
cd tests/e2e
npm install
npx playwright install chromium
```

## Running Tests

### Run all tests (headless)
```bash
npm test
```

### Run tests with browser visible
```bash
npm run test:headed
```

### Debug tests (step through with Playwright Inspector)
```bash
npm run test:debug
```

### Run tests in UI mode (interactive)
```bash
npm run test:ui
```

### View test report
```bash
npm run report
```

### Generate new tests (codegen)
```bash
npm run codegen
```

## Test Coverage

### Navigation Tests
- Load Smart Heating panel
- Display areas list
- Navigate to area detail

### Temperature Control Tests
- Adjust target temperature
- Enable/disable area

### Boost Mode Tests ✨
- Activate boost mode
- Cancel boost mode
- Verify boost mode affects heating state

### Preset Mode Tests
- Change preset modes (Eco, Comfort, etc.)

### Sensor Management Tests
- Add presence sensor
- Remove presence sensor
- Configure sensor actions

### Draggable Settings Tests
- Verify drag handles present
- Check localStorage persistence

### Schedule & History Tests
- Navigate to schedule tab
- Display history chart

### Error Handling Tests
- Handle backend errors gracefully
- Display backend log errors

### Real-time Updates Tests
- Receive WebSocket temperature updates

## Test Structure

```
tests/e2e/
├── playwright.config.ts     # Playwright configuration
├── tsconfig.json             # TypeScript configuration
├── package.json              # Dependencies and scripts
├── tests/
│   └── smart-heating.spec.ts # Main test suite
└── README.md                 # This file
```

## Writing New Tests

1. Add new test suites to `tests/smart-heating.spec.ts`
2. Use helper functions:
   - `navigateToSmartHeating(page)` - Navigate to Smart Heating panel
   - `navigateToArea(page, areaName)` - Navigate to specific area
   - `switchToTab(page, tabName)` - Switch between tabs

3. Always clean up after tests (e.g., cancel boost mode, remove sensors)

## Debugging Tips

### Check Backend Logs
```bash
docker logs -f homeassistant-test | grep "smart_heating\|ERROR"
```

### Check Frontend Console
Errors are captured automatically in tests via:
```typescript
page.on('console', msg => {
  if (msg.type() === 'error') {
    consoleErrors.push(msg.text());
  }
});
```

### Screenshots on Failure
Playwright automatically captures:
- Screenshots on test failure
- Video recordings (if enabled)
- Traces for debugging

Find them in:
- `test-results/` - Individual test artifacts
- `playwright-report/` - HTML report with screenshots

## Continuous Integration

To run tests in CI:

```bash
# In your CI pipeline
cd tests/e2e
npm ci
npx playwright install --with-deps chromium
npm test
```

## Troubleshooting

### Tests fail to connect to Home Assistant
- Verify Home Assistant is running: `curl http://localhost:8123`
- Check Docker container: `docker ps | grep homeassistant`

### Selectors not found
- UI may have changed - update selectors in tests
- Use `npm run codegen` to generate new selectors

### Tests timeout
- Increase timeout in `playwright.config.ts`
- Check if Home Assistant is responding slowly
- Climate control cycle is 30 seconds - tests wait accordingly

## Future Enhancements

- [ ] Add visual regression testing
- [ ] Add performance metrics
- [ ] Add API-level tests (bypass UI)
- [ ] Add mobile device testing
- [ ] Add accessibility tests
- [ ] Integrate backend log checking
- [ ] Add network condition simulation
- [ ] Add multi-area tests
