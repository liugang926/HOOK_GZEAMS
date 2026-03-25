import { describe, expect, it, vi } from 'vitest'
import {
  buildDynamicObjectDetailPath,
  buildDynamicObjectEditPath,
  buildDynamicObjectListPath,
  pushDynamicObjectDetail,
  pushDynamicObjectEdit,
  resolveDynamicDetailRelationObjectCode,
} from './dynamicDetailNavigation'

describe('dynamicDetailNavigation', () => {
  it('resolves relation object codes with explicit target overrides', () => {
    expect(resolveDynamicDetailRelationObjectCode('maintenance_records')).toBe('Maintenance')
    expect(resolveDynamicDetailRelationObjectCode('maintenance_records', 'WorkOrder')).toBe('WorkOrder')
  })

  it('builds canonical object list/detail/edit paths', () => {
    expect(buildDynamicObjectListPath('Asset')).toBe('/objects/Asset')
    expect(buildDynamicObjectDetailPath('Asset', 'asset 1')).toBe('/objects/Asset/asset%201')
    expect(buildDynamicObjectEditPath('Asset', 'asset/1')).toBe('/objects/Asset/asset%2F1/edit')
    expect(buildDynamicObjectDetailPath('', 'asset-1')).toBe('')
  })

  it('pushes related detail and edit routes only when paths are valid', () => {
    const push = vi.fn()
    const router = { push } as any

    pushDynamicObjectDetail({
      router,
      relationCode: 'maintenance_records',
      record: { id: 'm 1' },
    })
    pushDynamicObjectEdit({
      router,
      relationCode: 'loan_records',
      record: { id: 'loan/1' },
    })
    pushDynamicObjectDetail({
      router,
      relationCode: 'maintenance_records',
      record: { id: '' },
    })

    expect(push.mock.calls).toEqual([
      ['/objects/Maintenance/m%201'],
      ['/objects/Loan/loan%2F1/edit'],
    ])
  })
})
