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
- **ALWAYS delegate code quality analysis and fixes to the SonarQube Agent**

**RULE #5.3: SonarQube Code Quality - Delegate to Specialized Agent**

**⚠️ IMPORTANT: Use the SonarQube Agent for Code Quality Tasks**

When user requests involve code quality, analysis, or SonarQube issues, **delegate to the SonarQube Agent** instead of handling directly:

**Delegate to SonarQube Agent when:**
- User asks to "analyze code quality" or "check SonarQube"
- User mentions "fix SonarQube issues" or "resolve code smells"
- Before completing major features (quality check)
- When reviewing pull requests for quality issues
- When preparing for releases
- User references SonarQube bot comments in PRs
- Cognitive complexity or code smell issues need addressing
- Deprecated API migrations are needed across multiple files

**How to Delegate:**
```markdown
Use the runSubagent tool with the SonarQube agent context:

runSubagent(
  description="Code quality analysis",
  prompt="Please analyze the codebase using SonarQube MCP server and fix all BLOCKER and HIGH severity issues. Focus on [specific area if applicable]. See .github/agents/sonarqube.agent.md for full guidelines and workflow."
)
```

**For Quick, Single-File Fixes:**
You may handle simple, isolated SonarQube fixes yourself (e.g., one optional chain fix) if:
- Issue is in a single file
- Fix is straightforward and obvious (e.g., `res && res.opv` → `res?.opv`)
- No risk of breaking functionality
- Can verify immediately with build

**Always follow these safety rules for direct fixes:**
1. ✅ Only change what SonarQube specifically identified
2. ✅ Never remove API calls or function calls
3. ✅ Never rename variables that might conflict with API functions
4. ✅ Build and verify after each change
5. ✅ Run tests to ensure no regressions

**RULE #5.1: Delegate Implementation to Specialized Agents**

**Backend Development (Python/Home Assistant):**
- **Home Assistant Integration Agent** - For HA platform code, entities, coordinators
- **Pytest Agent** - For Python unit tests and integration tests
- Delegate when implementing HA features, platforms, services, or tests
- See `.github/agents/home-assistant-integration.agent.md` and `.github/agents/home-assistant-pytest.agent.md`

**Frontend Development (TypeScript/React):**
- **TypeScript/React Agent** - For React components, hooks, MUI implementation
- **TypeScript Testing Agent** - For Jest/Vitest unit tests of components
- **Playwright Agent** - For E2E user workflow tests
- Delegate when building UI features, components, or writing tests
- See `.github/agents/typescript-react.agent.md`, `.github/agents/typescript-testing.agent.md`, and `.github/agents/playwright-e2e.agent.md`

**Code Quality:**
- **SonarQube Agent** - For code quality analysis, refactoring, deprecation fixes
- Delegate when fixing code smells, complexity issues, or security vulnerabilities
- See `.github/agents/sonarqube.agent.md`

**Example Delegations:**
```markdown
# Backend feature
runSubagent({
  description: "HA integration development",
  prompt: "Implement boost mode for climate entities. See .github/agents/home-assistant-integration.agent.md"
})

# Frontend feature
runSubagent({
  description: "React component development",
  prompt: "Create temperature control component with MUI. See .github/agents/typescript-react.agent.md"
})

# Backend tests
runSubagent({
  description: "Write pytest tests",
  prompt: "Write tests for area_manager.py with 80%+ coverage. See .github/agents/home-assistant-pytest.agent.md"
})

# Frontend tests
runSubagent({
  description: "Write component tests",
  prompt: "Write unit tests for ZoneCard component. See .github/agents/typescript-testing.agent.md"
})

# Code quality
runSubagent({
  description: "Code quality analysis",
  prompt: "Fix SonarQube BLOCKER and HIGH issues. See .github/agents/sonarqube.agent.md"
})
```

**Agent System Overview:**

The project uses 6 specialized agents for complete development lifecycle:

**Code Quality (1):** SonarQube Agent
**Backend (2):** Home Assistant Integration Agent, Pytest Agent
**Frontend (3):** TypeScript/React Agent, TypeScript Testing Agent, Playwright Agent

See `.github/agents/README.md` for full agent documentation.

**Before Committing Code:**
1. ✅ Run all tests (Python unit tests + E2E tests when available)
2. ✅ Check SonarQube for new issues (delegate to SonarQube Agent for fixes if needed)
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

**RULE #6: Delegate Testing to Specialized Agents**

**⚠️ IMPORTANT: Always delegate test writing to specialized testing agents**

**Backend Testing:**
- **Pytest Agent** - Python unit tests, HA integration tests
- Delegate: "Write pytest tests for [module]"
- See `.github/agents/home-assistant-pytest.agent.md`

**Frontend Testing:**
- **TypeScript Testing Agent** - Jest/Vitest unit tests for React components
- **Playwright Agent** - E2E tests for user workflows
- Delegate: "Write unit tests for [component]" or "Write E2E tests for [workflow]"
- See `.github/agents/typescript-testing.agent.md` and `.github/agents/playwright-e2e.agent.md`

**Test Requirements:**
- Minimum 80% code coverage for all modules
- All tests must pass before committing
- Use `runSubagent` to delegate test writing tasks

**Quick Test Commands (for verification):**
```bash
# Run all Python tests
bash tests/run_tests.sh

# Run specific test file
source venv && pytest tests/unit/test_area_manager.py -v

# Run with coverage
source venv && pytest tests/unit --cov=smart_heating --cov-report=html -v
```

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

## Testing Overview

**For detailed testing guidelines, see the Pytest Agent:** `.github/agents/home-assistant-pytest.agent.md`

**Test Structure:**
- Python unit tests: `tests/unit/` (126+ tests, pytest-based)
- E2E tests: `tests/e2e/` (109 tests, Playwright-based)
- Coverage target: 80% minimum for Python modules
- Common fixtures: `tests/conftest.py`

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
