import { describe, expect, it } from 'vitest'
import { extractRuntimeListColumns } from './runtimeListLayoutAdapter'

describe('extractRuntimeListColumns', () => {
  it('returns explicit columns when layout has columns', () => {
    const runtime = {
      layout: {
        layoutConfig: {
          columns: [
            { fieldCode: 'code', label: 'Code' },
            { fieldCode: 'name', label: 'Name' },
          ]
        }
      }
    }

    const columns = extractRuntimeListColumns(runtime)
    expect(columns).toHaveLength(2)
    expect(columns[0].fieldCode).toBe('code')
  })

  it('flattens section/tab/collapse fields when columns are absent', () => {
    const runtime = {
      layout: {
        layoutConfig: {
          sections: [
            { type: 'section', fields: [{ fieldCode: 'assetCode' }] },
            { type: 'tab', tabs: [{ fields: [{ fieldCode: 'assetName' }] }] },
            { type: 'collapse', items: [{ fields: [{ fieldCode: 'status' }] }] },
          ]
        }
      }
    }

    const columns = extractRuntimeListColumns(runtime)
    expect(columns.map((c) => c.fieldCode)).toEqual(['assetCode', 'assetName', 'status'])
  })

  it('returns empty array when runtime layout is empty', () => {
    expect(extractRuntimeListColumns({})).toEqual([])
    expect(extractRuntimeListColumns({ layout: {} })).toEqual([])
  })
})
