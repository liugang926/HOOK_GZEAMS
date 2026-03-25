import { expect, type Locator, type Page } from '@playwright/test'

export interface EnsureInlineEditModeOptions {
  timeout?: number
  editButtonName?: RegExp
}

export interface WaitForDetailPageReadyOptions {
  timeout?: number
}

const matchActionName = (name: string | RegExp): string | RegExp => {
  const raw = typeof name === 'string' ? name.trim() : name.source.trim()

  if (/^Edit$/i.test(raw)) return /^(Edit|编辑)$/i
  if (/^Save$/i.test(raw)) return /^(Save|保存)$/i
  if (/^Cancel$/i.test(raw)) return /^(Cancel|取消)$/i
  if (/^Confirm$/i.test(raw)) return /^(Confirm|确定|确认)$/i
  if (/^Reset$/i.test(raw)) return /^(Reset|重置)$/i
  if (/^Advanced Search$/i.test(raw)) return /^(Advanced Search|高级搜索)$/i
  if (/^Columns$/i.test(raw)) return /^(Columns|列|列设置)$/i

  return name
}

export const getDetailContent = (page: Page): Locator => {
  return page.locator('.detail-content')
}

export const getDetailFieldItem = (
  pageOrRoot: Page | Locator,
  fieldLabel: string
): Locator => {
  const root = isPage(pageOrRoot) ? getDetailContent(pageOrRoot) : pageOrRoot
  const label = root.locator('.field-label', { hasText: fieldLabel }).first()
  return label.locator('xpath=ancestor::*[contains(concat(" ", normalize-space(@class), " "), " field-item ")][1]')
}

export const getHeaderActionButton = (page: Page, name: string | RegExp): Locator => {
  return page.locator('.header-actions').getByRole('button', { name: matchActionName(name) }).first()
}

export async function waitForLoadingMaskToClear(page: Page): Promise<void> {
  await page.locator('.el-loading-mask').first().waitFor({ state: 'detached' }).catch(() => {})
}

export async function expectNoLoadError(page: Page): Promise<void> {
  await expect(page.locator('.load-error')).toHaveCount(0)
}

export async function waitForDetailPageReady(
  page: Page,
  options: WaitForDetailPageReadyOptions = {}
): Promise<Locator> {
  const root = page.locator('.dynamic-detail-page, .base-detail-page, .object-detail-page').first()
  await expect(root).toBeVisible({ timeout: options.timeout ?? 15_000 })
  await expectNoLoadError(page)
  return root
}

export async function ensureInlineEditMode(
  page: Page,
  options: EnsureInlineEditModeOptions = {}
): Promise<void> {
  const timeout = options.timeout ?? 20_000
  const editButtonName = options.editButtonName ?? /Edit/i
  await waitForDetailPageReady(page, { timeout })
  await waitForLoadingMaskToClear(page)
  const cancelButton = page.getByRole('button', { name: matchActionName('Cancel') }).first()
  const saveButton = page.getByRole('button', { name: matchActionName('Save') }).first()
  const isEditing = async () => {
    return await cancelButton.isVisible().catch(() => false)
      && await saveButton.isVisible().catch(() => false)
  }
  const alreadyEditing = await expect.poll(isEditing, { timeout: Math.min(timeout, 10_000) }).toBe(true)
    .then(() => true)
    .catch(() => false)

  if (!alreadyEditing) {
    const editButton = page.getByRole('button', { name: matchActionName(editButtonName) }).first()
    await expect(editButton).toBeVisible({ timeout })
    await editButton.click()
  }

  await expect(cancelButton).toBeVisible()
  await expect(saveButton).toBeVisible()
}

function isPage(pageOrRoot: Page | Locator): pageOrRoot is Page {
  return 'goto' in pageOrRoot
}
