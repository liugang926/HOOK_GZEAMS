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

type DesignerRenderMode = 'design' | 'preview'
type DesignerActionOptions = {
  timeout?: number
  ensureEnabled?: boolean
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

export async function setDesignerRenderMode(
  page: Page,
  mode: DesignerRenderMode,
  timeout = 5000
): Promise<void> {
  const toggle = page.getByTestId(
    mode === 'design' ? 'layout-render-design-button' : 'layout-render-preview-button'
  )

  await expect(toggle).toBeVisible({ timeout })
  await toggle.click()

  if (mode === 'design') {
    await expect(page.getByTestId('layout-field-panel')).toBeVisible({ timeout })
    await expect(page.getByTestId('layout-property-panel')).toBeVisible({ timeout })
    return
  }

  await expect(page.getByTestId('layout-field-panel')).toHaveCount(0, { timeout })
  await expect(page.getByTestId('layout-property-panel')).toHaveCount(0, { timeout })
}

export async function clickDesignerSaveDraft(
  page: Page,
  options: DesignerActionOptions = {}
): Promise<void> {
  const timeout = options.timeout ?? 5000
  const button = page.getByTestId('layout-save-button').first()
  await expect(button).toBeVisible({ timeout })
  if (options.ensureEnabled !== false) {
    await expect(button).toBeEnabled({ timeout })
  }
  await button.click()
}

export async function clickDesignerPublish(
  page: Page,
  options: DesignerActionOptions = {}
): Promise<void> {
  const timeout = options.timeout ?? 5000
  const button = page.getByTestId('layout-publish-button').first()
  await expect(button).toBeVisible({ timeout })
  if (options.ensureEnabled !== false) {
    await expect(button).toBeEnabled({ timeout })
  }
  await button.click()
}

export async function confirmDialogPrimary(
  page: Page,
  timeout = 5000
): Promise<void> {
  const dialog = page.locator('.el-message-box').first()
  await expect(dialog).toBeVisible({ timeout })
  await dialog.locator('.el-message-box__btns .el-button--primary').first().click()
}

export async function clickDesignerResetAndConfirm(
  page: Page,
  options: DesignerActionOptions = {}
): Promise<void> {
  const timeout = options.timeout ?? 5000
  const button = page.getByTestId('layout-reset-button').first()
  await expect(button).toBeVisible({ timeout })
  if (options.ensureEnabled !== false) {
    await expect(button).toBeEnabled({ timeout })
  }
  await button.click()
  await confirmDialogPrimary(page, timeout)
}
