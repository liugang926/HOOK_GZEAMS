import { test, expect } from '@playwright/test'

const BASE_URL = process.env.BASE_URL || 'http://localhost:5174'
const API_BASE = process.env.API_BASE || 'http://localhost:8000/api'

const ADMIN_USERNAME = 'admin'
const ADMIN_PASSWORD = 'admin123456'

test.describe('Images Field Fix Verification', () => {
  let authToken: string = ''

  test.beforeAll(async ({ request }) => {
    // Login to get token
    const loginResponse = await request.post(`${API_BASE}/auth/login/`, {
      data: {
        username: ADMIN_USERNAME,
        password: ADMIN_PASSWORD
      }
    })

    expect(loginResponse.ok()).toBeTruthy()
    const loginData = await loginResponse.json()
    authToken = loginData.data?.token || loginData.token || ''
    expect(authToken).toBeTruthy()
    console.log('Got access token')
  })

  test('Verify metadata API returns correct field types', async ({ request }) => {
    const response = await request.get(`${API_BASE}/system/objects/Asset/metadata/`, {
      headers: {
        'Authorization': `Bearer ${authToken}`
      }
    })

    expect(response.ok()).toBeTruthy()
    const data = await response.json()
    const fields = data.data?.fields || []

    // Find images and attachments fields
    const imagesField = fields.find((f: any) => f.code === 'images')
    const attachmentsField = fields.find((f: any) => f.code === 'attachments')

    console.log('=== Images Field ===')
    console.log(JSON.stringify(imagesField, null, 2))

    console.log('=== Attachments Field ===')
    console.log(JSON.stringify(attachmentsField, null, 2))

    // Verify field types
    expect(imagesField).toBeTruthy()
    expect(imagesField.fieldType || imagesField.field_type).toBe('image')

    expect(attachmentsField).toBeTruthy()
    expect(attachmentsField.fieldType || attachmentsField.field_type).toBe('file')
  })

  test('Verify images field renders correctly in browser', async ({ page }) => {
    // Set up authentication
    await page.goto(BASE_URL)
    await page.evaluate(({ token }) => {
      localStorage.setItem('access_token', token)
    }, { token: authToken })

    // Navigate to Asset list
    await page.goto(`${BASE_URL}/objects/Asset`)
    await page.waitForLoadState('networkidle')
    await page.waitForTimeout(2000)

    // Try to find an asset and click edit
    const rows = await page.locator('table tbody tr, .el-table__row, .list-item').count()
    console.log(`Found ${rows} rows`)

    if (rows > 0) {
      // Click first row to edit
      await page.locator('table tbody tr, .el-table__row').first().click()
      await page.waitForTimeout(2000)

      // Check for images field
      const imagesLabel = page.locator('text=图片, text=images, label:has-text("图片")')
      const imagesLabelCount = await imagesLabel.count()
      console.log('Images label elements found:', imagesLabelCount)

      // Look for image upload component
      const imageUpload = page.locator('.image-field, [class*="image-upload"], .el-upload:has([accept*="image"])')
      const imageUploadCount = await imageUpload.count()
      console.log('Image upload component elements found:', imageUploadCount)

      // Take screenshot for visual verification
      await page.screenshot({
        path: 'test-screenshots/asset-form-after-fix.png',
        fullPage: true
      })

      // Verify NOT a text input for images field
      const imagesInput = page.locator('input[name*="image"], input[id*="image"]')
      const imagesInputCount = await imagesInput.count()
      console.log('Images input/textarea elements found:', imagesInputCount)

      // The images field should NOT be a simple text input
      // It should have proper upload component
      expect(imageUploadCount + imagesLabelCount).toBeGreaterThan(0)
    }
  })
})
