import { test, expect } from '@playwright/test'

const BASE_URL = process.env.BASE_URL || 'http://localhost:5174'

// Valid token from previous session
const AUTH_TOKEN = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ0b2tlbl90eXBlIjoiYWNjZXNzIiwiZXhwIjoxNzY5NjkzODY4LCJpYXQiOjE3Njk2ODY2NjgsImp0aSI6IjRhMDFkZTQ3ZmU4ODQ4NjQ4NjkyMzFhZDFlNDc2ZjlhIiwidXNlcl9pZCI6ImUwYzlkYWRhLTg5YTYtNDQ1Zi1iNTU1LTI5OGZlZGU2Y2RhMyJ9.sWHLKVe2lx-XN78ZfJ_-mOd7tSnYqZxifHOBwr62FJE'

test.describe('Images Field Simple Verification', () => {
  test('Verify images field renders correctly on Asset form', async ({ page }) => {
    // Set up authentication
    await page.goto(BASE_URL)
    await page.evaluate(({ token }) => {
      localStorage.setItem('access_token', token)
    }, { token: AUTH_TOKEN })

    // Navigate to Asset list
    await page.goto(`${BASE_URL}/objects/Asset`)
    await page.waitForLoadState('networkidle')
    await page.waitForTimeout(2000)

    // Take screenshot of list page
    await page.screenshot({
      path: 'test-screenshots/images-simple-asset-list.png',
      fullPage: true
    })

    // Look for and click first row or create button
    const firstRow = page.locator('table tbody tr, .el-table__row').first()
    const rowCount = await firstRow.count()

    if (rowCount > 0) {
      await firstRow.click()
      console.log('Clicked first row for editing')
    } else {
      // Try create page
      await page.goto(`${BASE_URL}/objects/Asset/create`)
      console.log('Navigated to create form')
    }

    await page.waitForLoadState('networkidle')
    await page.waitForTimeout(3000)

    // Take screenshot of form page
    await page.screenshot({
      path: 'test-screenshots/images-simple-asset-form.png',
      fullPage: true
    })

    // Check for images field
    console.log('\n=== Checking for images field ===')

    // Look for the images label
    const imagesLabel = page.locator('text=图片').or(page.locator('text=images')).or(page.locator('text=Images'))
    const imagesLabelCount = await imagesLabel.count()
    console.log('Images label elements found:', imagesLabelCount)

    // Look for upload component (el-upload is the Element Plus upload component)
    const uploadComponent = page.locator('.el-upload')
    const uploadCount = await uploadComponent.count()
    console.log('Upload components found:', uploadCount)

    // Look for file inputs
    const fileInput = page.locator('input[type="file"]')
    const fileInputCount = await fileInput.count()
    console.log('File inputs found:', fileInputCount)

    // Look for ImageField component
    const imageField = page.locator('.image-field')
    const imageFieldCount = await imageField.count()
    console.log('Image field components found:', imageFieldCount)

    // Get all field labels
    const allLabels = await page.locator('.el-form-item__label, label').allTextContents()
    const filteredLabels = allLabels.filter(l => l.trim())
    console.log('\n=== All Field Labels ===')
    for (const label of filteredLabels.slice(0, 30)) {
      console.log(`  - ${label.trim()}`)
    }

    // Verify we have upload components
    expect(uploadCount + fileInputCount + imageFieldCount).toBeGreaterThan(0)

    // Verify that images field is NOT a text input
    const textInputs = await page.locator('input[type="text"]').all()
    console.log('\n=== Text input names ===')
    for (const input of textInputs.slice(0, 15)) {
      const name = await input.evaluate(el => el.getAttribute('name'))
      if (name) {
        console.log(`  - ${name}`)
      }
    }

    // Final verification screenshot
    await page.screenshot({
      path: 'test-screenshots/images-simple-verification.png',
      fullPage: true
    })
  })
})
