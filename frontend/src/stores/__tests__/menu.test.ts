import { describe, expect, it } from 'vitest'
import { mergeMenuGroups, type LocalMenuGroup } from '@/stores/menu'

describe('mergeMenuGroups', () => {
  it('adds static branding item into an existing system menu group', () => {
    const baseGroups: LocalMenuGroup[] = [
      {
        id: 'system',
        code: 'system',
        name: 'menu.categories.system',
        icon: 'Setting',
        items: [
          {
            code: 'systemConfig',
            name: 'systemConfig',
            url: '/system/config',
            order: 900,
          },
        ],
      },
    ]

    const supplementGroups: LocalMenuGroup[] = [
      {
        id: 'system',
        code: 'system',
        name: 'menu.categories.system',
        icon: 'Setting',
        items: [
          {
            code: 'systemBranding',
            name: 'systemBranding',
            url: '/system/branding',
            order: 910,
          },
        ],
      },
    ]

    const merged = mergeMenuGroups(baseGroups, supplementGroups)
    const systemGroup = merged.find((group) => group.code === 'system')

    expect(systemGroup).toBeDefined()
    expect(systemGroup!.items.map((item) => item.code)).toEqual(['systemConfig', 'systemBranding'])
  })

  it('does not duplicate branding item when the backend already returns it', () => {
    const baseGroups: LocalMenuGroup[] = [
      {
        id: 'system',
        code: 'system',
        name: 'menu.categories.system',
        icon: 'Setting',
        items: [
          {
            code: 'systemBranding',
            name: 'systemBranding',
            url: '/system/branding',
            order: 910,
          },
        ],
      },
    ]

    const supplementGroups: LocalMenuGroup[] = [
      {
        id: 'system',
        code: 'system',
        name: 'menu.categories.system',
        icon: 'Setting',
        items: [
          {
            code: 'systemBranding',
            name: 'systemBranding',
            url: '/system/branding',
            order: 910,
          },
        ],
      },
    ]

    const merged = mergeMenuGroups(baseGroups, supplementGroups)
    const systemGroup = merged.find((group) => group.code === 'system')

    expect(systemGroup).toBeDefined()
    expect(systemGroup!.items).toHaveLength(1)
  })

  it('deduplicates branding item when backend uses different code casing', () => {
    const baseGroups: LocalMenuGroup[] = [
      {
        id: 'system',
        code: 'system',
        name: 'menu.categories.system',
        icon: 'Setting',
        items: [
          {
            code: 'SystemBranding',
            name: 'SystemBranding',
            url: '/system/branding',
            order: 910,
          },
        ],
      },
    ]

    const supplementGroups: LocalMenuGroup[] = [
      {
        id: 'system',
        code: 'system',
        name: 'menu.categories.system',
        icon: 'Setting',
        items: [
          {
            code: 'systemBranding',
            name: 'systemBranding',
            url: '/system/branding',
            order: 910,
          },
        ],
      },
    ]

    const merged = mergeMenuGroups(baseGroups, supplementGroups)
    const systemGroup = merged.find((group) => group.code === 'system')

    expect(systemGroup).toBeDefined()
    expect(systemGroup!.items).toHaveLength(1)
  })

  it('replaces malformed backend branding url with the canonical route', () => {
    const baseGroups: LocalMenuGroup[] = [
      {
        id: 'system',
        code: 'system',
        name: 'menu.categories.system',
        icon: 'Setting',
        items: [
          {
            code: 'SystemBranding',
            name: 'SystemBranding',
            url: 'system/branding',
            order: 910,
          },
        ],
      },
    ]

    const supplementGroups: LocalMenuGroup[] = [
      {
        id: 'system',
        code: 'system',
        name: 'menu.categories.system',
        icon: 'Setting',
        items: [
          {
            code: 'systemBranding',
            name: 'systemBranding',
            url: '/system/branding',
            order: 910,
          },
        ],
      },
    ]

    const merged = mergeMenuGroups(baseGroups, supplementGroups)
    const systemGroup = merged.find((group) => group.code === 'system')

    expect(systemGroup).toBeDefined()
    expect(systemGroup!.items).toHaveLength(1)
    expect(systemGroup!.items[0].url).toBe('/system/branding')
  })
})
