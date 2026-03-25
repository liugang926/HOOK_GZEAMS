import { describe, expect, it } from 'vitest'
import {
  buildDesignerPreviewScopeId,
  buildObjectPageScopeId,
  buildRecordScopeId
} from '@/platform/reference/pageScope'

describe('pageScope', () => {
  it('builds designer preview scope with defaults', () => {
    expect(buildDesignerPreviewScopeId({ mode: 'readonly', layoutId: 'layout-1' }))
      .toBe('designer-preview:readonly:layout-1')
    expect(buildDesignerPreviewScopeId({}))
      .toBe('designer-preview:edit:draft')
  })

  it('builds record scope with id fallback', () => {
    expect(buildRecordScopeId('asset-1')).toBe('asset-1')
    expect(buildRecordScopeId('', 'ASSET-001')).toBe('record:ASSET-001')
    expect(buildRecordScopeId(null, null)).toBe('')
  })

  it('builds object page scope for detail/edit/create', () => {
    expect(buildObjectPageScopeId({
      routePath: '/objects/Asset/a-1',
      objectCode: 'Asset',
      recordId: 'a-1'
    })).toBe('object-detail:Asset')

    expect(buildObjectPageScopeId({
      routePath: '/objects/Asset/a-1/edit',
      objectCode: 'Asset',
      recordId: 'a-1'
    })).toBe('object-edit:Asset')

    expect(buildObjectPageScopeId({
      routePath: '/objects/Asset/create',
      objectCode: 'Asset'
    })).toBe('object-create:Asset')
  })

  it('maps redirected action=edit to object edit scope', () => {
    expect(buildObjectPageScopeId({
      routePath: '/objects/Asset/a-1',
      objectCode: 'Asset',
      recordId: 'a-1',
      action: 'edit'
    })).toBe('object-edit:Asset')
  })
})

