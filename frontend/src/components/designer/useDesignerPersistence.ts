import { useI18n } from 'vue-i18n'
import { useDesignerPersistenceActions } from '@/components/designer/useDesignerPersistenceActions'
import { useDesignerPersistenceLoader } from '@/components/designer/useDesignerPersistenceLoader'
import { useDesignerPersistenceShared } from '@/components/designer/useDesignerPersistenceShared'
import type { UseDesignerPersistenceOptions } from '@/components/designer/designerPersistenceTypes'

export function useDesignerPersistence(options: UseDesignerPersistenceOptions) {
  const { t } = useI18n()

  const shared = useDesignerPersistenceShared(options)
  const loader = useDesignerPersistenceLoader({
    ...options,
    normalizeAndEnsureLayoutConfig: shared.normalizeAndEnsureLayoutConfig,
    populateSampleData: shared.populateSampleData,
    t
  })
  const actions = useDesignerPersistenceActions({
    ...options,
    isReadonlyMode: shared.isReadonlyMode,
    normalizeAndEnsureLayoutConfig: shared.normalizeAndEnsureLayoutConfig,
    extractConfigPayload: shared.extractConfigPayload,
    buildReadonlyModeOverride: shared.buildReadonlyModeOverride,
    prepareLayoutConfig: shared.prepareLayoutConfig,
    populateSampleData: shared.populateSampleData,
    loadAvailableFields: loader.loadAvailableFields,
    t
  })

  return {
    isReadonlyMode: shared.isReadonlyMode,
    normalizeAndEnsureLayoutConfig: shared.normalizeAndEnsureLayoutConfig,
    populateSampleData: shared.populateSampleData,
    loadLayout: loader.loadLayout,
    loadAvailableFields: loader.loadAvailableFields,
    setPreviewMode: loader.setPreviewMode,
    handleSave: actions.handleSave,
    handlePublish: actions.handlePublish,
    handleReset: actions.handleReset
  }
}
