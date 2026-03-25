import { describe, expect, it } from 'vitest'
import {
  applyDesignerSectionPreviewOverlay,
  resolveDetailRegionPreviewSectionId
} from '@/components/designer/designerPreviewOverlay'

describe('designerPreviewOverlay', () => {
  it('applies a temporary section override without mutating the source config', () => {
    const layoutConfig = {
      sections: [
        {
          id: 'detail_1',
          type: 'detail-region',
          fieldCode: 'items',
          relatedFields: [{ code: 'quantity', minWidth: 140 }]
        },
        {
          id: 'section_2',
          type: 'section',
          title: 'Basic'
        }
      ]
    }

    const next = applyDesignerSectionPreviewOverlay(layoutConfig, {
      sectionId: 'detail_1',
      value: {
        relatedFields: [{ code: 'quantity', minWidth: 160, fixed: 'right' }]
      }
    })

    expect(next).not.toBe(layoutConfig)
    expect(next.sections?.[0]).toMatchObject({
      id: 'detail_1',
      relatedFields: [{ code: 'quantity', minWidth: 160, fixed: 'right' }]
    })
    expect(next.sections?.[1]).toEqual(layoutConfig.sections[1])
    expect(layoutConfig.sections[0]).toEqual({
      id: 'detail_1',
      type: 'detail-region',
      fieldCode: 'items',
      relatedFields: [{ code: 'quantity', minWidth: 140 }]
    })
  })

  it('resolves a matching detail-region preview target and prefers the selected section', () => {
    const layoutConfig = {
      sections: [
        {
          id: 'detail_1',
          type: 'detail-region',
          relationCode: 'pickup_items',
          fieldCode: 'items'
        },
        {
          id: 'detail_2',
          type: 'detail-region',
          relationCode: 'pickup_items',
          fieldCode: 'items'
        },
        {
          id: 'section_3',
          type: 'section',
          title: 'Basic'
        }
      ]
    }

    expect(resolveDetailRegionPreviewSectionId(layoutConfig, {
      relationCode: 'pickup_items',
      fieldCode: 'items'
    })).toBe('detail_1')

    expect(resolveDetailRegionPreviewSectionId(layoutConfig, {
      relationCode: 'pickup_items',
      fieldCode: 'items'
    }, 'detail_2')).toBe('detail_2')

    expect(resolveDetailRegionPreviewSectionId(layoutConfig, {
      relationCode: 'return_items',
      fieldCode: 'items'
    }, 'section_3')).toBe('detail_1')

    expect(resolveDetailRegionPreviewSectionId(layoutConfig, {
      relationCode: 'missing_relation',
      fieldCode: 'missing_field'
    })).toBeNull()
  })
})
