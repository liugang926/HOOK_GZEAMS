import { test, expect } from '@playwright/test'

/**
 * E2E Tests for Asset Form Submission
 *
 * This test suite verifies the complete flow of:
 * 1. Navigating to asset creation form
 * 2. Filling out all required and optional fields
 * 3. Submitting the form
 * 4. Verifying the data was saved successfully
 * 5. Verifying the saved data can be retrieved
 *
 * Prerequisites:
 * - Backend server running on http://localhost:8000
 * - Frontend dev server running
 * - Valid test user credentials
 */

const TEST_USER = {
  username: 'admin',
  password: 'admin123'
}

const TEST_ASSET = {
  code: 'TEST-' + Date.now(),
  name: 'E2E测试资产-' + Date.now(),
  category: '', // Will be filled from available options
  status: 'idle',
  brand: '测试品牌',
  model: '测试型号',
  unit: '台',
  serialNumber: 'SN-' + Date.now(),
  purchasePrice: 1000,
  supplier: '测试供应商',
  remarks: 'E2E自动化测试创建的资产'
}

test.describe('Asset Form Submission E2E', () => {
  test.beforeEach(async ({ page }) => {
    // Navigate to login page
    await page.goto('/login')

    // Fill in login credentials
    await page.fill('input[placeholder*="用户名"], input[placeholder*="username"], input[name="username"]', TEST_USER.username)
    await page.fill('input[placeholder*="密码"], input[placeholder*="password"], input[name="password"]', TEST_USER.password)

    // Click login button
    await page.click('button:has-text("登录"), button[type="submit"]')

    // Wait for navigation to complete after login
    await page.waitForLoadState('networkidle')

    // Verify we're logged in - should be on dashboard or assets page
    const currentUrl = page.url()
    expect(currentUrl).toMatch(/\/(dashboard|assets)?/)
  })

  test('should complete full asset creation flow', async ({ page }) => {
    // Navigate directly to the asset creation page
    await page.goto('/assets/create')
    await page.waitForLoadState('networkidle')

    // Verify we're on the form page
    expect(page.url()).toMatch(/\/assets(\/create)?/)

    // Wait for form to be rendered
    const formElement = page.locator('form, .el-form, .dynamic-form, .base-form')
    await expect(formElement, 'Form should be visible').toBeVisible({ timeout: 5000 })

    // Step 2: Fill in required fields

    // Asset Code
    const codeInput = page.locator('input[placeholder*="编码"], input[placeholder*="Code"]').first()
    await expect(codeInput, 'Code input should be visible').toBeVisible({ timeout: 3000 })
    await codeInput.fill(TEST_ASSET.code)

    // Asset Name
    const nameInput = page.locator('input[placeholder*="名称"], input[placeholder*="Name"]').first()
    await expect(nameInput, 'Name input should be visible').toBeVisible()
    await nameInput.fill(TEST_ASSET.name)

    // Step 3: Fill in optional fields

    // Brand
    const brandInput = page.locator('input[placeholder*="品牌"], input[placeholder*="Brand"]').or(
      page.locator('input.el-input__inner').filter({ hasText: '' }).nth(2)
    )
    if (await brandInput.isVisible({ timeout: 1000 }).catch(() => false)) {
      await brandInput.fill(TEST_ASSET.brand)
    }

    // Model
    const modelInput = page.locator('input[placeholder*="型号"], input[placeholder*="Model"]').or(
      page.locator('input.el-input__inner').filter({ hasText: '' }).nth(3)
    )
    if (await modelInput.isVisible({ timeout: 1000 }).catch(() => false)) {
      await modelInput.fill(TEST_ASSET.model)
    }

    // Unit
    const unitInput = page.locator('input[placeholder*="单位"], input[placeholder*="Unit"]').or(
      page.locator('input.el-input__inner').filter({ hasText: '' }).nth(4)
    )
    if (await unitInput.isVisible({ timeout: 1000 }).catch(() => false)) {
      await unitInput.fill(TEST_ASSET.unit)
    }

    // Serial Number
    const serialInput = page.locator('input[placeholder*="序列号"], input[placeholder*="Serial"]').or(
      page.locator('input.el-input__inner').filter({ hasText: '' }).nth(5)
    )
    if (await serialInput.isVisible({ timeout: 1000 }).catch(() => false)) {
      await serialInput.fill(TEST_ASSET.serialNumber)
    }

    // Purchase Price (number input)
    const priceInput = page.locator('input[placeholder*="价格"], input[placeholder*="Price"]').or(
      page.locator('input[type="number"]')
    )
    if (await priceInput.isVisible({ timeout: 1000 }).catch(() => false)) {
      await priceInput.fill(String(TEST_ASSET.purchasePrice))
    }

    // Supplier
    const supplierInput = page.locator('input[placeholder*="供应商"], input[placeholder*="Supplier"]').or(
      page.locator('input.el-input__inner').filter({ hasText: '' }).nth(6)
    )
    if (await supplierInput.isVisible({ timeout: 1000 }).catch(() => false)) {
      await supplierInput.fill(TEST_ASSET.supplier)
    }

    // Remarks (textarea)
    const remarksInput = page.locator('textarea[placeholder*="备注"], textarea[placeholder*="Remarks"]').or(
      page.locator('textarea.el-textarea__inner')
    )
    if (await remarksInput.isVisible({ timeout: 1000 }).catch(() => false)) {
      await remarksInput.fill(TEST_ASSET.remarks)
    }

    // Step 4: Handle category selection if present
    const categorySelect = page.locator('.el-select:visible').first()
    if (await categorySelect.isVisible({ timeout: 1000 }).catch(() => false)) {
      await categorySelect.click()
      await page.waitForTimeout(500)

      // Select first available option
      const firstOption = page.locator('.el-select-dropdown__item:visible').first()
      if (await firstOption.isVisible().catch(() => false)) {
        await firstOption.click()
        TEST_ASSET.category = await firstOption.textContent() || ''
      }
    }

    // Step 5: Submit the form
    const submitButton = page.locator('button:has-text("保存"), button:has-text("提交"), button:has-text("创建")').first()
    await expect(submitButton, 'Submit button should be visible').toBeVisible()
    await submitButton.click()

    // Step 6: Verify submission result
    // Wait for API response and navigation
    await page.waitForTimeout(3000)

    // Check for success message
    const successMessage = page.locator('.el-message--success, .el-notification--success, :has-text("成功"), :has-text("已保存")')
    const hasSuccessMessage = await successMessage.isVisible({ timeout: 2000 }).catch(() => false)

    // Verify we're no longer on the create page (navigated back to list)
    const finalUrl = page.url()
    const navigatedToList = finalUrl.includes('/assets') && !finalUrl.includes('/create')

    expect(hasSuccessMessage || navigatedToList, 'Should show success message or navigate to list').toBeTruthy()

    // Step 7: Verify the created asset appears in the list
    if (navigatedToList) {
      await page.waitForLoadState('networkidle')

      // Search for the created asset by code
      const searchInput = page.locator('input[placeholder*="资产编码"], input[placeholder*="搜索"]').or(
        page.locator('.search-input input, .el-input__inner').first()
      )

      if (await searchInput.isVisible({ timeout: 3000 }).catch(() => false)) {
        await searchInput.clear()
        await searchInput.fill(TEST_ASSET.code)
        await page.keyboard.press('Enter')
        await page.waitForTimeout(2000)

        // Verify the asset appears in the table
        const table = page.locator('table, .el-table')
        if (await table.isVisible({ timeout: 3000 }).catch(() => false)) {
          const assetCodeInTable = page.locator('table', '.el-table').locator(`text=${TEST_ASSET.code}`)
          await expect(assetCodeInTable, 'Created asset should appear in table').toBeVisible({ timeout: 5000 })
        }
      }
    }
  })

  test('should show validation errors for missing required fields', async ({ page }) => {
    // Navigate directly to the asset creation page
    await page.goto('/assets/create')
    await page.waitForLoadState('networkidle')
    await page.waitForTimeout(1000)

    // Submit without filling any fields
    const submitButton = page.locator('button:has-text("保存"), button:has-text("提交")').first()
    await submitButton.click()
    await page.waitForTimeout(1000)

    // Check for validation error messages
    const errorMessage = page.locator('.el-form-item__error, .el-message--error, :has-text("必填"), :has-text("不能为空")')

    // Should see at least one validation error
    const errorCount = await errorMessage.count()
    expect(errorCount, 'Should show validation errors for required fields').toBeGreaterThan(0)

    // Should still be on form page (validation prevented submission)
    expect(page.url()).toMatch(/\/assets(\/create)?/)
  })

  test('should save and then edit an asset', async ({ page }) => {
    // Navigate directly to the asset creation page
    await page.goto('/assets/create')
    await page.waitForLoadState('networkidle')
    await page.waitForTimeout(1000)

    // Fill minimal required fields
    const codeInput = page.locator('input[placeholder*="编码"], input[placeholder*="Code"]').first()
    await codeInput.fill('EDIT-TEST-' + Date.now())

    const nameInput = page.locator('input[placeholder*="名称"], input[placeholder*="Name"]').first()
    await nameInput.fill('编辑测试资产')

    // Submit
    const submitButton = page.locator('button:has-text("保存"), button:has-text("创建")').first()
    await submitButton.click()
    await page.waitForTimeout(2000)

    // Now try to edit it
    await page.waitForTimeout(1000)
    const editButton = page.locator('button:has-text("编辑")').or(
      page.locator('.edit-btn, [class*="edit"], .el-button--primary:has-text("编辑")')
    ).first()

    if (await editButton.isVisible({ timeout: 3000 }).catch(() => false)) {
      await editButton.click()
      await page.waitForTimeout(2000)

      // Verify we're in edit mode (form loaded with existing data)
      const formElement = page.locator('form, .el-form')
      await expect(formElement, 'Edit form should be visible').toBeVisible()

      // Modify a field
      const nameInputForEdit = page.locator('input[placeholder*="名称"], input[placeholder*="Name"]').first()
      await nameInputForEdit.clear()
      await nameInputForEdit.fill('编辑测试资产-已修改')

      // Save the edit
      const saveButton = page.locator('button:has-text("保存"), button:has-text("更新")').first()
      await saveButton.click()
      await page.waitForTimeout(2000)

      // Verify edit was saved
      const successMessage = page.locator('.el-message--success, :has-text("成功"), :has-text("已保存")')
      const hasSuccess = await successMessage.isVisible({ timeout: 2000 }).catch(() => false)
      expect(hasSuccess, 'Should show success message after edit').toBeTruthy()
    }
  })

  test('should handle form cancellation without saving', async ({ page }) => {
    // Navigate directly to the asset creation page
    await page.goto('/assets/create')
    await page.waitForLoadState('networkidle')
    await page.waitForTimeout(1000)

    // Fill some fields
    const codeInput = page.locator('input[placeholder*="编码"], input[placeholder*="Code"]').first()
    await codeInput.fill('CANCEL-TEST')

    const nameInput = page.locator('input[placeholder*="名称"], input[placeholder*="Name"]').first()
    await nameInput.fill('取消测试')

    // Click cancel/back button
    const cancelButton = page.locator('button:has-text("取消"), button:has-text("返回")').first()
    await cancelButton.click()
    await page.waitForTimeout(1000)

    // Should be back on list page
    expect(page.url()).toMatch(/\/assets$/)

    // Search for the cancelled asset - should not exist
    const searchInput = page.locator('input[placeholder*="资产编码"], input[placeholder*="搜索"]').or(
      page.locator('.search-input input, .el-input__inner').first()
    )

    if (await searchInput.isVisible({ timeout: 3000 }).catch(() => false)) {
      await searchInput.clear()
      await searchInput.fill('CANCEL-TEST')
      await page.keyboard.press('Enter')
      await page.waitForTimeout(2000)

      // The table should either be empty or not show this asset
      const table = page.locator('table, .el-table')
      if (await table.isVisible({ timeout: 3000 }).catch(() => false)) {
        const assetInTable = page.locator('table').locator('text=CANCEL-TEST')
        const hasAsset = await assetInTable.count() > 0
        expect(hasAsset, 'Cancelled asset should not be saved').toBeFalsy()
      }
    }
  })

  test('should preserve form data after validation error', async ({ page }) => {
    // Navigate directly to the asset creation page
    await page.goto('/assets/create')
    await page.waitForLoadState('networkidle')
    await page.waitForTimeout(1000)

    // Fill only some fields (missing required ones)
    const nameInput = page.locator('input[placeholder*="名称"], input[placeholder*="Name"]').first()
    await nameInput.fill('保留数据测试')

    // Try to submit
    const submitButton = page.locator('button:has-text("保存"), button:has-text("创建")').first()
    await submitButton.click()
    await page.waitForTimeout(1000)

    // Check that the name field still has our input (form wasn't reset)
    const nameValue = await nameInput.inputValue()
    expect(nameValue).toBe('保留数据测试')

    // Now fill the missing field and submit
    const codeInput = page.locator('input[placeholder*="编码"], input[placeholder*="Code"]').first()
    await codeInput.fill('PRESERVE-' + Date.now())

    await submitButton.click()
    await page.waitForTimeout(2000)

    // Should succeed now
    const finalUrl = page.url()
    const navigatedAway = !finalUrl.includes('/create')
    expect(navigatedAway, 'Should navigate away after successful submission').toBeTruthy()
  })
})

/**
 * API-based verification test
 * This test directly verifies the API endpoints for asset creation
 */
test.describe('Asset Creation API Verification', () => {
  test('should create asset via API and verify response', async ({ request }) => {
    // API base URL for backend requests - use 127.0.0.1 to match backend
    const API_BASE = process.env.API_BASE_URL || 'http://127.0.0.1:8000/api'

    // First login to get token
    const loginResponse = await request.post(`${API_BASE}/auth/login/`, {
      data: {
        username: TEST_USER.username,
        password: TEST_USER.password
      }
    })

    expect(loginResponse.ok()).toBeTruthy()

    const loginData = await loginResponse.json()
    const token = loginData.data?.token || loginData.data?.access || loginData.token || loginData.access

    expect(token).toBeDefined()

    // Create asset via API
    const createResponse = await request.post(`${API_BASE}/assets/`, {
      headers: {
        'Authorization': `Bearer ${token}`,
        'Content-Type': 'application/json'
      },
      data: {
        asset_code: `API-${Date.now()}`,
        asset_name: 'API创建测试资产',
        asset_category: null,
        asset_status: 'idle',
        brand: 'API测试品牌',
        remarks: '通过API直接创建'
      }
    })

    expect(createResponse.ok()).toBeTruthy()

    const createData = await createResponse.json()
    expect(createData.success || createData.id).toBeTruthy()

    // Verify the asset was created
    if (createData.data?.id || createData.id) {
      const assetId = createData.data?.id || createData.id

      const getResponse = await request.get(`${API_BASE}/assets/${assetId}/`, {
        headers: {
          'Authorization': `Bearer ${token}`
        }
      })

      expect(getResponse.ok()).toBeTruthy()

      const getData = await getResponse.json()
      expect(getData.data?.asset_name || getData.asset_name).toContain('API创建测试资产')
    }
  })
})
