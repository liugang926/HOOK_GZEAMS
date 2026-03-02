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

test.describe('Finance Voucher Detail Regression', () => {
  test('voucher list detail action should navigate and render business fields', async ({ page }) => {
    await page.addInitScript(() => {
      localStorage.setItem('access_token', 'e2e-finance-regression-token')
      localStorage.setItem('current_org_id', 'org-regression')
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
    await expect(page.locator('.el-table')).toBeVisible()
    await expect(page.locator('.voucher-list-page')).toContainText(VOUCHER_NO)

    const voucherRow = page.locator('.el-table__row', { hasText: VOUCHER_NO }).first()
    await expect(voucherRow).toBeVisible()
    await voucherRow.locator('button').first().click()

    await expect(page).toHaveURL(new RegExp(`/finance/vouchers/${VOUCHER_ID}$`))
    await expect(page.locator('.voucher-detail-page')).toBeVisible()
    await expect(page.locator('.voucher-detail-page')).toContainText(VOUCHER_NO)
    await expect(page.locator('.voucher-detail-page')).toContainText('Regression voucher for detail rendering')
    await expect(page.locator('.voucher-detail-page')).toContainText('Depreciation Expense')
    await expect(page.locator('.voucher-detail-page')).toContainText('Accumulated Depreciation')
  })
})
