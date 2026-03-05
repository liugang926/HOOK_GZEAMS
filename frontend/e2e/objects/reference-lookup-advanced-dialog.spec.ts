import { expect, test, type Page, type Route } from '@playwright/test'

function fulfillSuccess(route: Route, data: unknown) {
  return route.fulfill({
    status: 200,
    contentType: 'application/json',
    body: JSON.stringify({ success: true, data })
  })
}

type MockState = {
  ownerId: string
  lastUpdatePayload: Record<string, any> | null
}

const USER_POOL: Array<Record<string, any>> = [
  { id: 'user-alice', fullName: 'Alice Stone', username: 'alice', name: 'Alice Stone', code: 'U-ALICE', email: 'alice@example.com', mobile: '13800000001' },
  { id: 'user-john', fullName: 'John Carter', username: 'john', name: 'John Carter', code: 'U-JOHN', email: 'john@example.com', mobile: '13800000002' },
  { id: 'user-zoe', fullName: 'Zoe Green', username: 'zoe', name: 'Zoe Green', code: 'U-ZOE', email: 'zoe@example.com', mobile: '13800000003' }
]

function buildRuntimeLayoutResponse() {
  return {
    runtime_version: 1,
    mode: 'edit',
    context: 'form',
    fields: {
      editable_fields: [
        {
          code: 'asset_name',
          name: 'Asset Name',
          label: 'Asset Name',
          fieldType: 'text',
          isHidden: false,
          showInForm: true,
          showInDetail: true,
          sortOrder: 1
        },
        {
          code: 'owner',
          name: 'Owner',
          label: 'Owner',
          fieldType: 'reference',
          referenceObject: 'User',
          referenceDisplayField: 'fullName',
          referenceSecondaryField: 'username',
          componentProps: {
            lookupCompactKeys: ['email']
          },
          isHidden: false,
          showInForm: true,
          showInDetail: true,
          sortOrder: 2
        }
      ],
      reverse_relations: []
    },
    layout: {
      layout_type: 'form',
      layout_config: {
        sections: [
          {
            id: 'overview',
            name: 'overview',
            title: 'Overview',
            columns: 2,
            fields: [
              { fieldCode: 'asset_name' },
              { fieldCode: 'owner' }
            ]
          }
        ]
      },
      status: 'published',
      version: '1.0.0'
    },
    permissions: {
      view: true,
      add: true,
      change: true,
      delete: true
    },
    is_default: true
  }
}

function pickUsersBySearch(keyword: string): Array<Record<string, any>> {
  const q = keyword.trim().toLowerCase()
  if (!q) return USER_POOL
  return USER_POOL.filter((user) => {
    return (
      String(user.fullName || '').toLowerCase().includes(q) ||
      String(user.username || '').toLowerCase().includes(q) ||
      String(user.code || '').toLowerCase().includes(q)
    )
  })
}

async function mockApis(page: Page, state: MockState) {
  await page.addInitScript(() => {
    localStorage.setItem('access_token', 'e2e-reference-lookup-token')
    localStorage.setItem('current_org_id', 'org-reference-lookup')
    localStorage.setItem('locale', 'en-US')
    localStorage.setItem('gzeams:lookup:recent:User', JSON.stringify(['user-john', 'user-alice']))
  })

  await page.route('**/*', async (route) => {
    const url = new URL(route.request().url())
    const pathname = url.pathname
    if (!pathname.startsWith('/api/')) return route.continue()

    if (pathname.endsWith('/api/system/objects/User/me/')) {
      return fulfillSuccess(route, {
        id: 'user-reference-lookup',
        username: 'admin',
        roles: ['admin'],
        permissions: ['*'],
        primaryOrganization: {
          id: 'org-reference-lookup',
          name: 'Lookup Org',
          code: 'LOOK'
        }
      })
    }

    if (pathname.endsWith('/api/system/menu/')) {
      return route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({ groups: [], items: [] })
      })
    }
    if (pathname.endsWith('/api/system/menu/flat/')) return fulfillSuccess(route, [])
    if (pathname.endsWith('/api/system/menu/config/')) {
      return route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({ schema: {}, common_groups: [], common_icons: [] })
      })
    }

    if (/\/api\/system\/objects\/Asset\/metadata\/?$/.test(pathname)) {
      return fulfillSuccess(route, {
        code: 'Asset',
        name: 'Asset',
        permissions: { view: true, add: true, change: true, delete: true }
      })
    }

    if (/\/api\/system\/objects\/Asset\/runtime\/?$/.test(pathname)) {
      return fulfillSuccess(route, buildRuntimeLayoutResponse())
    }

    if (/\/api\/system\/objects\/Asset\/fields\/?$/.test(pathname)) {
      return fulfillSuccess(route, {
        editable_fields: [],
        reverse_relations: [],
        context: 'form'
      })
    }

    if (/\/api\/system\/objects\/Asset\/asset-lookup-1\/?$/.test(pathname) && route.request().method() === 'GET') {
      return fulfillSuccess(route, {
        id: 'asset-lookup-1',
        assetName: 'Lookup Asset',
        assetCode: 'ASSET-LOOKUP-001',
        owner: state.ownerId
      })
    }

    if (/\/api\/system\/objects\/Asset\/asset-lookup-1\/?$/.test(pathname) && route.request().method() === 'PUT') {
      const body = route.request().postDataJSON() as Record<string, any>
      state.lastUpdatePayload = body
      const owner = String(body?.owner || body?.owner_id || body?.ownerId || '').trim()
      if (owner) state.ownerId = owner
      return fulfillSuccess(route, {
        id: 'asset-lookup-1',
        ...body
      })
    }

    if (pathname.endsWith('/api/system/objects/User/batch-get/')) {
      const body = route.request().postDataJSON() as { ids?: string[] }
      const ids = Array.isArray(body?.ids) ? body.ids.map((id) => String(id)) : []
      const map = new Map(USER_POOL.map((user) => [String(user.id), user]))
      const results = ids
        .map((id) => map.get(id))
        .filter((item): item is Record<string, any> => !!item)
      const missing_ids = ids.filter((id) => !map.has(id))
      return route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({ success: true, results, missing_ids })
      })
    }

    if (/\/api\/system\/objects\/User\/[^/]+\/$/.test(pathname)) {
      const id = pathname.split('/').filter(Boolean).pop() || ''
      const user = USER_POOL.find((item) => item.id === id)
      if (!user) {
        return route.fulfill({
          status: 404,
          contentType: 'application/json',
          body: JSON.stringify({ success: false, message: 'not found' })
        })
      }
      return fulfillSuccess(route, user)
    }

    if (pathname.endsWith('/api/system/objects/User/')) {
      const search = url.searchParams.get('search') || ''
      const pageNo = Number(url.searchParams.get('page') || '1')
      const pageSize = Number(url.searchParams.get('page_size') || '20')
      const filtered = pickUsersBySearch(search)
      const start = Math.max(0, (pageNo - 1) * pageSize)
      const results = filtered.slice(start, start + pageSize)
      return route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          success: true,
          count: filtered.length,
          results
        })
      })
    }

    return fulfillSuccess(route, {})
  })
}

test.describe('Reference Lookup Advanced Dialog', () => {
  test.setTimeout(120_000)

  test('should search in advanced dialog and submit selected reference id', async ({ page }) => {
    const state: MockState = {
      ownerId: 'user-alice',
      lastUpdatePayload: null
    }
    await mockApis(page, state)

    await page.goto('/objects/Asset/asset-lookup-1')
    await expect(page.locator('.load-error')).toHaveCount(0)
    const editButton = page.locator('.header-actions .el-button').filter({ hasText: /Edit|编辑/i }).first()
    await expect(editButton).toBeVisible({ timeout: 20_000 })
    await editButton.click()
    await expect(page.getByRole('button', { name: 'Cancel' })).toBeVisible()
    await expect(page.getByRole('button', { name: 'Save' })).toBeVisible()

    const ownerField = () => page.locator('.field-item').filter({
      has: page.locator('.field-label', { hasText: 'Owner' })
    }).first()
    const openOwnerLookup = async () => {
      const field = ownerField()
      await expect(field).toBeVisible()
      await field.locator('.el-select').first().click()
    }

    await openOwnerLookup()
    const dropdownFooter = page.locator('.reference-dropdown-footer').last()
    await expect(dropdownFooter).toBeVisible()
    await dropdownFooter.getByRole('button', { name: 'Advanced Search' }).click()

    const dialog = page.locator('.el-dialog').filter({
      has: page.locator('.lookup-toolbar')
    }).first()
    await expect(dialog).toBeVisible()

    await dialog.getByRole('button', { name: 'Reset' }).click()
    const groupTitles = dialog.locator('.lookup-cell__group-title')
    await expect(groupTitles).toContainText(['Recent Records (2)', 'Search Results (1)'])
    await dialog.locator('.lookup-toolbar__columns-trigger').click()
    const columnSettings = page.locator('.lookup-column-settings:visible').last()
    await expect(columnSettings).toBeVisible()
    await columnSettings.locator('.lookup-column-settings__item').filter({ hasText: 'Code' }).first().click()
    await expect(dialog.locator('.el-table__header-wrapper')).not.toContainText('Code')
    const idSettingRow = columnSettings.locator('.lookup-column-settings__row[data-column-key="id"]').first()
    await expect(idSettingRow.locator('.lookup-column-settings__lock-icon')).toBeVisible()
    await expect(idSettingRow.locator('.lookup-column-settings__move-up')).toBeDisabled()
    const headersAfterMove = dialog.locator('.el-table__header-wrapper thead th .cell')
    await expect(headersAfterMove.first()).toContainText('Name')
    await dialog.getByRole('button', { name: 'Cancel' }).click()
    await expect(dialog).toBeHidden()

    await openOwnerLookup()
    await page.locator('.reference-dropdown-footer').last().getByRole('button', { name: 'Advanced Search' }).click()
    const reopenDialog = page.locator('.el-dialog').filter({
      has: page.locator('.lookup-toolbar')
    }).first()
    await expect(reopenDialog).toBeVisible()
    await expect(reopenDialog.locator('.el-table__header-wrapper')).not.toContainText('Code')
    const reopenHeaders = reopenDialog.locator('.el-table__header-wrapper thead th .cell')
    await expect(reopenHeaders.first()).toContainText('Name')
    await reopenDialog.locator('.lookup-toolbar__columns-trigger').click()
    const reopenedColumnSettings = page.locator('.lookup-column-settings:visible').last()
    await expect(reopenedColumnSettings).toBeVisible()
    await reopenedColumnSettings.locator('.lookup-column-settings__profiles').getByText('Compact').click()
    await expect(reopenedColumnSettings.locator('.lookup-column-settings__profiles .is-selected')).toContainText('Compact')
    await reopenDialog.getByRole('button', { name: 'Cancel' }).click()
    await expect(reopenDialog).toBeHidden()

    await openOwnerLookup()
    await page.locator('.reference-dropdown-footer').last().getByRole('button', { name: 'Advanced Search' }).click()
    const compactDialog = page.locator('.el-dialog').filter({
      has: page.locator('.lookup-toolbar')
    }).first()
    await expect(compactDialog).toBeVisible()
    await compactDialog.locator('.lookup-toolbar__columns-trigger').click()
    const compactSettings = page.locator('.lookup-column-settings:visible').last()
    await expect(compactSettings.locator('.lookup-column-settings__profiles .is-selected')).toContainText('Compact')
    await expect(compactDialog.locator('.el-table__header-wrapper')).toContainText('email')
    await expect(compactDialog.locator('.el-table__header-wrapper')).not.toContainText('mobile')
    await compactSettings.locator('.lookup-column-settings__reset-columns').click()
    await expect(compactSettings.locator('.lookup-column-settings__profiles .is-selected')).toContainText('Standard')
    await compactDialog.getByRole('button', { name: 'Cancel' }).click()
    await expect(compactDialog).toBeHidden()

    await openOwnerLookup()
    await page.locator('.reference-dropdown-footer').last().getByRole('button', { name: 'Advanced Search' }).click()
    const resetDialog = page.locator('.el-dialog').filter({
      has: page.locator('.lookup-toolbar')
    }).first()
    await expect(resetDialog).toBeVisible()
    await resetDialog.locator('.lookup-toolbar__columns-trigger').click()
    const resetSettings = page.locator('.lookup-column-settings:visible').last()
    await expect(resetSettings.locator('.lookup-column-settings__profiles .is-selected')).toContainText('Standard')
    await resetSettings.locator('.lookup-column-settings__reset-columns').click()
    await expect(resetDialog.locator('.el-table__header-wrapper')).toContainText('Code')
    await expect(resetDialog.locator('.el-table__header-wrapper thead th .cell').first()).toContainText('Name')
    await resetDialog.getByRole('button', { name: 'Cancel' }).click()
    await expect(resetDialog).toBeHidden()

    await openOwnerLookup()
    await page.locator('.reference-dropdown-footer').last().getByRole('button', { name: 'Advanced Search' }).click()
    const afterResetDialog = page.locator('.el-dialog').filter({
      has: page.locator('.lookup-toolbar')
    }).first()
    await expect(afterResetDialog).toBeVisible()
    await expect(afterResetDialog.locator('.el-table__header-wrapper')).toContainText('Code')
    await expect(afterResetDialog.locator('.el-table__header-wrapper thead th .cell').first()).toContainText('Name')

    const firstRow = afterResetDialog.locator('.el-table__row').first()
    await firstRow.click()
    const activeBefore = (await afterResetDialog.locator('.el-table__row.is-active-single-row').first().textContent()) || ''
    await afterResetDialog.locator('.lookup-footer__meta').click()
    await page.keyboard.press('ArrowDown')
    const activeAfter = (await afterResetDialog.locator('.el-table__row.is-active-single-row').first().textContent()) || ''
    expect(activeAfter).not.toBe(activeBefore)

    await afterResetDialog.locator('.lookup-toolbar .el-input__inner').fill('john')
    await afterResetDialog.locator('.lookup-toolbar .el-input__inner').press('Enter')
    const johnRow = afterResetDialog.locator('.el-table__row').filter({ hasText: 'John Carter' }).first()
    await expect(johnRow).toBeVisible()
    await expect(afterResetDialog.locator('.lookup-cell__recent-tag')).toContainText('Recent')

    await johnRow.click()
    await afterResetDialog.getByRole('button', { name: 'Confirm' }).click()
    await expect(afterResetDialog).toBeHidden()

    await expect(ownerField()).toContainText('John Carter')
    const selectedCard = ownerField().locator('.reference-selected')
    if (await selectedCard.count()) {
      await selectedCard.first().hover()
      const hoverCard = page.locator('.reference-hover-card').filter({
        has: page.locator('.reference-hover-card__title', { hasText: 'John Carter' })
      }).last()
      await expect(hoverCard).toBeVisible()
      await expect(hoverCard).toContainText('user-john')
    }

    await page.getByRole('button', { name: 'Save' }).click()
    await expect.poll(() => state.lastUpdatePayload?.owner || state.lastUpdatePayload?.owner_id).toBe('user-john')

    await expect(page.locator('.detail-content')).toContainText('John Carter')
  })
})
