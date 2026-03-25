import { apiRequest, getTestUserToken } from '../helpers/api.helpers'
import {
  expectNoLoadError,
  getHeaderActionButton,
  waitForDetailPageReady,
  waitForLoadingMaskToClear
} from '../helpers/detail-page.helpers'
import { test, expect } from '../fixtures/auth.fixture'

interface AssetListItem {
  id: string
}

interface AssetListResponse {
  results?: AssetListItem[]
}

interface ReferenceValue {
  id?: string
  name?: string
}

interface AssetRecordResponse {
  id: string
  assetCode?: string
  assetCategory?: ReferenceValue | null
  organization?: ReferenceValue | null
}

test.describe('Dynamic Object Detail', () => {
  test('should render detail values and submit reference as id', async ({ authenticatedPage: page }) => {
    const notFound: Array<{ url: string; method?: string }> = []
    const legacyCalls: Array<{ url: string; method?: string }> = []

    const isLegacy = (url: string) => {
      if (!url.includes('/api/')) return false
      if (url.includes('/api/system/objects/')) return false
      if (url.includes('/api/system/page-layouts/')) return false
      if (url.includes('/api/system/files/')) return false
      if (url.includes('/api/system/file')) return false
      if (url.includes('/api/auth/login')) return false
      // Engine/runtime must not depend on these legacy domain endpoints.
      if (url.includes('/api/auth/users/')) {
        return true
      }
      if (url.includes('/api/assets/')) return true
      if (url.includes('/api/organizations/')) return true
      return false
    }

    page.on('request', (req) => {
      const url = req.url()
      if (isLegacy(url)) legacyCalls.push({ url, method: req.method() })
    })

    page.on('response', (res) => {
      if (res.status() !== 404) return
      const url = res.url()
      // Focus on backend/API calls (ignore Vite HMR + static assets).
      if (!url.includes('/api/')) return
      notFound.push({ url, method: res.request().method() })
    })

    const token = await getTestUserToken()
    if (!token) test.skip(true, 'Missing E2E auth token')

    const listRes = await apiRequest<AssetListResponse>('/system/objects/Asset/?page=1&page_size=1', token)
    const first = listRes.data?.results?.[0]
    if (!listRes.success || !first?.id) test.skip(true, 'No Asset records available')

    const recordRes = await apiRequest<AssetRecordResponse>(`/system/objects/Asset/${first.id}/`, token)
    if (!recordRes.success || !recordRes.data) test.skip(true, 'Failed to load Asset record')

    const assetId = recordRes.data.id as string
    const assetCode = recordRes.data.assetCode as string | undefined
    const category = recordRes.data.assetCategory as { id?: string; name?: string } | null | undefined
    const organization = recordRes.data.organization as { id?: string; name?: string } | null | undefined

    legacyCalls.length = 0
    await page.goto(`/objects/Asset/${assetId}`)
    await page.waitForLoadState('domcontentloaded')

    await waitForDetailPageReady(page)

    // Wait for loading mask to disappear (if any)
    await waitForLoadingMaskToClear(page)
    // Give async option loaders (reference fields, etc.) a moment to settle.
    await page.waitForTimeout(800)
    expect(notFound, `Unexpected 404 API calls: ${JSON.stringify(notFound, null, 2)}`).toEqual([])
    expect(legacyCalls, `Unexpected legacy API calls: ${JSON.stringify(legacyCalls, null, 2)}`).toEqual([])

    await expectNoLoadError(page)

    const hasInputWithValue = async (value: string) => {
      return page.evaluate((v) => {
        const inputs = Array.from(document.querySelectorAll('input, textarea')) as Array<
          HTMLInputElement | HTMLTextAreaElement
        >
        return inputs.some((el) => el.value === v || el.value.includes(v))
      }, value)
    }

    const hasAnyObjectObjectValue = async () => {
      return page.evaluate(() => {
        const inputs = Array.from(document.querySelectorAll('input, textarea')) as Array<
          HTMLInputElement | HTMLTextAreaElement
        >
        return inputs.some((el) => (el.value || '').includes('[object Object]'))
      })
    }

    if (assetCode) {
      expect(await hasInputWithValue(assetCode)).toBeTruthy()
    }

    expect(await hasAnyObjectObjectValue()).toBeFalsy()

    if (category?.name) {
      await expect(page.locator('.dynamic-detail-page').locator(`text=${category.name}`)).toBeVisible()
    }

    const editButton = getHeaderActionButton(page, /Edit/i)
    if (!(await editButton.isVisible({ timeout: 3000 }).catch(() => false))) {
      test.skip(true, 'Edit button not available')
    }

    await editButton.click()
    const navigatedToEdit = await page
      .waitForURL(new RegExp(`/objects/Asset/${assetId}/edit`), { timeout: 5000 })
      .then(() => true)
      .catch(() => false)

    if (!navigatedToEdit) {
      await expect(page.locator('.el-drawer:visible')).toHaveCount(1)
    }

    await waitForLoadingMaskToClear(page)
    await page.waitForTimeout(500)
    expect(legacyCalls, `Unexpected legacy API calls (edit): ${JSON.stringify(legacyCalls, null, 2)}`).toEqual([])

    if (assetCode) {
      expect(await hasInputWithValue(assetCode)).toBeTruthy()
    }

    // Regression guard: runtime field merge must not wipe `reference` types (otherwise objects render as [object Object]).
    expect(await hasAnyObjectObjectValue()).toBeFalsy()
    if (organization?.name) {
      await expect(page.locator(`text=${organization.name}`).first()).toBeVisible()
    }

    const saveButton = navigatedToEdit
      ? page.locator('.form-actions button.el-button--primary').first()
      : page.locator('.el-drawer__footer button.el-button--primary').first()
    await expect(saveButton).toBeVisible()

    // Force a data change to ensure the page issues an update request.
    const remarksControl = page.locator('[aria-label="remarks"]').first()
    if (await remarksControl.count()) {
      await remarksControl.fill(`e2e-${Date.now()}`)
    }

    let capturedPayload: Record<string, unknown> | null = null
    await page.route(new RegExp(`/api/system/objects/Asset/${assetId}/$`), async (route) => {
      const req = route.request()
      if (req.method() !== 'PUT') return route.continue()

      const raw = req.postData() || '{}'
      try {
        capturedPayload = JSON.parse(raw)
      } catch {
        capturedPayload = {}
      }

      // Prevent real DB mutation in E2E: return a successful response in the app's unified format.
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({ success: true, data: {} })
      })
    })

    await saveButton.click()
    if (navigatedToEdit) {
      await page.waitForURL('/objects/Asset', { timeout: 20000 })
    } else {
      await expect(page.locator('.el-drawer:visible')).toHaveCount(0, { timeout: 10000 })
      await expect(page).toHaveURL(new RegExp(`/objects/Asset/${assetId}$`))
    }
    const payload = capturedPayload || {}

    if (category?.id) {
      expect(typeof payload?.assetCategory).toBe('string')
      expect(payload.assetCategory).toBe(category.id)
    }
  })
})
