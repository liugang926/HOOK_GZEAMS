import { describe, expect, it } from 'vitest'
import { buildDynamicListRequestParams } from './dynamicListQuery'

describe('dynamicListQuery', () => {
  it('merges route filters and unified search into a global search request', () => {
    expect(buildDynamicListRequestParams({
      params: {
        page: 1,
        __unifiedKeyword: 'Laptop',
        __unifiedField: '__all',
        __visibleFieldCodes: ['asset_code', 'asset_name'],
      },
      routeFilters: {
        status: 'active',
      },
      unifiedSearchFieldOptions: [
        { value: 'asset_code' },
        { value: 'asset_name' },
        { value: 'brand' },
      ],
    })).toEqual({
      page: 1,
      status: 'active',
      search: 'Laptop',
      searchFields: 'asset_code,asset_name',
    })
  })

  it('routes unified search to a specific field when selected', () => {
    expect(buildDynamicListRequestParams({
      params: {
        __unifiedKeyword: 'Dell',
        __unifiedField: 'brand',
      },
      routeFilters: {},
      unifiedSearchFieldOptions: [
        { value: 'asset_code' },
        { value: 'brand' },
      ],
    })).toEqual({
      brand: 'Dell',
    })
  })

  it('cleans internal search keys even when keyword is empty', () => {
    expect(buildDynamicListRequestParams({
      params: {
        __unifiedKeyword: '',
        __unifiedField: '__all',
        __visibleFieldCodes: ['asset_code'],
        searchFields: 'legacy',
        search_fields: 'legacy_snake',
      },
      routeFilters: {
        page: 2,
      },
      unifiedSearchFieldOptions: [
        { value: 'asset_code' },
      ],
    })).toEqual({
      page: 2,
    })
  })
})
