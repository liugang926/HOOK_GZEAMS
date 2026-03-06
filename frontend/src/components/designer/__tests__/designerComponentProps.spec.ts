import { describe, expect, it } from 'vitest'
import {
  DESIGNER_COMPONENT_PROP_KEYS,
  normalizeLookupColumns,
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
      lookupColumns: [{ key: 'code', label: 'Code', minWidth: '200' }],
      component_props: {
        lookup_compact_keys: [' name ', '', 'email'],
        lookup_columns: [{ key: 'name', min_width: 120 }],
        pagination_page_size: 25,
        shortcut_help_default_pinned: '1'
      }
    })

    expect(resolved.showShortcutHelp).toBe(false)
    expect(resolved.defaultShortcutHelpPinned).toBe(true)
    expect(resolved.paginationPageSize).toBe(25)
    expect(resolved.lookupCompactKeys).toEqual(['name', 'email'])
    expect(resolved.lookupColumns).toEqual([{ key: 'code', label: 'Code', minWidth: 200 }])
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

  it('exposes expected component-prop keys for designer wiring', () => {
    expect(DESIGNER_COMPONENT_PROP_KEYS.has('lookupCompactKeys')).toBe(true)
    expect(DESIGNER_COMPONENT_PROP_KEYS.has('paginationPageSize')).toBe(true)
    expect(DESIGNER_COMPONENT_PROP_KEYS.has('showShortcutHelp')).toBe(true)
    expect(DESIGNER_COMPONENT_PROP_KEYS.has('defaultShortcutHelpPinned')).toBe(true)
  })
})
