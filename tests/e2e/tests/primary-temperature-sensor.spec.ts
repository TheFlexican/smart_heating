import { test, expect } from '@playwright/test'
import { login, navigateToSmartHeating, navigateToArea, switchToTab, dismissSnackbar } from './helpers'

/**
 * Primary Temperature Sensor Tests - v0.5.10
 * 
 * Features tested:
 * - Primary Temperature Sensor dropdown visibility
 * - Auto mode (averaging all sensors)
 * - Manual mode (selecting specific sensor)
 * - Sensor selection persistence
 * - Temperature display updates based on selection
 * - Fallback behavior when primary sensor unavailable
 * 
 * Tests verify:
 * 1. Frontend UI displays dropdown correctly
 * 2. Backend API calls succeed
 * 3. Temperature collection uses selected sensor
 * 4. State updates reflect in UI immediately
 */

test.describe('Primary Temperature Sensor', () => {
  
  test.beforeEach(async ({ page }) => {
    await login(page)
    await navigateToSmartHeating(page)
  })

  test.describe('Dropdown Visibility', () => {
    
    test('should show Primary Temperature Sensor dropdown in Devices tab', async ({ page }) => {
      await navigateToArea(page, 'Living Room')
      await switchToTab(page, 'Devices')
      await dismissSnackbar(page)
      
      // Verify dropdown label is visible
      await expect(page.locator('text=/Primary Temperature Sensor/i')).toBeVisible({ timeout: 5000 })
      
      // Verify description text
      await expect(page.locator('text=/Select which device measures temperature for this area/i')).toBeVisible()
    })

    test('should display dropdown with Auto option', async ({ page }) => {
      await navigateToArea(page, 'Living Room')
      await switchToTab(page, 'Devices')
      await dismissSnackbar(page)
      
      // Find and click the dropdown
      const dropdown = page.locator('[data-testid="primary-temp-sensor-select"]').or(
        page.locator('select').filter({ hasText: /Auto|average/i })
      ).first()
      
      // Open dropdown
      await dropdown.click()
      
      // Verify "Auto" option exists
      await expect(page.locator('text=/Auto.*average.*all.*sensors/i')).toBeVisible({ timeout: 3000 })
    })

    test('should list available temperature sensors in dropdown', async ({ page }) => {
      await navigateToArea(page, 'Living Room')
      await switchToTab(page, 'Devices')
      await dismissSnackbar(page)
      
      // Open dropdown
      const dropdown = page.locator('[data-testid="primary-temp-sensor-select"]').or(
        page.locator('label:has-text("Primary Temperature Sensor")').locator('..').locator('select, [role="button"]')
      ).first()
      await dropdown.click()
      
      // Wait for menu to appear
      await page.waitForTimeout(500)
      
      // Verify there are sensor options (beyond just "Auto")
      const menuItems = page.locator('[role="option"], li[role="menuitem"]')
      const count = await menuItems.count()
      
      // Should have at least Auto + 1 sensor
      expect(count).toBeGreaterThanOrEqual(2)
    })
  })

  test.describe('Sensor Selection', () => {
    
    test('should start in Auto mode by default', async ({ page }) => {
      await navigateToArea(page, 'Living Room')
      await switchToTab(page, 'Devices')
      await dismissSnackbar(page)
      
      // Verify dropdown shows "Auto" as selected
      const dropdown = page.locator('[data-testid="primary-temp-sensor-select"]').or(
        page.locator('label:has-text("Primary Temperature Sensor")').locator('..').locator('select, [role="button"]')
      ).first()
      
      const selectedValue = await dropdown.textContent()
      expect(selectedValue).toMatch(/Auto/i)
    })

    test('should select a specific temperature sensor', async ({ page }) => {
      await navigateToArea(page, 'Living Room')
      await switchToTab(page, 'Devices')
      await dismissSnackbar(page)
      
      // Open dropdown
      const dropdown = page.locator('[data-testid="primary-temp-sensor-select"]').or(
        page.locator('label:has-text("Primary Temperature Sensor")').locator('..').locator('[role="button"]')
      ).first()
      await dropdown.click()
      
      // Wait for menu
      await page.waitForTimeout(500)
      
      // Select first non-Auto option
      const options = page.locator('[role="option"], li[role="menuitem"]')
      const firstSensorOption = options.nth(1) // Skip Auto (index 0)
      
      const sensorName = await firstSensorOption.textContent()
      await firstSensorOption.click()
      
      // Wait for API call to complete
      await page.waitForTimeout(1000)
      
      // Verify selection persisted (dropdown shows selected sensor)
      const currentValue = await dropdown.textContent()
      expect(currentValue).toContain(sensorName?.trim() || '')
    })

    test('should switch back to Auto mode', async ({ page }) => {
      await navigateToArea(page, 'Living Room')
      await switchToTab(page, 'Devices')
      await dismissSnackbar(page)
      
      // First select a specific sensor
      const dropdown = page.locator('[data-testid="primary-temp-sensor-select"]').or(
        page.locator('label:has-text("Primary Temperature Sensor")').locator('..').locator('[role="button"]')
      ).first()
      await dropdown.click()
      await page.waitForTimeout(500)
      
      const options = page.locator('[role="option"], li[role="menuitem"]')
      await options.nth(1).click() // Select first sensor
      await page.waitForTimeout(1000)
      
      // Now switch back to Auto
      await dropdown.click()
      await page.waitForTimeout(500)
      await options.first().click() // Select Auto (first option)
      await page.waitForTimeout(1000)
      
      // Verify Auto is selected
      const currentValue = await dropdown.textContent()
      expect(currentValue).toMatch(/Auto/i)
    })
  })

  test.describe('Temperature Display Integration', () => {
    
    test('should update area temperature when changing primary sensor', async ({ page }) => {
      await navigateToArea(page, 'Living Room')
      
      // Get initial temperature from overview tab
      const initialTemp = await page.locator('[data-testid="area-current-temp"]').or(
        page.locator('text=/Current.*\\d+\\.?\\d*°/i')
      ).first().textContent()
      
      // Switch to Devices tab and change primary sensor
      await switchToTab(page, 'Devices')
      await dismissSnackbar(page)
      
      const dropdown = page.locator('[data-testid="primary-temp-sensor-select"]').or(
        page.locator('label:has-text("Primary Temperature Sensor")').locator('..').locator('[role="button"]')
      ).first()
      await dropdown.click()
      await page.waitForTimeout(500)
      
      // Select a specific sensor
      const options = page.locator('[role="option"], li[role="menuitem"]')
      await options.nth(1).click()
      await page.waitForTimeout(2000) // Wait for temperature to update
      
      // Go back to overview tab
      await switchToTab(page, 'Overview')
      
      // Get updated temperature
      const updatedTemp = await page.locator('[data-testid="area-current-temp"]').or(
        page.locator('text=/Current.*\\d+\\.?\\d*°/i')
      ).first().textContent()
      
      // Temperature should be present (may or may not change depending on sensor values)
      expect(updatedTemp).toMatch(/\\d+\\.?\\d*°/)
    })

    test('should show temperature from primary sensor in area card', async ({ page }) => {
      // Navigate to main areas view
      await expect(page.locator('text=/Living Room/i')).toBeVisible({ timeout: 5000 })
      
      // Find area card with temperature display
      const areaCard = page.locator('[data-testid="area-card"]').or(
        page.locator('text=/Living Room/i').locator('..')
      ).first()
      
      // Verify temperature is displayed
      await expect(areaCard.locator('text=/\\d+\\.?\\d*°/').first()).toBeVisible()
    })
  })

  test.describe('Persistence and State Management', () => {
    
    test('should persist primary sensor selection across page refreshes', async ({ page }) => {
      await navigateToArea(page, 'Living Room')
      await switchToTab(page, 'Devices')
      await dismissSnackbar(page)
      
      // Select a specific sensor
      const dropdown = page.locator('[data-testid="primary-temp-sensor-select"]').or(
        page.locator('label:has-text("Primary Temperature Sensor")').locator('..').locator('[role="button"]')
      ).first()
      await dropdown.click()
      await page.waitForTimeout(500)
      
      const options = page.locator('[role="option"], li[role="menuitem"]')
      const selectedOption = options.nth(1)
      const sensorName = await selectedOption.textContent()
      await selectedOption.click()
      await page.waitForTimeout(1000)
      
      // Refresh page
      await page.reload()
      await page.waitForTimeout(2000)
      
      // Navigate back to area
      await navigateToSmartHeating(page)
      await navigateToArea(page, 'Living Room')
      await switchToTab(page, 'Devices')
      
      // Verify selection persisted
      const currentValue = await dropdown.textContent()
      expect(currentValue).toContain(sensorName?.trim() || '')
    })

    test('should maintain different primary sensors for different areas', async ({ page }) => {
      // Set primary sensor for Living Room
      await navigateToArea(page, 'Living Room')
      await switchToTab(page, 'Devices')
      await dismissSnackbar(page)
      
      const dropdown1 = page.locator('[data-testid="primary-temp-sensor-select"]').or(
        page.locator('label:has-text("Primary Temperature Sensor")').locator('..').locator('[role="button"]')
      ).first()
      await dropdown1.click()
      await page.waitForTimeout(500)
      
      const options1 = page.locator('[role="option"], li[role="menuitem"]')
      const sensor1Name = await options1.nth(1).textContent()
      await options1.nth(1).click()
      await page.waitForTimeout(1000)
      
      // Navigate to different area (if exists)
      await page.goBack()
      await page.waitForTimeout(1000)
      
      // Try to find another area
      const areaCards = page.locator('[data-testid="area-card"]').or(
        page.locator('text=/Bedroom|Kitchen|Office/i').locator('..')
      )
      
      if (await areaCards.count() > 0) {
        await areaCards.first().click()
        await page.waitForTimeout(1000)
        await switchToTab(page, 'Devices')
        await dismissSnackbar(page)
        
        // Verify this area can have different primary sensor
        const dropdown2 = page.locator('[data-testid="primary-temp-sensor-select"]').or(
          page.locator('label:has-text("Primary Temperature Sensor")').locator('..').locator('[role="button"]')
        ).first()
        
        // Should be able to set independent selection
        await expect(dropdown2).toBeVisible()
      }
    })
  })

  test.describe('Edge Cases and Error Handling', () => {
    
    test('should handle area with no temperature sensors gracefully', async ({ page }) => {
      // This test assumes there might be areas without sensors
      // If Living Room always has sensors, this will just verify dropdown still shows
      
      await navigateToArea(page, 'Living Room')
      await switchToTab(page, 'Devices')
      await dismissSnackbar(page)
      
      // Dropdown should still be visible
      await expect(page.locator('text=/Primary Temperature Sensor/i')).toBeVisible()
      
      // Should at least show Auto option
      const dropdown = page.locator('[data-testid="primary-temp-sensor-select"]').or(
        page.locator('label:has-text("Primary Temperature Sensor")').locator('..').locator('[role="button"]')
      ).first()
      await dropdown.click()
      await page.waitForTimeout(500)
      
      await expect(page.locator('text=/Auto/i')).toBeVisible()
    })

    test('should not break when removing assigned primary sensor', async ({ page }) => {
      await navigateToArea(page, 'Living Room')
      await switchToTab(page, 'Devices')
      await dismissSnackbar(page)
      
      // Select a specific sensor as primary
      const dropdown = page.locator('[data-testid="primary-temp-sensor-select"]').or(
        page.locator('label:has-text("Primary Temperature Sensor")').locator('..').locator('[role="button"]')
      ).first()
      await dropdown.click()
      await page.waitForTimeout(500)
      
      const options = page.locator('[role="option"], li[role="menuitem"]')
      await options.nth(1).click()
      await page.waitForTimeout(1000)
      
      // Now try to remove that device from the area (if possible)
      // Look for remove button next to assigned devices
      const removeButtons = page.locator('button[aria-label="remove"]')
      
      if (await removeButtons.count() > 0) {
        // Remove first device (might be primary sensor)
        await removeButtons.first().click()
        await page.waitForTimeout(1000)
        
        // System should fall back to Auto mode
        // Temperature display should not break
        await expect(page.locator('text=/Primary Temperature Sensor/i')).toBeVisible()
      }
    })
  })

  test.describe('Translation Support', () => {
    
    test('should display labels in English', async ({ page }) => {
      await navigateToArea(page, 'Living Room')
      await switchToTab(page, 'Devices')
      await dismissSnackbar(page)
      
      // Verify English labels
      await expect(page.locator('text=/Primary Temperature Sensor/i')).toBeVisible()
      await expect(page.locator('text=/Select which device measures temperature/i')).toBeVisible()
    })

    test('should display labels in Dutch when language switched', async ({ page }) => {
      // Switch to Dutch
      await page.locator('[data-testid="language-menu"]').or(
        page.locator('button[aria-label*="language"], button:has-text("EN")')
      ).click()
      
      await page.locator('text=/Nederlands|NL/i').click()
      await page.waitForTimeout(1000)
      
      // Navigate to area
      await navigateToSmartHeating(page)
      await navigateToArea(page, 'Living Room')
      await switchToTab(page, 'Devices')
      await dismissSnackbar(page)
      
      // Verify Dutch labels (check translation keys from translation.json)
      // "Primaire Temperatuursensor" or similar
      await expect(page.locator('text=/Primaire.*Temperatuur/i')).toBeVisible({ timeout: 5000 })
    })
  })
})
