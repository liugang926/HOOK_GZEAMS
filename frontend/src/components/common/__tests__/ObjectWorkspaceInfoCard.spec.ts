import { describe, expect, it } from 'vitest'
import { mount, RouterLinkStub } from '@vue/test-utils'
import ObjectWorkspaceInfoCard from '../object-workspace/ObjectWorkspaceInfoCard.vue'

describe('ObjectWorkspaceInfoCard', () => {
  it('renders row metadata and action links', () => {
    const wrapper = mount(ObjectWorkspaceInfoCard, {
      props: {
        variant: 'detail',
        eyebrow: 'Summary',
        title: 'Asset Loan',
        rows: [
          {
            label: 'Latest signal',
            value: 'Approval Comment: Approved for audit remediation',
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

    expect(wrapper.text()).toContain('Approval Comment: Approved for audit remediation')
    expect(wrapper.text()).toContain('Purchase Request · 03/18/2026, 08:15 AM')
    const links = wrapper.findAllComponents(RouterLinkStub)
    expect(links).toHaveLength(2)
    expect(links[0]?.props('to')).toBe('/objects/PurchaseRequest/pr-1')
    expect(links[1]?.props('to')).toEqual({ hash: '#detail-activity' })
  })
})
