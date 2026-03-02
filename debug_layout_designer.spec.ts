import { test, expect } from '@playwright/test'

/**
 * Debug test for Layout Designer
 * Investigates why layout designer shows example text instead of proper layout
 */

const BASE_URL = process.env.BASE_URL || 'http://localhost:5175'
const API_BASE = process.env.API_BASE || 'http://localhost:8000/api'

// Test token - you may need to update this
const TOKEN = process.env.TOKEN || 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ0b2tlbl90eXBlIjoiYWNjZXNzIiwiZXhwIjoxNzcwMjc4MzE2LCJpYXQiOjE3NzAyNzExMTYsImp0aSI6IjdjZDMxNjU1NzA2NDRkYWRiMDRmNmFhY2NmZWY0ZTAwIiwidXNlcl9pZCI6ImUwYzlkYWRhLTg5YTYtNDQ1Zi1iNTU1LTI5OGZlZGU2Y2RhMyJ9.2p7hqvBCvfVzIwARF1235N9EP5TbcRyQ3RBF7NGAP_s'

test.describe('Layout Designer Debug', () => {
  let authToken: string = TOKEN

  test.beforeAll(async ({ request }) => {
    // Login if no token provided
    if (!authToken) {
      const loginResponse = await request.post(`${API_BASE}/auth/login/`, {
        data: {
          username: 'admin',
          password: 'admin123'
        }
      })
      const loginData = await loginResponse.json()
      authToken = loginData.data?.access_token || loginData.data?.token || loginData.access_token || ''
      console.log('Auth Token:', authToken.substring(0, 20) + '...')
    }
  })

  test('check layout list and layout config', async ({ request }) => {
    // Headers for authenticated requests
    const headers = {
      'Authorization': `Bearer ${authToken}`,
      'X-Organization-ID': '1'
    }

    // 1. Get the list of layouts
    console.log('\n=== Fetching Layout List ===')
    const layoutsResponse = await request.get(`${API_BASE}/system/page-layouts/`, { headers })
    const layoutsData = await layoutsResponse.json()

    console.log('Layouts response:', JSON.stringify(layoutsData, null, 2).substring(0, 2000))

    // Find first layout
    const firstLayout = layoutsData.data?.results?.[0]
    expect(firstLayout).toBeTruthy()

    console.log('\n=== First Layout ===')
    console.log('Layout ID:', firstLayout.id)
    console.log('Layout Name:', firstLayout.layout_name)
    console.log('Layout Config:', JSON.stringify(firstLayout.layout_config, null, 2).substring(0, 2000))

    // 2. Get detailed layout info
    console.log('\n=== Fetching Layout Detail ===')
    const detailResponse = await request.get(`${API_BASE}/system/page-layouts/${firstLayout.id}/`, { headers })
    const detailData = await detailResponse.json()

    console.log('Detail response:', JSON.stringify(detailData, null, 2).substring(0, 3000))
    console.log('Layout Config sections:', detailData.data?.layout_config?.sections?.length || 0)

    // 3. Check if layout has sections
    const sections = detailData.data?.layout_config?.sections || []
    console.log('\n=== Sections Analysis ===')
    sections.forEach((section: any, idx: number) => {
      console.log(`Section ${idx}:`, section.type, '-', section.title)
      console.log('  Fields:', section.fields?.length || 0)
      if (section.fields) {
        section.fields.forEach((field: any) => {
          console.log(`    - ${field.label || field.name || 'N/A'} (${field.field_code || field.field || field.code || 'N/A'})`)
        })
      }
    })

    // 4. Get all available fields for Asset object
    console.log('\n=== Fetching Asset Fields ===')
    const fieldsResponse = await request.get(`${API_BASE}/system/business-objects/fields/?object_code=Asset&context=form`, { headers })
    const fieldsData = await fieldsResponse.json()

    const allFields = fieldsData.data?.editableFields || []
    console.log(`Total editable fields for Asset: ${allFields.length}`)

    // List first 20 fields
    allFields.slice(0, 20).forEach((field: any, idx: number) => {
      console.log(`  ${idx + 1}. ${field.name || field.label || 'N/A'} (${field.code || field.field_code || 'N/A'}) - ${field.fieldType || 'N/A'}`)
    })
    if (allFields.length > 20) {
      console.log(`  ... and ${allFields.length - 20} more fields`)
    }

    // 5. Compare: which fields are in layout vs available
    const layoutFields = new Set<string>()
    sections.forEach((section: any) => {
      if (section.fields) {
        section.fields.forEach((field: any) => {
          const fieldCode = field.field_code || field.field || field.code
          if (fieldCode) layoutFields.add(fieldCode)
        })
      }
    })

    const availableFields = new Set<string>()
    allFields.forEach((field: any) => {
      const fieldCode = field.code || field.field_code
      if (fieldCode) availableFields.add(fieldCode)
    })

    console.log('\n=== Field Comparison ===')
    console.log(`Fields in layout: ${layoutFields.size}`)
    console.log(`Fields available: ${availableFields.size}`)

    const notInLayout = [...availableFields].filter(f => !layoutFields.has(f))
    console.log(`\nFields available but NOT in layout (${notInLayout.length}):`)
    notInLayout.slice(0, 20).forEach(f => console.log(`  - ${f}`))
    if (notInLayout.length > 20) {
      console.log(`  ... and ${notInLayout.length - 20} more`)
    }
  })

  test('take screenshot of layout designer', async ({ page }) => {
    // Navigate to layout list page
    await page.goto(`${BASE_URL}/system/layouts`)

    // Wait for page to load
    await page.waitForLoadState('networkidle')
    await page.waitForTimeout(2000)

    // Take screenshot of layout list
    await page.screenshot({ path: 'test-screenshots/layout-list.png' })

    console.log('Screenshot saved to test-screenshots/layout-list.png')

    // Check if there are any layouts in the table
    const layoutButtons = await page.locator('button:has-text("设计")').count()
    console.log('Number of design buttons:', layoutButtons)

    if (layoutButtons > 0) {
      // Click the first "设计" button
      await page.locator('button:has-text("设计")').first().click()
      await page.waitForTimeout(3000)

      // Take screenshot of layout designer
      await page.screenshot({ path: 'test-screenshots/layout-designer.png', fullPage: true })
      console.log('Screenshot saved to test-screenshots/layout-designer.png')

      // Check for field panel
      const fieldPanel = await page.locator('.field-panel').isVisible()
      console.log('Field panel visible:', fieldPanel)

      // Check for canvas area
      const canvasArea = await page.locator('.canvas-area').isVisible()
      console.log('Canvas area visible:', canvasArea)

      // Count fields in canvas
      const canvasFields = await page.locator('.canvas-area .field-renderer').count()
      console.log('Fields in canvas:', canvasFields)

      // Get text content of first few fields
      for (let i = 0; i < Math.min(canvasFields, 5); i++) {
        const fieldEl = await page.locator('.canvas-area .field-renderer').nth(i)
        const text = await fieldEl.textContent()
        console.log(`Field ${i} text:`, text.substring(0, 100))
      }
    }
  })
})
