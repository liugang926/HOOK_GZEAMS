import { test, expect } from '@playwright/test'

/**
 * E2E Test to inspect actual field rendering in Asset edit/detail pages
 *
 * This test opens the browser, navigates to Asset pages,
 * and inspects how fields are actually being rendered.
 */

test.describe('Field Rendering Inspection', () => {
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

  test('should inspect asset detail page field rendering', async ({ page }) => {
    // Navigate to Asset list
    await page.goto('/assets')
    await page.waitForLoadState('networkidle')
    await page.waitForTimeout(2000)

    console.log('=== INSPECTING ASSET LIST PAGE ===')

    // Get first row
    const firstRow = page.locator('.el-table__body .el-table__row').first()
    const rowCount = await firstRow.count()
    console.log(`Found ${rowCount} rows in the table`)

    if (rowCount > 0) {
      // Click first row to view detail
      await firstRow.click()
      await page.waitForTimeout(2000)

      console.log('\n=== INSPECTING ASSET DETAIL PAGE ===')

      // Take screenshot
      await page.screenshot({ path: 'test-results/asset-detail.png', fullPage: true })
      console.log('Screenshot saved to test-results/asset-detail.png')

      // Get all field labels
      const labels = await page.locator('.field-label, .el-form-item__label, .el-descriptions__label').allTextContents()
      console.log(`\nFound ${labels.length} field labels:`)
      labels.slice(0, 15).forEach(label => console.log(`  - ${label}`))

      // Check for specific field types
      const qrCodeElements = await page.locator('[class*="qr-code"], [class*="qrcode"]').count()
      console.log(`\nQR code elements: ${qrCodeElements}`)

      const imageElements = await page.locator('img, [class*="image"], .el-image').count()
      console.log(`Image elements: ${imageElements}`)

      const fileUploadElements = await page.locator('[class*="upload"], [class*="attachment"]').count()
      console.log(`File upload elements: ${fileUploadElements}`)

      const textInputs = await page.locator('input[type="text"]').count()
      console.log(`Text input elements: ${textInputs}`)

      // Get page HTML for analysis
      const bodyText = await page.locator('body').textContent()
      console.log('\n=== PAGE CONTENT ANALYSIS ===')
      console.log('Contains "qr_code":', bodyText.includes('qr_code'))
      console.log('Contains "二维码":', bodyText.includes('二维码'))
      console.log('Contains "images":', bodyText.includes('images'))
      console.log('Contains "图片":', bodyText.includes('图片'))
      console.log('Contains "attachments":', bodyText.includes('attachments'))
      console.log('Contains "附件":', bodyText.includes('附件'))
    }
  })

  test('should inspect asset edit page field rendering', async ({ page }) => {
    // Navigate to Asset list
    await page.goto('/assets')
    await page.waitForLoadState('networkidle')
    await page.waitForTimeout(1000)

    const firstRow = page.locator('.el-table__body .el-table__row').first()
    const rowCount = await firstRow.count()

    if (rowCount > 0) {
      // Click first row
      await firstRow.click()
      await page.waitForTimeout(1000)

      // Look for edit button
      const editButton = page.locator('button:has-text("编辑"), button:has-text("Edit")').first()
      const editButtonCount = await editButton.count()

      if (editButtonCount > 0) {
        await editButton.click()
        await page.waitForTimeout(2000)

        console.log('\n=== INSPECTING ASSET EDIT PAGE ===')

        // Take screenshot
        await page.screenshot({ path: 'test-results/asset-edit.png', fullPage: true })
        console.log('Screenshot saved to test-results/asset-edit.png')

        // Get all form items
        const formItems = page.locator('.el-form-item')
        const formItemCount = await formItems.count()
        console.log(`\nFound ${formItemCount} form items`)

        // Inspect first 20 form items
        for (let i = 0; i < Math.min(20, formItemCount); i++) {
          const item = formItems.nth(i)

          const label = await item.locator('.el-form-item__label').textContent() || '(no label)'

          // Check for different input types
          const hasTextInput = await item.locator('input[type="text"]').count() > 0
          const hasNumberInput = await item.locator('input[type="number"]').count() > 0
          const hasSelect = await item.locator('el-select, .el-select').count() > 0
          const hasTextarea = await item.locator('textarea').count() > 0
          const hasUpload = await item.locator('[class*="upload"]').count() > 0
          const hasQRCode = await item.locator('[class*="qr"]').count() > 0
          const hasImage = await item.locator('[class*="image"], .el-image').count() > 0

          console.log(`  ${i + 1}. ${label.trim()}:`)
          console.log(`     - text input: ${hasTextInput}`)
          console.log(`     - number input: ${hasNumberInput}`)
          console.log(`     - select: ${hasSelect}`)
          console.log(`     - textarea: ${hasTextarea}`)
          console.log(`     - upload: ${hasUpload}`)
          console.log(`     - qr code: ${hasQRCode}`)
          console.log(`     - image: ${hasImage}`)
        }

        // Check URL to understand which page we're on
        const url = page.url()
        console.log(`\nCurrent URL: ${url}`)

        // Check if this is using DynamicFormPage or AssetForm component
        const hasDynamicForm = await page.locator('.dynamic-form').count() > 0
        const hasBaseForm = await page.locator('.base-form').count() > 0
        console.log(`Has .dynamic-form: ${hasDynamicForm}`)
        console.log(`Has .base-form: ${hasBaseForm}`)
      }
    }
  })

  test('should check API response for field metadata', async ({ request }) => {
    // Check the metadata API to see what field types are returned
    const response = await request.get('/api/system/objects/Asset/fields/', {
      headers: {
        'Authorization': `Bearer ${AUTH_TOKEN}`
      }
    })

    expect(response.ok()).toBeTruthy()

    const data = await response.json()
    console.log('\n=== API FIELD METADATA ===')
    console.log('Response success:', data.success)

    if (data.data && data.data.fields) {
      const fields = data.data.fields
      console.log(`\nTotal fields: ${fields.length}`)

      // Find special field types
      const specialFields = fields.filter((f: any) =>
        ['file', 'image', 'qr_code', 'qrcode', 'barcode', 'location', 'percent', 'time', 'rich_text']
        .includes(f.fieldType || f.field_type)
      )

      console.log(`\nSpecial field types found: ${specialFields.length}`)
      specialFields.forEach((f: any) => {
        console.log(`  - ${f.fieldName || f.field_code || f.code}: ${f.fieldType || f.field_type}`)
      })

      // Print first 10 fields
      console.log('\n=== FIRST 10 FIELDS ===')
      fields.slice(0, 10).forEach((f: any) => {
        const name = f.fieldName || f.field_code || f.code || 'unnamed'
        const type = f.fieldType || f.field_type || 'unknown'
        const displayName = f.displayName || f.name || f.label || ''
        console.log(`  ${name}: ${type} (${displayName})`)
      })
    }
  })
})
