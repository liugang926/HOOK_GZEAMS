import { describe, it, expect } from 'vitest'
import {
  isAuditFieldCode,
  normalizeDetailSpan,
  toUnifiedDetailField,
  buildRequiredFormRules
} from '@/platform/layout/unifiedDetailField'

describe('unifiedDetailField', () => {
  it('detects audit field codes', () => {
    expect(isAuditFieldCode('created_at')).toBe(true)
    expect(isAuditFieldCode('updatedBy')).toBe(true)
    expect(isAuditFieldCode('name')).toBe(false)
  })

  it('normalizes span values by columns', () => {
    expect(normalizeDetailSpan(1, 2)).toBe(12)
    expect(normalizeDetailSpan(2, 2)).toBe(24)
    expect(normalizeDetailSpan(24, 2)).toBe(24)
    expect(normalizeDetailSpan(undefined, 3)).toBe(8)
  })

  it('projects field type and options to unified detail field', () => {
    const statusField = toUnifiedDetailField({
      code: 'status',
      label: 'Status',
      fieldType: 'select',
      options: [{ label: 'Active', value: 'active', color: 'green' }]
    })
    expect(statusField.type).toBe('tag')
    expect(statusField.editorType).toBe('select')
    expect(statusField.prop).toBe('status')

    const fileField = toUnifiedDetailField({
      code: 'attachment',
      label: 'Attachment',
      fieldType: 'attachment'
    })
    expect(fileField.type).toBe('attachment')
    expect(fileField.span).toBe(24)

    const qrField = toUnifiedDetailField({
      code: 'qr_code',
      label: 'QR Code',
      fieldType: 'qr_code'
    })
    expect(qrField.type).toBe('qr_code')

    const barcodeField = toUnifiedDetailField({
      code: 'barcode',
      label: 'Barcode',
      fieldType: 'barcode'
    })
    expect(barcodeField.type).toBe('barcode')

    const daterangeField = toUnifiedDetailField({
      code: 'warranty_period',
      label: 'Warranty',
      fieldType: 'daterange'
    })
    expect(daterangeField.type).toBe('daterange')

    const yearField = toUnifiedDetailField({
      code: 'fiscal_year',
      label: 'Year',
      fieldType: 'year'
    })
    expect(yearField.type).toBe('year')

    const boolField = toUnifiedDetailField({
      code: 'active',
      label: 'Active',
      fieldType: 'boolean'
    })
    expect(boolField.type).toBe('boolean')

    const colorField = toUnifiedDetailField({
      code: 'theme_color',
      label: 'Theme Color',
      fieldType: 'color'
    })
    expect(colorField.type).toBe('color')

    const urlField = toUnifiedDetailField({
      code: 'website',
      label: 'Website',
      fieldType: 'url'
    })
    expect(urlField.type).toBe('link')
    expect(urlField.href).toBe('{value}')
    expect(urlField.editorType).toBe('url')

    const emailField = toUnifiedDetailField({
      code: 'email',
      label: 'Email',
      fieldType: 'email'
    })
    expect(emailField.type).toBe('link')
    expect(emailField.href).toBe('mailto:{value}')

    const phoneField = toUnifiedDetailField({
      code: 'mobile',
      label: 'Mobile',
      fieldType: 'phone'
    })
    expect(phoneField.type).toBe('link')
    expect(phoneField.href).toBe('tel:{value}')

    const richTextField = toUnifiedDetailField({
      code: 'description',
      label: 'Description',
      fieldType: 'rich_text'
    })
    expect(richTextField.type).toBe('rich_text')
    expect(richTextField.span).toBe(24)

    const subTableField = toUnifiedDetailField({
      code: 'lines',
      label: 'Lines',
      fieldType: 'sub_table'
    })
    expect(subTableField.type).toBe('sub_table')
    expect(subTableField.span).toBe(24)

    const jsonField = toUnifiedDetailField({
      code: 'extra',
      label: 'Extra',
      fieldType: 'json'
    })
    expect(jsonField.type).toBe('json')
    expect(jsonField.span).toBe(24)

    const sizedField = toUnifiedDetailField({
      code: 'asset_name',
      label: 'Asset Name',
      fieldType: 'text',
      minHeight: 148
    })
    expect((sizedField as any).minHeight).toBe(148)

    const sizedFromComponentProps = toUnifiedDetailField({
      code: 'asset_code',
      label: 'Asset Code',
      fieldType: 'text',
      component_props: {
        min_height: 164
      }
    })
    expect((sizedFromComponentProps as any).minHeight).toBe(164)
  })

  it('builds required form rules from field metadata', () => {
    const rules = buildRequiredFormRules([
      { code: 'name', label: 'Name', isRequired: true },
      { code: 'description', label: 'Description', required: false },
      { code: 'code', label: 'Code', is_required: true }
    ])

    expect(Object.keys(rules)).toEqual(['name', 'code'])
    expect(rules.name?.[0]?.required).toBe(true)
    expect(rules.code?.[0]?.message).toContain('Code')
  })
})
