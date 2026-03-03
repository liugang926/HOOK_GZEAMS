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
      metadataContext: 'form'
    } as const

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
})
