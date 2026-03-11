export const dynamicFormTranslations: Record<string, string> = {
  'common.actions.back': 'Back',
  'common.actions.cancel': 'Cancel',
  'common.actions.create': 'Create',
  'common.actions.edit': 'Edit',
  'common.actions.refresh': 'Refresh',
  'common.actions.save': 'Save',
  'common.messages.createSuccess': 'Created successfully',
  'common.messages.loadFailed': 'Load failed',
  'common.messages.operationFailed': 'Operation failed',
  'common.messages.permissionDenied': 'Permission denied',
  'common.messages.permissionDeniedHint': 'You do not have access to this page.',
  'common.messages.updateSuccess': 'Updated successfully',
}

export const createMappedI18nMock = (
  translations: Record<string, string>,
  locale = 'zh-CN'
) => ({
  t: (key: string) => translations[key] || key,
  te: () => false,
  locale: { value: locale },
})

export const createPassthroughI18nMock = (locale = 'zh-CN', te = false) => ({
  t: (key: string) => key,
  te: () => te,
  locale: { value: locale },
})
