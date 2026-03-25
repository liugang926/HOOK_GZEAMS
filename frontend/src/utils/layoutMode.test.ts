import { describe, expect, it } from 'vitest'
import {
  normalizeDesignerMode,
  normalizeLayoutType,
  toMetadataContext,
  toRuntimeMode,
} from './layoutMode'

describe('layoutMode helpers', () => {
  it('normalizes mixed mode/type values to layout_type', () => {
    expect(normalizeLayoutType('edit')).toBe('form')
    expect(normalizeLayoutType('form')).toBe('form')
    expect(normalizeLayoutType('readonly')).toBe('form')
    expect(normalizeLayoutType('detail')).toBe('form')
    expect(normalizeLayoutType('list')).toBe('list')
    expect(normalizeLayoutType('search')).toBe('form')
  })

  it('normalizes values for designer mode', () => {
    expect(normalizeDesignerMode('form')).toBe('edit')
    expect(normalizeDesignerMode('edit')).toBe('edit')
    expect(normalizeDesignerMode('detail')).toBe('edit')
    expect(normalizeDesignerMode('readonly')).toBe('edit')
    expect(normalizeDesignerMode('search')).toBe('edit')
    expect(normalizeDesignerMode('list')).toBe('edit')
  })

  it('maps to runtime mode and metadata context consistently', () => {
    expect(toRuntimeMode('detail')).toBe('readonly')
    expect(toRuntimeMode('readonly')).toBe('readonly')
    expect(toRuntimeMode('form')).toBe('edit')
    expect(toRuntimeMode('list')).toBe('list')
    expect(toRuntimeMode('search')).toBe('search')

    expect(toMetadataContext('readonly')).toBe('form')
    expect(toMetadataContext('detail')).toBe('form')
    expect(toMetadataContext('list')).toBe('list')
    expect(toMetadataContext('search')).toBe('form')
    expect(toMetadataContext('edit')).toBe('form')
  })
})
