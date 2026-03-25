import { describe, expect, it } from 'vitest'
import { resolveReferenceLookupDefaultColumns } from './referenceLookupColumnPresets'

describe('referenceLookupColumnPresets', () => {
  it('should include object preset columns for user', () => {
    const columns = resolveReferenceLookupDefaultColumns({
      objectCode: 'User',
      displayField: 'fullName',
      secondaryField: 'username'
    })
    expect(columns.map((column) => column.key)).toEqual([
      'fullName',
      'username',
      'id',
      'email',
      'mobile'
    ])
  })

  it('should return base columns for unknown object', () => {
    const columns = resolveReferenceLookupDefaultColumns({
      objectCode: 'CustomObject',
      displayField: 'name',
      secondaryField: 'code'
    })
    expect(columns.map((column) => column.key)).toEqual(['name', 'code', 'id'])
  })

  it('should dedupe repeated display and secondary fields', () => {
    const columns = resolveReferenceLookupDefaultColumns({
      objectCode: 'Asset',
      displayField: 'name',
      secondaryField: 'name'
    })
    expect(columns.map((column) => column.key)).toEqual(['name', 'id', 'assetCode', 'status'])
  })
})
