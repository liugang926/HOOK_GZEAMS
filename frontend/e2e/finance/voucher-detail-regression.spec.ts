import { test, expect, type Route } from '@playwright/test'

const VOUCHER_ID = 'voucher-reg-1'
const VOUCHER_NO = 'VCH-REG-001'

const voucherRecord = {
  id: VOUCHER_ID,
  voucherNo: VOUCHER_NO,
  businessType: 'depreciation',
  voucherDate: '2026-02-25',
  totalAmount: 1200.5,
  status: 'approved',
  summary: 'Regression voucher for detail rendering',
  notes: 'Finance detail page must render business fields',
  entryCount: 2,
  isBalanced: true,
  entries: [
    {
      lineNo: 1,
      accountCode: '6601',
      accountName: 'Depreciation Expense',
      debitAmount: 600.25,
      creditAmount: 0,
      description: 'Monthly depreciation (debit)'
    },
    {
      lineNo: 2,
      accountCode: '2801',
      accountName: 'Accumulated Depreciation',
      debitAmount: 0,
      creditAmount: 600.25,
      description: 'Monthly depreciation (credit)'
    }
  ],
  createdBy: { username: 'admin' },
  createdAt: '2026-02-25T08:00:00+08:00',
  updatedBy: { username: 'admin' },
  updatedAt: '2026-02-25T08:15:00+08:00'
}

function fulfillSuccess(route: Route, data: unknown) {
  return route.fulfill({
    status: 200,
    contentType: 'application/json',
    body: JSON.stringify({ success: true, data })
  })
}

function buildFinanceVoucherMetadata() {
  return {
    code: 'FinanceVoucher',
    name: 'Finance Voucher',
    module: 'Finance',
    icon: 'Tickets',
    fields: [
      { code: 'voucherNo', name: 'Voucher No', fieldType: 'text', isSearchable: true, showInList: true, showInDetail: true },
      { code: 'businessType', name: 'Business Type', fieldType: 'text', showInList: true, showInDetail: true },
      { code: 'voucherDate', name: 'Voucher Date', fieldType: 'date', showInList: true, showInDetail: true },
      { code: 'summary', name: 'Summary', fieldType: 'textarea', showInList: true, showInDetail: true },
      { code: 'totalAmount', name: 'Total Amount', fieldType: 'currency', showInList: true, showInDetail: true },
      { code: 'status', name: 'Status', fieldType: 'select', showInList: true, showInDetail: true },
    ],
    permissions: { view: true, add: true, change: true, delete: true },
    layouts: {
      list: {
        columns: [
          { fieldCode: 'voucherNo', label: 'Voucher No', visible: true },
          { fieldCode: 'summary', label: 'Summary', visible: true },
          { fieldCode: 'status', label: 'Status', visible: true },
        ]
      }
    }
  }
}

function buildFinanceVoucherRuntime(mode: 'list' | 'edit') {
  return {
    runtime_version: 1,
    object_code: 'FinanceVoucher',
    mode,
    context: mode === 'list' ? 'list' : 'form',
    fields: {
      editable_fields: [
        { code: 'voucherNo', name: 'Voucher No', fieldType: 'text', showInList: true, showInForm: true, showInDetail: true },
        { code: 'businessType', name: 'Business Type', fieldType: 'text', showInList: true, showInForm: true, showInDetail: true },
        { code: 'voucherDate', name: 'Voucher Date', fieldType: 'date', showInList: true, showInForm: true, showInDetail: true },
        { code: 'summary', name: 'Summary', fieldType: 'textarea', showInList: true, showInForm: true, showInDetail: true },
        { code: 'totalAmount', name: 'Total Amount', fieldType: 'currency', showInList: true, showInForm: true, showInDetail: true },
        { code: 'status', name: 'Status', fieldType: 'select', showInList: true, showInForm: true, showInDetail: true },
      ],
      reverse_relations: []
    },
    layout: mode === 'list'
      ? {
        layout_type: 'list',
        layout_config: {
          columns: [
            { fieldCode: 'voucherNo', label: 'Voucher No', visible: true },
            { fieldCode: 'summary', label: 'Summary', visible: true },
            { fieldCode: 'status', label: 'Status', visible: true },
          ]
        },
        status: 'published',
        version: '1.0.0'
      }
      : {
        layout_type: 'form',
        layout_config: {
          sections: [
            {
              id: 'basic',
              type: 'section',
              title: 'Basic Information',
              columns: 2,
              fields: [
                { fieldCode: 'voucherNo', label: 'Voucher No', span: 12 },
                { fieldCode: 'businessType', label: 'Business Type', span: 12 },
                { fieldCode: 'voucherDate', label: 'Voucher Date', span: 12 },
                { fieldCode: 'status', label: 'Status', span: 12 },
                { fieldCode: 'summary', label: 'Summary', span: 24 },
                { fieldCode: 'totalAmount', label: 'Total Amount', span: 12 },
              ]
            }
          ]
        },
        status: 'published',
        version: '1.0.0'
      },
    permissions: { view: true, add: true, change: true, delete: true },
    workbench: mode === 'edit'
      ? {
        workspace_mode: 'extended',
        primary_entry_route: '/objects/FinanceVoucher',
        legacy_aliases: ['/finance/vouchers'],
        toolbar: {
          primary_actions: [
            {
              code: 'post',
              label_key: 'finance.actions.post',
              action_path: 'post',
              button_type: 'success',
              visible_when: { statuses: ['approved'] }
            }
          ],
          secondary_actions: [
            {
              code: 'retry_push',
              label_key: 'finance.actions.retryPush',
              action_path: 'retry',
              button_type: 'warning',
              visible_when: { statuses: ['approved', 'posted'] }
            }
          ]
        },
        detail_panels: [
          { code: 'voucher_entries', title_key: 'finance.panels.entries', component: 'finance-voucher-entries' },
          { code: 'integration_logs', title_key: 'finance.panels.integrationLogs', component: 'finance-voucher-integration-logs' }
        ],
        async_indicators: []
      }
      : {
        workspace_mode: 'extended',
        primary_entry_route: '/objects/FinanceVoucher',
        legacy_aliases: ['/finance/vouchers'],
        toolbar: { primary_actions: [], secondary_actions: [] },
        detail_panels: [],
        async_indicators: []
      },
    is_default: true
  }
}

test.describe('Finance Voucher Detail Regression', () => {
  test('legacy finance voucher route should redirect into unified workspace and render voucher details', async ({ page }) => {
    await page.addInitScript(() => {
      localStorage.setItem('access_token', 'e2e-finance-regression-token')
      localStorage.setItem('current_org_id', 'org-regression')
      localStorage.setItem('locale', 'en-US')
    })

    await page.route('**/*', async (route) => {
      const url = new URL(route.request().url())
      const pathname = url.pathname

      if (!pathname.startsWith('/api/')) {
        return route.continue()
      }

      if (pathname.endsWith('/api/system/objects/User/me/')) {
        return fulfillSuccess(route, {
          id: 'user-regression',
          username: 'admin',
          roles: ['admin'],
          permissions: ['*'],
          primaryOrganization: { id: 'org-regression', name: 'Regression Org', code: 'REG' }
        })
      }

      if (pathname.endsWith('/api/system/menu/')) {
        return route.fulfill({
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify({ groups: [], items: [] })
        })
      }

      if (pathname.endsWith('/api/system/menu/flat/')) {
        return fulfillSuccess(route, [])
      }

      if (pathname.endsWith('/api/system/menu/config/')) {
        return route.fulfill({
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify({ schema: {}, common_groups: [], common_icons: [] })
        })
      }

      if (pathname.endsWith('/api/system/objects/FinanceVoucher/metadata/')) {
        return fulfillSuccess(route, buildFinanceVoucherMetadata())
      }

      if (pathname.endsWith('/api/system/objects/FinanceVoucher/runtime/')) {
        const mode = url.searchParams.get('mode') === 'list' ? 'list' : 'edit'
        return fulfillSuccess(route, buildFinanceVoucherRuntime(mode))
      }

      if (pathname.endsWith('/api/system/objects/FinanceVoucher/fields/')) {
        return fulfillSuccess(route, {
          editable_fields: buildFinanceVoucherRuntime('edit').fields.editable_fields,
          reverse_relations: [],
          context: 'form'
        })
      }

      if (pathname.endsWith('/api/system/objects/FinanceVoucher/')) {
        return fulfillSuccess(route, {
          count: 1,
          next: null,
          previous: null,
          results: [voucherRecord]
        })
      }

      if (pathname.endsWith(`/api/system/objects/FinanceVoucher/${VOUCHER_ID}/`)) {
        return fulfillSuccess(route, voucherRecord)
      }

      if (pathname.endsWith(`/api/system/objects/FinanceVoucher/${VOUCHER_ID}/actions/`)) {
        return fulfillSuccess(route, {
          objectCode: 'FinanceVoucher',
          recordId: VOUCHER_ID,
          actions: []
        })
      }

      if (pathname.endsWith(`/api/system/objects/FinanceVoucher/${VOUCHER_ID}/integration-logs/`)) {
        return fulfillSuccess(route, [])
      }

      if (pathname.endsWith(`/api/system/objects/FinanceVoucher/${VOUCHER_ID}/post/`)) {
        return fulfillSuccess(route, { status: 'posted' })
      }

      if (pathname.endsWith(`/api/system/objects/FinanceVoucher/${VOUCHER_ID}/retry/`)) {
        return fulfillSuccess(route, {})
      }

      return fulfillSuccess(route, {})
    })

    await page.goto('/finance/vouchers')
    await expect(page).toHaveURL(/\/objects\/FinanceVoucher$/, { timeout: 15000 })
    await expect(page.locator('.dynamic-list-page')).toBeVisible({ timeout: 15000 })
    await expect(page.locator('.dynamic-list-page')).toContainText(VOUCHER_NO, { timeout: 15000 })

    const voucherEntry = page.locator('.el-table__row, .mobile-card').filter({ hasText: VOUCHER_NO }).first()
    await expect(voucherEntry).toBeVisible({ timeout: 15000 })
    await voucherEntry.click()

    await expect(page).toHaveURL(new RegExp(`/objects/FinanceVoucher/${VOUCHER_ID}$`), { timeout: 15000 })
    const detailPage = page.locator('.dynamic-detail-page').first()
    await expect(detailPage).toBeVisible({ timeout: 15000 })
    await expect(detailPage).toContainText(VOUCHER_NO, { timeout: 15000 })
    await expect(detailPage).toContainText('Regression voucher for detail rendering', { timeout: 15000 })
    await expect(detailPage).toContainText('Depreciation Expense', { timeout: 15000 })
    await expect(detailPage).toContainText('Accumulated Depreciation', { timeout: 15000 })
  })
})
