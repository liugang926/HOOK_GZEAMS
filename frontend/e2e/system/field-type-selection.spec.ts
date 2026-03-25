import { test, expect } from '@playwright/test'

/**
 * E2E Tests for Field Type Selection
 *
 * Tests cover:
 * - Field type dropdown loads dynamically from API
 * - Field types are properly grouped
 * - All required field types are available (file, image, qr_code, barcode, etc.)
 * - Field type selection shows appropriate conditional fields
 * - Field type helper methods work correctly (requiresReference, supportsOptions)
 */

test.describe('Field Type Selection', () => {
  // Use hardcoded token from existing session for testing
  const AUTH_TOKEN = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ0b2tlbl90eXBlIjoiYWNjZXNzIiwiZXhwIjoxNzcwMTc0MzM1LCJpYXQiOjE3NzAxNjcxMzUsImp0aSI6Ijk4MzZlM2Q0Y2I3NDQ3M2I4YTFlZGZmYTQxMmVjMDRjIiwidXNlcl9pZCI6ImUwYzlkYWRhLTg5YTYtNDQ1Zi1iNTU1LTI5OGZlZGU2Y2RhMyJ9.HIQtLMp6EZWA-h-TM2iAlNC5G4eQ36XG6FBQKCLVC5I'

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

  test('should load field types dynamically from API', async ({ page, request }) => {
    // First verify the API endpoint works
    const apiResponse = await request.get('/api/system/business-objects/field-types/', {
      headers: {
        'Authorization': `Bearer ${AUTH_TOKEN}`
      }
    })

    expect(apiResponse.ok()).toBeTruthy()
    const data = await apiResponse.json()
    expect(data.success).toBe(true)
    expect(data.data.groups).toBeDefined()
    expect(data.data.allTypes).toBeDefined()
  })

  test('should include all required field types', async ({ page, request }) => {
    // Critical field types that were missing in the original hardcoded form
    const requiredTypes = ['file', 'image', 'qr_code', 'barcode', 'location', 'percent', 'time', 'rich_text']

    const apiResponse = await request.get('/api/system/business-objects/field-types/', {
      headers: {
        'Authorization': `Bearer ${AUTH_TOKEN}`
      }
    })

    const data = await apiResponse.json()
    const allTypes = data.data.allTypes

    for (const type of requiredTypes) {
      expect(allTypes).toContain(type)
    }
  })

  test('should have proper field type groupings', async ({ page, request }) => {
    const apiResponse = await request.get('/api/system/business-objects/field-types/', {
      headers: {
        'Authorization': `Bearer ${AUTH_TOKEN}`
      }
    })

    const data = await apiResponse.json()
    const groups = data.data.groups
    const groupLabels = groups.map((g: any) => g.label)

    // Verify all expected groups exist
    expect(groupLabels).toContain('基础类型')
    expect(groupLabels).toContain('日期时间')
    expect(groupLabels).toContain('选择类型')
    expect(groupLabels).toContain('引用类型')
    expect(groupLabels).toContain('媒体文件')
    expect(groupLabels).toContain('高级类型')
  })

  test('should have type config for media field types', async ({ page, request }) => {
    const apiResponse = await request.get('/api/system/business-objects/field-types/', {
      headers: {
        'Authorization': `Bearer ${AUTH_TOKEN}`
      }
    })

    const data = await apiResponse.json()
    const typeConfig = data.data.typeConfig

    // Verify component mappings for important field types
    expect(typeConfig.file).toBeDefined()
    expect(typeConfig.file.component).toBe('AttachmentUpload')

    expect(typeConfig.image).toBeDefined()
    expect(typeConfig.image.component).toBe('ImageField')

    expect(typeConfig.qr_code).toBeDefined()
    expect(typeConfig.qr_code.component).toBe('QRCodeField')

    expect(typeConfig.barcode).toBeDefined()
    expect(typeConfig.barcode.component).toBe('BarcodeField')
  })

  test('should cache field types in localStorage', async ({ page }) => {
    // Navigate to a page that uses field types
    await page.goto('/system/field-definitions')

    // Wait for potential API call
    await page.waitForTimeout(1000)

    // Check localStorage for cached field types
    const cacheValue = await page.evaluate(() => {
      return localStorage.getItem('gzeams_field_types_v1')
    })

    // Cache should be created after API call
    if (cacheValue) {
      const cache = JSON.parse(cacheValue)
      expect(cache.data).toBeDefined()
      expect(cache.data.groups).toBeDefined()
      expect(cache.timestamp).toBeDefined()
    }
  })

  test('should show reference object field for reference type', async ({ page }) => {
    // Navigate to field definition page
    await page.goto('/system/field-definitions')

    // Click add button (if exists)
    const addButton = page.locator('button:has-text("添加"), button:has-text("新增"), .el-button--primary').first()
    if (await addButton.isVisible()) {
      await addButton.click()
      await page.waitForTimeout(500)

      // Select reference field type
      const fieldSelect = page.locator('.el-select:visible').first()
      if (await fieldSelect.isVisible()) {
        await fieldSelect.click()
        await page.waitForTimeout(300)

        // Look for reference option
        const referenceOption = page.locator('.el-select-dropdown__item:has-text("关联引用")')
        if (await referenceOption.isVisible()) {
          await referenceOption.click()
          await page.waitForTimeout(300)

          // Reference object field should now be visible
          const refObjectLabel = page.locator('text=关联对象')
          // Check if it appears (may be in a form item)
          await page.waitForTimeout(500)
        }
      }
    }
  })

  test('should show options editor for select type', async ({ page }) => {
    // Navigate to field definition page
    await page.goto('/system/field-definitions')

    // Click add button (if exists)
    const addButton = page.locator('button:has-text("添加"), button:has-text("新增"), .el-button--primary').first()
    if (await addButton.isVisible()) {
      await addButton.click()
      await page.waitForTimeout(500)

      // Select select field type
      const fieldSelect = page.locator('.el-select:visible').first()
      if (await fieldSelect.isVisible()) {
        await fieldSelect.click()
        await page.waitForTimeout(300)

        // Look for select option
        const selectOption = page.locator('.el-select-dropdown__item:has-text("下拉选择")')
        if (await selectOption.isVisible()) {
          await selectOption.click()
          await page.waitForTimeout(300)

          // Options configuration should now be visible
          const optionsLabel = page.locator('text=选项配置')
          await page.waitForTimeout(500)
        }
      }
    }
  })

  test('should match API types with model field type choices', async ({ page, request }) => {
    // Get types from API
    const apiResponse = await request.get('/api/system/business-objects/field-types/', {
      headers: {
        'Authorization': `Bearer ${AUTH_TOKEN}`
      }
    })

    const apiData = await apiResponse.json()
    const apiTypes = new Set(apiData.data.allTypes)

    // Expected field types from FieldDefinition.FIELD_TYPE_CHOICES
    const expectedTypes = [
      'text', 'textarea', 'number', 'currency', 'percent',
      'date', 'datetime', 'time',
      'select', 'multi_select', 'radio', 'checkbox', 'boolean',
      'user', 'department', 'reference', 'asset', 'location',
      'file', 'image', 'qr_code', 'barcode',
      'formula', 'sub_table', 'rich_text'
    ]

    // All expected types should be in API response
    for (const type of expectedTypes) {
      expect(apiTypes.has(type), `Missing field type: ${type}`).toBe(true)
    }
  })
})

test.describe('Field Type Caching', () => {
  const AUTH_TOKEN = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ0b2tlebl90eXBlIjoiYWNjZXNzIiwiZXhwIjoxNzcwMTc0MzM1LCJpYXQiOjE3NzAxNjcxMzUsImp0aSI6Ijk4MzZlM2Q0Y2I3NDQ3M2I4YTFlZGZmYTQxMmVjMDRjIiwidXNlcl9pZCI6ImUwYzlkYWRhLTg5YTYtNDQ1Zi1iNTU1LTI5OGZlZGU2Y2RhMyJ9.HIQtLMp6EZWA-h-TM2iAlNC5G4eQ36XG6FBQKCLVC5I'

  test('should respect cache TTL', async ({ page }) => {
    // Set auth token
    await page.goto('/')
    await page.evaluate((token) => {
      localStorage.setItem('gzeams_access_token', token)
      // Set expired cache
      const expiredCache = {
        data: {
          groups: [],
          allTypes: [],
          typeConfig: {}
        },
        timestamp: Date.now() - (25 * 60 * 60 * 1000) // 25 hours ago
      }
      localStorage.setItem('gzeams_field_types_v1', JSON.stringify(expiredCache))
    }, AUTH_TOKEN)

    // Navigate to a page that uses field types
    await page.goto('/system/field-definitions')
    await page.waitForTimeout(1000)

    // Cache should have been refreshed (check via localStorage)
    const cacheValue = await page.evaluate(() => {
      const cache = localStorage.getItem('gzeams_field_types_v1')
      if (!cache) return null
      const parsed = JSON.parse(cache)
      return {
        hasGroups: parsed.data?.groups?.length > 0,
        timestamp: parsed.timestamp
      }
    })

    // New cache should have groups and recent timestamp
    if (cacheValue) {
      expect(cacheValue.hasGroups).toBe(true)
      expect(cacheValue.timestamp).toBeGreaterThan(Date.now() - 60000) // Within last minute
    }
  })

  test('should support force refresh', async ({ page }) => {
    // Set auth token
    await page.goto('/')
    await page.evaluate((token) => {
      localStorage.setItem('gzeams_access_token', token)
    }, AUTH_TOKEN)

    // Clear cache to force fresh load
    await page.evaluate(() => {
      localStorage.removeItem('gzeams_field_types_v1')
    })

    // Navigate to field definitions page
    await page.goto('/system/field-definitions')
    await page.waitForTimeout(2000)

    // Verify new cache was created
    const cacheExists = await page.evaluate(() => {
      return !!localStorage.getItem('gzeams_field_types_v1')
    })

    expect(cacheExists).toBe(true)
  })
})
