import { describe, expect, it } from 'vitest'
import type { SearchField } from '@/types/common'
import {
  buildDynamicListUnifiedSearchFields,
  extractDynamicListRouteFilters,
  resolveDynamicListEffectivePermissions,
  shouldRefreshDynamicListOnPathChange,
} from './dynamicListPageShellModel'

describe('dynamicListPageShellModel', () => {
  it('extracts route filters while ignoring reserved or empty query keys', () => {
    expect(extractDynamicListRouteFilters({
      status: 'draft',
      keyword: '',
      mode: 'list',
      department: ['ops', 'finance'],
      assignee: null,
    })).toEqual({
      status: 'draft',
      department: 'ops',
    })

    expect(extractDynamicListRouteFilters(undefined)).toEqual({})
  })

  it('refreshes list data only when returning to the canonical object list path', () => {
    expect(shouldRefreshDynamicListOnPathChange({
      objectCode: 'Asset',
      oldPath: '/objects/Asset/create',
      newPath: '/objects/Asset',
    })).toBe(true)

    expect(shouldRefreshDynamicListOnPathChange({
      objectCode: 'Asset',
      oldPath: '/objects/Asset',
      newPath: '/objects/Asset/1',
    })).toBe(false)

    expect(shouldRefreshDynamicListOnPathChange({
      objectCode: 'Asset',
      oldPath: '/objects/Asset',
      newPath: '/objects/Asset',
    })).toBe(false)
  })

  it('prefers runtime permissions and falls back to metadata or open access defaults', () => {
    expect(resolveDynamicListEffectivePermissions(
      { view: false, add: false, change: true, delete: false },
      { view: true, add: true, change: true, delete: true },
    )).toEqual({
      view: false,
      add: false,
      change: true,
      delete: false,
    })

    expect(resolveDynamicListEffectivePermissions(
      null,
      { view: true, add: false, change: true, delete: false },
    )).toEqual({
      view: true,
      add: false,
      change: true,
      delete: false,
    })

    expect(resolveDynamicListEffectivePermissions(null, null)).toEqual({
      view: true,
      add: true,
      change: true,
      delete: true,
    })
  })

  it('appends the unified keyword slot to the regular search fields', () => {
    const rawSearchFields: SearchField[] = [
      {
        prop: 'asset_code',
        label: 'Asset code',
        type: 'text',
      },
    ]

    expect(buildDynamicListUnifiedSearchFields(rawSearchFields, 'Search')).toEqual([
      {
        prop: 'asset_code',
        label: 'Asset code',
        type: 'text',
      },
      {
        prop: '__unifiedKeyword',
        label: 'Search',
        type: 'slot',
        defaultValue: '',
      },
    ])
  })
})
