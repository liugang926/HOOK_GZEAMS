import { describe, expect, it } from 'vitest'
import {
  canAddFieldInDesigner,
  getFieldDisabledReason,
  getRequiredModesForDesigner,
  getUnsupportedModesForField,
} from './designerFieldGuard'

describe('designerFieldGuard', () => {
  it('requires both edit and readonly support for shared form layout mode', () => {
    expect(getRequiredModesForDesigner('edit')).toEqual(['edit', 'readonly'])
    expect(getRequiredModesForDesigner(undefined)).toEqual(['edit', 'readonly'])
  })

  it('maps special modes correctly', () => {
    expect(getRequiredModesForDesigner('readonly')).toEqual(['readonly'])
    expect(getRequiredModesForDesigner('detail')).toEqual(['readonly'])
    expect(getRequiredModesForDesigner('search')).toEqual(['search'])
    expect(getRequiredModesForDesigner('list')).toEqual(['list'])
  })

  it('blocks field types unsupported by required mode set', () => {
    expect(getUnsupportedModesForField('password', 'edit')).toEqual(['readonly'])
    expect(canAddFieldInDesigner('password', 'edit')).toBe(false)
    expect(canAddFieldInDesigner('text', 'edit')).toBe(true)
  })

  it('returns a readable disabled reason', () => {
    expect(getFieldDisabledReason('password', 'edit')).toContain('readonly')
    expect(getFieldDisabledReason('text', 'edit')).toBeNull()
  })
})
