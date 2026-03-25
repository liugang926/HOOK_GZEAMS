import { describe, expect, it } from 'vitest'

import {
  buildAssetProjectDetailPath,
  buildAssetProjectReturnCreateRoute,
  formatTransferProjectOptionLabel,
} from '../assetProjectAssetActions'

describe('assetProjectAssetActions', () => {
  it('builds the AssetProject detail path', () => {
    expect(buildAssetProjectDetailPath('project-1')).toBe('/objects/AssetProject/project-1')
  })

  it('builds an AssetReturn create route with project returnTo context', () => {
    const route = buildAssetProjectReturnCreateRoute({
      projectId: 'project-1',
      projectRecord: {
        projectCode: 'XM2026030001',
        projectName: 'AI Platform',
      },
      row: {
        id: 'allocation-1',
        asset: 'asset-1',
        assetCode: 'ZC001',
        assetName: 'GPU Server',
      },
      date: new Date('2026-03-20T08:00:00.000Z'),
    })

    expect(route.path).toBe('/objects/AssetReturn/create')
    expect(route.query.returnTo).toBe('/objects/AssetProject/project-1')

    const payload = JSON.parse(String(route.query.prefill || '{}'))
    expect(payload.return_date).toBe('2026-03-20')
    expect(payload.return_reason).toContain('XM2026030001 AI Platform')
    expect(payload.items).toEqual([
      {
        asset_id: 'asset-1',
        project_allocation_id: 'allocation-1',
        asset_status: 'idle',
        remark: 'Source project: XM2026030001 AI Platform | Asset: ZC001 GPU Server',
      },
    ])
  })

  it('formats transfer target project labels from metadata fields', () => {
    expect(formatTransferProjectOptionLabel({
      project_code: 'XM2026030002',
      project_name: 'Target Project',
    })).toBe('XM2026030002 - Target Project')
  })
})
