import { describe, expect, it, vi } from 'vitest'
import {
  buildDynamicListCreatePath,
  buildDynamicListDetailPath,
  buildDynamicListEditPath,
  buildDynamicListLayoutSettingsRoute,
  buildDynamicListObjectPath,
  pushDynamicListCreate,
  pushDynamicListEdit,
  pushDynamicListLayoutSettings,
  pushDynamicListView,
  resolveDynamicListRowId,
} from './dynamicListNavigation'

describe('dynamicListNavigation', () => {
  it('resolves row ids from id and _id fields', () => {
    expect(resolveDynamicListRowId({ id: 'asset-1' })).toBe('asset-1')
    expect(resolveDynamicListRowId({ _id: 'asset-2' })).toBe('asset-2')
    expect(resolveDynamicListRowId({})).toBe('')
  })

  it('builds canonical list/create/detail/edit paths and layout settings route', () => {
    expect(buildDynamicListObjectPath('Asset')).toBe('/objects/Asset')
    expect(buildDynamicListCreatePath('Asset')).toBe('/objects/Asset/create')
    expect(buildDynamicListDetailPath({ objectCode: 'Asset', row: { id: 'asset 1' } })).toBe('/objects/Asset/asset%201')
    expect(buildDynamicListEditPath({ objectCode: 'Asset', row: { _id: 'asset/1' } })).toBe('/objects/Asset/asset%2F1/edit')
    expect(buildDynamicListLayoutSettingsRoute({
      objectCode: 'Asset',
      objectName: 'Asset',
    })).toEqual({
      path: '/system/page-layouts',
      query: {
        objectCode: 'Asset',
        objectName: 'Asset',
      },
    })
  })

  it('pushes valid routes and skips invalid targets', () => {
    const push = vi.fn()
    const router = { push } as any

    pushDynamicListView({
      router,
      objectCode: 'Asset',
      row: { id: 'asset-1' },
    })
    pushDynamicListCreate({
      router,
      objectCode: 'Asset',
    })
    pushDynamicListEdit({
      router,
      objectCode: 'Asset',
      row: { _id: 'asset-2' },
    })
    pushDynamicListLayoutSettings({
      router,
      objectCode: 'Asset',
      objectName: 'Asset',
    })
    pushDynamicListView({
      router,
      objectCode: 'Asset',
      row: {},
    })

    expect(push.mock.calls).toEqual([
      ['/objects/Asset/asset-1'],
      ['/objects/Asset/create'],
      ['/objects/Asset/asset-2/edit'],
      [{
        path: '/system/page-layouts',
        query: {
          objectCode: 'Asset',
          objectName: 'Asset',
        },
      }],
    ])
  })
})
