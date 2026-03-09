import { ElMessage, ElMessageBox } from 'element-plus'
import { pageLayoutApi } from '@/api/system'
import { normalizeFieldType } from '@/utils/fieldType'
import { normalizeLayoutType } from '@/utils/layoutMode'
import { storage } from '@/utils/storage'
import type {
  AnyRecord,
  ApiDataEnvelope,
  UseDesignerPersistenceOptions
} from '@/components/designer/designerPersistenceTypes'
import type {
  LayoutConfig,
  LayoutSection
} from '@/components/designer/designerTypes'

interface UseDesignerPersistenceActionsOptions extends UseDesignerPersistenceOptions {
  isReadonlyMode: { value: boolean }
  normalizeAndEnsureLayoutConfig: (rawConfig: LayoutConfig) => LayoutConfig
  extractConfigPayload: (raw: unknown) => LayoutConfig
  buildReadonlyModeOverride: (sharedBase: LayoutConfig, readonlyConfig: LayoutConfig) => LayoutConfig
  prepareLayoutConfig: () => LayoutConfig | null
  populateSampleData: () => void
  loadAvailableFields: () => Promise<void>
  t: (key: string) => string
}

export function useDesignerPersistenceActions(options: UseDesignerPersistenceActionsOptions) {
  function clearAutosaveCache() {
    if (options.props.objectCode && options.props.mode) {
      storage.remove(`layout_autosave_${options.props.objectCode}_${options.props.mode}`)
    }
  }

  async function resolveSharedEditLayout(readonlySeed?: LayoutConfig): Promise<AnyRecord> {
    if (!options.props.objectCode) {
      throw new Error('Missing objectCode')
    }

    if (options.sharedEditLayoutId.value) {
      const existing = options.unwrapData(await pageLayoutApi.detail(options.sharedEditLayoutId.value) as ApiDataEnvelope<AnyRecord> | AnyRecord)
      if (existing?.id) return existing
    }

    let activeEdit: unknown = null
    try {
      activeEdit = await pageLayoutApi.byObjectAndMode(options.props.objectCode, 'edit')
    } catch {
      activeEdit = null
    }

    const normalizedEdit = options.unwrapData(activeEdit as ApiDataEnvelope<AnyRecord> | AnyRecord | null)
    if (normalizedEdit?.id && !normalizedEdit?.isDefault) {
      options.sharedEditLayoutId.value = String(normalizedEdit.id)
      return normalizedEdit
    }

    const sourceBusinessObject =
      normalizedEdit?.businessObject ||
      normalizedEdit?.business_object ||
      options.props.businessObjectId

    let baseLayoutConfig: LayoutConfig | null = null
    if (normalizedEdit?.layoutConfig || normalizedEdit?.layout_config) {
      baseLayoutConfig = options.extractConfigPayload(normalizedEdit)
    } else {
      try {
        const defaultEdit = await pageLayoutApi.getDefault(options.props.objectCode, 'edit')
        baseLayoutConfig = options.extractConfigPayload(defaultEdit)
      } catch {
        baseLayoutConfig = null
      }
    }

    const fallbackSeed = options.normalizeAndEnsureLayoutConfig(readonlySeed || { sections: [] })
    const createPayload = {
      layoutCode: `${options.props.objectCode}_edit_shared_${Date.now()}`,
      layoutName: `${options.props.objectCode} Edit Shared`,
      mode: 'edit',
      business_object: sourceBusinessObject || options.props.businessObjectId,
      status: 'draft',
      isDefault: false,
      layoutConfig: baseLayoutConfig || fallbackSeed
    }

    const created = options.unwrapData(await pageLayoutApi.create(createPayload as Record<string, unknown>) as ApiDataEnvelope<AnyRecord> | AnyRecord)
    if (!created?.id) {
      if (options.props.layoutId) {
        const legacy = options.unwrapData(await pageLayoutApi.detail(options.props.layoutId) as ApiDataEnvelope<AnyRecord> | AnyRecord)
        if (legacy?.id) {
          options.sharedEditLayoutId.value = String(legacy.id)
          return legacy
        }
      }
      throw new Error('Failed to resolve shared edit layout')
    }
    options.sharedEditLayoutId.value = String(created.id)
    return created
  }

  async function saveReadonlyToSharedLayout(readonlyConfig: LayoutConfig, publish = false) {
    const targetLayout = await resolveSharedEditLayout(readonlyConfig)
    const targetLayoutId = String(targetLayout.id)
    const targetMode = String(targetLayout?.mode || '').toLowerCase()
    const targetType = String(targetLayout?.layoutType || targetLayout?.layout_type || '').toLowerCase()
    const isEditTarget = targetMode === 'edit' || targetType === 'form'
    const mergedConfig = isEditTarget
      ? options.buildReadonlyModeOverride(options.extractConfigPayload(targetLayout), readonlyConfig)
      : options.normalizeAndEnsureLayoutConfig(readonlyConfig)

    await pageLayoutApi.partialUpdate(targetLayoutId, {
      layoutConfig: mergedConfig,
      status: 'draft'
    })

    if (publish) {
      await pageLayoutApi.publish(targetLayoutId, {
        change_summary: 'Publish readonly override on shared edit layout'
      })
    }

    options.sharedEditLayoutId.value = targetLayoutId
    return {
      id: targetLayoutId,
      layoutConfig: mergedConfig
    }
  }

  async function handleSave() {
    options.saving.value = true
    try {
      const sanitizedConfig = options.prepareLayoutConfig()
      if (!sanitizedConfig) return
      const data: AnyRecord = {
        layoutConfig: sanitizedConfig,
        status: 'draft',
        view_mode: options.layoutMode.value
      }

      if (options.isReadonlyMode.value && options.props.objectCode) {
        const result = await saveReadonlyToSharedLayout(sanitizedConfig, false)
        data.sharedLayoutId = result.id
        if (options.props.layoutId && options.props.layoutId !== result.id) {
          try {
            await pageLayoutApi.partialUpdate(options.props.layoutId, {
              layoutConfig: sanitizedConfig,
              status: 'draft'
            } as Record<string, unknown>)
          } catch {
            // shared edit layout is source of truth
          }
        }
      } else if (options.props.layoutId) {
        await pageLayoutApi.partialUpdate(options.props.layoutId, data as Record<string, unknown>)
      } else {
        await pageLayoutApi.create({
          ...data,
          layoutCode: `${options.props.objectCode}_${options.props.mode}_${Date.now()}`,
          layoutName: options.props.layoutName,
          mode: options.props.mode,
          business_object: options.props.businessObjectId
        } as Record<string, unknown>)
      }

      clearAutosaveCache()
      ElMessage.success(options.t('system.pageLayout.designer.messages.layoutSaved'))
      options.emitSave(data)
    } catch (error: unknown) {
      ElMessage.error(options.readErrorMessage(error) || options.t('system.pageLayout.designer.messages.saveFailed'))
    } finally {
      options.saving.value = false
    }
  }

  async function handlePublish() {
    options.publishing.value = true
    try {
      const sanitizedConfig = options.prepareLayoutConfig()
      if (!sanitizedConfig) return

      if (options.isReadonlyMode.value && options.props.objectCode) {
        const result = await saveReadonlyToSharedLayout(sanitizedConfig, true)
        if (options.props.layoutId && options.props.layoutId !== result.id) {
          try {
            await pageLayoutApi.partialUpdate(options.props.layoutId, {
              layoutConfig: sanitizedConfig,
              status: 'draft'
            } as Record<string, unknown>)
            await pageLayoutApi.publish(options.props.layoutId, {
              change_summary: 'Sync readonly snapshot from shared edit layout'
            })
          } catch {
            // shared edit layout is source of truth
          }
        }
      } else if (options.props.layoutId) {
        await pageLayoutApi.partialUpdate(options.props.layoutId, {
          layoutConfig: sanitizedConfig,
          status: 'draft',
          view_mode: options.layoutMode.value
        })
        await pageLayoutApi.publish(options.props.layoutId, {
          change_summary: 'Publish layout'
        })
      } else {
        const createResult = options.unwrapData(await pageLayoutApi.create({
          layoutConfig: sanitizedConfig,
          layoutCode: `${options.props.objectCode}_${options.props.mode}_${Date.now()}`,
          layoutName: options.props.layoutName,
          mode: options.props.mode,
          business_object: options.props.businessObjectId,
          status: 'draft'
        } as Record<string, unknown>) as ApiDataEnvelope<{ id: string }> | { id: string })
        await pageLayoutApi.publish(createResult.id, {
          change_summary: 'Publish layout',
          set_as_default: true
        })
      }

      options.isPublished.value = true
      clearAutosaveCache()
      ElMessage.success(options.t('system.pageLayout.designer.messages.layoutPublished'))
      options.emitPublished(options.layoutConfig.value)
    } catch (error: unknown) {
      ElMessage.error(options.readErrorMessage(error) || options.t('system.pageLayout.designer.messages.publishFailed'))
    } finally {
      options.publishing.value = false
    }
  }

  async function handleReset() {
    try {
      await ElMessageBox.confirm(
        options.t('system.pageLayout.designer.messages.resetConfirm'),
        options.t('system.pageLayout.designer.messages.resetConfirmTitle'),
        { type: 'warning' }
      )
    } catch {
      return
    }

    try {
      if (!options.props.objectCode) throw new Error('Missing objectCode')

      const result = await pageLayoutApi.getDefault(options.props.objectCode, normalizeLayoutType(options.props.mode))
      const payload = options.unwrapData(result as ApiDataEnvelope<AnyRecord> | AnyRecord)
      const backendConfig = payload?.layoutConfig || payload?.layout_config || payload?.layout || null

      if (
        backendConfig &&
        (
          (Array.isArray(backendConfig.sections) && backendConfig.sections.length > 0) ||
          (Array.isArray(backendConfig.columns) && backendConfig.columns.length > 0) ||
          Object.keys(backendConfig).length > 0
        )
      ) {
        options.layoutConfig.value = options.normalizeAndEnsureLayoutConfig(backendConfig as LayoutConfig)
        await options.loadAvailableFields()
        options.populateSampleData()
      } else {
        await options.loadAvailableFields()
        const defaultSection: LayoutSection = {
          id: `section-${Date.now()}`,
          type: 'section',
          title: options.t('system.pageLayout.designer.defaults.basicInformation'),
          collapsible: true,
          collapsed: false,
          columns: 2,
          border: false,
          fields: options.availableFields.value.map((field, index) => ({
            id: `field-${Date.now()}-${index}`,
            fieldCode: field.code,
            label: field.name || field.displayName || field.code,
            fieldType: normalizeFieldType(field.fieldType || field.field_type || field.type || 'text'),
            span: 12,
            required: field.isRequired || false,
            options: field.options,
            referenceObject: field.referenceObject || field.relatedObject,
            componentProps: field.componentProps,
            dictionaryType: field.dictionaryType
          }))
        }

        options.layoutConfig.value = {
          sections: [defaultSection],
          actions: [
            { code: 'submit', label: 'Submit', type: 'primary', position: 'bottom-right' },
            { code: 'cancel', label: 'Cancel', type: 'default', position: 'bottom-right' }
          ]
        }
        options.populateSampleData()
      }

      options.selectedId.value = ''
      options.history.clear()
      ElMessage.success(options.t('system.pageLayout.designer.messages.resetToDefaultSuccess'))
    } catch {
      ElMessage.error(options.t('system.pageLayout.designer.messages.resetFailedRefresh'))
    }
  }

  return {
    handleSave,
    handlePublish,
    handleReset
  }
}
