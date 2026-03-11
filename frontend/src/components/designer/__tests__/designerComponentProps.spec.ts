import { describe, expect, it } from 'vitest'
import {
  DESIGNER_COMPONENT_PROP_KEYS,
  normalizeLookupColumns,
  normalizeRelatedFields,
  resolveDesignerFieldProps,
  setDesignerComponentProp
} from '@/components/designer/designerComponentProps'

describe('designerComponentProps', () => {
  it('writes lookup compact keys to camel and snake aliases', () => {
    const field: Record<string, any> = {}
    const handled = setDesignerComponentProp(field, 'lookupCompactKeys', [' name ', '', 'email'])
    expect(handled).toBe(true)
    expect(field.componentProps.lookupCompactKeys).toEqual(['name', 'email'])
    expect(field.componentProps.lookup_compact_keys).toEqual(['name', 'email'])
    expect(field.component_props.lookupCompactKeys).toEqual(['name', 'email'])
  })

  it('writes pagination page size to camel and snake aliases when value is valid', () => {
    const field: Record<string, any> = {}
    setDesignerComponentProp(field, 'paginationPageSize', '13.8')
    expect(field.componentProps.paginationPageSize).toBe(13)
    expect(field.componentProps.pagination_page_size).toBe(13)
  })

  it('writes related object runtime props to component props aliases', () => {
    const field: Record<string, any> = {}
    setDesignerComponentProp(field, 'relatedObjectCode', 'Maintenance')
    setDesignerComponentProp(field, 'displayMode', 'inline_editable')
    setDesignerComponentProp(field, 'pageSize', '6.9')

    expect(field.componentProps.relatedObjectCode).toBe('Maintenance')
    expect(field.componentProps.related_object_code).toBe('Maintenance')
    expect(field.componentProps.targetObjectCode).toBe('Maintenance')
    expect(field.componentProps.displayMode).toBe('inline_editable')
    expect(field.componentProps.display_mode).toBe('inline_editable')
    expect(field.componentProps.pageSize).toBe(6)
    expect(field.componentProps.page_size).toBe(6)
  })

  it('writes lookup columns and related fields into component props', () => {
    const field: Record<string, any> = {}
    setDesignerComponentProp(field, 'lookupColumns', [
      { key: 'name', label: 'Name', min_width: 160 },
      { key: 'code', width: 120 }
    ])
    setDesignerComponentProp(field, 'relatedFields', [
      { code: 'name', label: 'Name', fieldType: 'text', width: 180 },
      { fieldCode: 'amount', name: 'Amount', field_type: 'number' }
    ])

    expect(field.componentProps.lookupColumns).toEqual([
      { key: 'name', label: 'Name', minWidth: 160 },
      { key: 'code', width: 120 }
    ])
    expect(field.componentProps.relatedFields).toEqual([
      { code: 'name', fieldCode: 'name', label: 'Name', name: 'Name', fieldType: 'text', field_type: 'text', width: 180 },
      { code: 'amount', fieldCode: 'amount', label: 'Amount', name: 'Amount', fieldType: 'number', field_type: 'number' }
    ])
  })

  it('keeps existing pagination config when value is invalid', () => {
    const field: Record<string, any> = {
      componentProps: {
        paginationPageSize: 20,
        pagination_page_size: 20
      }
    }
    setDesignerComponentProp(field, 'paginationPageSize', 'invalid')
    expect(field.componentProps.paginationPageSize).toBe(20)
    expect(field.componentProps.pagination_page_size).toBe(20)
  })

  it('writes subtable shortcut switches to all required aliases', () => {
    const field: Record<string, any> = {}
    setDesignerComponentProp(field, 'showShortcutHelp', 'off')
    setDesignerComponentProp(field, 'defaultShortcutHelpPinned', 1)
    expect(field.componentProps.showShortcutHelp).toBe(false)
    expect(field.componentProps.show_shortcut_help).toBe(false)
    expect(field.componentProps.defaultShortcutHelpPinned).toBe(true)
    expect(field.componentProps.default_shortcut_help_pinned).toBe(true)
    expect(field.componentProps.shortcutHelpDefaultPinned).toBe(true)
    expect(field.componentProps.shortcut_help_default_pinned).toBe(true)
  })

  it('resolves designer field props with alias precedence and normalization', () => {
    const resolved = resolveDesignerFieldProps({
      show_shortcut_help: '0',
      display_mode: 'inline_readonly',
      target_object_code: 'Maintenance',
      lookupColumns: [{ key: 'code', label: 'Code', minWidth: '200' }],
      component_props: {
        lookup_compact_keys: [' name ', '', 'email'],
        lookup_columns: [{ key: 'name', min_width: 120 }],
        pagination_page_size: 25,
        page_size: 8,
        shortcut_help_default_pinned: '1'
      }
    })

    expect(resolved.showShortcutHelp).toBe(false)
    expect(resolved.defaultShortcutHelpPinned).toBe(true)
    expect(resolved.paginationPageSize).toBe(25)
    expect(resolved.pageSize).toBe(8)
    expect(resolved.relatedObjectCode).toBe('Maintenance')
    expect(resolved.displayMode).toBe('inline_readonly')
    expect(resolved.lookupCompactKeys).toEqual(['name', 'email'])
    expect(resolved.lookupColumns).toEqual([{ key: 'code', label: 'Code', minWidth: 200 }])
    expect(resolved.relatedFields).toEqual([])
  })

  it('normalizes lookup columns and removes duplicate keys', () => {
    expect(
      normalizeLookupColumns([
        { key: 'name', label: 'Name', min_width: 120 },
        { key: 'name', label: 'Name Duplicate', min_width: 150 },
        'code',
        { key: 'status', width: 180 }
      ])
    ).toEqual([
      { key: 'name', label: 'Name', minWidth: 120 },
      { key: 'code' },
      { key: 'status', width: 180 }
    ])
  })

  it('normalizes related fields and fills aliases', () => {
    expect(
      normalizeRelatedFields([
        { code: 'name', label: 'Name', fieldType: 'text', width: 160 },
        { fieldCode: 'amount', name: 'Amount', field_type: 'number' },
        null
      ])
    ).toEqual([
      { code: 'name', fieldCode: 'name', label: 'Name', name: 'Name', fieldType: 'text', field_type: 'text', width: 160 },
      { code: 'amount', fieldCode: 'amount', label: 'Amount', name: 'Amount', fieldType: 'number', field_type: 'number' }
    ])
  })

  it('exposes expected component-prop keys for designer wiring', () => {
    expect(DESIGNER_COMPONENT_PROP_KEYS.has('lookupCompactKeys')).toBe(true)
    expect(DESIGNER_COMPONENT_PROP_KEYS.has('lookupColumns')).toBe(true)
    expect(DESIGNER_COMPONENT_PROP_KEYS.has('relatedFields')).toBe(true)
    expect(DESIGNER_COMPONENT_PROP_KEYS.has('relatedObjectCode')).toBe(true)
    expect(DESIGNER_COMPONENT_PROP_KEYS.has('displayMode')).toBe(true)
    expect(DESIGNER_COMPONENT_PROP_KEYS.has('pageSize')).toBe(true)
    expect(DESIGNER_COMPONENT_PROP_KEYS.has('paginationPageSize')).toBe(true)
    expect(DESIGNER_COMPONENT_PROP_KEYS.has('showShortcutHelp')).toBe(true)
    expect(DESIGNER_COMPONENT_PROP_KEYS.has('defaultShortcutHelpPinned')).toBe(true)
  })
})
