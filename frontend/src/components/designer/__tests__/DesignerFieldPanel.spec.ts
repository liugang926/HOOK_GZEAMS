import { describe, expect, it, vi } from 'vitest'
import { mount } from '@vue/test-utils'
import DesignerFieldPanel from '../DesignerFieldPanel.vue'

vi.mock('vue-i18n', () => ({
  useI18n: () => ({
    t: (_key: string, fallback?: string) => fallback || _key
  })
}))

describe('DesignerFieldPanel', () => {
  it('renders assignment progress summary', () => {
    const wrapper = mount(DesignerFieldPanel, {
      props: {
        renderMode: 'design',
        searchQuery: '',
        assignedFieldCount: 2,
        totalFieldCount: 5,
        filteredFieldGroups: [],
        isGroupExpanded: () => true,
        canAddField: () => true,
        getDisabledReason: () => null,
        isFieldAdded: () => false
      },
      global: {
        stubs: {
          'el-input': { template: '<div class="el-input-stub"></div>' },
          'el-progress': {
            props: ['percentage'],
            template: '<div class="el-progress-stub">{{ percentage }}</div>'
          },
          'el-icon': { template: '<i><slot /></i>' },
          ArrowRight: true,
          Search: true
        }
      }
    })

    expect(wrapper.text()).toContain('2/5')
    expect(wrapper.find('.el-progress-stub').text()).toContain('40')
  })
})
