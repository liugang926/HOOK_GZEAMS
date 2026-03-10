import { describe, expect, it } from 'vitest'

import { resolveListFieldValue } from '@/utils/listFieldValue'

describe('resolveListFieldValue', () => {
  it('preserves the reference id when a flattened display alias exists', () => {
    const value = resolveListFieldValue(
      {
        department: 'dept-1',
        departmentName: 'Finance'
      },
      {
        fieldCode: 'department',
        prop: 'department',
        fieldType: 'department',
        referenceDisplayField: 'name'
      }
    )

    expect(value).toEqual({
      id: 'dept-1',
      name: 'Finance'
    })
  })

  it('supports user-style flattened reference fields', () => {
    const value = resolveListFieldValue(
      {
        custodian: 'user-1',
        custodianUsername: 'zhangsan'
      },
      {
        fieldCode: 'custodian',
        prop: 'custodian',
        fieldType: 'user',
        referenceDisplayField: 'username'
      }
    )

    expect(value).toEqual({
      id: 'user-1',
      username: 'zhangsan'
    })
  })

  it('supports expanded location aliases such as full path names', () => {
    const value = resolveListFieldValue(
      {
        location: 'loc-1',
        locationFullPathName: 'HQ / Floor 1 / Warehouse'
      },
      {
        fieldCode: 'location',
        prop: 'location',
        fieldType: 'location',
        referenceDisplayField: 'fullPathName'
      }
    )

    expect(value).toEqual({
      id: 'loc-1',
      fullPathName: 'HQ / Floor 1 / Warehouse'
    })
  })

  it('treats columns with reference metadata as references even when fieldType degrades to text', () => {
    const value = resolveListFieldValue(
      {
        custodianUsername: 'zhangsan'
      },
      {
        fieldCode: 'custodian',
        prop: 'custodian',
        fieldType: 'text',
        referenceObject: 'User',
        referenceDisplayField: 'username'
      }
    )

    expect(value).toBe('zhangsan')
  })

  it('accepts targetObjectCode as a reference hint when referenceObject is absent', () => {
    const value = resolveListFieldValue(
      {
        department: 'dept-1',
        departmentName: 'Finance'
      },
      {
        fieldCode: 'department',
        prop: 'department',
        fieldType: 'text',
        targetObjectCode: 'Department',
        referenceDisplayField: 'name'
      }
    )

    expect(value).toEqual({
      id: 'dept-1',
      name: 'Finance'
    })
  })

  it('keeps object values intact for reference-like fields', () => {
    const value = resolveListFieldValue(
      {
        location: {
          id: 'loc-1',
          fullPath: 'HQ / Floor 1 / Warehouse'
        }
      },
      {
        fieldCode: 'location',
        prop: 'location',
        fieldType: 'location',
        referenceDisplayField: 'fullPath'
      }
    )

    expect(value).toEqual({
      id: 'loc-1',
      fullPath: 'HQ / Floor 1 / Warehouse'
    })
  })
})
