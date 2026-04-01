import { describe, expect, it } from 'vitest'
import { mount, RouterLinkStub } from '@vue/test-utils'
import ObjectWorkspaceHero from '../object-workspace/ObjectWorkspaceHero.vue'

describe('ObjectWorkspaceHero', () => {
  it('renders signal metadata and quick links in stat cards', () => {
    const wrapper = mount(ObjectWorkspaceHero, {
      props: {
        variant: 'detail',
        objectCode: 'Asset',
        eyebrow: 'Asset Center',
        title: 'Asset Detail',
        description: 'Detail summary',
        stats: [
          {
            label: 'Latest signal',
            value: 'Approved for remediation',
            meta: 'Purchase Request · 03/18/2026, 08:15 AM',
            actions: [
              { label: 'Open source', to: '/objects/PurchaseRequest/pr-1' },
              { label: 'Jump to activity', to: { hash: '#detail-activity' } },
            ],
          },
        ],
      },
      global: {
        stubs: {
          RouterLink: RouterLinkStub,
        },
      },
    })

    expect(wrapper.text()).toContain('Approved for remediation')
    expect(wrapper.text()).toContain('Purchase Request · 03/18/2026, 08:15 AM')
    const links = wrapper.findAllComponents(RouterLinkStub)
    expect(links).toHaveLength(2)
    expect(links[0]?.props('to')).toBe('/objects/PurchaseRequest/pr-1')
    expect(links[1]?.props('to')).toEqual({ hash: '#detail-activity' })
  })
})
