import { describe, expect, it, vi } from 'vitest'
import { mount } from '@vue/test-utils'
import DesignerSectionHeader from '../DesignerSectionHeader.vue'

describe('DesignerSectionHeader', () => {
  it('supports inline title editing with enter confirm and escape cancel', async () => {
    const selectSection = vi.fn()
    const wrapper = mount(DesignerSectionHeader, {
      props: {
        sectionId: 'section_1',
        title: 'Basic Info',
        selected: true,
        interactive: true,
        selectSection
      }
    })

    await wrapper.find('[data-testid="designer-section-title"]').trigger('dblclick')
    const input = wrapper.find('[data-testid="designer-section-title-input"]')
    expect(input.exists()).toBe(true)
    expect(selectSection).toHaveBeenCalledWith('section_1')

    await input.setValue('Overview')
    await input.trigger('keydown', { key: 'Enter' })

    expect(wrapper.emitted('titleUpdate')?.[0]).toEqual(['section_1', 'Overview'])

    await wrapper.setProps({ title: 'Basic Info' })
    await wrapper.find('[data-testid="designer-section-title"]').trigger('dblclick')
    const secondInput = wrapper.find('[data-testid="designer-section-title-input"]')
    await secondInput.setValue('Cancelled')
    await secondInput.trigger('keydown', { key: 'Escape' })

    expect(wrapper.find('[data-testid="designer-section-title-input"]').exists()).toBe(false)
    expect((wrapper.emitted('titleUpdate') || [])).toHaveLength(1)
  })
})
