# Vacation Mode E2E Test Guide

## Overview

This guide covers the E2E tests for the **Vacation Mode** feature introduced in v0.6.0. Vacation Mode allows users to set all areas to a specific preset (Away, Eco, or Sleep) for extended periods with frost protection.

## Test File

**Location:** `tests/e2e/tests/vacation-mode.spec.ts`  
**Test Count:** 9 tests  
**Feature Version:** v0.6.0

## Test Cases

### 1. Display vacation mode settings in global settings page
**Purpose:** Verify vacation mode UI is accessible and visible  
**Steps:**
1. Navigate to global settings (click settings icon)
2. Verify vacation mode section header is visible
3. Verify description text is present

**Expected Result:** Vacation mode section displays with proper header and description

---

### 2. Enable vacation mode with valid configuration
**Purpose:** Test the complete flow of enabling vacation mode  
**Steps:**
1. Navigate to global settings
2. Disable vacation mode if already enabled
3. Configure vacation mode settings:
   - Verify preset mode selector (defaults to "away")
   - Verify frost protection toggle
   - Verify auto-disable toggle
4. Click "Enable Vacation Mode" button
5. Wait for enable to complete

**Expected Result:** 
- "Vacation mode is ACTIVE" alert appears
- "Disable Vacation Mode" button becomes visible
- All form fields become disabled

---

### 3. Display vacation mode banner on dashboard when active
**Purpose:** Verify dashboard banner shows when vacation mode is active  
**Steps:**
1. Enable vacation mode via settings
2. Navigate to main dashboard
3. Check for vacation mode banner

**Expected Result:**
- Banner displays "🏖️ Vacation Mode Active"
- Shows current preset mode (e.g., "away")
- Shows end date if configured

---

### 4. Disable vacation mode from banner
**Purpose:** Test quick disable from dashboard banner  
**Steps:**
1. Ensure vacation mode is active
2. Navigate to dashboard
3. Click "Disable" button in banner
4. Wait for disable to complete

**Expected Result:**
- Banner disappears from dashboard
- Vacation mode is no longer active

---

### 5. Disable vacation mode from settings
**Purpose:** Test disable from settings page  
**Steps:**
1. Ensure vacation mode is active
2. Navigate to settings
3. Click "Disable Vacation Mode" button
4. Wait for disable to complete

**Expected Result:**
- "Vacation mode is ACTIVE" alert disappears
- "Enable Vacation Mode" button becomes visible
- All form fields become enabled

---

### 6. Show frost protection minimum temperature field when enabled
**Purpose:** Verify conditional rendering of frost protection settings  
**Steps:**
1. Navigate to settings
2. Ensure vacation mode is disabled
3. Toggle frost protection on (if not already)
4. Look for minimum temperature field

**Expected Result:**
- "Minimum Temperature (°C)" field appears when frost protection is enabled
- Field has proper min/max validation (5-15°C)

---

### 7. Preserve vacation mode settings across page reloads
**Purpose:** Test state persistence  
**Steps:**
1. Enable vacation mode
2. Reload the page
3. Navigate to settings
4. Verify vacation mode is still active

**Expected Result:**
- Vacation mode remains active after reload
- "Vacation mode is ACTIVE" alert still visible
- Settings preserved

---

### 8. Show different preset mode options
**Purpose:** Verify preset mode dropdown options  
**Steps:**
1. Navigate to settings
2. Ensure vacation mode is disabled
3. Click preset mode dropdown
4. Verify available options

**Expected Result:**
- Dropdown shows "Away", "Eco", and "Sleep" options
- All options are selectable

---

## Running the Tests

### Single Test File
```bash
cd tests/e2e
npm test vacation-mode.spec.ts
```

### With UI (Headed Mode)
```bash
npm test vacation-mode.spec.ts -- --headed
```

### Specific Test
```bash
npm test vacation-mode.spec.ts -- --grep "enable vacation mode"
```

### Debug Mode
```bash
npm test vacation-mode.spec.ts -- --debug
```

## Known Issues & Notes

### Date Picker Handling
- Material-UI date pickers may require special handling
- Current tests verify the date picker components exist but don't extensively test date selection
- Future improvement: Add comprehensive date selection tests

### Timing Considerations
- Tests use `waitForTimeout(2000)` after enable/disable operations
- This may need adjustment based on backend response time
- WebSocket updates should be instant but API calls may vary

### State Management
- Tests ensure clean state by disabling vacation mode before testing enable
- Each test should be independent and not rely on previous test state

### Person Entity Integration
- Current implementation includes person entity array but doesn't populate it in tests
- Future enhancement: Add tests for auto-disable with person entities

## Test Data Requirements

### Minimal Setup
- Home Assistant instance running
- Smart Heating integration installed
- At least one area configured
- Access to global settings page

### Optional Setup
- Person entities for auto-disable testing
- Multiple areas for comprehensive testing

## Expected Behavior

### When Vacation Mode is Active
1. All areas switch to the selected preset mode
2. Banner appears on dashboard
3. Frost protection minimum temperature applies if enabled
4. Settings are persisted to storage
5. WebSocket event is broadcast

### When Vacation Mode is Disabled
1. Banner disappears from dashboard
2. Areas return to normal scheduling
3. Enable button becomes available
4. Settings remain available for next vacation

## Maintenance

### When UI Changes
Update selectors in the test file if:
- Button text changes
- Alert messages change
- Component structure changes

### When API Changes
Update API expectations if:
- Endpoint URLs change
- Response structure changes
- New fields are added to vacation mode config

## Integration with Other Features

### Climate Controller
- Vacation mode overrides area preset modes
- Climate controller checks `vacation_manager.is_active()`
- Frost protection applies on top of preset temperatures

### Global Settings
- Vacation mode is displayed before preset settings
- Settings page should load vacation mode state on mount
- Changes are saved via POST to `/api/smart_heating/vacation_mode`

### WebSocket Updates
- Vacation mode changes trigger `smart_heating_vacation_mode_changed` event
- Frontend should react to these events and update UI
- Banner component refreshes every 30 seconds as fallback

## Troubleshooting

### Tests Timing Out
- Increase `waitForTimeout` values
- Check if Home Assistant is responsive
- Verify API endpoints are working

### Banner Not Appearing
- Check if vacation mode is actually enabled via API
- Verify banner component is imported in App.tsx
- Check browser console for errors

### Settings Not Persisting
- Verify storage is working in Home Assistant
- Check `.storage/smart_heating/vacation_mode.json`
- Verify API POST is successful

## Future Enhancements

1. **Date Selection Tests**: Comprehensive tests for date picker functionality
2. **Person Entity Tests**: Test auto-disable when person arrives home
3. **Multi-Preset Tests**: Test switching between different preset modes
4. **Duration Tests**: Test various vacation durations
5. **Validation Tests**: Test error handling for invalid dates
6. **API Tests**: Direct API testing without UI
7. **Performance Tests**: Measure impact on large installations
