import { beforeEach, describe, expect, it, vi } from 'vitest'

import request from '@/utils/request'
import {
  buildAssetSearchPayload,
  createSavedSearch,
  getSearchHistory,
  getSearchSuggestions,
  searchAssetsForList,
  useSavedSearch,
} from '@/api/search'

vi.mock('@/utils/request', () => ({
  default: {
    get: vi.fn(),
    post: vi.fn(),
  },
}))

type MockedRequest = {
  get: ReturnType<typeof vi.fn>
  post: ReturnType<typeof vi.fn>
}

const mockedRequest = request as unknown as MockedRequest

describe('smart search api adapters', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('buildAssetSearchPayload should map BaseListPage params into the smart search payload', () => {
    expect(buildAssetSearchPayload({
      search: 'Laptop',
      categoryId: ['cat-1'],
      status: 'in_use',
      locationId: 'loc-1',
      purchaseDateRange: ['2026-01-01', '2026-01-31'],
      ordering: '-purchasePrice',
      page: 2,
      pageSize: 50,
    })).toEqual({
      searchType: 'asset',
      keyword: 'Laptop',
      filters: {
        category: ['cat-1'],
        status: 'in_use',
        location: 'loc-1',
        purchaseDateFrom: '2026-01-01',
        purchaseDateTo: '2026-01-31',
      },
      sortBy: 'price',
      sortOrder: 'desc',
      page: 2,
      pageSize: 50,
    })
  })

  it('searchAssetsForList should call the search endpoint and normalize the list response', async () => {
    mockedRequest.post.mockResolvedValue({
      total: 1,
      page: 1,
      pageSize: 20,
      totalPages: 1,
      results: [
        {
          id: 'asset-1',
          assetCode: 'ASSET-1',
          assetName: 'Laptop',
        },
      ],
      aggregations: {
        status: { inUse: 1 },
      },
      engine: 'database',
    })

    const response = await searchAssetsForList({
      search: 'Laptop',
      page: 1,
      pageSize: 20,
    })

    expect(mockedRequest.post).toHaveBeenCalledWith('/search/', {
      searchType: 'asset',
      keyword: 'Laptop',
      filters: {},
      sortBy: 'relevance',
      sortOrder: 'desc',
      page: 1,
      pageSize: 20,
    })
    expect(response.count).toBe(1)
    expect(response.results[0].assetCode).toBe('ASSET-1')
    expect(response.aggregations.status.inUse).toBe(1)
  })

  it('history, suggestions, save, and use helpers should target the dedicated endpoints', async () => {
    mockedRequest.get.mockResolvedValue({
      count: 0,
      next: null,
      previous: null,
      results: [],
    })
    mockedRequest.post.mockResolvedValue({
      id: 'saved-1',
      name: 'Laptop Search',
      keyword: 'Laptop',
      filters: {},
      isShared: false,
      useCount: 1,
    })

    await getSearchSuggestions({ keyword: 'Lap', type: 'asset', limit: 8 })
    await getSearchHistory({ type: 'asset', limit: 5 })
    await createSavedSearch({ name: 'Laptop Search', keyword: 'Laptop' })
    await useSavedSearch('saved-1')

    expect(mockedRequest.get).toHaveBeenNthCalledWith(1, '/search/suggestions/', {
      params: {
        keyword: 'Lap',
        type: 'asset',
        limit: 8,
      },
    })
    expect(mockedRequest.get).toHaveBeenNthCalledWith(2, '/search/history/', {
      params: {
        type: 'asset',
        page: 1,
        page_size: 5,
      },
    })
    expect(mockedRequest.post).toHaveBeenNthCalledWith(1, '/search/saved/', {
      name: 'Laptop Search',
      keyword: 'Laptop',
    })
    expect(mockedRequest.post).toHaveBeenNthCalledWith(2, '/search/saved/saved-1/use/')
  })
})
