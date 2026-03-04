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
  createdByName: 'admin',
  createdAt: '2026-02-25T08:00:00+08:00',
  updatedByName: 'admin',
  updatedAt: '2026-02-25T08:15:00+08:00'
}

function fulfillSuccess(route: Route, data: unknown) {
  return route.fulfill({
    status: 200,
    contentType: 'application/json',
    body: JSON.stringify({ success: true, data })
  })
}

test.describe('Finance Voucher Task Status Transition', () => {
  test('retry should show running then success task state on detail page', async ({ page }) => {
    await page.addInitScript(() => {
      localStorage.setItem('access_token', 'e2e-finance-task-token')
      localStorage.setItem('current_org_id', 'org-regression')
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

      if (pathname.endsWith(`/api/system/objects/FinanceVoucher/${VOUCHER_ID}/`)) {
        return fulfillSuccess(route, voucherRecord)
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

    await page.goto(`/finance/vouchers/${VOUCHER_ID}`)
    await expect(page.locator('.voucher-detail-page')).toBeVisible({ timeout: 15000 })
    await expect(page.locator('.voucher-detail-page')).toContainText(VOUCHER_NO, { timeout: 15000 })

    await page.getByRole('button', { name: 'Retry Push' }).click()
    await page.locator('.el-message-box__btns .el-button--primary').click()

    await expect(page.locator('.voucher-detail-page')).toContainText(SYNC_TASK_ID, { timeout: 15000 })
    await expect(page.locator('.voucher-detail-page')).toContainText('Running', { timeout: 15000 })
    await expect(page.locator('.voucher-detail-page')).toContainText('Success', { timeout: 20000 })
  })
})
