# Agent Workflow Examples

This document provides practical examples of how to use the custom agents for common development tasks in the Smart Heating project.

## Table of Contents

- [Implementing a New Feature](#implementing-a-new-feature)
- [Fixing Backend Bugs](#fixing-backend-bugs)
- [Fixing Frontend Bugs](#fixing-frontend-bugs)
- [Backend Code Quality Check](#backend-code-quality-check)
- [Frontend Code Quality Check](#frontend-code-quality-check)

---

## Implementing a New Feature

### Example: Add Vacation Mode Feature

**Full workflow from planning to deployment:**

#### Step 1: Start with Home Assistant Integration Agent
```
@home-assistant-integration "Add vacation mode feature:
- Allow users to set away dates
- Reduce temperature during vacation
- Store vacation schedule in area configuration"
```

**What the agent does:**
- Creates vacation mode logic in `area_manager.py`
- Updates coordinator with vacation state
- Adds vacation mode service
- Updates `services.yaml`

**Handoff:** Click **[Write Tests]** button

---

#### Step 2: Write Backend Tests
```
@home-assistant-pytest "Write tests for vacation mode:
- Test vacation mode enable/disable
- Test temperature reduction during vacation
- Test vacation schedule validation
- Ensure 80%+ coverage"
```

**What the agent does:**
- Creates `tests/unit/test_vacation_mode.py`
- Tests all vacation mode scenarios
- Verifies coverage meets 80%

**Handoff:** Click **[Run Tests]** button

---

#### Step 3: Run Backend Tests
```
Run bash tests/run_tests.sh to verify all tests pass
```

---

#### Step 4: Build Frontend UI
```
@typescript-react "Create vacation mode UI component:
- Date picker for start/end dates
- Toggle for vacation mode
- Display active vacation status in ZoneCard
- Use Material-UI DatePicker
- Add EN/NL translations"
```

**What the agent does:**
- Creates `VacationModeDialog.tsx` component
- Updates `ZoneCard.tsx` to show vacation status
- Adds vacation mode button
- Updates translations

**Handoff:** Click **[Write Unit Tests]** button

---

#### Step 5: Write Frontend Unit Tests
```
@typescript-testing "Write unit tests for VacationModeDialog:
- Test date selection
- Test validation (start < end)
- Test API calls
- Test error handling
- Achieve 80%+ coverage"
```

**What the agent does:**
- Creates `VacationModeDialog.test.tsx`
- Tests component rendering and interactions
- Mocks API calls

**Handoff:** Click **[Run Tests]** button

---

#### Step 6: Write E2E Tests
```
@playwright-e2e "Write E2E test for vacation mode workflow:
1. Navigate to area detail
2. Click vacation mode button
3. Set start and end dates
4. Save vacation mode
5. Verify vacation status displayed
6. Verify temperature adjusted"
```

**What the agent does:**
- Creates `tests/e2e/tests/vacation-mode.spec.ts`
- Tests complete user workflow
- Verifies real-time updates

**Handoff:** Click **[Run E2E Tests]** button

---

#### Step 7: Check Code Quality
```
@sonarqube-quality "Review vacation mode implementation:
- Check for code smells
- Verify no security issues
- Check cognitive complexity
- Fix any BLOCKER or HIGH issues"
```

**What the agent does:**
- Analyzes all vacation mode code
- Refactors complex functions
- Fixes quality issues

**Handoff:** Click **[Deploy Changes]** button

---

#### Step 8: Deploy and Test
```
Deploy using bash scripts/deploy_test.sh
Test manually at http://localhost:8123
```

---

#### Step 9: Update Documentation
```
Update CHANGELOG.md and README.md with vacation mode feature
Add EN + NL documentation
```

---

## Fixing Backend Bugs

### Example: Fix Temperature Sensor Reading Error

#### Step 1: Identify the Bug
```
Bug report: Temperature sensor occasionally returns None,
causing crashes in area_manager.py
```

#### Step 2: Write Failing Test First (TDD Approach)
```
@home-assistant-pytest "Write regression test for temperature sensor None handling:
- Test area_manager handles None temperature
- Test fallback to last known temperature
- Test logging of sensor errors"
```

**What the agent does:**
- Creates test that currently fails
- Documents expected behavior

---

#### Step 3: Fix the Bug
```
@home-assistant-integration "Fix temperature sensor None handling:
- Add None check in area_manager.get_current_temperature()
- Use last known temperature as fallback
- Log warning when sensor returns None
- Don't crash the coordinator"
```

**What the agent does:**
- Adds defensive code
- Implements fallback logic
- Adds proper error handling

**Handoff:** Click **[Write Tests]** button (if more tests needed)

---

#### Step 4: Verify Fix
```
Run bash tests/run_tests.sh
Verify the new test now passes
```

---

#### Step 5: Check for Similar Issues
```
@sonarqube-quality "Review area_manager.py for similar None handling issues:
- Check all sensor access points
- Verify defensive programming
- Look for potential NullPointerExceptions"
```

**Handoff:** Click **[Deploy Changes]** button

---

#### Step 6: Deploy and Verify
```
bash scripts/deploy_test.sh
Test with actual sensor that returns None
Monitor logs for warnings
```

---

## Fixing Frontend Bugs

### Example: Fix ZoneCard Not Updating on WebSocket Message

#### Step 1: Identify the Bug
```
Bug report: ZoneCard doesn't update when temperature changes
via WebSocket. Manual refresh shows correct value.
```

#### Step 2: Write Failing Test First
```
@typescript-testing "Write test for ZoneCard WebSocket updates:
- Mock WebSocket message with temperature change
- Verify component re-renders
- Verify new temperature displayed"
```

**What the agent does:**
- Creates failing test
- Sets up WebSocket mocks

---

#### Step 3: Fix the Bug
```
@typescript-react "Fix ZoneCard WebSocket subscription:
- Review useEffect dependencies in ZoneCard
- Ensure WebSocket listener updates state
- Verify component re-renders on state change
- Check if area.id is in dependency array"
```

**What the agent does:**
- Fixes useEffect dependencies
- Updates WebSocket subscription logic
- Ensures proper cleanup

**Handoff:** Click **[Write Unit Tests]** button

---

#### Step 4: Add Comprehensive Tests
```
@typescript-testing "Add tests for ZoneCard WebSocket lifecycle:
- Test subscription on mount
- Test unsubscription on unmount
- Test multiple rapid updates
- Test error handling"
```

---

#### Step 5: Verify with E2E Test
```
@playwright-e2e "Add E2E test for real-time temperature updates:
1. Open area detail page
2. Trigger temperature change via API
3. Wait for WebSocket update
4. Verify UI updates without refresh"
```

**Handoff:** Click **[Run E2E Tests]** button

---

#### Step 6: Check Code Quality
```
@sonarqube-quality "Review ZoneCard.tsx and WebSocket code:
- Check for memory leaks
- Verify proper cleanup
- Check useEffect dependencies
- Look for similar issues in other components"
```

---

#### Step 7: Deploy and Test
```
bash scripts/deploy_test.sh
Clear browser cache (Cmd+Shift+R)
Test real-time updates work correctly
```

---

## Backend Code Quality Check

### Example: Quality Review Before Release

#### Step 1: Run Full SonarQube Analysis
```
@sonarqube-quality "Perform comprehensive quality analysis of Python backend:
- Analyze all smart_heating/*.py files
- Focus on BLOCKER and HIGH severity issues
- Check cognitive complexity (max 15)
- Review code duplication
- Check test coverage (min 80%)
- Identify security vulnerabilities"
```

**What the agent does:**
- Runs SonarQube analysis
- Lists all quality issues by severity
- Provides refactoring recommendations

---

#### Step 2: Fix Critical Issues
```
@sonarqube-quality "Fix all BLOCKER and HIGH severity issues in backend:
- Refactor complex functions
- Extract duplicate code
- Fix security vulnerabilities
- Add missing error handling
- Update deprecated API calls"
```

**What the agent does:**
- Refactors code systematically
- Maintains functionality
- Adds proper error handling

**Handoff:** Click **[Write Tests]** button

---

#### Step 3: Verify Tests Still Pass
```
@home-assistant-pytest "Update tests for refactored code:
- Fix any broken tests due to refactoring
- Add tests for new error handling
- Ensure coverage remains 80%+"
```

**Handoff:** Click **[Run Tests]** button

---

#### Step 4: Run Tests
```
bash tests/run_tests.sh
Verify 100% pass rate
Check coverage report in coverage_html/
```

---

#### Step 5: Review Medium/Low Issues
```
@sonarqube-quality "Review MEDIUM and LOW severity issues:
- Prioritize high-impact improvements
- Ignore false positives
- Create TODO list for future improvements"
```

---

#### Step 6: Verify Quality Gate
```
Check SonarQube dashboard
Ensure Quality Gate passes:
✅ No BLOCKER issues
✅ No HIGH issues
✅ Coverage ≥ 80%
✅ Duplications < 3%
✅ Maintainability rating A or B
```

---

#### Step 7: Document Improvements
```
Update CHANGELOG.md with code quality improvements
Document any breaking changes
Update architecture docs if needed
```

---

## Frontend Code Quality Check

### Example: Quality Review Before Release

#### Step 1: Run SonarQube Analysis on Frontend
```
@sonarqube-quality "Perform comprehensive quality analysis of TypeScript frontend:
- Analyze smart_heating/frontend/src/**/*.tsx files
- Focus on BLOCKER and HIGH severity issues
- Check cognitive complexity
- Review React anti-patterns
- Check for deprecated MUI components
- Identify security issues (XSS, etc.)"
```

**What the agent does:**
- Analyzes TypeScript/React code
- Identifies code smells
- Flags deprecated patterns

---

#### Step 2: Fix Deprecated MUI Components
```
@typescript-react "Migrate deprecated MUI components to v6:
- Replace InputLabelProps with slotProps
- Replace InputProps with slotProps
- Update Grid to Grid2 where applicable
- Replace deprecated Typography variants
- Ensure responsive design maintained"
```

**What the agent does:**
- Updates MUI v5 → v6 patterns
- Maintains functionality
- Tests responsive behavior

**Handoff:** Click **[Write Unit Tests]** button

---

#### Step 3: Fix Complex Components
```
@sonarqube-quality "Refactor components with high cognitive complexity:
- Extract helper functions
- Simplify nested conditionals
- Use early returns
- Create custom hooks for complex logic"
```

**What the agent does:**
- Refactors complex components
- Extracts reusable logic
- Improves readability

---

#### Step 4: Update Component Tests
```
@typescript-testing "Update tests for refactored components:
- Fix broken tests due to refactoring
- Add tests for extracted helpers
- Test new custom hooks
- Maintain 80%+ coverage"
```

**Handoff:** Click **[Run Tests]** button

---

#### Step 5: Run Frontend Tests
```
cd smart_heating/frontend && npm test -- --coverage
Verify all tests pass
Check coverage meets 80%
```

---

#### Step 6: Check for Security Issues
```
@sonarqube-quality "Security review of frontend code:
- Check for XSS vulnerabilities
- Review data sanitization
- Check API token handling
- Verify input validation
- Review localStorage usage"
```

---

#### Step 7: Verify E2E Tests
```
@playwright-e2e "Review and update E2E tests after refactoring:
- Ensure tests still pass with refactored code
- Update selectors if needed
- Add tests for new patterns"
```

**Handoff:** Click **[Run E2E Tests]** button

---

#### Step 8: Run E2E Test Suite
```
cd tests/e2e && npm test
Verify 100% pass rate (109/109 tests)
Check for flaky tests
```

---

#### Step 9: Build and Deploy
```
bash scripts/deploy_test.sh
Verify build succeeds with no warnings
Test UI in browser (all viewports)
Test dark/light mode
```

---

#### Step 10: TypeScript Strict Mode Check
```
cd smart_heating/frontend && tsc --noEmit
Verify no TypeScript errors
Fix any type issues found
```

---

## Tips for Using Agents

### General Best Practices

1. **Start with Planning Agents**
   - Use agents to understand the problem first
   - Let them analyze existing code
   - Get implementation suggestions

2. **Follow Handoff Workflows**
   - Use handoff buttons for guided workflows
   - Don't skip testing steps
   - Always verify before deploying

3. **Test Coverage is Required**
   - Backend: 80% minimum (pytest)
   - Frontend: 80% minimum (Jest/Vitest)
   - E2E: Cover all user workflows (Playwright)

4. **Quality Checks Before Commits**
   - Run SonarQube analysis
   - Fix BLOCKER and HIGH issues
   - Address security vulnerabilities

5. **Deploy and Verify**
   - Use `bash scripts/deploy_test.sh`
   - Test in browser (clear cache!)
   - Run full test suite

### Agent Selection Guide

**When to use each agent:**

- `@home-assistant-integration` - HA Python code, coordinators, entities
- `@home-assistant-pytest` - Python unit tests, integration tests
- `@typescript-react` - React components, hooks, MUI patterns
- `@typescript-testing` - Jest/Vitest unit tests for React
- `@playwright-e2e` - E2E tests for user workflows
- `@sonarqube-quality` - Code quality, refactoring, security

### Workflow Patterns

**Feature Development:**
```
Implementation Agent → Testing Agent → Quality Agent → Deploy
```

**Bug Fixing:**
```
Testing Agent (failing test) → Implementation Agent (fix) → Quality Agent (review) → Deploy
```

**Quality Review:**
```
Quality Agent (analysis) → Implementation Agent (fixes) → Testing Agent (verify) → Deploy
```

---

## Quick Reference Commands

### Testing
```bash
# Python tests
bash tests/run_tests.sh

# Frontend unit tests
cd smart_heating/frontend && npm test

# Frontend tests with coverage
cd smart_heating/frontend && npm test -- --coverage

# E2E tests
cd tests/e2e && npm test

# E2E tests (headed mode for debugging)
cd tests/e2e && npm test -- --headed
```

### Deployment
```bash
# Deploy to test environment
bash scripts/deploy_test.sh

# Check HA logs
docker logs homeassistant-test -f

# Restart HA (if needed)
docker restart homeassistant-test
```

### Code Quality
```bash
# TypeScript type check
cd smart_heating/frontend && tsc --noEmit

# Build frontend
cd smart_heating/frontend && npm run build
```

---

**Version:** 1.0
**Last Updated:** 2025-12-13
**Maintained By:** Smart Heating Development Team
