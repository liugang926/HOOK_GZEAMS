import { flushPromises, mount } from '@vue/test-utils'
import { defineComponent } from 'vue'
import { beforeEach, describe, expect, it, vi } from 'vitest'

import TagSelector from '../TagSelector.vue'

const listMock = vi.fn()

vi.mock('@/api/tags', () => ({
  assetTagGroupApi: {
    list: (...args: unknown[]) => listMock(...args),
  },
}))

const ElSelectStub = defineComponent({
  name: 'ElSelect',
  props: {
    modelValue: {
      type: [Array, String, null],
      default: null,
    },
    multiple: Boolean,
    placeholder: {
      type: String,
      default: '',
    },
    loading: Boolean,
  },
  emits: ['change'],
  template: `
    <div class="el-select-stub" :data-placeholder="placeholder" :data-loading="String(loading)">
      <slot />
      <button class="change-trigger" @click="$emit('change', multiple ? ['tag-1', 'tag-2'] : 'tag-1')">
        change
      </button>
    </div>
  `,
})

const ElOptionGroupStub = defineComponent({
  name: 'ElOptionGroup',
  props: {
    label: {
      type: String,
      default: '',
    },
  },
  template: `
    <section class="el-option-group-stub">
      <h4>{{ label }}</h4>
      <slot />
    </section>
  `,
})

const ElOptionStub = defineComponent({
  name: 'ElOption',
  props: {
    label: {
      type: String,
      default: '',
    },
    value: {
      type: String,
      default: '',
    },
  },
  template: `
    <div class="el-option-stub" :data-value="value">
      <span class="el-option-stub__label">{{ label }}</span>
      <slot />
    </div>
  `,
})

describe('TagSelector', () => {
  beforeEach(() => {
    listMock.mockReset()
  })

  it('autoloads asset tag groups and renders grouped tag options', async () => {
    listMock.mockResolvedValue({
      count: 1,
      next: null,
      previous: null,
      results: [
        {
          id: 'group-1',
          name: 'Usage Status',
          code: 'usage_status',
          description: '',
          color: '#409EFF',
          icon: 'Collection',
          sortOrder: 1,
          isSystem: false,
          isActive: true,
          tagsCount: 2,
          tags: [
            {
              id: 'tag-1',
              tagGroup: 'group-1',
              groupName: 'Usage Status',
              groupColor: '#409EFF',
              name: 'In Use',
              code: 'in_use',
              color: '#67C23A',
              icon: 'CircleCheck',
              assetCount: 12,
            },
            {
              id: 'tag-2',
              tagGroup: 'group-1',
              groupName: 'Usage Status',
              groupColor: '#409EFF',
              name: 'Idle',
              code: 'idle',
              color: '',
              icon: '',
              assetCount: 5,
            },
          ],
        },
      ],
    })

    const wrapper = mount(TagSelector, {
      props: {
        modelValue: [],
        showCount: true,
      },
      global: {
        stubs: {
          'el-select': ElSelectStub,
          'el-option-group': ElOptionGroupStub,
          'el-option': ElOptionStub,
        },
      },
    })

    await flushPromises()

    expect(listMock).toHaveBeenCalledWith({
      pageSize: 200,
      isActive: true,
    })
    expect(wrapper.text()).toContain('Usage Status')
    expect(wrapper.text()).toContain('In Use')
    expect(wrapper.text()).toContain('(12)')
    expect(wrapper.text()).toContain('Idle')
  })

  it('emits updated values when the selection changes', async () => {
    const wrapper = mount(TagSelector, {
      props: {
        modelValue: [],
        groups: [
          {
            id: 'group-1',
            name: 'Source',
            code: 'source',
            description: '',
            color: '#E6A23C',
            icon: '',
            sortOrder: 1,
            isSystem: false,
            isActive: true,
            tagsCount: 1,
            tags: [
              {
                id: 'tag-1',
                tagGroup: 'group-1',
                groupName: 'Source',
                groupColor: '#E6A23C',
                name: 'Purchase',
                code: 'purchase',
                color: '#E6A23C',
                icon: '',
              },
            ],
          },
        ],
      },
      global: {
        stubs: {
          'el-select': ElSelectStub,
          'el-option-group': ElOptionGroupStub,
          'el-option': ElOptionStub,
        },
      },
    })

    await wrapper.get('.change-trigger').trigger('click')

    expect(listMock).not.toHaveBeenCalled()
    expect(wrapper.emitted('update:modelValue')).toEqual([[['tag-1', 'tag-2']]])
    expect(wrapper.emitted('change')).toEqual([[['tag-1', 'tag-2']]])
  })
})
