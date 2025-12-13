# Copilot Instructions - Smart Heating

## Project Overview
Home Assistant integration for zone-based heating control with learning capabilities.

**Tech Stack:** Python 3.13, React + TypeScript + Material-UI v5, Docker test environment

## Production API Access
**Production Home Assistant URL:** http://homeassistant.local:8123
**Production API Token:** `eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiIwNTc5M2FmNzM5Y2I0ZGQ2ODkzNjZlNzQ0MWRmMWM1YiIsImlhdCI6MTc2NTI5OTk5NywiZXhwIjoyMDgwNjU5OTk3fQ.fBxqcbRlz7oyoH50cBjEmUcJoNr2kMiRDqoJg9T0JFs`

**Example API calls:**
```bash
# Get entity state
curl -s "http://homeassistant.local:8123/api/states/climate.opentherm_gateway_otgw_otgw_thermostat" \
  -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiIwNTc5M2FmNzM5Y2I0ZGQ2ODkzNjZlNzQ0MWRmMWM1YiIsImlhdCI6MTc2NTI5OTk5NywiZXhwIjoyMDgwNjU5OTk3fQ.fBxqcbRlz7oyoH50cBjEmUcJoNr2kMiRDqoJg9T0JFs" | jq

# Get all states
curl -s "http://homeassistant.local:8123/api/states" \
  -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiIwNTc5M2FmNzM5Y2I0ZGQ2ODkzNjZlNzQ0MWRmMWM1YiIsImlhdCI6MTc2NTI5OTk5NywiZXhwIjoyMDgwNjU5OTk3fQ.fBxqcbRlz7oyoH50cBjEmUcJoNr2kMiRDqoJg9T0JFs" | jq
```

## Critical Rules

**RULE #1: Never Remove Features Without Permission**
- ALWAYS ask before removing/changing functionality
- When in doubt, KEEP existing feature and ADD new one

**RULE #2: E2E Testing Required**
- Run `cd tests/e2e && npm test` after ALL code changes
- All tests must pass (100%) before committing

**RULE #3: Git Operations Require User Approval**
- **NEVER** commit code without user testing and approval first
- **NEVER** create git tags without explicit user request
- **NEVER** push to GitHub without user confirmation
- **NEVER** push any code when there are failing tests
- After implementing features: Deploy → Test API → Run Tests → Update Docs & Translations → Let user test → Wait for approval → THEN commit/tag/push
- Workflow: Code → Deploy (bash scripts/deploy_test.sh) → Test API → Run bash tests/run_tests.sh → Run E2E tests → Update Docs (EN+NL) → Update Translations (EN+NL) → User approval → Git operations

**RULE #3.1: Version Synchronization**
- App version MUST match git tag version
- When creating a git tag (e.g., v0.4.3), update these files FIRST:
  - `smart_heating/manifest.json` - `"version": "0.4.3"`
  - `smart_heating/frontend/package.json` - `"version": "0.4.3"`
  - `smart_heating/frontend/src/components/Header.tsx` - `label="v0.4.3"`
- Then commit version changes: `git commit -m "chore: Update version to v0.4.3"`
- Then create tag: `git tag v0.4.3`
- Keep versions in sync: manifest.json = package.json = Header.tsx = git tag

**RULE #4: Update Documentation & Translations**
- **ALWAYS** update documentation in BOTH languages (EN + NL) when making changes
- **ALWAYS** update translations when adding/modifying UI text
- **ALWAYS** do this BEFORE running tests and asking for user approval
- Required updates:
  - `CHANGELOG.md` + `CHANGELOG.nl.md` - Version history
  - `README.md` + `README.nl.md` - User documentation (if user-facing changes)
  - `docs/en/ARCHITECTURE.md` + `docs/nl/ARCHITECTURE.md` - Architecture changes
  - `docs/en/DEVELOPER.md` + `docs/nl/DEVELOPER.md` - Developer workflow changes
  - Frontend translations: `locales/en/translation.json` + `locales/nl/translation.json`
- Root `ARCHITECTURE.md` should match `docs/en/ARCHITECTURE.md`
- Workflow: Code → Deploy (bash scripts/deploy_test.sh) → Test API → Update All Docs & Translations (EN+NL) → Run Tests (bash tests/run_tests.sh && cd tests/e2e && npm test) → User approval → Commit

**RULE #5: Maintain Code Quality**
- Follow existing code patterns and styles for Home Assistant and this project
- Ensure code is clean, well-documented, and efficient
- **Fix bugs in actual code, don't work around them in tests**
- When HA test suite provides proper fixtures/helpers, use them instead of mocking HA internals
- **ALWAYS use SonarQube MCP server to check code quality before completing tasks**

**RULE #5.3: SonarQube Code Quality Standards**

**CRITICAL: Check SonarQube Before Completing Any Task**
- After making code changes, ALWAYS run: `mcp_sonarqube_search_sonar_issues_in_projects` to check for new issues
- Fix all BLOCKER and HIGH severity issues before committing
- Address MEDIUM severity issues when feasible
- Document any intentionally ignored issues with `# NOSONAR` comments explaining why

**Code Quality Thresholds:**
- **Cognitive Complexity:** Keep functions under 15 complexity (refactor if higher)
- **Function Length:** Keep functions focused and under 50 lines when possible
- **Nesting Depth:** Avoid nesting functions more than 4 levels deep
- **Code Coverage:** Maintain minimum 80% test coverage for all modules
- **Duplication:** Avoid duplicating string literals more than 3 times (use constants)

**Python-Specific Rules:**
- Use `async` file operations in async functions (avoid synchronous `open()`)
- Always provide radix parameter to `int()` conversions: `int(value, 10)`
- Avoid reassigning function parameters
- Use type hints for function parameters and return values
- Keep imports organized: stdlib → third-party → local
- Use `if __name__ == "__main__":` guards for executable scripts

**TypeScript/JavaScript-Specific Rules:**
- Replace deprecated MUI components:
  - `InputLabelProps` → `slotProps={{ inputLabel: { shrink: true } }}`
  - `InputProps` → `slotProps={{ input: { ... } }}`
  - `primaryTypographyProps` → `slotProps={{ primary: { ... } }}`
  - `paragraph` Typography variant → `body1`
  - MUI `Grid` → `Grid2` or CSS Grid with Box component
- Use `globalThis` instead of `window` for global scope
- Always provide radix to `parseInt(value, 10)` and use `Number.parseFloat(value)`
- Avoid nested ternary operators (extract to helper functions or if/else)
- Fix optional chaining issues: ensure safe property access
- Use `Array.from()` or spread operator instead of `.slice()` for array copies
- Avoid deeply nested callbacks (refactor to separate functions)
- Use `const` by default, `let` only when reassignment needed, never `var`

**Common Refactoring Patterns:**
1. **High Cognitive Complexity** → Extract helper functions, use early returns, reduce nesting
2. **Nested Ternaries** → Create helper functions with clear names
3. **Duplicated Literals** → Extract to constants at module/class level
4. **Long Functions** → Split into smaller, focused functions with single responsibilities
5. **Deep Nesting** → Use guard clauses, early returns, and extract nested logic

**SonarQube MCP Server Workflow:**
```bash
# 1. Check for issues after making changes
mcp_sonarqube_search_sonar_issues_in_projects(projects=["TheFlexican_smart-heating"], severities=["HIGH", "BLOCKER"])

# 2. Get details on specific rules if needed
mcp_sonarqube_show_rule(key="typescript:S3776")  # Cognitive complexity
mcp_sonarqube_show_rule(key="python:S3776")     # Cognitive complexity

# 3. Analyze specific file for issues
mcp_sonarqube_analyze_code_snippet(projectKey="TheFlexican_smart-heating", codeSnippet="...", language="typescript")

# 4. Check project quality gate status
mcp_sonarqube_get_project_quality_gate_status(projectKey="TheFlexican_smart-heating")
```

**Before Committing Code:**
1. ✅ Run all tests (Python unit tests + E2E tests when available)
2. ✅ Check SonarQube for new issues: `mcp_sonarqube_search_sonar_issues_in_projects`
3. ✅ Fix all BLOCKER and HIGH severity issues
4. ✅ Verify code coverage meets 80% threshold
5. ✅ Update documentation (EN + NL) if user-facing changes
6. ✅ Update translations if UI text changed
7. ✅ Build succeeds without errors or warnings
8. ✅ Get user approval before git operations

**RULE #5.1: Never Stop Halfway During Tasks**
- **ALWAYS complete assigned work fully** - No stopping to give summaries or status updates
- **Continue working until the task is 100% done** - Don't pause for user confirmation mid-task
- If a task has multiple steps, complete ALL steps before finishing
- Only stop when explicitly encountering a blocker that requires user input
- Token budget is 1,000,000 - use it fully to complete work
- No matter how complex or time-consuming, finish what you start

**RULE #5.2: Task Planning & Tracking**
- **DO NOT create detailed implementation plans** - Jump straight into implementation
- **DO use manage_todo_list tool** to track multi-step work as you implement
- **Create todos at start of complex tasks** to track what needs to be done
- **Update todos as in-progress/completed** while working through the task
- **Keep todos actionable and specific** - "Implement X feature" not "Plan X feature"
- Example workflow:
  1. User: "Add multi-user presence tracking"
  2. Create todos: Backend, API, Frontend, Tests
  3. Mark todo #1 in-progress → implement → mark completed
  4. Mark todo #2 in-progress → implement → mark completed
  5. Continue until all todos complete
- Skip todo tracking for simple single-step tasks

**RULE #6: Test Coverage**
- **Minimum 80% code coverage required** for all Python modules
- **Two test layers:** Python unit tests (pytest) + E2E tests (Playwright)
- **NEVER skip writing tests** - No matter how complex or time-consuming
- **ALL tests must be fully implemented** - No placeholder or skipped tests without explicit user permission
- **NEVER stop implementing tests** due to "complexity" or token usage concerns
- If a test is complex, take the time to implement it properly with mocks and fixtures
- Token budget is 1,000,000 - don't stop until the work is complete or you hit actual limits

**NOTE FOR TEST AUTHORS**
- When writing tests for numeric values (e.g., hysteresis thresholds and temperatures), avoid relying on MagicMock objects in a way that causes accidental numeric conversions. MagicMock values may respond to arithmetic operators and can create unexpected behavior. Prefer explicitly typed numbers or parseable strings when required by the code under test.
- If an area-level configuration value (like `hysteresis_override`) may be present in tests as a MagicMock, explicitly cast or validate numeric types in tests or in code. E.g.:

```python
val = getattr(area, 'hysteresis_override', None)
if isinstance(val, (int, float)):
  val = float(val)
else:
  # choose default
  val = 0.5
```

This ensures tests don't assume MagicMock numeric behavior and makes results deterministic.

**FINDINGS FROM RECENT CHANGE:**
- The thermostat idle logic has been updated to use a hysteresis-aware setpoint for idle devices. If the current area temperature >= (target - hysteresis) then we set the thermostat to the current temperature; otherwise keep the target temperature. Duplicate `climate.set_temperature` calls are avoided by caching the last set setpoint per thermostat.
- To test the new code, prefer to create fixtures that set `area.current_temperature` and `area.hysteresis_override` to numeric values (int/float or numeric-string). Avoid MagicMock for these values so comparisons are safe.
- Example test pattern for idle thermostat behavior:

```python
@pytest.mark.asyncio
async def test_idle_hysteresis_behavior(device_handler, mock_area):
  mock_area.get_thermostats.return_value = ['climate.thermo1']
  mock_area.current_temperature = 21.0
  await device_handler.async_control_thermostats(mock_area, False, 22.0)
  # Expect climate.set_temperature called to 22.0 or 21.0 depending on hysteresis
```

Following this pattern will avoid unexpected comparisons and make tests deterministic.

**RULE #7: API Testing After Deployment**
- **ALWAYS test API endpoints after deploying features/fixes** using curl commands
- Test all new/modified endpoints with valid and invalid inputs
- Verify error handling and validation rules
- Test boundary conditions (min/max values, edge cases)
- Example workflow after deployment:
  1. Deploy changes: `bash scripts/deploy_test.sh`
  2. Test GET endpoints: `curl -s http://localhost:8123/api/smart_heating/[endpoint] | jq`
  3. Test POST endpoints with valid data: `curl -s -X POST ... -d '{...}' | jq`
  4. Test validation with invalid data (above/below limits, wrong types)
  5. Verify responses match expected schema
  6. Check error messages are clear and helpful
- Document test results showing successful validation and error handling
- This ensures features work end-to-end before user testing

**Python Unit Tests (pytest):**
- Location: `tests/unit/` directory
- Framework: pytest with pytest-asyncio, pytest-cov, pytest-homeassistant-custom-component
- Run: `bash tests/run_tests.sh` (automated) or `pytest tests/unit --cov=smart_heating -v`
- Coverage: HTML report at `coverage_html/index.html`, enforced 80% threshold
- Test files: 12+ files with 126+ test functions covering:
  - `test_area_manager.py` - Area CRUD, global settings (19 tests, 90%+ target)
  - `test_models_area.py` - Area model, devices, sensors (20 tests, 90%+ target)
  - `test_coordinator.py` - Data coordination (15 tests, 80%+ target)
  - `test_climate.py` - Climate platform (14 tests, 80%+ target)
  - `test_scheduler.py` - Schedule execution (11 tests, 80%+ target)
  - `test_safety_monitor.py` - Safety monitoring (10 tests, 80%+ target)
  - `test_vacation_manager.py` - Vacation mode (10 tests, 80%+ target)
  - `test_switch.py` - Switch platform (8 tests, 80%+ target)
  - `test_utils.py` - Validators, response builders (8 tests, 90%+ target)
  - `test_config_flow.py` - Config flow (5 tests, 80%+ target)
  - `test_init.py` - Integration setup (6 tests, 80%+ target)
- Common fixtures in `tests/conftest.py`: mock_area_manager, mock_coordinator, mock_area_data, etc.
- Documentation: `tests/README.md` (comprehensive guide), `TESTING_SUMMARY.md`, `TESTING_QUICKSTART.md`

**E2E Tests (Playwright):**
- Location: `tests/e2e/` directory
- Run: `cd tests/e2e && npm test`
- Coverage: 109 total tests, 105 passing, 4 skipped
- Test files: navigation, temperature-control, boost-mode, comprehensive-features, sensor-management, backend-logging, device-management, enhanced-schedule-ui, vacation-mode
- Must pass 100% before committing

**When Adding New Features:**
1. Write Python unit tests FIRST (TDD approach recommended)
2. Add E2E tests for user-facing features
3. Run both test suites: `bash tests/run_tests.sh && cd tests/e2e && npm test`
4. Verify coverage meets 80%: check `coverage_html/index.html`
5. Update tests when modifying existing code
6. Test edge cases, error conditions, and boundary values
7. **Never skip tests** - implement them fully even if complex

**Home Assistant Testing Best Practices (per official docs):**
- Use official `pytest-homeassistant-custom-component` package
- Use `MockConfigEntry` from `pytest_homeassistant_custom_component.common`
- Use `hass` fixture for Home Assistant instance
- Test via HA core interfaces (hass.states, hass.services, registries)
- Mock external dependencies properly
- Use async_setup_entry/async_unload_entry patterns
- Test entity properties through coordinator data
- Follow patterns from https://developers.home-assistant.io/docs/development_testing/

**Quick Commands:**
```bash
# Run Python unit tests
bash tests/run_tests.sh

# Run specific test file
source venv && pytest tests/unit/test_area_manager.py -v

# Run with coverage report
source venv && pytest tests/unit --cov=smart_heating --cov-report=html -v

# Run E2E tests
cd tests/e2e && npm test
```

## Key Directories
```
smart_heating/          # Main integration (backend .py files + frontend/)
tests/e2e/             # Playwright tests
tests/unit/            # Python unit tests
docs/                  # Language-specific documentation
  en/                  # English technical docs (ARCHITECTURE.md, DEVELOPER.md)
  nl/                  # Dutch technical docs (ARCHITECTURE.md, DEVELOPER.md)
scripts/deploy_test.sh # Deploy to test container (PRIMARY DEPLOY SCRIPT)
```

## Documentation Structure

**Dual-language support:** All documentation available in English and Dutch

**Root-level files:**
- `README.md` / `README.nl.md` - User documentation
- `CHANGELOG.md` / `CHANGELOG.nl.md` - Version history

**Organized docs (PRIMARY SOURCE):**
- `docs/en/` - English technical documentation (ARCHITECTURE.md, DEVELOPER.md)
- `docs/nl/` - Dutch technical documentation (ARCHITECTURE.md, DEVELOPER.md)
- **Always update docs/ versions first, they are the authoritative source**

**Frontend translations:**
- `smart_heating/frontend/src/locales/en/translation.json` - English UI text
- `smart_heating/frontend/src/locales/nl/translation.json` - Dutch UI text

**When updating documentation:**
1. Update docs/en/ and docs/nl/ versions (primary source)
2. Update both EN and NL versions
3. Update frontend translation.json if UI text changed
4. See `docs/README.md` for complete maintenance checklist

## Development Workflow

**Note:** No time constraints - take time to ensure quality and completeness

**Primary Deploy Script:** `bash scripts/deploy_test.sh` - builds frontend, syncs to container, restarts HA

```bash
# Normal development cycle:
1. Edit code
2. bash scripts/deploy_test.sh  # ALWAYS use this script
3. Clear browser cache (Cmd+Shift+R)
4. Test at http://localhost:8123
5. Run tests: bash tests/run_tests.sh && cd tests/e2e && npm test
6. Update docs & translations (EN + NL)
7. Commit only after user approval
```

**CRITICAL:** Always use `bash scripts/deploy_test.sh` for deployment - never use sync.sh or setup.sh

## Testing

**Run tests:** `cd tests/e2e && npm test`
**Test files:** navigation, temperature-control, boost-mode, comprehensive-features, sensor-management, backend-logging

**Debug tests:**
- Run headed: `npm test -- --headed`
- Add `await page.pause()` for inspection
- Check `playwright.config.ts` for headless setting

## API Architecture

### Backend (api.py)
Key endpoints: `/api/smart_heating/areas`, `/devices`, `/schedule/*`, `/learning/*`

**Critical patterns:**
- Always exclude `"learning_engine"` from coordinator data before returning
- Device discovery is platform-agnostic (works with ALL HA integrations, not just MQTT)

### Frontend (api.ts)
TypeScript client wrapping backend REST API

### WebSocket (websocket.py)
Real-time updates via `smart_heating/subscribe` event type

## TypeScript & React

**Key files:**
- `types.ts` - Zone, Device, ScheduleEntry, LearningData interfaces
- `api.ts` - Frontend API client
- Material-UI v5 components
- WebSocket updates via custom hooks

**Build:** `cd smart_heating/frontend && npm run build` (or use sync.sh)
**TypeScript strict mode:** Remove unused imports, no implicit any

## Common Tasks

### Adding Features
1. **Backend:** Update coordinator, add API endpoint, update services.yaml
2. **Frontend:** Add types, API functions, UI components, WebSocket subscriptions
3. **Deploy:** `./sync.sh` → Clear cache (Cmd+Shift+R) → **WAIT FOR USER TO TEST**
4. **After user approval:** Run E2E tests if needed
5. **After user confirms:** Ask before committing/tagging/pushing to git

### Debugging
- Browser: Check Network/Console tabs
- Backend: `docker logs homeassistant-test`
- Common fixes:
  - 500 errors → Check learning_engine exclusions
  - Stale UI → Check WebSocket subscription
  - Build fails → Remove unused imports
  - Changes not visible → Clear cache

## Important Patterns

### Device Heating Status
Use `area.target_temperature > device.current_temperature`, NOT `device.hvac_action`

### Coordinator Data Returns
Always exclude learning_engine:
```python
return {k: v for k, v in coordinator.data.items() if k != "learning_engine"}
```

### Material-UI Imports
Only import used components:
```typescript
import { Box, Typography, Button } from '@mui/material'
```

---
