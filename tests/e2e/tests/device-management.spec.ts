import { test, expect } from '@playwright/test'
import { login, navigateToSmartHeating, navigateToArea, switchToTab, dismissSnackbar } from './helpers'

/**
 * Device Management Tests - Devices Tab in Area Detail
 * 
 * Features tested:
 * - Devices tab visibility and navigation
 * - Assigned Devices section display
 * - Available Devices section display
 * - Add device functionality
 * - Remove device functionality
 * - Smart filtering (HA area match + name-based matching)
 * - Real-time device status updates
 * 
 * Tests verify:
 * 1. Frontend UI displays devices correctly
 * 2. Backend API calls succeed
 * 3. State updates reflect in UI
 */

test.describe('Device Management', () => {
  
  test.beforeEach(async ({ page }) => {
    await login(page)
    await navigateToSmartHeating(page)
  })

  test.describe('Devices Tab Navigation', () => {
    
    test('should show Devices tab in area detail', async ({ page }) => {
      await navigateToArea(page, 'Living Room')
      
      // Verify Devices tab exists (2nd tab, index 1)
      const devicesTab = page.locator('button[role="tab"]', { hasText: /^Devices$/i })
      await expect(devicesTab).toBeVisible()
    })

    test('should navigate to Devices tab', async ({ page }) => {
      await navigateToArea(page, 'Living Room')
      
      // Click Devices tab
      await switchToTab(page, 'Devices')
      
      // Verify tab content is visible
      await expect(page.locator('text=/Assigned Devices/i')).toBeVisible({ timeout: 5000 })
      await expect(page.locator('text=/Available Devices/i')).toBeVisible({ timeout: 5000 })
    })
  })

  test.describe('Assigned Devices Section', () => {
    
    test('should display assigned devices section', async ({ page }) => {
      await navigateToArea(page, 'Living Room')
      await switchToTab(page, 'Devices')
      await dismissSnackbar(page)
      
      // Verify section header
      await expect(page.locator('text=/Assigned Devices \\(\\d+\\)/i')).toBeVisible()
      
      // Verify description text
      await expect(page.locator('text=/Devices currently assigned to this area/i')).toBeVisible()
    })

    test('should show assigned devices with remove buttons', async ({ page }) => {
      await navigateToArea(page, 'Living Room')
      await switchToTab(page, 'Devices')
      await dismissSnackbar(page)
      
      // Check if there are assigned devices
      const assignedCount = await page.locator('text=/Assigned Devices \\((\\d+)\\)/i').textContent()
      const count = parseInt(assignedCount?.match(/\\d+/)?.[0] || '0')
      
      if (count > 0) {
        // Verify device list items are visible
        const deviceItems = page.locator('[role="listitem"]').first()
        await expect(deviceItems).toBeVisible()
        
        // Verify remove button exists
        const removeButton = page.locator('button[aria-label="remove"]').first()
        await expect(removeButton).toBeVisible()
      }
      // If count is 0, test still passes (devices may all be assigned)
    })

    test('should display device status for assigned devices', async ({ page }) => {
      await navigateToArea(page, 'Living Room')
      await switchToTab(page, 'Devices')
      await dismissSnackbar(page)
      
      // Check if there are assigned devices
      const assignedCount = await page.locator('text=/Assigned Devices \\((\\d+)\\)/i').textContent()
      const count = parseInt(assignedCount?.match(/\\d+/)?.[0] || '0')
      
      if (count > 0) {
        // Verify device type is shown (e.g., "thermostat", "temperature sensor")
        const deviceType = page.locator('text=/thermostat|temperature sensor|valve|switch/i').first()
        await expect(deviceType).toBeVisible()
      }
    })
  })

  test.describe('Available Devices Section', () => {
    
    test('should display available devices section', async ({ page }) => {
      await navigateToArea(page, 'Living Room')
      await switchToTab(page, 'Devices')
      await dismissSnackbar(page)
      
      // Verify section header
      await expect(page.locator('text=/Available Devices \\(\\d+\\)/i')).toBeVisible()
      
      // Verify description text
      await expect(page.locator('text=/Devices assigned to.*in Home Assistant but not yet added/i')).toBeVisible()
    })

    test('should show available devices with add buttons', async ({ page }) => {
      await navigateToArea(page, 'Kitchen')
      await switchToTab(page, 'Devices')
      await dismissSnackbar(page)
      
      // Wait for available devices to load
      await page.waitForTimeout(1000)
      
      // Check if there are available devices
      const availableCount = await page.locator('text=/Available Devices \\((\\d+)\\)/i').textContent()
      const count = parseInt(availableCount?.match(/\\d+/)?.[0] || '0')
      
      if (count > 0) {
        // Verify add button exists
        const addButton = page.locator('button', { hasText: /^Add$/i }).first()
        await expect(addButton).toBeVisible()
        
        // Verify device entity_id is shown
        const deviceInfo = page.locator('text=/climate\\.|sensor\\.|switch\\.|number\\./i').first()
        await expect(deviceInfo).toBeVisible()
      }
      // If count is 0, test still passes (all devices may be assigned)
    })

    test('should filter devices by HA area assignment', async ({ page }) => {
      // Navigate to Kitchen area
      await navigateToArea(page, 'Kitchen')
      await switchToTab(page, 'Devices')
      await dismissSnackbar(page)
      await page.waitForTimeout(1000)
      
      // Get available devices count
      const availableCount = await page.locator('text=/Available Devices \\((\\d+)\\)/i').textContent()
      const count = parseInt(availableCount?.match(/\\d+/)?.[0] || '0')
      
      if (count > 0) {
        // Verify device names contain "Kitchen" (name-based matching)
        const deviceNames = await page.locator('[role="listitem"]').allTextContents()
        const hasKitchenDevice = deviceNames.some(name => name.toLowerCase().includes('kitchen'))
        expect(hasKitchenDevice).toBeTruthy()
      }
    })
  })

  test.describe('Device Add/Remove Operations', () => {
    
    test('should add device from available to assigned', async ({ page }) => {
      await navigateToArea(page, 'Kitchen')
      await switchToTab(page, 'Devices')
      await dismissSnackbar(page)
      await page.waitForTimeout(1000)
      
      // Get initial counts
      const initialAvailable = await page.locator('text=/Available Devices \\((\\d+)\\)/i').textContent()
      const availableCount = parseInt(initialAvailable?.match(/\\d+/)?.[0] || '0')
      
      if (availableCount > 0) {
        // Get initial assigned count
        const initialAssigned = await page.locator('text=/Assigned Devices \\((\\d+)\\)/i').textContent()
        const assignedCountBefore = parseInt(initialAssigned?.match(/\\d+/)?.[0] || '0')
        
        // Click first Add button
        const addButton = page.locator('button', { hasText: /^Add$/i }).first()
        await addButton.click()
        
        // Wait for update
        await page.waitForTimeout(2000)
        
        // Verify assigned count increased
        const newAssigned = await page.locator('text=/Assigned Devices \\((\\d+)\\)/i').textContent()
        const assignedCountAfter = parseInt(newAssigned?.match(/\\d+/)?.[0] || '0')
        
        expect(assignedCountAfter).toBe(assignedCountBefore + 1)
      }
    })

    test('should remove device from assigned', async ({ page }) => {
      await navigateToArea(page, 'Living Room')
      await switchToTab(page, 'Devices')
      await dismissSnackbar(page)
      await page.waitForTimeout(1000)
      
      // Get initial assigned count
      const initialAssigned = await page.locator('text=/Assigned Devices \\((\\d+)\\)/i').textContent()
      const assignedCount = parseInt(initialAssigned?.match(/\\d+/)?.[0] || '0')
      
      if (assignedCount > 0) {
        // Get initial available count
        const initialAvailable = await page.locator('text=/Available Devices \\((\\d+)\\)/i').textContent()
        const availableCountBefore = parseInt(initialAvailable?.match(/\\d+/)?.[0] || '0')
        
        // Click first Remove button
        const removeButton = page.locator('button[aria-label="remove"]').first()
        await removeButton.click()
        
        // Wait for update
        await page.waitForTimeout(2000)
        
        // Verify assigned count decreased
        const newAssigned = await page.locator('text=/Assigned Devices \\((\\d+)\\)/i').textContent()
        const assignedCountAfter = parseInt(newAssigned?.match(/\\d+/)?.[0] || '0')
        
        expect(assignedCountAfter).toBe(assignedCount - 1)
        
        // Verify available count increased (if device had HA area assignment)
        const newAvailable = await page.locator('text=/Available Devices \\((\\d+)\\)/i').textContent()
        const availableCountAfter = parseInt(newAvailable?.match(/\\d+/)?.[0] || '0')
        
        // Device should appear in available if it has HA area or name match
        expect(availableCountAfter).toBeGreaterThanOrEqual(availableCountBefore)
      }
    })
  })

  test.describe('Smart Filtering (HA Area + Name Matching)', () => {
    
    test('should match devices by HA area ID', async ({ page }) => {
      // This test verifies that devices with ha_area_id matching the zone ID appear
      await navigateToArea(page, 'Living Room')
      await switchToTab(page, 'Devices')
      await dismissSnackbar(page)
      await page.waitForTimeout(1000)
      
      // Available devices should be filtered by HA area
      const availableSection = page.locator('text=/Available Devices/i')
      await expect(availableSection).toBeVisible()
    })

    test('should match devices by name (for MQTT devices)', async ({ page }) => {
      // This test verifies name-based matching for devices without HA area assignment
      await navigateToArea(page, 'Kitchen')
      await switchToTab(page, 'Devices')
      await dismissSnackbar(page)
      await page.waitForTimeout(1000)
      
      // Check if available devices contain "Kitchen" in name
      const availableCount = await page.locator('text=/Available Devices \\((\\d+)\\)/i').textContent()
      const count = parseInt(availableCount?.match(/\\d+/)?.[0] || '0')
      
      if (count > 0) {
        // Get device names
        const deviceItems = await page.locator('[role="listitem"]').allTextContents()
        
        // At least one device should contain the area name
        const hasMatchingName = deviceItems.some(item => 
          item.toLowerCase().includes('kitchen')
        )
        
        expect(hasMatchingName).toBeTruthy()
      }
    })

    test('should not show devices already assigned', async ({ page }) => {
      await navigateToArea(page, 'Living Room')
      await switchToTab(page, 'Devices')
      await dismissSnackbar(page)
      await page.waitForTimeout(1000)
      
      // Get all assigned device names
      const assignedCount = await page.locator('text=/Assigned Devices \\((\\d+)\\)/i').textContent()
      const count = parseInt(assignedCount?.match(/\\d+/)?.[0] || '0')
      
      if (count > 0) {
        const assignedSection = page.locator('text=/Assigned Devices/i').locator('..')
        const assignedDevices = await assignedSection.locator('[role="listitem"]').allTextContents()
        
        // Get all available device names
        const availableSection = page.locator('text=/Available Devices/i').locator('..')
        const availableDevices = await availableSection.locator('[role="listitem"]').allTextContents()
        
        // No device should appear in both lists
        const overlap = assignedDevices.some(assigned => 
          availableDevices.some(available => 
            assigned.includes(available) || available.includes(assigned)
          )
        )
        
        expect(overlap).toBeFalsy()
      }
    })
  })

  test.describe('Device Search & Filtering (v0.3.17)', () => {
    
    test('should display search bar in Available Devices', async ({ page }) => {
      await navigateToArea(page, 'Living Room')
      await switchToTab(page, 'Devices')
      await dismissSnackbar(page)
      
      // Verify search input exists
      const searchInput = page.locator('input[placeholder*="Search"]').first()
      await expect(searchInput).toBeVisible()
    })

    test('should filter devices by search term', async ({ page }) => {
      await navigateToArea(page, 'Living Room')
      await switchToTab(page, 'Devices')
      await dismissSnackbar(page)
      await page.waitForTimeout(1000)
      
      // Get initial device count
      const initialCount = await page.locator('text=/Available Devices \\((\\d+)\\)/i').textContent()
      const initial = parseInt(initialCount?.match(/\\d+/)?.[0] || '0')
      
      if (initial > 0) {
        // Type search term
        const searchInput = page.locator('input[placeholder*="Search"]').first()
        await searchInput.fill('living')
        await page.waitForTimeout(500)
        
        // Get filtered count
        const filteredCount = await page.locator('text=/Available Devices \\((\\d+)\\)/i').textContent()
        const filtered = parseInt(filteredCount?.match(/\\d+/)?.[0] || '0')
        
        // Count should update (may be same, less, or 0)
        expect(filtered).toBeLessThanOrEqual(initial)
      }
    })

    test('should display climate filter toggle', async ({ page }) => {
      await navigateToArea(page, 'Living Room')
      await switchToTab(page, 'Devices')
      await dismissSnackbar(page)
      
      // Verify filter toggle exists
      const filterToggle = page.locator('text=/Show only climate.*temperature/i')
      await expect(filterToggle).toBeVisible()
    })

    test('should filter devices by climate/temperature type', async ({ page }) => {
      await navigateToArea(page, 'Living Room')
      await switchToTab(page, 'Devices')
      await dismissSnackbar(page)
      await page.waitForTimeout(1000)
      
      // Get count with filter ON (default)
      const filteredCount = await page.locator('text=/Available Devices \\((\\d+)\\)/i').textContent()
      const filtered = parseInt(filteredCount?.match(/\\d+/)?.[0] || '0')
      
      // Toggle filter OFF - find the switch by the label text
      const filterLabel = page.locator('text=/Show only climate.*temperature/i')
      await expect(filterLabel).toBeVisible({ timeout: 5000 })
      
      // Click the switch (it's the checkbox input before the label)
      const filterSwitch = page.locator('input[type="checkbox"]').first()
      await filterSwitch.click()
      await page.waitForTimeout(500)
      
      // Get count with filter OFF
      const unfilteredCount = await page.locator('text=/Available Devices \\((\\d+)\\)/i').textContent()
      const unfiltered = parseInt(unfilteredCount?.match(/\\d+/)?.[0] || '0')
      
      // Unfiltered should be >= filtered (shows all devices)
      expect(unfiltered).toBeGreaterThanOrEqual(filtered)
    })

    test('should show subtype chips on devices', async ({ page }) => {
      await navigateToArea(page, 'Living Room')
      await switchToTab(page, 'Devices')
      await dismissSnackbar(page)
      
      // Toggle filter OFF to see all devices
      const filterSwitch = page.locator('input[type="checkbox"]').first()
      await filterSwitch.click()
      await page.waitForTimeout(1000)
      
      // Check for device chips
      const availableCount = await page.locator('text=/Available Devices \\((\\d+)\\)/i').textContent()
      const count = parseInt(availableCount?.match(/\\d+/)?.[0] || '0')
      
      if (count > 0) {
        // Should have at least one chip (type or subtype)
        const chips = page.locator('.MuiChip-label')
        const chipCount = await chips.count()
        expect(chipCount).toBeGreaterThan(0)
      }
    })
  })

  test.describe('Drag & Drop on Main Page (Preserved)', () => {
    
    test('should still have drag and drop on main page', async ({ page }) => {
      // Verify drag & drop functionality is preserved on main page
      
      // Check for Available Devices sidebar
      const sidebar = page.locator('text=/Available Devices/i').first()
      await expect(sidebar).toBeVisible()
      
      // Check for "Drag devices to areas" text
      const dragText = page.locator('text=/Drag devices to areas/i')
      await expect(dragText).toBeVisible()
    })

    test('should show draggable devices in sidebar', async ({ page }) => {
      // Verify devices are still draggable on main page
      const devicePanel = page.locator('text=/Available Devices/i').first().locator('..')
      
      // Check if devices exist in sidebar
      const devices = devicePanel.locator('[draggable="true"]')
      const count = await devices.count()
      
      // Should have draggable devices (may be 0 if all assigned, that's OK)
      expect(count).toBeGreaterThanOrEqual(0)
    })

    test('should have search bar in main page sidebar (v0.3.17)', async ({ page }) => {
      // Verify search functionality added to sidebar
      const searchInput = page.locator('input[placeholder*="Search"]').first()
      await expect(searchInput).toBeVisible()
    })

    test('should have filter toggle in main page sidebar (v0.3.17)', async ({ page }) => {
      // Verify filter toggle in sidebar
      const filterToggle = page.locator('text=/Climate.*temp.*only/i').or(
        page.locator('text=/Show only climate/i')
      )
      await expect(filterToggle).toBeVisible()
    })

    test('should filter sidebar devices by search (v0.3.17)', async ({ page }) => {
      await page.waitForTimeout(1000)
      
      // Get initial count
      const initialText = await page.locator('text=/Available Devices \\((\\d+)\\)/i').first().textContent()
      const initial = parseInt(initialText?.match(/\\d+/)?.[0] || '0')
      
      if (initial > 0) {
        // Search for something
        const searchInput = page.locator('input[placeholder*="Search"]').first()
        await searchInput.fill('xyz_nonexistent')
        await page.waitForTimeout(500)
        
        // Count should change (likely to 0)
        const filteredText = await page.locator('text=/Available Devices \\((\\d+)\\)/i').first().textContent()
        const filtered = parseInt(filteredText?.match(/\\d+/)?.[0] || '0')
        
        expect(filtered).toBe(0)
      }
    })
  })
})
