import { test, expect } from '@playwright/test'

test.describe('Theme Toggle', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('http://localhost:8123/smart_heating')
    await page.waitForLoadState('networkidle')
  })

  test('should display theme toggle in Global Settings Advanced tab', async ({ page }) => {
    // Navigate to Global Settings
    await page.click('button[aria-label="Open menu"]')
    await page.click('text=Global Settings')
    await page.waitForLoadState('networkidle')

    // Click on Advanced tab
    await page.click('text=Advanced')
    await page.waitForTimeout(500)

    // Verify theme section exists
    const themeTitle = page.locator('text=Theme').first()
    await expect(themeTitle).toBeVisible()

    // Verify theme toggle switch exists
    const themeSwitch = page.locator('input[type="checkbox"]').first()
    await expect(themeSwitch).toBeVisible()
  })

  test('should toggle between light and dark mode', async ({ page }) => {
    // Navigate to Global Settings → Advanced
    await page.click('button[aria-label="Open menu"]')
    await page.click('text=Global Settings')
    await page.waitForLoadState('networkidle')
    await page.click('text=Advanced')
    await page.waitForTimeout(500)

    // Get initial theme state from localStorage
    const initialTheme = await page.evaluate(() => localStorage.getItem('appThemeMode'))

    // Click the theme toggle switch
    const themeSwitch = page.locator('input[type="checkbox"]').first()
    await themeSwitch.click()
    await page.waitForTimeout(300)

    // Verify theme changed in localStorage
    const newTheme = await page.evaluate(() => localStorage.getItem('appThemeMode'))
    expect(newTheme).not.toBe(initialTheme)
    expect(['light', 'dark']).toContain(newTheme)

    // Toggle back
    await themeSwitch.click()
    await page.waitForTimeout(300)

    // Verify theme reverted
    const revertedTheme = await page.evaluate(() => localStorage.getItem('appThemeMode'))
    expect(revertedTheme).toBe(initialTheme)
  })

  test('should persist theme preference across page reloads', async ({ page }) => {
    // Navigate to Global Settings → Advanced
    await page.click('button[aria-label="Open menu"]')
    await page.click('text=Global Settings')
    await page.waitForLoadState('networkidle')
    await page.click('text=Advanced')
    await page.waitForTimeout(500)

    // Set theme to light mode
    const themeSwitch = page.locator('input[type="checkbox"]').first()
    const isChecked = await themeSwitch.isChecked()

    if (isChecked) {
      // Currently dark, switch to light
      await themeSwitch.click()
      await page.waitForTimeout(300)
    }

    // Verify light mode is set
    let currentTheme = await page.evaluate(() => localStorage.getItem('appThemeMode'))
    expect(currentTheme).toBe('light')

    // Reload page
    await page.reload()
    await page.waitForLoadState('networkidle')

    // Verify theme persisted
    currentTheme = await page.evaluate(() => localStorage.getItem('appThemeMode'))
    expect(currentTheme).toBe('light')

    // Navigate back to settings and verify UI reflects the persisted theme
    await page.click('button[aria-label="Open menu"]')
    await page.click('text=Global Settings')
    await page.waitForLoadState('networkidle')
    await page.click('text=Advanced')
    await page.waitForTimeout(500)

    const switchAfterReload = page.locator('input[type="checkbox"]').first()
    const isCheckedAfterReload = await switchAfterReload.isChecked()
    expect(isCheckedAfterReload).toBe(false) // false = light mode
  })

  test('should show correct theme status text', async ({ page }) => {
    // Navigate to Global Settings → Advanced
    await page.click('button[aria-label="Open menu"]')
    await page.click('text=Global Settings')
    await page.waitForLoadState('networkidle')
    await page.click('text=Advanced')
    await page.waitForTimeout(500)

    // Check for theme status text (English or Dutch)
    const themeStatus = page.locator('text=/Dark mode is active|Light mode is active|Donkere modus is actief|Lichte modus is actief/').first()
    await expect(themeStatus).toBeVisible()
  })

  test('should display Light/Dark labels next to toggle', async ({ page }) => {
    // Navigate to Global Settings → Advanced
    await page.click('button[aria-label="Open menu"]')
    await page.click('text=Global Settings')
    await page.waitForLoadState('networkidle')
    await page.click('text=Advanced')
    await page.waitForTimeout(500)

    // Verify Light label exists (English or Dutch)
    const lightLabel = page.locator('text=/^Light$|^Licht$/').first()
    await expect(lightLabel).toBeVisible()

    // Verify Dark label exists (English or Dutch)
    const darkLabel = page.locator('text=/^Dark$|^Donker$/').first()
    await expect(darkLabel).toBeVisible()
  })

  test('should initialize with default dark theme if no preference exists', async ({ page }) => {
    // Clear localStorage to simulate first visit
    await page.evaluate(() => localStorage.removeItem('appThemeMode'))

    // Reload page
    await page.reload()
    await page.waitForLoadState('networkidle')

    // Check that dark mode is the default
    const currentTheme = await page.evaluate(() => localStorage.getItem('appThemeMode'))
    expect(currentTheme).toBe('dark')
  })
})
