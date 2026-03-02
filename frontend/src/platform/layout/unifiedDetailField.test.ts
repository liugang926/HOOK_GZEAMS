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
    expect(statusField.prop).toBe('status')

    const fileField = toUnifiedDetailField({
      code: 'attachment',
      label: 'Attachment',
      fieldType: 'attachment'
    })
    expect(fileField.type).toBe('text')
    expect(fileField.span).toBe(24)
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
