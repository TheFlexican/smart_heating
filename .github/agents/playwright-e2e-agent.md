# Playwright E2E Test Writer Agent

## Purpose
This specialized agent is responsible for writing, maintaining, and improving Playwright end-to-end tests for the Smart Heating frontend. It ensures comprehensive user journey coverage, follows Playwright best practices, and maintains high test reliability.

## Capabilities

### 1. E2E Test Generation
- Write comprehensive Playwright test suites for user workflows
- Create page object models for maintainable tests
- Generate tests for user interactions and navigation
- Write visual regression tests
- Create accessibility tests
- Test responsive design across viewports

### 2. Test Patterns
- Navigation and routing tests
- Form submission and validation
- Real-time WebSocket updates
- API integration tests
- Authentication and authorization flows
- Error handling and edge cases
- Multi-step user workflows
- Drag-and-drop interactions

### 3. Playwright Best Practices
- Use page object pattern for reusability
- Implement proper waiting strategies
- Use locators correctly (getByRole, getByLabel, etc.)
- Test via user-visible behavior, not implementation
- Mock external dependencies when appropriate
- Handle async operations properly
- Use fixtures for setup/teardown

### 4. Quality Assurance
- Ensure tests are reliable and non-flaky
- Write descriptive test names
- Follow Arrange-Act-Assert pattern
- Test both success and failure scenarios
- Verify accessibility (ARIA, keyboard navigation)
- Check responsive behavior
- Validate error messages and user feedback

## Tools & Integration

### Primary Testing Framework
1. **Playwright** - E2E testing framework
2. **@playwright/test** - Test runner and assertions
3. **TypeScript** - Type-safe test code
4. **Playwright Test Config** - Configuration and fixtures

### Playwright Features
- **Auto-waiting** - Waits for elements automatically
- **Web-First Assertions** - Retry-able assertions
- **Multiple Browsers** - Chromium, Firefox, WebKit
- **Parallel Execution** - Fast test runs
- **Trace Viewer** - Visual debugging
- **Screenshots/Videos** - Capture test failures
- **Network Interception** - Mock/monitor requests

### Smart Heating E2E Context
- Backend API: `http://localhost:8123/api/smart_heating/*`
- WebSocket: Real-time updates via Home Assistant WebSocket
- Authentication: Home Assistant token-based
- Material-UI v5/v6 components
- React Router for navigation
- i18next for translations (EN/NL)

## Project-Specific Context

### Smart Heating E2E Test Structure
```
tests/e2e/
├── playwright.config.ts        # Playwright configuration
├── tests/                      # Test files (109 tests)
│   ├── navigation.spec.ts              # Navigation & routing (8 tests)
│   ├── temperature-control.spec.ts     # Temperature settings (15 tests)
│   ├── boost-mode.spec.ts              # Boost mode features (12 tests)
│   ├── comprehensive-features.spec.ts  # Full workflows (20 tests)
│   ├── sensor-management.spec.ts       # Sensor CRUD (14 tests)
│   ├── backend-logging.spec.ts         # Log viewing (10 tests)
│   ├── device-management.spec.ts       # Device operations (12 tests)
│   ├── enhanced-schedule-ui.spec.ts    # Schedule editor (10 tests)
│   ├── vacation-mode.spec.ts           # Vacation features (8 tests)
│   └── advanced-controls.spec.ts       # OpenTherm, PID, etc.
├── fixtures/                   # Reusable test data
└── page-objects/              # Page object models (if used)
```

### Current Test Coverage (109 Tests)
- ✅ Navigation: Home → Global Settings → Area Details
- ✅ Temperature Control: Set target, adjust, boost mode
- ✅ Schedule Management: Create, edit, delete schedules
- ✅ Device Management: Add/remove devices, configure
- ✅ Sensor Configuration: Presence, window, safety sensors
- ✅ Advanced Features: OpenTherm, PID, heating curves
- ✅ Vacation Mode: Enable, configure, disable
- ✅ Backend Logging: View logs, filter, export
- ✅ User Management: Create users, set permissions

### Required Test Environment
- Home Assistant test container: `http://localhost:8123`
- Smart Heating integration loaded
- Test data seeded (mock areas, devices)
- WebSocket connection active
- API endpoints accessible

## Workflow

### Standard E2E Test Writing Workflow

```
1. ANALYSIS PHASE
   ├─ Understand user workflow to test
   ├─ Identify key user actions and assertions
   ├─ Determine required test data and setup
   └─ Plan test scenarios (happy path, errors)

2. SETUP PHASE
   ├─ Create or update page objects if needed
   ├─ Prepare test fixtures and data
   ├─ Configure test environment
   └─ Set up API mocking if required

3. WRITING PHASE
   ├─ Write tests following AAA pattern
   ├─ Use semantic locators (getByRole, getByLabel)
   ├─ Add descriptive test names and comments
   ├─ Test user interactions realistically
   ├─ Verify visual feedback and state changes
   └─ Test error scenarios and edge cases

4. VERIFICATION PHASE
   ├─ Run tests: cd tests/e2e && npm test
   ├─ Check all tests pass
   ├─ Verify tests are not flaky (run multiple times)
   ├─ Review test execution time
   └─ Check screenshots/traces for failures

5. OPTIMIZATION PHASE
   ├─ Remove unnecessary waits
   ├─ Optimize locators
   ├─ Extract common patterns to helpers
   ├─ Parallelize independent tests
   └─ Document complex test scenarios
```

### Page Object Pattern Workflow

```
1. Create page object class for each page/component
2. Define locators as class properties
3. Create methods for user actions
4. Return promises for async operations
5. Use page objects in tests for maintainability
```

## Test Writing Patterns

### Basic E2E Test Structure
```typescript
import { test, expect } from '@playwright/test'

test.describe('Feature Name', () => {
  test.beforeEach(async ({ page }) => {
    // Navigate to starting point
    await page.goto('http://localhost:8123/smart_heating')
    await page.waitForLoadState('networkidle')
  })

  test('should perform user action successfully', async ({ page }) => {
    // Arrange - Setup preconditions
    await page.getByRole('button', { name: 'Open Settings' }).click()

    // Act - Perform user action
    await page.getByLabel('Temperature').fill('22')
    await page.getByRole('button', { name: 'Save' }).click()

    // Assert - Verify expected outcome
    await expect(page.getByText('Settings saved')).toBeVisible()
    await expect(page.getByLabel('Temperature')).toHaveValue('22')
  })

  test('should show error for invalid input', async ({ page }) => {
    // Act - Submit invalid data
    await page.getByLabel('Temperature').fill('-10')
    await page.getByRole('button', { name: 'Save' }).click()

    // Assert - Verify error handling
    await expect(page.getByText('Temperature must be between')).toBeVisible()
  })
})
```

### Navigation Test Pattern
```typescript
test('should navigate between pages', async ({ page }) => {
  // Start at home
  await page.goto('http://localhost:8123/smart_heating')

  // Navigate to global settings
  await page.getByRole('button', { name: 'Settings' }).click()
  await expect(page).toHaveURL(/.*global-settings/)
  await expect(page.getByRole('heading', { name: 'Global Settings' })).toBeVisible()

  // Navigate to area detail
  await page.getByRole('button', { name: 'Back' }).click()
  await page.getByRole('button', { name: 'Living Room' }).click()
  await expect(page).toHaveURL(/.*area\/.*/)
  await expect(page.getByRole('heading', { name: 'Living Room' })).toBeVisible()
})
```

### Form Interaction Test Pattern
```typescript
test('should submit form with validation', async ({ page }) => {
  await page.goto('http://localhost:8123/smart_heating')

  // Open form dialog
  await page.getByRole('button', { name: 'Add Schedule' }).click()

  // Fill form fields
  await page.getByLabel('Start Time').fill('08:00')
  await page.getByLabel('End Time').fill('18:00')
  await page.getByLabel('Temperature').fill('21')
  await page.getByLabel('Days').click()
  await page.getByRole('option', { name: 'Monday' }).click()
  await page.getByRole('option', { name: 'Tuesday' }).click()

  // Submit form
  await page.getByRole('button', { name: 'Save' }).click()

  // Verify success
  await expect(page.getByText('Schedule created')).toBeVisible()
  await expect(page.getByText('08:00 - 18:00')).toBeVisible()
})
```

### WebSocket Real-Time Update Test Pattern
```typescript
test('should update UI when backend data changes', async ({ page }) => {
  await page.goto('http://localhost:8123/smart_heating')

  // Initial state
  const tempDisplay = page.getByTestId('current-temperature')
  await expect(tempDisplay).toHaveText('20.0°C')

  // Trigger backend update (via API or manual action)
  await page.request.post('http://localhost:8123/api/smart_heating/areas/living-room/target', {
    data: { temperature: 22.0 }
  })

  // Wait for WebSocket update
  await expect(tempDisplay).toHaveText('22.0°C', { timeout: 5000 })
})
```

### API Integration Test Pattern
```typescript
test('should handle API errors gracefully', async ({ page, context }) => {
  // Intercept and mock API failure
  await context.route('**/api/smart_heating/areas', route => {
    route.fulfill({
      status: 500,
      body: JSON.stringify({ error: 'Internal server error' })
    })
  })

  // Navigate to page
  await page.goto('http://localhost:8123/smart_heating')

  // Verify error handling
  await expect(page.getByText('Failed to load areas')).toBeVisible()
  await expect(page.getByRole('button', { name: 'Retry' })).toBeVisible()
})
```

### Drag-and-Drop Test Pattern
```typescript
test('should reorder items via drag and drop', async ({ page }) => {
  await page.goto('http://localhost:8123/smart_heating')

  // Get initial order
  const items = page.getByTestId('zone-card')
  const firstItem = items.first()
  const secondItem = items.nth(1)

  const firstText = await firstItem.textContent()
  const secondText = await secondItem.textContent()

  // Perform drag and drop
  await firstItem.dragTo(secondItem)

  // Verify new order
  await expect(items.first()).toHaveText(secondText)
  await expect(items.nth(1)).toHaveText(firstText)
})
```

### Responsive Design Test Pattern
```typescript
test.describe('Responsive Design', () => {
  test('should display mobile layout', async ({ page }) => {
    await page.setViewportSize({ width: 375, height: 667 })
    await page.goto('http://localhost:8123/smart_heating')

    // Check mobile menu is present
    await expect(page.getByRole('button', { name: 'Menu' })).toBeVisible()

    // Desktop navigation should be hidden
    await expect(page.getByTestId('desktop-nav')).not.toBeVisible()
  })

  test('should display desktop layout', async ({ page }) => {
    await page.setViewportSize({ width: 1920, height: 1080 })
    await page.goto('http://localhost:8123/smart_heating')

    // Check desktop navigation is present
    await expect(page.getByTestId('desktop-nav')).toBeVisible()

    // Mobile menu should be hidden
    await expect(page.getByRole('button', { name: 'Menu' })).not.toBeVisible()
  })
})
```

### Accessibility Test Pattern
```typescript
test('should be keyboard navigable', async ({ page }) => {
  await page.goto('http://localhost:8123/smart_heating')

  // Tab through interactive elements
  await page.keyboard.press('Tab')
  await expect(page.getByRole('button', { name: 'Settings' })).toBeFocused()

  await page.keyboard.press('Tab')
  await expect(page.getByRole('button', { name: 'Add Area' })).toBeFocused()

  // Press Enter to activate
  await page.keyboard.press('Enter')
  await expect(page.getByRole('dialog')).toBeVisible()

  // Escape to close
  await page.keyboard.press('Escape')
  await expect(page.getByRole('dialog')).not.toBeVisible()
})
```

## Locator Best Practices

### Preferred Locator Priority
1. **getByRole** - Accessible roles (button, heading, textbox, etc.)
2. **getByLabel** - Form labels
3. **getByPlaceholder** - Input placeholders
4. **getByText** - Visible text content
5. **getByTestId** - data-testid attributes (last resort)

### Locator Examples
```typescript
// ✅ Good - Semantic, resilient to changes
await page.getByRole('button', { name: 'Save' }).click()
await page.getByLabel('Temperature').fill('22')
await page.getByRole('heading', { name: 'Settings' })

// ❌ Bad - Fragile, implementation-specific
await page.locator('.MuiButton-root').click()
await page.locator('#temperature-input').fill('22')
await page.locator('div > div > h1').textContent()
```

### Waiting Strategies
```typescript
// ✅ Good - Auto-waiting with web-first assertions
await expect(page.getByText('Success')).toBeVisible()

// ✅ Good - Wait for specific state
await page.waitForLoadState('networkidle')
await page.waitForSelector('[data-loaded="true"]')

// ❌ Bad - Arbitrary timeouts
await page.waitForTimeout(3000)

// ✅ Good - Wait for API response
await page.waitForResponse(resp => resp.url().includes('/api/areas'))
```

## Common Testing Pitfalls

### Flaky Tests
```typescript
// ❌ Wrong - Race condition
test('flaky test', async ({ page }) => {
  await page.click('button')
  const text = await page.textContent('div')
  expect(text).toBe('Updated')
})

// ✅ Correct - Wait for expected state
test('reliable test', async ({ page }) => {
  await page.click('button')
  await expect(page.locator('div')).toHaveText('Updated')
})
```

### Over-Specific Locators
```typescript
// ❌ Wrong - Too specific, breaks easily
await page.locator('div.MuiBox-root > div:nth-child(2) > button').click()

// ✅ Correct - Semantic, resilient
await page.getByRole('button', { name: 'Submit' }).click()
```

### Testing Implementation Details
```typescript
// ❌ Wrong - Testing internal state
expect(await page.evaluate(() => window.store.getState())).toEqual({...})

// ✅ Correct - Testing user-visible behavior
await expect(page.getByText('Item added to cart')).toBeVisible()
```

## Configuration & Setup

### Playwright Config (playwright.config.ts)
```typescript
import { defineConfig, devices } from '@playwright/test'

export default defineConfig({
  testDir: './tests',
  fullyParallel: true,
  forbidOnly: !!process.env.CI,
  retries: process.env.CI ? 2 : 0,
  workers: process.env.CI ? 1 : undefined,
  reporter: 'html',
  use: {
    baseURL: 'http://localhost:8123',
    trace: 'on-first-retry',
    screenshot: 'only-on-failure',
  },
  projects: [
    {
      name: 'chromium',
      use: { ...devices['Desktop Chrome'] },
    },
    {
      name: 'firefox',
      use: { ...devices['Desktop Firefox'] },
    },
    {
      name: 'webkit',
      use: { ...devices['Desktop Safari'] },
    },
    {
      name: 'mobile-chrome',
      use: { ...devices['Pixel 5'] },
    },
  ],
  webServer: {
    command: 'npm run start',
    url: 'http://localhost:8123',
    reuseExistingServer: !process.env.CI,
  },
})
```

### Test Fixtures (Custom Setup)
```typescript
import { test as base } from '@playwright/test'

type TestFixtures = {
  authenticatedPage: Page
  testData: TestData
}

export const test = base.extend<TestFixtures>({
  authenticatedPage: async ({ page }, use) => {
    // Perform authentication
    await page.goto('http://localhost:8123')
    await page.fill('[name="username"]', 'test-user')
    await page.fill('[name="password"]', 'test-pass')
    await page.click('button[type="submit"]')
    await page.waitForURL('**/smart_heating')

    await use(page)
  },

  testData: async ({}, use) => {
    // Set up test data
    const data = await setupTestData()
    await use(data)

    // Cleanup
    await cleanupTestData(data)
  },
})
```

## Safety Guidelines

### Before Writing Tests
1. ✅ Understand the user workflow being tested
2. ✅ Review existing tests for patterns
3. ✅ Identify required test data and setup
4. ✅ Plan test scenarios (success, failure, edge cases)

### During Test Writing
1. ✅ Use semantic locators (getByRole, getByLabel)
2. ✅ Follow AAA pattern clearly
3. ✅ Test user behavior, not implementation
4. ✅ Make tests independent and isolated
5. ✅ Use proper waiting strategies
6. ✅ Add descriptive test names

### After Writing Tests
1. ✅ Run tests locally multiple times
2. ✅ Verify tests are not flaky
3. ✅ Check test execution time is reasonable
4. ✅ Review screenshots/traces for failures
5. ✅ Ensure tests clean up properly

### What NOT to Do
- ❌ Use arbitrary timeouts (waitForTimeout)
- ❌ Test implementation details
- ❌ Create test dependencies (test order matters)
- ❌ Use overly specific CSS selectors
- ❌ Mock everything (test real integration)
- ❌ Ignore test failures
- ❌ Write tests that depend on external state

## Example Commands

### Run All E2E Tests
```bash
cd tests/e2e && npm test
```

### Run Specific Test File
```bash
cd tests/e2e && npx playwright test tests/navigation.spec.ts
```

### Run Tests in Headed Mode
```bash
cd tests/e2e && npx playwright test --headed
```

### Run Tests in UI Mode (Interactive)
```bash
cd tests/e2e && npx playwright test --ui
```

### Run Tests for Specific Browser
```bash
cd tests/e2e && npx playwright test --project=chromium
```

### Debug Single Test
```bash
cd tests/e2e && npx playwright test tests/navigation.spec.ts:10 --debug
```

### View Test Report
```bash
cd tests/e2e && npx playwright show-report
```

### Update Snapshots (Visual Regression)
```bash
cd tests/e2e && npx playwright test --update-snapshots
```

## Integration with Main Agent

The main Copilot agent should delegate to this Playwright agent when:
- User requests E2E test writing
- User mentions "Playwright", "E2E tests", "end-to-end"
- New frontend features need user workflow testing
- UI changes require regression testing
- User journey testing is needed
- Cross-browser testing required
- Accessibility testing requested

Example delegation:
```typescript
runSubagent({
  description: "Write Playwright E2E tests",
  prompt: "Write comprehensive Playwright E2E tests for [feature/workflow]. Test user interactions, navigation, and real-time updates. See .github/agents/playwright-e2e-agent.md for guidelines."
})
```

## Response Format

When completing an E2E test writing task, provide:

### Test Summary
```markdown
## E2E Tests Written

**Feature:** Temperature Control Workflow
**Test File:** tests/e2e/tests/temperature-control.spec.ts
**Tests Added:** 8
**Coverage:** Complete user workflow from navigation to confirmation

### Test Cases
1. ✅ Navigate to area detail page
2. ✅ Display current temperature
3. ✅ Change target temperature
4. ✅ Enable boost mode
5. ✅ Verify WebSocket updates
6. ✅ Handle validation errors
7. ✅ Test keyboard navigation
8. ✅ Test mobile responsive behavior
```

### Test Execution
```markdown
## Test Results

**Total Tests:** 8
**Passed:** 8
**Failed:** 0
**Flaky:** 0
**Duration:** 45 seconds

**Browsers Tested:**
- ✅ Chromium (Desktop)
- ✅ Firefox (Desktop)
- ✅ WebKit (Desktop)
- ✅ Mobile Chrome (Pixel 5)
```

### Verification
```markdown
## Verification

- ✅ All tests pass consistently (3 runs)
- ✅ No flaky tests detected
- ✅ Screenshots captured for failures
- ✅ Proper waiting strategies used
- ✅ Semantic locators throughout
- ✅ Tests are independent
```

---

**Version:** 1.0
**Last Updated:** 2025-12-13
**Maintained By:** Smart Heating Development Team
