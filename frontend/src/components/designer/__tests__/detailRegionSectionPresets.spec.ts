import { describe, expect, it } from 'vitest'
import {
  buildDetailRegionSectionPresetPatch,
  resolveDetailRegionSectionPreset
} from '@/components/designer/detailRegionSectionPresets'

const detailRegion = {
  relationCode: 'pickup_items',
  fieldCode: 'items',
  title: 'Pickup Items',
  targetObjectCode: 'PickupItem',
  detailEditMode: 'inline_table',
  toolbarConfig: {
    addRow: true,
    import: true
  },
  relatedFields: [
    { code: 'asset', label: 'Asset', fieldType: 'reference' },
    { code: 'quantity', label: 'Quantity', fieldType: 'number' },
    { code: 'remark', label: 'Remark', fieldType: 'text' },
    { code: 'status', label: 'Status', fieldType: 'select' }
  ],
  lookupColumns: [
    { code: 'asset', label: 'Asset', fieldType: 'reference' },
    { code: 'status', label: 'Status', fieldType: 'select' },
    { code: 'updatedAt', label: 'Updated At', fieldType: 'datetime' }
  ]
}

describe('detailRegionSectionPresets', () => {
  it('builds a sidebar summary patch with compact child columns', () => {
    const patch = buildDetailRegionSectionPresetPatch(detailRegion, 'sidebarSummary')

    expect(patch).toMatchObject({
      position: 'sidebar',
      detailEditMode: 'readonly_table',
      toolbarConfig: {}
    })
    expect(patch?.relatedFields).toHaveLength(3)
    expect(patch?.lookupColumns).toHaveLength(3)
    expect((patch?.relatedFields as Array<Record<string, unknown>>)[0]).toMatchObject({ code: 'asset' })
  })

  it('resolves the active preset from a matching section snapshot', () => {
    const patch = buildDetailRegionSectionPresetPatch(detailRegion, 'reviewTable')
    expect(resolveDetailRegionSectionPreset(patch, detailRegion)).toBe('reviewTable')
  })
})
