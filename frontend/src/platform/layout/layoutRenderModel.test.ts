import { describe, expect, it } from 'vitest'
import {
  buildLayoutRenderModel,
  createModePolicyForContext,
  toFieldViewModels
} from '@/platform/layout/layoutRenderModel'

describe('layoutRenderModel', () => {
  it('creates mode policy by context with sane defaults', () => {
    expect(createModePolicyForContext('detail-runtime')).toMatchObject({
      metadataContext: 'form',
      strictVisibility: false,
      source: 'runtime'
    })
    expect(createModePolicyForContext('detail-strict')).toMatchObject({
      metadataContext: 'detail',
      strictVisibility: true,
      source: 'runtime'
    })
    expect(createModePolicyForContext('designer-preview')).toMatchObject({
      metadataContext: 'form',
      strictVisibility: false,
      source: 'designer'
    })
  })

  it('normalizes raw fields into stable field view model payload', () => {
    const fields = toFieldViewModels([
      { code: 'assetName', name: 'Asset Name', fieldType: 'text', show_in_form: true },
      { fieldCode: 'assetCode', label: 'Asset Code', field_type: 'text', is_hidden: false },
      { code: '' }
    ] as any)

    expect(fields).toHaveLength(2)
    expect(fields[0]).toMatchObject({
      code: 'assetName',
      name: 'Asset Name',
      label: 'Asset Name',
      fieldType: 'text'
    })
    expect(fields[1]).toMatchObject({
      code: 'assetCode',
      name: 'Asset Code',
      label: 'Asset Code',
      fieldType: 'text'
    })
  })

  it('builds layout render model for shared render pipeline input', () => {
    const model = buildLayoutRenderModel({
      sections: [{ id: 'basic', fields: [{ fieldCode: 'assetName' }] }],
      fields: [{ code: 'assetName', name: 'Asset Name', fieldType: 'text' }] as any[],
      modePolicy: createModePolicyForContext('detail-runtime')
    })

    expect(model.sections).toHaveLength(1)
    expect(model.fields).toHaveLength(1)
    expect(model.fields[0].code).toBe('assetName')
    expect(model.modePolicy.source).toBe('runtime')
  })
})
