import { describe, expect, it } from 'vitest'
import { projectUnifiedDetailSectionsFromLayout, shouldSkipUnifiedDetailField } from '@/platform/layout/unifiedDetailSections'

describe('unifiedDetailSections', () => {
  it('applies audit/system always and visibility only under strict mode', () => {
    const input = {
      layoutSections: [
        {
          id: 'basic',
          type: 'section',
          title: 'Basic',
          columns: 2,
          fields: [
            { fieldCode: 'assetName', label: 'Asset Name', span: 1 },
            { fieldCode: 'assetCode', label: 'Asset Code', span: 1 },
            { fieldCode: 'createdAt', label: 'Created At', span: 1 }
          ]
        }
      ],
      fields: [
        { code: 'assetName', name: 'Asset Name', fieldType: 'text', showInForm: true } as any,
        { code: 'assetCode', name: 'Asset Code', fieldType: 'text', showInForm: false } as any,
        { code: 'createdAt', name: 'Created At', fieldType: 'datetime', showInForm: true } as any
      ],
      metadataContext: 'form' as const
    }

    const looseSections = projectUnifiedDetailSectionsFromLayout({
      ...input,
      strictVisibility: false
    })

    const strictSections = projectUnifiedDetailSectionsFromLayout({
      ...input,
      strictVisibility: true
    })

    expect(looseSections).toHaveLength(1)
    expect(looseSections[0].fields.map((field) => field.prop)).toEqual(['assetName', 'assetCode'])
    expect(looseSections[0].fields[0].span).toBe(12)
    expect(strictSections[0].fields.map((field) => field.prop)).toEqual(['assetName'])
  })

  it('keeps form/detail visibility semantics explicit and deterministic', () => {
    const field = {
      code: 'assetStatus',
      name: 'Asset Status',
      fieldType: 'text',
      showInDetail: false
      // showInForm intentionally undefined
    } as any

    expect(shouldSkipUnifiedDetailField(field, 'form')).toBe(false)
    expect(shouldSkipUnifiedDetailField(field, 'detail')).toBe(true)
  })

  it('skips layout-only injected fields that are missing from runtime metadata', () => {
    const sections = projectUnifiedDetailSectionsFromLayout({
      layoutSections: [
        {
          id: 'basic',
          type: 'section',
          title: 'Basic',
          columns: 2,
          fields: [
            { fieldCode: 'left_field', label: 'Left Field', span: 1 },
            { fieldCode: 'runtime_shadow_field', label: 'Runtime Shadow', span: 1 },
            { fieldCode: 'right_field', label: 'Right Field', span: 1 }
          ]
        }
      ],
      fields: [
        { code: 'left_field', name: 'Left Field', fieldType: 'text', showInForm: true } as any,
        { code: 'right_field', name: 'Right Field', fieldType: 'text', showInForm: true } as any
      ],
      metadataContext: 'form',
      strictVisibility: false
    })

    expect(sections).toHaveLength(1)
    expect(sections[0].fields.map((field) => field.prop)).toEqual(['left_field', 'right_field'])
  })

  it('preserves layout-injected related_object fields so placed relations can render in detail', () => {
    const sections = projectUnifiedDetailSectionsFromLayout({
      layoutSections: [
        {
          id: 'related',
          type: 'section',
          title: 'Related',
          columns: 1,
          fields: [
            {
              fieldCode: 'maintenance_records',
              label: 'Maintenance Records',
              fieldType: 'related_object',
              span: 1,
              componentProps: {
                relationCode: 'maintenance_records',
                relatedObjectCode: 'Maintenance'
              }
            }
          ]
        }
      ],
      fields: [
        { code: 'asset_name', name: 'Asset Name', fieldType: 'text', showInForm: true } as any
      ],
      metadataContext: 'form',
      strictVisibility: false
    })

    expect(sections).toHaveLength(1)
    expect(sections[0].fields).toHaveLength(1)
    expect(sections[0].fields[0].prop).toBe('maintenance_records')
    expect(sections[0].fields[0].type).toBe('related_object')
    expect((sections[0].fields[0] as any).componentProps?.relationCode).toBe('maintenance_records')
  })
})
