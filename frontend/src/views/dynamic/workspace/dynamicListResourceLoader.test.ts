import { describe, expect, it } from 'vitest'
import {
  buildDynamicListFallbackMetadata,
  loadDynamicListResources,
  resolveDynamicListLoadError,
} from './dynamicListResourceLoader'

const t = (key: string) => key

describe('dynamicListResourceLoader', () => {
  it('builds fallback metadata for unresolved objects', () => {
    expect(buildDynamicListFallbackMetadata('UnknownObject')).toMatchObject({
      code: 'UnknownObject',
      name: 'UnknownObject',
      permissions: {
        view: true,
        add: true,
        change: true,
        delete: true,
      },
    })
  })

  it('loads runtime fields and metadata when both sources succeed', async () => {
    const result = await loadDynamicListResources({
      objectCode: 'Asset',
      t,
      loadRuntimeLayout: async () => ({
        fields: [
          { code: 'asset_code', name: 'Asset code' },
          { code: 'asset_name', name: 'Asset name' },
        ],
        layoutConfig: {
          columns: [{ fieldCode: 'asset_code' }],
        },
        permissions: { view: true, add: false, change: true, delete: false },
      }),
      loadMetadata: async () => ({
        code: 'Asset',
        name: 'Asset',
        fields: [{ code: 'asset_code', name: 'Asset code' }],
        layouts: {},
        permissions: { view: true, add: true, change: true, delete: true },
      } as any),
    })

    expect(result.objectMetadata.name).toBe('Asset')
    expect(result.runtimeFields).toHaveLength(2)
    expect(result.runtimeColumns).toEqual([
      expect.objectContaining({
        prop: 'asset_code',
      }),
    ])
    expect(result.runtimePermissions).toEqual({
      view: true,
      add: false,
      change: true,
      delete: false,
    })
    expect(result.loadError).toBeNull()
    expect(result.usedFallbackMetadata).toBe(false)
  })

  it('falls back to metadata-backed fields when runtime layout fails', async () => {
    const result = await loadDynamicListResources({
      objectCode: 'Asset',
      t,
      loadRuntimeLayout: async () => {
        throw new Error('runtime failed')
      },
      loadMetadata: async () => ({
        code: 'Asset',
        name: 'Asset',
        fields: [{ code: 'asset_name', name: 'Asset name' }],
        layouts: {
          list: {
            columns: [{ fieldCode: 'asset_name' }],
          },
        },
        permissions: { view: true, add: true, change: true, delete: true },
      } as any),
    })

    expect(result.objectMetadata.name).toBe('Asset')
    expect(result.runtimeFields).toEqual([{ code: 'asset_name', name: 'Asset name' }])
    expect(result.runtimeColumns).toEqual([{ fieldCode: 'asset_name' }])
    expect(result.loadError).toBeNull()
  })

  it('surfaces runtime-first errors when both runtime and metadata fail', async () => {
    await expect(loadDynamicListResources({
      objectCode: 'Asset',
      t,
      loadRuntimeLayout: async () => {
        throw new Error('runtime failed')
      },
      loadMetadata: async () => {
        throw new Error('metadata failed')
      },
    })).resolves.toMatchObject({
      loadError: 'runtime failed',
      usedFallbackMetadata: true,
    })

    expect(resolveDynamicListLoadError({
      runtimeError: new Error('runtime'),
      metadataError: new Error('metadata'),
      t,
    })).toBe('runtime')
  })
})
