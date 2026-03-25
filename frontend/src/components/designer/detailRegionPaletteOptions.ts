import {
  buildDetailRegionSectionPresetPatch,
  getDetailRegionSectionPresetDefinitions
} from '@/components/designer/detailRegionSectionPresets'
import {
  localizeDetailRegionTarget,
  localizeDetailRegionTitle
} from '@/components/designer/detailRegionMetadata'
import type { DesignerDetailRegionOption } from '@/components/designer/designerTypes'
import type { RuntimeAggregateDetailRegion } from '@/types/runtime'

type LocaleCode = 'zh-CN' | 'en-US'

type TranslateFn = (key: string, fallback: string) => string

export const buildDetailRegionPaletteOptions = (
  detailRegions: RuntimeAggregateDetailRegion[],
  locale: LocaleCode,
  tr: TranslateFn
): DesignerDetailRegionOption[] => {
  return detailRegions
    .filter((region) => typeof region?.relationCode === 'string' && region.relationCode.trim())
    .flatMap((region) => {
      const baseTitle = localizeDetailRegionTitle(region, locale)
      const targetLabel = localizeDetailRegionTarget(region, locale)

      return getDetailRegionSectionPresetDefinitions().map((preset) => {
        const variantTitle = tr(preset.labelKey, preset.fallbackLabel)

        return {
          templateCode: `${region.relationCode}:${preset.code}`,
          presetCode: preset.code,
          relationCode: region.relationCode,
          fieldCode: region.fieldCode,
          title: `${baseTitle} · ${variantTitle}`,
          groupTitle: baseTitle,
          groupMeta: targetLabel,
          variantTitle,
          targetObjectCode: region.targetObjectCode || '',
          targetObjectLabel: targetLabel,
          description: tr(preset.descriptionKey, preset.fallbackDescription),
          preset: buildDetailRegionSectionPresetPatch(region, preset.code) || undefined
        }
      })
    })
}
