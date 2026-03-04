import { describe, expect, it } from 'vitest'
import { buildRenderSchema } from './renderSchema'

describe('renderSchema', () => {
  it('follows layout field order across section/tab/collapse', () => {
    const schema = buildRenderSchema({
      mode: 'readonly',
      fields: [
        { code: 'name', fieldType: 'text' },
        { code: 'amount', fieldType: 'number' },
        { code: 'owner', fieldType: 'user' },
        { code: 'memo', fieldType: 'textarea' }
      ],
      layoutConfig: {
        sections: [
          {
            id: 'basic',
            type: 'section',
            title: 'Basic',
            collapsible: true,
            collapsed: true,
            fields: [{ fieldCode: 'name' }, { fieldCode: 'amount' }]
          },
          {
            id: 'extra',
            type: 'tab',
            title: 'Extra',
            tabs: [
              { id: 'main', title: 'Main', fields: [{ fieldCode: 'owner' }] }
            ]
          },
          {
            id: 'notes',
            type: 'collapse',
            title: 'Notes',
            items: [
              { id: 'memo', title: 'Memo', fields: [{ fieldCode: 'memo' }] }
            ]
          }
        ]
      }
    })

    expect(schema.fieldOrder).toEqual(['name', 'amount', 'owner', 'memo'])
    expect(schema.sections).toHaveLength(3)
    expect(schema.sections[0].collapsible).toBe(true)
    expect(schema.sections[0].collapsed).toBe(true)
    expect(schema.sections[1].kind).toBe('tab')
    expect(schema.sections[1].containerId).toBe('extra')
    expect(schema.sections[1].itemId).toBe('main')
    expect(schema.sections[2].kind).toBe('collapse')
    expect(schema.sections[2].containerId).toBe('notes')
    expect(schema.sections[2].itemId).toBe('memo')
  })

  it('falls back to sort order when layout sections are missing', () => {
    const schema = buildRenderSchema({
      mode: 'edit',
      fields: [
        { code: 'c', fieldType: 'text', sortOrder: 3 },
        { code: 'a', fieldType: 'text', sortOrder: 1 },
        { code: 'b', fieldType: 'text', sortOrder: 2 }
      ],
      layoutConfig: null
    })

    expect(schema.sections).toHaveLength(1)
    expect(schema.fieldOrder).toEqual(['a', 'b', 'c'])
  })

  it('uses layout label override and mode readonly policy', () => {
    const schema = buildRenderSchema({
      mode: 'readonly',
      fields: [{ code: 'assetName', fieldType: 'text', name: 'Asset Name', isReadonly: false }],
      layoutConfig: {
        sections: [
          {
            id: 'basic',
            type: 'section',
            fields: [
              {
                fieldCode: 'assetName',
                label: 'Asset Name (Layout)'
              }
            ]
          }
        ]
      }
    })

    expect(schema.sections[0].fields[0].label).toBe('Asset Name (Layout)')
    expect(schema.sections[0].fields[0].readonly).toBe(true)
  })

  it('prioritizes layout readonly/editable flags in edit mode', () => {
    const schema = buildRenderSchema({
      mode: 'edit',
      fields: [
        { code: 'assetCode', fieldType: 'text', isReadonly: false, isEditable: true },
        { code: 'assetName', fieldType: 'text', isReadonly: false, isEditable: true }
      ],
      layoutConfig: {
        sections: [
          {
            id: 'basic',
            type: 'section',
            fields: [
              { fieldCode: 'assetCode', readonly: true },
              { fieldCode: 'assetName', editable: false }
            ]
          }
        ]
      }
    })

    expect(schema.sections[0].fields[0].readonly).toBe(true)
    expect(schema.sections[0].fields[1].readonly).toBe(true)
  })

  it('falls back to metadata editable flags when layout readonly is missing', () => {
    const schema = buildRenderSchema({
      mode: 'edit',
      fields: [
        { code: 'assetCode', fieldType: 'text', isEditable: false },
        { code: 'assetName', fieldType: 'text', isEditable: true }
      ],
      layoutConfig: {
        sections: [
          {
            id: 'basic',
            type: 'section',
            fields: [{ fieldCode: 'assetCode' }, { fieldCode: 'assetName' }]
          }
        ]
      }
    })

    expect(schema.sections[0].fields[0].readonly).toBe(true)
    expect(schema.sections[0].fields[1].readonly).toBe(false)
  })

  it('keeps layout minHeight in render fields', () => {
    const schema = buildRenderSchema({
      mode: 'edit',
      fields: [{ code: 'assetName', fieldType: 'text', name: 'Asset Name' }],
      layoutConfig: {
        sections: [
          {
            id: 'basic',
            type: 'section',
            fields: [{ fieldCode: 'assetName', minHeight: 132 }]
          }
        ]
      }
    })

    expect(schema.sections[0].fields[0].minHeight).toBe(132)
  })

  it('reads minHeight from componentProps when direct key is missing', () => {
    const schema = buildRenderSchema({
      mode: 'edit',
      fields: [{ code: 'assetName', fieldType: 'text', name: 'Asset Name' }],
      layoutConfig: {
        sections: [
          {
            id: 'basic',
            type: 'section',
            fields: [{ fieldCode: 'assetName', componentProps: { minHeight: 168 } }]
          }
        ]
      }
    })

    expect(schema.sections[0].fields[0].minHeight).toBe(168)
  })

  it('keeps persisted layoutPlacement in render fields', () => {
    const schema = buildRenderSchema({
      mode: 'edit',
      fields: [{ code: 'assetName', fieldType: 'text', name: 'Asset Name' }],
      layoutConfig: {
        sections: [
          {
            id: 'basic',
            type: 'section',
            fields: [
              {
                fieldCode: 'assetName',
                layoutPlacement: {
                  row: 1,
                  colStart: 2,
                  colSpan: 1,
                  rowSpan: 1,
                  columns: 2,
                  totalRows: 1,
                  order: 1,
                  canvas: { x: 0.5, y: 0, width: 0.5, height: 1 }
                }
              }
            ]
          }
        ]
      }
    })

    expect((schema.sections[0].fields[0] as any).layoutPlacement).toMatchObject({
      row: 1,
      colStart: 2,
      colSpan: 1
    })
  })
})
