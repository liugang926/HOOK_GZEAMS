import { describe, expect, it } from 'vitest'
import {
  buildDesignerRelationGroupScopeId,
  buildRecordRelationGroupScopeId
} from '@/platform/reference/relationGroupScope'
import { buildDesignerPreviewScopeId, buildRecordScopeId } from '@/platform/reference/pageScope'

describe('relationGroupScope', () => {
  it('uses record id as scope for business records', () => {
    expect(buildRecordRelationGroupScopeId('asset-1')).toBe('asset-1')
    expect(buildRecordRelationGroupScopeId('  asset-2  ')).toBe('asset-2')
  })

  it('falls back to record code when record id is unavailable', () => {
    expect(buildRecordRelationGroupScopeId('', 'ASSET-001')).toBe('record:ASSET-001')
    expect(buildRecordRelationGroupScopeId(null, null)).toBe('')
  })

  it('builds isolated designer preview scope', () => {
    expect(buildDesignerRelationGroupScopeId({ mode: 'edit', layoutId: 'layout-1' }))
      .toBe('designer-preview:edit:layout-1')
    expect(buildDesignerRelationGroupScopeId({}))
      .toBe('designer-preview:edit:draft')
    expect(buildDesignerRelationGroupScopeId({ mode: 'edit', layoutId: 'layout-1' }))
      .toBe(buildDesignerPreviewScopeId({ mode: 'edit', layoutId: 'layout-1' }))
    expect(buildRecordRelationGroupScopeId('asset-1')).toBe(buildRecordScopeId('asset-1'))
  })
})
