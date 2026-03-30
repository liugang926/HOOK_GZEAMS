import request from '@/utils/request'

export interface AssetSearchFilters {
  category?: string | string[]
  status?: string | string[]
  location?: string | string[]
  brand?: string
  tags?: string[]
  purchasePriceMin?: number
  purchasePriceMax?: number
  purchaseDateFrom?: string
  purchaseDateTo?: string
}

export interface AssetSearchResultRow {
  id: string
  assetCode: string
  assetName: string
  assetCategory?: string | null
  assetCategoryName?: string
  assetStatus: string
  statusLabel?: string
  specification?: string
  brand?: string
  model?: string
  serialNumber?: string
  purchasePrice?: number | null
  currentValue?: number | null
  purchaseDate?: string | null
  location?: string | null
  locationPath?: string
  department?: string | null
  departmentName?: string
  custodian?: string | null
  custodianName?: string
  supplier?: string | null
  supplierName?: string
  tags?: string[]
  tagNames?: string[]
  highlight?: Record<string, string[]>
  score?: number
}

export interface AssetSearchResponse {
  total: number
  page: number
  pageSize: number
  totalPages: number
  results: AssetSearchResultRow[]
  aggregations: Record<string, any>
  engine?: string
}

export interface SearchSuggestionRecord {
  suggestion: string
  count: number
}

export interface SearchHistoryRecord {
  id: string
  searchType: string
  keyword: string
  filters: Record<string, any>
  resultCount: number
  searchCount: number
  lastSearchedAt: string
}

export interface SavedSearchRecord {
  id: string
  name: string
  searchType: string
  keyword: string
  filters: Record<string, any>
  isShared: boolean
  useCount: number
}

export interface PaginatedSearchRecords<T> {
  count: number
  next: string | null
  previous: string | null
  results: T[]
}

export interface SearchSuggestionQuery {
  keyword: string
  type?: string
  limit?: number
}

export interface SearchHistoryQuery {
  type?: string
  limit?: number
  page?: number
}

export interface SavedSearchQuery {
  type?: string
  limit?: number
  page?: number
}

export interface CreateSavedSearchPayload {
  name: string
  searchType?: string
  keyword?: string
  filters?: Record<string, any>
  isShared?: boolean
}

const normalizeOrdering = (ordering?: string): { sortBy: string; sortOrder: 'asc' | 'desc' } => {
  if (!ordering) {
    return { sortBy: 'relevance', sortOrder: 'desc' }
  }

  const sortOrder: 'asc' | 'desc' = ordering.startsWith('-') ? 'desc' : 'asc'
  const normalized = ordering.replace(/^-/, '')
  const sortByMap: Record<string, string> = {
    assetCode: 'code',
    purchaseDate: 'date',
    purchasePrice: 'price',
  }
  return {
    sortBy: sortByMap[normalized] || 'relevance',
    sortOrder,
  }
}

export const buildAssetSearchPayload = (params: Record<string, any> = {}) => {
  const filters: AssetSearchFilters = {}

  if (params.categoryId) filters.category = params.categoryId
  if (params.status) filters.status = params.status
  if (params.locationId) filters.location = params.locationId
  if (Array.isArray(params.purchaseDateRange)) {
    if (params.purchaseDateRange[0]) filters.purchaseDateFrom = params.purchaseDateRange[0]
    if (params.purchaseDateRange[1]) filters.purchaseDateTo = params.purchaseDateRange[1]
  }

  const { sortBy, sortOrder } = normalizeOrdering(params.ordering)
  return {
    searchType: 'asset',
    keyword: String(params.search || '').trim(),
    filters,
    sortBy,
    sortOrder,
    page: Number(params.page || 1),
    pageSize: Number(params.pageSize || params.page_size || 20),
  }
}

export const searchAssets = (payload: Record<string, any>): Promise<AssetSearchResponse> => {
  return request.post('/search/', payload)
}

export const searchAssetsForList = async (
  params: Record<string, any> = {}
): Promise<PaginatedSearchRecords<AssetSearchResultRow> & Record<string, any>> => {
  const response = await searchAssets(buildAssetSearchPayload(params))
  return {
    count: response.total || 0,
    next: null,
    previous: null,
    results: response.results || [],
    aggregations: response.aggregations || {},
    page: response.page,
    pageSize: response.pageSize,
    totalPages: response.totalPages,
    engine: response.engine,
  }
}

export const getSearchSuggestions = (
  params: SearchSuggestionQuery
): Promise<SearchSuggestionRecord[]> => {
  return request.get('/search/suggestions/', { params })
}

export const getSearchHistory = async (
  params: SearchHistoryQuery = {}
): Promise<PaginatedSearchRecords<SearchHistoryRecord>> => {
  return request.get('/search/history/', {
    params: {
      type: params.type || 'asset',
      page: params.page || 1,
      page_size: params.limit || 10,
    },
  })
}

export const getSavedSearches = async (
  params: SavedSearchQuery = {}
): Promise<PaginatedSearchRecords<SavedSearchRecord>> => {
  return request.get('/search/saved/', {
    params: {
      type: params.type || 'asset',
      page: params.page || 1,
      page_size: params.limit || 20,
    },
  })
}

export const createSavedSearch = (
  payload: CreateSavedSearchPayload
): Promise<SavedSearchRecord> => {
  return request.post('/search/saved/', payload)
}

export const useSavedSearch = (id: string): Promise<SavedSearchRecord> => {
  return request.post(`/search/saved/${id}/use/`)
}
