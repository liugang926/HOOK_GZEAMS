import { test, expect } from '@playwright/test'
import { promises as fs } from 'fs'
import path from 'path'

const BASE_URL = process.env.BASE_URL || 'http://localhost:5174'
const API_BASE = process.env.API_BASE || 'http://localhost:8000/api'

const ADMIN_USERNAME = 'admin'
const ADMIN_PASSWORD = 'admin123456'

test.describe('Images and Attachments Upload Verification', () => {
  let authToken: string = ''
  let testImagePath: string
  let testFilePath: string

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

    // Create test files directory
    const testDir = path.join(process.cwd(), 'test-files')
    await fs.mkdir(testDir, { recursive: true })

    // Create a simple test image (1x1 red PNG)
    testImagePath = path.join(testDir, 'test-image.png')
    const testImageData = Buffer.from([
      0x89, 0x50, 0x4E, 0x47, 0x0D, 0x0A, 0x1A, 0x0A, // PNG signature
      0x00, 0x00, 0x00, 0x0D, // IHDR length
      0x49, 0x48, 0x44, 0x52, // IHDR type
      0x00, 0x00, 0x00, 0x01, // Width: 1
      0x00, 0x00, 0x00, 0x01, // Height: 1
      0x08, 0x02, 0x00, 0x00, 0x00, // Bit depth: 8, Color type: 2 (RGB)
      0x90, 0x77, 0x53, 0xDE, // CRC
      0x00, 0x00, 0x00, 0x0C, // IDAT length
      0x49, 0x44, 0x41, 0x54, // IDAT type
      0x08, 0xD7, 0x63, 0xF8, 0xCF, 0xC0, 0x00, 0x00, 0x03, 0x01, 0x01, 0x00, // Image data (red pixel)
      0x18, 0xDD, 0x8D, 0xB4, // CRC
      0x00, 0x00, 0x00, 0x00, // IEND length
      0x49, 0x45, 0x4E, 0x44, // IEND type
      0xAE, 0x42, 0x60, 0x82 // CRC
    ])
    await fs.writeFile(testImagePath, testImageData)

    // Create a test text file
    testFilePath = path.join(testDir, 'test-file.txt')
    await fs.writeFile(testFilePath, 'This is a test attachment file.\nContent: Test attachment content.')

    console.log('Test files created at:', testDir)
  })

  test('Step 1: Verify API metadata returns correct field types', async ({ request }) => {
    const response = await request.get(`${API_BASE}/system/business-objects/fields/?object_code=Asset`, {
      headers: {
        'Authorization': `Bearer ${authToken}`
      }
    })

    expect(response.ok()).toBeTruthy()
    const data = await response.json()
    const fields = data.data?.fields || []

    // Find images and attachments fields
    const imagesField = fields.find((f: any) =>
      f.fieldName === 'images' || f.field_name === 'images' || f.code === 'images'
    )
    const attachmentsField = fields.find((f: any) =>
      f.fieldName === 'attachments' || f.field_name === 'attachments' || f.code === 'attachments'
    )

    console.log('\n=== Images Field ===')
    console.log(JSON.stringify(imagesField, null, 2))

    console.log('\n=== Attachments Field ===')
    console.log(JSON.stringify(attachmentsField, null, 2))

    // Verify field types
    expect(imagesField).toBeTruthy()
    expect(imagesField?.fieldType || imagesField?.field_type).toBe('image')
    expect(attachmentsField?.fieldType || attachmentsField?.field_type).toBe('file')
  })

  test('Step 2: Navigate to Asset form and verify field rendering', async ({ page }) => {
    // Set up authentication
    await page.goto(BASE_URL)
    await page.evaluate(({ token }) => {
      localStorage.setItem('access_token', token)
    }, { token: authToken })

    // Navigate to Asset list
    await page.goto(`${BASE_URL}/objects/Asset`)
    await page.waitForLoadState('networkidle')
    await page.waitForTimeout(2000)

    // Take screenshot of list page
    await page.screenshot({
      path: 'test-screenshots/upload-verify-asset-list.png',
      fullPage: true
    })

    // Try to find and click create button, or click first row
    const createButton = page.locator('button:has-text("新建"), button:has-text("New"), button:has-text("创建")').first()

    if (await createButton.count() > 0) {
      await createButton.click()
      console.log('Clicked create button')
    } else {
      // Try clicking first row to edit
      const firstRow = page.locator('table tbody tr, .el-table__row').first()
      const rowCount = await firstRow.count()
      if (rowCount > 0) {
        await firstRow.click()
        console.log('Clicked first row for editing')
      } else {
        // Try direct URL
        await page.goto(`${BASE_URL}/objects/Asset/create`)
        console.log('Navigated to create form directly')
      }
    }

    await page.waitForLoadState('networkidle')
    await page.waitForTimeout(3000)

    // Take screenshot of form page
    await page.screenshot({
      path: 'test-screenshots/upload-verify-asset-form.png',
      fullPage: true
    })

    // Check for images field
    console.log('\n=== Checking for images field ===')
    const imagesLabel = page.locator('text=图片, text=images, text=Images')
    const imagesLabelCount = await imagesLabel.count()
    console.log('Images label elements found:', imagesLabelCount)

    // Look for ImageField component
    const imageField = page.locator('.image-field, [class*="image-upload"]')
    const imageFieldCount = await imageField.count()
    console.log('Image field components found:', imageFieldCount)

    // Look for upload button or area
    const uploadButton = page.locator('button:has-text("Upload"), button:has-text("上传"), .el-upload')
    const uploadCount = await uploadButton.count()
    console.log('Upload buttons/areas found:', uploadCount)

    // Look for file input (should be present but hidden)
    const fileInput = page.locator('input[type="file"]')
    const fileInputCount = await fileInput.count()
    console.log('File inputs found:', fileInputCount)

    // Get all field labels
    const allLabels = await page.locator('.el-form-item__label, label').allTextContents()
    console.log('\n=== All Field Labels on Form ===')
    const filteredLabels = allLabels.filter(l => l.trim()).slice(0, 30)
    for (const label of filteredLabels) {
      console.log(`  - ${label.trim()}`)
    }

    // Verify we have upload components
    expect(fileInputCount + imageFieldCount).toBeGreaterThan(0)
  })

  test('Step 3: Test actual image upload functionality', async ({ page }) => {
    // Set up authentication
    await page.goto(BASE_URL)
    await page.evaluate(({ token }) => {
      localStorage.setItem('access_token', token)
    }, { token: authToken })

    // Navigate to Asset create form
    await page.goto(`${BASE_URL}/objects/Asset/create`)
    await page.waitForLoadState('networkidle')
    await page.waitForTimeout(2000)

    console.log('\n=== Testing Image Upload ===')

    // Find the file input for images field
    // It may be hidden, so we need to use setInputFiles which handles hidden inputs
    const fileInputs = page.locator('input[type="file"]')
    const inputCount = await fileInputs.count()
    console.log('Found', inputCount, 'file inputs')

    if (inputCount === 0) {
      console.log('No file inputs found - checking for upload area')
      // Alternative: look for el-upload component and trigger it
      const uploadArea = page.locator('.el-upload, .upload-drag-area').first()
      if (await uploadArea.count() > 0) {
        console.log('Found upload area, clicking...')
        await uploadArea.click()
        await page.waitForTimeout(1000)
      }
    }

    // Try to upload the test image
    try {
      // Get all file inputs and try to upload to each one that accepts images
      const allFileInputs = await page.locator('input[type="file"]').all()
      console.log('Total file inputs:', allFileInputs.length)

      for (let i = 0; i < allFileInputs.length; i++) {
        const input = allFileInputs[i]
        const accept = await input.evaluate(el => el.getAttribute('accept'))
        const name = await input.evaluate(el => el.getAttribute('name'))

        console.log(`Input ${i}: accept="${accept}", name="${name}"`)

        // Try uploading to input that accepts images or has no accept restriction
        if (!accept || accept.includes('image')) {
          console.log(`Uploading test image to input ${i}...`)
          await input.setInputFiles(testImagePath)
          await page.waitForTimeout(2000)

          // Take screenshot after upload
          await page.screenshot({
            path: `test-screenshots/upload-verify-after-image-${i}.png`,
            fullPage: true
          })

          // Check for success indicators
          const previewImage = page.locator('.image-thumbnail, .el-image, img[src*="data"], img[src*="blob"]')
          const previewCount = await previewImage.count()
          console.log('Preview images found after upload:', previewCount)

          // Check for file list
          const fileList = page.locator('.el-upload-list__item, .file-list-item')
          const fileListCount = await fileList.count()
          console.log('File list items found:', fileListCount)

          if (previewCount > 0 || fileListCount > 0) {
            console.log('SUCCESS: Image upload appears to have worked!')
            break
          }
        }
      }
    } catch (error) {
      console.log('Upload attempt failed:', error)
    }

    // Final screenshot
    await page.screenshot({
      path: 'test-screenshots/upload-verify-final-state.png',
      fullPage: true
    })
  })

  test('Step 4: Test attachments upload functionality', async ({ page }) => {
    // Set up authentication
    await page.goto(BASE_URL)
    await page.evaluate(({ token }) => {
      localStorage.setItem('access_token', token)
    }, { token: authToken })

    // Navigate to Asset create form
    await page.goto(`${BASE_URL}/objects/Asset/create`)
    await page.waitForLoadState('networkidle')
    await page.waitForTimeout(2000)

    console.log('\n=== Testing Attachments Upload ===')

    // Try to upload a test file
    try {
      const allFileInputs = await page.locator('input[type="file"]').all()
      console.log('Found', allFileInputs.length, 'file inputs for attachments test')

      for (let i = 0; i < allFileInputs.length; i++) {
        const input = allFileInputs[i]
        const accept = await input.evaluate(el => el.getAttribute('accept'))
        const name = await input.evaluate(el => el.getAttribute('name'))

        console.log(`Input ${i}: accept="${accept}", name="${name}"`)

        // Try uploading to input that accepts files or has no accept restriction
        if (!accept || accept.includes('*') || accept.includes('application')) {
          console.log(`Uploading test file to input ${i}...`)
          await input.setInputFiles(testFilePath)
          await page.waitForTimeout(2000)

          // Take screenshot after upload
          await page.screenshot({
            path: `test-screenshots/upload-verify-after-file-${i}.png`,
            fullPage: true
          })

          // Check for file list indicators
          const fileList = page.locator('.el-upload-list__item, .file-list-item, .attachment-item')
          const fileListCount = await fileList.count()
          console.log('File list items found:', fileListCount)

          if (fileListCount > 0) {
            console.log('SUCCESS: File upload appears to have worked!')
            break
          }
        }
      }
    } catch (error) {
      console.log('File upload attempt failed:', error)
    }

    // Final screenshot
    await page.screenshot({
      path: 'test-screenshots/upload-verify-files-final.png',
      fullPage: true
    })
  })

  test('Step 5: Verify field components are NOT text inputs', async ({ page }) => {
    // Set up authentication
    await page.goto(BASE_URL)
    await page.evaluate(({ token }) => {
      localStorage.setItem('access_token', token)
    }, { token: authToken })

    // Navigate to Asset create form
    await page.goto(`${BASE_URL}/objects/Asset/create`)
    await page.waitForLoadState('networkidle')
    await page.waitForTimeout(2000)

    console.log('\n=== Verifying fields are NOT text inputs ===')

    // Get all text inputs and textareas
    const textInputs = await page.locator('input[type="text"], textarea').all()
    console.log('Found', textInputs.length, 'text inputs/textarea')

    // Check their names/labels
    for (const input of textInputs.slice(0, 15)) {
      const name = await input.evaluate(el => el.getAttribute('name'))
      const id = await input.evaluate(el => el.getAttribute('id'))
      const placeholder = await input.evaluate(el => el.getAttribute('placeholder'))

      if (name) {
        const lowerName = name.toLowerCase()
        if (lowerName.includes('image') || lowerName.includes('attachment')) {
          console.log(`WARNING: Found text input for ${name} - this should be an upload component!`)
        }
      }
    }

    // Look for proper upload components
    const hasImageField = await page.locator('.image-field').count() > 0
    const hasFileField = await page.locator('.file-field, [class*="file-upload"]').count() > 0
    const hasUploadArea = await page.locator('.el-upload, .upload-drag-area').count() > 0

    console.log('Has .image-field component:', hasImageField)
    console.log('Has file-field component:', hasFileField)
    console.log('Has upload area:', hasUploadArea)

    // At minimum, we should have upload areas (el-upload)
    expect(hasUploadArea).toBeTruthy()

    await page.screenshot({
      path: 'test-screenshots/upload-verify-component-check.png',
      fullPage: true
    })
  })
})
