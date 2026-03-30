import request from '@/utils/request'
import { normalizeQueryParams } from '@/api/contract'
import type { BatchResponse, PaginatedResponse } from '@/types/api'
import type {
  AssetByTagsPayload,
  AssetByTagsResult,
  AssetTag,
  AssetTagAssignmentPayload,
  AssetTagBatchActionPayload,
  AssetTagBatchActionResponse,
  AssetTagGroup,
  AssetTagGroupQueryParams,
  AssetTagMutationResult,
  AssetTagQueryParams,
  AssetTagStatistics,
  Tag,
  TagApplyResult,
  TagBusinessObjectOption,
  TagObjectActionPayload,
  TagRemoveResult,
  TagStatistics,
} from '@/types/tags'

type BatchDeleteResponse = BatchResponse & {
  success: boolean
  message?: string
}

export const tagApi = {
  list(params?: Record<string, any>) {
    return request.get<PaginatedResponse<Tag>>('/system/tags/', { params })
  },

  detail(id: string) {
    return request.get<Tag>(`/system/tags/${id}/`)
  },

  create(data: Partial<Tag>) {
    return request.post<Tag>('/system/tags/', data)
  },

  update(id: string, data: Partial<Tag>) {
    return request.put<Tag>(`/system/tags/${id}/`, data)
  },

  delete(id: string) {
    return request.delete(`/system/tags/${id}/`)
  },

  batchDelete(ids: string[]) {
    return request.post<BatchDeleteResponse>('/system/tags/batch-delete/', { ids })
  },

  statistics() {
    return request.get<TagStatistics>('/system/tags/statistics/')
  },

  getBusinessObjectOptions() {
    return request.get<TagBusinessObjectOption[]>('/system/tags/business-object-options/')
  },

  apply(data: TagObjectActionPayload) {
    return request.post<TagApplyResult>('/system/tags/apply/', data)
  },

  remove(data: TagObjectActionPayload) {
    return request.post<TagRemoveResult>('/system/tags/remove/', data)
  },
}

const ASSET_TAG_GROUP_BASE = '/objects/tags/groups'
const ASSET_TAG_BASE = '/objects/tags'
const ASSET_TAG_ASSET_BASE = '/objects/assets'

export const assetTagGroupApi = {
  list(params?: AssetTagGroupQueryParams) {
    return request.get<PaginatedResponse<AssetTagGroup>>(`${ASSET_TAG_GROUP_BASE}/`, {
      params: normalizeQueryParams(params, {
        aliases: {
          pageSize: 'page_size',
          isActive: 'is_active',
          isSystem: 'is_system',
        },
      }),
    })
  },

  detail(id: string) {
    return request.get<AssetTagGroup>(`${ASSET_TAG_GROUP_BASE}/${id}/`)
  },

  create(data: Partial<AssetTagGroup>) {
    return request.post<AssetTagGroup>(`${ASSET_TAG_GROUP_BASE}/`, data)
  },

  update(id: string, data: Partial<AssetTagGroup>) {
    return request.put<AssetTagGroup>(`${ASSET_TAG_GROUP_BASE}/${id}/`, data)
  },

  delete(id: string) {
    return request.delete<{ success: boolean; message?: string }>(`${ASSET_TAG_GROUP_BASE}/${id}/`)
  },
}

export const assetTagApi = {
  list(params?: AssetTagQueryParams) {
    return request.get<PaginatedResponse<AssetTag>>(`${ASSET_TAG_BASE}/`, {
      params: normalizeQueryParams(params, {
        aliases: {
          pageSize: 'page_size',
          tagGroup: 'tag_group',
          isActive: 'is_active',
        },
      }),
    })
  },

  detail(id: string) {
    return request.get<AssetTag>(`${ASSET_TAG_BASE}/${id}/`)
  },

  create(data: Partial<AssetTag>) {
    return request.post<AssetTag>(`${ASSET_TAG_BASE}/`, data)
  },

  update(id: string, data: Partial<AssetTag>) {
    return request.put<AssetTag>(`${ASSET_TAG_BASE}/${id}/`, data)
  },

  delete(id: string) {
    return request.delete<{ success: boolean; message?: string }>(`${ASSET_TAG_BASE}/${id}/`)
  },

  statistics(params?: { tagGroup?: string }) {
    return request.get<AssetTagStatistics>(`${ASSET_TAG_BASE}/statistics/`, {
      params: normalizeQueryParams(params, {
        aliases: {
          tagGroup: 'tag_group',
        },
      }),
    })
  },

  batchAdd(data: AssetTagBatchActionPayload) {
    return request.post<AssetTagBatchActionResponse>(`${ASSET_TAG_BASE}/batch-add/`, data)
  },

  batchRemove(data: AssetTagBatchActionPayload) {
    return request.post<AssetTagBatchActionResponse>(`${ASSET_TAG_BASE}/batch-remove/`, data)
  },
}

export const assetTagAssignmentApi = {
  list(assetId: string) {
    return request.get<AssetTagAssignmentPayload>(`${ASSET_TAG_ASSET_BASE}/${assetId}/tags/`)
  },

  add(assetId: string, data: { tagIds: string[]; notes?: string }) {
    return request.post<AssetTagMutationResult>(`${ASSET_TAG_ASSET_BASE}/${assetId}/tags/`, data)
  },

  remove(assetId: string, tagId: string) {
    return request.delete<{ success: boolean; message?: string }>(
      `${ASSET_TAG_ASSET_BASE}/${assetId}/tags/${tagId}/`
    )
  },

  searchAssetsByTags<T = Record<string, any>>(data: AssetByTagsPayload) {
    return request.post<AssetByTagsResult<T>>(`${ASSET_TAG_ASSET_BASE}/by-tags/`, data)
  },
}
