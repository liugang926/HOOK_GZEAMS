import {
  getDetailRegionColumnPresetConfig,
  getDetailRegionColumnPresetDefinition,
  getDetailRegionColumnPresetDefinitions,
} from '@/components/designer/detailRegionColumnPresets'
import {
  getDetailRegionSectionPresetDefinition,
  type DetailRegionSectionPresetCode,
} from '@/components/designer/detailRegionSectionPresets'

export type DesignerTranslateFn = (key: string, fallback: string) => string
export type DesignerTranslateFormatFn = (
  key: string,
  fallback: string,
  params: Record<string, string | number>
) => string

type PresetOption = {
  label: string
  value: string
}

function resolveFormatterFallbackLabel(formatter: string): string {
  switch (formatter) {
    case 'uppercase':
      return 'Uppercase'
    case 'lowercase':
      return 'Lowercase'
    case 'number':
      return 'Number'
    case 'date':
      return 'Date'
    case 'datetime':
      return 'DateTime'
    case 'boolean':
      return 'Boolean'
    default:
      return formatter
  }
}

export function buildDetailRegionSectionPresetPreviewItems(
  patch: Record<string, any> | null,
  tr: DesignerTranslateFn,
  trf: DesignerTranslateFormatFn
): string[] {
  if (!patch) return []

  const items: string[] = []
  const position = String(patch.position || '').trim()
  if (position) {
    items.push(
      tr(
        `system.pageLayout.designer.detailRegionConfigurator.sectionPreviewItems.position.${position}`,
        position === 'sidebar' ? 'Sidebar' : 'Main area'
      )
    )
  }

  const detailEditMode = String(patch.detailEditMode || patch.detail_edit_mode || '').trim()
  if (detailEditMode) {
    const optionKey =
      detailEditMode === 'inline_table'
        ? 'inlineTable'
        : detailEditMode === 'readonly_table'
          ? 'readonlyTable'
          : 'nestedForm'
    items.push(
      tr(
        `system.pageLayout.designer.sectionProperties.options.detailEditMode.${optionKey}`,
        detailEditMode
      )
    )
  }

  const columnCount = Array.isArray(patch.relatedFields)
    ? patch.relatedFields.length
    : Array.isArray(patch.related_fields)
      ? patch.related_fields.length
      : 0
  if (columnCount > 0) {
    items.push(
      trf(
        'system.pageLayout.designer.detailRegionConfigurator.sectionPreviewItems.columns',
        '{count} columns',
        { count: columnCount }
      )
    )
  }

  const toolbarConfig = patch.toolbarConfig || patch.toolbar_config
  items.push(
    tr(
      toolbarConfig && typeof toolbarConfig === 'object' && Object.keys(toolbarConfig).length > 0
        ? 'system.pageLayout.designer.detailRegionConfigurator.sectionPreviewItems.toolbar.enabled'
        : 'system.pageLayout.designer.detailRegionConfigurator.sectionPreviewItems.toolbar.hidden',
      toolbarConfig && typeof toolbarConfig === 'object' && Object.keys(toolbarConfig).length > 0
        ? 'Toolbar enabled'
        : 'Toolbar hidden'
    )
  )

  return items
}

export function buildDetailRegionSectionPresetPreviewHint(
  presetCode: DetailRegionSectionPresetCode | '',
  tr: DesignerTranslateFn,
  trf: DesignerTranslateFormatFn
): string {
  if (!presetCode) return ''
  const definition = getDetailRegionSectionPresetDefinition(presetCode)
  if (!definition) return ''
  return trf(
    'system.pageLayout.designer.detailRegionConfigurator.sectionPreviewHint',
    'Previewing {preset}. Click a template to apply.',
    { preset: tr(definition.labelKey, definition.fallbackLabel) }
  )
}

export function buildConfiguredFieldPresetOptions(
  value: unknown,
  tr: DesignerTranslateFn
): PresetOption[] {
  return [
    {
      label: tr('system.pageLayout.designer.detailRegionConfigurator.presetOptions.default', 'Default'),
      value: ''
    },
    ...getDetailRegionColumnPresetDefinitions(value).map((preset) => ({
      label: tr(preset.labelKey, preset.fallbackLabel),
      value: preset.code
    }))
  ]
}

export function buildConfiguredFieldPreviewCandidates(
  value: unknown,
  tr: DesignerTranslateFn
): PresetOption[] {
  return getDetailRegionColumnPresetDefinitions(value).map((preset) => ({
    label: tr(preset.labelKey, preset.fallbackLabel),
    value: preset.code
  }))
}

export function resolveConfiguredFieldPresetLabel(
  presetCode: unknown,
  tr: DesignerTranslateFn
): string {
  const preset = getDetailRegionColumnPresetDefinition(presetCode)
  if (!preset) return ''
  return tr(preset.labelKey, preset.fallbackLabel)
}

export function buildConfiguredFieldPresetDescription(
  presetCode: unknown,
  tr: DesignerTranslateFn
): string {
  const preset = getDetailRegionColumnPresetDefinition(presetCode)
  if (!preset) return ''
  return tr(preset.descriptionKey, preset.fallbackDescription)
}

export function buildConfiguredFieldPresetPreviewHint(
  previewPresetCode: unknown,
  tr: DesignerTranslateFn,
  trf: DesignerTranslateFormatFn
): string {
  const label = resolveConfiguredFieldPresetLabel(previewPresetCode, tr)
  if (!label) return ''
  return trf(
    'system.pageLayout.designer.detailRegionConfigurator.previewHint',
    'Previewing {preset}. Click a preset to apply.',
    { preset: label }
  )
}

export function buildConfiguredFieldPresetPreviewItems(
  presetCode: unknown,
  tr: DesignerTranslateFn,
  trf: DesignerTranslateFormatFn
): string[] {
  const preset = getDetailRegionColumnPresetConfig(presetCode)
  if (!preset) return []

  const items: string[] = []
  if (typeof preset.minWidth === 'number' && preset.minWidth > 0) {
    items.push(
      trf(
        'system.pageLayout.designer.detailRegionConfigurator.previewItems.minWidth',
        'Min {value}px',
        { value: preset.minWidth }
      )
    )
  }
  if (preset.align) {
    items.push(
      tr(
        `system.pageLayout.designer.detailRegionConfigurator.previewItems.align.${preset.align}`,
        preset.align === 'left'
          ? 'Left aligned'
          : preset.align === 'center'
            ? 'Center aligned'
            : 'Right aligned'
      )
    )
  }
  if (preset.fixed) {
    items.push(
      tr(
        `system.pageLayout.designer.detailRegionConfigurator.previewItems.fixed.${preset.fixed}`,
        preset.fixed === 'left' ? 'Fixed left' : 'Fixed right'
      )
    )
  }
  if (preset.ellipsis) {
    items.push(
      tr('system.pageLayout.designer.detailRegionConfigurator.previewItems.ellipsis', 'Ellipsis')
    )
  }
  if (preset.formatter) {
    items.push(
      tr(
        `system.pageLayout.designer.detailRegionConfigurator.previewItems.formatter.${preset.formatter}`,
        tr(
          `system.pageLayout.designer.detailRegionConfigurator.formatterOptions.${preset.formatter}`,
          resolveFormatterFallbackLabel(preset.formatter)
        )
      )
    )
  }
  if (preset.emptyText) {
    items.push(
      trf(
        'system.pageLayout.designer.detailRegionConfigurator.previewItems.emptyText',
        'Empty: {value}',
        { value: preset.emptyText }
      )
    )
  }
  if (preset.tooltipTemplate) {
    items.push(
      trf(
        'system.pageLayout.designer.detailRegionConfigurator.previewItems.tooltipTemplate',
        'Tooltip: {value}',
        { value: preset.tooltipTemplate }
      )
    )
  }

  return items
}

export function buildConfiguredFieldRecommendedPresetText(
  activePresetCode: string,
  presetOptions: PresetOption[],
  trf: DesignerTranslateFormatFn
): string {
  if (activePresetCode) return ''
  const recommended = presetOptions
    .filter((option) => option.value)
    .map((option) => option.label)
  if (recommended.length === 0) return ''
  return trf(
    'system.pageLayout.designer.detailRegionConfigurator.recommendedPresets',
    'Recommended: {presets}',
    { presets: recommended.join(' / ') }
  )
}
