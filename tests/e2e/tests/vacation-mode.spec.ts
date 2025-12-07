import { test, expect } from '@playwright/test'

test.describe('Vacation Mode', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/')
    await page.waitForLoadState('networkidle')
  })

  test('should display vacation mode settings in global settings page', async ({ page }) => {
    // Navigate to global settings
    await page.click('[aria-label="Settings"]')
    await page.waitForLoadState('networkidle')

    // Verify vacation mode section exists
    const vacationSection = page.locator('text=🏖️ Vacation Mode')
    await expect(vacationSection).toBeVisible()

    // Verify description is present
    const description = page.locator('text=One-click mode to set all areas to Away preset for extended periods')
    await expect(description).toBeVisible()
  })

  test('should enable vacation mode with valid configuration', async ({ page }) => {
    // Navigate to global settings
    await page.click('[aria-label="Settings"]')
    await page.waitForLoadState('networkidle')

    // Wait for vacation mode section to load
    await page.waitForSelector('text=🏖️ Vacation Mode')

    // Check if vacation mode is already enabled and disable it first
    const disableButton = page.locator('button:has-text("Disable Vacation Mode")')
    const isEnabled = await disableButton.isVisible()
    
    if (isEnabled) {
      await disableButton.click()
      await page.waitForTimeout(1000)
    }

    // Set start date (today)
    const today = new Date()
    const todayStr = today.toLocaleDateString('en-US', { month: '2-digit', day: '2-digit', year: 'numeric' })
    
    // Set end date (7 days from now)
    const endDate = new Date(today)
    endDate.setDate(endDate.getDate() + 7)
    const endDateStr = endDate.toLocaleDateString('en-US', { month: '2-digit', day: '2-digit', year: 'numeric' })

    // Fill in vacation mode form
    // Note: Date pickers might need special handling depending on MUI version
    
    // Select preset mode (should default to "away")
    const presetSelect = page.locator('label:has-text("Preset Mode")').locator('..')
    await expect(presetSelect).toBeVisible()

    // Verify frost protection toggle exists
    const frostProtectionToggle = page.locator('text=Frost Protection Override')
    await expect(frostProtectionToggle).toBeVisible()

    // Verify auto-disable toggle exists
    const autoDisableToggle = page.locator('text=Auto-disable when someone arrives home')
    await expect(autoDisableToggle).toBeVisible()

    // Enable vacation mode
    const enableButton = page.locator('button:has-text("Enable Vacation Mode")')
    await expect(enableButton).toBeVisible()
    await enableButton.click()

    // Wait for the mode to be enabled
    await page.waitForTimeout(2000)

    // Verify vacation mode is enabled - should show "Vacation mode is ACTIVE" alert
    const activeAlert = page.locator('text=Vacation mode is ACTIVE')
    await expect(activeAlert).toBeVisible({ timeout: 5000 })

    // Verify disable button is now visible
    const disableBtn = page.locator('button:has-text("Disable Vacation Mode")')
    await expect(disableBtn).toBeVisible()
  })

  test('should display vacation mode banner on dashboard when active', async ({ page }) => {
    // First enable vacation mode if not already enabled
    await page.click('[aria-label="Settings"]')
    await page.waitForLoadState('networkidle')

    // Check if vacation mode is enabled
    const activeAlert = page.locator('text=Vacation mode is ACTIVE')
    const isAlreadyActive = await activeAlert.isVisible()

    if (!isAlreadyActive) {
      // Enable it
      const enableButton = page.locator('button:has-text("Enable Vacation Mode")')
      if (await enableButton.isVisible()) {
        await enableButton.click()
        await page.waitForTimeout(2000)
      }
    }

    // Navigate back to dashboard
    await page.goto('/')
    await page.waitForLoadState('networkidle')

    // Verify vacation mode banner is visible on dashboard
    const banner = page.locator('text=🏖️ Vacation Mode Active')
    await expect(banner).toBeVisible({ timeout: 5000 })

    // Verify banner shows preset mode
    const bannerText = await banner.textContent()
    expect(bannerText).toContain('away')
  })

  test('should disable vacation mode from banner', async ({ page }) => {
    // Ensure vacation mode is enabled first
    await page.click('[aria-label="Settings"]')
    await page.waitForLoadState('networkidle')

    const activeAlert = page.locator('text=Vacation mode is ACTIVE')
    const isActive = await activeAlert.isVisible()

    if (!isActive) {
      const enableButton = page.locator('button:has-text("Enable Vacation Mode")')
      if (await enableButton.isVisible()) {
        await enableButton.click()
        await page.waitForTimeout(2000)
      }
    }

    // Go back to dashboard
    await page.goto('/')
    await page.waitForLoadState('networkidle')

    // Click disable button in banner
    const bannerDisableBtn = page.locator('button:has-text("Disable")')
    await expect(bannerDisableBtn).toBeVisible({ timeout: 5000 })
    await bannerDisableBtn.click()

    // Wait for disable to complete
    await page.waitForTimeout(2000)

    // Verify banner is no longer visible
    const banner = page.locator('text=🏖️ Vacation Mode Active')
    await expect(banner).not.toBeVisible({ timeout: 5000 })
  })

  test('should disable vacation mode from settings', async ({ page }) => {
    // Navigate to settings and enable vacation mode first
    await page.click('[aria-label="Settings"]')
    await page.waitForLoadState('networkidle')

    const activeAlert = page.locator('text=Vacation mode is ACTIVE')
    const isActive = await activeAlert.isVisible()

    if (!isActive) {
      const enableButton = page.locator('button:has-text("Enable Vacation Mode")')
      if (await enableButton.isVisible()) {
        await enableButton.click()
        await page.waitForTimeout(2000)
      }
    }

    // Now disable it
    const disableButton = page.locator('button:has-text("Disable Vacation Mode")')
    await expect(disableButton).toBeVisible()
    await disableButton.click()

    // Wait for disable to complete
    await page.waitForTimeout(2000)

    // Verify vacation mode is disabled - active alert should not be visible
    await expect(activeAlert).not.toBeVisible({ timeout: 5000 })

    // Verify enable button is now visible
    const enableBtn = page.locator('button:has-text("Enable Vacation Mode")')
    await expect(enableBtn).toBeVisible()
  })

  test('should show frost protection minimum temperature field when enabled', async ({ page }) => {
    // Navigate to global settings
    await page.click('[aria-label="Settings"]')
    await page.waitForLoadState('networkidle')

    // Ensure vacation mode is disabled
    const disableButton = page.locator('button:has-text("Disable Vacation Mode")')
    if (await disableButton.isVisible()) {
      await disableButton.click()
      await page.waitForTimeout(1000)
    }

    // Find frost protection toggle
    const frostToggle = page.locator('text=Frost Protection Override').locator('..').locator('input[type="checkbox"]')
    
    // If not checked, check it
    const isChecked = await frostToggle.isChecked()
    if (!isChecked) {
      await frostToggle.click()
    }

    // Verify minimum temperature field appears
    const minTempField = page.locator('label:has-text("Minimum Temperature")')
    await expect(minTempField).toBeVisible()
  })

  test('should preserve vacation mode settings across page reloads', async ({ page }) => {
    // Enable vacation mode
    await page.click('[aria-label="Settings"]')
    await page.waitForLoadState('networkidle')

    // Disable first if enabled
    const disableButton = page.locator('button:has-text("Disable Vacation Mode")')
    if (await disableButton.isVisible()) {
      await disableButton.click()
      await page.waitForTimeout(1000)
    }

    // Enable vacation mode
    const enableButton = page.locator('button:has-text("Enable Vacation Mode")')
    await enableButton.click()
    await page.waitForTimeout(2000)

    // Reload the page
    await page.reload()
    await page.waitForLoadState('networkidle')

    // Navigate back to settings
    await page.click('[aria-label="Settings"]')
    await page.waitForLoadState('networkidle')

    // Verify vacation mode is still active
    const activeAlert = page.locator('text=Vacation mode is ACTIVE')
    await expect(activeAlert).toBeVisible({ timeout: 5000 })

    // Clean up - disable vacation mode
    const disableBtn = page.locator('button:has-text("Disable Vacation Mode")')
    await disableBtn.click()
    await page.waitForTimeout(1000)
  })

  test('should show different preset mode options', async ({ page }) => {
    // Navigate to global settings
    await page.click('[aria-label="Settings"]')
    await page.waitForLoadState('networkidle')

    // Ensure vacation mode is disabled
    const disableButton = page.locator('button:has-text("Disable Vacation Mode")')
    if (await disableButton.isVisible()) {
      await disableButton.click()
      await page.waitForTimeout(1000)
    }

    // Click on preset mode select
    const presetSelect = page.locator('label:has-text("Preset Mode")').locator('..').locator('[role="combobox"]')
    await presetSelect.click()

    // Verify preset options are visible
    await expect(page.locator('text=Away')).toBeVisible()
    await expect(page.locator('text=Eco')).toBeVisible()
    await expect(page.locator('text=Sleep')).toBeVisible()

    // Close dropdown
    await page.keyboard.press('Escape')
  })
})
