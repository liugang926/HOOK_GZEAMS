import { describe, expect, it } from 'vitest'
import { mount } from '@vue/test-utils'
import DocumentWorkflowProgress from '../DocumentWorkflowProgress.vue'

describe('DocumentWorkflowProgress', () => {
  it('passes the resolved active step index to the steps component', () => {
    const wrapper = mount(DocumentWorkflowProgress, {
      props: {
        currentStatus: 'approved',
        steps: [
          { key: 'draft', label: 'Draft' },
          { key: 'submitted', label: 'Submitted' },
          { key: 'approved', label: 'Approved' },
        ],
      },
      global: {
        stubs: {
          'el-steps': {
            props: ['active'],
            template: '<div class="steps-stub" :data-active="active"><slot /></div>',
          },
          'el-step': {
            props: ['title'],
            template: '<span class="step-stub">{{ title }}</span>',
          },
        },
      },
    })

    expect(wrapper.get('.steps-stub').attributes('data-active')).toBe('2')
    expect(wrapper.text()).toContain('Draft')
    expect(wrapper.text()).toContain('Approved')
  })
})
