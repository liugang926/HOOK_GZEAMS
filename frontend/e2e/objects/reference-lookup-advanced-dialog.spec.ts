import { expect, test, type Page } from '@playwright/test'
import {
  ensureInlineEditMode,
  getDetailFieldItem,
  getLookupHeaderCells,
  openLookupColumnSettings,
  openReferenceAdvancedLookup,
  resetLookupColumns,
  searchLookup,
  selectLookupProfile
} from '../helpers/reference-lookup.helpers'
import { fulfillSuccess, mockReferenceLookupApis } from '../helpers/reference-lookup.api'

type MockState = {
  ownerId: string
  lastUpdatePayload: Record<string, unknown> | null
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

async function mockApis(page: Page, state: MockState) {
  await mockReferenceLookupApis(page, {
    accessToken: 'e2e-reference-lookup-token',
    orgId: 'org-reference-lookup',
    currentUser: {
      id: 'user-reference-lookup',
      username: 'admin',
      roles: ['admin'],
      permissions: ['*'],
      primaryOrganization: {
        id: 'org-reference-lookup',
        name: 'Lookup Org',
        code: 'LOOK'
      }
    },
    localStorageEntries: {
      'gzeams:lookup:recent:User:object-detail:Asset': JSON.stringify(['user-john', 'user-alice'])
    },
    searchKeys: ['fullName', 'username', 'code'],
    handleApiRoute: async ({ route, pathname }) => {
      if (/\/api\/system\/objects\/Asset\/metadata\/?$/.test(pathname)) {
        await fulfillSuccess(route, {
          code: 'Asset',
          name: 'Asset',
          permissions: { view: true, add: true, change: true, delete: true }
        })
        return true
      }

      if (/\/api\/system\/objects\/Asset\/runtime\/?$/.test(pathname)) {
        await fulfillSuccess(route, buildRuntimeLayoutResponse())
        return true
      }

      if (/\/api\/system\/objects\/Asset\/fields\/?$/.test(pathname)) {
        await fulfillSuccess(route, {
          editable_fields: [],
          reverse_relations: [],
          context: 'form'
        })
        return true
      }

      if (/\/api\/system\/objects\/Asset\/asset-lookup-1\/?$/.test(pathname) && route.request().method() === 'GET') {
        await fulfillSuccess(route, {
          id: 'asset-lookup-1',
          assetName: 'Lookup Asset',
          assetCode: 'ASSET-LOOKUP-001',
          owner: state.ownerId
        })
        return true
      }

      if (/\/api\/system\/objects\/Asset\/asset-lookup-1\/?$/.test(pathname) && route.request().method() === 'PUT') {
        const body = route.request().postDataJSON() as Record<string, unknown>
        state.lastUpdatePayload = body
        const owner = String(body?.owner || body?.owner_id || body?.ownerId || '').trim()
        if (owner) state.ownerId = owner
        await fulfillSuccess(route, {
          id: 'asset-lookup-1',
          ...body
        })
        return true
      }

      return false
    }
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
    await ensureInlineEditMode(page, { timeout: 20_000 })

    const ownerField = () => getDetailFieldItem(page, 'Owner')
    const dialog = await openReferenceAdvancedLookup(page, { fieldLabel: 'Owner' })

    await dialog.getByRole('button', { name: /^(Reset|重置)$/i }).click({ force: true })
    const groupTitles = dialog.locator('.lookup-cell__group-title')
    await expect(groupTitles).toContainText(['Recent Records (2)', 'Search Results (1)'])
    const columnSettings = await openLookupColumnSettings(page, dialog)
    await columnSettings.locator('.lookup-column-settings__item').filter({ hasText: 'Code' }).first().click()
    await expect(dialog.locator('.el-table__header-wrapper')).not.toContainText('Code')
    const idSettingRow = columnSettings.locator('.lookup-column-settings__row[data-column-key="id"]').first()
    await expect(idSettingRow.locator('.lookup-column-settings__lock-icon')).toBeVisible()
    await expect(idSettingRow.locator('.lookup-column-settings__move-up')).toBeDisabled()
    const headersAfterMove = getLookupHeaderCells(dialog)
    await expect(headersAfterMove.first()).toContainText('Name')
    await dialog.getByRole('button', { name: /^(Cancel|取消)$/i }).click({ force: true })
    await expect(dialog).toBeHidden()

    const reopenDialog = await openReferenceAdvancedLookup(page, { fieldLabel: 'Owner' })
    await expect(reopenDialog.locator('.el-table__header-wrapper')).not.toContainText('Code')
    const reopenHeaders = getLookupHeaderCells(reopenDialog)
    await expect(reopenHeaders.first()).toContainText('Name')
    const reopenedColumnSettings = await openLookupColumnSettings(page, reopenDialog)
    await selectLookupProfile(reopenedColumnSettings, 'Compact')
    await reopenDialog.getByRole('button', { name: /^(Cancel|取消)$/i }).click({ force: true })
    await expect(reopenDialog).toBeHidden()

    const compactDialog = await openReferenceAdvancedLookup(page, { fieldLabel: 'Owner' })
    const compactSettings = await openLookupColumnSettings(page, compactDialog)
    await expect(compactSettings.locator('.lookup-column-settings__profiles .is-selected')).toContainText('Compact')
    await expect(compactDialog.locator('.el-table__header-wrapper')).toContainText('email')
    await expect(compactDialog.locator('.el-table__header-wrapper')).not.toContainText('mobile')
    await resetLookupColumns(compactSettings)
    await expect(compactSettings.locator('.lookup-column-settings__profiles .is-selected')).toContainText('Standard')
    await compactDialog.getByRole('button', { name: /^(Cancel|取消)$/i }).click({ force: true })
    await expect(compactDialog).toBeHidden()

    const resetDialog = await openReferenceAdvancedLookup(page, { fieldLabel: 'Owner' })
    const resetSettings = await openLookupColumnSettings(page, resetDialog)
    await expect(resetSettings.locator('.lookup-column-settings__profiles .is-selected')).toContainText('Standard')
    await resetLookupColumns(resetSettings)
    await expect(resetDialog.locator('.el-table__header-wrapper')).toContainText('Code')
    await expect(getLookupHeaderCells(resetDialog).first()).toContainText('Name')
    await resetDialog.getByRole('button', { name: /^(Cancel|取消)$/i }).click({ force: true })
    await expect(resetDialog).toBeHidden()

    const afterResetDialog = await openReferenceAdvancedLookup(page, { fieldLabel: 'Owner' })
    await expect(afterResetDialog.locator('.el-table__header-wrapper')).toContainText('Code')
    await expect(getLookupHeaderCells(afterResetDialog).first()).toContainText('Name')

    const activeRow = afterResetDialog.locator('.el-table__row.is-active-single-row').first()
    await afterResetDialog.locator('.lookup-footer__meta').click({ force: true })
    await page.keyboard.press('ArrowUp')
    await expect(activeRow).toContainText('John Carter')
    await page.keyboard.press('ArrowDown')
    await expect(activeRow).toContainText('Alice Stone')

    await searchLookup(afterResetDialog, 'john')
    const johnRow = afterResetDialog.locator('.el-table__row').filter({ hasText: 'John Carter' }).first()
    await expect(johnRow).toBeVisible()
    await expect(afterResetDialog.locator('.lookup-cell__recent-tag').first()).toContainText('Recent')

    await afterResetDialog.locator('.lookup-footer__meta').click({ force: true })
    await page.keyboard.press('ArrowUp')
    await expect(activeRow).toContainText('John Carter')
    const confirmButton = afterResetDialog.getByRole('button', { name: /^(Confirm|确定|确认)$/i })
    await expect(confirmButton).toBeEnabled()
    await confirmButton.click({ force: true })
    await expect(afterResetDialog).toBeHidden()

    const selectedCard = ownerField().locator('.reference-selected')
    if (await selectedCard.count()) {
      await selectedCard.first().hover()
      const hoverCard = page.locator('.reference-hover-card').filter({
        has: page.locator('.reference-hover-card__title', { hasText: 'John Carter' })
      }).last()
      await expect(hoverCard).toBeVisible()
      await expect(hoverCard).toContainText('user-john')
    }

    await page.getByRole('button', { name: /^(Save|保存)$/i }).click()
    await expect.poll(() => state.lastUpdatePayload?.owner || state.lastUpdatePayload?.owner_id).toBe('user-john')

    await expect(page.locator('.detail-content')).toContainText('user-john')
  })
})
