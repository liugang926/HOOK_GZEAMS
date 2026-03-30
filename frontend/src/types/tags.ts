/**
 * Tag module type definitions.
 */

import type { BaseModel } from './common'

export interface Tag extends BaseModel {
  name: string
  color: string
  description?: string
  bizType?: string
  usageCount: number
}

export interface TagBusinessObjectOption {
  value: string
  label: string
  nameEn?: string
  isHardcoded?: boolean
}

export interface TagStatisticsBucket {
  bizType: string
  label: string
  nameEn?: string
  count: number
  usageCount: number
}

export interface TagStatistics {
  total: number
  used: number
  unused: number
  byBizType: TagStatisticsBucket[]
  topTags: Array<Pick<Tag, 'id' | 'name' | 'color' | 'bizType' | 'usageCount'>>
}

export interface TagObjectActionPayload {
  tagIds: string[]
  objectIds: string[]
  bizType: string
}

export interface TagApplyResult {
  bizType: string
  tagIds: string[]
  objectIds: string[]
  createdCount: number
  restoredCount: number
  skippedCount: number
  assignmentCount: number
}

export interface TagRemoveResult {
  bizType: string
  tagIds: string[]
  objectIds: string[]
  removedCount: number
}

export type AssetTagMatchType = 'and' | 'or'

export interface AssetTagSummary {
  id: string
  tagGroup: string
  groupName: string
  groupColor: string
  name: string
  code: string
  color: string
  icon?: string
  assetCount?: number
}

export interface AssetTagGroup {
  id: string
  name: string
  code: string
  description?: string
  color: string
  icon?: string
  sortOrder: number
  isSystem: boolean
  isActive: boolean
  tagsCount: number
  tags: AssetTagSummary[]
}

export interface AssetTag extends AssetTagSummary {
  description?: string
  sortOrder: number
  isActive: boolean
  tagGroupName: string
}

export interface AssetTagRelation {
  id: string
  asset: string
  tag: AssetTagSummary
  taggedBy?: {
    id: string
    username: string
    email?: string
    firstName?: string
    lastName?: string
  } | null
  taggedAt: string
  notes?: string
}

export interface AssetTagAssignmentPayload {
  assetId: string
  assetCode: string
  assetName: string
  tags: AssetTagRelation[]
}

export interface AssetTagMutationResult {
  addedCount: number
  restoredCount: number
  skippedCount: number
  relations: AssetTagRelation[]
}

export interface AssetTagBatchActionPayload {
  assetIds: string[]
  tagIds: string[]
  notes?: string
}

export interface AssetTagBatchActionResult {
  assetId: string
  assetCode: string
  tagsAdded?: number
  tagsRemoved?: number
  skipped?: number
}

export interface AssetTagBatchActionResponse {
  success: boolean
  message?: string
  summary: {
    total: number
    succeeded: number
    failed: number
    totalAssets?: number
    totalTags?: number
    relationsCreated?: number
    relationsRestored?: number
    relationsRemoved?: number
    skipped?: number
  }
  results: AssetTagBatchActionResult[]
}

export interface AssetTagStatisticsItem {
  id: string
  tagGroup: string
  groupName: string
  name: string
  code: string
  color: string
  assetCount: number
  percentage: number
}

export interface AssetTagStatistics {
  totalTags: number
  totalTaggedAssets: number
  tagStatistics: AssetTagStatisticsItem[]
}

export interface AssetByTagsPayload {
  tagIds: string[]
  matchType?: AssetTagMatchType
}

export interface AssetByTagsResult<T = Record<string, any>> {
  count: number
  matchType: AssetTagMatchType
  results: T[]
}

export interface AssetTagQueryParams {
  page?: number
  pageSize?: number
  search?: string
  tagGroup?: string
  isActive?: boolean
  ordering?: string
}

export interface AssetTagGroupQueryParams {
  page?: number
  pageSize?: number
  search?: string
  isActive?: boolean
  isSystem?: boolean
  ordering?: string
}
