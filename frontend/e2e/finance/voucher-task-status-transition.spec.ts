import { test, expect, type Route } from '@playwright/test'

const VOUCHER_ID = 'voucher-task-1'
const VOUCHER_NO = 'VCH-TASK-001'
const SYNC_TASK_ID = 'sync-task-001'

const voucherRecord = {
  id: VOUCHER_ID,
  voucherNo: VOUCHER_NO,
  businessType: 'depreciation',
  voucherDate: '2026-02-25',
  totalAmount: 500,
  status: 'approved',
  summary: 'Task status transition regression',
  notes: 'Check running to success transition',
  entryCount: 1,
  isBalanced: true,
  entries: [
    {
      lineNo: 1,
      accountCode: '6601',
      accountName: 'Depreciation Expense',
      debitAmount: 500,
      creditAmount: 0,
      description: 'Task transition line'
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

function buildMetadata() {
  return {
    code: 'FinanceVoucher',
    name: 'Finance Voucher',
    module: 'Finance',
    icon: 'Tickets',
    fields: [
      { code: 'voucherNo', name: 'Voucher No', fieldType: 'text', showInDetail: true },
      { code: 'summary', name: 'Summary', fieldType: 'textarea', showInDetail: true },
      { code: 'status', name: 'Status', fieldType: 'select', showInDetail: true },
    ],
    permissions: { view: true, add: true, change: true, delete: true }
  }
}

function buildDetailRuntime() {
  return {
    runtime_version: 1,
    object_code: 'FinanceVoucher',
    mode: 'edit',
    context: 'form',
    fields: {
      editable_fields: [
        { code: 'voucherNo', name: 'Voucher No', fieldType: 'text', showInForm: true, showInDetail: true },
        { code: 'summary', name: 'Summary', fieldType: 'textarea', showInForm: true, showInDetail: true },
        { code: 'status', name: 'Status', fieldType: 'select', showInForm: true, showInDetail: true },
      ],
      reverse_relations: []
    },
    layout: {
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
              { fieldCode: 'status', label: 'Status', span: 12 },
              { fieldCode: 'summary', label: 'Summary', span: 24 },
            ]
          }
        ]
      },
      status: 'published',
      version: '1.0.0'
    },
    permissions: { view: true, add: true, change: true, delete: false },
    workbench: {
      workspace_mode: 'extended',
      primary_entry_route: '/objects/FinanceVoucher',
      legacy_aliases: ['/finance/vouchers'],
      toolbar: {
        primary_actions: [],
        secondary_actions: [
          {
            code: 'retry_push',
            label_key: 'finance.actions.retryPush',
            action_path: 'retry',
            button_type: 'warning',
            confirm_message_key: 'finance.messages.confirmRetryPush',
            visible_when: { statuses: ['approved', 'posted'] }
          }
        ]
      },
      detail_panels: [
        {
          code: 'sync_status',
          title_key: 'finance.panels.syncStatus',
          component: 'finance-voucher-sync-status',
          visible_when: { statuses: ['approved', 'posted'] }
        },
        {
          code: 'integration_logs',
          title_key: 'finance.panels.integrationLogs',
          component: 'finance-voucher-integration-logs'
        }
      ],
      async_indicators: [
        {
          code: 'sync_task',
          type: 'sync-task',
          visible_when: { statuses: ['approved', 'posted'] }
        }
      ]
    },
    is_default: true
  }
}

test.describe('Finance Voucher Task Status Transition', () => {
  test('retry should show running then success task state on unified detail page', async ({ page }) => {
    await page.addInitScript(() => {
      localStorage.setItem('access_token', 'e2e-finance-task-token')
      localStorage.setItem('current_org_id', 'org-regression')
      localStorage.setItem('locale', 'en-US')
    })

    let syncTaskDetailCalls = 0

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
        return fulfillSuccess(route, buildMetadata())
      }

      if (pathname.endsWith('/api/system/objects/FinanceVoucher/runtime/')) {
        return fulfillSuccess(route, buildDetailRuntime())
      }

      if (pathname.endsWith('/api/system/objects/FinanceVoucher/fields/')) {
        return fulfillSuccess(route, {
          editable_fields: buildDetailRuntime().fields.editable_fields,
          reverse_relations: [],
          context: 'form'
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

      if (pathname.endsWith(`/api/system/objects/FinanceVoucher/${VOUCHER_ID}/retry/`)) {
        return fulfillSuccess(route, {
          success: true,
          queued: true,
          task_id: 'celery-task-001',
          sync_task_id: SYNC_TASK_ID
        })
      }

      if (pathname.endsWith(`/api/integration/sync-tasks/${SYNC_TASK_ID}/`)) {
        syncTaskDetailCalls += 1
        if (syncTaskDetailCalls <= 1) {
          return fulfillSuccess(route, {
            id: SYNC_TASK_ID,
            status: 'running',
            status_display: 'Running'
          })
        }
        return fulfillSuccess(route, {
          id: SYNC_TASK_ID,
          status: 'success',
          status_display: 'Success'
        })
      }

      return fulfillSuccess(route, {})
    })

    await page.goto(`/objects/FinanceVoucher/${VOUCHER_ID}`)
    const detailPage = page.locator('.dynamic-detail-page').first()
    await expect(detailPage).toBeVisible({ timeout: 15000 })
    await expect(detailPage).toContainText(VOUCHER_NO, { timeout: 15000 })

    await page.getByRole('button', { name: 'Retry Push' }).click()
    await page.locator('.el-message-box__btns .el-button--primary').click()

    await expect(detailPage).toContainText(SYNC_TASK_ID, { timeout: 15000 })
    await expect(detailPage).toContainText('Running', { timeout: 15000 })
    await expect(detailPage).toContainText('Success', { timeout: 20000 })
  })
})
