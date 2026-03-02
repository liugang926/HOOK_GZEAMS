import { test, expect } from '@playwright/test'

const BASE_URL = process.env.BASE_URL || 'http://localhost:5174'
const API_BASE = process.env.API_BASE || 'http://localhost:8000/api'

// Admin credentials for login
const ADMIN_USERNAME = 'admin'
const ADMIN_PASSWORD = 'admin123456'

test.describe('Images Field Debug Analysis', () => {
  let authToken: string = ''

  test.beforeAll(async ({ request }) => {
    // Step 1: Login to get a valid token
    const loginResponse = await request.post(`${API_BASE}/auth/login/`, {
      data: {
        username: ADMIN_USERNAME,
        password: ADMIN_PASSWORD
      }
    })

    if (!loginResponse.ok()) {
      throw new Error(`Login failed: ${loginResponse.status()}`)
    }

    const loginData = await loginResponse.json()
    console.log('=== Login Response ===')
    console.log(JSON.stringify(loginData, null, 2))

    // Extract token from response (response format is {success: true, data: {token: "...", ...}})
    authToken = loginData.data?.token || loginData.token || loginData.access_token || ''
    if (!authToken) {
      throw new Error('No access token in login response')
    }
    console.log('Got access token:', authToken.substring(0, 50) + '...')
  })

  test('Step 1: Verify API returns correct field types', async ({ request }) => {
    const response = await request.get(`${API_BASE}/system/business-objects/fields/?object_code=Asset`, {
      headers: {
        'Authorization': `Bearer ${authToken}`
      }
    })

    console.log('=== API Response Status ===', response.status())
    expect(response.ok()).toBeTruthy()

    const data = await response.json()
    console.log('=== API Response Structure ===')
    console.log('Success:', data.success)
    console.log('Data keys:', Object.keys(data.data || {}))

    // Find images and attachments fields
    const fields = data.data?.fields || data.fields || []
    console.log('Total fields count:', fields.length)

    // Check both possible naming conventions
    const imagesField = fields.find((f: any) =>
      f.fieldName === 'images' || f.field_name === 'images' || f.code === 'images'
    )
    const attachmentsField = fields.find((f: any) =>
      f.fieldName === 'attachments' || f.field_name === 'attachments' || f.code === 'attachments'
    )

    console.log('\n=== Images Field ===')
    if (imagesField) {
      console.log('Found:', true)
      console.log('Field Name:', imagesField.fieldName || imagesField.field_name)
      console.log('Field Type:', imagesField.fieldType || imagesField.field_type)
      console.log('Django Field Type:', imagesField.djangoFieldType || imagesField.django_field_type)
      console.log('Full object:', JSON.stringify(imagesField, null, 2))
    } else {
      console.log('Found: false - searching for similar fields...')
      const imageRelated = fields.filter((f: any) => {
        const name = (f.fieldName || f.field_name || f.code || '').toLowerCase()
        return name.includes('image') || name.includes('img')
      })
      console.log('Image-related fields:', imageRelated.map((f: any) => ({
        name: f.fieldName || f.field_name,
        type: f.fieldType || f.field_type
      })))
    }

    console.log('\n=== Attachments Field ===')
    if (attachmentsField) {
      console.log('Found:', true)
      console.log('Field Name:', attachmentsField.fieldName || attachmentsField.field_name)
      console.log('Field Type:', attachmentsField.fieldType || attachmentsField.field_type)
      console.log('Django Field Type:', attachmentsField.djangoFieldType || attachmentsField.django_field_type)
    } else {
      console.log('Found: false - searching for similar fields...')
      const attachmentRelated = fields.filter((f: any) => {
        const name = (f.fieldName || f.field_name || f.code || '').toLowerCase()
        return name.includes('attachment') || name.includes('file')
      })
      console.log('Attachment-related fields:', attachmentRelated.map((f: any) => ({
        name: f.fieldName || f.field_name,
        type: f.fieldType || f.field_type
      })))
    }

    // List all fields for debugging
    console.log('\n=== All Field Names and Types ===')
    fields.forEach((f: any) => {
      console.log(`  ${(f.fieldName || f.field_name || f.code || '').padEnd(25)} : ${f.fieldType || f.field_type || 'unknown'}`)
    })
  })

  test('Step 2: Navigate to Asset list and take screenshot', async ({ page }) => {
    // Set up authentication by storing token
    await page.goto(BASE_URL)
    await page.evaluate(({ token }) => {
      localStorage.setItem('access_token', token)
    }, { token: authToken })

    // Navigate to Asset list
    await page.goto(`${BASE_URL}/objects/Asset`)
    await page.waitForLoadState('networkidle')

    // Take screenshot
    await page.screenshot({
      path: 'test-screenshots/asset-list-page.png',
      fullPage: true
    })

    // Get page title and URL
    console.log('Current URL:', page.url())
    console.log('Page title:', await page.title())

    // Look for data loaded indicators
    const hasTable = await page.locator('table, .el-table').count() > 0
    const hasLoading = await page.locator('.is-loading, [class*="loading"]').count() > 0

    console.log('Has table:', hasTable)
    console.log('Has loading indicator:', hasLoading)

    // Get list of any asset items if present
    const rows = await page.locator('table tbody tr, .el-table__row, .list-item').count()
    console.log('Number of rows/items:', rows)

    // Try to find an edit button or clickable row
    const editButtons = await page.locator('button:has-text("编辑"), button:has-text("Edit"), .el-button:has([class*="edit"])').count()
    console.log('Edit buttons found:', editButtons)

    if (rows > 0) {
      // Click first row to navigate to detail/edit
      const firstRow = page.locator('table tbody tr, .el-table__row').first()
      await firstRow.click()
      await page.waitForTimeout(2000)

      // Take screenshot of detail page
      await page.screenshot({
        path: 'test-screenshots/asset-detail-page.png',
        fullPage: true
      })
      console.log('Navigated to detail page')
    }
  })

  test('Step 3: Navigate directly to create/edit form and check field rendering', async ({ page }) => {
    // Set up authentication
    await page.goto(BASE_URL)
    await page.evaluate(({ token }) => {
      localStorage.setItem('access_token', token)
    }, { token: authToken })

    // Try to navigate to a create form directly
    // First, let's check if there's a create button
    await page.goto(`${BASE_URL}/objects/Asset`)
    await page.waitForLoadState('networkidle')
    await page.waitForTimeout(2000)

    // Look for create/new button
    const createButton = page.locator('button:has-text("新建"), button:has-text("New"), button:has-text("创建"), .el-button--primary').first()
    if (await createButton.count() > 0) {
      await createButton.click()
      await page.waitForTimeout(3000)
    } else {
      // Try direct URL for create form
      await page.goto(`${BASE_URL}/objects/Asset/create`)
      await page.waitForTimeout(3000)
    }

    // Take screenshot of form page
    await page.screenshot({
      path: 'test-screenshots/asset-form-page.png',
      fullPage: true
    })

    // Check for images field specifically
    console.log('\n=== Checking for images field on form ===')

    // Look for images field label
    const imagesLabel = page.locator('text=图片, text=images, text=Images, label:has-text("图片")')
    const imagesLabelCount = await imagesLabel.count()
    console.log('Images label elements found:', imagesLabelCount)

    // Look for any input/textarea with images-related name/id
    const imagesInput = page.locator('input[name*="image"], input[id*="image"], textarea[name*="image"]')
    const imagesInputCount = await imagesInput.count()
    console.log('Images input/textarea elements found:', imagesInputCount)

    // Look for image upload component
    const imageUpload = page.locator('.image-field, [class*="image-upload"], .el-upload:has([accept*="image"])')
    const imageUploadCount = await imageUpload.count()
    console.log('Image upload component elements found:', imageUploadCount)

    // Get all field labels on the form
    const allLabels = await page.locator('.el-form-item__label, label, .field-label').allTextContents()
    console.log('\n=== All Field Labels on Form ===')
    for (const label of allLabels) {
      if (label.trim()) {
        console.log(`  - ${label.trim()}`)
      }
    }

    // Check for all input types
    const inputs = await page.locator('input, textarea, select').all()
    console.log('\n=== Input Elements on Form ===')
    for (const input of inputs.slice(0, 20)) { // Limit to first 20
      const tag = await input.evaluate(e => e.tagName)
      const type = await input.evaluate(e => e.getAttribute('type'))
      const name = await input.evaluate(e => e.getAttribute('name'))
      const id = await input.evaluate(e => e.getAttribute('id'))
      console.log(`  ${tag.toLowerCase()} - type: ${type || 'text'}, name: ${name || 'none'}, id: ${id || 'none'}`)
    }
  })

  test('Step 4: Check console logs and network requests', async ({ page }) => {
    // Set up console log collection
    const consoleLogs: string[] = []
    page.on('console', msg => {
      consoleLogs.push(`${msg.type()}: ${msg.text()}`)
    })

    // Set up network request monitoring
    const apiRequests: { url: string; status: number }[] = []
    page.on('response', response => {
      if (response.url().includes('/api/')) {
        apiRequests.push({
          url: response.url(),
          status: response.status()
        })
      }
    })

    // Set up authentication
    await page.goto(BASE_URL)
    await page.evaluate(({ token }) => {
      localStorage.setItem('access_token', token)
    }, { token: authToken })

    // Navigate to Asset list
    await page.goto(`${BASE_URL}/objects/Asset`)
    await page.waitForLoadState('networkidle')
    await page.waitForTimeout(3000)

    console.log('\n=== Console Logs ===')
    consoleLogs.slice(-20).forEach(log => console.log(log))

    console.log('\n=== API Requests ===')
    apiRequests.forEach(req => {
      console.log(`  ${req.status} - ${req.url}`)
    })

    // Look specifically for the metadata API call
    const metadataCall = apiRequests.find(r => r.url.includes('business-objects') && r.url.includes('fields'))
    if (metadataCall) {
      console.log('\n=== Metadata API Call Found ===')
      console.log(`Status: ${metadataCall.status}`)
      console.log(`URL: ${metadataCall.url}`)
    }
  })
})
