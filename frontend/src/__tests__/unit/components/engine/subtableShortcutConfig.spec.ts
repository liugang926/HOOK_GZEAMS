import { describe, expect, it } from 'vitest'
import { buildSubTableShortcutItems } from '@/components/engine/fields/subtableShortcutConfig'

describe('subtableShortcutConfig', () => {
  it('builds Windows-style combos when command builder returns Ctrl', () => {
    const items = buildSubTableShortcutItems({
      commandCombo: (key) => `Ctrl + ${key}`,
      shiftCommandCombo: (key) => `Shift + Ctrl + ${key}`
    })

    const combos = items.map((item) => item.combo)
    expect(combos).toContain('F1')
    expect(combos).toContain('Shift + F1')
    expect(combos).toContain('Ctrl + Enter')
    expect(combos).toContain('Shift + Ctrl + D')
    expect(combos).not.toContain('⌘ + Enter')
  })

  it('builds macOS-style combos when command builder returns ⌘', () => {
    const items = buildSubTableShortcutItems({
      commandCombo: (key) => `⌘ + ${key}`,
      shiftCommandCombo: (key) => `Shift + ⌘ + ${key}`
    })

    const combos = items.map((item) => item.combo)
    expect(combos).toContain('F1')
    expect(combos).toContain('Shift + F1')
    expect(combos).toContain('⌘ + Enter')
    expect(combos).toContain('Shift + ⌘ + D')
    expect(combos).not.toContain('Ctrl + Enter')
  })
})
