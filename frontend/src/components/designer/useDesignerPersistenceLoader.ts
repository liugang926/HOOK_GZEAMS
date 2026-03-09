import { ElMessage } from 'element-plus'
import { dynamicApi } from '@/api/dynamic'
import { pageLayoutApi } from '@/api/system'
import { resolveRuntimeLayout, type RuntimeLayoutResolution } from '@/platform/layout/runtimeLayoutResolver'
import { mergeFieldSources } from '@/platform/layout/unifiedFieldOrder'
import { cloneLayoutConfig, getDefaultLayoutConfig } from '@/utils/layoutValidation'
import { normalizeLayoutType } from '@/utils/layoutMode'
import type {
  AnyRecord,
  ApiDataEnvelope,
  UseDesignerPersistenceOptions
} from '@/components/designer/designerPersistenceTypes'
import type { LayoutConfig } from '@/components/designer/designerTypes'

interface UseDesignerPersistenceLoaderOptions extends UseDesignerPersistenceOptions {
  normalizeAndEnsureLayoutConfig: (rawConfig: LayoutConfig) => LayoutConfig
  populateSampleData: () => void
  t: (key: string) => string
}

export function useDesignerPersistenceLoader(options: UseDesignerPersistenceLoaderOptions) {
  function applyResolvedLayoutToDesigner(resolved: Partial<RuntimeLayoutResolution>): boolean {
    const editableFields = Array.isArray(resolved?.editableFields) ? resolved.editableFields : []
    if (editableFields.length > 0 && options.availableFields.value.length === 0) {
      const normalizedEditableFields = options.normalizeAvailableFields(editableFields as AnyRecord[])
      if (normalizedEditableFields.length > 0) {
        options.availableFields.value = normalizedEditableFields
      }
    }

    const activeConfig = resolved?.layoutConfig || null
    if (!activeConfig) return false
    if (!(activeConfig.sections?.length || activeConfig.columns?.length)) return false

    options.layoutConfig.value = options.normalizeAndEnsureLayoutConfig({ ...activeConfig } as LayoutConfig)
    return true
  }

  async function loadActiveLayoutPreview(): Promise<boolean> {
    if (!options.props.objectCode) return false
    try {
      const resolved = await resolveRuntimeLayout(options.props.objectCode, options.props.mode || 'edit', {
        includeRelations: true
      })
      if (applyResolvedLayoutToDesigner(resolved)) {
        options.sampleData.value = { ...options.sampleData.value }
        return true
      }
    } catch {
      // keep current canvas
    }
    return false
  }

  async function loadAvailableFields() {
    if (!options.props.objectCode) {
      options.previewReverseRelations.value = []
      return
    }

    try {
      const [runtimeResult, metadataResult] = await Promise.allSettled([
        resolveRuntimeLayout(options.props.objectCode, options.props.mode || 'edit', {
          includeRelations: true
        }),
        dynamicApi.getMetadata(options.props.objectCode)
      ])

      const runtimeFields =
        runtimeResult.status === 'fulfilled' && Array.isArray(runtimeResult.value?.editableFields)
          ? runtimeResult.value.editableFields
          : []
      const runtimeReverseRelations =
        runtimeResult.status === 'fulfilled' && Array.isArray((runtimeResult.value as RuntimeLayoutResolution)?.reverseRelations)
          ? (runtimeResult.value as RuntimeLayoutResolution).reverseRelations
          : []
      options.previewReverseRelations.value = options.mapPreviewReverseRelations(runtimeReverseRelations)

      const metadataPayload =
        metadataResult.status === 'fulfilled'
          ? options.unwrapData(metadataResult.value as ApiDataEnvelope<AnyRecord> | AnyRecord)
          : null
      const metadataFields = Array.isArray(metadataPayload?.fields) ? metadataPayload.fields : []
      const combined = mergeFieldSources(runtimeFields, metadataFields)

      if (combined.length > 0) {
        const normalizedFields = options.normalizeAvailableFields(combined)
        if (normalizedFields.length > 0) {
          options.availableFields.value = normalizedFields
          options.layoutConfig.value = options.normalizeAndEnsureLayoutConfig(options.layoutConfig.value)
          return
        }
      }
    } catch {
      options.previewReverseRelations.value = []
      if (options.availableFields.value.length === 0) {
        options.availableFields.value = [
          { code: 'name', name: 'Name', fieldType: 'text', isRequired: true },
          { code: 'code', name: 'Code', fieldType: 'text', isRequired: true },
          { code: 'status', name: 'Status', fieldType: 'select', isRequired: false },
          { code: 'description', name: 'Description', fieldType: 'textarea', isRequired: false }
        ]
        options.layoutConfig.value = options.normalizeAndEnsureLayoutConfig(options.layoutConfig.value)
      }
    }
  }

  async function setPreviewMode(mode: 'current' | 'active') {
    if (options.previewLoading.value) return
    if (options.previewMode.value === mode) return

    if (mode === 'current') {
      options.previewMode.value = mode
      if (options.currentLayoutSnapshot.value) {
        options.layoutConfig.value = cloneLayoutConfig(options.currentLayoutSnapshot.value)
        options.populateSampleData()
      }
      ElMessage.info(options.t('system.pageLayout.designer.messages.switchedToCustomMode'))
      return
    }

    options.previewLoading.value = true
    options.currentLayoutSnapshot.value = cloneLayoutConfig(options.layoutConfig.value)

    try {
      options.previewMode.value = mode
      const ok = await loadActiveLayoutPreview()
      if (!ok) {
        options.previewMode.value = 'current'
        if (options.currentLayoutSnapshot.value) {
          options.layoutConfig.value = cloneLayoutConfig(options.currentLayoutSnapshot.value)
          options.populateSampleData()
        }
        ElMessage.warning(options.t('system.pageLayout.designer.messages.noPreviewLayoutFallback'))
        return
      }
      ElMessage.success(options.t('system.pageLayout.designer.messages.switchedToPreviewMode'))
    } finally {
      options.previewLoading.value = false
    }
  }

  async function loadLayout() {
    options.previewMode.value = 'current'
    options.currentLayoutSnapshot.value = null
    options.previewLoading.value = false

    if (options.props.layoutId && options.props.mode !== 'readonly') {
      try {
        const layout = options.unwrapData(await pageLayoutApi.detail(options.props.layoutId) as ApiDataEnvelope<AnyRecord> | AnyRecord)
        const rawConfig = (layout.layoutConfig || layout.layout_config || getDefaultLayoutConfig(options.props.mode)) as LayoutConfig
        options.layoutConfig.value = options.normalizeAndEnsureLayoutConfig(rawConfig)
        options.layoutMode.value = options.layoutConfig.value.layoutType === 'Compact' ? 'Compact' : 'Detail'
        options.isDefault.value = Boolean(layout.isDefault ?? layout.is_default)
        options.isPublished.value = String(layout.status || '') === 'published'
        options.layoutVersion.value = String(layout.version || options.layoutVersion.value)
        await loadAvailableFields()
        options.populateSampleData()
        return
      } catch {
        // fall through
      }
    }

    if (options.props.objectCode) {
      try {
        const resolved = await resolveRuntimeLayout(options.props.objectCode, options.props.mode || 'edit', {
          includeRelations: true
        })
        applyResolvedLayoutToDesigner(resolved)
        options.layoutMode.value = options.layoutConfig.value.layoutType === 'Compact' ? 'Compact' : 'Detail'
        await loadAvailableFields()
        options.isDefault.value = !!resolved?.isDefault
        options.isPublished.value = resolved?.layoutStatus === 'published'
        options.layoutVersion.value = resolved?.layoutVersion || options.layoutVersion.value
        options.populateSampleData()
        return
      } catch {
        // fall through
      }
    }

    if (options.props.layoutConfig && (options.props.layoutConfig.sections?.length || options.props.layoutConfig.columns?.length)) {
      options.layoutConfig.value = options.normalizeAndEnsureLayoutConfig({ ...options.props.layoutConfig } as LayoutConfig)
      options.layoutMode.value = options.layoutConfig.value.layoutType === 'Compact' ? 'Compact' : 'Detail'
      options.populateSampleData()
      return
    }

    if (options.props.objectCode) {
      try {
        const defaultData = options.unwrapData(await pageLayoutApi.getDefault(options.props.objectCode, normalizeLayoutType(options.props.mode)) as ApiDataEnvelope<AnyRecord> | AnyRecord)
        const backendConfig = defaultData?.layoutConfig || defaultData?.layout_config
        if (backendConfig && (backendConfig.sections?.length || backendConfig.columns?.length)) {
          options.layoutConfig.value = options.normalizeAndEnsureLayoutConfig({ ...backendConfig } as LayoutConfig)
          options.layoutMode.value = options.layoutConfig.value.layoutType === 'Compact' ? 'Compact' : 'Detail'
          options.populateSampleData()
        }
      } catch {
        // ignore fallback miss
      }
    }
  }

  return {
    loadAvailableFields,
    loadLayout,
    setPreviewMode
  }
}
