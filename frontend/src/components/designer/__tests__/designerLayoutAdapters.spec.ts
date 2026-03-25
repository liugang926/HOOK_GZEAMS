import { describe, expect, it } from 'vitest'
import {
  readComponentProps,
  normalizeLayoutConfigFieldAliases,
  normalizeLayoutFieldAliases
} from '../designerLayoutAdapters'

describe('designerLayoutAdapters', () => {
  it('normalizes field validation aliases onto both camelCase and snake_case keys', () => {
    const field = normalizeLayoutFieldAliases({
      id: 'field-name',
      fieldCode: 'name',
      label: 'Name',
      span: 1,
      field_type: 'text',
      min_length: 2,
      maxLength: 10,
      regex_pattern: '^[A-Z].*$',
      validationMessage: 'Invalid name'
    } as any)

    expect(field.fieldType).toBe('text')
    expect(field.field_type).toBe('text')
    expect(field.minLength).toBe(2)
    expect(field.min_length).toBe(2)
    expect(field.maxLength).toBe(10)
    expect(field.max_length).toBe(10)
    expect(field.regexPattern).toBe('^[A-Z].*$')
    expect(field.regex_pattern).toBe('^[A-Z].*$')
    expect(field.validationMessage).toBe('Invalid name')
    expect(field.validation_message).toBe('Invalid name')
  })

  it('normalizes nested layout fields inside sections', () => {
    const config = normalizeLayoutConfigFieldAliases({
      sections: [
        {
          id: 'section-basic',
          type: 'section',
          fields: [
            {
              id: 'field-code',
              fieldCode: 'code',
              label: 'Code',
              span: 1,
              min_length: 1
            }
          ]
        }
      ]
    } as any)

    const field = config.sections?.[0]?.fields?.[0]
    expect(field?.minLength).toBe(1)
    expect(field?.min_length).toBe(1)
  })

  it('clamps invalid legacy minHeight into the supported designer range', () => {
    const config = normalizeLayoutConfigFieldAliases({
      sections: [
        {
          id: 'section-basic',
          type: 'section',
          fields: [
            {
              id: 'field-name',
              fieldCode: 'name',
              label: 'Name',
              span: 1,
              minHeight: 20
            }
          ]
        }
      ]
    } as any)

    const field = config.sections?.[0]?.fields?.[0]
    expect(field?.minHeight).toBe(44)
    expect(field?.min_height).toBe(44)
    expect(field?.componentProps?.minHeight).toBeUndefined()
  })

  it('hydrates legacy related object props into componentProps', () => {
    const componentProps = readComponentProps({
      fieldType: 'related_object',
      relatedObjectCode: 'Maintenance',
      displayMode: 'inline_editable',
      pageSize: 7
    } as any)

    expect(componentProps.relatedObjectCode).toBe('Maintenance')
    expect(componentProps.targetObjectCode).toBe('Maintenance')
    expect(componentProps.displayMode).toBe('inline_editable')
    expect(componentProps.pageSize).toBe(7)
  })

  it('hydrates legacy lookup columns and related fields into componentProps', () => {
    const componentProps = readComponentProps({
      fieldType: 'sub_table',
      lookupColumns: [{ key: 'name', label: 'Name' }],
      relatedFields: [{ code: 'amount', label: 'Amount', fieldType: 'number' }]
    } as any)

    expect(componentProps.lookupColumns).toEqual([{ key: 'name', label: 'Name' }])
    expect(componentProps.relatedFields).toEqual([{ code: 'amount', label: 'Amount', fieldType: 'number' }])
  })
})
