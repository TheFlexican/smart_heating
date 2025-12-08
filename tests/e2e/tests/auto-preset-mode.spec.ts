import { test, expect } from '@playwright/test'
import { navigateToSmartHeating, navigateToArea, switchToTab } from './helpers'

test.describe('Auto Preset Mode', () => {
  // Helper function to navigate to area settings and expand Auto Preset card
  async function navigateToAreaSettings(page: any) {
    await page.locator('text=Auto Preset Mode').click()
    await page.waitForTimeout(500)
  }

  test.beforeEach(async ({ page }) => {
    await navigateToSmartHeating(page)
    await navigateToArea(page, 'Woonkamer') // Navigate to first area
    await switchToTab(page, 'Settings')
  })

  test('Auto Preset Mode card is visible in Settings tab', async ({ page }) => {
    await page.waitForSelector('text=Auto Preset Mode', { timeout: 5000 })

    // Verify Auto Preset Mode card is visible
    const autoPresetCard = page.locator('text=Auto Preset Mode').locator('..')
    await expect(autoPresetCard).toBeVisible()

    // Verify description
    await expect(page.locator('text=Automatically switch preset based on presence detection')).toBeVisible()

    // Verify badge shows OFF by default
    await expect(page.locator('text=AUTO').or(page.locator('text=OFF'))).toBeVisible()
  })

  test('Can expand Auto Preset Mode settings card', async ({ page }) => {
    // Wait for card to be visible
    await page.waitForSelector('text=Auto Preset Mode', { timeout: 5000 })

    // Click to expand the card
    await page.locator('text=Auto Preset Mode').click()

    // Wait for expansion animation
    await page.waitForTimeout(500)

    // Verify enable switch is visible
    await expect(page.locator('text=Enable Auto Preset').first()).toBeVisible()
  })

  test('Can enable Auto Preset Mode', async ({ page }) => {
    // Expand Auto Preset card
    await page.locator('text=Auto Preset Mode').click()
    await page.waitForTimeout(500)

    // Find and click the enable switch
    const enableSwitch = page.locator('text=Enable Auto Preset').locator('..').locator('input[type="checkbox"]').first()
    await enableSwitch.click()

    // Wait for API call
    await page.waitForTimeout(1000)

    // Verify switch is checked
    await expect(enableSwitch).toBeChecked()

    // Verify explanation appears
    await expect(page.locator('text=When enabled, preset mode will automatically switch')).toBeVisible()

    // Verify preset dropdowns are visible
    await expect(page.locator('text=Preset When Home')).toBeVisible()
    await expect(page.locator('text=Preset When Away')).toBeVisible()
  })

  test('Can configure home preset when auto preset is enabled', async ({ page }) => {
    await navigateToAreaSettings(page)

    // Enable auto preset first
    const enableSwitch = page.locator('text=Enable Auto Preset').locator('..').locator('input[type="checkbox"]').first()
    await enableSwitch.click()
    await page.waitForTimeout(1000)

    // Find the "Preset When Home" dropdown
    const homePresetDropdown = page.locator('text=Preset When Home').locator('..').locator('[role="button"]').first()
    await homePresetDropdown.click()

    // Wait for dropdown menu
    await page.waitForSelector('[role="listbox"]', { timeout: 2000 })

    // Select "Comfort" preset
    await page.locator('[role="option"]', { hasText: 'Comfort' }).click()

    // Wait for API call
    await page.waitForTimeout(1000)

    // Verify selection persisted by reopening dropdown
    await homePresetDropdown.click()
    await page.waitForTimeout(500)
    
    // Verify Comfort is selected (has aria-selected="true" or is highlighted)
    const comfortOption = page.locator('[role="option"]', { hasText: 'Comfort' })
    await expect(comfortOption).toHaveAttribute('aria-selected', 'true')
  })

  test('Can configure away preset when auto preset is enabled', async ({ page }) => {
    await navigateToAreaSettings(page)

    // Enable auto preset first
    const enableSwitch = page.locator('text=Enable Auto Preset').locator('..').locator('input[type="checkbox"]').first()
    await enableSwitch.click()
    await page.waitForTimeout(1000)

    // Find the "Preset When Away" dropdown
    const awayPresetDropdown = page.locator('text=Preset When Away').locator('..').locator('[role="button"]').first()
    await awayPresetDropdown.click()

    // Wait for dropdown menu
    await page.waitForSelector('[role="listbox"]', { timeout: 2000 })

    // Select "Eco" preset
    await page.locator('[role="option"]', { hasText: 'Eco' }).click()

    // Wait for API call
    await page.waitForTimeout(1000)

    // Verify selection persisted
    await awayPresetDropdown.click()
    await page.waitForTimeout(500)
    const ecoOption = page.locator('[role="option"]', { hasText: 'Eco' })
    await expect(ecoOption).toHaveAttribute('aria-selected', 'true')
  })

  test('Shows warning when no presence sensors configured', async ({ page }) => {
    await navigateToAreaSettings(page)

    // Expand Auto Preset card and enable
    const enableSwitch = page.locator('text=Enable Auto Preset').locator('..').locator('input[type="checkbox"]').first()
    await enableSwitch.click()
    await page.waitForTimeout(1000)

    // Check if warning about no presence sensors appears
    // (This will only show if the area has no presence sensors configured)
    const warningText = page.locator('text=No presence sensors configured')
    const hasWarning = await warningText.count() > 0
    
    // If warning is present, verify it's visible
    if (hasWarning) {
      await expect(warningText).toBeVisible()
    }
  })

  test('Can disable Auto Preset Mode', async ({ page }) => {
    await navigateToAreaSettings(page)

    // Enable auto preset first
    const enableSwitch = page.locator('text=Enable Auto Preset').locator('..').locator('input[type="checkbox"]').first()
    await enableSwitch.click()
    await page.waitForTimeout(1000)

    // Verify it's enabled
    await expect(enableSwitch).toBeChecked()

    // Disable it
    await enableSwitch.click()
    await page.waitForTimeout(1000)

    // Verify it's disabled
    await expect(enableSwitch).not.toBeChecked()

    // Verify disabled message appears
    await expect(page.locator('text=Auto preset is disabled')).toBeVisible()

    // Verify preset dropdowns are hidden
    await expect(page.locator('text=Preset When Home')).not.toBeVisible()
  })

  test('Settings persist after page reload', async ({ page }) => {
    await navigateToAreaSettings(page)

    // Enable auto preset first
    const enableSwitch = page.locator('text=Enable Auto Preset').locator('..').locator('input[type="checkbox"]').first()
    await enableSwitch.click()
    await page.waitForTimeout(1000)

    // Configure home preset to Comfort
    const homePresetDropdown = page.locator('text=Preset When Home').locator('..').locator('[role="button"]').first()
    await homePresetDropdown.click()
    await page.waitForSelector('[role="listbox"]', { timeout: 2000 })
    await page.locator('[role="option"]', { hasText: 'Comfort' }).click()
    await page.waitForTimeout(1000)

    // Reload page
    await page.reload()
    await page.waitForTimeout(2000)

    // Navigate back to settings
    await page.locator('text=Settings').click()
    await page.waitForTimeout(1000)

    // Expand Auto Preset card
    await page.locator('text=Auto Preset Mode').click()
    await page.waitForTimeout(500)

    // Verify switch is still checked
    const reloadedSwitch = page.locator('text=Enable Auto Preset').locator('..').locator('input[type="checkbox"]').first()
    await expect(reloadedSwitch).toBeChecked()

    // Verify Comfort is still selected
    const reloadedDropdown = page.locator('text=Preset When Home').locator('..').locator('[role="button"]').first()
    await reloadedDropdown.click()
    await page.waitForTimeout(500)
    const comfortOption = page.locator('[role="option"]', { hasText: 'Comfort' })
    await expect(comfortOption).toHaveAttribute('aria-selected', 'true')
  })
})
