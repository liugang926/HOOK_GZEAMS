import { beforeEach, describe, expect, it, vi } from 'vitest'

import request from '@/utils/request'
import { assetTagApi, assetTagAssignmentApi, assetTagGroupApi } from '@/api/tags'

vi.mock('@/utils/request', () => ({
  default: {
    get: vi.fn(),
    post: vi.fn(),
    put: vi.fn(),
    patch: vi.fn(),
    delete: vi.fn(),
  },
}))

type MockedRequest = {
  get: ReturnType<typeof vi.fn>
  post: ReturnType<typeof vi.fn>
  put: ReturnType<typeof vi.fn>
  patch: ReturnType<typeof vi.fn>
  delete: ReturnType<typeof vi.fn>
}

const mockedRequest = request as unknown as MockedRequest

describe('asset tag api adapters', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('assetTagGroupApi.list should map query params to the alias endpoint', async () => {
    mockedRequest.get.mockResolvedValue({
      count: 1,
      next: null,
      previous: null,
      results: [],
    })

    await assetTagGroupApi.list({
      page: 2,
      pageSize: 50,
      search: 'usage',
      isActive: true,
      isSystem: false,
    })

    expect(mockedRequest.get).toHaveBeenCalledWith('/objects/tags/groups/', {
      params: {
        page: 2,
        page_size: 50,
        search: 'usage',
        is_active: true,
        is_system: false,
      },
    })
  })

  it('assetTagApi should use the tag statistics and batch endpoints', async () => {
    mockedRequest.get.mockResolvedValue({
      totalTags: 2,
      totalTaggedAssets: 3,
      tagStatistics: [],
    })
    mockedRequest.post.mockResolvedValue({
      success: true,
      summary: {
        total: 2,
        succeeded: 2,
        failed: 0,
      },
      results: [],
    })

    await assetTagApi.statistics({ tagGroup: 'group-1' })
    await assetTagApi.batchAdd({
      assetIds: ['asset-1', 'asset-2'],
      tagIds: ['tag-1'],
      notes: 'batch add',
    })

    expect(mockedRequest.get).toHaveBeenCalledWith('/objects/tags/statistics/', {
      params: {
        tag_group: 'group-1',
      },
    })
    expect(mockedRequest.post).toHaveBeenCalledWith('/objects/tags/batch-add/', {
      assetIds: ['asset-1', 'asset-2'],
      tagIds: ['tag-1'],
      notes: 'batch add',
    })
  })

  it('assetTagAssignmentApi should target the asset tag assignment alias routes', async () => {
    mockedRequest.get.mockResolvedValue({
      assetId: 'asset-1',
      tags: [],
    })
    mockedRequest.post.mockResolvedValue({
      addedCount: 1,
      restoredCount: 0,
      skippedCount: 0,
      relations: [],
    })
    mockedRequest.delete.mockResolvedValue({
      success: true,
    })

    await assetTagAssignmentApi.list('asset-1')
    await assetTagAssignmentApi.add('asset-1', {
      tagIds: ['tag-1', 'tag-2'],
      notes: 'apply',
    })
    await assetTagAssignmentApi.remove('asset-1', 'tag-1')
    await assetTagAssignmentApi.searchAssetsByTags({
      tagIds: ['tag-1', 'tag-2'],
      matchType: 'and',
    })

    expect(mockedRequest.get).toHaveBeenCalledWith('/objects/assets/asset-1/tags/')
    expect(mockedRequest.post).toHaveBeenNthCalledWith(1, '/objects/assets/asset-1/tags/', {
      tagIds: ['tag-1', 'tag-2'],
      notes: 'apply',
    })
    expect(mockedRequest.delete).toHaveBeenCalledWith('/objects/assets/asset-1/tags/tag-1/')
    expect(mockedRequest.post).toHaveBeenNthCalledWith(2, '/objects/assets/by-tags/', {
      tagIds: ['tag-1', 'tag-2'],
      matchType: 'and',
    })
  })
})
