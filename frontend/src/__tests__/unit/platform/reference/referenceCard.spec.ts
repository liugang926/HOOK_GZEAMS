import { describe, expect, it } from 'vitest'
import { buildReferenceCardMetaItems } from '@/platform/reference/referenceCard'

const t = (key: string) => {
  const map: Record<string, string> = {
    'common.referenceCard.fields.status': '状态',
    'common.referenceCard.fields.department': '部门',
    'common.referenceCard.fields.location': '位置',
    'common.referenceCard.fields.depreciationMethod': '折旧方法',
    'common.referenceCard.fields.defaultUsefulLife': '默认使用年限',
    'common.referenceCard.fields.residualRate': '残值率',
    'common.yes': '是',
    'common.no': '否'
  }
  return map[key] || key
}

const te = (key: string) => key.startsWith('common.referenceCard.fields.') || key === 'common.yes' || key === 'common.no'

describe('referenceCard', () => {
  it('filters out id and duplicate title fields while keeping business summary fields', () => {
    const items = buildReferenceCardMetaItems(
      {
        id: '7b5d6b6e-52d6-4b38-862e-1ee0fbe8e331',
        code: '2001',
        name: '电子设备',
        depreciationMethodDisplay: 'Straight Line Method',
        defaultUsefulLife: 60,
        residualRate: '5.00',
        isActive: true
      },
      {
        label: '电子设备',
        secondary: '2001',
        t,
        te
      }
    )

    expect(items.map((item) => item.label)).toEqual([
      '折旧方法',
      '默认使用年限',
      '残值率',
      'Is Active'
    ])
    expect(items.map((item) => item.value)).toEqual([
      'Straight Line Method',
      '60',
      '5.00',
      '是'
    ])
  })
})
