import { describe, expect, it } from 'vitest'
import {
  buildDynamicListHeroChips,
  buildDynamicListHeroStats,
  countDynamicListVisibleColumns,
  resolveDynamicListWorkspaceCopy,
  resolveDynamicListWorkspaceModuleLabel,
} from './dynamicListWorkspaceModel'

describe('dynamicListWorkspaceModel', () => {
  it('resolves the module label from module name, display name, or object code', () => {
    expect(resolveDynamicListWorkspaceModuleLabel({
      moduleName: 'Lifecycle',
      objectDisplayName: 'Asset',
      objectCode: 'Asset',
    })).toBe('Lifecycle')

    expect(resolveDynamicListWorkspaceModuleLabel({
      moduleName: '   ',
      objectDisplayName: 'Asset',
      objectCode: 'Asset',
    })).toBe('Asset')

    expect(resolveDynamicListWorkspaceModuleLabel({
      moduleName: '',
      objectDisplayName: '',
      objectCode: 'Asset',
    })).toBe('Asset')
  })

  it('returns localized fallback copy and respects metadata descriptions when present', () => {
    expect(resolveDynamicListWorkspaceCopy({
      isZhLocale: true,
      metadataDescription: '',
    })).toEqual(expect.objectContaining({
      listModeLabel: '对象列表',
      listPanelTitle: '记录工作台',
    }))

    expect(resolveDynamicListWorkspaceCopy({
      isZhLocale: false,
      metadataDescription: 'Custom object description',
    })).toEqual(expect.objectContaining({
      listHeroDescription: 'Custom object description',
      listPanelTitle: 'Record workspace',
    }))
  })

  it('counts only visible columns and builds hero chips with create capability', () => {
    expect(countDynamicListVisibleColumns([
      { visible: true },
      { visible: false },
      {},
    ])).toBe(2)

    expect(buildDynamicListHeroChips({
      listModeLabel: 'List view',
      objectCode: 'Asset',
      canAdd: true,
      createEnabledLabel: 'Create enabled',
    })).toEqual([
      { label: 'List view', kind: 'primary' },
      { label: 'Asset' },
      { label: 'Create enabled', kind: 'muted' },
    ])
  })

  it('builds hero stats from the resolved labels and counts', () => {
    expect(buildDynamicListHeroStats({
      fieldCountLabel: 'Fields',
      visibleFieldCountLabel: 'List columns',
      searchableFieldCountLabel: 'Search fields',
      fieldCount: 12,
      visibleFieldCount: 8,
      searchableFieldCount: 5,
    })).toEqual([
      { label: 'Fields', value: 12 },
      { label: 'List columns', value: 8 },
      { label: 'Search fields', value: 5 },
    ])
  })
})
