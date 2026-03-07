import { expect, test, type Page } from '@playwright/test'
import { openReferenceAdvancedLookup } from '../helpers/reference-lookup.helpers'
import {
  type LookupTraceWindow,
} from '../helpers/reference-lookup.fixtures'
import { fulfillSuccess, mockReferenceLookupApis } from '../helpers/reference-lookup.api'

const OBJECT_CODE = 'Asset'
const RECORD_ID = 'asset-lookup-scope-1'
const USER_SCOPE = 'user-reference-scope'
const PREF_KEYS = ['owner', 'owner_id']
const USER_SCOPES = [USER_SCOPE, 'anonymous']

type MockState = {
  ownerId: string
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
  const localStorageEntries: Record<string, string> = {}
  for (const key of PREF_KEYS) {
    for (const userScope of USER_SCOPES) {
      localStorageEntries[`gzeams:lookup:columns:User:object-detail:Asset:${key}:${userScope}`] = JSON.stringify({
        hidden: ['username'],
        order: [],
        widths: {},
        profile: 'custom'
      })
      localStorageEntries[`gzeams:lookup:columns:User:object-edit:Asset:${key}:${userScope}`] = JSON.stringify({
        hidden: [],
        order: [],
        widths: {},
        profile: 'standard'
      })
    }
  }

  await mockReferenceLookupApis(page, {
    accessToken: 'e2e-reference-scope-token',
    orgId: 'org-reference-scope',
    currentUser: {
      id: USER_SCOPE,
      username: 'admin',
      roles: ['admin'],
      permissions: ['*'],
      primaryOrganization: {
        id: 'org-reference-scope',
        name: 'Lookup Scope Org',
        code: 'LSCOPE'
      }
    },
    trackLookupGetKeys: true,
    localStorageEntries,
    handleApiRoute: async ({ route, pathname }) => {
      if (pathname.endsWith(`/api/system/objects/${OBJECT_CODE}/metadata/`)) {
        await fulfillSuccess(route, {
          code: OBJECT_CODE,
          name: OBJECT_CODE,
          permissions: { view: true, add: true, change: true, delete: true }
        })
        return true
      }

      if (pathname.endsWith(`/api/system/objects/${OBJECT_CODE}/runtime/`)) {
        await fulfillSuccess(route, buildRuntimeLayoutResponse())
        return true
      }

      if (pathname.endsWith(`/api/system/objects/${OBJECT_CODE}/fields/`)) {
        await fulfillSuccess(route, {
          editable_fields: [],
          reverse_relations: [],
          context: 'form'
        })
        return true
      }

      if (pathname.endsWith(`/api/system/objects/${OBJECT_CODE}/${RECORD_ID}/`) && route.request().method() === 'GET') {
        await fulfillSuccess(route, {
          id: RECORD_ID,
          assetName: 'Scope Isolation Asset',
          assetCode: 'ASSET-SCOPE-001',
          owner: state.ownerId
        })
        return true
      }

      if (pathname.endsWith(`/api/system/objects/${OBJECT_CODE}/relations/`)) {
        await fulfillSuccess(route, {
          objectCode: OBJECT_CODE,
          locale: 'en-US',
          relations: []
        })
        return true
      }

      return false
    }
  })
}

test.describe('Reference Lookup Scope Isolation', () => {
  test('detail and edit pages should not share lookup preference scope', async ({ page }) => {
    const state: MockState = {
      ownerId: 'user-alice'
    }
    await mockApis(page, state)

    await page.goto(`/objects/${OBJECT_CODE}/${RECORD_ID}`)
    await expect(page.locator('.load-error')).toHaveCount(0)
    const detailDialog = await openReferenceAdvancedLookup(page, {
      fieldLabel: 'Owner',
      enterInlineEdit: true
    })
    await expect.poll(async () => {
      return await page.evaluate(() => {
        return Object.keys(localStorage).filter((key) => key.startsWith('gzeams:lookup:columns:User:object-detail:Asset')).length
      })
    }).toBeGreaterThan(0)
    const detailGetKeys = await page.evaluate(() => {
      return (window as LookupTraceWindow).__lookupGetKeys || []
    })
    expect(detailGetKeys.some((key) => key.includes('gzeams:lookup:columns:User:object-detail:Asset'))).toBe(true)
    await expect(detailDialog.locator('.el-table__header-wrapper')).not.toContainText('Code')
    await detailDialog.getByRole('button', { name: 'Cancel' }).click()
    await expect(detailDialog).toBeHidden()

    await page.goto(`/objects/${OBJECT_CODE}/${RECORD_ID}/edit`)
    await expect(page.locator('.load-error')).toHaveCount(0)
    const editDialog = await openReferenceAdvancedLookup(page, {
      fieldLabel: 'Owner'
    })
    const editGetKeys = await page.evaluate(() => {
      return (window as LookupTraceWindow).__lookupGetKeys || []
    })
    expect(editGetKeys.some((key) => key.includes('gzeams:lookup:columns:User:object-edit:Asset'))).toBe(true)
    await expect(editDialog.locator('.el-table__header-wrapper')).toContainText('Code')
    await editDialog.getByRole('button', { name: 'Cancel' }).click()
    await expect(editDialog).toBeHidden()
  })
})
