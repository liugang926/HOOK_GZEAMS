import { computed } from 'vue'
import { useI18n } from 'vue-i18n'
import { ElMessage } from 'element-plus'
import { preparePersistLayoutConfig } from '@/platform/layout/layoutPersistGuard'
import { buildLayoutFieldDropper, compileLayoutSchema } from '@/platform/layout/layoutCompiler'
import { normalizeLayoutConfigFieldAliases } from '@/components/designer/designerLayoutAdapters'
import {
  cloneLayoutConfig,
  type LayoutType
} from '@/utils/layoutValidation'
import { normalizeLayoutType } from '@/utils/layoutMode'
import type {
  AnyRecord,
  ApiDataEnvelope,
  UseDesignerPersistenceOptions
} from '@/components/designer/designerPersistenceTypes'
import type { LayoutConfig } from '@/components/designer/designerTypes'

interface UseDesignerPersistenceSharedResult {
  isReadonlyMode: ReturnType<typeof computed<boolean>>
  resolveLayoutType: () => LayoutType
  normalizeAndEnsureLayoutConfig: (rawConfig: LayoutConfig) => LayoutConfig
  extractConfigPayload: (raw: unknown) => LayoutConfig
  buildReadonlyModeOverride: (sharedBase: LayoutConfig, readonlyConfig: LayoutConfig) => LayoutConfig
  prepareLayoutConfig: () => LayoutConfig | null
  populateSampleData: () => void
}

export function useDesignerPersistenceShared(
  options: UseDesignerPersistenceOptions
): UseDesignerPersistenceSharedResult {
  const { t } = useI18n()

  const isReadonlyMode = computed(() => options.props.mode === 'readonly')

  const resolveLayoutType = (): LayoutType => {
    return normalizeLayoutType(options.props.mode) as LayoutType
  }

  function resolveDesignerRuntimeMode(): 'edit' | 'readonly' | 'search' {
    if (options.props.mode === 'readonly') return 'readonly'
    if (options.props.mode === 'search') return 'search'
    return 'edit'
  }

  function normalizeAndEnsureLayoutConfig(rawConfig: LayoutConfig): LayoutConfig {
    const compiled = compileLayoutSchema({
      mode: resolveDesignerRuntimeMode(),
      fields: options.availableFields.value as Array<Record<string, unknown>>,
      layoutConfig: rawConfig || { sections: [] },
      ensureIds: true
    }).layoutConfig as LayoutConfig

    return normalizeLayoutConfigFieldAliases(compiled)
  }

  function extractConfigPayload(raw: unknown): LayoutConfig {
    const payload = options.unwrapData(raw as ApiDataEnvelope<AnyRecord> | AnyRecord)
    const config = payload?.layoutConfig || payload?.layout_config || payload?.layout || { sections: [] }
    return normalizeAndEnsureLayoutConfig(config as LayoutConfig)
  }

  function buildReadonlyModeOverride(sharedBase: LayoutConfig, readonlyConfig: LayoutConfig): LayoutConfig {
    const next = cloneLayoutConfig(normalizeAndEnsureLayoutConfig(sharedBase || { sections: [] })) as LayoutConfig & {
      mode_overrides?: AnyRecord
    }
    const normalizedReadonly = normalizeAndEnsureLayoutConfig(readonlyConfig || { sections: [] })
    const existingOverrides = (next.modeOverrides || next.mode_overrides || {}) as AnyRecord

    next.modeOverrides = {
      ...existingOverrides,
      readonly: {
        sections: normalizedReadonly.sections || [],
        actions: normalizedReadonly.actions || []
      }
    }

    return next as LayoutConfig
  }

  const prepareLayoutConfig = (): LayoutConfig | null => {
    try {
      const availableFieldCodes = options.availableFields.value.map((item) => String(item.code || '').trim()).filter(Boolean)
      const dropFieldCode = buildLayoutFieldDropper({
        knownFieldCodes: availableFieldCodes
      })
      const snapshotConfig = options.buildLayoutConfigWithPlacementSnapshot(options.layoutConfig.value || { sections: [] } as LayoutConfig)
      const prepared = preparePersistLayoutConfig(snapshotConfig, {
        layoutType: resolveLayoutType(),
        availableFieldCodes,
        dropFieldCode
      }) as LayoutConfig
      prepared.layoutType = options.layoutMode.value
      options.layoutConfig.value = prepared
      return prepared
    } catch (error: unknown) {
      ElMessage.error(error instanceof Error ? error.message : t('system.pageLayout.designer.messages.invalidLayoutConfig'))
      return null
    }
  }

  function populateSampleData() {
    const data: AnyRecord = {}
    for (const section of options.layoutConfig.value.sections || []) {
      if (section.type === 'tab') {
        for (const tab of section.tabs || []) {
          for (const field of tab.fields || []) {
            data[field.fieldCode] = field.defaultValue ?? ''
          }
        }
      } else if (section.type === 'collapse') {
        for (const item of section.items || []) {
          for (const field of item.fields || []) {
            data[field.fieldCode] = field.defaultValue ?? ''
          }
        }
      } else {
        for (const field of section.fields || []) {
          data[field.fieldCode] = field.defaultValue ?? ''
        }
      }
    }

    if (!String(data.id || '').trim()) data.id = 'preview-record'
    if (!String(data.code || '').trim()) data.code = 'PREVIEW-001'
    if (!String(data.name || '').trim()) data.name = options.props.layoutName || options.previewObjectName.value || 'Preview Record'
    options.sampleData.value = data
  }

  return {
    isReadonlyMode,
    resolveLayoutType,
    normalizeAndEnsureLayoutConfig,
    extractConfigPayload,
    buildReadonlyModeOverride,
    prepareLayoutConfig,
    populateSampleData
  }
}
