import { describe, expect, it } from 'vitest'
import { buildReferenceLookupScopeId } from '@/platform/reference/referenceLookupScope'
import { buildObjectPageScopeId } from '@/platform/reference/pageScope'

describe('referenceLookupScope', () => {
  it('builds business page scope by object and page mode', () => {
    expect(buildReferenceLookupScopeId({
      routePath: '/objects/Asset/a-1',
      hostObjectCode: 'Asset',
      hostRecordId: 'a-1'
    })).toBe('object-detail:Asset')

    expect(buildReferenceLookupScopeId({
      routePath: '/objects/Asset/a-1/edit',
      hostObjectCode: 'Asset',
      hostRecordId: 'a-1'
    })).toBe('object-edit:Asset')

    expect(buildReferenceLookupScopeId({
      routePath: '/objects/Asset/create',
      hostObjectCode: 'Asset'
    })).toBe('object-create:Asset')
  })

  it('treats action=edit query as edit scope for redirected routes', () => {
    expect(buildReferenceLookupScopeId({
      routePath: '/objects/Asset/a-1',
      hostObjectCode: 'Asset',
      hostRecordId: 'a-1',
      action: 'edit'
    })).toBe('object-edit:Asset')
  })

  it('builds isolated designer lookup scope', () => {
    expect(buildReferenceLookupScopeId({
      routeName: 'PageLayoutDesigner',
      routePath: '/system/page-layouts/designer',
      layoutMode: 'edit',
      layoutId: 'layout-1'
    })).toBe('designer-preview:edit:layout-1')
  })

  it('falls back to route scope when host object is unavailable', () => {
    const input = {
      routeName: 'AssetDetail',
      routePath: '/assets/1'
    }
    expect(buildReferenceLookupScopeId(input)).toBe('route:AssetDetail')
    expect(buildReferenceLookupScopeId(input)).toBe(buildObjectPageScopeId(input))
  })
})
