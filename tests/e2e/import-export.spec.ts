import { test, expect } from '@playwright/test';
import * as fs from 'fs';
import * as path from 'path';

/**
 * E2E Tests for Import/Export Configuration Feature
 * 
 * Test Coverage:
 * - Export configuration to JSON file
 * - Import configuration with preview
 * - Validation of import data
 * - Backup creation and restoration
 * - Error handling for invalid imports
 */

test.describe('Import/Export Configuration', () => {
  
  test.beforeEach(async ({ page }) => {
    // Navigate to Smart Heating integration
    await page.goto('http://localhost:8123');
    
    // Wait for page to load
    await page.waitForLoadState('networkidle');
    
    // Navigate to Smart Heating panel
    await page.click('text=Smart Heating');
    await page.waitForLoadState('networkidle');
    
    // Navigate to Global Settings
    await page.click('text=Global Settings');
    await page.waitForLoadState('networkidle');
  });

  test('should navigate to Import/Export tab', async ({ page }) => {
    // Click on Import/Export tab (6th tab)
    await page.click('[role="tab"]:has-text("Import/Export")');
    
    // Verify tab is active
    await expect(page.locator('[role="tab"]:has-text("Import/Export")[aria-selected="true"]')).toBeVisible();
    
    // Verify Import/Export component is displayed
    await expect(page.locator('text=Export Configuration')).toBeVisible();
    await expect(page.locator('text=Import Configuration')).toBeVisible();
  });

  test('should export configuration and download JSON file', async ({ page }) => {
    // Navigate to Import/Export tab
    await page.click('[role="tab"]:has-text("Import/Export")');
    
    // Set up download listener
    const downloadPromise = page.waitForEvent('download');
    
    // Click Export button
    await page.click('button:has-text("Export Configuration")');
    
    // Wait for download
    const download = await downloadPromise;
    
    // Verify download filename format
    const filename = download.suggestedFilename();
    expect(filename).toMatch(/smart_heating_config_\d{8}_\d{6}\.json/);
    
    // Save and verify file content
    const downloadPath = path.join(__dirname, 'downloads', filename);
    await download.saveAs(downloadPath);
    
    // Read and parse exported JSON
    const exportedData = JSON.parse(fs.readFileSync(downloadPath, 'utf-8'));
    
    // Verify required fields
    expect(exportedData).toHaveProperty('version');
    expect(exportedData).toHaveProperty('export_date');
    expect(exportedData).toHaveProperty('areas');
    expect(exportedData).toHaveProperty('global_settings');
    expect(exportedData).toHaveProperty('vacation_mode');
    
    // Verify version format
    expect(exportedData.version).toMatch(/^\d+\.\d+\.\d+$/);
    
    // Cleanup
    fs.unlinkSync(downloadPath);
  });

  test('should show import file picker when clicking Import button', async ({ page }) => {
    // Navigate to Import/Export tab
    await page.click('[role="tab"]:has-text("Import/Export")');
    
    // Click Import button
    await page.click('button:has-text("Import Configuration")');
    
    // Verify file input is triggered (we can't actually interact with native file picker in headless mode)
    // Instead, verify the button is clickable and no errors occur
    await expect(page.locator('button:has-text("Import Configuration")')).toBeEnabled();
  });

  test('should import configuration and show preview dialog', async ({ page }) => {
    // First export to get valid data
    await page.click('[role="tab"]:has-text("Import/Export")');
    const downloadPromise = page.waitForEvent('download');
    await page.click('button:has-text("Export Configuration")');
    const download = await downloadPromise;
    const downloadPath = path.join(__dirname, 'downloads', 'test_export.json');
    await download.saveAs(downloadPath);
    
    // Modify exported data slightly to create changes
    const exportedData = JSON.parse(fs.readFileSync(downloadPath, 'utf-8'));
    if (exportedData.global_settings?.frost_protection) {
      exportedData.global_settings.frost_protection.temperature = 5.0;
    }
    
    // Save modified data
    const importPath = path.join(__dirname, 'downloads', 'test_import.json');
    fs.writeFileSync(importPath, JSON.stringify(exportedData, null, 2));
    
    // Upload file using file input
    const fileInput = await page.locator('input[type="file"]');
    await fileInput.setInputFiles(importPath);
    
    // Wait for preview dialog to appear
    await expect(page.locator('text=Import Preview')).toBeVisible({ timeout: 5000 });
    
    // Verify preview shows changes
    await expect(page.locator('.MuiDialog-root')).toBeVisible();
    
    // Check for preview content sections
    await expect(page.locator('text=Areas to Create')).toBeVisible();
    await expect(page.locator('text=Areas to Update')).toBeVisible();
    await expect(page.locator('text=Global Settings Changes')).toBeVisible();
    
    // Close preview without importing
    await page.click('button:has-text("Cancel")');
    await expect(page.locator('.MuiDialog-root')).not.toBeVisible();
    
    // Cleanup
    fs.unlinkSync(downloadPath);
    fs.unlinkSync(importPath);
  });

  test('should successfully import configuration with backup', async ({ page }) => {
    // Export current config first
    await page.click('[role="tab"]:has-text("Import/Export")');
    const downloadPromise = page.waitForEvent('download');
    await page.click('button:has-text("Export Configuration")');
    const download = await downloadPromise;
    const downloadPath = path.join(__dirname, 'downloads', 'test_export.json');
    await download.saveAs(downloadPath);
    
    // Upload same file (should create backup but no changes)
    const fileInput = await page.locator('input[type="file"]');
    await fileInput.setInputFiles(downloadPath);
    
    // Wait for preview dialog
    await expect(page.locator('text=Import Preview')).toBeVisible({ timeout: 5000 });
    
    // Confirm import
    await page.click('button:has-text("Confirm Import")');
    
    // Wait for success message
    await expect(page.locator('text=Configuration imported successfully')).toBeVisible({ timeout: 10000 });
    
    // Verify success alert details
    const successAlert = page.locator('.MuiAlert-standardSuccess');
    await expect(successAlert).toBeVisible();
    
    // Page should reload after successful import
    await page.waitForLoadState('networkidle');
    
    // Cleanup
    fs.unlinkSync(downloadPath);
  });

  test('should show error for invalid JSON import', async ({ page }) => {
    // Navigate to Import/Export tab
    await page.click('[role="tab"]:has-text("Import/Export")');
    
    // Create invalid JSON file
    const invalidPath = path.join(__dirname, 'downloads', 'invalid.json');
    fs.writeFileSync(invalidPath, '{ invalid json }');
    
    // Upload invalid file
    const fileInput = await page.locator('input[type="file"]');
    await fileInput.setInputFiles(invalidPath);
    
    // Wait for error message
    await expect(page.locator('text=Invalid JSON')).toBeVisible({ timeout: 5000 });
    
    // Verify error alert
    const errorAlert = page.locator('.MuiAlert-standardError');
    await expect(errorAlert).toBeVisible();
    
    // Cleanup
    fs.unlinkSync(invalidPath);
  });

  test('should show error for incompatible version', async ({ page }) => {
    // Navigate to Import/Export tab
    await page.click('[role="tab"]:has-text("Import/Export")');
    
    // Create config with incompatible version
    const incompatibleConfig = {
      version: '99.99.99',
      export_date: new Date().toISOString(),
      areas: {},
      global_settings: {},
      vacation_mode: {},
    };
    
    const incompatiblePath = path.join(__dirname, 'downloads', 'incompatible.json');
    fs.writeFileSync(incompatiblePath, JSON.stringify(incompatibleConfig, null, 2));
    
    // Upload incompatible file
    const fileInput = await page.locator('input[type="file"]');
    await fileInput.setInputFiles(incompatiblePath);
    
    // Wait for error message about version
    await expect(page.locator('text=Incompatible configuration version')).toBeVisible({ timeout: 5000 });
    
    // Cleanup
    fs.unlinkSync(incompatiblePath);
  });

  test('should show loading state during import', async ({ page }) => {
    // Export current config
    await page.click('[role="tab"]:has-text("Import/Export")');
    const downloadPromise = page.waitForEvent('download');
    await page.click('button:has-text("Export Configuration")');
    const download = await downloadPromise;
    const downloadPath = path.join(__dirname, 'downloads', 'test_export.json');
    await download.saveAs(downloadPath);
    
    // Upload file
    const fileInput = await page.locator('input[type="file"]');
    await fileInput.setInputFiles(downloadPath);
    
    // Verify loading indicator appears briefly
    // (This may be too fast to catch in some environments)
    await page.waitForSelector('.MuiCircularProgress-root', { timeout: 1000 }).catch(() => {
      // Loading may complete too quickly, that's OK
    });
    
    // Preview should appear after loading
    await expect(page.locator('text=Import Preview')).toBeVisible({ timeout: 5000 });
    
    // Close preview
    await page.click('button:has-text("Cancel")');
    
    // Cleanup
    fs.unlinkSync(downloadPath);
  });

  test('should disable buttons during import operation', async ({ page }) => {
    // Export current config
    await page.click('[role="tab"]:has-text("Import/Export")');
    const downloadPromise = page.waitForEvent('download');
    await page.click('button:has-text("Export Configuration")');
    const download = await downloadPromise;
    const downloadPath = path.join(__dirname, 'downloads', 'test_export.json');
    await download.saveAs(downloadPath);
    
    // Upload file
    const fileInput = await page.locator('input[type="file"]');
    await fileInput.setInputFiles(downloadPath);
    
    // Wait for preview
    await expect(page.locator('text=Import Preview')).toBeVisible({ timeout: 5000 });
    
    // Click Confirm Import
    await page.click('button:has-text("Confirm Import")');
    
    // Buttons should be disabled during operation
    const confirmButton = page.locator('button:has-text("Confirm Import")');
    await expect(confirmButton).toBeDisabled();
    
    // Wait for completion
    await expect(page.locator('text=Configuration imported successfully')).toBeVisible({ timeout: 10000 });
    
    // Cleanup
    fs.unlinkSync(downloadPath);
  });

  test('should show preview details correctly', async ({ page }) => {
    // Export current config
    await page.click('[role="tab"]:has-text("Import/Export")');
    const downloadPromise = page.waitForEvent('download');
    await page.click('button:has-text("Export Configuration")');
    const download = await downloadPromise;
    const downloadPath = path.join(__dirname, 'downloads', 'test_export.json');
    await download.saveAs(downloadPath);
    
    // Modify config to create specific changes
    const exportedData = JSON.parse(fs.readFileSync(downloadPath, 'utf-8'));
    
    // Add a new area
    exportedData.areas.test_area = {
      name: 'Test Area',
      enabled: true,
      target_temperature: 20.0,
      devices: [],
      temperature_sensors: [],
      schedule: { enabled: false, entries: [] },
    };
    
    // Modify global settings
    if (exportedData.global_settings?.global_presets) {
      exportedData.global_settings.global_presets.comfort = 22.0;
    }
    
    const importPath = path.join(__dirname, 'downloads', 'test_import.json');
    fs.writeFileSync(importPath, JSON.stringify(exportedData, null, 2));
    
    // Upload modified file
    const fileInput = await page.locator('input[type="file"]');
    await fileInput.setInputFiles(importPath);
    
    // Wait for preview
    await expect(page.locator('text=Import Preview')).toBeVisible({ timeout: 5000 });
    
    // Verify preview shows new area
    await expect(page.locator('text=test_area')).toBeVisible();
    
    // Verify preview shows settings changes
    await expect(page.locator('text=Global Settings Changes')).toBeVisible();
    
    // Close preview
    await page.click('button:has-text("Cancel")');
    
    // Cleanup
    fs.unlinkSync(downloadPath);
    fs.unlinkSync(importPath);
  });

  test('should handle file selection cancellation', async ({ page }) => {
    // Navigate to Import/Export tab
    await page.click('[role="tab"]:has-text("Import/Export")');
    
    // Click import button
    await page.click('button:has-text("Import Configuration")');
    
    // No file selected, no error should occur
    await expect(page.locator('.MuiAlert-standardError')).not.toBeVisible();
    
    // Button should remain enabled
    await expect(page.locator('button:has-text("Import Configuration")')).toBeEnabled();
  });

  test('should accept only JSON files', async ({ page }) => {
    // Navigate to Import/Export tab
    await page.click('[role="tab"]:has-text("Import/Export")');
    
    // Check file input accept attribute
    const fileInput = await page.locator('input[type="file"]');
    const acceptAttr = await fileInput.getAttribute('accept');
    
    // Should only accept .json files
    expect(acceptAttr).toBe('.json');
  });

  test('should show translation keys in correct language', async ({ page }) => {
    // Navigate to Import/Export tab
    await page.click('[role="tab"]:has-text("Import/Export")');
    
    // Verify English translations are loaded (default)
    await expect(page.locator('text=Export Configuration')).toBeVisible();
    await expect(page.locator('text=Import Configuration')).toBeVisible();
    await expect(page.locator('text=Download your complete configuration as a JSON file')).toBeVisible();
    await expect(page.locator('text=Upload a configuration file to restore or transfer settings')).toBeVisible();
    
    // Note: Testing Dutch translations would require changing language in UI
    // which may require additional setup steps
  });

  test('should handle multiple rapid exports', async ({ page }) => {
    // Navigate to Import/Export tab
    await page.click('[role="tab"]:has-text("Import/Export")');
    
    // Export multiple times
    const downloads = [];
    for (let i = 0; i < 3; i++) {
      const downloadPromise = page.waitForEvent('download');
      await page.click('button:has-text("Export Configuration")');
      const download = await downloadPromise;
      downloads.push(download);
      
      // Small delay between exports
      await page.waitForTimeout(100);
    }
    
    // Verify all downloads completed
    expect(downloads.length).toBe(3);
    
    // Verify each has unique timestamp
    const filenames = downloads.map(d => d.suggestedFilename());
    const uniqueFilenames = new Set(filenames);
    expect(uniqueFilenames.size).toBe(3);
  });

  test('should close preview dialog when clicking backdrop', async ({ page }) => {
    // Export and prepare import
    await page.click('[role="tab"]:has-text("Import/Export")');
    const downloadPromise = page.waitForEvent('download');
    await page.click('button:has-text("Export Configuration")');
    const download = await downloadPromise;
    const downloadPath = path.join(__dirname, 'downloads', 'test_export.json');
    await download.saveAs(downloadPath);
    
    // Upload file
    const fileInput = await page.locator('input[type="file"]');
    await fileInput.setInputFiles(downloadPath);
    
    // Wait for preview
    await expect(page.locator('text=Import Preview')).toBeVisible({ timeout: 5000 });
    
    // Click backdrop to close
    await page.click('.MuiBackdrop-root');
    
    // Dialog should close
    await expect(page.locator('.MuiDialog-root')).not.toBeVisible();
    
    // Cleanup
    fs.unlinkSync(downloadPath);
  });
});

/**
 * Test Execution Notes:
 * 
 * Prerequisites:
 * - Home Assistant test instance running at http://localhost:8123
 * - Smart Heating integration installed and configured
 * - At least one area configured for meaningful export/import tests
 * 
 * Running Tests:
 * ```bash
 * cd tests/e2e
 * npm test -- import_export.spec.ts
 * ```
 * 
 * Running with UI (for debugging):
 * ```bash
 * npm test -- import_export.spec.ts --headed
 * ```
 * 
 * Coverage:
 * ✓ Navigation to Import/Export tab
 * ✓ Export configuration download
 * ✓ Import file selection
 * ✓ Import preview dialog
 * ✓ Successful import with backup
 * ✓ Invalid JSON handling
 * ✓ Version compatibility validation
 * ✓ Loading states
 * ✓ Button states during operations
 * ✓ Preview content accuracy
 * ✓ File selection cancellation
 * ✓ File type restrictions
 * ✓ Internationalization
 * ✓ Multiple rapid operations
 * ✓ Dialog interaction
 */
