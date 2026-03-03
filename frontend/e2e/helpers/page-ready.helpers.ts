import { expect, type Page } from '@playwright/test'

type ObjectListReadyOptions = {
  expectedContent?: string
  timeout?: number
  requireSearchForm?: boolean
  requireColumnManagerTrigger?: boolean
}

type DesignerReadyOptions = {
  timeout?: number
  requiredFieldCode?: string
}

type DesignerSectionClickOptions = {
  title?: string
  index?: number
  timeout?: number
}

const DEFAULT_TIMEOUT = 30000

export async function waitForObjectListReady(
  page: Page,
  options: ObjectListReadyOptions = {}
): Promise<void> {
  const timeout = options.timeout ?? DEFAULT_TIMEOUT
  const listRoot = page.locator('.dynamic-list-page').first()

  await expect(page.getByRole('heading', { level: 2 }).first()).toBeVisible({ timeout })
  await expect(listRoot).toBeVisible({ timeout })

  if (options.expectedContent) {
    await expect(listRoot).toContainText(options.expectedContent, { timeout })
  }

  if (options.requireSearchForm !== false) {
    await expect(page.locator('.search-form-container').first()).toBeVisible({ timeout })
  }

  if (options.requireColumnManagerTrigger === true) {
    await expect(page.locator('.column-manager-trigger .el-button').first()).toBeVisible({ timeout })
  }
}

export async function gotoObjectListAndWait(
  page: Page,
  objectCode: string,
  options: ObjectListReadyOptions = {}
): Promise<void> {
  await page.goto(`/objects/${objectCode}`, { waitUntil: 'load' })
  await waitForObjectListReady(page, options)
}

export async function waitForDesignerReady(
  page: Page,
  options: DesignerReadyOptions = {}
): Promise<void> {
  const timeout = options.timeout ?? DEFAULT_TIMEOUT

  await expect(page.getByTestId('layout-designer')).toBeVisible({ timeout })

  if (options.requiredFieldCode) {
    const fieldCards = page.locator(
      `[data-testid="layout-canvas-field"][data-field-code="${options.requiredFieldCode}"]`
    )
    await expect.poll(async () => fieldCards.count(), { timeout }).toBeGreaterThan(0)

    const visibleField = page.locator(
      `[data-testid="layout-canvas-field"][data-field-code="${options.requiredFieldCode}"]:visible`
    ).first()
    if (await visibleField.count()) {
      await expect(visibleField).toBeVisible({ timeout: Math.min(timeout, 5000) })
    }
  } else {
    await expect(page.getByTestId('layout-canvas')).toBeVisible({ timeout })
  }
}

export async function gotoDesignerAndWait(
  page: Page,
  url: string,
  options: DesignerReadyOptions = {}
): Promise<void> {
  await page.goto(url, { waitUntil: 'load' })
  await waitForDesignerReady(page, options)
}

export async function clickDesignerSectionHeader(
  page: Page,
  options: DesignerSectionClickOptions = {}
): Promise<void> {
  const timeout = options.timeout ?? 5000
  const index = options.index ?? 0

  let headers = page.getByTestId('layout-section-header')
  if (options.title) {
    headers = headers.filter({ hasText: options.title })
  }

  const target = headers.nth(index)
  await expect(target).toBeVisible({ timeout })
  await target.click()
}
