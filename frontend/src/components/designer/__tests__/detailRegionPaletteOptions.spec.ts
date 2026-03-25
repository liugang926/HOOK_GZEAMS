import { describe, expect, it } from 'vitest'
import { buildDetailRegionPaletteOptions } from '@/components/designer/detailRegionPaletteOptions'

describe('detailRegionPaletteOptions', () => {
  it('builds multiple palette variants for each aggregate detail region', () => {
    const options = buildDetailRegionPaletteOptions(
      [
        {
          relationCode: 'pickup_items',
          fieldCode: 'items',
          title: 'Pickup Items',
          targetObjectCode: 'PickupItem',
          targetObjectName: 'Pickup Item',
          detailEditMode: 'inline_table',
          toolbarConfig: { addRow: true },
          relatedFields: [
            { code: 'asset', label: 'Asset', fieldType: 'reference' },
            { code: 'quantity', label: 'Quantity', fieldType: 'number' }
          ],
          lookupColumns: [
            { code: 'asset', label: 'Asset', fieldType: 'reference' }
          ]
        }
      ],
      'en-US',
      (_key, fallback) => fallback
    )

    expect(options.map((option) => option.templateCode)).toEqual([
      'pickup_items:editableDetail',
      'pickup_items:reviewTable',
      'pickup_items:sidebarSummary'
    ])
    expect(options[0]).toMatchObject({
      title: 'Pickup Items · Editable Detail',
      groupTitle: 'Pickup Items',
      groupMeta: 'Pickup Item',
      variantTitle: 'Editable Detail',
      targetObjectLabel: 'Pickup Item'
    })
    expect(options[1].description).toContain('Readonly review table')
    expect(options[2].preset).toMatchObject({
      position: 'sidebar',
      detailEditMode: 'readonly_table'
    })
  })
})
