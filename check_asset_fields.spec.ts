import { test, expect } from '@playwright/test'

const BASE_URL = process.env.BASE_URL || 'http://localhost:5174'
const API_BASE = process.env.API_BASE || 'http://localhost:8000/api'

// Use a valid token from previous session
const TOKEN = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ0b2tlbl90eXBlIjoiYWNjZXNzIiwiZXhwIjoxNzY5NjkzODY4LCJpYXQiOjE3Njk2ODY2NjgsImp0aSI6IjRhMDFkZTQ3ZmU4ODQ4NjQ4NjkyMzFhZDFlNDc2ZjlhIiwidXNlcl9pZCI6ImUwYzlkYWRhLTg5YTYtNDQ1Zi1iNTU1LTI5OGZlZGU2Y2RhMyJ9.sWHLKVe2lx-XN78ZfJ_-mOd7tSnYqZxifHOBwr62FJE'

test.describe('Asset Field Type Analysis', () => {
  test('check API returns correct field types for Asset', async ({ request }) => {
    // First, get the metadata from the API
    const context = await request.newContext({
      extraHTTPHeaders: {
        'Authorization': `Bearer ${TOKEN}`
      }
    })

    const response = await context.get(`${API_BASE}/system/business-objects/fields/?object_code=Asset`)

    console.log('=== API Response Status ===', response.status())

    const data = await response.json()
    console.log('=== API Response Structure ===')
    console.log(JSON.stringify(data, null, 2).substring(0, 5000))

    // Find images and attachments fields
    const fields = data.data?.fields || data.fields || []
    const imagesField = fields.find((f: any) =>
      f.fieldName === 'images' || f.field_name === 'images' || f.code === 'images'
    )
    const attachmentsField = fields.find((f: any) =>
      f.fieldName === 'attachments' || f.field_name === 'attachments' || f.code === 'attachments'
    )

    console.log('=== Images Field ===')
    console.log(JSON.stringify(imagesField, null, 2))
    console.log('=== Attachments Field ===')
    console.log(JSON.stringify(attachmentsField, null, 2))

    expect(imagesField).toBeTruthy()
    expect(imagesField?.fieldType || imagesField?.field_type).toBe('image')
    expect(attachmentsField?.fieldType || attachmentsField?.field_type).toBe('file')
  })

  test('check dynamic form page field rendering', async ({ page }) => {
    // Set up authentication
    await page.goto(BASE_URL)

    // Set token in localStorage
    await page.evaluate((token) => {
      localStorage.setItem('access_token', token)
      localStorage.setItem('user_info', JSON.stringify({
        id: 'e0c9dada-89a6-445f-b555-298fede6cda3',
        username: 'admin',
        email: 'admin@example.com'
      }))
    }, TOKEN)

    // Navigate to dynamic asset list page
    await page.goto(`${BASE_URL}/objects/Asset`)
    await page.waitForLoadState('networkidle')

    // Wait for list to load
    await page.waitForTimeout(2000)

    // Take screenshot of list page
    await page.screenshot({ path: 'test-screenshots/asset-list.png' })

    // Try to find and click an edit button (first row)
    const editButton = page.locator('button:has-text("编辑"), .el-button:has-text("Edit")').first()
    const editIcon = page.locator('.el-icon-edit, [class*="edit"]').first()

    if (await editButton.count() > 0) {
      await editButton.click()
    } else if (await editIcon.count() > 0) {
      await editIcon.first().click()
    } else {
      // Try to click on a row
      const firstRow = page.locator('table tbody tr, .el-table__row').first()
      await firstRow.click()
    }

    await page.waitForTimeout(2000)

    // Take screenshot of form page
    await page.screenshot({ path: 'test-screenshots/asset-form.png', fullPage: true })

    // Check for images and attachments fields
    const imagesLabel = page.locator('text=图片, text=images, text=Images')
    const attachmentsLabel = page.locator('text=附件, text=attachments, text=Attachments')
    const imagesField = page.locator('[class*="image"], [class*="Image"]')
    const attachmentsField = page.locator('[class*="attach"], [class*="Attach"], [class*="upload"], [class*="Upload"]')

    console.log('=== Page Elements Check ===')
    console.log('Images label found:', await imagesLabel.count())
    console.log('Attachments label found:', await attachmentsLabel.count())
    console.log('Images field components found:', await imagesField.count())
    console.log('Attachments field components found:', await attachmentsField.count())

    // Get all field labels on the form
    const allLabels = await page.locator('.el-form-item__label, label').allTextContents()
    console.log('=== All Field Labels ===')
    console.log(allLabels)

    // Get all input elements
    const inputs = await page.locator('input, textarea, .el-input').count()
    const fileInputs = await page.locator('input[type="file"]').count()
    console.log('Total inputs:', inputs)
    console.log('File inputs:', fileInputs)
  })
})
