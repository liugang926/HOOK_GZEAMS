import { describe, expect, it } from 'vitest'
import {
  ensureLayoutConfigIds,
  preparePersistLayoutConfig,
  resolveRawLayoutConfig
} from './layoutPersistGuard'

describe('layoutPersistGuard', () => {
  it('ensures required ids for sections and fields', () => {
    const prepared = ensureLayoutConfigIds({
      sections: [
        {
          type: 'section',
          title: 'Basic',
          fields: [{ fieldCode: 'assetName', label: 'Asset Name', span: 1 }]
        },
        {
          type: 'tab',
          tabs: [
            {
              title: 'Overview',
              fields: [{ fieldCode: 'assetCode', label: 'Asset Code', span: 1 }]
            }
          ]
        },
        {
          type: 'collapse',
          items: [
            {
              title: 'Ops',
              fields: [{ fieldCode: 'status', label: 'Status', span: 1 }]
            }
          ]
        }
      ]
    })

    expect(prepared.sections[0].id).toBeTruthy()
    expect(prepared.sections[0].fields[0].id).toBeTruthy()
    expect(prepared.sections[1].tabs[0].id).toBeTruthy()
    expect(prepared.sections[1].tabs[0].fields[0].id).toBeTruthy()
    expect(prepared.sections[2].items[0].id).toBeTruthy()
    expect(prepared.sections[2].items[0].fields[0].id).toBeTruthy()
  })

  it('extracts layout config from response payload', () => {
    const config = resolveRawLayoutConfig({
      data: {
        layoutConfig: {
          sections: [{ id: 'basic', type: 'section', fields: [] }]
        }
      }
    })

    expect(config.sections).toHaveLength(1)
    expect(config.sections[0].id).toBe('basic')
  })

  it('drops filtered fields and rejects unknown references', () => {
    const prepared = preparePersistLayoutConfig(
      {
        layoutConfig: {
          sections: [
            {
              type: 'section',
              fields: [
                { fieldCode: 'assetName', label: 'Asset Name', span: 1 },
                { fieldCode: 'created_at', label: 'Created At', span: 1 }
              ]
            }
          ]
        }
      },
      {
        layoutType: 'form',
        availableFieldCodes: ['assetName'],
        dropFieldCode: (code) => code === 'created_at'
      }
    )

    expect(prepared.sections[0].fields.map((field: any) => field.fieldCode)).toEqual(['assetName'])

    expect(() =>
      preparePersistLayoutConfig(
        {
          sections: [
            {
              type: 'section',
              fields: [{ fieldCode: 'ghostField', label: 'Ghost', span: 1 }]
            }
          ]
        },
        {
          layoutType: 'form',
          availableFieldCodes: ['assetName']
        }
      )
    ).toThrow('Layout contains unknown fields: ghostField')
  })
})

