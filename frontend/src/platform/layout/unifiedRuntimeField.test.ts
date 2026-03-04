import { describe, it, expect } from 'vitest'
import { toRuntimeFieldFromLayout } from '@/platform/layout/unifiedRuntimeField'

describe('unifiedRuntimeField', () => {
  it('projects layout field without catalog fallback', () => {
    const runtime = toRuntimeFieldFromLayout({
      fieldCode: 'name',
      label: 'Name',
      fieldType: 'text',
      required: true,
      span: 2
    })

    expect(runtime.code).toBe('name')
    expect(runtime.label).toBe('Name')
    expect(runtime.fieldType).toBe('text')
    expect(runtime.required).toBe(true)
    expect(runtime.span).toBe(2)
  })

  it('merges catalog metadata with layout overrides', () => {
    const runtime = toRuntimeFieldFromLayout(
      {
        fieldCode: 'status',
        label: 'Status',
        fieldType: 'select',
        visible: false,
        componentProps: { clearable: true }
      },
      [
        {
          code: 'status',
          name: 'Status',
          fieldType: 'select',
          options: [{ label: 'Active', value: 'active' }],
          componentProps: { filterable: true }
        }
      ]
    )

    expect(runtime.code).toBe('status')
    expect(runtime.hidden).toBe(true)
    expect(runtime.options?.length).toBe(1)
    expect((runtime.componentProps as any).filterable).toBe(true)
    expect((runtime.componentProps as any).clearable).toBe(true)
  })

  it('resolves minHeight from componentProps aliases', () => {
    const runtime = toRuntimeFieldFromLayout({
      fieldCode: 'assetName',
      label: 'Asset Name',
      fieldType: 'text',
      component_props: { min_height: '176' }
    } as any)

    expect(runtime.minHeight).toBe(176)
    expect((runtime.componentProps as any).minHeight).toBe(176)
  })
})
