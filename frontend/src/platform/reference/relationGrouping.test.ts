import { describe, expect, it } from 'vitest'
import {
  defaultRelationGroupExpanded,
  groupRelations,
  inferRelationGroupKey
} from './relationGrouping'

describe('relationGrouping', () => {
  it('infers workflow and finance groups', () => {
    expect(inferRelationGroupKey({ code: 'workflow_instances', relatedObjectCode: 'WorkflowInstance' })).toBe('workflow')
    expect(inferRelationGroupKey({ code: 'finance_vouchers', relatedObjectCode: 'FinanceVoucher' })).toBe('finance')
  })

  it('uses explicit group and keeps relation order', () => {
    const grouped = groupRelations(
      [
        { code: 'b', sortOrder: 20, groupKey: 'workflow', groupName: 'Workflow' },
        { code: 'a', sortOrder: 10, groupKey: 'workflow', groupName: 'Workflow' }
      ],
      { getTitle: (key) => key }
    )
    expect(grouped).toHaveLength(1)
    expect(grouped[0].relations.map((r) => r.code)).toEqual(['a', 'b'])
  })

  it('applies default expanded strategy', () => {
    expect(defaultRelationGroupExpanded('business')).toBe(true)
    expect(defaultRelationGroupExpanded('workflow')).toBe(true)
    expect(defaultRelationGroupExpanded('finance')).toBe(false)
  })
})

