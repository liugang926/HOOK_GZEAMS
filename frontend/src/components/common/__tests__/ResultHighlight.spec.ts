import { mount } from '@vue/test-utils'
import { describe, expect, it } from 'vitest'

import ResultHighlight from '../ResultHighlight.vue'

describe('ResultHighlight', () => {
  it('renders sanitized highlight markup while preserving <em> tags', () => {
    const wrapper = mount(ResultHighlight, {
      props: {
        highlight: 'Dell <em>Laptop</em> <script>alert(1)</script>',
      },
    })

    expect(wrapper.html()).toContain('<em>Laptop</em>')
    expect(wrapper.html()).not.toContain('<script>')
    expect(wrapper.text()).toContain('alert(1)')
  })

  it('falls back to plain text when highlight is absent', () => {
    const wrapper = mount(ResultHighlight, {
      props: {
        fallback: 'Fallback Label',
      },
    })

    expect(wrapper.text()).toContain('Fallback Label')
  })
})
