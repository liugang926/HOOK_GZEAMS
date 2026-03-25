import { describe, expect, it } from 'vitest'
import {
  resolveDynamicDetailEffectivePermissions,
  shouldShowDynamicDetailEnhancements,
} from './dynamicDetailPageShellModel'

describe('dynamicDetailPageShellModel', () => {
  it('prefers runtime permissions and falls back to metadata or open access defaults', () => {
    expect(resolveDynamicDetailEffectivePermissions(
      { view: false, add: false, change: true, delete: false },
      { view: true, add: true, change: true, delete: true },
    )).toEqual({
      view: false,
      add: false,
      change: true,
      delete: false,
    })

    expect(resolveDynamicDetailEffectivePermissions(
      null,
      { view: true, add: false, change: true, delete: false },
    )).toEqual({
      view: true,
      add: false,
      change: true,
      delete: false,
    })

    expect(resolveDynamicDetailEffectivePermissions(null, null)).toEqual({
      view: true,
      add: true,
      change: true,
      delete: true,
    })
  })

  it('shows detail enhancements when lifecycle, navigation, or timeline data exists', () => {
    expect(shouldShowDynamicDetailEnhancements({
      isLifecycle: false,
      hasNavigationSection: false,
      hasTimelineConfig: false,
    })).toBe(false)

    expect(shouldShowDynamicDetailEnhancements({
      isLifecycle: true,
      hasNavigationSection: false,
      hasTimelineConfig: false,
    })).toBe(true)

    expect(shouldShowDynamicDetailEnhancements({
      isLifecycle: false,
      hasNavigationSection: true,
      hasTimelineConfig: false,
    })).toBe(true)

    expect(shouldShowDynamicDetailEnhancements({
      isLifecycle: false,
      hasNavigationSection: false,
      hasTimelineConfig: true,
    })).toBe(true)
  })
})
