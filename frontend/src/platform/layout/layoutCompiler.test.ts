import { describe, expect, it } from 'vitest'
import { buildLayoutFieldDropper, compileLayoutSchema } from '@/platform/layout/layoutCompiler'

describe('layoutCompiler', () => {
  it('drops system and unknown fields from layout by default', () => {
    const compiled = compileLayoutSchema({
      mode: 'edit',
      fields: [
        { code: 'left_field', fieldType: 'text' },
        { code: 'right_field', fieldType: 'text' }
      ],
      layoutConfig: {
        sections: [
          {
            id: 'basic',
            type: 'section',
            fields: [
              { fieldCode: 'left_field', span: 1 },
              { fieldCode: 'created_at', span: 1 },
              { fieldCode: 'shadow_runtime_field', span: 1 },
              { fieldCode: 'right_field', span: 1 }
            ]
          }
        ]
      }
    })

    const fields = compiled.layoutConfig.sections?.[0]?.fields || []
    expect(fields.map((item: any) => item.fieldCode)).toEqual(['left_field', 'right_field'])
    expect(compiled.renderSchema.fieldOrder).toEqual(['left_field', 'right_field'])
  })

  it('can keep unknown fields when explicitly requested', () => {
    const compiled = compileLayoutSchema({
      mode: 'edit',
      fields: [
        { code: 'left_field', fieldType: 'text' },
        { code: 'right_field', fieldType: 'text' }
      ],
      keepUnknownFields: true,
      layoutConfig: {
        sections: [
          {
            id: 'basic',
            type: 'section',
            fields: [
              { fieldCode: 'left_field', span: 1 },
              { fieldCode: 'shadow_runtime_field', span: 1 },
              { fieldCode: 'right_field', span: 1 }
            ]
          }
        ]
      }
    })

    const fields = compiled.layoutConfig.sections?.[0]?.fields || []
    expect(fields.map((item: any) => item.fieldCode)).toEqual([
      'left_field',
      'shadow_runtime_field',
      'right_field'
    ])
  })

  it('field dropper keeps unknown codes when known field set is empty', () => {
    const dropFieldCode = buildLayoutFieldDropper({
      knownFieldCodes: new Set<string>()
    })

    expect(dropFieldCode('shadow_runtime_field')).toBe(false)
    expect(dropFieldCode('created_at')).toBe(true)
  })

  it('keeps runtime compile stable without random ids when section ids are missing', () => {
    const input = {
      mode: 'edit' as const,
      fields: [{ code: 'name', fieldType: 'text' }],
      layoutConfig: {
        sections: [
          {
            type: 'section',
            fields: [{ fieldCode: 'name', span: 1 }]
          }
        ]
      }
    }

    const first = compileLayoutSchema(input)
    const second = compileLayoutSchema(input)

    expect(first.layoutConfig.sections?.[0]?.id).toBe('section_1')
    expect(second.layoutConfig.sections?.[0]?.id).toBe('section_1')
    expect(first.renderSchema.sections[0].id).toBe('section_1')
    expect(second.renderSchema.sections[0].id).toBe('section_1')
  })
})
