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
})
