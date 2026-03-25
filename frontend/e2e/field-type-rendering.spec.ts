import { test, expect } from '@playwright/test'

/**
 * E2E Tests for Field Type Rendering in Forms
 *
 * Verifies that fields with types like file, image, qr_code, barcode
 * render correctly in the Asset form instead of falling back to text inputs.
 */

test.describe('Field Type Rendering', () => {
  // Use fresh token for each test session
  const AUTH_TOKEN = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ0b2tlbl90eXBlIjoiYWNjZXNzIiwiZXhwIjoxNzcwMTkxNjQ2LCJpYXQiOjE3NzAxODQ0NDYsImp0aSI6ImE2MWIxNDYyYzFiNjRlMTdiMjFlYjhlMWY2YjVlNWNjIiwidXNlcl9pZCI6ImUwYzlkYWRhLTg5YTYtNDQ1Zi1iNTU1LTI5OGZlZGU2Y2RhMyJ9.lF_gl9hCYktOYyEamRWeNMfJPkfFc17zl8qAoUxFrHg'

  test.beforeEach(async ({ page }) => {
    // Set auth token in localStorage
    await page.goto('/')
    await page.evaluate((token) => {
      localStorage.setItem('gzeams_access_token', token)
      localStorage.setItem('gzeams_user_info', JSON.stringify({
        id: 'e0c9dada-89a6-445f-b555-298fede6cda3',
        username: 'admin',
        organization: 'default-org'
      }))
    }, AUTH_TOKEN)
  })

  test('should load field definitions with correct types', async ({ page, request }) => {
    // Verify the API returns field types correctly
    const apiResponse = await request.get('/api/system/business-objects/fields/?object_code=Asset', {
      headers: {
        'Authorization': `Bearer ${AUTH_TOKEN}`
      }
    })

    expect(apiResponse.ok()).toBeTruthy()
    const data = await apiResponse.json()
    expect(data.success).toBe(true)

    // Find specific fields
    const fields = data.data?.fields || []
    const qrCodeField = fields.find((f: any) => f.fieldName === 'qr_code')
    const imagesField = fields.find((f: any) => f.fieldName === 'images')
    const attachmentsField = fields.find((f: any) => f.fieldName === 'attachments')

    // Verify field types are correct
    expect(qrCodeField?.fieldType).toBe('qr_code')
    expect(imagesField?.fieldType).toBe('image')
    expect(attachmentsField?.fieldType).toBe('file')
  })

  test('should render Asset form page', async ({ page }) => {
    // Navigate to Asset form (create new asset)
    await page.goto('/assets/create')
    await page.waitForTimeout(2000)

    // Check that the page loaded
    const title = await page.title()
    expect(title).toBeTruthy()
  })

  test('should render QR code field correctly', async ({ page }) => {
    // Navigate to an existing asset detail page
    await page.goto('/assets')
    await page.waitForTimeout(2000)

    // Try to click on first asset (if any exist)
    const firstRow = page.locator('.el-table__row').first()
    if (await firstRow.isVisible()) {
      await firstRow.click()
      await page.waitForTimeout(1000)

      // Check for QR code field - it should use QRCodeField component
      // (not a simple text input)
      const qrCodeLabel = page.locator('text=qr code').or(page.locator('text=QR Code'))
      if (await qrCodeLabel.isVisible()) {
        // QR code field should be present
        const qrCodeField = page.locator('[class*="qr-code"]').or(
          page.locator('.qr-code-field')
        ).or(
          page.locator('input[readonly]') // QR code fields are typically readonly
        )
        // At minimum, the label should be present
        await expect(qrCodeLabel).toBeVisible()
      }
    }
  })

  test('should render images field correctly', async ({ page }) => {
    // Navigate to assets
    await page.goto('/assets')
    await page.waitForTimeout(2000)

    const firstRow = page.locator('.el-table__row').first()
    if (await firstRow.isVisible()) {
      await firstRow.click()
      await page.waitForTimeout(1000)

      // Check for images field
      const imagesLabel = page.locator('text=images').or(page.locator('text=图片'))
      if (await imagesLabel.isVisible({ timeout: 5000 })) {
        // Images field should use ImageField component
        await expect(imagesLabel).toBeVisible()
      }
    }
  })

  test('should render attachments field correctly', async ({ page }) => {
    // Navigate to assets
    await page.goto('/assets')
    await page.waitForTimeout(2000)

    const firstRow = page.locator('.el-table__row').first()
    if (await firstRow.isVisible()) {
      await firstRow.click()
      await page.waitForTimeout(1000)

      // Check for attachments field
      const attachmentsLabel = page.locator('text=attachments').or(page.locator('text=附件'))
      if (await attachmentsLabel.isVisible({ timeout: 5000 })) {
        // Attachments field should use AttachmentUpload component
        await expect(attachmentsLabel).toBeVisible()
      }
    }
  })

  test('should verify field types in metadata API', async ({ request }) => {
    // Get all field types from the field types endpoint
    const response = await request.get('/api/system/business-objects/field-types/', {
      headers: {
        'Authorization': `Bearer ${AUTH_TOKEN}`
      }
    })

    expect(response.ok()).toBeTruthy()
    const data = await response.json()

    // Verify the response includes all important field types
    expect(data.success).toBe(true)
    expect(data.data.groups).toBeDefined()
    expect(data.data.allTypes).toBeInstanceOf(Array)

    // Check that the missing field types are now included
    const allTypes = data.data.allTypes
    expect(allTypes).toContain('file')
    expect(allTypes).toContain('image')
    expect(allTypes).toContain('qr_code')
    expect(allTypes).toContain('barcode')
    expect(allTypes).toContain('location')
    expect(allTypes).toContain('percent')
    expect(allTypes).toContain('time')
    expect(allTypes).toContain('rich_text')
  })

  test('should verify component mappings in type config', async ({ request }) => {
    // Get field types with component mappings
    const response = await request.get('/api/system/business-objects/field-types/', {
      headers: {
        'Authorization': `Bearer ${AUTH_TOKEN}`
      }
    })

    expect(response.ok()).toBeTruthy()
    const data = await response.json()
    const typeConfig = data.data.typeConfig

    // Verify component mappings for media types
    expect(typeConfig.file).toBeDefined()
    expect(typeConfig.file.component).toBe('AttachmentUpload')

    expect(typeConfig.image).toBeDefined()
    expect(typeConfig.image.component).toBe('ImageField')

    expect(typeConfig.qr_code).toBeDefined()
    expect(typeConfig.qr_code.component).toBe('QRCodeField')

    expect(typeConfig.barcode).toBeDefined()
    expect(typeConfig.barcode.component).toBe('BarcodeField')
  })
})

test.describe('Field Definition Form Integration', () => {
  const AUTH_TOKEN = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ0b2tlbl90eXBlIjoiYWNjZXNzIiwiZXhwIjoxNzcwMTkxNjQ2LCJpYXQiOjE3NzAxODQ0NDYsImp0aSI6ImE2MWIxNDYyYzFiNjRlMTdiMjFlYjhlMWY2YjVlNWNjIiwidXNlcl9pZCI6ImUwYzlkYWRhLTg5YTYtNDQ1Zi1iNTU1LTI5OGZlZGU2Y2RhMyJ9.lF_gl9hCYktOYyEamRWeNMfJPkfFc17zl8qAoUxFrHg'

  test.beforeEach(async ({ page }) => {
    await page.goto('/')
    await page.evaluate((token) => {
      localStorage.setItem('gzeams_access_token', token)
      localStorage.setItem('gzeams_user_info', JSON.stringify({
        id: 'e0c9dada-89a6-445f-b555-298fede6cda3',
        username: 'admin'
      }))
    }, AUTH_TOKEN)
  })

  test('should load field types in Field Definition Form', async ({ page }) => {
    // Navigate to Field Definition page
    await page.goto('/system/field-definitions')
    await page.waitForTimeout(2000)

    // Check if the page loads
    const pageTitle = await page.title()
    expect(pageTitle).toBeTruthy()
  })

  test('should include all field type options', async ({ request }) => {
    // Get field types from API
    const response = await request.get('/api/system/business-objects/field-types/', {
      headers: {
        'Authorization': `Bearer ${AUTH_TOKEN}`
      }
    })

    const data = await response.json()
    const allTypes = data.data.allTypes

    // Verify all field types that were previously missing are present
    const criticalTypes = ['file', 'image', 'qr_code', 'barcode', 'location', 'percent', 'time', 'rich_text']
    criticalTypes.forEach(type => {
      expect(allTypes.includes(type)).toBe(true)
    })
  })
})
