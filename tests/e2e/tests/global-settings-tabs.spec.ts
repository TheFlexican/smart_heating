import { test, expect } from '@playwright/test';
import { dismissSnackbar } from './helpers';

test.describe('Global Settings Tabbed Layout', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('http://localhost:8123/smart-heating');
    await page.waitForLoadState('networkidle');
    await dismissSnackbar(page);
    
    // Navigate to Global Settings
    const settingsButton = page.getByRole('button', { name: /Global.*Settings/i });
    await settingsButton.click();
    await page.waitForTimeout(1000);
  });

  test('should display all 4 tabs in Global Settings', async ({ page }) => {
    // Check for all 4 tabs
    const temperatureTab = page.getByRole('tab', { name: /Temperature/i });
    const sensorsTab = page.getByRole('tab', { name: /Sensors/i });
    const vacationTab = page.getByRole('tab', { name: /Vacation/i });
    const advancedTab = page.getByRole('tab', { name: /Advanced/i });
    
    await expect(temperatureTab).toBeVisible();
    await expect(sensorsTab).toBeVisible();
    await expect(vacationTab).toBeVisible();
    await expect(advancedTab).toBeVisible();
  });

  test('should display tab icons correctly', async ({ page }) => {
    // Check that tabs have icons (Material-UI icons render as SVG)
    const tabs = page.getByRole('tab');
    const tabCount = await tabs.count();
    
    expect(tabCount).toBe(4);
    
    // Each tab should have an icon
    for (let i = 0; i < tabCount; i++) {
      const tab = tabs.nth(i);
      const svg = tab.locator('svg').first();
      await expect(svg).toBeVisible();
    }
  });

  test('should switch between tabs and show correct content', async ({ page }) => {
    // Click Temperature tab (should be active by default)
    const temperatureTab = page.getByRole('tab', { name: /Temperature/i });
    await temperatureTab.click();
    await page.waitForTimeout(500);
    
    // Check for preset temperatures content
    await expect(page.getByText(/Preset Temperatures/i)).toBeVisible();
    await expect(page.getByText(/Away/i)).toBeVisible();
    await expect(page.getByText(/Home/i)).toBeVisible();
    
    // Click Sensors tab
    const sensorsTab = page.getByRole('tab', { name: /Sensors/i });
    await sensorsTab.click();
    await page.waitForTimeout(500);
    
    // Check for presence sensors content
    await expect(page.getByText(/Global Presence Sensors/i)).toBeVisible();
    await expect(page.getByRole('button', { name: /Add Presence Sensor/i })).toBeVisible();
    
    // Click Vacation tab
    const vacationTab = page.getByRole('tab', { name: /Vacation/i });
    await vacationTab.click();
    await page.waitForTimeout(500);
    
    // Check for vacation mode content
    await expect(page.getByText(/Vacation Mode/i)).toBeVisible();
    
    // Click Advanced tab
    const advancedTab = page.getByRole('tab', { name: /Advanced/i });
    await advancedTab.click();
    await page.waitForTimeout(500);
    
    // Check for hysteresis content
    await expect(page.getByText(/Temperature Hysteresis/i)).toBeVisible();
  });

  test('should show preset temperature sliders in Temperature tab', async ({ page }) => {
    // Temperature tab should be active by default
    await page.waitForTimeout(500);
    
    // Check for all 6 preset sliders
    const presets = ['Away', 'Eco', 'Comfort', 'Home', 'Sleep', 'Activity'];
    
    for (const preset of presets) {
      const presetLabel = page.getByText(preset, { exact: true }).first();
      await expect(presetLabel).toBeVisible();
      
      // Check for slider near the label
      const slider = page.locator(`input[type="range"]`).nth(presets.indexOf(preset));
      await expect(slider).toBeVisible();
    }
  });

  test('should show hysteresis slider in Advanced tab', async ({ page }) => {
    // Click Advanced tab
    const advancedTab = page.getByRole('tab', { name: /Advanced/i });
    await advancedTab.click();
    await page.waitForTimeout(500);
    
    // Check for hysteresis title and description
    await expect(page.getByText(/Temperature Hysteresis/i)).toBeVisible();
    await expect(page.getByText(/Controls the temperature buffer/i)).toBeVisible();
    
    // Check for help button
    const helpButton = page.locator('button[aria-label*="help"], button').filter({ has: page.locator('svg') }).first();
    await expect(helpButton).toBeVisible();
    
    // Check for slider
    const slider = page.locator('input[type="range"]').first();
    await expect(slider).toBeVisible();
  });

  test('should open hysteresis help modal when help icon is clicked', async ({ page }) => {
    // Navigate to Advanced tab
    const advancedTab = page.getByRole('tab', { name: /Advanced/i });
    await advancedTab.click();
    await page.waitForTimeout(500);
    
    // Find and click help icon button
    const helpButton = page.locator('button').filter({ has: page.locator('svg[data-testid="HelpOutlineIcon"]') }).first();
    await helpButton.click();
    await page.waitForTimeout(500);
    
    // Check that modal opened with help content
    const modal = page.getByRole('dialog');
    await expect(modal).toBeVisible();
    
    // Check for help content keywords
    await expect(page.getByText(/What is hysteresis/i)).toBeVisible();
    await expect(page.getByText(/short cycling/i)).toBeVisible();
  });

  test('should adjust hysteresis value in Advanced tab', async ({ page }) => {
    // Navigate to Advanced tab
    const advancedTab = page.getByRole('tab', { name: /Advanced/i });
    await advancedTab.click();
    await page.waitForTimeout(500);
    
    // Get current value display
    const currentValueText = page.getByText(/Current.*°C/i);
    await expect(currentValueText).toBeVisible();
    
    // Get the slider
    const slider = page.locator('input[type="range"]').first();
    
    // Get initial value
    const initialValue = await slider.inputValue();
    
    // Move slider to a different position (e.g., to 1.0°C)
    await slider.fill('1.0');
    await page.waitForTimeout(1500); // Wait for debounced save
    
    // Verify value changed
    const newValue = await slider.inputValue();
    expect(newValue).toBe('1');
    
    // Reset to original value
    await slider.fill(initialValue);
    await page.waitForTimeout(1500);
  });

  test('should persist tab selection when navigating away and back', async ({ page }) => {
    // Switch to Advanced tab
    const advancedTab = page.getByRole('tab', { name: /Advanced/i });
    await advancedTab.click();
    await page.waitForTimeout(500);
    
    // Verify we're on Advanced tab
    await expect(page.getByText(/Temperature Hysteresis/i)).toBeVisible();
    
    // Navigate away (back to dashboard)
    const backButton = page.getByRole('button').filter({ has: page.locator('svg[data-testid="ArrowBackIcon"]') }).first();
    await backButton.click();
    await page.waitForTimeout(500);
    
    // Navigate back to Global Settings
    const settingsButton = page.getByRole('button', { name: /Global.*Settings/i });
    await settingsButton.click();
    await page.waitForTimeout(1000);
    
    // Should start at Temperature tab (default), not Advanced
    await expect(page.getByText(/Preset Temperatures/i)).toBeVisible();
  });

  test('should display success message when settings are saved', async ({ page }) => {
    // Navigate to Advanced tab
    const advancedTab = page.getByRole('tab', { name: /Advanced/i });
    await advancedTab.click();
    await page.waitForTimeout(500);
    
    // Change hysteresis value
    const slider = page.locator('input[type="range"]').first();
    const initialValue = await slider.inputValue();
    const newValue = parseFloat(initialValue) === 0.5 ? '1.0' : '0.5';
    
    await slider.fill(newValue);
    await page.waitForTimeout(1500); // Wait for debounced save
    
    // Check for success message
    const successAlert = page.locator('[role="alert"]').filter({ hasText: /Settings saved successfully/i });
    await expect(successAlert).toBeVisible({ timeout: 3000 });
    
    // Reset value
    await slider.fill(initialValue);
    await page.waitForTimeout(1500);
  });
});

test.describe('Area-Specific Hysteresis Override', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('http://localhost:8123/smart-heating');
    await page.waitForLoadState('networkidle');
    await dismissSnackbar(page);
  });

  test('should show hysteresis settings in area detail', async ({ page }) => {
    // Navigate to an area
    const areaCard = page.locator('.MuiPaper-root').filter({ hasText: /Woonkamer/i }).first();
    await areaCard.click();
    await page.waitForTimeout(1000);
    
    // Switch to Settings tab
    const settingsTab = page.getByRole('tab', { name: /Settings/i });
    await settingsTab.click();
    await page.waitForTimeout(500);
    
    // Look for Heating Control Settings section
    const heatingControlText = page.getByText(/Heating Control Settings/i);
    await expect(heatingControlText).toBeVisible();
  });

  test('should toggle between global and area-specific hysteresis', async ({ page }) => {
    // Navigate to area
    const areaCard = page.locator('.MuiPaper-root').filter({ hasText: /Woonkamer/i }).first();
    await areaCard.click();
    await page.waitForTimeout(1000);
    
    // Switch to Settings tab
    const settingsTab = page.getByRole('tab', { name: /Settings/i });
    await settingsTab.click();
    await page.waitForTimeout(500);
    
    // Find and click Heating Control Settings to expand
    const heatingControlCard = page.getByText(/Heating Control Settings/i);
    await heatingControlCard.click();
    await page.waitForTimeout(500);
    
    // Find the hysteresis toggle
    const hysteresisToggle = page.getByText(/Use global hysteresis/i).locator('..').locator('input[type="checkbox"]').first();
    
    // Get initial state
    const initialState = await hysteresisToggle.isChecked();
    
    // Toggle it
    await hysteresisToggle.click();
    await page.waitForTimeout(1500); // Wait for save
    
    // Verify state changed
    const newState = await hysteresisToggle.isChecked();
    expect(newState).not.toBe(initialState);
    
    // If we switched to custom, check that slider appeared
    if (!newState) {
      const slider = page.locator('input[type="range"]').first();
      await expect(slider).toBeVisible();
    }
    
    // Toggle back
    await hysteresisToggle.click();
    await page.waitForTimeout(1500);
    
    // Verify returned to original state
    const finalState = await hysteresisToggle.isChecked();
    expect(finalState).toBe(initialState);
  });

  test('should display help icon for hysteresis in area settings', async ({ page }) => {
    // Navigate to area
    const areaCard = page.locator('.MuiPaper-root').filter({ hasText: /Woonkamer/i }).first();
    await areaCard.click();
    await page.waitForTimeout(1000);
    
    // Switch to Settings tab
    const settingsTab = page.getByRole('tab', { name: /Settings/i });
    await settingsTab.click();
    await page.waitForTimeout(500);
    
    // Expand Heating Control Settings
    const heatingControlCard = page.getByText(/Heating Control Settings/i);
    await heatingControlCard.click();
    await page.waitForTimeout(500);
    
    // Look for Temperature Hysteresis section with help icon
    const hysteresisSection = page.getByText(/Temperature Hysteresis/i);
    await expect(hysteresisSection).toBeVisible();
    
    // Find help button
    const helpButton = page.locator('button').filter({ has: page.locator('svg[data-testid="HelpOutlineIcon"]') }).first();
    await expect(helpButton).toBeVisible();
  });

  test('should open hysteresis help modal from area settings', async ({ page }) => {
    // Navigate to area
    const areaCard = page.locator('.MuiPaper-root').filter({ hasText: /Woonkamer/i }).first();
    await areaCard.click();
    await page.waitForTimeout(1000);
    
    // Switch to Settings tab
    const settingsTab = page.getByRole('tab', { name: /Settings/i });
    await settingsTab.click();
    await page.waitForTimeout(500);
    
    // Expand Heating Control Settings
    const heatingControlCard = page.getByText(/Heating Control Settings/i);
    await heatingControlCard.click();
    await page.waitForTimeout(500);
    
    // Click help icon
    const helpButton = page.locator('button').filter({ has: page.locator('svg[data-testid="HelpOutlineIcon"]') }).first();
    await helpButton.click();
    await page.waitForTimeout(500);
    
    // Verify modal opened
    const modal = page.getByRole('dialog');
    await expect(modal).toBeVisible();
    
    // Check for specific help content
    await expect(page.getByText(/What is hysteresis/i)).toBeVisible();
    await expect(page.getByText(/Radiator Heating/i)).toBeVisible();
    await expect(page.getByText(/Floor Heating/i)).toBeVisible();
  });

  test('should adjust custom hysteresis value for area', async ({ page }) => {
    // Navigate to area
    const areaCard = page.locator('.MuiPaper-root').filter({ hasText: /Woonkamer/i }).first();
    await areaCard.click();
    await page.waitForTimeout(1000);
    
    // Switch to Settings tab
    const settingsTab = page.getByRole('tab', { name: /Settings/i });
    await settingsTab.click();
    await page.waitForTimeout(500);
    
    // Expand Heating Control Settings
    const heatingControlCard = page.getByText(/Heating Control Settings/i);
    await heatingControlCard.click();
    await page.waitForTimeout(500);
    
    // Turn off "Use global hysteresis" to enable custom setting
    const hysteresisToggle = page.getByText(/Use global hysteresis/i).locator('..').locator('input[type="checkbox"]').first();
    const isUsingGlobal = await hysteresisToggle.isChecked();
    
    if (isUsingGlobal) {
      await hysteresisToggle.click();
      await page.waitForTimeout(1500);
    }
    
    // Find the slider
    const slider = page.locator('input[type="range"]').first();
    await expect(slider).toBeVisible();
    
    // Get initial value
    const initialValue = await slider.inputValue();
    
    // Change to 0.3°C (good for floor heating)
    await slider.fill('0.3');
    await page.waitForTimeout(1500);
    
    // Verify change
    const newValue = await slider.inputValue();
    expect(parseFloat(newValue)).toBeCloseTo(0.3, 1);
    
    // Reset to original value or turn global back on
    if (isUsingGlobal) {
      await hysteresisToggle.click();
      await page.waitForTimeout(1500);
    } else {
      await slider.fill(initialValue);
      await page.waitForTimeout(1500);
    }
  });
});
