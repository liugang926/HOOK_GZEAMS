import { expect, type Locator, type Page } from '@playwright/test'
import {
  ensureInlineEditMode,
  getDetailFieldItem,
  type EnsureInlineEditModeOptions
} from './detail-page.helpers'

export {
  ensureInlineEditMode,
  getDetailFieldItem,
  type EnsureInlineEditModeOptions
} from './detail-page.helpers'

export interface OpenReferenceAdvancedLookupOptions extends EnsureInlineEditModeOptions {
  fieldLabel: string
  enterInlineEdit?: boolean
}

export async function openReferenceAdvancedLookup(
  page: Page,
  options: OpenReferenceAdvancedLookupOptions
): Promise<Locator> {
  if (options.enterInlineEdit) {
    await ensureInlineEditMode(page, options)
  }

  const field = getDetailFieldItem(page, options.fieldLabel)
  await expect(field).toBeVisible()

  const select = field.locator('.el-select').first()
  await expect(select).toBeVisible()
  await select.click()

  const dropdownFooter = page.locator('.reference-dropdown-footer:visible').last()
  await expect(dropdownFooter).toBeVisible()
  await dropdownFooter.getByRole('button', { name: 'Advanced Search' }).click()

  const dialog = page.locator('.el-dialog:visible').filter({
    has: page.locator('.lookup-toolbar')
  }).first()
  await expect(dialog).toBeVisible()
  return dialog
}

export async function openLookupColumnSettings(page: Page, dialog: Locator): Promise<Locator> {
  const trigger = dialog.getByRole('button', { name: /Columns/i }).first()
  await expect(trigger).toBeVisible()
  await trigger.click({ force: true })
  const settings = page.locator('.lookup-column-settings:visible').last()
  await expect(settings).toBeVisible()
  return settings
}

export async function selectLookupProfile(settings: Locator, profileLabel: string): Promise<void> {
  await settings.locator('.lookup-column-settings__profiles').getByText(profileLabel).click()
  await expect(settings.locator('.lookup-column-settings__profiles .is-selected')).toContainText(profileLabel)
}

export async function resetLookupColumns(settings: Locator): Promise<void> {
  await settings.locator('.lookup-column-settings__reset-columns').click()
}

export const getLookupHeaderCells = (dialog: Locator): Locator => {
  return dialog.locator('.el-table__header-wrapper thead th .cell')
}

export async function searchLookup(dialog: Locator, keyword: string): Promise<void> {
  const input = dialog.locator('.lookup-toolbar .el-input__inner')
  await input.fill(keyword)
  await input.press('Enter')
}
