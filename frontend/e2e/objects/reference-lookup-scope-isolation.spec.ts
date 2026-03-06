import { expect, test, type Page, type Route } from '@playwright/test'

const OBJECT_CODE = 'Asset'
const RECORD_ID = 'asset-lookup-scope-1'
const USER_SCOPE = 'user-reference-scope'
const PREF_KEYS = ['owner', 'owner_id']
const USER_SCOPES = [USER_SCOPE, 'anonymous']

type MockState = {
  ownerId: string
}

const USER_POOL: Array<Record<string, any>> = [
  { id: 'user-alice', fullName: 'Alice Stone', username: 'alice', name: 'Alice Stone', code: 'U-ALICE', email: 'alice@example.com', mobile: '13800000001' },
  { id: 'user-john', fullName: 'John Carter', username: 'john', name: 'John Carter', code: 'U-JOHN', email: 'john@example.com', mobile: '13800000002' },
  { id: 'user-zoe', fullName: 'Zoe Green', username: 'zoe', name: 'Zoe Green', code: 'U-ZOE', email: 'zoe@example.com', mobile: '13800000003' }
]

function fulfillSuccess(route: Route, data: unknown) {
  return route.fulfill({
    status: 200,
    contentType: 'application/json',
    body: JSON.stringify({ success: true, data })
  })
}

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

async function mockApis(page: Page, state: MockState) {
  await page.addInitScript(([prefKeys, userScopes]) => {
    (window as any).__lookupGetKeys = []
    const originalGetItem = localStorage.getItem.bind(localStorage)
    localStorage.getItem = ((key: string) => {
      (window as any).__lookupGetKeys.push(String(key || ''))
      return originalGetItem(key)
    }) as Storage['getItem']

    localStorage.setItem('access_token', 'e2e-reference-scope-token')
    localStorage.setItem('current_org_id', 'org-reference-scope')
    localStorage.setItem('locale', 'en-US')

    for (const key of prefKeys as string[]) {
      for (const userScope of userScopes as string[]) {
        localStorage.setItem(
          `gzeams:lookup:columns:User:object-detail:Asset:${key}:${userScope}`,
          JSON.stringify({ hidden: ['username'], order: [], widths: {}, profile: 'custom' })
        )
        localStorage.setItem(
          `gzeams:lookup:columns:User:object-edit:Asset:${key}:${userScope}`,
          JSON.stringify({ hidden: [], order: [], widths: {}, profile: 'standard' })
        )
      }
    }
  }, [PREF_KEYS, USER_SCOPES])

  await page.route('**/*', async (route) => {
    const url = new URL(route.request().url())
    const pathname = url.pathname
    if (!pathname.startsWith('/api/')) return route.continue()

    if (pathname.endsWith('/api/system/objects/User/me/')) {
      return fulfillSuccess(route, {
        id: USER_SCOPE,
        username: 'admin',
        roles: ['admin'],
        permissions: ['*'],
        primaryOrganization: {
          id: 'org-reference-scope',
          name: 'Lookup Scope Org',
          code: 'LSCOPE'
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

    if (pathname.endsWith(`/api/system/objects/${OBJECT_CODE}/metadata/`)) {
      return fulfillSuccess(route, {
        code: OBJECT_CODE,
        name: OBJECT_CODE,
        permissions: { view: true, add: true, change: true, delete: true }
      })
    }

    if (pathname.endsWith(`/api/system/objects/${OBJECT_CODE}/runtime/`)) {
      return fulfillSuccess(route, buildRuntimeLayoutResponse())
    }

    if (pathname.endsWith(`/api/system/objects/${OBJECT_CODE}/fields/`)) {
      return fulfillSuccess(route, {
        editable_fields: [],
        reverse_relations: [],
        context: 'form'
      })
    }

    if (pathname.endsWith(`/api/system/objects/${OBJECT_CODE}/${RECORD_ID}/`) && route.request().method() === 'GET') {
      return fulfillSuccess(route, {
        id: RECORD_ID,
        assetName: 'Scope Isolation Asset',
        assetCode: 'ASSET-SCOPE-001',
        owner: state.ownerId
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

    if (pathname.endsWith('/api/system/objects/User/')) {
      return route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          success: true,
          count: USER_POOL.length,
          results: USER_POOL
        })
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

    if (pathname.endsWith(`/api/system/objects/${OBJECT_CODE}/relations/`)) {
      return fulfillSuccess(route, {
        objectCode: OBJECT_CODE,
        locale: 'en-US',
        relations: []
      })
    }

    return fulfillSuccess(route, {})
  })
}

async function openAdvancedLookup(page: Page, options?: { enterInlineEdit?: boolean }) {
  if (options?.enterInlineEdit) {
    const editButton = page.locator('.header-actions .el-button').filter({ hasText: /Edit|编辑/i }).first()
    await expect(editButton).toBeVisible()
    await editButton.click()
    await expect(page.getByRole('button', { name: 'Cancel' })).toBeVisible()
    await expect(page.getByRole('button', { name: 'Save' })).toBeVisible()
  }

  const ownerField = page.locator('.reference-field .el-select').first()
  await expect(ownerField).toBeVisible()
  await ownerField.click()

  const dropdownFooter = page.locator('.reference-dropdown-footer').last()
  await expect(dropdownFooter).toBeVisible()
  await dropdownFooter.getByRole('button', { name: 'Advanced Search' }).click()

  const dialog = page.locator('.el-dialog').filter({
    has: page.locator('.lookup-toolbar')
  }).first()
  await expect(dialog).toBeVisible()
  return dialog
}

test.describe('Reference Lookup Scope Isolation', () => {
  test('detail and edit pages should not share lookup preference scope', async ({ page }) => {
    const state: MockState = {
      ownerId: 'user-alice'
    }
    await mockApis(page, state)

    await page.goto(`/objects/${OBJECT_CODE}/${RECORD_ID}`)
    await expect(page.locator('.load-error')).toHaveCount(0)
    const detailDialog = await openAdvancedLookup(page, { enterInlineEdit: true })
    await expect.poll(async () => {
      return await page.evaluate(() => {
        return Object.keys(localStorage).filter((key) => key.startsWith('gzeams:lookup:columns:User:object-detail:Asset')).length
      })
    }).toBeGreaterThan(0)
    const detailGetKeys = await page.evaluate(() => {
      return ((window as any).__lookupGetKeys || []) as string[]
    })
    expect(detailGetKeys.some((key) => key.includes('gzeams:lookup:columns:User:object-detail:Asset'))).toBe(true)
    await expect(detailDialog.locator('.el-table__header-wrapper')).not.toContainText('Code')
    await detailDialog.getByRole('button', { name: 'Cancel' }).click()
    await expect(detailDialog).toBeHidden()

    await page.goto(`/objects/${OBJECT_CODE}/${RECORD_ID}/edit`)
    await expect(page.locator('.load-error')).toHaveCount(0)
    const editDialog = await openAdvancedLookup(page)
    const editGetKeys = await page.evaluate(() => {
      return ((window as any).__lookupGetKeys || []) as string[]
    })
    expect(editGetKeys.some((key) => key.includes('gzeams:lookup:columns:User:object-edit:Asset'))).toBe(true)
    await expect(editDialog.locator('.el-table__header-wrapper')).toContainText('Code')
    await editDialog.getByRole('button', { name: 'Cancel' }).click()
    await expect(editDialog).toBeHidden()
  })
})
